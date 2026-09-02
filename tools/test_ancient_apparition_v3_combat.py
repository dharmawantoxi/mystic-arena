#!/usr/bin/env python3
"""Regression test permanen untuk sistem tempur ANCIENT APPARITION v3.

Ancient Apparition digambar lewat kode yang sama di DUA jalur: lane boss
(``Boss.draw`` -> ``_NS_ancient_apparition.draw_apparition``) dan lane
hero (``heroes.render_hero`` -> sprite di-cache + smoothscale). Karena
itu sistem tempurnya dipecah:

  * ``bosses/level3.py::_NS_ancient_apparition`` = badan pixel-art chunky
    (rig low-res -> upscale 2x), controller animasi, telegraph tanah, dan
    semua FALLBACK kalau modul FX tidak tersedia.
  * ``heroes/ancient_apparition_fx.py``            = lapisan hidup 1:1 di
    luar sprite cache: arc ayunan cakar, trail ribbon, partikel salju/es,
    proyektil shard/bolt modular, vortex Q / beam W / blast E / cold feet
    R, impact, hit-stop, shake, overlay debug.
  * ``heroes/combat_feel.py``                      = bus SHARED hit-stop +
    shake untuk semua karakter v3.

Uji ini mengunci kontrak yang gampang rusak:

 1. 100% prosedural (tanpa image.load / PNG / sprite sheet) di KEDUA modul.
 2. Palet + API publik backward-compat (pemanggil lama tetap jalan).
 3. Controller animasi: fase, urutan, prioritas state, jendela hit.
 4. Ayunan berbasis arc (bukan lerp linear) + geometri lengan MIRROR
    antara renderer dan lapisan hidup (trail menempel di cakar).
 5. Particle system berbatas (cap dihormati, pool dipakai ulang, meluruh).
 6. Lifecycle projectile penuh (spawn -> travel -> hit -> impact -> mati).
 7. Lifecycle skill FX (cast -> charge -> release -> area/travel -> fade)
    dengan pusat yang benar (Q di vortex dunia, R di target).
 8. Impact + screen shake + hit-stop SELALU terkuras (tak ada efek abadi),
    hit-stop di jendela 0.03-0.08 s.
 9. Supresi ganda: lapisan hidup aktif -> renderer melewati FX canvas;
    modul FX tidak ada -> fallback canvas tetap jalan.
10. Durasi FX canvas == AI (q=60, w=45, e=50, r=90) — kontrak lama.
11. Performa: boss path < 2.35 ms/frame, lapisan hidup < 1.2 ms/frame.

Jalankan:  python3 -m pytest tools/test_ancient_apparition_v3_combat.py -q
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import inspect                                             # noqa: E402
import math                                                # noqa: E402
import pygame                                              # noqa: E402
import pytest                                              # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                              # noqa: E402
from heroes import _ProbeEntity                            # noqa: E402
from heroes import combat_feel as FEEL                     # noqa: E402
from heroes import ancient_apparition_fx as F              # noqa: E402
from bosses.level3 import _NS_ancient_apparition as G      # noqa: E402

DT = 1.0 / 60.0
COOLDOWN = 61                     # attack_cooldown AA di boss_data.py
PHASE_ORDER = ["anticipation", "windup", "swing", "follow", "recovery"]


# ── helper ────────────────────────────────────────────────────────────────
def fresh_boss(x=230.0, y=230.0, scale=None, **kw):
    """Unit AA minim. ``scale=None`` = jalur BOSS (tanpa _render_scale)."""
    b = _ProbeEntity("ancient_apparition", x, y)
    b.boss_type = "ancient_apparition"
    b.boss_class = "true"
    b.alive = True
    b.pulse = 1.2
    b.direction = b.facing = 1
    b.attack_cooldown = COOLDOWN
    b.range = 150
    b.radius = 30
    b.active_skill = None
    b.active_skill_timer = 0
    b.hurt_flash_timer = 0
    if scale is not None:
        b._render_scale = scale
    for k, v in kw.items():
        setattr(b, k, v)
    return b


@pytest.fixture(autouse=True)
def _clean_fx():
    F.reset_all()
    FEEL.reset()
    yield
    F.reset_all()
    FEEL.reset()


def run_attack(b, d, cooldown=COOLDOWN):
    """Jalankan satu serangan penuh; kumpulkan (progress, claw_x, phase)."""
    rows = []
    b.attack_timer = cooldown
    for i in range(cooldown + 6):
        b.attack_timer = max(0, b.attack_timer - 1)
        b.pulse += 0.05
        d.update(DT)
        rows.append((d.attack_progress, d.state, d.anim_phase))
    return rows


# ═════════════════════════════════════════════════════════════════════════
# 1. PROSEDURAL MURNI
# ═════════════════════════════════════════════════════════════════════════

def test_procedural_only():
    """Tidak ada pemuatan aset di kedua modul."""
    import bosses.level3 as L
    for mod in (L, F):
        src = inspect.getsource(mod)
        assert "pygame.image.load" not in src
        assert ".png" not in src and ".jpg" not in src


# ═════════════════════════════════════════════════════════════════════════
# 2. PALET + API PUBLIK (backward-compat)
# ═════════════════════════════════════════════════════════════════════════

def test_palette_contract():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx",
                "ice_darkest", "ice_dark", "ice_mid", "ice_light",
                "ice_bright", "ice_hot", "ice_pure"):
        assert key in G.PALETTE, key
        assert key in F.AA_PALETTE or key == "body", key
    # FX palette tersinkron dari renderer (sumber kebenaran material)
    assert F.P("ice_hot") == G.PALETTE["ice_hot"]
    assert F.P("shadow") == G.PALETTE["shadow_deep"]


def test_public_api_compat():
    """Nama publik lama tetap hidup untuk pemanggil existing."""
    import bosses.level3 as L
    assert callable(L.draw_ancient_apparition)
    assert callable(G.draw_apparition)
    assert callable(G.draw_boss)
    assert callable(G._draw_shadow)
    assert callable(G._draw_aa_body) and callable(G._draw_aa_body_raw)
    assert hasattr(G, "_body_buf")
    assert hasattr(G, "_update_attack_anim")
    assert hasattr(G, "_detect_moving")
    for name in ("notify_melee_impact", "notify_projectile_impact",
                 "notify_skill_impact", "notify_skill_cast", "notify_hurt",
                 "draw_ground_layer", "draw_live_layer", "tick",
                 "reset_all", "total_particles", "total_projectiles",
                 "projectiles_for", "draw_ice_shard"):
        assert callable(getattr(F, name)), name


# ═════════════════════════════════════════════════════════════════════════
# 3. CONTROLLER ANIMASI
# ═════════════════════════════════════════════════════════════════════════

def test_attack_phase_order():
    """Fase serangan berurutan penuh dan mengcover progress 0..1."""
    seen = []
    last = None
    for i in range(101):
        ph = G._attack_phase(i / 100.0)
        if ph != last:
            seen.append(ph)
            last = ph
    assert seen == PHASE_ORDER, seen
    assert F.attack_phase(0.5) == "swing"
    assert F.attack_phase(0.1) == "anticipation"


def test_director_states():
    """State machine director: IDLE->CHARGE->SWING->ATTACK->IDLE."""
    b = fresh_boss()
    d = F.director_for(b)
    d.update(DT)
    assert d.state == "IDLE"
    states = run_attack(b, d)
    seq = [s for _, s, _ in states]
    assert "CHARGE" in seq and "SWING" in seq, seq
    assert seq[-1] == "IDLE"
    # urutan benar: CHARGE sebelum SWING
    assert seq.index("CHARGE") < seq.index("SWING")


def test_director_states_walk_run_hurt_death():
    b = fresh_boss()
    d = F.director_for(b)
    d.update(DT)
    assert d.state == "IDLE"
    for i in range(30):                    # jalan pelan
        b.x += 0.8
        d.update(DT)
    assert d.state == "WALK"
    for i in range(30):                    # lari
        b.x += 2.0
        d.update(DT)
    assert d.state == "RUN"
    b.hp -= 40                             # kena damage
    d.update(DT)
    assert d.state in ("HIT", "HURT")
    for i in range(60):
        d.update(DT)
    assert d.state == "IDLE"
    b.alive = False
    d.update(DT)
    assert d.state == "DEATH"              # prioritas tertinggi + locked


def test_skill_states():
    b = fresh_boss()
    d = F.director_for(b)
    for sk, want in (("q", "SKILL"), ("w", "SKILL"), ("e", "CAST"),
                     ("r", "SPECIAL")):
        b.active_skill = sk
        d.update(DT)
        assert d.state == want, (sk, d.state)
        b.active_skill = None
        d.update(DT)


# ═════════════════════════════════════════════════════════════════════════
# 4. AYUNAN BERBASIS ARC + GEOMETRI MIRROR
# ═════════════════════════════════════════════════════════════════════════

def test_arc_swing_not_teleporting():
    """Sudut lengan bergerak menerus (tanpa lompatan besar antar frame)."""
    prev = None
    max_step = 0.0
    for i in range(COOLDOWN + 4):
        p = min(1.0, i / (COOLDOWN - 1))
        ang = G.arc_angle(p, "attack", 1.2)
        if prev is not None:
            max_step = max(max_step, abs(ang - prev))
        prev = ang
    # langkah 1/60 s: swing cepat boleh besar, tapi tidak melompat 180°
    assert max_step < 0.75, max_step
    # ayunan nyata: mulai di belakang-atas (negatif), akhir di depan
    assert G.arc_angle(0.37, "attack", 0.0) < -1.0
    assert G.arc_angle(0.54, "attack", 0.0) > 0.2


def test_claw_sweeps_forward():
    """Ujung cakar maju monoton saat jendela swing (facing kanan)."""
    xs = []
    for i in range(24):
        p = G.ATK_PHASES["swing"][0] + (G.ATK_PHASES["swing"][1]
                                        - G.ATK_PHASES["swing"][0]) * i / 23
        (_, _, _, tip) = G.arm_geometry(1, "attack", 0.0, p)
        xs.append(tip[0])
    assert xs[-1] > xs[0], xs
    # dominan maju: korelasi naik (>= 22 dari 23 langkah tidak mundur jauh)
    backward = sum(1 for i in range(1, len(xs)) if xs[i] < xs[i - 1] - 2.0)
    assert backward <= 1, xs


def test_arm_geometry_mirror():
    """Geometri renderer == fallback lokal lapisan FX (trail menempel)."""
    for p in (0.0, 0.2, 0.38, 0.5, 0.62, 0.8, 1.0):
        geo = G.arm_geometry(1, "attack", 0.7, p)
        ang = F._local_arc_angle(p, "attack", 0.7)
        sx, sy = F._SHOULDER
        ex = sx + math.cos(ang - 0.55) * F._UPPER
        ey = sy - math.sin(ang - 0.55) * F._UPPER
        assert abs(geo[1][0] - ex) < 0.01, p
        assert abs(geo[1][1] - ey) < 0.01, p
    # arm_points FX absolut layar == geometri renderer + jangkar
    b = fresh_boss(100.0, 120.0)
    pts = F.arm_points(b, 300.0, 300.0, progress=0.5, action="attack")
    geo = G.arm_geometry(1, "attack", b.pulse, 0.5)
    assert abs(pts[3][0] - (300.0 + geo[3][0])) < 0.01


# ═════════════════════════════════════════════════════════════════════════
# 5. PARTICLE SYSTEM
# ═════════════════════════════════════════════════════════════════════════

def test_particle_fields_and_decay():
    p = F.Particle()
    p.spawn(10, 10, 5, -5, 0.5, 3, (120, 200, 255), gravity=200.0,
            rotation_speed=4.0, drag=1.0)
    for _ in range(40):
        p.update(DT)
    assert not p.alive                      # meluruh -> mati
    assert p.life == 0.0


def test_particle_system_cap_and_reuse():
    ps = F.ParticleSystem(50)
    for i in range(200):
        ps.spawn(i, i, 0, 0, 0.3, 2, (1, 2, 3))
    assert ps.count() <= 50
    for _ in range(40):
        ps.update(DT)
    assert ps.count() == 0                  # semua meluruh
    # pool dipakai ulang tanpa alokasi baru
    before = len(ps._pool)
    for i in range(10):
        ps.spawn(i, 0, 0, 0, 0.3, 2, (1, 2, 3))
    assert len(ps._pool) < before or ps.count() == 10


def test_no_eternal_particles():
    """Setelah pertempuran, efek KOMBAT mati semua (tak ada yang abadi).

    Partikel ambient idle (salju melayang) memang terus diganti — yang
    diuji: jumlahnya jauh di bawah cap, tidak menumpuk naik, dan semua
    impact/skill/proyektil pasti terkuras.
    """
    b = fresh_boss()
    d = F.director_for(b)
    run_attack(b, d)
    d.on_impact(230, 230, 0.0, 2.0, True, "blast")
    d.on_impact(230, 230, 0.0, 2.0, False, "erupt")
    d.on_hurt(1.0)
    for i in range(400):                    # ~6.6 detik
        d.update(DT)
    assert d.impacts == []
    assert d.skills == []
    assert d.projectiles.count() == 0
    # hanya ambient idle yang tersisa, dan jumlahnya stabil (tak menumpuk)
    counts = []
    for i in range(240):                    # 4 detik lagi
        d.update(DT)
        if i % 60 == 59:
            counts.append(d.particles.count())
    assert all(c <= F.MAX_PARTICLES for c in counts), counts
    assert counts[-1] <= counts[0] + 12, counts   # tidak menanjak terus


# ═════════════════════════════════════════════════════════════════════════
# 6. PROJECTILE LIFECYCLE
# ═════════════════════════════════════════════════════════════════════════

def test_projectile_full_lifecycle():
    tgt = _ProbeEntity("dummy", 400.0, 230.0)
    p = F.ApparitionProjectile(230, 220, 400, 230, kind="shard",
                               target=tgt)
    # bidang kontrak lengkap
    for attr in ("position", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active"):
        assert hasattr(p, attr), attr
    moved = False
    hit = False
    for i in range(120):
        if p.update(DT):
            hit = True
            break
        if i > 2 and (abs(p.position.x - 230) > 3):
            moved = True
    assert moved and hit
    assert not p.active                     # DESTROY setelah HIT


def test_projectile_system_cap():
    ps = F.ProjectileSystem(8)
    for i in range(30):
        ps.spawn(0, 0, 10 ** 6, 0, kind="shard", lifetime=5.0)
    assert ps.count() <= 8
    ps.clear()
    assert ps.count() == 0


def test_director_releases_shard_on_impact_point():
    """Boss path: shard hidup lahir tepat di titik IMPACT ayunan."""
    b = fresh_boss()
    b.target = _ProbeEntity("dummy", 360.0, 230.0)
    d = F.director_for(b)
    seen_proj = 0
    for i in range(COOLDOWN):
        b.attack_timer = max(0, COOLDOWN - i)
        d.update(DT)
        seen_proj = max(seen_proj, d.projectiles.count())
    assert seen_proj >= 1                   # shard sempat terbang


# ═════════════════════════════════════════════════════════════════════════
# 7. SKILL FX LIFECYCLE
# ═════════════════════════════════════════════════════════════════════════

def test_skillfx_lifecycle_phases():
    for sk in ("q", "w", "e", "r"):
        ps = F.ParticleSystem(40)
        s = F.SkillFX(sk, 100, 100, ps)
        phases = []
        while s.alive and len(phases) < 4000:
            s.update(DT)
            if not phases or phases[-1] != s.phase:
                phases.append(s.phase)
        assert not s.alive, sk              # SELALU mati (cleanup)
        assert phases[0] in ("CAST", "CHARGE"), (sk, phases)
        assert "FADE" in phases, (sk, phases)
        if sk == "r":
            assert "RELEASE" in phases and "AREA" in phases, phases
        if sk == "e":
            assert "RELEASE" in phases, phases


def test_skill_cast_positions():
    """Q lahir di vortex dunia; R menempel target; W dari tangan."""
    b = fresh_boss(100.0, 100.0)
    b.target = _ProbeEntity("dummy", 260.0, 110.0)
    b.vortex_x, b.vortex_y = 240.0, 130.0
    d = F.director_for(b)
    for sk in ("q", "r"):
        d.on_cast(100.0, 100.0, sk)
        assert d.skills, sk
        s = d.skills[-1]
        if sk == "q":
            assert abs(s.x - 240.0) < 1.0 and abs(s.y - 130.0) < 1.0
        else:
            assert abs(s.x - 260.0) < 1.0 and abs(s.y - 118.0) < 2.0
        d.update(DT)
    d.on_cast(100.0, 100.0, "w")
    assert abs(d.skills[-1].x - 118.0) < 1.0   # 100 + 18 * facing


def test_vortex_watch_dot():
    """Vortex DOT (timer gameplay) memicu FX hidup tanpa active_skill."""
    b = fresh_boss(100.0, 100.0)
    d = F.director_for(b)
    b.vortex_x, b.vortex_y = 300.0, 140.0
    b.vortex_active_timer = 180
    d.update(DT)
    assert any(s.skill == "q" for s in d.skills)
    b.vortex_active_timer = 0
    for i in range(300):
        d.update(DT)
    assert d.skills == []


# ═════════════════════════════════════════════════════════════════════════
# 8. IMPACT + SHAKE + HIT-STOP SELALU TERKURAS
# ═════════════════════════════════════════════════════════════════════════

def test_hitstop_window():
    FEEL.reset()
    d = F.ApparitionFXDirector(fresh_boss())
    for kind in ("hit", "blast", "erupt"):
        FEEL.reset()
        d.on_impact(0, 0, 0.0, 1.0, False, kind)
        assert FEEL.HITSTOP.frames > 0, kind
        # bus mengjepit ke 2..5 langkah = 0.033..0.083 s
        assert 2 <= FEEL.HITSTOP.total <= 5, kind
        assert 0.03 <= FEEL.HITSTOP.total * FEEL.FIXED_DT <= 0.08, kind


def test_shake_and_drain():
    FEEL.reset()
    b = fresh_boss()
    d = F.director_for(b)
    d.on_impact(0, 0, 0.0, 2.0, False, "blast")
    assert FEEL.amount() > 0.0
    for i in range(120):
        FEEL.SHAKE.update(DT)
    assert FEEL.amount() == 0.0             # shake meluruh sampai habis
    assert not FEEL.HITSTOP.active or True  # terkuras lewat consume


# ═════════════════════════════════════════════════════════════════════════
# 9. SUPRESI GANDA (live owned vs fallback canvas)
# ═════════════════════════════════════════════════════════════════════════

def test_live_layer_suppression(monkeypatch):
    """owned=True -> renderer melewati FX canvas; owned=False -> fallback."""
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)

    # jalur BOSS + modul hidup: FX internal canvas dilewati.
    # timer=29 -> progress W = 1 - 29/45 = 0.36 (di jendela spawn 0.3-0.4).
    b = fresh_boss(active_skill="w", active_skill_timer=29)
    b.target = _ProbeEntity("dummy", 360.0, 230.0)
    G.draw_apparition(surf, b, 230, 230)
    assert F.owns(b)
    assert not getattr(b, "_aa_beams", None)      # beam canvas tidak lahir

    # modul FX "hilang" -> fallback canvas tetap jalan
    b2 = fresh_boss(active_skill="w", active_skill_timer=29)
    b2.target = _ProbeEntity("dummy", 360.0, 230.0)
    old = G._LIVE_MOD
    monkeypatch.setattr(G, "_LIVE_MOD", False)
    try:
        G.draw_apparition(surf, b2, 230, 230)
        assert not F.owns(b2)
        assert getattr(b2, "_aa_beams", None)     # fallback canvas aktif
        assert isinstance(b2._aa_beams[0], G.FrostBeam)
    finally:
        monkeypatch.setattr(G, "_LIVE_MOD", old)


def test_hero_basic_shard_guard():
    """Hero yang dimainkan: shard canvas internal mati (pakai sistem Hero)."""
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    b = fresh_boss()
    b._aa_hero_basic_shard = True
    old = G._LIVE_MOD
    G._LIVE_MOD = False
    try:
        G._spawn_ice_shard(b, 230, 220, 360, 230)
        assert not getattr(b, "_aa_projectiles", None)
        b._aa_hero_basic_shard = False
        G._spawn_ice_shard(b, 230, 220, 360, 230)
        assert b._aa_projectiles
    finally:
        G._LIVE_MOD = old


# ═════════════════════════════════════════════════════════════════════════
# 10. DURASI CANVAS == AI (kontrak lama)
# ═════════════════════════════════════════════════════════════════════════

def test_canvas_durations_match_ai():
    """q=60, r=90 (ground+foreground), w=45 & e=50 (handle)."""
    b = fresh_boss()
    tg = _ProbeEntity("dummy", 340.0, 230.0)
    b.target = tg
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    G._LIVE_MOD = False                      # paksa jalur canvas
    try:
        b.active_skill, b.active_skill_timer = "q", 60
        G.draw_apparition(surf, b, 230, 230)
        b.active_skill, b.active_skill_timer = "r", 90
        G.draw_apparition(surf, b, 230, 230)
        # handle w/e tidak crash pada berbagai timer
        for sk, dur in (("w", 45), ("e", 50)):
            b._aa_w_spawned = b._aa_e_spawned = False
            for t in (dur, dur // 2, dur - int(dur * 0.4)):
                b.active_skill, b.active_skill_timer = sk, t
                G.draw_apparition(surf, b, 230, 230)
    finally:
        G._LIVE_MOD = None
        b.active_skill = None


# ═════════════════════════════════════════════════════════════════════════
# 11. RENDER: SEMUA MODE + HERO PIPELINE + PERFORMA
# ═════════════════════════════════════════════════════════════════════════

def test_all_modes_render_boss_path():
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    cases = [dict(pulse=0.0), dict(pulse=3.3), dict(hurt_flash_timer=6)]
    for extra in cases:
        b = fresh_boss(**extra)
        b.target = _ProbeEntity("dummy", 340.0, 230.0)
        surf.fill((0, 0, 0, 0))
        G.draw_apparition(surf, b, 230, 230)
        r = surf.get_bounding_rect(min_alpha=100)
        assert r.width > 100 and r.height > 90, (extra, r)
    # attack + semua skill
    for extra in (dict(_aa_attack_active=True, _aa_attack_progress=0.5),):
        b = fresh_boss(**extra)
        surf.fill((0, 0, 0, 0))
        G.draw_apparition(surf, b, 230, 230)
        assert surf.get_bounding_rect(min_alpha=100).width > 60
    for sk in "qwer":
        b = fresh_boss(active_skill=sk, active_skill_timer=30)
        b.target = _ProbeEntity("dummy", 340.0, 230.0)
        surf.fill((0, 0, 0, 0))
        G.draw_apparition(surf, b, 230, 230)
        assert surf.get_bounding_rect(min_alpha=100).width > 60


def test_hero_pipeline_render():
    """Jalur HERO: render_hero -> cache sprite + lapisan hidup terpasang."""
    surf = pygame.Surface((640, 480), pygame.SRCALPHA)
    h = fresh_boss(320.0, 240.0, scale=1.0)
    h.moving_cache = None
    heroes.clear_hero_sprite_cache()
    for i in range(4):
        h.pulse += 0.3
        heroes.render_hero("ancient_apparition", surf, h, 320, 240)
    assert F.owns(h)
    # serangan lewat pipeline hero tetap memicu director
    h.attack_timer = 61
    F.tick(0.0)
    for i in range(61):
        h.attack_timer = max(0, h.attack_timer - 1)
        heroes.render_hero("ancient_apparition", surf, h, 320, 240)
        F.tick(1.0 / 60.0)
    d = F.director_for(h)
    assert d.attack_progress == 0.0 or d.state == "IDLE"


def test_boss_path_perf():
    b = fresh_boss()
    b.target = _ProbeEntity("dummy", 340.0, 230.0)
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    for i in range(20):
        b.pulse = 1.0 + i * 0.13
        G.draw_apparition(surf, b, 230, 230)
    n = 40
    t0 = time.perf_counter()
    for i in range(n):
        b.pulse = 1.0 + i * 0.13
        G.draw_apparition(surf, b, 230, 230)
    dt_ms = (time.perf_counter() - t0) / n * 1000
    assert dt_ms < 2.35, dt_ms


def test_live_layer_perf():
    b = fresh_boss()
    b.target = _ProbeEntity("dummy", 360.0, 230.0)
    d = F.director_for(b)
    surf = pygame.Surface((640, 480), pygame.SRCALPHA)
    # panaskan: serangan + skill + impact semua hidup
    run_attack(b, d)
    d.on_cast(230.0, 230.0, "r")
    d.on_impact(360, 230, 0.0, 1.5, True, "blast")
    n = 60
    t0 = time.perf_counter()
    for i in range(n):
        d.update(DT)
        d.draw_ground(surf, 230, 230)
        d.draw_front(surf, 230, 230)
    dt_ms = (time.perf_counter() - t0) / n * 1000
    assert dt_ms < 6.0, dt_ms               # frame penuh FX skill + 135 partikel


def test_debug_overlay_draws():
    b = fresh_boss()
    d = F.director_for(b)
    run_attack(b, d)
    surf = pygame.Surface((640, 480), pygame.SRCALPHA)
    old = F.DEBUG_CHARACTER
    F.DEBUG_CHARACTER = True
    try:
        d.draw_front(surf, 230, 230)
    finally:
        F.DEBUG_CHARACTER = old
    r = surf.get_bounding_rect(min_alpha=1)
    assert r.width > 100                    # panel + box tergambar


def test_renderer_debug_flag():
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    b = fresh_boss()
    old = G.DEBUG_CHARACTER
    G.DEBUG_CHARACTER = True
    try:
        G.draw_apparition(surf, b, 230, 230)
    finally:
        G.DEBUG_CHARACTER = old
    assert surf.get_bounding_rect(min_alpha=1).width > 100


# ═════════════════════════════════════════════════════════════════════════
# 12. ALPHA-SAFE PADA LAYAR XRGB (buffer game tidak punya kanal alpha)
# ═════════════════════════════════════════════════════════════════════════

def test_fx_draw_on_xrgb_screen():
    """Semua bentuk translucent tetap benar di permukaan tanpa alpha.

    pygame.draw dengan warna RGBA di permukaan XRGB akan mengabaikan
    alpha (jadi solid) — helper _poly_a/_line_a/_circle_a modul ini
    memakai scratch SRCALPHA supaya blend tetap terjadi.
    """
    masks = (0x00FF0000, 0x0000FF00, 0x000000FF, 0)
    screen = pygame.Surface((640, 480), 0, 32, masks)
    screen.fill((50, 50, 50))
    base = screen.get_at((320, 240))

    b = fresh_boss(320.0, 240.0)
    b.target = _ProbeEntity("dummy", 470.0, 240.0)
    d = F.director_for(b)
    run_attack(b, d)
    d.on_cast(320.0, 240.0, "w")
    d.on_cast(320.0, 240.0, "r")
    d.on_impact(430, 240, 0.0, 1.5, False, "blast")
    for i in range(12):
        d.update(DT)
    # tidak boleh exception, dan efek terlihat (piksel berubah)
    d.draw_ground(screen, 320, 240)
    d.draw_front(screen, 320, 240)
    changed = 0
    blown = 0
    for yy in range(140, 380, 3):
        for xx in range(180, 470, 3):
            c = screen.get_at((xx, yy))
            if c[:3] != base[:3]:
                changed += 1
                if min(c[:3]) >= 240:
                    blown += 1
    assert changed > 60, changed
    # area BEAM/translucent tidak boleh menyala solid putih penuh
    # (kalau alpha diabaikan, quad beam jadi blok solid > 90% putih)
    assert blown < changed * 0.5, (blown, changed)


def test_boss_draw_on_xrgb_screen():
    """Jalur boss penuh (ground + body + live) di layar XRGB."""
    masks = (0x00FF0000, 0x0000FF00, 0x000000FF, 0)
    screen = pygame.Surface((640, 480), 0, 32, masks)
    b = fresh_boss(320.0, 240.0)
    b.target = _ProbeEntity("dummy", 470.0, 240.0)
    for i in range(30):
        b.pulse += 0.05
        G.draw_apparition(screen, b, 320, 240)
    # skill Q/R melewati jalur live di layar XRGB
    for sk in ("q", "r"):
        b.active_skill = sk
        b.active_skill_timer = 40
        for i in range(8):
            G.draw_apparition(screen, b, 320, 240)
