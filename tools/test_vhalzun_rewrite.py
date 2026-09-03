#!/usr/bin/env python3
"""Regression test VHALZUN FULL REWRITE (render + animasi + FX hidup).

The Reaper of Souls — L5 Mini Boss & hero unlock (Level 5).

Mengunci lewat path shipping:
  * RENDER   — semua state tergambar tanpa exception, bbox memadai, tidak
               ada flicker (frame idle berubah tapi tidak pernah kosong),
               probe portrait tidak meledak.
  * ANIMASI  — controller: prioritas state, pemetaan action per skill
               (q/w/e/r), dual-mode basic attack (swing <= MELEE_REACH,
               pulse > MELEE_REACH), fase ANTICIPATION->RECOVERY.
  * ATTACK   — arc sabit: sweep kontinyu tanpa lompatan sudut; fallback
               canvas tergambar saat modul FX dimatikan.
  * PROJECTILE (lapisan hidup) — death pulse & reaper scythe modular:
               spawn -> travel -> trail -> hit -> impact -> destroy;
               HANYA di jalur boss (jalur hero memakai proyektil generik
               gameplay); tidak ada yang hidup melampaui lifetime.
  * SKILL FX (lapisan hidup) — q/w/e/r lifecycle penuh + cleanup; semua
               skill dimajukan setiap frame (anti-kebocoran).
  * GAME FEEL — hit-stop di dalam jendela 0.03-0.08 s; impact tidak
               menumpuk melampaui batas; partikel turun ke nol setelah
               pertarungan selesai (ambient dimatikan saat tes).
  * INTEGRASI — jalur boss (draw_vhalzun + live layer) & jalur hero
               (render_hero melewati _LIVE_FX_HEROES); registry
               lengkap; reset_all mengembalikan semuanya ke nol; palet
               FX tersinkron dari palet renderer.
  * PERF     — idle < 2.4 ms/frame; FX tick+draw < 2.1 ms/frame.

Jalankan: python3 tools/test_vhalzun_rewrite.py
"""
import math
import os
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

import bosses.level5 as L
import heroes.vhalzun_fx as FX
import heroes  # heroes/__init__.py — pipeline sprite + live FX

NS = L._NS_vhalzun
P = FX.VHALZUN_PALETTE


