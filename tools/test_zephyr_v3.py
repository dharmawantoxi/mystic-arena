#!/usr/bin/env python3
"""Regression test permanen untuk sistem tempur ZEPHYR v3.

Mengunci kontrak yang gampang rusak saat orang lain menyentuh
``heroes/zephyr_fx.py`` atau ``_NS_zephyr`` di ``heroes/_bundle.py``:

  * palet + API publik (backward-compat untuk pemanggil lama)
  * animation controller ayunan (fase, urutan, jendela hit, busur)
  * particle system berbatas (cap dihormati, pool dipakai ulang, meluruh)
  * lifecycle projectile penuh (spawn -> travel -> hit -> impact -> mati)
  * impact FX + screen shake + hit-stop yang selalu terkuras
  * lifecycle skill FX (cast -> charge -> release -> area -> impact -> fade)
  * surface cache berbatas & performa layer FX
  * tidak ada asset eksternal yang dimuat

Jalankan:  python3 -m pytest tools/test_zephyr_v3.py -q
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import math                                                    # noqa: E402
import pygame                                                  # noqa: E402
import pytest                                                  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                                  # noqa: E402
from heroes import _ProbeEntity                                # noqa: E402
from heroes._bundle import _NS_zephyr as Z                     # noqa: E402
from heroes import zephyr_fx as F                              # noqa: E402

DT = 1.0 / 60.0


# ── helper ────────────────────────────────────────────────────────────────
def fresh_hero(x=0.0, y=0.0, cooldown=30):
    h = _ProbeEntity("zephyr", x, y)
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = cooldown
    h.range = 130
    h.speed = 1.6
    return h


def dummy_target(x=180.0, y=0.0):
    t = _ProbeEntity("zephyr", x, y)
    t.alive = True
    t.radius = 14
    return t


def run_attack(hero, cooldown=30):
    """Putar satu siklus serangan penuh, kembalikan daftar snapshot."""
    out = []
    hero.timer = 0
    Z._update_attack_anim(hero)
    for t in range(cooldown, -1, -1):
        hero.timer = t
        Z._update_attack_anim(hero)
        out.append({
            "timer": t,
            "phase": hero._zp_attack_phase,
            "state": hero._zp_state,
            "p": hero._zp_attack_progress,
            "hit": bool(getattr(hero, "_zp_hit_active", False)),
        })
    return out


def _reset_fx():
    F.HITSTOP.frames = 0
    F.HITSTOP.total = 0
    F.SHAKE.shake_strength = 0.0
    F.SHAKE.shake_duration = 0.0
    F.SHAKE._max_duration = 0.0001


@pytest.fixture(autouse=True)
def _clean_fx():
    """Setiap test mulai dari screen-shake + hit-stop kosong."""
    _reset_fx()
    yield
    _reset_fx()


# ══════════════════════════════════════════════════════════════════════════
# 1. PALET & API PUBLIK
# ══════════════════════════════════════════════════════════════════════════
def test_palette_lengkap():
    pal = F.ZEPHYR_PALETTE
    for key in ("outline", "shadow", "dark", "body", "mid",
                "light", "highlight", "weapon", "fx"):
        assert key in pal, "kunci palet hilang: %s" % key
        col = pal[key]
        assert len(col) >= 3 and all(0 <= c <= 255 for c in col[:3])


def test_api_publik_ada():
    for name in ("draw_bolt", "should_freeze_frame",
                 "notify_projectile_impact", "director_for",
                 "glow_surface", "ground_glow_surface", "ring_surface",
                 "ellipse_ring_surface", "spark_surface", "cache_size",
                 "ParticleSystem", "ProjectileSystem", "SkillFX",
                 "ImpactFX", "SHAKE", "HITSTOP"):
        assert hasattr(F, name), "API hilang: zephyr_fx.%s" % name


def test_debug_toggle_default_mati():
    from heroes import _bundle
    assert _bundle._NS_zephyr.DEBUG_CHARACTER is False


def test_tidak_memuat_asset_eksternal():
    """100% prosedural: tak ada image.load / font.Font(path) / open()."""
    src = open(os.path.join(ROOT, "heroes", "zephyr_fx.py"),
               encoding="utf-8").read()
    for bad in ("pygame.image.load", "image.load(", "pygame.mixer.Sound",
                "pygame.font.Font(\"", "pygame.font.Font('",
                ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ogg", ".wav"):
        assert bad not in src, "referensi asset eksternal: %s" % bad


# ══════════════════════════════════════════════════════════════════════════
# 2. ANIMATION CONTROLLER — AYUNAN
# ══════════════════════════════════════════════════════════════════════════
def test_urutan_fase_ayunan():
    seq = [s["phase"] for s in run_attack(fresh_hero())]
    order = []
    for p in seq:
        if not order or order[-1] != p:
            order.append(p)
    expect = ["ANTICIPATION", "WINDUP", "SWING",
              "IMPACT", "FOLLOW", "RECOVERY", "NONE"]
    assert order == expect, order


def test_progress_monoton_naik():
    snaps = [s for s in run_attack(fresh_hero()) if s["timer"] > 0]
    ps = [s["p"] for s in snaps]
    assert ps[0] == pytest.approx(0.0, abs=1e-6)
    assert ps[-1] == pytest.approx(1.0, abs=1e-6)
    assert all(b >= a - 1e-9 for a, b in zip(ps, ps[1:])), ps


def test_jendela_hit_aktif_dan_tertutup():
    snaps = run_attack(fresh_hero())
    hit = [s["p"] for s in snaps if s["hit"]]
    assert hit, "jendela hit tidak pernah aktif"
    assert 0.30 <= min(hit) <= 0.50, min(hit)
    assert 0.50 <= max(hit) <= 0.70, max(hit)
    # tertutup lagi sebelum recovery selesai
    assert not snaps[-1]["hit"]
    assert not snaps[-2]["hit"]


def test_state_animasi_dipetakan():
    states = {s["state"] for s in run_attack(fresh_hero())}
    assert "SWING" in states
    assert "IDLE" in states
    assert states <= {"IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST",
                      "SKILL", "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"}


def test_ayunan_berbasis_busur_bukan_lerp_lurus():
    """Ujung tongkat harus melengkung jauh dari garis lurus start->end."""
    n = 24
    pts = [pygame.Vector2(Z._staff_tip_local(0.0, "attack", i / float(n)))
           for i in range(n + 1)]
    a, b = pts[0], pts[-1]
    worst = 0.0
    for i, p in enumerate(pts):
        worst = max(worst, (p - a.lerp(b, i / float(n))).length())
    assert worst > 20.0, "deviasi busur hanya %.1f px" % worst


def test_ujung_tongkat_bergerak_kontinu():
    """Tidak boleh ada lompatan teleport antar frame ayunan."""
    n = 60
    pts = [pygame.Vector2(Z._staff_tip_local(0.0, "attack", i / float(n)))
           for i in range(n + 1)]
    steps = [(b - a).length() for a, b in zip(pts, pts[1:])]
    assert max(steps) < 14.0, "lompatan %.1f px antar frame" % max(steps)
    assert sum(steps) > 60.0, "ujung tongkat nyaris tidak bergerak"


# ── SKELETON LENGAN (regresi "tangan melar" saat menyerang) ───────────────
def _arm_samples(action="attack", n=60):
    return [Z._arm_pose_local(0.0, action, i / float(n))
            for i in range(n + 1)]


@pytest.mark.parametrize("action", ["idle", "walk", "attack"])
def test_panjang_lengan_konstan(action):
    """Bug lama: tangan diambil dari ujung tongkat -> lengan melar 2-3x."""
    up = Z.ARM_UPPER
    fore = Z.ARM_FORE
    tol = 1.6                       # toleransi pembulatan ke piksel
    for fs, fe, fh, rs, re_, rh, _t in _arm_samples(action):
        for sh, el, hd, tag in ((fs, fe, fh, "depan"), (rs, re_, rh, "blkg")):
            l1 = math.dist(sh, el)
            l2 = math.dist(el, hd)
            assert abs(l1 - up) <= tol, \
                "%s: lengan atas %.1f px (harus %.1f)" % (tag, l1, up)
            assert abs(l2 - fore) <= tol, \
                "%s: lengan bawah %.1f px (harus %.1f)" % (tag, l2, fore)


def test_tangan_tidak_pernah_di_luar_jangkauan():
    for fs, _fe, fh, rs, _re, rh, _t in _arm_samples("attack"):
        assert math.dist(fs, fh) <= Z.ARM_REACH + 1.5, math.dist(fs, fh)
        assert math.dist(rs, rh) <= Z.ARM_REACH + 1.5, math.dist(rs, rh)


def test_tangan_menempel_di_batang_tongkat():
    """Tangan wajib berada pada garis pangkal->ujung tongkat."""
    n = 40
    for i in range(n + 1):
        ap = i / float(n)
        b = pygame.Vector2(Z._staff_bottom_local(0.0, "attack", ap))
        t = pygame.Vector2(Z._staff_tip_local(0.0, "attack", ap))
        axis = t - b
        if axis.length() < 1e-3:
            continue
        axis = axis.normalize()
        fs, _fe, fh, rs, _re, rh, _gt = Z._arm_pose_local(0.0, "attack", ap)
        for hd, tag in ((fh, "depan"), (rh, "belakang")):
            v = pygame.Vector2(hd) - b
            perp = abs(v.x * axis.y - v.y * axis.x)     # jarak tegak lurus
            assert perp <= 3.0, \
                "tangan %s melayang %.1f px dari batang (ap %.2f)" % (
                    tag, perp, ap)


def test_pose_lengan_kontinu_tanpa_lompatan():
    pts = _arm_samples("attack", n=90)
    for a, b in zip(pts, pts[1:]):
        for ia in (1, 2, 4, 5):     # elbow/hand depan & belakang
            step = math.dist(a[ia], b[ia])
            assert step < 9.0, "sendi lompat %.1f px antar frame" % step


def test_genggaman_bergerak_sepanjang_ayunan():
    """Tangan harus ikut menyusuri batang, bukan diam menempel di badan."""
    hands = [p[2] for p in _arm_samples("attack")]
    xs = [h[0] for h in hands]
    assert max(xs) - min(xs) > 8, "tangan depan nyaris tidak bergerak"


def test_cooldown_pendek_tetap_melewati_semua_fase():
    for cd in (8, 12, 45, 90):
        phases = {s["phase"] for s in run_attack(fresh_hero(cooldown=cd), cd)}
        for need in ("WINDUP", "SWING", "RECOVERY"):
            assert need in phases, "cooldown %d kehilangan %s" % (cd, need)


# ══════════════════════════════════════════════════════════════════════════
# 3. PARTICLE SYSTEM — BERBATAS
# ══════════════════════════════════════════════════════════════════════════
def test_particle_cap_dihormati():
    ps = F.ParticleSystem(cap=40)
    for _ in range(50):
        ps.burst(0, 0, 30)
    assert ps.count() <= 40, ps.count()


def test_particle_meluruh_ke_nol():
    ps = F.ParticleSystem(cap=40)
    ps.burst(0, 0, 40)
    for _ in range(600):
        ps.update(DT)
        if ps.count() == 0:
            break
    assert ps.count() == 0, "partikel tidak pernah mati (%d)" % ps.count()


def test_particle_pool_dipakai_ulang():
    ps = F.ParticleSystem(cap=40)
    ps.burst(0, 0, 40)
    for _ in range(600):
        ps.update(DT)
        if ps.count() == 0:
            break
    assert len(ps._pool) > 0, "pool kosong -> alokasi ulang tiap burst"


def test_particle_draw_tidak_meledak():
    ps = F.ParticleSystem(cap=40)
    ps.burst(0, 0, 40)
    surf = pygame.Surface((160, 160))
    for _ in range(30):
        ps.update(DT)
        ps.draw(surf, layer="ground")
        ps.draw(surf, layer="front")


# ══════════════════════════════════════════════════════════════════════════
# 4. PROJECTILE — LIFECYCLE PENUH
# ══════════════════════════════════════════════════════════════════════════
def test_projectile_spawn_travel_hit():
    sysm = F.ProjectileSystem(F.ParticleSystem(cap=60))
    tgt = dummy_target(180, 0)
    p = sysm.spawn(0, 0, tgt.x, tgt.y, target=tgt, damage=12, speed=420.0)
    assert p.active and p.state == p.STATE_TRAVEL
    start = pygame.Vector2(p.position)
    moved = False
    saw_impact = False
    for _ in range(240):
        sysm.update(DT)
        if p.position.distance_to(start) > 4:
            moved = True
        if p.state == p.STATE_IMPACT:
            saw_impact = True
        if not p.active:
            break
    assert saw_impact, "projectile tidak pernah masuk fase IMPACT"
    assert moved, "projectile tidak pernah bergerak"
    assert not p.active, "projectile tidak pernah mati (tak ada lifetime?)"


def test_projectile_mati_karena_lifetime_tanpa_target():
    sysm = F.ProjectileSystem(F.ParticleSystem(cap=60))
    p = sysm.spawn(0, 0, 10000, 0, target=None, damage=5, speed=420.0)
    for _ in range(2000):
        sysm.update(DT)
        if not p.active:
            break
    assert not p.active, "lifetime tidak menghentikan projectile"
    assert len(sysm.projectiles) == 0


def test_projectile_homing_membelokkan_kecepatan():
    sysm = F.ProjectileSystem(F.ParticleSystem(cap=60))
    tgt = dummy_target(200, 0)
    p = sysm.spawn(0, 0, 200, 0, target=tgt, damage=5, speed=300.0)
    tgt.y = 160                                  # target kabur ke bawah
    for _ in range(20):
        sysm.update(DT)
        if p.state != p.STATE_TRAVEL:
            break
    assert p.velocity.y > 5.0, "tidak ada homing (vy=%.2f)" % p.velocity.y


def test_projectile_menghasilkan_trail_dan_partikel():
    parts = F.ParticleSystem(cap=60)
    sysm = F.ProjectileSystem(parts)
    tgt = dummy_target(300, 0)
    p = sysm.spawn(0, 0, 900, 0, target=tgt, damage=5, speed=300.0)
    for _ in range(20):
        sysm.update(DT)
    assert len(p.trail) >= 3, "trail projectile kosong"
    assert parts.count() > 0, "projectile tidak memuntahkan partikel"


def test_draw_bolt_menggambar_sesuatu():
    for crit in (False, True):
        surf = pygame.Surface((80, 80))
        surf.fill((0, 0, 0))
        F.draw_bolt(surf, 40, 40, angle=0.6, age=7, crit=crit)
        assert pygame.transform.average_color(surf)[:3] != (0, 0, 0), \
            "draw_bolt(crit=%s) tidak menggambar apa-apa" % crit


def test_draw_bolt_bukan_lingkaran_polos():
    """Bolt harus punya arah: bounding box tidak boleh (nyaris) bujursangkar."""
    def box_for(angle):
        surf = pygame.Surface((160, 160), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        F.draw_bolt(surf, 80, 80, angle=angle, age=6, crit=False)
        rect = surf.get_bounding_rect(min_alpha=24)
        assert rect.width > 4, "tidak ada piksel bolt"
        return rect

    flat = box_for(0.0)
    tall = box_for(math.pi / 2.0)
    assert flat.width > flat.height * 1.25, \
        "bolt horizontal tampak bulat (%dx%d)" % (flat.width, flat.height)
    assert tall.height > tall.width * 1.25, \
        "bolt vertikal tampak bulat (%dx%d)" % (tall.width, tall.height)


# ══════════════════════════════════════════════════════════════════════════
# 5. IMPACT / SCREEN SHAKE / HIT-STOP
# ══════════════════════════════════════════════════════════════════════════
def test_impact_fx_selesai():
    fx = F.ImpactFX(50, 50, angle=0.6, power=1.2, crit=False)
    surf = pygame.Surface((120, 120))
    frames = 0
    while fx.active and frames < 300:
        fx.update(DT)
        fx.draw(surf)
        frames += 1
    assert not fx.active, "ImpactFX tidak pernah selesai"
    assert frames < 120, "ImpactFX terlalu panjang (%d frame)" % frames


def test_screen_shake_meluruh_ke_nol():
    F.SHAKE.add(10.0, 0.35)
    assert F.SHAKE.amount > 0
    for _ in range(300):
        F.SHAKE.update(DT)
        if F.SHAKE.amount <= 0.01:
            break
    assert F.SHAKE.amount <= 0.01, F.SHAKE.amount


def test_hitstop_diklem_dan_selalu_terkuras():
    # durasi diminta besar -> tetap diklem ke jendela ~0.03-0.08 s
    F.HITSTOP.frames = 0
    F.HITSTOP.trigger(5.0)   # diminta 5 detik
    assert 1 <= F.HITSTOP.frames <= 5, F.HITSTOP.frames
    drained = 0
    while F.HITSTOP.active and drained < 30:
        F.should_freeze_frame()
        drained += 1
    assert not F.HITSTOP.active, "hit-stop tidak pernah selesai"
    assert drained <= 5, drained


def test_hitstop_minimum_dua_frame():
    F.HITSTOP.frames = 0
    F.HITSTOP.trigger(0.0001)
    assert F.HITSTOP.frames >= 2, F.HITSTOP.frames


def test_notify_projectile_impact_memicu_fx():
    hero = fresh_hero()
    d = F.director_for(hero)
    d.impacts.clear()
    _reset_fx()
    F.notify_projectile_impact(hero, 40, 40, damage=25, crit=True)
    assert len(d.impacts) >= 1, "tidak ada ImpactFX yang dibuat"
    assert F.SHAKE.amount > 0, "impact tidak menggoyang layar"


# ══════════════════════════════════════════════════════════════════════════
# 6. SKILL FX — LIFECYCLE
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("kind", ["q", "w", "e", "r"])
def test_skillfx_lifecycle_lengkap(kind):
    parts = F.ParticleSystem(cap=60)
    fx = F.SkillFX(kind, 60, 60, parts)
    surf = pygame.Surface((140, 140))
    seen = []
    frames = 0
    while fx.active and frames < 600:
        fx.update(DT)
        fx.draw_ground(surf)
        fx.draw_front(surf)
        if not seen or seen[-1] != fx.phase:
            seen.append(fx.phase)
        frames += 1
    assert not fx.active, "SkillFX %s tidak pernah selesai" % kind
    for need in ("charge", "release", "area", "impact", "fade"):
        assert need in seen, "skill %s kehilangan fase %s (%s)" % (
            kind, need, seen)
    assert frames < 400, "skill %s kelamaan (%d frame)" % (kind, frames)


def test_skillfx_tiap_skill_punya_warna_berbeda():
    tints = {k: F.SkillFX.TINT[k] for k in ("q", "w", "e", "r")}
    assert len(set(tints.values())) == 4, tints


# ══════════════════════════════════════════════════════════════════════════
# 7. DIRECTOR / INTEGRASI
# ══════════════════════════════════════════════════════════════════════════
def test_director_stabil_satu_instance_per_hero():
    hero = fresh_hero()
    assert F.director_for(hero) is F.director_for(hero)


def test_director_frame_penuh_tanpa_exception():
    hero = fresh_hero(120, 140)
    tgt = dummy_target(260, 136)
    hero.target = tgt
    d = F.director_for(hero)
    d.on_cast(hero.x, hero.y, "q")
    d.on_hurt(18)
    d.projectiles.spawn(hero.x, hero.y, tgt.x, tgt.y, target=tgt, damage=9)
    F.notify_projectile_impact(hero, tgt.x, tgt.y, damage=9, crit=False)
    surf = pygame.Surface((420, 300))
    seq = [0] * 2 + list(range(30, 0, -1))
    for i in range(180):
        hero.attack_timer = hero.timer = seq[i % len(seq)]
        hero.pulse += 0.06
        Z._update_attack_anim(hero)
        d.update(DT)
        surf.fill((16, 20, 18))
        d.draw_ground(surf)
        heroes.render_hero("zephyr", surf, hero, 120, 140)
        d.draw_front(surf)
    st = d.stats()
    assert st["particles"] <= 200, st
    assert isinstance(st, dict)


def test_render_hero_tetap_jalan_dengan_debug_on():
    from heroes import _bundle
    hero = fresh_hero(100, 120)
    hero.timer = 16
    Z._update_attack_anim(hero)
    surf = pygame.Surface((300, 240))
    old = _bundle._NS_zephyr.DEBUG_CHARACTER
    try:
        _bundle._NS_zephyr.DEBUG_CHARACTER = True
        heroes._hero_sprite_cache.clear()
        heroes.render_hero("zephyr", surf, hero, 100, 120)
    finally:
        _bundle._NS_zephyr.DEBUG_CHARACTER = old
        heroes._hero_sprite_cache.clear()


# ══════════════════════════════════════════════════════════════════════════
# 8. PERFORMA / CACHE
# ══════════════════════════════════════════════════════════════════════════
def test_surface_cache_tidak_tumbuh_tanpa_batas():
    before = F.cache_size()
    surf = pygame.Surface((200, 200))
    for i in range(400):
        F.glow_surface(8 + (i % 4) * 4, F.P["fx_mid"], 0.5)
        F.ring_surface(10 + (i % 3) * 3, 2, F.P["fx_light"], 180)
        F.spark_surface(4 + (i % 2) * 2, F.P["fx_hot"])
    grown = F.cache_size() - before
    assert grown < 60, "cache thrashing (+%d entri)" % grown
    assert F.cache_size() <= F._SURF_CACHE_MAX
    surf.fill((0, 0, 0))


def test_layer_fx_dalam_budget_waktu():
    hero = fresh_hero(200, 160)
    tgt = dummy_target(360, 156)
    hero.target = tgt
    d = F.director_for(hero)
    d.on_cast(200, 160, "r")
    d.particles.burst(200, 160, 40)
    d.projectiles.spawn(hero.x, hero.y, tgt.x, tgt.y, target=tgt, damage=9)
    F.notify_projectile_impact(hero, tgt.x, tgt.y, damage=30, crit=True)
    surf = pygame.Surface((640, 480))
    samples = []
    for _ in range(60):
        t0 = time.perf_counter()
        d.update(DT)
        d.draw_ground(surf)
        d.draw_front(surf)
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    median = samples[len(samples) // 2]
    assert median < 3.5, "layer FX %.2f ms (budget 3.5 ms)" % median


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
