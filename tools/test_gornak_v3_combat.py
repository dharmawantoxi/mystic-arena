#!/usr/bin/env python3
"""Regression test permanen untuk sistem tempur GORNAK v3.

Gornak adalah satu-satunya unit yang digambar lewat kode yang sama di DUA
jalur: lane boss (``Boss.draw`` -> ``_NS_gornak.draw_gornak``) dan lane hero
(``heroes.render_hero`` -> sprite di-cache + smoothscale). Karena itu sistem
tempurnya dipecah:

  * ``bosses/level1.py::_NS_gornak``  = badan, rig, pose, controller animasi,
    telegraph tanah, dan semua FALLBACK kalau modul FX tidak tersedia.
  * ``heroes/gornak_fx.py``           = lapisan hidup 1:1 di luar sprite cache:
    trail bilah, partikel, proyektil Mana Break, impact, hit-stop, shake,
    overlay debug.
  * ``heroes/combat_feel.py``         = bus SHARED (hit-stop + shake) yang
    dipakai Zephyr dan Gornak, jadi dua karakter tidak menumpuk freeze.

Uji ini mengunci kontrak yang gampang rusak saat orang lain menyentuh salah
satu dari ketiganya:

  1. 100% prosedural (tanpa image.load / PNG / sprite sheet) di KEDUA modul.
  2. Palet + API publik (backward-compat untuk pemanggil lama).
  3. Controller animasi: fase, urutan, delta-time, jendela hit, prioritas
     state, dan semua nama atribut lama yang masih dipakai renderer/tools.
  4. Ayunan berbasis busur (bukan lerp linear) + trail dari histori bilah.
  5. Particle system berbatas (cap dihormati, pool dipakai ulang, meluruh).
  6. Lifecycle projectile penuh (spawn -> travel -> hit -> impact -> mati).
  7. Lifecycle skill FX (cast -> charge -> release -> area -> impact -> fade)
     dan pusat yang benar (R di pusat void, W di titik asal blink).
  8. Impact + screen shake + hit-stop yang SELALU terkuras (tidak ada efek
     abadi), dengan hit-stop di 0.03-0.08 s.
  9. Supresi ganda: saat lapisan hidup mengambil alih, renderer tidak
     menggambar pita ayunan / proc foreground dua kali - dan sebaliknya
     fallback canvas tetap jalan kalau modul FX tidak dimuat.
 10. Overlay debug (DEBUG_CHARACTER) + performansi lapisan hidup.

Jalankan:  python3 -m pytest tools/test_gornak_v3_combat.py -q
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
from heroes import gornak_fx as F                          # noqa: E402
from bosses.level1 import _NS_gornak as G                   # noqa: E402

DT = 1.0 / 60.0
COOLDOWN = 38                     # attack_cooldown gornak di boss_data.py
PHASE_ORDER = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT",
               "FOLLOW", "RECOVERY"]


# ── helper ────────────────────────────────────────────────────────────────
def fresh_hero(x=0.0, y=0.0, cooldown=COOLDOWN, scale=None):
    """Unit Gornak minim. ``scale=None`` = jalur BOSS (tanpa _render_scale)."""
    h = _ProbeEntity("gornak", x, y)
    h.boss_type = "gornak"
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = cooldown
    h.range = 60
    h.speed = 1.6
    h.hp = h.max_hp = 800
    h.radius = 16
    h.skill_damage = 180
    h.skill_range = 180
    h.hurt_flash_timer = 0
    h.blink_from_x = h.blink_from_y = 0
    h.mana_void_x = h.mana_void_y = 0
    if scale is not None:
        h._render_scale = scale
    return h


def dummy_target(x=180.0, y=0.0):
    t = _ProbeEntity("creep", x, y)
    t.alive = True
    t.radius = 14
    return t


def attack_frames(hero, cooldown=COOLDOWN):
    """Satu siklus serangan penuh lewat controller renderer.

    Snapshot per frame; ``None`` menandai "serangan selesai". Semua angka
    dibaca dari atribut yang DIHASILKAN controller, jadi kalau ada yang
    menukar sumber timing, uji ini yang berteriak.
    """
    hero._gnk_attack_active = False
    hero._gnk_attack_frame = 0
    hero._gnk_previous_timer = 0
    hero._gnk_state = "IDLE"
    hero._gnk_state_prev = "IDLE"
    hero._gnk_state_time = 0.0
    hero._gnk_hurt_frames = 0
    out = []
    for t in range(cooldown, -1, -1):
        hero.timer = t
        G._update_gnk_attack_anim(hero)
        out.append({
            "timer": t,
            "active": bool(hero._gnk_attack_active),
            "frame": int(hero._gnk_attack_frame),
            "progress": float(hero._gnk_attack_progress),
            "phase": hero._gnk_attack_phase,
            "state": hero._gnk_state,
            "hit": bool(getattr(hero, "_gnk_hit_active", False)),
            "dt": float(hero._gnk_dt),
        })
    return out


def run_live(hero, frames, dt=DT, attack=False, skill=None, skill_dur=40,
             surf=None):
    """Jalankan lapisan hidup selama ``frames`` frame, kembalikan surface.

    Surface DI-CLEAR tiap frame: test "tidak ada efek abadi" membandingkan
    isi buffer sebelum/sesudah, dan blit kumulatif akan menyembunyikannya.
    """
    if surf is None:
        surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    for i in range(frames):
        hero.pulse += 0.3
        if attack:
            # mode manual: pemanggil yang menggerakkan progress (sama seperti
            # tools/_audit_gornak_v2.py), controller tinggal menurunkan fase
            hero._gnk_attack_active = True
            hero._gnk_attack_manual = True
            hero._gnk_attack_progress = (i % COOLDOWN) / float(COOLDOWN)
        if skill is not None:
            hero.active_skill = skill
            hero.active_skill_timer = max(0, skill_dur - i)
            if hero.active_skill_timer == 0:
                hero.active_skill = None
        G._update_gnk_attack_anim(hero)
        F.tick(dt)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, hero, hero.x, hero.y)
        F.draw_live_layer(surf, hero, hero.x, hero.y)
    return surf


def engine_attack_frame(hero, t, cooldown=COOLDOWN):
    """Satu frame serangan VERSI ENGINE: timer turun, controller yang kerja."""
    hero.timer = t
    G._update_gnk_attack_anim(hero)


def start_engine_attack(hero, cooldown=COOLDOWN):
    hero._gnk_attack_active = False
    hero._gnk_attack_manual = False
    hero._gnk_attack_frame = 0
    hero._gnk_previous_timer = 0
    hero.timer = cooldown
    G._update_gnk_attack_anim(hero)


def _clear_feel():
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()
    FEEL.reset()


@pytest.fixture(autouse=True)
def _clean_fx():
    """Setiap test mulai dari FX kosong dan bus feel kosong."""
    F.reset_all()
    _clear_feel()
    yield
    F.reset_all()
    _clear_feel()


# ══════════════════════════════════════════════════════════════════════════
# 1. 100% PROSEDURAL & API PUBLIK
# ══════════════════════════════════════════════════════════════════════════
def test_tidak_memuat_asset_eksternal():
    """Baik lapisan FX maupun controller renderer: tanpa asset apa pun."""
    for rel in (os.path.join("heroes", "gornak_fx.py"),
                os.path.join("heroes", "combat_feel.py")):
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for bad in ("pygame.image.load", "image.load(",
                    "pygame.mixer.Sound", 'pygame.font.Font("',
                    "pygame.font.Font('", ".png", ".jpg", ".jpeg", ".gif",
                    ".bmp", ".ogg", ".wav", "surf(", "load_asset"):
            assert bad not in src, "%s memakai %s" % (rel, bad)
    # jalur renderer: sumber _NS_gornak juga tidak boleh memuat bitmap
    src = inspect.getsource(G)
    assert "pygame.image.load" not in src


def test_api_publik_lapisan_hidup():
    for name in ("attach", "owns", "director_for", "tick", "reset_all",
                 "total_particles", "draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_projectile_impact",
                 "notify_skill_impact", "notify_skill_cast",
                 "draw_mana_bolt", "hit_stop", "shake",
                 "should_freeze_frame", "clear_cache", "cache_size",
                 "GORNAK_PALETTE", "GORNAK_FX_ENABLED",
                 "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
                 "GornakProjectile", "ProjectileSystem", "SkillFX",
                 "GornakFXDirector"):
        assert hasattr(F, name), "API hilang: gornak_fx.%s" % name


def test_api_publik_renderer_tetap_ada():
    """Renderer tidak boleh kehilangan nama yang dipakai Boss.draw / tools."""
    for name in ("draw_gornak", "_resolve_pose", "_update_gnk_attack_anim",
                 "_detect_moving", "_attack_curve", "_blade_angle",
                 "_tip_local", "_tip_screen", "_draw_crescent_slash",
                 "_draw_manabreak_ground", "_draw_manabreak_foreground",
                 "_draw_cast_shockwave", "_fx_scale", "_skill_progress",
                 "SKILL_DUR", "ACTIONS", "PALETTE"):
        assert hasattr(G, name), "kontrak renderer hilang: %s" % name


def test_palet_lengkap_dan_sinkron_dengan_renderer():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in F.GORNAK_PALETTE, "kunci palet hilang: %s" % key
        col = F.GORNAK_PALETTE[key]
        assert len(col) >= 3 and all(0 <= c <= 255 for c in col[:3])
    # palet lapisan hidup = palet renderer (satu karakter, satu warna).
    # _PALETTE_SYNC adalah satu-satunya jembatan; tidak boleh ada yang
    # melenceng, kalau tidak si layer hidup jadi karakter lain warnanya.
    drift = [dst for dst, src in F._PALETTE_SYNC.items()
             if src in G.PALETTE and tuple(F.P[dst][:3])
             != tuple(G.PALETTE[src][:3])]
    assert not drift, "drift palet: %s" % drift


def test_debug_mode_ada_dan_mati_secara_default():
    assert G.DEBUG_CHARACTER is False
    assert F.DEBUG_CHARACTER is False


def test_bus_feel_dipakai_bersama():
    """Zephyr & Gornak berbagi satu bus - tidak ada salinan matematika."""
    from heroes import zephyr_fx as ZF
    assert ZF.HITSTOP is FEEL.HITSTOP
    assert ZF.SHAKE is FEEL.SHAKE
    src = inspect.getsource(F.should_freeze_frame)
    assert "_feel.should_freeze_frame" in src, src
    assert "_feel" in inspect.getsource(F.hit_stop)


# ══════════════════════════════════════════════════════════════════════════
# 2. CONTROLLER ANIMASI (state, fase, timing, delta time)
# ══════════════════════════════════════════════════════════════════════════
def test_urutan_fase_ayunan_lengkap():
    order = []
    for s in attack_frames(fresh_hero()):
        if not s["active"]:
            continue
        p = s["phase"]
        if not order or order[-1] != p:
            order.append(p)
    assert order == PHASE_ORDER, order


def test_setiap_fase_punya_durasi():
    """Fase tanpa durasi = animasi 'kedip'; tiap fase harus >= 1 frame."""
    counts = {p: 0 for p in PHASE_ORDER}
    for s in attack_frames(fresh_hero()):
        if s["active"]:
            counts[s["phase"]] += 1
    for p, n in counts.items():
        assert n >= 1, "fase %s tidak pernah muncul" % p


def test_progress_monoton_dan_habis_tepat():
    snaps = [s for s in attack_frames(fresh_hero()) if s["active"]]
    ps = [s["progress"] for s in snaps]
    assert ps[0] == pytest.approx(0.0, abs=1e-6)
    assert ps[-1] == pytest.approx(1.0, abs=1e-6)
    assert all(b >= a - 1e-9 for a, b in zip(ps, ps[1:])), ps


def test_delta_time_dipakai_dan_dijepit():
    """Controller harus expose dt (detik) yang masuk akal, bukan 0/frame."""
    snaps = attack_frames(fresh_hero())
    for s in snaps:
        assert 0.0 < s["dt"] <= 0.05, s["dt"]
    # dipakai juga oleh FX: dt yang sama dibaca lapisan hidup
    h = fresh_hero()
    G._update_gnk_attack_anim(h)
    assert h._gnk_dt > 0.0
    assert h._gnk_frame_duration == pytest.approx(h._gnk_dt)


def test_jendela_hit_aktif_di_tengah_ayunan():
    snaps = [s for s in attack_frames(fresh_hero()) if s["active"]]
    hit = [s["progress"] for s in snaps if s["hit"]]
    assert hit, "jendela hit tidak pernah aktif"
    assert min(hit) >= G.ATTACK_ACTIVE_WINDOW[0] - 1e-6
    assert max(hit) < G.ATTACK_ACTIVE_WINDOW[1] + 1e-6
    assert not snaps[-1]["hit"] and not snaps[-2]["hit"]
    # jendela harus jatuh di fase tebasan/impact, bukan di recovery
    hit_phases = {s["phase"] for s in snaps if s["hit"]}
    assert hit_phases <= {"SWING", "IMPACT", "FOLLOW"}, hit_phases


def test_prioritas_state_dan_kunci_death():
    h = fresh_hero()
    h._gnk_hurt_frames = 6
    assert G._resolve_anim_state(h, False, "NONE") == "HURT"
    h._gnk_hurt_frames = 0
    h.active_skill = "r"
    h.active_skill_timer = 40
    assert G._resolve_anim_state(h, False, "NONE") == "SPECIAL"
    h.active_skill = None
    h.alive = False
    assert G._resolve_anim_state(h, False, "NONE") == "DEATH"
    # DEATH tidak boleh direbut state lain di update()
    h.alive = False
    for _ in range(4):
        G._update_gnk_attack_anim(h)
    assert h._gnk_state == "DEATH"


def test_hurt_dari_flash_boss():
    """Boss men-set hurt_flash_timer 8..0; controller harus menerjemahkan."""
    h = fresh_hero()
    h.hurt_flash_timer = 9
    G._update_gnk_attack_anim(h)
    assert int(h._gnk_hurt_frames) > 0
    for _ in range(14):
        h.hurt_flash_timer = max(0, h.hurt_flash_timer - 1)   # seperti Boss
        G._update_gnk_attack_anim(h)
    assert int(h._gnk_hurt_frames) == 0


def test_state_walk_run_dari_gerakan():
    h = fresh_hero()
    G._detect_moving(h)
    h.x += 30.0
    assert G._detect_moving(h) is True
    assert h._moving_cached is True
    h.speed = 1.6
    assert G._resolve_anim_state(h, False, "NONE") == "WALK"
    h.speed = 2.6
    assert G._resolve_anim_state(h, False, "NONE") == "RUN"
    h.x -= 30.0
    G._detect_moving(h)
    G._detect_moving(h)
    assert h._moving_cached is False
    assert G._resolve_anim_state(h, False, "NONE") == "IDLE"


def test_tabel_prioritas_mengandung_semua_state_master_prompt():
    need = {"IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
            "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"}
    assert need <= set(G.ANIM_STATES), need - set(G.ANIM_STATES)
    assert G.ANIM_STATES["DEATH"] > G.ANIM_STATES["HURT"]
    assert G.ANIM_STATES["IDLE"] == min(G.ANIM_STATES.values())


def test_atribut_lama_pemain_lain_masih_diisi():
    """_gnk_attack_raw/_gnk_pose_action dipakai _audit_gornak_v2 & tools."""
    h = fresh_hero()
    for t in (COOLDOWN, 30, 20, 10, 1):
        h.timer = t
        G._update_gnk_attack_anim(h)
    assert hasattr(h, "_gnk_attack_raw") or hasattr(h, "_gnk_attack_progress")
    G.draw_gornak(pygame.Surface((240, 240), pygame.SRCALPHA), h, 120, 150)
    assert h._gnk_pose_action in G.ACTIONS


# ══════════════════════════════════════════════════════════════════════════
# 3. AYUNAN BERBASIS BUSUR + TRAIL
# ══════════════════════════════════════════════════════════════════════════
def test_ujung_bilah_mengikuti_busur_bukan_lerp():
    n = 30
    pts = [pygame.Vector2(G._tip_local("attack", 0.0, G._attack_curve(
        i / float(n)))) for i in range(n + 1)]
    a, b = pts[0], pts[-1]
    worst = 0.0
    for i, p in enumerate(pts):
        worst = max(worst, (p - a.lerp(b, i / float(n))).length())
    assert worst > 8.0, "deviasi busur hanya %.1f px" % worst


def test_ujung_bilah_kontinu_tanpa_teleport():
    """Tidak boleh ada ledakan langkah dari pose yang sedang ditahan.

    Ayunan BOLEH cepat (itu yang membuatnya terasa berbobot) tapi tidak
    boleh melompat dari "diam" ke "jauh" dalam satu frame: itu terbaca
    sebagai glitch. Dijaga dengan membandingkan tiap langkah dengan
    langkah sebelumnya.
    """
    import statistics
    n = 38                                   # == panjang serangan dlm frame
    pts = [pygame.Vector2(G._tip_local("attack", 0.0,
                                       G._attack_curve(i / float(n))))
           for i in range(n + 1)]
    steps = [(q - p).length() for p, q in zip(pts, pts[1:])]
    assert max(steps) <= 26.0, "satu langkah bilah %.1f px" % max(steps)
    for i in range(1, len(steps)):
        assert steps[i] <= 3.0 * steps[i - 1] + 6.0, (
            "bilah meledak di frame %d: %.1f px setelah %.1f px"
            % (i, steps[i], steps[i - 1]))
    assert sum(steps) > 60.0, "bilah nyaris tidak bergerak saat ayunan"
    assert statistics.median(steps) > 0.5, "hampir semua frame diam"


def test_kurva_serangan_ada_hold_dan_akselerasi():
    """Tahan di atas kepala lalu tebas cepat: kurva tidak boleh linear."""
    ramp = [G._attack_curve(i / 100.0) for i in range(101)]
    assert all(b >= a - 1e-9 for a, b in zip(ramp, ramp[1:])), "tidak monoton"
    rate = [b - a for a, b in zip(ramp, ramp[1:])]
    peak = max(rate)
    assert peak > 0.0
    # TAHAN: banyak langkah yang nyaris diam (puncak wind-up + impact hold)
    slow = sum(1 for r in rate if r < 0.2 * peak)
    assert slow >= 12, "tidak ada fase TAHAN (%d/100 langkah pelan)" % slow
    assert peak > 4.0 * min(r for r in rate if r > 0), "ayunan terlalu linear"
    # titik kunci fase = patahan kurva -> pose puncak & pose impact
    assert G._attack_curve(0.30) == pytest.approx(G._SWING_WIND, abs=0.02)
    assert G._attack_curve(0.46) == pytest.approx(G._SWING_HIT - 0.02,
                                                 abs=0.02)


def test_engine_swing_tidak_hilang_saat_timer_renderer_basi():
    """Start swing harus membaca event serangan, bukan previous timer basi."""
    h = fresh_hero(cooldown=COOLDOWN)
    h._gnk_previous_timer = 12          # tersisa dari frame/off-screen lama
    h._basic_attack_seq = 1             # ditulis engine saat basic attack
    h.timer = 24                        # serangan sudah masuk jendela swing
    G._update_gnk_attack_anim(h)
    assert h._gnk_attack_active
    assert h._gnk_attack_phase == "SWING"
    assert h._gnk_hit_active


def test_engine_swing_idempoten_dan_selesai_di_timer_nol():
    """Renderer/cache boleh memanggil controller berkali-kali per frame.

    Frame swing tidak boleh maju kalau timer belum berubah, dan akhir
    cooldown engine tidak boleh tersalah-baca sebagai mode manual.
    """
    h = fresh_hero(cooldown=COOLDOWN)
    h._basic_attack_seq = 1
    h.timer = COOLDOWN
    G._update_gnk_attack_anim(h)
    assert h._gnk_attack_frame == 0
    G._update_gnk_attack_anim(h)
    assert h._gnk_attack_frame == 0
    h.timer = COOLDOWN - 1
    G._update_gnk_attack_anim(h)
    assert h._gnk_attack_frame == 1
    G._update_gnk_attack_anim(h)
    assert h._gnk_attack_frame == 1
    for t in range(COOLDOWN - 2, -1, -1):
        h.timer = t
        G._update_gnk_attack_anim(h)
    assert not h._gnk_attack_active
    assert not getattr(h, "_gnk_attack_manual", False)
    assert h._gnk_attack_phase == "NONE"


def test_trail_dibangun_dari_histori_dan_meluruh():
    trail = F.SwingTrail()
    for i in range(F.TRAIL_SAMPLES + 8):
        trail.push(pygame.Vector2(10 + i, 20), pygame.Vector2(40 + i, 5))
        trail.update(DT)
    assert len(trail.points) <= F.TRAIL_SAMPLES, "trail tidak dibatasi"
    for _ in range(40):
        trail.update(DT)
    assert not trail.points, "sampel trail tidak pernah mati"


def test_trail_diisi_lapisan_hidup_saat_swing():
    h = fresh_hero()
    F.attach(h)
    d = F.director_for(h)
    for i in range(14):
        h._gnk_attack_active = True
        h._gnk_attack_progress = 0.30 + i * 0.02
        h._gnk_attack_phase = "SWING"
        h.pulse += 0.4
        F.tick(DT)
    assert d.trail.points, "ayunan tidak meninggalkan jejak bilah"
    h._gnk_attack_active = False
    h._gnk_attack_phase = "NONE"
    for _ in range(40):
        F.tick(DT)
    assert not d.trail.points, "trail tidak pernah pudar"


# ══════════════════════════════════════════════════════════════════════════
# 4. PARTICLE SYSTEM
# ══════════════════════════════════════════════════════════════════════════
def test_cap_partikel_dihormati():
    ps = F.ParticleSystem(F.MAX_PARTICLES)
    for i in range(600):
        ps.spawn(0.0, 0.0, 1.0, 1.0, 1.0, 2, F.P["fx_light"])
    assert ps.count() <= F.MAX_PARTICLES
    ps.update(DT)
    assert ps.count() > 0


def test_partikel_mati_tidak_abadi():
    ps = F.ParticleSystem(64)
    for i in range(20):
        ps.spawn(0.0, 0.0, 40.0, -60.0, 0.3, 2, F.P["fx_light"],
                 gravity=300.0, drag=2.0)
    for _ in range(120):
        ps.update(DT)
    assert ps.count() == 0, "partikel tidak habis (efek abadi)"


def test_partikel_punya_semua_bidang_master_prompt():
    p = F.Particle()
    for field in ("position", "velocity", "acceleration", "life", "max_life",
                  "size", "rotation", "rotation_speed", "alpha", "gravity",
                  "color"):
        assert hasattr(p, field), "Particle.%s hilang" % field
    p.spawn(1.0, 2.0, 10.0, 0.0, 0.5, 3, (255, 255, 255), gravity=100.0)
    y0 = p.pos.y
    for _ in range(6):
        p.update(DT)
    assert p.pos.x > 1.0, "velocity tidak menggerakkan posisi"
    assert p.vel.y > 0.0 or p.pos.y > y0, "gravity tidak bekerja"
    assert p.position is p.pos and p.velocity is p.vel, "alias posisi hilang"
    assert p.acceleration is p.acc, "alias percepatan hilang"
    assert p.life < p.max_life, "umur tidak dimundurkan"


def test_alpha_partikel_meluruh_saat_digambar():
    """Fade bagian dari kontrak: alpha yang DI BLIT mengecil, bukan mendadak."""
    ps = F.ParticleSystem(8)
    surf = pygame.Surface((60, 60), pygame.SRCALPHA)

    def peak_alpha():
        surf.fill((0, 0, 0, 0))
        ps.draw(surf)
        return max(surf.get_at((x, y))[3] for x in range(28, 33)
                   for y in range(28, 33))

    p = ps.spawn(30.0, 30.0, 0.0, 0.0, 0.5, 4, F.P["fx_white"])
    assert p is not None
    first = peak_alpha()
    for _ in range(int(0.40 / DT)):
        ps.update(DT)
    late = peak_alpha()
    assert first > 0 and late < first, (first, late)
    for _ in range(int(0.30 / DT)):
        ps.update(DT)
    assert ps.count() == 0, "partikel tidak pernah mati"


def test_lapisan_hidup_meluruh_penuh_setelah_pertempuran():
    h = fresh_hero()
    h.target = dummy_target()
    F.attach(h)
    d = F.director_for(h)
    surf = run_live(h, 40, attack=True)
    for _ in range(6):
        F.notify_melee_impact(h, h.target, 90, True)
        F.tick(DT)
        surf.fill((0, 0, 0, 0))
        F.draw_live_layer(surf, h, h.x, h.y)
    assert F.total_particles() > 0
    h._gnk_attack_active = False
    h._gnk_attack_manual = False
    h._gnk_attack_phase = "NONE"
    for _ in range(400):
        F.tick(DT)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
    assert F.total_particles() == 0, "partikel tersangkut setelah 400 frame"
    assert d.stats()["impacts"] == 0
    assert d.stats()["trail"] == 0
    assert surf.get_bounding_rect(min_alpha=4).width == 0, \
        "surface masih berisi efek"


# ══════════════════════════════════════════════════════════════════════════
# 5. PROJECTILE
# ══════════════════════════════════════════════════════════════════════════
def test_bidang_projectile_lengkap():
    src = inspect.getsource(F.GornakProjectile)
    for field in ("position", "velocity", "speed", "damage", "lifetime",
                  "target", "radius", "rotation", "trail", "particles",
                  "active"):
        assert field in src, "GornakProjectile.%s hilang" % field


def test_projectile_dipakai_hanya_visual():
    """Damage tetap milik hero_skills (instant); bolt di sini = FX saja."""
    h = fresh_hero()
    h.target = dummy_target(120.0, 0.0)
    F.attach(h)
    d = F.director_for(h)
    d.on_cast(h.x, h.y, "q")
    assert d.projectiles.count() == 1
    pr = d.projectiles.list()[0]
    assert pr.damage == 0, "bolt FX tidak boleh menambah damage"
    assert pr.state == pr.STATE_TRAVEL, "proyektil harus mulai TRAVEL"
    assert h.target.alive is True           # tidak ada side-effect gameplay
    assert pr.lifetime >= 0.0


def test_projectile_lahir_dari_ujung_bilah():
    h = fresh_hero()
    h.target = dummy_target(140.0, 4.0)
    F.attach(h)
    d = F.director_for(h)
    h._gnk_attack_active = False
    d.on_cast(h.x, h.y, "q")
    pr = d.projectiles.list()[0]
    g, tip = F.blade_points(h, h.x, h.y, False)
    start = pygame.Vector2(pr.spawn_pos)
    # dalam rentang beberapa px dari tip (kuantisasi int + flip)
    assert (start - tip).length() <= 10.0, (start, tip)


def test_lifecycle_projectile_sampai_hancur():
    h = fresh_hero()
    h.target = None                       # tak ada target -> terbang & mati
    F.attach(h)
    d = F.director_for(h)
    d.on_cast(h.x, h.y, "q")
    pr = d.projectiles.list()[0]
    seen = {pr.state}
    for _ in range(200):
        F.tick(DT)
        if d.projectiles.count():
            seen.add(d.projectiles.list()[0].state)
    assert d.projectiles.count() == 0, "proyektil abadi"
    assert pr.active is False
    assert pr.STATE_TRAVEL in seen


def test_projectile_mengenai_target_memicu_impact():
    h = fresh_hero()
    h.target = dummy_target(150.0, 0.0)
    F.attach(h)
    d = F.director_for(h)
    _clear_feel()
    d.on_cast(h.x, h.y, "q")
    for _ in range(90):
        F.tick(DT)
        if d.impacts:
            break
    else:
        pytest.fail("bolt tidak pernah memicu impact")
    assert d.impacts, "impact list kosong"


def test_cap_projectile():
    h = fresh_hero()
    h.target = dummy_target(150.0, 0.0)
    F.attach(h)
    d = F.director_for(h)
    for _ in range(F.MAX_PROJECTILES + 6):
        d.on_cast(h.x, h.y, "q")
    assert d.projectiles.count() <= F.MAX_PROJECTILES


# ══════════════════════════════════════════════════════════════════════════
# 6. SKILL FX
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("key,dur", [("q", 40), ("w", 25), ("e", 60),
                                     ("r", 90)])
def test_skill_fx_selesai_dan_hilang(key, dur):
    h = fresh_hero()
    h.target = dummy_target(160.0, 0.0)
    F.attach(h)
    d = F.director_for(h)
    h.active_skill = key
    h.active_skill_timer = dur
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    drawn = False
    for i in range(dur + 140):
        h.active_skill_timer = max(0, dur - i)
        if h.active_skill_timer == 0:
            h.active_skill = None
        F.tick(DT)
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
        if d.skills:
            drawn = True
    assert drawn, "skill %s tidak pernah punya SkillFX" % key
    assert not d.skills, "SkillFX %s tidak dibuang (efek abadi)" % key
    assert d.state != "SKILL" or h.active_skill


def test_skill_durasi_sama_dengan_engine():
    """SKILL_DUR lapisan hidup = timer yang ditulis hero_skills/_bundle."""
    for k, v in G.SKILL_DUR.items():
        assert F.SKILL_DUR[k] == v, k


def test_radius_dunia_e_dan_r_dipakai_penuh():
    """E=100 / R=180 px dunia di layar (bukan ikut mengecil di cache)."""
    assert F.WORLD_RADIUS["e"] == 100.0
    assert F.WORLD_RADIUS["r"] == 180.0
    assert F.WORLD_RADIUS["e"] > F.WORLD_RADIUS["q"]


def test_r_meledak_di_pusat_void_bukan_di_badan():
    h = fresh_hero(x=100.0, y=100.0)
    F.attach(h)
    d = F.director_for(h)
    h.active_skill = "r"
    h.active_skill_timer = 90
    h.mana_void_x, h.mana_void_y = 40.0, 130.0
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    for i in range(60):
        h.active_skill_timer = 90 - i
        F.tick(DT)
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
    assert d.void_screen is not None, "impact R tidak pernah dilepas"
    vx, vy, vr = d.void_screen
    assert (vx, vy) == pytest.approx((40.0, 130.0), abs=2.0), (vx, vy)
    assert vr == pytest.approx(180.0, abs=1.0)
    h.active_skill = None
    h.active_skill_timer = 0


def test_w_burst_di_titik_asal_blink():
    """Sisa tubuh ditinggalkan di titik asal -> burst pertama di sana."""
    h = fresh_hero(x=200.0, y=100.0)
    F.attach(h)
    d = F.director_for(h)
    d.on_blink(200.0, 100.0, 80.0, 100.0)
    parts = d.particles.alive()
    assert parts, "burst W tidak spawn apa pun"
    assert any(abs(p.pos.x - 80.0) < 26.0 for p in parts), \
        "tidak ada partikel di titik asal blink"
    assert d.impacts, "pendaratan W tanpa cincin kedatangan"


def test_w_dipicu_dari_state_engine():
    """Watcher membaca blink_from_x tanpa ada yang perlu memanggilnya."""
    h = fresh_hero(x=200.0, y=100.0)
    F.attach(h)
    d = F.director_for(h)
    h.active_skill = "w"
    h.active_skill_timer = 25
    h.blink_from_x, h.blink_from_y = 80.0, 100.0
    for i in range(6):
        h.active_skill_timer = 25 - i
        F.tick(DT)
    assert d._blink_seen is True
    assert d.impacts or d.particles.count()
    h.active_skill = None
    h.blink_from_x = 0
    F.tick(DT)
    assert d._blink_seen is False, "guard blink tidak di-reset"


# ══════════════════════════════════════════════════════════════════════════
# 7. IMPACT, SCREEN SHAKE, HIT STOP
# ══════════════════════════════════════════════════════════════════════════
def test_hit_stop_dalam_rentang_master_prompt():
    h = fresh_hero()
    h.target = dummy_target()
    F.attach(h)
    _clear_feel()
    F.notify_melee_impact(h, h.target, 120, False)
    sec = FEEL.HITSTOP.total * DT
    assert 0.03 - 1e-3 <= sec <= 0.08 + 2e-3, "hit-stop %.3f s" % sec


def test_hit_stop_membekukan_lalu_melepas():
    _clear_feel()
    FEEL.hit_stop(0.06)
    frozen = 0
    for _ in range(12):
        if FEEL.should_freeze_frame():
            frozen += 1
    assert 2 <= frozen <= FEEL.HITSTOP.MAX_FRAMES, frozen
    assert not FEEL.should_freeze_frame()
    # karakter lain tidak menambah freeze sendiri
    assert F.should_freeze_frame() is False


def test_shake_meluruh_ke_nol():
    h = fresh_hero()
    h.target = dummy_target()
    F.attach(h)
    _clear_feel()
    FEEL.SHAKE.enabled = True
    F.notify_melee_impact(h, h.target, 100, True)
    assert FEEL.SHAKE.amount > 0.0
    for _ in range(80):
        FEEL.SHAKE.update(DT)
    assert FEEL.SHAKE.amount == pytest.approx(0.0, abs=1e-6)
    assert FEEL.SHAKE.shake_strength == 0.0


def test_shake_tidak_dilaporkan_dua_kali(monkeypatch):
    """frame_dt() idempoten dalam satu frame: decay cuma sekali per frame.

    Jam SDL dipalsukan supaya 1 "frame" = 1000 us, tanpa tidur nyata.
    """
    _clear_feel()
    clock = {"ms": 1000}
    monkeypatch.setattr(pygame.time, "get_ticks",
                        lambda: clock["ms"], raising=True)

    def frame():
        clock["ms"] += 1000.0 / 60.0          # satu frame baru
        return FEEL.frame_dt()

    FEEL.SHAKE.enabled = True      # setting kamera default OFF di GameSettings
    FEEL.shake(6.0, 1.0, forward_to_camera=False)
    assert frame() == pytest.approx(0.0)      # frame acuan: dt belum ada
    before = FEEL.SHAKE.shake_duration
    dt_a = frame()
    assert 0.015 <= dt_a <= 0.017, dt_a
    # karakter KEDUA di frame yang sama: dt identik, decay TIDAK diulang
    same = FEEL.frame_dt()
    assert same == pytest.approx(dt_a)
    assert FEEL.SHAKE.shake_duration == pytest.approx(before - dt_a, abs=1e-9), \
        "shake meluruh dua kali dalam satu frame"
    for _ in range(6):
        frame()
    assert FEEL.SHAKE.shake_duration <= before - 7 * dt_a * 0.9


def test_impact_tanpa_target_tidak_error():
    h = fresh_hero()
    F.attach(h)
    F.notify_melee_impact(h, None, 50, False)
    F.notify_projectile_impact(h, h.x + 30, h.y, 0.4, 40, False)
    F.notify_skill_impact(h, h.x + 20, h.y, 100, "e")
    F.notify_skill_cast(h, "q")
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    for _ in range(30):
        F.tick(DT)
        F.draw_live_layer(surf, h, h.x, h.y)
    assert True


def test_bus_pintu_hit_stop_core():
    """Game.update membekukan lewat bus SHARED, bukan modul karakter."""
    src = open(os.path.join(ROOT, "_core.py"), encoding="utf-8").read()
    gate = src[src.index("def update(self):"):]
    gate = gate[:gate.index("GAME SPEED")]
    assert "combat_feel" in gate and "should_freeze_frame" in gate
    assert "zephyr_fx as _zfx" not in gate


# ══════════════════════════════════════════════════════════════════════════
# 8. INTEGRASI RENDERER <-> LAPISAN HIDUP
# ══════════════════════════════════════════════════════════════════════════
def test_jalur_boss_mengambil_alih_effect():
    h = fresh_hero()                       # tanpa _render_scale = lane boss
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    calls = {"crescent": 0, "proc": 0}
    real_crescent = G._draw_crescent_slash
    real_proc = G._draw_manabreak_foreground

    def spy_crescent(*a, **k):
        calls["crescent"] += 1
        return real_crescent(*a, **k)

    def spy_proc(*a, **k):
        calls["proc"] += 1
        return real_proc(*a, **k)

    G._draw_crescent_slash = staticmethod(spy_crescent)
    G._draw_manabreak_foreground = staticmethod(spy_proc)
    try:
        h._gnk_attack_active = True
        h._gnk_attack_manual = True
        h._gnk_attack_progress = 0.5
        h.active_skill = "q"
        h.active_skill_timer = 30
        for _ in range(4):
            surf.fill((0, 0, 0, 0))
            h.pulse += 0.4
            G.draw_gornak(surf, h, 120, 150)
        assert F.owns(h), "lapisan hidup tidak mengambil alih di lane boss"
        assert calls["crescent"] == 0, "pita ayunan digambar DUA kali"
        assert calls["proc"] == 0, "proc foreground digambar dua kali"
        assert F.total_particles() >= 0
        assert F.director_for(h).trail.samples
    finally:
        G._draw_crescent_slash = real_crescent
        G._draw_manabreak_foreground = real_proc


def test_fallback_canvas_saat_modul_fx_tidak_ada():
    """Tanpa modul FX, renderer harus tetap menggambar semuanya sendiri."""
    h = fresh_hero()
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    seen = {"crescent": 0}
    real_mod, real_crescent = G._LIVE_MOD, G._draw_crescent_slash

    def spy(*a, **k):
        seen["crescent"] += 1

    G._LIVE_MOD = False                    # simulasi import gagal
    G._draw_crescent_slash = staticmethod(spy)
    try:
        h._gnk_attack_active = True
        h._gnk_attack_manual = True
        h._gnk_attack_progress = 0.5
        G.draw_gornak(surf, h, 120, 150)
        assert seen["crescent"] == 1, "fallback canvas hilang"
        assert not F.owns(h)
    finally:
        G._draw_crescent_slash = real_crescent
        G._LIVE_MOD = real_mod


def test_lane_hero_terdaftar_di_live_fx():
    assert "gornak" in heroes._LIVE_FX_HEROES
    assert heroes._live_fx_module("gornak") is F


def test_render_hero_menjalankan_lapisan_hidup():
    heroes.clear_hero_sprite_cache()
    h = fresh_hero(scale=0.7)
    h._gnk_attack_active = True
    h._gnk_attack_manual = True
    h._gnk_attack_progress = 0.5
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    for _ in range(3):
        heroes.render_hero("gornak", surf, h, 120, 150)
    assert F.owns(h), "lane hero tidak memasang lapisan hidup"
    heroes.clear_hero_sprite_cache()


def test_telegraph_tanah_tetap_di_renderer():
    """Telegraph E/R adalah ground FX yang boleh di-cache; jangan disupresi."""
    h = fresh_hero()
    calls = {"ground": 0}
    real = G._draw_manabreak_ground

    def spy(*a, **k):
        calls["ground"] += 1
        return real(*a, **k)

    G._draw_manabreak_ground = staticmethod(spy)
    try:
        h.active_skill = "q"
        h.active_skill_timer = 30
        F.attach(h)                        # owned=True, tapi telegraph tetap
        G.draw_gornak(pygame.Surface((240, 240), pygame.SRCALPHA), h, 120,
                      150)
        assert calls["ground"] == 1
    finally:
        G._draw_manabreak_ground = real


# ══════════════════════════════════════════════════════════════════════════
# 9. DEBUG OVERLAY
# ══════════════════════════════════════════════════════════════════════════
def test_hitbox_hanya_saat_jendela_hit():
    h = fresh_hero()
    assert G._swing_hitbox(h, 100, 100) is None
    h._gnk_hit_active = True
    hb = G._swing_hitbox(h, 100, 100)
    assert hb is not None and hb.width > 8 and hb.height > 8
    # di depan badan sesuai arah
    h.direction = -1
    hb_l = G._swing_hitbox(h, 100, 100)
    assert hb_l.right <= 101


def test_debug_overlay_tidak_merusak_render():
    h = fresh_hero()
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    before = G.DEBUG_CHARACTER
    G.DEBUG_CHARACTER = True
    try:
        h._gnk_attack_active = True
        h._gnk_attack_manual = True
        h._gnk_attack_progress = 0.5
        G._update_gnk_attack_anim(h)
        assert h._gnk_hit_active
        F.attach(h)
        G.draw_gornak(surf, h, 120, 150)
        assert surf.get_bounding_rect(min_alpha=4).height > 0
    finally:
        G.DEBUG_CHARACTER = before


def test_debug_overlay_menyebut_state_dan_partikel():
    src = inspect.getsource(G._draw_gnk_debug)
    for token in ("_gnk_state", "_gnk_attack_phase", "particles", "fps",
                  "_swing_hitbox"):
        assert token in src, "overlay debug kehilangan %s" % token


# ══════════════════════════════════════════════════════════════════════════
# 10. PERFORMA
# ══════════════════════════════════════════════════════════════════════════
def test_lapisan_hidup_cepat():
    h = fresh_hero()
    h.target = dummy_target(150.0, 0.0)
    F.attach(h)
    surf = pygame.Surface((640, 360), pygame.SRCALPHA)
    run_live(h, 30, attack=True)                  # panaskan cache
    t0 = time.perf_counter()
    n = 60
    for i in range(n):
        h._gnk_attack_active = True
        h._gnk_attack_progress = (i % COOLDOWN) / float(COOLDOWN)
        h._gnk_attack_phase = PHASE_ORDER[min(5, i // 6)]
        if i % 10 == 0:
            F.notify_melee_impact(h, h.target, 90, i % 20 == 0)
        F.tick(DT)
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
    ms = (time.perf_counter() - t0) / n * 1000.0
    assert ms < 5.0, "lapisan hidup %.2f ms/frame" % ms


def test_draw_gornak_lane_boss_masih_dibawah_anggaran():
    h = fresh_hero()
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    for _ in range(10):
        h.pulse += 0.3
        G.draw_gornak(surf, h, 120, 150)
    t0 = time.perf_counter()
    for _ in range(60):
        h.pulse += 0.3
        G.draw_gornak(surf, h, 120, 150)
    ms = (time.perf_counter() - t0) / 60.0 * 1000.0
    assert ms < 5.0, "draw_gornak(live) %.2f ms/frame" % ms


def test_cache_surface_dibatasi():
    h = fresh_hero()
    surf = pygame.Surface((400, 300), pygame.SRCALPHA)
    for r in range(260):
        F.ring_surface(r, 2, F.P["fx_light"], 200, 0)
        F.glow_surface(max(2, r // 2), F.P["fx_bright"], 0.8)
    assert F.cache_size() <= F._SURF_CACHE_MAX, F.cache_size()
    F.clear_cache()
    assert F.cache_size() == 0


def test_kualitas_rendah_memangkas_partikel():
    try:
        from mobile import perf as PERF
    except Exception:
        pytest.skip("mobile.perf tidak tersedia")
    h = fresh_hero()
    h.target = dummy_target(150.0, 0.0)
    F.attach(h)
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    counts = {}
    orig = (getattr(PERF.Quality, "particles", True),
            getattr(PERF.Quality, "particle_ratio", 1.0))
    for ratio in (1.0, 0.35):
        PERF.Quality.particles = True
        PERF.Quality.particle_ratio = ratio
        F.reset_all()
        _clear_feel()
        hh = fresh_hero()
        hh.target = dummy_target(150.0, 0.0)
        F.attach(hh)
        dd = F.director_for(hh)
        for i in range(30):
            hh._gnk_attack_active = True
            hh._gnk_attack_progress = i / 30.0
            hh._gnk_attack_phase = "SWING" if i < 20 else "IMPACT"
            F.tick(DT)
            F.draw_ground_layer(surf, hh, hh.x, hh.y)
            F.draw_live_layer(surf, hh, hh.x, hh.y)
            if i % 6 == 0:
                F.notify_melee_impact(hh, hh.target, 90, True)
        counts[ratio] = dd.stats()["particles"] + dd.particles.count()
    PERF.Quality.particles, PERF.Quality.particle_ratio = orig
    assert counts[0.35] <= counts[1.0], counts


def test_semua_nya_bersaat_kosong():
    """Aftermath: tidak ada unit terdaftar setelah reset_all()."""
    h = fresh_hero()
    F.attach(h)
    d = F.director_for(h)
    d.on_cast(h.x, h.y, "e")
    F.notify_melee_impact(h, dummy_target(), 60, False)
    F.reset_all()
    _clear_feel()
    assert F.total_particles() == 0
    assert F.owns(h) is False
    assert not F.should_freeze_frame()
    assert FEEL.SHAKE.amount == 0.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
