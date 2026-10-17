"""Source oracle for the `splash_screen.py` port (layer 9at).

The source boot splash shows the logo (assets/logo.png, scaled into a
340x320 box and growing from 85 % to 100 % over 0.9 s) or a glowing text
title, a subtitle, a "Tap anywhere to skip" hint, 46 drifting particles on a
baked gradient + vignette background. It fades in over 0.4 s, fades out over
the last 0.45 s of SPLASH_DURATION (3 s), and a tap skips with a 0.25 s fade.

This oracle runs the REAL `SplashScreen` under a recording pygame shim
(surfaces log their draw calls, fonts measure 0.55*size px per glyph, the
logo is a 1024x1024 stand-in like the shipped `assets/logo.png`) and records
the timeline, the baked background, the particle motion and the layout so
`scripts/ui/splash_timeline.gd` replays them exactly.

Run: python godot_rebuild/tests/splash_screen_source_oracle.py
"""
import json
import random
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "splash_screen.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "splash_screen_source.json"
W, H = 1280, 720
LOGO_PX = 1024


class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    width = property(lambda s: s.w)
    height = property(lambda s: s.h)
    right = property(lambda s: s.x + s.w)
    bottom = property(lambda s: s.y + s.h)
    centerx = property(lambda s: s.x + s.w // 2)
    centery = property(lambda s: s.y + s.h // 2)
    center = property(lambda s: (s.centerx, s.centery))


class Surface:
    def __init__(self, size, flags=0, *_args):
        self.size = (int(size[0]), int(size[1]))
        self.flags = flags
        self.log = []
        self.alpha = 255

    def get_size(self):
        return self.size

    def get_width(self):
        return self.size[0]

    def get_height(self):
        return self.size[1]

    def convert(self):
        return self

    def copy(self):
        other = Surface(self.size, self.flags)
        other.alpha = self.alpha
        return other

    def set_alpha(self, value):
        self.alpha = value

    def fill(self, color, rect=None, special_flags=0):
        self.log.append(("fill", tuple(color), special_flags))

    def blit(self, src, dest, *_args, **_kwargs):
        if isinstance(dest, Rect):
            pos = (dest.x, dest.y)
        else:
            pos = (int(dest[0]), int(dest[1]))
        self.log.append(("blit", src, pos))

    def get_rect(self, **anchors):
        r = Rect(0, 0, self.size[0], self.size[1])
        if "center" in anchors:
            cx, cy = anchors["center"]
            r.x, r.y = int(cx) - r.w // 2, int(cy) - r.h // 2
        return r


class Text(Surface):
    def __init__(self, text, size, color):
        super().__init__((int(size * 0.55) * len(text), size))
        self.text, self.color, self.font_size = text, tuple(color), size


class Font:
    def __init__(self, _name, size):
        self.size = size

    def render(self, text, _aa, color):
        return Text(text, self.size, color)


class Draw:
    @staticmethod
    def rect(surface, color, rect, width=0, **_kw):
        surface.log.append(("rect", tuple(color), tuple(int(v) for v in rect), width))

    @staticmethod
    def circle(surface, color, center, radius, **_kw):
        surface.log.append(("circle", tuple(color), (int(center[0]), int(center[1])), radius))

    @staticmethod
    def line(surface, color, a, b, width=1):
        surface.log.append(("line", tuple(color), tuple(a), tuple(b), width))


def _scale(surface, size):
    return Surface(size, surface.flags)


def _load(logo):
    pygame = types.ModuleType("pygame")
    pygame.Surface = Surface
    pygame.Rect = Rect
    pygame.SRCALPHA = 65536
    pygame.BLEND_RGBA_MULT = 7
    pygame.draw = Draw
    pygame.font = types.SimpleNamespace(Font=Font)
    pygame.transform = types.SimpleNamespace(smoothscale=_scale)
    if logo:
        pygame.image = types.SimpleNamespace(load=lambda _p: Surface((LOGO_PX, LOGO_PX)))
    else:
        pygame.image = types.SimpleNamespace(
            load=lambda _p: (_ for _ in ()).throw(IOError("no logo")))
    saved = sys.modules.get("pygame")
    sys.modules["pygame"] = pygame
    try:
        ns = {"__name__": "splash_oracle", "__file__": str(SOURCE)}
        exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), ns)
    finally:
        if saved is None:
            sys.modules.pop("pygame", None)
        else:
            sys.modules["pygame"] = saved
    return ns


def _frame(splash):
    screen = splash.screen
    screen.log = []
    splash.draw()
    out = {"elapsed": round(splash.elapsed, 6), "title_alpha": splash.title_alpha,
           "overall_alpha": round(splash._overall_alpha(), 6), "done": splash.done,
           "drawn": bool(screen.log)}
    if not screen.log:
        return out
    particles = [e for e in screen.log if e[0] == "circle"]
    out["particles"] = [{"color": list(e[1]), "pos": list(e[2]), "radius": e[3]} for e in particles]
    blits = [e for e in screen.log if e[0] == "blit"]
    texts = []
    for _, src, pos in blits:
        if isinstance(src, Text):
            texts.append({"text": src.text, "size": src.font_size, "color": list(src.color),
                          "alpha": src.alpha, "pos": list(pos), "w": src.size[0], "h": src.size[1]})
    out["texts"] = texts
    images = [{"size": list(src.size), "alpha": src.alpha, "pos": list(pos)}
              for _, src, pos in blits
              if isinstance(src, Surface) and not isinstance(src, Text) and src is not splash._bg_cache]
    out["images"] = images
    out["lines"] = [{"color": list(e[1]), "a": list(e[2]), "b": list(e[3]), "width": e[4]}
                    for e in screen.log if e[0] == "line"]
    return out


