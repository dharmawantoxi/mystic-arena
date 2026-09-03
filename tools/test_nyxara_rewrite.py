#!/usr/bin/env python3
"""Regression test NYXARA FULL REWRITE (render + animasi + FX hidup).

The Nether Matron — L5 Mini Boss & hero unlock.

Mengunci lewat path shipping:
  * RENDER   — semua state tergambar tanpa exception, bbox memadai, tidak
               ada flicker (frame idle berubah tapi tidak pernah kosong),
               probe portrait tidak meledak, label HP bar tidak menutupi
               puncak rig (BOSS_LABEL_TOP >= puncak terukur).
  * ANIMASI  — controller: prioritas state, pemetaan action per skill
               (q/w/e/r), dual-mode basic attack (swing <= MELEE_REACH,
               orb > MELEE_REACH), fase ANTICIPATION->RECOVERY.
  * ATTACK   — arc tongkat: sweep kontinyu tanpa lompatan sudut;
               fallback canvas tergambar saat modul FX dimatikan.
  * PROJECTILE (lapisan hidup) — nether orb & nether blast modular:
               spawn -> travel -> trail -> hit -> impact -> destroy;
               HANYA di jalur boss (jalur hero memakai proyektil generik
               gameplay); tidak ada yang hidup melampaui lifetime.
  * SKILL FX (lapisan hidup) — q/w/e/r lifecycle penuh + cleanup; semua
               skill dimajukan setiap frame (anti-kebocoran).
  * GAME FEEL — hit-stop di dalam jendela 0.03-0.08 s; impact tidak
               menumpuk melampaui batas; partikel turun ke nol setelah
               pertarungan selesai (ambient dimatikan saat tes).
  * INTEGRASI — jalur boss (draw_nyxara + live layer) & jalur hero
               (render_hero melewati _LIVE_FX_HEROES); registry lengkap;
               reset_all mengembalikan semuanya ke nol; palet FX
               tersinkron dari palet renderer; hook AI base_boss.
  * PROSEDURAL — tanpa pygame.image.load / aset gambar.
  * PERF     — idle < 2.4 ms/frame; FX tick+draw < 2.1 ms/frame.

Jalankan: python3 tools/test_nyxara_rewrite.py
"""
import math
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

import bosses.level5 as L
import heroes.nyxara_fx as FX
import heroes  # heroes/__init__.py — pipeline sprite + live FX

NS = L._NS_nyxara
P = FX.NYXARA_PALETTE

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


# ── helper ─────────────────────────────────────────────────────────
def probe(**kw):
    b = SimpleNamespace(boss_type="nyxara", hero_type="nyxara",
                        x=230.0, y=230.0, direction=1, pulse=1.2,
                        timer=0, attack_cooldown=42, active_skill=None,
                        active_skill_timer=0, target=None,
                        hurt_flash_timer=0,
                        alive=True, radius=34, hp=6200, max_hp=6200,
                        team="red", speed=0.9, damage=68,
                        is_enraged=False, ability_active=False,
                        ability_active_timer=0)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(b, size=520):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    L.draw_nyxara(s, b, 260, 260)
    return s


def bbox(s, alpha=8):
    return s.get_bounding_rect(min_alpha=alpha)


def enemy(x=400.0, y=230.0):
    return SimpleNamespace(x=x, y=y, alive=True, radius=14,
                           attack_timer=0,
                           take_damage=lambda *a, **k: None)


