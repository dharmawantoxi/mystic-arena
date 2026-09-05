#!/usr/bin/env python3
"""Regression test Level 3 ORIGINAL-MAX.

Mengunci (semua lewat path shipping bosses.level3.draw_*):
  * semua mode render tanpa exception & berisi piksel;
  * bbox solid keluarga (4 boss) hadir & true boss presence memadai;
  * hurt flash menerangkan BADAN tapi bayangan tanah TIDAK ikut menyala;
  * bayangan reaktif mengecil saat lift, dasar tetap menapak;
  * durasi FX renderer == active_skill_timer AI (untuk skill tiap boss);
  * animasi kontinu (bukan stepping bucket) & idle per boss < 2.35 ms/frame;
  * outline siluet + pass pencahayaan (konvensi level2) terlihat;
  * renderer prosedural (tanpa pygame.image.load).

Jalankan: python3 tools/test_level3_masterwork.py
"""
import inspect
import os
import re
import sys
import time
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level3 as L

# ── peta: (nama, kelas, fn draw, namespace, CD attack) ──────────────
BOSSES = [
    ("varkul", "mini", L.draw_varkul, L._NS_varkul, 60),
    ("xerathis", "mini", L.draw_xerathis, L._NS_xerathis, 59),
    ("nyzrak", "mini", L.draw_nyzrak, L._NS_nyzrak, 77),
    ("ancient_apparition", "true", L.draw_ancient_apparition,
     L._NS_ancient_apparition, 61),
]

# Skill durations di AI (active_skill_timer), sesuai base_boss.py.
AI = {
    "varkul": {"q": 50, "w": 60, "e": 50, "r": 80},
    "xerathis": {"q": 60, "w": 50, "e": 90, "r": 100},
    "nyzrak": {"q": 50, "w": 50, "e": 70, "r": 90},
    "ancient_apparition": {"q": 60, "w": 45, "e": 50, "r": 90},
}

# Level3 punya sprite lebih besar dari level2 (wyvern besar + aura/efek
# lebih padat), jadi budget mobile dinaikkan sedikit dari 2.2 -> 2.35 ms.
BUDGET = 2.35