def source_fixture():
    random.seed(7)
    ns = _load(logo=True)
    screen = Surface((W, H))
    splash = ns["SplashScreen"](screen)
    particles0 = [dict(p, color=list(p["color"])) for p in splash.particles]

    dt = 1.0 / 60.0
    sample_frames = {0, 6, 12, 24, 30, 36, 54, 60, 66, 120, 150, 153, 160, 170, 174, 175, 180, 181}
    timeline = []
    frame = 0
    while not splash.done and frame < 400:
        if frame in sample_frames:
            timeline.append(_frame(splash))
        splash.update(dt)
        frame += 1
    timeline.append(dict(_frame(splash), frame=frame))
    done_frame = frame

    bg = splash._bg_cache
    gradient = [{"rect": list(e[2]), "color": list(e[1])} for e in bg.log if e[0] == "rect"]
    vignette = None
    for e in bg.log:
        if e[0] == "blit" and isinstance(e[1], Surface):
            vignette = [{"inset": v[2][0], "alpha": v[1][3]} for v in e[1].log if v[0] == "rect"]
    # Particle motion is pinned over the longest stretch in which no particle
    # wraps (the wrap re-rolls x with `random`, which the port must not share).
    safe_frames = min(120, min(int((p["y"] + 6) / p["speed"]) - 1 for p in particles0))
    random.seed(7)
    motion = ns["SplashScreen"](Surface((W, H)))
    for _ in range(safe_frames):
        motion.update(dt)
    particles_after = [{"x": round(p["x"], 6), "y": round(p["y"], 6)} for p in motion.particles]

    # Skip path: fresh splash, 1 s in, then skip.
    random.seed(7)
    skip_splash = ns["SplashScreen"](Surface((W, H)))
    for _ in range(60):
        skip_splash.update(dt)
    skip_splash.skip()
    skip_timeline = []
    frames = 0
    while not skip_splash.done and frames < 100:
        skip_timeline.append({"elapsed": round(skip_splash.elapsed, 6),
                              "overall_alpha": round(skip_splash._overall_alpha(), 6)})
        skip_splash.update(dt)
        frames += 1
    skip_done = {"frames_after_skip": frames, "elapsed": round(skip_splash.elapsed, 6)}

    # Logo grow quantisation samples and glow ring alphas at full size.
    grow = []
    for t in (0.0, 0.1, 0.3, 0.45, 0.6, 0.89, 0.9, 2.0):
        g = min(1.0, t / 0.9)
        gq = round((0.85 + 0.15 * g) * 20) / 20.0
        grow.append({"elapsed": t, "gq": gq, "size": [max(1, int(320 * gq)), max(1, int(320 * gq))]})
    glow_r = 320 // 2 + 30
    glow = [{"g": g, "alpha": int(12 * (1 - g / glow_r))} for g in range(glow_r, 0, -3)]

    # Title-only layout (no logo file).
    random.seed(7)
    ns2 = _load(logo=False)
    plain = ns2["SplashScreen"](Surface((W, H)))
    for _ in range(120):
        plain.update(dt)
    plain_frame = _frame(plain)

    return {
        "source": "splash_screen.py (real SplashScreen under a recording pygame shim)",
        "game_name": ns["GAME_NAME"],
        "duration": ns["SPLASH_DURATION"],
        "subtitle": "A MOBA TOWER DEFENSE ADVENTURE",
        "hint": "Tap anywhere to skip",
        "colors": {k: list(ns[k]) for k in ("ACCENT", "ACCENT_2", "TEXT_MAIN", "TEXT_DIM")},
        "particle_count": len(particles0),
        "particle_palette": [[255, 210, 120], [230, 160, 255], [255, 245, 230], [180, 200, 255]],
        "particles_initial": particles0,
        "particles_after_frames": safe_frames,
        "particles_after": particles_after,
        "logo_px": LOGO_PX,
        "logo_box": [340, 320],
        "logo_scaled": [320, 320],
        "logo_grow": grow,
        "logo_glow_radius": glow_r,
        "logo_glow": glow,
        "gradient": gradient,
        "vignette": vignette,
        "timeline": timeline,
        "done_frame": done_frame,
        "skip_timeline": skip_timeline,
        "skip_done": skip_done,
        "plain_frame": plain_frame,
    }


def main():
    fixture = source_fixture()
    assert fixture["timeline"][-1]["done"] is True
    assert fixture["skip_done"]["frames_after_skip"] > 0
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)


if __name__ == "__main__":
    main()