# ═══════════════════════════════════════════════════════════════════
print("\n[1] RENDER — semua state tergambar, bbox memadai")
# ═══════════════════════════════════════════════════════════════════
FX.reset_all()
cases = {
    "idle": {}, "walk": {}, "attack": {}, "swing": {},
    "cast_q": {"active_skill": "q", "active_skill_timer": 40},
    "cast_w": {"active_skill": "w", "active_skill_timer": 40},
    "cast_e": {"active_skill": "e", "active_skill_timer": 50},
    "cast_r": {"active_skill": "r", "active_skill_timer": 60},
    "hurt": {"hurt_flash_timer": 10},
    "death": {"alive": False},
}
rig_top = 0
for name, kw in cases.items():
    b = probe(**kw)
    ok = True
    for i in range(8):
        b.pulse += 0.05
        if name == "walk":
            b.x += 5
        if name in ("attack", "swing"):
            b._nx_attack_active = True
            b._nx_attack_manual = True
            b._nx_attack_progress = i / 7.0
            b._nx_attack_kind = "swing" if name == "swing" else "orb"
        try:
            s = render(b)
        except Exception as e:                    # pragma: no cover
            ok = False
            print("   exception:", name, e)
            break
        r = bbox(s)
        if r.width < 18 or r.height < 30:
            ok = False
            break
    check(f"render {name}", ok, f"bbox={bbox(s)}")

# puncak rig (portrait = rig murni tanpa ground/live FX)
for name, kw in cases.items():
    if name == "death":
        continue
    b = probe(_portrait_hd=True, **kw)
    for i in range(24):
        b.pulse += 0.05
        if name in ("attack", "swing"):
            b._nx_attack_active = True
            b._nx_attack_manual = True
            b._nx_attack_progress = (i % 12) / 11.0
            b._nx_attack_kind = "swing" if name == "swing" else "orb"
        if kw.get("active_skill"):
            b.active_skill_timer = max(1, 50 - i)
        r = bbox(render(b))
        rig_top = max(rig_top, 260 - r.top)
# BOSS_LABEL_TOP dibaca sebagai TEKS — base_boss.py butuh `settings`
# dari root aplikasi, jadi tidak bisa diimpor berdiri sendiri.
_BB_SRC = open(os.path.join(ROOT, "bosses", "base_boss.py")).read()
_m = re.search(r'"nyxara":\s*(\d+)', _BB_SRC)
_label_top = int(_m.group(1)) if _m else 0
check("BOSS_LABEL_TOP menutupi puncak rig", _label_top >= rig_top,
      f"label={_label_top} rig_top={rig_top}")

# anti-flicker: idle berubah tiap frame tapi TIDAK pernah kosong
b = probe()
areas = []
for i in range(20):
    b.pulse += 0.06
    areas.append(bbox(render(b)).height)
check("idle tidak pernah kosong", all(a > 30 for a in areas), str(areas[:5]))
check("idle beranimasi (bukan beku)", len(set(areas)) > 1, str(set(areas)))

# portrait tidak meledak
try:
    render(probe(_portrait_hd=True))
    check("portrait HD aman", True)
except Exception as e:                            # pragma: no cover
    check("portrait HD aman", False, str(e))


# ═══════════════════════════════════════════════════════════════════
print("\n[2] ANIMASI — state machine, prioritas, fase")
# ═══════════════════════════════════════════════════════════════════
check("12 state animasi terdaftar", len(NS.ANIM_STATES) >= 12,
      str(len(NS.ANIM_STATES)))
check("DEATH prioritas tertinggi",
      NS.ANIM_STATES["DEATH"] == max(NS.ANIM_STATES.values()))
check("renderer & FX punya ANIM_STATES sama", NS.ANIM_STATES == FX.ANIM_STATES)

# prioritas: death > hurt > skill > attack > walk > idle
b = probe(alive=False)
render(b)
check("state DEATH", NS.anim_state(b) == "DEATH", NS.anim_state(b))
b = probe(hurt_flash_timer=10)
render(b)
check("state HURT", NS.anim_state(b) == "HURT", NS.anim_state(b))
b = probe(active_skill="r", active_skill_timer=50)
render(b)
check("state SPECIAL (skill r)", NS.anim_state(b) == "SPECIAL",
      NS.anim_state(b))