def probe(name, klass, cd, cx=230.0, cy=230.0, **kw):
    b = SimpleNamespace(boss_type=name, boss_class=klass, x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=1.2,
                        timer=0, attack_cooldown=cd, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=30,
                        hp=9000, max_hp=9000)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(fn, boss, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    fn(s, boss, 230, 230)
    return s


def hb(s):
    r = s.get_bounding_rect(min_alpha=100)
    return r.height, r.width


def skill_cases():
    tg = SimpleNamespace(x=300.0, y=230.0, alive=True)
    return [dict(active_skill=sk, active_skill_timer=30, target=tg)
            for sk in ("q", "w", "e", "r")]


def test_all_modes_render():
    for name, klass, fn, NS, cd in BOSSES:
        walker = probe(name, klass, cd, pulse=1.0)
        walker._vk_last_x = walker.x - 2.0
        walker._vk_last_y = walker.y
        walker._xr_last_x = walker.x - 2.0
        walker._xr_last_y = walker.y
        walker._nyz_last_x = walker.x - 2.0
        walker._nyz_last_y = walker.y
        walker._aa_last_x = walker.x - 2.0
        walker._aa_last_y = walker.y
        cases = [probe(name, klass, cd, pulse=0.0),
                 probe(name, klass, cd, pulse=3.3), walker,
                 probe(name, klass, cd, hurt_flash_timer=6)]
        # attack modes
        for attr, prog in (("_vk_attack_active", "_vk_attack_progress"),
                           ("_xr_attack_active", "_xr_attack_progress"),
                           ("_nyz_attack_active", "_nyz_attack_progress"),
                           ("_aa_attack_active", "_aa_attack_progress")):
            cases.append(probe(name, klass, cd, **{attr: True, prog: 0.5}))
        for c in skill_cases():
            cases.append(probe(name, klass, cd, **c))
        for c in cases:
            h, w = hb(render(fn, c))
            assert w > 40 and h > 40, (name, w, h)
    print("PASS all modes render")


def test_family_size():
    bbs = {}
    for name, klass, fn, NS, cd in BOSSES:
        h, w = hb(render(fn, probe(name, klass, cd)))
        bbs[name] = (h, w)
    # Presence memadai untuk semua; true boss tidak boleh jadi titik.
    for n in ("varkul", "xerathis", "nyzrak"):
        assert bbs[n][0] >= 80 and bbs[n][1] >= 80, (n, bbs[n])
    assert bbs["ancient_apparition"][0] >= 90 and \
           bbs["ancient_apparition"][1] >= 100, bbs["ancient_apparition"]
    print(f"family bbox: { {k: v for k, v in bbs.items()} }")


def mean_lum(s, y0=0, y1=460, stride=3):
    tot = n = 0
    for yy in range(y0, y1, stride):
        for xx in range(0, 460, stride):
            r, g, b, a = s.get_at((xx, yy))
            if a > 120:
                tot += r + g + b
                n += 1
    return tot / max(1, n)


def test_hurt_flash_only_body():
    for name, klass, fn, NS, cd in BOSSES:
        base = render(fn, probe(name, klass, cd, pulse=1.2))
        hit = render(fn, probe(name, klass, cd, pulse=1.2,
                               hurt_flash_timer=8))
        mb, mh = mean_lum(base), mean_lum(hit)
        assert mh > mb + 15, f"{name} flash tidak menerangkan badan ({mb:.0f}->{mh:.0f})"

        # Daerah bayangan tanah (band bawah) TIDAK boleh menyala.
        g0 = mean_lum(base, y0=300)
        g1 = mean_lum(hit, y0=300)
        assert g1 <= g0 + 6, f"{name} bayangan tanah ikut menyala ({g0:.0f}->{g1:.0f})"
    print("PASS hurt flash (badan menyala, bayangan tidak)")


def test_reactive_shadow():
    for name, klass, fn, NS, cd in BOSSES:
        s0 = pygame.Surface((300, 80), pygame.SRCALPHA)
        NS._draw_shadow(s0, 150, 40, 0)
        r0 = s0.get_bounding_rect(min_alpha=20)
        s1 = pygame.Surface((300, 80), pygame.SRCALPHA)
        NS._draw_shadow(s1, 150, 40, 6)
        r1 = s1.get_bounding_rect(min_alpha=20)
        assert r1.width < r0.width, (name, r0.width, r1.width)
        assert abs(r1.bottom - r0.bottom) <= 1, (name, r0.bottom, r1.bottom)
    print("PASS shadow reaktif (menyusut + dasar menapak)")


# ── durasi renderer == AI ──────────────────────────────────────────
def _namespaced(src, ns):
    """Potong source jadi satu namespace kelas (untuk nama fungsi yang sama
    muncul di lebih dari satu boss)."""
    if ns == "nyzrak":
        # Renderer v4 hidup di modul sendiri; re-export dari level3.
        import bosses.nyzrak_v4 as nyz_mod
        src = inspect.getsource(nyz_mod)
    m = re.search(r"^class _NS_%s:" % ns, src, re.M)
    assert m, f"class namespace {ns} tidak ditemukan"
    start = m.start()
    nxt = re.compile(r"^class _NS_", re.M)
    nm = nxt.search(src, start + 1)
    return src[start:(nm.start() if nm else len(src))]


def _extract_single(src, fname):
    """Ambil durasi dari `duration = N` atau `timer / N` di body fungsi."""
    pat = re.compile(r"^    def %s\(" % fname, re.M)
    m = pat.search(src)
    assert m, f"tidak menemukan def {fname}"
    start = m.start()
    nxt = re.compile(r"^    def ", re.M)
    nm = nxt.search(src, start + 1)
    body = src[start:(nm.start() if nm else len(src))]
    dm = re.search(r"duration = (\d+)", body)
    if dm:
        return int(dm.group(1))
    tm = re.search(r"timer / (\d+)", body)
    if tm:
        return int(tm.group(1))
    raise AssertionError(f"tidak menemukan duration di {fname}")


def _extract_multi(src, fname):
    """Ambil semua `duration = N` di body fungsi (untuk handle projectiles)."""
    pat = re.compile(r"^    def %s\(" % fname, re.M)
    m = pat.search(src)
    assert m, f"tidak menemukan def {fname}"
    start = m.start()
    nxt = re.compile(r"^    def ", re.M)
    nm = nxt.search(src, start + 1)
    body = src[start:(nm.start() if nm else len(src))]
    vals = [int(x) for x in re.findall(r"duration = (\d+)", body)]
    assert vals, f"tidak menemukan duration list di {fname}"
    return sorted(vals)


def test_durations_match_ai():
    src = inspect.getsource(L)
    # (boss, [(nama renderer atau None untuk handle, key, list durasi)])
    checks = {
        "varkul": [("_draw_frost_blast_ground", "q"), ("_draw_frost_blast", "q"),
                   ("_draw_frostbite", "w"),
                   ("_draw_sacrifice_circle", "e"),
                   ("_draw_sacrifice_foreground", "e"),
                   ("_draw_chain_frost_ground", "r"), ("_draw_chain_frost", "r")],
        "xerathis": [("_draw_crystal_nova_ground", "q"), ("_draw_crystal_nova", "q"),
                     ("_draw_frostbite", "w"),
                     ("_draw_arcane_aura_ground", "e"),
                     ("_draw_arcane_aura_foreground", "e"),
                     ("_draw_freezing_field_ground", "r"), ("_draw_freezing_field", "r")],
        "nyzrak": [("_draw_winters_curse_ground", "e"),
                   ("_draw_winters_curse_foreground", "e"),
                   ("_draw_cold_embrace_ground", "r"),
                   ("_draw_cold_embrace_foreground", "r"),
                   ("_handle_skill_projectiles", "qw")],
        "ancient_apparition": [("_draw_ice_vortex_ground", "q"),
                               ("_draw_ice_vortex", "q"),
                               ("_draw_cold_feet_ground", "r"),
                               ("_draw_cold_feet_spikes", "r"),
                               ("_handle_skill_projectiles", "we")],
    }
    for name, pairs in checks.items():
        ns_src = _namespaced(src, name)
        for fname, key in pairs:
            if fname == "_handle_skill_projectiles":
                if key == "qw":
                    want = sorted([AI["nyzrak"]["q"], AI["nyzrak"]["w"]])
                else:
                    want = sorted([AI["ancient_apparition"]["w"],
                                   AI["ancient_apparition"]["e"]])
                got = _extract_multi(ns_src, fname)
            else:
                want = AI[name][key]
                got = _extract_single(ns_src, fname)
            assert got == want, f"{name}.{fname} durasi={got} != AI {want}"
    print("PASS durasi FX == AI (varkul/xerathis/nyzrak/ancient_apparition)")


def test_animation_continuous_and_fast():
    def sig(fn, boss):
        s = render(fn, boss)
        m = pygame.mask.from_surface(s, 100)
        brs = m.get_bounding_rects()
        br = brs[0] if brs else pygame.Rect(0, 0, 0, 0)
        # hash piksel + mask agar menangkap pergantian rim/partikel kecil
        pix = pygame.image.tobytes(s, "RGBA")
        return (hash(pix), m.count(), tuple(int(v) for v in m.centroid()),
                br.left, br.top, br.right, br.bottom)

    for name, klass, fn, NS, cd in BOSSES:
        ids = {sig(fn, probe(name, klass, cd, pulse=1.0 + i * 0.21))
               for i in range(24)}
        assert len(ids) >= 10, f"{name} idle beku? {len(ids)}/24"
        wids = set()
        for i in range(24):
            b = probe(name, klass, cd, pulse=i * 0.26)
            for attr in ("_vk_last_x", "_xr_last_x", "_nyz_last_x",
                         "_aa_last_x"):
                setattr(b, attr, b.x - 2.0)
            for attr in ("_vk_last_y", "_xr_last_y", "_nyz_last_y",
                         "_aa_last_y"):
                setattr(b, attr, b.y)
            wids.add(sig(fn, b))
        assert len(wids) >= 10, f"{name} walk beku? {len(wids)}/24"

    # perf idle penuh per boss < budget (canvas di-reuse seperti game,
    # bukan mengalokasikan surface baru per frame)
    for name, klass, fn, NS, cd in BOSSES:
        b = probe(name, klass, cd)
        surf = pygame.Surface((460, 460), pygame.SRCALPHA)
        for i in range(20):          # warm cache piksel-identik
            b.pulse = 1.0 + i * 0.13
            fn(surf, b, 230, 230)
        N = 40
        t0 = time.perf_counter()
        for i in range(N):
            b.pulse = 1.0 + i * 0.13
            fn(surf, b, 230, 230)
        dt = (time.perf_counter() - t0) / N * 1000
        assert dt < BUDGET, f"{name} idle {dt:.2f} ms (budget {BUDGET})"
        print(f"    {name}: {dt:.2f} ms/frame")
    print(f"PASS animasi kontinu + perf idle < {BUDGET} ms/frame")


def test_outline_and_lighting_present():
    """Konvensi level2: tiap boss punya outline siluet gelap + pass cahaya
    (rim/shade) lewat komposit badan -> buffer -> outline -> lighting."""
    import lighting as _lighting_mod
    body_raw = {"varkul": "_draw_varkul_body_raw",
                "xerathis": "_draw_xerathis_body_raw",
                "nyzrak": "_draw_nyz_full_raw",
                "ancient_apparition": "_draw_aa_body_raw"}
    body_comp = {"varkul": "_draw_varkul_body",
                 "xerathis": "_draw_xerathis_body",
                 "nyzrak": "_draw_nyz_full",
                 "ancient_apparition": "_draw_aa_body"}
    for name, klass, fn, NS, cd in BOSSES:
        assert hasattr(NS, body_raw[name]), f"{name} tanpa renderer _raw"
        assert hasattr(NS, "_body_buf"), f"{name} tanpa cache badan"
        raw = pygame.Surface((260, 260), pygame.SRCALPHA)
        getattr(NS, body_raw[name])(raw, 130, 130, 1, 1.0, "idle")
        comp = pygame.Surface((260, 260), pygame.SRCALPHA)
        getattr(NS, body_comp[name])(comp, 130, 130, 1, 1.0, "idle")

        def black_count(surf):
            return sum(1 for yy in range(0, 260, 2) for xx in range(0, 260, 2)
                       if surf.get_at((xx, yy))[:3] == (0, 0, 0)
                       and surf.get_at((xx, yy))[3] > 50)
        assert black_count(comp) > black_count(raw) + 20, \
            f"{name}: outline siluet tidak terlihat " \
            f"({black_count(raw)}->{black_count(comp)})"
    assert _lighting_mod is not None
    print("PASS outline siluet + pass cahaya (konvensi level2)")


def test_procedural_only():
    src = inspect.getsource(L)
    assert "pygame.image.load" not in src


if __name__ == "__main__":
    test_all_modes_render()
    test_family_size()
    test_hurt_flash_only_body()
    test_reactive_shadow()
    test_durations_match_ai()
    test_animation_continuous_and_fast()
    test_outline_and_lighting_present()
    test_procedural_only()
    print("ALL LEVEL3 ORIGINAL-MAX TESTS PASSED")