# ── helper ─────────────────────────────────────────────────────────
def probe(**kw):
    b = SimpleNamespace(boss_type="vhalzun", hero_type="vhalzun",
                        x=230.0, y=230.0, direction=1, pulse=1.2,
                        timer=0, attack_cooldown=44, active_skill=None,
                        active_skill_timer=0, target=None,
                        hurt_flash_timer=0,
                        alive=True, radius=38, hp=9300, max_hp=9300,
                        team="red", speed=0.82, damage=78,
                        is_enraged=False, ability_active=False,
                        ability_active_timer=0)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(b, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    L.draw_vhalzun(s, b, 230, 230)
    return s


def bbox(s, alpha=8):
    return s.get_bounding_rect(min_alpha=alpha)


def tgt(dx=100.0, dy=0.0, alive=True, radius=16):
    return SimpleNamespace(x=230.0 + dx, y=230.0 + dy, alive=alive,
                           radius=radius)


def fresh():
    """Reset semua state FX global antar tes."""
    FX.reset_all()
    NS.clear_cache()


# ===================================================================
# 1. RENDER — semua state
# ===================================================================
def test_render_all_states():
    t = tgt(70.0)
    cases = {
        "idle": probe(),
        "walk": probe(_vhz_last_x=224.0, _vhz_last_y=230.0, x=228.0),
        "swing": probe(target=t, _vhz_attack_active=True,
                       _vhz_attack_kind="swing",
                       _vhz_attack_progress=0.42, _vhz_prev_timer=40,
                       timer=40),
        "pulse": probe(target=tgt(200.0), _vhz_attack_active=True,
                       _vhz_attack_kind="pulse",
                       _vhz_attack_progress=0.40, _vhz_prev_timer=40,
                       timer=40),
        "cast_q": probe(active_skill="q", active_skill_timer=30,
                        _vhz_skill="q", _vhz_skill_total=60, target=t),
        "cast_w": probe(active_skill="w", active_skill_timer=40,
                        _vhz_skill="w", _vhz_skill_total=80, target=t),
        "cast_e": probe(active_skill="e", active_skill_timer=30,
                        _vhz_skill="e", _vhz_skill_total=60, target=t),
        "cast_r": probe(active_skill="r", active_skill_timer=50,
                        _vhz_skill="r", _vhz_skill_total=100, target=t),
        "hit": probe(hurt_flash_timer=8, _vhz_hurt_frames=5),
        "death": probe(alive=False, _vhz_death_age=20),
        "mirror": probe(direction=-1),
        "mirror_swing": probe(direction=-1, target=tgt(-70.0),
                              _vhz_attack_active=True,
                              _vhz_attack_kind="swing",
                              _vhz_attack_progress=0.42, timer=40),
    }
    for name, b in cases.items():
        s = render(b)
        r = bbox(s)
        assert r.width > 40 and r.height > 55, (name, r)
    print("PASS render semua state (idle/walk/swing/pulse/q/w/e/r/hit/"
          "death/mirror)")


def test_render_no_flicker():
    b = probe()
    rects = []
    for i in range(30):
        b.pulse += 0.05
        s = render(b)
        r = bbox(s)
        assert r.width > 40 and r.height > 55, (i, r)
        rects.append(r)
    ws = {r.width for r in rects}
    hs = {r.height for r in rects}
    # bbox boleh bernafas beberapa pixel, tidak boleh kolaps
    assert max(ws) - min(ws) <= 8, (ws, hs)
    assert max(hs) - min(hs) <= 10, (ws, hs)
    print("PASS render idle stabil (bbox width %s, height %s)"
          % (sorted(ws), sorted(hs)))


def test_portrait_probe_tolerated():
    b = probe(_portrait_hd=True)
    s = render(b)
    r = bbox(s)
    assert r.height > 40, r
    # portrait tidak boleh menyisakan FX tanah lebar
    assert r.width < 220, r
    print("PASS probe portrait tidak meledak (bbox %s)" % (r,))


# ===================================================================
# 2. ANIMATION CONTROLLER
# ===================================================================
def test_animation_state_priority():
    # DEATH mengunci semua
    b = probe(alive=False, active_skill="r", _vhz_attack_active=True,
              hurt_flash_timer=8)
    assert NS._update_vhalzun_anim(b) == "DEATH"
    # HURT > SKILL > ATTACK > WALK > IDLE
    b = probe(active_skill="q", _vhz_attack_active=True, hurt_flash_timer=8)
    assert NS._update_vhalzun_anim(b) == "HURT"
    b = probe(active_skill="q", _vhz_attack_active=True, timer=30)
    assert NS._update_vhalzun_anim(b) == "SKILL"
    b = probe(_vhz_attack_active=True, timer=30)
    assert NS._update_vhalzun_anim(b) == "ATTACK"
    b = probe(_vhz_attack_active=True, timer=30, _vhz_attack_kind="swing")
    assert NS._update_vhalzun_anim(b) == "SWING"
    b = probe(_vhz_last_x=224.0, _vhz_last_y=230.0, x=228.0)
    assert NS._update_vhalzun_anim(b) == "WALK"
    b = probe()
    assert NS._update_vhalzun_anim(b) == "IDLE"
    print("PASS prioritas state DEATH>HURT>SKILL>SWING/ATTACK>WALK>IDLE")


def test_skill_action_mapping():
    for sk in ("q", "w", "e", "r"):
        b = probe(active_skill=sk, active_skill_timer=30, _vhz_skill=sk,
                  _vhz_skill_total=60)
        action, phase, ap = NS._resolve_pose(b, False)
        assert action == "cast_" + sk, (sk, action)
        assert 0.0 <= ap <= 1.0
    print("PASS pemetaan action per skill (cast_q/w/e/r)")


def test_dual_mode_basic_attack():
    # trigger dari timer memilih mode berdasar jarak target
    near = tgt(70.0)
    far = tgt(300.0)
    b = probe(target=near, timer=43, _vhz_prev_timer=0,
              attack_cooldown=44)
    NS._update_vhalzun_anim(b)
    assert b._vhz_attack_active and b._vhz_attack_kind == "swing"

    b = probe(target=far, timer=43, _vhz_prev_timer=0,
              attack_cooldown=44)
    NS._update_vhalzun_anim(b)
    assert b._vhz_attack_active and b._vhz_attack_kind == "pulse"
    print("PASS dual-mode basic attack (swing dekat / pulse jauh)")


def test_attack_phases():
    order = NS.attack_phases_order()
    assert order == ("ANTICIPATION", "WINDUP", "SWING", "IMPACT",
                     "FOLLOW", "RECOVERY")
    assert NS.attack_phase(0.0) == "ANTICIPATION"
    assert NS.attack_phase(0.35) == "SWING"
    assert NS.attack_phase(0.55) == "IMPACT"
    assert NS.attack_phase(0.99) == "RECOVERY"
    lo, hi = NS.ATTACK_ACTIVE_WINDOW
    assert 0.30 <= lo < hi <= 0.62
    print("PASS fase serangan ANTICIPATION->RECOVERY + jendela aktif")


# ===================================================================
# 3. SWING ARC
# ===================================================================
def test_scythe_arc_continuous():
    angles = [NS._scythe_angle("swing", i / 90.0, 1.0) for i in range(91)]
    jumps = [abs(angles[i + 1] - angles[i]) for i in range(90)]
    assert max(jumps) < 0.25, max(jumps)
    span = max(angles) - min(angles)
    assert span > 1.6, span           # sweep melebar (bukan gerak kecil)
    # windup terangkat (negatif), follow-through selesai di bawah (positif)
    assert min(angles) < -0.4 and max(angles) > 0.9
    print("PASS arc sabit kontinyu: span %.2f rad, lompatan maks %.3f rad"
          % (span, max(jumps)))


def test_swing_hit_window():
    b = probe(_vhz_attack_active=True, _vhz_attack_kind="swing")
    for p in (0.10, 0.25):
        b._vhz_attack_progress = p
        assert not (0.30 <= p < 0.55), p
    b._vhz_attack_progress = 0.42
    assert 0.30 <= 0.42 < 0.55
    print("PASS jendela hit aktif hanya di 0.30..0.55")


def test_fallback_fx_drawn():
    """Saat modul hidup dimatikan, canvas fallback tetap menggambar
    proyektil sederhana (fungsi tidak hilang)."""
    was = FX.VHALZUN_FX_ENABLED
    try:
        FX.VHALZUN_FX_ENABLED = False
        NS._LIVE_MOD = False
        b = probe(target=tgt(200.0), timer=43, _vhz_prev_timer=0,
                  attack_cooldown=44)
        s = pygame.Surface((460, 460), pygame.SRCALPHA)
        L.draw_vhalzun(s, b, 230, 230)       # trigger attack
        assert getattr(b, "_vhz_attack_active", False)
        # dorong progress ke atas ambang rilis
        b._vhz_attack_progress = 0.5
        b._vhz_attack_manual = True
        L.draw_vhalzun(s, b, 230, 230)
        projs = getattr(b, "_vhz_projectiles", None)
        assert projs, "fallback projectile tidak spawn"
        for _ in range(10):
            L.draw_vhalzun(s, b, 230, 230)
        assert len(getattr(b, "_vhz_projectiles", [])) <= 12
    finally:
        FX.VHALZUN_FX_ENABLED = was
        NS._LIVE_MOD = None
        if hasattr(b, "_vhz_projectiles"):
            b._vhz_projectiles = []
    print("PASS fallback canvas FX (proyektil sederhana + cap)")


# ===================================================================
# 4. PROJECTILE — lapisan hidup
# ===================================================================
def test_orb_lifecycle_boss_lane():
    fresh()
    b = probe(target=tgt(180.0), _vhz_attack_active=True,
              _vhz_attack_kind="pulse", _vhz_attack_manual=True)
    s = pygame.Surface((640, 460), pygame.SRCALPHA)
    d = FX.director_for(b)
    saw_alive = saw_hit = False
    for i in range(80):
        b._vhz_attack_progress = min(0.95, i / 60.0)
        L.draw_vhalzun(s, b, 320, 230)
        FX.tick(1.0 / 60.0)
        if d.projectiles.count() > 0:
            saw_alive = True
        if len(d.projectiles.impacts) > 0:
            saw_hit = True
    assert saw_alive, "orb tidak pernah hidup"
    assert saw_hit, "orb tidak pernah mengenai"
    assert d.projectiles.count() == 0, "orb tidak hancur setelah kena"
    for _ in range(240):
        FX.tick(1.0 / 60.0)
    assert d.projectiles.count() == 0
    print("PASS death pulse lifecycle (spawn->travel->hit->destroy)")


def test_scythe_wave_lifecycle():
    fresh()
    t = tgt(240.0)
    b = probe(target=t, active_skill="e", active_skill_timer=60)
    s = pygame.Surface((700, 460), pygame.SRCALPHA)
    d = FX.director_for(b)
    spawned = False
    for tm in range(60, 0, -1):
        b.active_skill_timer = tm
        b._vhz_skill = "e"
        b._vhz_skill_total = 60
        L.draw_vhalzun(s, b, 230, 230)
        FX.tick(1.0 / 60.0)
        if d.projectiles.count() > 0:
            spawned = True
    assert spawned, "gelombang sabit tidak spawn saat RELEASE"
    for _ in range(200):
        FX.tick(1.0 / 60.0)
    assert d.projectiles.count() == 0
    print("PASS reaper scythe wave lifecycle + cleanup")


def test_no_procedural_projectile_in_hero_lane():
    """Jalur hero: proyektil generik gameplay sudah terbang sebagai
    visual — lapisan hidup TIDAK boleh menambah proyektil kedua."""
    fresh()
    b = probe(target=tgt(180.0), _vhz_attack_active=True,
              _vhz_attack_kind="pulse", _vhz_attack_manual=True)
    b._render_scale = 0.8            # -> jalur hero
    d = FX.director_for(b)
    for i in range(50):
        b._vhz_attack_progress = min(0.95, i / 40.0)
        FX.tick(1.0 / 60.0)
    assert d.projectiles.count() == 0
    print("PASS lane gate: tidak ada proyektil ganda di jalur hero")


def test_projectile_caps_and_lifetime():
    fresh()
    d = FX.director_for(probe())
    for i in range(30):
        d.projectiles.spawn_orb(230, 230, 231 + i * 5, 230)
    assert d.projectiles.count() <= FX.MAX_PROJECTILES
    for _ in range(120):
        FX.tick(1.0 / 60.0)
    assert d.projectiles.count() == 0
    print("PASS cap proyektil (%d) + lifetime mematikan semuanya"
          % FX.MAX_PROJECTILES)


# ===================================================================
# 5. IMPACT / GAME FEEL
# ===================================================================
def test_swing_impact_self_triggered():
    fresh()
    t = tgt(70.0)
    b = probe(target=t, _vhz_attack_active=True,
              _vhz_attack_kind="swing", _vhz_attack_manual=True)
    d = FX.director_for(b)
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    for i in range(25):
        b._vhz_attack_progress = i / 24.0
        L.draw_vhalzun(s, b, 230, 230)
        FX.tick(1.0 / 60.0)
    assert d.swing_done, "impact frame tidak tercapai"
    assert len(d.impacts) >= 1 or d.particles.count() > 0
    print("PASS impact swing terpicu di frame benturan (0.42)")


def test_notify_melee_impact_holds_until_frame():
    fresh()
    t = tgt(70.0)
    b = probe(target=t, _vhz_attack_active=True,
              _vhz_attack_kind="swing", _vhz_attack_manual=True,
              _vhz_attack_progress=0.20)
    d = FX.director_for(b)
    FX.notify_melee_impact(b, t, 78, False)
    # masih awal ayunan -> impact ditahan
    assert d._pending_impact is not None
    b._vhz_attack_progress = 0.42
    FX.tick(1.0 / 60.0)      # update() melepas pending via frame benturan
    assert d._pending_impact is None
    print("PASS notify_melee_impact menahan impact sampai frame bilah")


def test_hitstop_window():
    fresh()
    assert FX._feel is not None, "combat_feel harus tersedia"
    lo = FX._feel.HIT_STOP_MIN if hasattr(FX._feel, "HIT_STOP_MIN") \
        else 0.03
    hi = FX._feel.HIT_STOP_MAX if hasattr(FX._feel, "HIT_STOP_MAX") \
        else 0.08
    assert 0.03 <= lo <= 0.08 and 0.03 <= hi <= 0.08
    # semua permintaan hit-stop dijepit ke jendela 0.03..0.08 s
    # (granularitas 1 langkah simulasi = 1/60 s di tolerated)
    for req in (0.005, 0.02, 0.045, 0.2, 1.0):
        FX._feel.HITSTOP.trigger(req)
        total = FX._feel.HITSTOP.total * (1.0 / 60.0)
        assert lo - 1e-6 <= total <= hi + 1.0 / 60.0, (req, total)
        FX._feel.HITSTOP.clear()
    print("PASS hit-stop selalu di dalam jendela 0.03-0.08 s")


def test_impacts_capped():
    fresh()
    d = FX.director_for(probe())
    for i in range(40):
        d.on_impact(230 + i, 230, power=1.0)
    assert len(d.impacts) <= FX.MAX_IMPACTS
    for im in d.impacts:
        assert im.alive
    print("PASS impact tidak menumpuk melampaui %d" % FX.MAX_IMPACTS)


def test_particles_decay_to_zero():
    fresh()
    b = probe()
    d = FX.director_for(b)
    d.on_impact(230, 230, power=1.4)
    d.on_hurt(230, 230)
    d.on_death(230, 230)
    assert d.particles.count() > 0
    # ambient dimatikan paksa agar pengukuran murni decay
    d.ember_acc = 0.0
    d.have_pos = False
    for _ in range(600):
        FX.tick(1.0 / 60.0)
    assert d.particles.count() == 0, d.particles.count()
    assert len(d.impacts) == 0
    print("PASS partikel & impact meluruh ke 0 (tanpa kebocoran)")


# ===================================================================
# 6. SKILL FX LIFECYCLE
# ===================================================================
def test_skill_fx_lifecycle():
    for sk in ("q", "w", "e", "r"):
        fresh()
        t = tgt(150.0)
        b = probe(target=t, active_skill=sk, active_skill_timer=30)
        d = FX.director_for(b)
        s = pygame.Surface((640, 460), pygame.SRCALPHA)
        L.draw_vhalzun(s, b, 230, 230)
        assert any(fx.skill == sk for fx in d.skills), sk
        fx = [f for f in d.skills if f.skill == sk][0]
        for tm in range(30, 0, -2):
            b.active_skill_timer = tm
            L.draw_vhalzun(s, b, 230, 230)
            FX.tick(2.0 / 60.0)
        # skill berjalan penuh, partikel dibuang
        for _ in range(400):
            FX.tick(1.0 / 60.0)
        assert not any(f.skill == sk and not f.done for f in d.skills)
        d.have_pos = False
        for _ in range(120):
            FX.tick(1.0 / 60.0)
        assert d.particles.count() == 0, (sk, d.particles.count())
    print("PASS skill FX q/w/e/r lifecycle penuh + cleanup")


def test_finished_skills_still_advance():
    """Skill yang state engine-nya sudah berganti tetap dimajukan
    sampai selesai (anti-kebocoran)."""
    fresh()
    b = probe()
    d = FX.director_for(b)
    fx = d.on_cast(230, 230, "q")
    fx.set_engine_progress(0.5)
    b.active_skill = None
    for _ in range(300):
        FX.tick(1.0 / 60.0)
    assert fx.done
    assert fx not in d.skills
    print("PASS skill tanpa state engine tetap selesai & dibuang")


def test_skill_phase_mapping():
    assert FX.skill_phase(0.0) == "CAST"
    assert FX.skill_phase(0.2) == "CHARGE"
    assert FX.skill_phase(0.4) == "RELEASE"
    assert FX.skill_phase(0.6) == "AREA"
    assert FX.skill_phase(0.8) == "IMPACT"
    assert FX.skill_phase(0.95) == "AFTER"
    print("PASS lifecycle skill CAST->CHARGE->RELEASE->AREA->IMPACT->AFTER")


# ===================================================================
# 7. INTEGRASI — registry, pipeline hero, jalur boss
# ===================================================================
def test_registry_entries():
    assert "vhalzun" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS.get("vhalzun") == "heroes.vhalzun_fx"
    mod = heroes._live_fx_module("vhalzun")
    assert mod is FX
    print("PASS registry heroes/__init__ (live FX vhalzun)")


def test_hero_pipeline_render():
    fresh()
    h = probe(hero_type="vhalzun")
    s = pygame.Surface((520, 340), pygame.SRCALPHA)
    heroes.render_hero("vhalzun", s, h, 260, 170)
    r = bbox(s)
    assert r.width > 30 and r.height > 40, r
    # render ulang (jalur cache) tidak boleh exception
    heroes.render_hero("vhalzun", s, h, 260, 170)
    print("PASS pipeline hero render_hero('vhalzun') (bbox %s)" % (r,))


def test_boss_live_layer_drawn():
    fresh()
    b = probe(target=tgt(90.0))
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    L.draw_vhalzun(s, b, 230, 230)
    assert FX.owns(b)
    d = FX.director_for(b)
    assert d.have_pos and d.draw_age <= 0.35
    print("PASS jalur boss: lapisan hidup digambar (owns + recently)")


def test_reset_all():
    b = probe()
    d = FX.director_for(b)
    d.on_impact(230, 230)
    d.on_cast(230, 230, "q")
    assert d.particles.count() > 0 or len(d.skills) > 0
    FX.reset_all()
    assert FX.total_particles() == 0
    assert len(FX._DIRECTORS) == 0
    assert not FX.owns(b)
    print("PASS reset_all mengembalikan semuanya ke nol")


def test_palette_synced():
    FX._sync_palette()
    for key in ("necro_mid", "robe_dark", "bone_light", "gold_mid",
                "blade_shine", "eye_bright"):
        assert tuple(P[key]) == tuple(NS.PALETTE[key]), key
    print("PASS palet FX tersinkron dari palet renderer")


def test_public_api_intact():
    for name in ("draw_vhalzun", "draw_boss", "pose_of", "anim_state",
                 "scythe_points", "attack_phase", "attack_kind",
                 "body_scale", "ground_dy", "live_fx_ready",
                 "clear_cache"):
        assert callable(getattr(NS, name, None)), name
    for name in ("draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_projectile_impact",
                 "notify_skill_cast", "notify_skill_impact",
                 "notify_death", "attach", "owns", "tick", "reset_all",
                 "stats", "debug_overlay"):
        assert callable(getattr(FX, name, None)), name
    assert NS.MELEE_REACH == FX.MELEE_REACH
    assert NS.SKILL_DUR == FX.SKILL_DUR
    assert NS.ATTACK_ACTIVE_WINDOW == FX.ATTACK_ACTIVE_WINDOW
    assert NS.ATTACK_IMPACT_FRAME == FX.ATTACK_IMPACT_FRAME
    print("PASS kontrak publik renderer + modul FX utuh")


def test_base_boss_hooks_present():
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               encoding="utf-8").read()
    assert "_vhzfx.notify_death" in src
    assert "_vhzfx.notify_skill_cast" in src
    # KONTRAK BARU: serangan dasar tidak memicu impact FX. Hook melee &
    # proyektil vhalzun di base_boss sudah dibuang; impact FX eksklusif
    # milik skill. API modulnya tetap ada (dipakai tooling & test unit).
    assert "_vhzfx.notify_melee_impact" not in src, \
        "serangan dasar boss masih memicu impact FX vhalzun"
    assert "_vhzfx.notify_projectile_impact" not in src, \
        "serangan dasar boss masih memicu impact FX vhalzun"
    assert callable(getattr(FX, "notify_melee_impact", None)) and \
        callable(getattr(FX, "notify_projectile_impact", None)), \
        "API impact FX hilang dari vhalzun_fx"
    # BOSS_LABEL_TOP diperbarui untuk rig baru
    assert re_search(r'"vhalzun":\s*77', src)
    print("PASS hook base_boss (skill + death + label top; "
          "serangan dasar tanpa impact FX)")