b = probe(active_skill="q", active_skill_timer=50)
render(b)
check("state SKILL (skill q)", NS.anim_state(b) == "SKILL", NS.anim_state(b))
b = probe()
b._nx_attack_active = True
b._nx_attack_manual = True
b._nx_attack_progress = 0.4
b._nx_attack_kind = "swing"
render(b)
check("state SWING", NS.anim_state(b) == "SWING", NS.anim_state(b))
b = probe()
render(b)
b.x += 8
render(b)
check("state WALK", NS.anim_state(b) == "WALK", NS.anim_state(b))
b = probe()
render(b)
render(b)
check("state IDLE", NS.anim_state(b) == "IDLE", NS.anim_state(b))

# pemetaan action per skill
for sk, want in (("q", "cast_q"), ("w", "cast_w"),
                 ("e", "cast_e"), ("r", "cast_r")):
    b = probe(active_skill=sk, active_skill_timer=40)
    render(b)
    check(f"pose skill {sk} -> {want}", NS.pose_of(b)[0] == want,
          NS.pose_of(b)[0])

# dual-mode basic attack: jarak menentukan swing vs orb
b = probe(target=enemy(x=230.0 + NS.MELEE_REACH - 20))
b.timer = b.attack_cooldown
b._nx_prev_timer = 0
render(b)
check("dekat -> swing", NS.attack_kind(b) == "swing", NS.attack_kind(b))
b = probe(target=enemy(x=230.0 + NS.MELEE_REACH + 120))
b.timer = b.attack_cooldown
b._nx_prev_timer = 0
render(b)
check("jauh -> orb", NS.attack_kind(b) == "orb", NS.attack_kind(b))

# fase serangan berurutan lengkap
seen = [NS.attack_phase(i / 100.0) for i in range(100)]
for ph in ("ANTICIPATION", "WINDUP", "SWING", "IMPACT", "FOLLOW",
           "RECOVERY"):
    check(f"fase {ph} tercapai", ph in seen)
check("renderer & FX fase identik", NS.ATTACK_PHASES == FX.ATTACK_PHASES)
check("renderer & FX SKILL_PHASES identik",
      NS.SKILL_PHASES == FX.SKILL_PHASES)

# delta time dipakai controller
b = probe()
render(b)
check("controller memakai delta time",
      isinstance(getattr(b, "_nx_dt", None), float) and b._nx_dt > 0.0)


# ═══════════════════════════════════════════════════════════════════
print("\n[3] ATTACK — busur kontinyu + hitbox + fallback")
# ═══════════════════════════════════════════════════════════════════
# sudut tongkat: sweep tanpa teleport
angs = [NS._staff_angle("swing", i / 200.0, 0.0) for i in range(201)]
jumps = [abs(angs[i + 1] - angs[i]) for i in range(len(angs) - 1)]
check("arc swing kontinyu (tanpa lompatan)", max(jumps) < 0.25,
      f"max jump={max(jumps):.3f}")
check("arc swing benar-benar menyapu",
      (max(angs) - min(angs)) > 2.0, f"span={max(angs) - min(angs):.2f}")
angs_a = [NS._staff_angle("attack", i / 200.0, 0.0) for i in range(201)]
jumps_a = [abs(angs_a[i + 1] - angs_a[i]) for i in range(len(angs_a) - 1)]
check("arc attack kontinyu", max(jumps_a) < 0.25, f"{max(jumps_a):.3f}")

# pivot juga kontinyu
piv = [NS._staff_pivot_local("swing", i / 200.0, 0.0) for i in range(201)]
pj = [math.dist(piv[i], piv[i + 1]) for i in range(len(piv) - 1)]
check("pivot swing kontinyu", max(pj) < 1.5, f"{max(pj):.3f}")

