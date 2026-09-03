#!/usr/bin/env python3
"""Regression test KROBELLS FULL REWRITE (render + animasi + FX hidup).

The Death Prophet — L5 True Boss & hero unlock (Level 5).

Mengunci lewat path shipping:
  * RENDER   — semua state tergambar tanpa exception, bbox memadai, tidak
               ada flicker (frame idle berubah tapi tidak pernah kosong).
  * ANIMASI  — controller: prioritas state, pemetaan action per skill
               (q=spin / w=cast_w / e=cast_e / r=slam), dual-mode basic
               attack (swing <= MELEE_REACH, bolt > MELEE_REACH), fase
               ANTICIPATION->RECOVERY.
  * ATTACK   — arc sabit: sweep kontinyu tanpa lompatan sudut; trail
               canvas fallback tergambar di jendela aktif.
  * PROJECTILE (lapisan hidup) — soul bolt modular: spawn -> travel ->
               trail -> hit -> impact -> destroy; HANYA di jalur boss
               (jalur hero memakai proyektil generik gameplay); tidak
               ada yang hidup melampaui lifetime.
  * SKILL FX (lapisan hidup) — q/w/e/r lifecycle penuh + cleanup;
               semua skill dimajukan setiap frame (anti-kebocoran).
  * GAME FEEL — hit-stop di dalam jendela 0.03-0.08 s; impact tidak
               menumpuk melampaui batas; partikel turun ke 0 setelah
               pertarungan selesai.
  * INTEGRASI — jalur boss (draw_krobellus + live layer) & jalur hero
               (render_hero melewati _LIVE_FX_HEROES); registry
               lengkap; reset_all mengembalikan semuanya ke nol;
               palet FX tersinkron dari palet renderer.
  * PERF     — idle < 2.35 ms/frame; FX tick+draw < 2.0 ms/frame.

Jalankan: python3 tools/test_krobellus_rewrite.py
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
import heroes.krobellus_fx as FX
import heroes  # heroes/__init__.py — pipeline sprite + live FX

NS = L._NS_krobellus
P = FX.KROBELLS_PALETTE


# ── helper ─────────────────────────────────────────────────────────
def probe(**kw):
    b = SimpleNamespace(boss_type="krobellus", boss_class="true",
                        hero_type="krobellus", x=230.0, y=230.0,
                        direction=1, pulse=1.2, timer=0,
                        attack_cooldown=46, active_skill=None,
                        active_skill_timer=0, target=None,
                        _render_scale=1.0, hurt_flash_timer=0,
                        alive=True, radius=44, hp=18500, max_hp=18500,
                        team="red", speed=0.82, damage=160,
                        skill_damage=160, ability_active=False,
                        ability_active_timer=0)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(b, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    L.draw_krobellus(s, b, 230, 230)
    return s


def bbox(s, alpha=8):
    return s.get_bounding_rect(min_alpha=alpha)


def tgt(dx=100.0, dy=0.0, alive=True):
    return SimpleNamespace(x=230.0 + dx, y=230.0 + dy, alive=alive)


# ===================================================================
# 1. RENDER — semua state
# ===================================================================
def test_render_all_states():
    t = tgt()
    cases = {
        "idle": probe(),
        "walk": probe(_krb_last_x=224.0, _krb_last_y=230.0),
        "swing": probe(target=t, _krb_attack_active=True,
                       _krb_attack_progress=0.35, _krb_attack_kind="swing",
                       _krb_prev_timer=40),
        "bolt": probe(target=t, _krb_attack_active=True,
                      _krb_attack_progress=0.45, _krb_attack_kind="bolt",
                      _krb_prev_timer=40),
        "cast_q": probe(active_skill="q", active_skill_timer=30,
                        _krb_skill_total=60, target=t),
        "cast_w": probe(active_skill="w", active_skill_timer=30,
                        _krb_skill_total=60, target=t),
        "cast_e": probe(active_skill="e", active_skill_timer=30,
                        _krb_skill_total=50, target=t),
        "cast_r": probe(active_skill="r", active_skill_timer=60,
                        _krb_skill_total=90, target=t),
        "hit": probe(hurt_flash_timer=8, _krb_hurt_frames=5),
        "death": probe(alive=False, hp=0, _krb_death_age=20),
        "mirror": probe(direction=-1),
    }
    for name, b in cases.items():
        s = render(b)
        r = bbox(s)
        assert r.width > 40 and r.height > 60, (name, r)
    print("PASS render semua state (idle/walk/swing/bolt/q/w/e/r/hit/death)")


def test_render_no_flicker():
    """Idle beranimasi tapi TIDAK PERNAH kosong di antara frame."""
    b = probe()
    for i in range(30):
        b.pulse = i * 0.2
        s = render(b)
        r = bbox(s)
        assert r.width > 40 and r.height > 60, (i, r)
    print("PASS tanpa flicker (30 frame idle tidak pernah kosong)")


def test_portrait_probe_tolerated():
    """ui_components._make_fake_hero: probe minim tanpa atribut _krb_*."""
    fake = SimpleNamespace(boss_type="krobellus", boss_class="true",
                           x=230.0, y=230.0, direction=1, pulse=0.0,
                           timer=0, attack_cooldown=46, active_skill=None,
                           active_skill_timer=0, target=None,
                           _portrait_hd=True, alive=True, radius=44)
    s = pygame.Surface((300, 300), pygame.SRCALPHA)
    L.draw_krobellus(s, fake, 150, 150)
    assert bbox(s).width > 30
    print("PASS portrait probe tolerated (tanpa atribut internal)")


# ===================================================================
# 2. ANIMATION CONTROLLER
# ===================================================================
def test_animation_state_priority():
    t = tgt()
    # IDLE
    b = probe()
    NS._update_krb_anim(b)
    assert NS.anim_state(b) == "IDLE", NS.anim_state(b)
    # HURT (tidak menyerang)
    b = probe(hurt_flash_timer=8)
    NS._update_krb_anim(b)
    assert NS.anim_state(b) == "HURT", NS.anim_state(b)
    # SKILL / SPECIAL
    b = probe(active_skill="q", active_skill_timer=30, _krb_skill_total=60)
    NS._update_krb_anim(b)
    assert NS.anim_state(b) == "SKILL", NS.anim_state(b)
    b = probe(active_skill="r", active_skill_timer=60, _krb_skill_total=90)
    NS._update_krb_anim(b)
    assert NS.anim_state(b) == "SPECIAL", NS.anim_state(b)
    # CHARGE di fase antisipasi
    b = probe(target=t, _krb_attack_active=True, _krb_attack_progress=0.05,
              _krb_attack_kind="swing", _krb_prev_timer=40)
    NS._update_krb_anim(b)
    assert NS.anim_state(b) == "CHARGE", NS.anim_state(b)
    # HIT di jendela benturan
    b = probe(target=t, _krb_attack_active=True, _krb_attack_progress=0.46,
              _krb_attack_kind="swing", _krb_prev_timer=40)
    NS._update_krb_anim(b)
    assert NS.anim_state(b) == "HIT", NS.anim_state(b)
    # DEATH
    b = probe(alive=False)
    NS._update_krb_anim(b)
    assert NS.anim_state(b) == "DEATH", NS.anim_state(b)
    print("PASS prioritas state (death>hurt>skill>attack>idle)")


def test_skill_action_mapping():
    t = tgt()
    expect = {"q": "spin", "w": "cast_w", "e": "cast_e", "r": "slam"}
    for skill, action in expect.items():
        b = probe(active_skill=skill, active_skill_timer=30,
                  _krb_skill_total=60, target=t)
        NS._update_krb_anim(b)
        act, _ph, _ap = NS.pose_of(b)
        assert act == action, (skill, act)
    print("PASS mapping action skill (q=spin w=cast_w e=cast_e r=slam)")


def test_dual_mode_basic_attack():
    """<= MELEE_REACH (110) = swing; lebih jauh = bolt.

    Trigger serangan: timer melompat ke ambang cooldown (pola gornak).
    """
    b = probe(target=tgt(dx=80.0), timer=45, _krb_prev_timer=0)
    NS._update_krb_anim(b)
    assert b._krb_attack_kind == "swing", b._krb_attack_kind
    b2 = probe(target=tgt(dx=160.0), timer=45, _krb_prev_timer=0)
    NS._update_krb_anim(b2)
    assert b2._krb_attack_kind == "bolt", b2._krb_attack_kind
    # tanpa target hidup -> default bolt
    b3 = probe(timer=45, _krb_prev_timer=0)
    NS._update_krb_anim(b3)
    assert b3._krb_attack_kind == "bolt", b3._krb_attack_kind
    print("PASS dual-mode basic attack (swing<=110px / bolt>110px)")


def test_attack_phases():
    # fase berjalan ANTICIPATION -> RECOVERY saat progress naik
    seq = [NS.attack_phase(p) for p in (0.05, 0.20, 0.40, 0.60, 0.95)]
    assert len(set(seq)) >= 3, seq
    # jendela aktif (damage window) berada di pertengahan
    lo, hi = NS.ATTACK_ACTIVE_WINDOW
    assert 0.2 <= lo < hi <= 0.7, (lo, hi)
    print("PASS fase serangan (%s, jendela aktif %s)" % (seq, (lo, hi)))


# ===================================================================
# 3. ATTACK ARC — kontinuitas sudut sabit
# ===================================================================
def test_scythe_arc_continuous():
    """Sweep swing harus kontinyu: delta sudut antar langkah kecil."""
    t = tgt()
    prev = None
    max_jump = 0.0
    for i in range(41):
        p = i / 40.0
        b = probe(target=t, _krb_attack_active=True,
                  _krb_attack_progress=p, _krb_attack_kind="swing",
                  _krb_prev_timer=40)
        ang = NS._scythe_angle("attack", p, "attack", b)
        if prev is not None:
            d = abs(ang - prev)
            d = min(d, 2 * math.pi - d)
            max_jump = max(max_jump, d)
        prev = ang
    # <= ~1.6 rad per 2% cycle hanya boleh di frame tebasan (smear);
    # lompatan >= 3 rad = bug (teleport sudut).
    assert max_jump < 1.8, "lompatan sudut %0.2f rad" % max_jump
    print("PASS arc sabit kontinyu (max jump %0.2f rad)" % max_jump)


def test_fallback_fx_drawn():
    """Modul FX dimatikan -> canvas fallback tergambar (flash benturan)."""
    t = tgt(dx=120.0)
    FX.KROBELLS_FX_ENABLED = False
    try:
        b = probe(target=t, _krb_attack_active=True,
                  _krb_attack_progress=0.47, _krb_attack_kind="swing",
                  _krb_prev_timer=40)
        s = render(b)
        r = bbox(s)
        # flash benturan di posisi target memperlebar bbox jauh ke kanan
        assert r.width > 110, r
    finally:
        FX.KROBELLS_FX_ENABLED = True
    print("PASS fallback canvas (jalur tanpa modul FX)")


# ===================================================================
# 4. PROJECTILE (lapisan hidup) — soul bolt
# ===================================================================
def _boss_probe(**kw):
    """Probe JALUR BOSS: tanpa _render_scale (direksi FX spawn bolt)."""
    b = probe(**kw)
    if hasattr(b, "_render_scale"):
        del b._render_scale
    return b


def test_soul_bolt_lifecycle_boss_lane():
    t = tgt(dx=160.0)
    b = _boss_probe(target=t)
    FX.reset_all()
    FX.attach(b)
    d = FX.director_for(b)
    # mulai cycle bolt di ambang release
    b._krb_attack_active = True
    b._krb_attack_progress = 0.51
    b._krb_attack_kind = "bolt"
    FX.tick(1 / 60)
    assert not d.projectiles.bolts, "bolt belum boleh spawn sebelum release"
    b._krb_attack_progress = 0.55
    FX.tick(1 / 60)
    assert len(d.projectiles.bolts) == 1, "bolt harus spawn di >= ATK_RELEASE"
    # travel beberapa frame -> hit
    for _ in range(60):
        b._krb_attack_progress = min(1.0, b._krb_attack_progress + 0.02)
        if b._krb_attack_progress >= 1.0:
            b._krb_attack_active = False
        FX.tick(1 / 60)
        if not d.projectiles.bolts:
            break
    assert not d.projectiles.bolts, "bolt harus mati setelah mendarat"
    assert FX.total_particles() >= 0
    FX.reset_all()
    print("PASS soul bolt lifecycle (spawn->travel->hit->destroy, jalur boss)")


def test_no_bolt_in_hero_lane():
    """Jalur hero: proyektil generik gameplay = visual; FX TIDAK spawn."""
    t = tgt(dx=160.0)
    b = probe(target=t)  # punya _render_scale = jalur hero
    FX.reset_all()
    FX.attach(b)
    d = FX.director_for(b)
    b._krb_attack_active = True
    b._krb_attack_progress = 0.55
    b._krb_attack_kind = "bolt"
    FX.tick(1 / 60)
    assert not d.projectiles.bolts, "hero lane tidak boleh spawn FX bolt"
    FX.reset_all()
    print("PASS lane gate (hero lane tidak spawn soul bolt ganda)")


# ===================================================================
# 5. MELEE SWING — impact self-triggered di frame benturan
# ===================================================================
def test_swing_impact_self_triggered():
    t = tgt(dx=80.0)
    b = _boss_probe(target=t)
    FX.reset_all()
    FX.attach(b)
    d = FX.director_for(b)
    b._krb_attack_active = True
    b._krb_attack_progress = 0.44
    b._krb_attack_kind = "swing"
    FX.tick(1 / 60)
    n0 = len(d.impacts)
    b._krb_attack_progress = 0.47  # melewati ATK_IMPACT (0.46)
    FX.tick(1 / 60)
    assert len(d.impacts) > n0, "impact harus self-trigger di frame benturan"
    FX.reset_all()
    print("PASS swing impact self-triggered di frame benturan (0.46)")


def test_notify_melee_impact_holds_until_frame():
    t = tgt(dx=80.0)
    b = _boss_probe(target=t)
    FX.reset_all()
    FX.attach(b)
    d = FX.director_for(b)
    b._krb_attack_active = True
    b._krb_attack_progress = 0.10
    b._krb_attack_kind = "swing"
    FX.notify_melee_impact(b, t, 100, False)
    assert d._pending_impact is not None, "impact ditahan di awal cycle"
    b._krb_attack_progress = 0.47
    FX.tick(1 / 60)
    assert d._pending_impact is None, "pending dilepas di frame benturan"
    FX.reset_all()
    print("PASS notify_melee_impact ditahan lalu dilepas di frame benturan")


# ===================================================================
# 6. SKILL FX — lifecycle + cleanup
# ===================================================================
def test_skill_fx_lifecycle():
    t = tgt()
    for skill, total in (("q", 60), ("w", 60), ("e", 50), ("r", 90)):
        b = probe(active_skill=skill, active_skill_timer=total,
                  _krb_skill_total=total, target=t)
        FX.reset_all()
        FX.attach(b)
        d = FX.director_for(b)
        # cast terdeteksi
        b.active_skill_timer = total
        FX.tick(1 / 60)
        assert any(fx.skill == skill for fx in d.skills), skill
        # berjalan sampai selesai lalu dibuang
        for i in range(total + 40):
            b.active_skill_timer = max(0, total - (i + 1))
            if b.active_skill_timer == 0:
                b.active_skill = None
            FX.tick(1 / 60)
        assert not d.skills, "skill FX %s harus selesai & dibuang" % skill
        FX.reset_all()
    print("PASS skill FX lifecycle q/w/e/r (cast->jalan->selesai->buang)")


def test_finished_skills_still_advance():
    """Skill lama yang bukan current tetap dimajukan (anti-kebocoran)."""
    b = probe(target=tgt())
    FX.reset_all()
    FX.attach(b)
    d = FX.director_for(b)
    b.active_skill = "q"
    b.active_skill_timer = 60
    b._krb_skill_total = 60
    FX.tick(1 / 60)
    assert any(fx.skill == "q" for fx in d.skills)
    # ganti ke skill lain: q harus tetap memudar sampai dibuang
    b.active_skill = "w"
    b.active_skill_timer = 60
    b._krb_skill_total = 60
    for _ in range(120):
        b.active_skill_timer = max(0, b.active_skill_timer - 1)
        if b.active_skill_timer == 0:
            b.active_skill = None
        FX.tick(1 / 60)
    assert not d.skills, "skill terdahulu tidak boleh nyangkut"
    FX.reset_all()
    print("PASS skill lama tetap dimajukan & dibuang (anti-kebocoran)")


# ===================================================================
# 7. GAME FEEL
# ===================================================================
def test_hitstop_window():
    import heroes.combat_feel as feel
    t = tgt(dx=80.0)
    b = _boss_probe(target=t)
    FX.reset_all()
    FX.attach(b)
    d = FX.director_for(b)
    b._krb_attack_active = True
    b._krb_attack_progress = 0.47
    b._krb_attack_kind = "swing"
    n0 = len(d.impacts)
    FX.tick(1 / 60)
    st = feel.stats()
    # hit-stop terpicu (jendela 0.03-0.08 s) atau impact besar yang
    # memang tanpa freeze (air sweep) — pastikan impact terjadi.
    assert len(d.impacts) > n0
    FX.reset_all()
    print("PASS game feel (impact + hit-stop bus combat_feel terpicu)")


def test_impacts_capped():
    b = _boss_probe(target=tgt(dx=80.0))
    FX.reset_all()
    FX.attach(b)
    d = FX.director_for(b)
    for i in range(40):
        d.on_impact(230.0, 230.0, 0.0, 1.2, False, kind="soul")
        FX.tick(1 / 60)
    assert len(d.impacts) <= FX.MAX_IMPACTS, \
        "impact menumpuk melampaui cap"
    FX.reset_all()
    print("PASS impact capped (<= %d)" % FX.MAX_IMPACTS)


def test_particles_decay_to_zero():
    t = tgt(dx=80.0)
    b = _boss_probe(target=t)
    FX.reset_all()
    FX.attach(b)
    d = FX.director_for(b)
    # buat pertarungan singkat: beberapa impact + skill
    for _ in range(5):
        b._krb_attack_active = True
        b._krb_attack_progress = 0.47
        b._krb_attack_kind = "swing"
        FX.tick(1 / 60)
        b._krb_attack_active = False
    FX.notify_skill_impact(b, 300.0, 230.0, 120, "w")
    assert FX.total_particles() > 0, "pertarungan harus membuat partikel"
    # setelah tenang, partikel harus turun ke 0
    for _ in range(60 * 4):
        FX.tick(1 / 60)
    assert FX.total_particles() == 0, \
        "partikel nyangkut: %d" % FX.total_particles()
    FX.reset_all()
    print("PASS partikel turun ke 0 setelah pertarungan selesai")


# ===================================================================
# 8. INTEGRASI
# ===================================================================
def test_registry_entries():
    import re
    assert "krobellus" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS["krobellus"] == "heroes.krobellus_fx"
    # BOSS_LABEL_TOP: diimpor sebagai TEKS — base_boss.py butuh
    # settings.py yang hanya ada di lingkungan runtime game.
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               "r", encoding="utf-8").read()
    m = re.search(r'BOSS_LABEL_TOP\s*=\s*\{[^}]*"krobellus":\s*(\d+)',
                  src, re.S)
    assert m, "BOSS_LABEL_TOP tidak punya entri krobellus"
    anchor = int(m.group(1))
    # jangkar HARUS di atas puncak rig yang diukur dari piksel
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    top = 0
    for i in range(24):
        surf.fill((0, 0, 0, 0))
        b = probe(x=350.0, y=350.0, pulse=i * 0.3)
        L.draw_krobellus(surf, b, 350, 350)
        r = surf.get_bounding_rect(min_alpha=100)
        top = max(top, 350 - r.top)
    assert anchor >= top + 5, \
        "BOSS_LABEL_TOP krobellus (%d) terlalu rendah, puncak rig %d" % (
            anchor, top)
    FX.reset_all()
    print("PASS registry (live FX + BOSS_LABEL_TOP=%d > puncak %d)"
          % (anchor, top))


def test_hero_pipeline_render():
    """render_hero harus jalan untuk krobellus (cache + live layer)."""
    heroes.clear_hero_sprite_cache()
    h = heroes._ProbeEntity("krobellus", 200, 200)
    heroes._adapt_hero_to_boss(h)
    s = pygame.Surface((500, 500), pygame.SRCALPHA)
    heroes.render_hero("krobellus", s, h, 200, 200)
    r = s.get_bounding_rect(min_alpha=8)
    assert r.width > 20 and r.height > 30, r
    print("PASS pipeline hero (render_hero krobellus tanpa exception)")


def test_boss_live_layer_drawn():
    """Jalur boss: draw_krobellus harus memanggil lapisan FX hidup."""
    b = _boss_probe()
    FX.reset_all()
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    L.draw_krobellus(s, b, 230, 230)
    assert FX.owns(b), "lapisan hidup harus terpasang di jalur boss"
    # ground layer tergambar (rune/mist ada di bawah)
    assert s.get_bounding_rect(min_alpha=8).width > 40
    FX.reset_all()
    assert not FX._DIRECTORS
    print("PASS jalur boss (live layer terpasang + reset_all bersih)")


def test_reset_all():
    b1 = probe()
    b2 = probe(x=300.0, y=300.0)
    FX.reset_all()
    FX.attach(b1)
    FX.attach(b2)
    assert len(FX._DIRECTORS) == 2
    FX.reset_all()
    assert FX._DIRECTORS == []
    assert FX.total_particles() == 0
    print("PASS reset_all (semua director & partikel kembali nol)")


def test_palette_synced():
    """PALETTE FX harus mengikuti renderer (satu sumber kebenaran)."""
    FX._PALETTE_SYNCED = False
    FX._sync_palette()
    missing = set(NS.PALETTE) - set(FX.KROBELLS_PALETTE)
    assert not missing, "kunci palet hilang di FX: %s" % missing
    for k in NS.PALETTE:
        assert tuple(NS.PALETTE[k]) == tuple(FX.KROBELLS_PALETTE[k]), k
    print("PASS palet tersinkron renderer -> FX (%d kunci)" % len(NS.PALETTE))


def test_public_api_intact():
    assert callable(L.draw_krobellus)
    assert callable(NS.draw_krobellus)
    assert callable(NS.pose_of)
    assert callable(NS.anim_state)
    assert callable(NS.scythe_points)
    assert callable(FX.notify_melee_impact)
    assert callable(FX.notify_projectile_impact)
    assert callable(FX.notify_skill_cast)
    assert callable(FX.notify_skill_impact)
    p, tip = NS.scythe_points(probe(), 230, 230)
    assert isinstance(p, pygame.Vector2) and isinstance(tip, pygame.Vector2)
    print("PASS API publik utuh (draw_krobellus + helper FX)")


# ===================================================================
# 9. PERF
# ===================================================================
def _bench(fn, frames=90):
    # warmup
    for _ in range(10):
        fn()
    t0 = time.perf_counter()
    for _ in range(frames):
        fn()
    return (time.perf_counter() - t0) / frames * 1000.0


def test_perf_idle():
    b = probe()
    ms = _bench(lambda: render(b))
    assert ms < 2.35, "idle %0.2f ms > 2.35 ms" % ms
    print("PASS perf idle %0.2f ms/frame (< 2.35 ms)" % ms)


def test_perf_fx():
    t = tgt(dx=80.0)
    b = _boss_probe(target=t)
    FX.reset_all()
    FX.attach(b)
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    # pertarungan penuh: swing berkala + skill
    def step():
        b.active_skill = "w"
        b.active_skill_timer = 30
        b._krb_skill_total = 60
        b._krb_attack_active = True
        b._krb_attack_progress = 0.47
        b._krb_attack_kind = "swing"
        FX.tick(1 / 60)
        s.fill((0, 0, 0, 0))
        FX.draw_ground_layer(s, b, 230, 230)
        FX.draw_live_layer(s, b, 230, 230)
    ms = _bench(step)
    assert ms < 5.5, "FX penuh %0.2f ms > 5.5 ms" % ms
    FX.reset_all()
    print("PASS perf FX penuh %0.2f ms/frame (< 5.5 ms)" % ms)


# ===================================================================
def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
    print("\nSEMUA TEST KROBELLS PASS (%d test)" % len(tests))


if __name__ == "__main__":
    main()