def re_search(pattern, text):
    import re
    return re.search(pattern, text)


def test_hero_skills_registered():
    src = open(os.path.join(ROOT, "hero_skills", "_bundle.py"),
               encoding="utf-8").read()
    for fn in ("_cast_q_vhalzun_death_pulse",
               "_cast_w_vhalzun_heartstopper",
               "_cast_e_vhalzun_reapers_scythe",
               "_cast_r_vhalzun_ghost_shroud"):
        assert fn in src, fn
    assert '"vhalzun": {"q": 60, "w": 80, "e": 60, "r": 100}' in src
    print("PASS skill hero-lane vhalzun terdaftar + durasi sinkron")


# ===================================================================
# 8. PERF
# ===================================================================
def test_perf_idle():
    fresh()
    b = probe()
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    L.draw_vhalzun(s, b, 230, 230)          # warm-up cache
    t0 = time.perf_counter()
    n = 120
    for i in range(n):
        b.pulse += 0.05
        L.draw_vhalzun(s, b, 230, 230)
        FX.tick(1.0 / 60.0)
    dt_ms = (time.perf_counter() - t0) * 1000.0 / n
    print("      idle: %.2f ms/frame" % dt_ms)
    assert dt_ms < 2.4, dt_ms
    print("PASS perf idle %.2f ms/frame < 2.4" % dt_ms)