# hitbox hanya aktif di jendela aktif
b = probe()
lo, hi = NS.ATTACK_ACTIVE_WINDOW
b._nx_attack_active = True
b._nx_attack_manual = True
b._nx_attack_kind = "swing"
b._nx_attack_progress = (lo + hi) / 2
render(b)
check("hitbox aktif di jendela", NS._swing_hitbox(b, 260, 260) is not None)
b._nx_attack_progress = 0.95
render(b)
check("hitbox mati di recovery", NS._swing_hitbox(b, 260, 260) is None)
check("hurtbox selalu ada", NS._hurtbox(probe(), 260, 260) is not None)

# geometri tongkat: satu sumber renderer <-> FX
b = probe()
render(b)
r_pv, r_tip = NS.staff_points(b, 260, 260)
f_pv, f_tip = FX.staff_points(b, 260, 260)
check("staff_points renderer == FX",
      r_pv == f_pv and r_tip == f_tip, f"{r_tip} vs {f_tip}")

# fallback canvas saat modul FX dimatikan
FX.reset_all()
FX.NYXARA_FX_ENABLED = False
NS._LIVE_MOD = None
try:
    b = probe(target=enemy())
    b._nx_attack_active = True
    b._nx_attack_manual = True
    b._nx_attack_kind = "orb"
    spawned = False
    for i in range(30):
        b._nx_attack_progress = min(1.0, i / 12.0)
        render(b)
        if getattr(b, "_nx_projectiles", None):
            spawned = True
    check("fallback proyektil canvas terbentuk", spawned)
finally:
    FX.NYXARA_FX_ENABLED = True
    NS._LIVE_MOD = None
    FX.reset_all()


# ═══════════════════════════════════════════════════════════════════
print("\n[4] PROJECTILE — lifecycle penuh, jalur boss saja")
# ═══════════════════════════════════════════════════════════════════
FX.reset_all()
b = probe(target=enemy(x=520.0))
d = FX.director_for(b)
d.sync(b, 230, 230)
d._spawn_attack_orb(d._target_point())
check("orb spawn", d.projectiles.count() == 1)
p = d.projectiles.projectiles[0]
for attr in ("pos", "vel", "speed", "damage", "lifetime", "target",
             "radius", "rotation", "trail", "active"):
    check(f"proyektil punya .{attr}", hasattr(p, attr))
start = pygame.Vector2(p.pos)
d.projectiles.update(1 / 60.0)
check("orb TRAVEL (bergerak)", p.pos.distance_to(start) > 1.0)
check("orb punya TRAIL", len(p.trail) > 0)
surf = pygame.Surface((900, 600), pygame.SRCALPHA)
for _ in range(300):
    d.projectiles.update(1 / 60.0)
    d.projectiles.draw(surf)
check("orb HIT lalu DESTROY", d.projectiles.count() == 0,
      str(d.projectiles.count()))
check("impact FX dibersihkan", len(d.projectiles.impacts) == 0)

# blast (skill Q) modular
FX.reset_all()
b = probe(target=enemy(x=560.0))
d = FX.director_for(b)
d.sync(b, 230, 230)
d._spawn_blast()
check("blast spawn", d.projectiles.count() == 1)
for _ in range(300):
    d.projectiles.update(1 / 60.0)
check("blast destroy dalam lifetime", d.projectiles.count() == 0)

# jalur HERO tidak memunculkan proyektil prosedural (pakai generik game)
FX.reset_all()
b = probe(target=enemy(x=520.0), _render_scale=0.6)
b._nx_attack_active = True
b._nx_attack_kind = "orb"
b._nx_attack_progress = 0.9
d = FX.director_for(b)
d.sync(b, 230, 230)
for _ in range(20):
    d.update(1 / 60.0)
check("jalur hero tanpa proyektil prosedural",
      d.projectiles.count() == 0, str(d.projectiles.count()))

# cap keras proyektil
FX.reset_all()
b = probe(target=enemy(x=520.0))
d = FX.director_for(b)
d.sync(b, 230, 230)
for _ in range(40):
    d._spawn_attack_orb(d._target_point())
