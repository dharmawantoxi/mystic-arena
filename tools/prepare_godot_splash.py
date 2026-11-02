#!/usr/bin/env python3
"""Export splash_screen.py to the active Godot project with a pygame oracle.

The contract is extracted from AST (reusing the pure extractor in
gen_splash_cpp.py, without generating C++). The oracle runs the real
SplashScreen headless with deterministic fake font metrics and a seeded RNG.
--check is byte-exact and fail-closed; it never writes in check mode.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "splash_screen.py"
CONTRACT = PROJECT / "data/splash.json"
FIXTURE = PROJECT / "tests/fixtures/splash_parity.json"
PYGAME_VERSION = "2.6.1"
SEED = 1234
_TRACK_SURFACE = None
_ROLES = {}
_KEEP = []
SCREEN = (1280, 720)
DT = 1.0 / 60.0
sys.path.insert(0, str(ROOT / "tools"))
import gen_splash_cpp as ast_spec  # noqa: E402


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise AssertionError(f"Non-finite splash value: {value!r}")
    return value


def _text(value) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, indent=2,
                      allow_nan=False, sort_keys=True) + "\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _literal(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing literal {name} in {path}")


def build_contract() -> dict:
    spec = ast_spec.build_spec()
    cfg = dict(spec.values)
    if cfg["duration"] <= 0 or cfg["particle_count"] <= 0:
        raise AssertionError("Splash duration/particle count must be positive")
    for key in ("accent", "accent_2", "text_main", "text_dim"):
        if len(cfg[key]) != 3 or any(not 0 <= int(v) <= 255 for v in cfg[key]):
            raise AssertionError(f"Invalid splash color {key}")
    font_map = _literal(ROOT / "_render.py", "_STYLE_FONT_MAP")
    perf = ast.parse((ROOT / "mobile/perf.py").read_text(encoding="utf-8"))
    quality = next(n for n in perf.body if isinstance(n, ast.ClassDef) and n.name == "_Quality")
    init = next(n for n in quality.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    cheap = None
    for node in ast.walk(init):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == "cheap_alpha":
                    cheap = ast.literal_eval(node.value)
    if not isinstance(cheap, bool):
        raise AssertionError("mobile.perf Quality.cheap_alpha default not found")
    return _jsonable({
        "schema": 1,
        "source": "splash_screen.py",
        "source_sha256": _sha(SOURCE.read_bytes()),
        "render_source_sha256": _sha((ROOT / "_render.py").read_bytes()),
        "perf_source_sha256": _sha((ROOT / "mobile/perf.py").read_bytes()),
        "config": cfg,
        "source_lines": spec.lines,
        "font_files": font_map,
        "cheap_alpha_default": cheap,
        "rng": "godot-RandomNumberGenerator-seeded-1234",
        "particle_seed": SEED,
    })


class FakeFont:
    def __init__(self, size, role):
        self.size = int(size)
        self.role = role

    def render(self, text, aa, color, *a, **k):
        import pygame
        w = max(1, len(str(text)) * self.size // 2)
        h = max(1, self.size)
        surf = _TRACK_SURFACE((w, h), pygame.SRCALPHA)
        surf.fill((int(color[0]), int(color[1]), int(color[2]), 255))
        _ROLES[id(surf)] = self.role
        _KEEP.append(surf)
        return surf


class RecordSurface:
    """Mixin installed on a pygame.Surface subclass by the oracle context."""

    def blit(self, src, dest=None, *a, **k):
        import pygame
        pos = dest if dest is not None else (0, 0)
        if hasattr(pos, "x"):
            pos = (pos.x, pos.y)
        self._splash_blits.append({
            "role": _ROLES.get(id(src), ""),
            "size": [src.get_width(), src.get_height()],
            "pos": [int(pos[0]), int(pos[1])],
            "alpha": src.get_alpha(),
        })
        return pygame.Surface.blit(self, src, dest, *a, **k)


@contextlib.contextmanager
def source_module():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    if pygame.version.ver != PYGAME_VERSION:
        raise AssertionError(f"Splash oracle requires pygame=={PYGAME_VERSION}")
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    rng_state = random.getstate()
    previous_backend = pygame.transform.get_smoothscale_backend()
    pygame.transform.set_smoothscale_backend("GENERIC")

    global _TRACK_SURFACE
    class TrackSurface(RecordSurface, pygame.Surface):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._splash_blits = []
            self._splash_lines = []

    _TRACK_SURFACE = TrackSurface
    spec = importlib.util.spec_from_file_location("mystic_splash_export", SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.SplashScreen._init_fonts = lambda self: None
    old_smoothscale = pygame.transform.smoothscale

    def smoothscale(surface, size, *a, **k):
        out = old_smoothscale(surface, size, *a, **k)
        if _ROLES.get(id(surface), "") == "logo":
            _ROLES[id(out)] = "logo"
            _KEEP.append(out)
        return out

    pygame.transform.smoothscale = smoothscale
    old_line = pygame.draw.line

    def line(surface, color, start, end, width=1, *a, **k):
        if hasattr(surface, "_splash_lines") and width == 2:
            surface._splash_lines.append({"start": [int(start[0]), int(start[1])],
                                          "end": [int(end[0]), int(end[1])],
                                          "color": [int(c) for c in color[:3]], "width": int(width)})
        return old_line(surface, color, start, end, width, *a, **k)

    pygame.draw.line = line
    try:
        yield module, TrackSurface
    finally:
        pygame.draw.line = old_line
        pygame.transform.smoothscale = old_smoothscale
        pygame.transform.set_smoothscale_backend(previous_backend)
        random.setstate(rng_state)
        sys.modules.pop(spec.name, None)


def _install_fonts(splash):
    splash.font_presents = FakeFont(34, "presents")
    splash.font_title = FakeFont(92, "title")
    splash.font_title_below = FakeFont(66, "title")
    splash.font_sub = FakeFont(22, "sub")
    splash.font_hint = FakeFont(16, "hint")


def _make(module, TrackSurface, size=SCREEN, logo_size=None, seed=SEED):
    import pygame
    random.seed(seed)
    screen = TrackSurface(size)
    splash = module.SplashScreen(screen)
    _install_fonts(splash)
    if logo_size is None:
        splash.logo_img = None
    else:
        img = pygame.Surface(logo_size, pygame.SRCALPHA)
        img.fill((200, 160, 90, 255))
        _ROLES[id(img)] = "logo"
        _KEEP.append(img)
        splash.logo_img = img
    return splash


def _timeline(module, TrackSurface) -> list:
    rows = []
    for name, skip_at in (("normal", None), ("skip_zero", 0.0),
                          ("skip_early", 0.1), ("skip_mid", 1.0),
                          ("skip_late", 2.0)):
        splash = _make(module, TrackSurface)
        frames = []
        for frame in range(200):
            if skip_at is not None and frame * DT >= skip_at and not splash.skipped:
                splash.skip()
            splash.update(DT)
            frames.append([splash.elapsed, splash.title_alpha,
                           splash._overall_alpha(), splash.done, splash.skipped])
        rows.append({"name": name, "skip_at": skip_at, "frames": frames})
    return rows


def _particles(module, TrackSurface) -> dict:
    splash = _make(module, TrackSurface)
    initial = [dict(p) for p in splash.particles]
    respawn = []
    real_uniform = random.uniform

    def spy(a, b):
        value = real_uniform(a, b)
        respawn.append(value)
        return value

    random.uniform = spy
    try:
        for _ in range(240):
            splash.update(DT)
    finally:
        random.uniform = real_uniform
    final = [dict(p) for p in splash.particles]
    splash.elapsed = 1.5
    draws = []
    for p in splash.particles:
        tw = 0.5 + 0.5 * math.sin(1.5 * 2.5 + p["phase"])
        draws.append({"pos": [int(p["x"]), int(p["y"])],
                      "radius": max(1, int(p["r"])),
                      "color": [int(ch * (0.35 + 0.65 * tw)) for ch in p["color"]]})
    return {"seed": SEED, "initial": initial, "final": final,
            "respawn": respawn, "frames": 240, "draw_at_1_5": draws}


def _background(module, TrackSurface) -> list:
    import pygame
    cases = []
    for size in ((64, 48), (320, 240), (1280, 720), (1277, 719)):
        splash = _make(module, TrackSurface, size=size)
        splash.elapsed = 1.5
        splash.title_alpha = 255
        splash.draw()
        bg = splash._bg_cache
        points = [(0, 0), (1, 1), (2, 2), (3, 3), (size[0] // 2, size[1] // 2),
                  (size[0] - 1, size[1] - 1), (size[0] - 2, size[1] - 2)]
        samples = [{"pos": list(pt), "rgb": list(bg.get_at(pt))[:3]} for pt in points]
        row = {"size": list(size), "samples": samples}
        if size[0] <= 320:
            row["rgb_sha256"] = _sha(pygame.image.tobytes(bg, "RGB"))
        cases.append(row)
    return cases


def _layout_case(module, TrackSurface, logo_size, elapsed) -> dict:
    splash = _make(module, TrackSurface, logo_size=logo_size)
    splash.elapsed = elapsed
    splash.title_alpha = int(255 * min(1.0, max(0.0, (elapsed - 0.5) / 0.6)))
    screen = splash.screen
    screen._splash_blits.clear()
    screen._splash_lines.clear()
    splash.draw()
    blits = screen._splash_blits
    has_logo = logo_size is not None
    if splash._overall_alpha() <= 0.001:
        return {"logo_source": list(logo_size) if has_logo else [0, 0],
                "has_logo": has_logo, "elapsed": elapsed, "drawn": False,
                "title_alpha": splash.title_alpha,
                "overall_alpha": splash._overall_alpha(),
                "hint_alpha": 0, "title_rect": None,
                "subtitle_rect": None, "hint_rect": None}
    title_size = [len(module.GAME_NAME) * (66 if has_logo else 92) // 2,
                  66 if has_logo else 92]
    sub_size = [len("A MOBA TOWER DEFENSE ADVENTURE") * 22 // 2, 22]
    hint_size = [len("Tap anywhere to skip") * 16 // 2, 16]

    def find(size, role="", required=True):
        for b in blits:
            if b["size"] == size and (not role or b["role"] == role):
                return b
        if required:
            raise AssertionError(f"Missing blit size={size} role={role}")
        return None

    title = find(title_size, required=splash.title_alpha > 0)
    sub = find(sub_size, "sub")
    hint = find(hint_size, "hint")
    row = {"logo_source": list(logo_size) if has_logo else [0, 0],
           "has_logo": has_logo, "elapsed": elapsed, "drawn": True,
           "title_alpha": splash.title_alpha,
           "overall_alpha": splash._overall_alpha(),
           "hint_alpha": int(140 * splash._overall_alpha()),
           "title_rect": (title["pos"] + title["size"]) if title else None,
           "subtitle_rect": sub["pos"] + sub["size"],
           "hint_rect": hint["pos"] + hint["size"],
           "accent_lines": list(screen._splash_lines)}
    if splash.title_alpha > 0:
        row["title_glow_rects"] = [b["pos"] + b["size"] for b in blits
                                    if b["role"] == "" and b["size"][0] > title_size[0]
                                    and title_size[1] < b["size"][1] < title_size[1] * 2
                                    and b["alpha"] == 255]
    if has_logo:
        logo = next(b for b in blits if b["role"] == "logo")
        row["logo_rect"] = logo["pos"] + logo["size"]
        row["logo_alpha"] = logo["alpha"]
    return row


def _logo_glow(module, TrackSurface) -> list:
    # Direct source-equivalent glow surfaces for deterministic alpha profiles.
    import pygame
    out = []
    for radius in (30, 47, 190):
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for g in range(radius, 0, -3):
            alpha = int(12 * (1 - g / radius))
            pygame.draw.circle(surf, (*module.ACCENT, alpha), (radius, radius), g)
        profile = [surf.get_at((radius + d, radius))[3] for d in range(radius)]
        out.append({"radius": radius, "alpha_profile": profile})
    return out


def build_oracle(module, TrackSurface) -> dict:
    contract = build_contract()
    layout = []
    for logo_size in (None, (1024, 1024), (800, 300), (64, 32)):
        for elapsed in (0.0, 0.45, 0.9, 1.5):
            layout.append(_layout_case(module, TrackSurface, logo_size, elapsed))
    return _jsonable({
        "source_sha256": contract["source_sha256"],
        "seed": SEED,
        "screen": list(SCREEN),
        "dt": DT,
        "fake_font": "w=len(text)*size//2, h=size",
        "timeline": _timeline(module, TrackSurface),
        "particles": _particles(module, TrackSurface),
        "background": _background(module, TrackSurface),
        "layout_cases": layout,
        "logo_glow": _logo_glow(module, TrackSurface),
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        contract = build_contract()
        with source_module() as (module, TrackSurface):
            oracle = build_oracle(module, TrackSurface)
        contract_text, oracle_text = _text(contract), _text(oracle)
        if args.check:
            if not CONTRACT.is_file() or not FIXTURE.is_file():
                raise AssertionError("Missing splash contract/fixture; run prepare first")
            if CONTRACT.read_text(encoding="utf-8") != contract_text:
                raise AssertionError("Stale splash contract")
            if FIXTURE.read_text(encoding="utf-8") != oracle_text:
                raise AssertionError("Stale splash oracle fixture")
        else:
            CONTRACT.parent.mkdir(parents=True, exist_ok=True)
            FIXTURE.parent.mkdir(parents=True, exist_ok=True)
            CONTRACT.write_text(contract_text, encoding="utf-8")
            FIXTURE.write_text(oracle_text, encoding="utf-8")
    except (AssertionError, ValueError, TypeError, KeyError, OSError, ImportError,
            ast_spec.SplashError) as exc:
        print(f"splash preparation failed: {exc}", file=sys.stderr)
        return 1
    print(f"{'Verified' if args.check else 'Prepared'} splash: "
          f"{len(oracle['timeline'])} timelines, {len(oracle['layout_cases'])} layouts; "
          f"sha256={contract['source_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