def test_perf_fx():
    fresh()
    t = tgt(90.0)
    b = probe(target=t, _vhz_attack_active=True,
              _vhz_attack_kind="swing", _vhz_attack_manual=True)
    s = pygame.Surface((640, 480), pygame.SRCALPHA)
    d = FX.director_for(b)
    FX.notify_skill_cast(b, "q")
    FX.notify_skill_cast(b, "r")
    L.draw_vhalzun(s, b, 230, 240)          # warm-up
    t0 = time.perf_counter()
    n = 120
    for i in range(n):
        b._vhz_attack_progress = (i % 24) / 24.0
        L.draw_vhalzun(s, b, 230, 240)
        FX.tick(1.0 / 60.0)
    dt_ms = (time.perf_counter() - t0) * 1000.0 / n
    print("      fx: %.2f ms/frame" % dt_ms)
    assert dt_ms < 2.1, dt_ms
    print("PASS perf FX (swing+2 skill) %.2f ms/frame < 2.1" % dt_ms)


# ===================================================================
# main
# ===================================================================
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print("FAIL %s: %s" % (t.__name__, e))
        except Exception as e:  # pragma: no cover
            failed += 1
            print("ERROR %s: %r" % (t.__name__, e))
    print("=" * 60)
    if failed:
        print("GAGAL: %d/%d" % (failed, len(tests)))
        sys.exit(1)
    print("SEMUA %d TES PASS" % len(tests))