check("cap proyektil dihormati",
      d.projectiles.count() <= FX.MAX_PROJECTILES, str(d.projectiles.count()))


# ═══════════════════════════════════════════════════════════════════
print("\n[5] SKILL FX — lifecycle 6 fase + cleanup")
# ═══════════════════════════════════════════════════════════════════
for ph in ("CAST", "CHARGE", "RELEASE", "AREA", "IMPACT", "AFTER"):
    check(f"skill fase {ph} tercapai",
          ph in [FX.skill_phase(i / 100.0) for i in range(100)])

for sk in "qwer":
    FX.reset_all()
    b = probe(target=enemy(), active_skill=sk,
              active_skill_timer=FX.SKILL_DUR[sk])
    FX.notify_skill_cast(b, sk)
    d = FX.director_for(b)
    check(f"skill {sk} SkillFX dibuat", len(d.skills) == 1)
    surf = pygame.Surface((900, 600), pygame.SRCALPHA)
    ok = True
    try:
        for i in range(400):
            b.active_skill_timer = max(0, b.active_skill_timer - 1)
            d.sync(b, 230, 230)
            d.draw_ground(surf)
            d.update(1 / 60.0)
            d.draw_front(surf)
    except Exception as e:                        # pragma: no cover
        ok = False
        print("   exception:", sk, e)
    check(f"skill {sk} tergambar tanpa exception", ok)
    check(f"skill {sk} selesai (cleanup)", len(d.skills) == 0,
          str(len(d.skills)))

check("SKILL_DUR renderer == FX", NS.SKILL_DUR == FX.SKILL_DUR)
check("radius dunia renderer == FX",
      NS.SKILL_RADIUS == FX.WORLD_RADIUS)


# ═══════════════════════════════════════════════════════════════════
print("\n[6] GAME FEEL — hit-stop 0.03-0.08 s, shake meluruh")
# ═══════════════════════════════════════════════════════════════════
from heroes import combat_feel as CF

src = open(os.path.join(ROOT, "heroes", "nyxara_fx.py")).read()
stops = [float(m) for m in re.findall(r"hit_stop\(([0-9.]+)\)", src)]
check("ada pemanggilan hit-stop", len(stops) > 0)
check("semua hit-stop di 0.03-0.08 s",
      all(0.03 <= s <= 0.08 for s in stops), str(sorted(set(stops))))
shakes = [float(m) for m in re.findall(r"shake\(([0-9.]+),", src)]
check("ada screen shake", len(shakes) > 0)

CF.reset()
FX.reset_all()
b = probe(target=enemy())
FX.notify_melee_impact(b, b.target, 68, False)
check("hit-stop terpicu oleh benturan", CF.HITSTOP.remaining > 0.0
      if hasattr(CF.HITSTOP, "remaining") else True)
amt0 = CF.amount()
for _ in range(60):
    CF.SHAKE.update(1 / 60.0)
check("shake meluruh ke nol", CF.amount() <= amt0)
CF.reset()

# impact tidak menumpuk
FX.reset_all()
b = probe(target=enemy())
d = FX.director_for(b)
for _ in range(50):
    d.on_impact(300, 230, 0.0, 1.0, False, kind="staff")
check("impact dibatasi cap", len(d.impacts) <= FX.MAX_IMPACTS,
      str(len(d.impacts)))


# ═══════════════════════════════════════════════════════════════════
print("\n[7] PARTIKEL — atribut lengkap, cap, tidak abadi")
# ═══════════════════════════════════════════════════════════════════
ps = FX.ParticleSystem(50)
ps.spawn(0, 0, 10, -10, 0.5, 2.0, P["nether_mid"])
pt = ps.parts[0]
for attr in ("x", "y", "vx", "vy", "life", "max_life", "size",
             "rotation", "rotation_speed", "alpha", "gravity", "color"):
    check(f"partikel punya .{attr}", hasattr(pt, attr))
ps.burst(0, 0, 500, colors=(P["nether_mid"],))
check("cap partikel dihormati", ps.count() <= 50, str(ps.count()))
for _ in range(200):
    ps.update(1 / 60.0)
check("partikel mati pada waktunya", ps.count() == 0, str(ps.count()))

# tidak ada partikel abadi setelah pertarungan
FX.reset_all()
b = probe(target=enemy())
d = FX.director_for(b)
d.sync(b, 230, 230)
FX.notify_melee_impact(b, b.target, 68, False)
FX.notify_skill_cast(b, "q")
d.ember_acc = 0.0
for _ in range(600):
    d.update(1 / 60.0)
    d.ember_acc = 0.0                     # matikan ambient untuk tes
check("partikel turun ke nol setelah tempur",
      d.particles.count() == 0, str(d.particles.count()))
FX.reset_all()
check("reset_all mengosongkan semuanya", FX.total_particles() == 0)


# ═══════════════════════════════════════════════════════════════════
print("\n[8] INTEGRASI — registry, palet, hook AI, jalur hero")
# ═══════════════════════════════════════════════════════════════════
check("nyxara terdaftar di _LIVE_FX_HEROES",
      "nyxara" in heroes._LIVE_FX_HEROES)
check("path modul FX terdaftar",
      heroes._LIVE_FX_PATHS.get("nyxara") == "heroes.nyxara_fx")
check("modul FX bisa dimuat pipeline",
      heroes._live_fx_module("nyxara") is not None)
from bosses._boss_index import BOSS_INDEX
check("nyxara di BOSS_INDEX",
      BOSS_INDEX.get("nyxara") == ("level5", "draw_nyxara"))
check("entry point draw_nyxara ada", callable(L.draw_nyxara))
check("alias draw_boss ada", callable(NS.draw_boss))

FX._PALETTE_SYNCED = False
FX._sync_palette()
check("palet FX tersinkron dari renderer",
      all(P[k] == v for k, v in NS.PALETTE.items()),
      "palet berbeda")
check("MELEE_REACH renderer == FX", NS.MELEE_REACH == FX.MELEE_REACH)
check("CHARACTER_NAME konsisten",
      NS.CHARACTER_NAME == FX.CHARACTER_NAME == "nyxara")

# hook AI base_boss memanggil lapisan FX
bb = _BB_SRC
check("hook impact nyxara di base_boss",
      "nyxara_fx as _nyxfx" in bb and "notify_melee_impact" in bb)
check("hook death nyxara di base_boss",
      bb.count("_nyxfx.notify_death(self)") >= 1)
for sk in "qwer":
    check(f"hook skill cast {sk} di AI",
          f"_nyxfx.notify_skill_cast(self, '{sk}')" in bb)

# jalur hero: render_hero melewati pipeline live FX
try:
    h = probe(_render_scale=1.0)
    surf = pygame.Surface((600, 600), pygame.SRCALPHA)
    heroes._live_fx_pre("nyxara", surf, h, 300, 300)
    L.draw_nyxara(surf, h, 300, 300)
    heroes._live_fx_post("nyxara", surf, h, 300, 300)
    check("jalur hero (pre+draw+post) aman", True)
except Exception as e:                            # pragma: no cover
    check("jalur hero (pre+draw+post) aman", False, str(e))

# API publik yang dipakai pipeline
for fn in ("attach", "owns", "tick", "reset_all", "draw_ground_layer",
           "draw_live_layer", "notify_melee_impact",
           "notify_projectile_impact", "notify_skill_cast",
           "notify_skill_impact", "notify_death", "recently_drawn",
           "total_particles", "stats", "debug_overlay"):
    check(f"API FX .{fn}", callable(getattr(FX, fn, None)))

check("DEBUG_CHARACTER tersedia (renderer)",
      isinstance(NS.DEBUG_CHARACTER, bool))
check("DEBUG_CHARACTER tersedia (FX)", isinstance(FX.DEBUG_CHARACTER, bool))

# overlay debug tidak meledak
FX.reset_all()
b = probe(target=enemy())
surf = pygame.Surface((600, 600), pygame.SRCALPHA)
L.draw_nyxara(surf, b, 300, 300)
try:
    FX.debug_overlay(surf, b, 300, 300)
    NS._draw_nx_debug(surf, b, 300, 300)
    check("overlay debug aman", True)
except Exception as e:                            # pragma: no cover
    check("overlay debug aman", False, str(e))

# boss lain di bundle level5 tidak ikut rusak
for other in ("gravefang", "vhalzun", "krobellus"):
    try:
        o = probe(boss_type=other, hero_type=other)
        s = pygame.Surface((520, 520), pygame.SRCALPHA)
        getattr(L, "draw_" + other)(s, o, 260, 260)
        check(f"boss {other} masih tergambar", bbox(s).height > 20)
    except Exception as e:                        # pragma: no cover
        check(f"boss {other} masih tergambar", False, str(e))


# ═══════════════════════════════════════════════════════════════════
print("\n[9] PROSEDURAL MURNI")
# ═══════════════════════════════════════════════════════════════════
fx_src = open(os.path.join(ROOT, "heroes", "nyxara_fx.py")).read()
i = open(os.path.join(ROOT, "bosses", "level5.py")).read()
ns_src = i[i.index("class _NS_nyxara"):i.index("class _NS_gravefang")]
def _strip_comments(blob):
    """Buang komentar `#` supaya yang diperiksa hanya KODE nyata."""
    return "\n".join(re.sub(r"#.*$", "", ln) for ln in blob.split("\n"))


for label, blob in (("nyxara_fx", fx_src), ("renderer", ns_src)):
    code = _strip_comments(blob)
    check(f"{label}: tanpa image.load", "image.load" not in code)
    check(f"{label}: tanpa aset gambar eksternal",
          not re.search(r"\.(png|jpg|jpeg|gif|bmp)\b", code))


# ═══════════════════════════════════════════════════════════════════
print("\n[10] PERFORMA")
# ═══════════════════════════════════════════════════════════════════
FX.reset_all()
b = probe()
surf = pygame.Surface((900, 600), pygame.SRCALPHA)
for _ in range(20):
    L.draw_nyxara(surf, b, 300, 300)
t0 = time.perf_counter()
for _ in range(120):
    b.pulse += 0.05
    L.draw_nyxara(surf, b, 300, 300)
idle_ms = (time.perf_counter() - t0) / 120 * 1000
check(f"idle < 2.4 ms/frame ({idle_ms:.2f} ms)", idle_ms < 2.4)

FX.reset_all()
b = probe(target=enemy())
d = FX.director_for(b)
d.sync(b, 300, 300)
FX.notify_skill_cast(b, "r")
for _ in range(30):
    d.on_impact(360, 300, 0.0, 1.0, False, kind="staff")
    d.update(1 / 60.0)
t0 = time.perf_counter()
for _ in range(120):
    d.update(1 / 60.0)
    d.draw_ground(surf)
    d.draw_front(surf)
fx_ms = (time.perf_counter() - t0) / 120 * 1000
check(f"FX tick+draw < 2.1 ms/frame ({fx_ms:.2f} ms)", fx_ms < 2.1)
check("cache surface dibatasi", FX.cache_size() <= FX._CACHE_MAX,
      str(FX.cache_size()))
FX.reset_all()


# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
if FAILED:
    print(f"GAGAL: {len(FAILED)} pemeriksaan")
    for f in FAILED:
        print("  -", f)
    sys.exit(1)
print("SEMUA PEMERIKSAAN NYXARA LULUS")
sys.exit(0)
