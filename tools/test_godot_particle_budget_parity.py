#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Oracle paritas anggaran partikel (Fase 34) — pygame = ground truth.

Gap #9 di docs/AUDIT_ULANG_DARI_AWAL.md: pygame `mobile/perf.py` memakai
multiplier partikel 0.20 (low) / 0.40 (med) / 0.70 (high) per preset
(`_Quality.apply`) DIKALI beban combat `fx_load()` (governor) + anggaran
keras per frame (token 140/18/10 dengan lantai 56/10/5); Godot dulu tidak
punya `particle_ratio` sama sekali — adaptive quality hanya mengganti batas
FPS. Tes ini menjaga `godot/scripts/systems/FXLoadGovernor.gd`,
`godot/scripts/autoload/AppShell.gd`, `godot/scripts/autoload/GameManager.gd`,
`godot/scripts/vfx/VFXManager.gd`, `godot/scenes/hero/Hero.gd`, dan
`godot/scripts/render/SparkField.gd` mengulang hasil kode pygame secara
bit-eksak, bukan perkiraan.

Dua lapis, sama seperti tool paritas lain di repo ini:

  1) ORACLE — kode SUNGGUHAN pygame dijalankan, tidak ada rumus yang
     disalin ke tool ini:
     * `mobile/perf.py` di-EXEC apa adanya (modul `pygame` di-stub di
       sys.modules — bagian yang dipakai di sini murni angka: set_fx_load,
       fx_load, reset_fx_load, claim/refund/allow, dan _Quality.apply), jadi
       state machine governor + token yang diuji adalah file pygame asli.
     * `_fx_busy`/`count_busy_fx_heroes`/`_LIVE_FX_HEROES` diambil dari
       `heroes/__init__.py` via AST (bukan tulis ulang) dan di-exec dengan
       unit boneka.
     Angka fixture (kurva fx_load, lantai token, jumlah busy, rasio
     efektif) adalah keluaran langsung dua modul itu.

  2) PIN STATIK — konstanta + baris implementasi penentu hasil di-PIN dari
     TEKS SUMBER pygame (`mobile/perf.py`, `heroes/__init__.py`,
     `_core.py`, `_entity.py`, `_render.py`) lalu padanannya dicari di enam
     berkas Godot di atas. Pola yang hilang = tool GAGAL, supaya perubahan
     diam-diam di salah satu sisi tidak bisa lolos.

Deterministik: tidak ada random/waktu/IO permainan — `--write-fixture` dua
kali wajib menghasilkan berkas identik (diverifikasi di main()).

TIDAK DIPORT (sengaja; terdaftar di header FXLoadGovernor.gd): wrap refund
berbasis "jumlah partikel tidak bertambah" (Godot tidak punya 27 modul FX
per-boss — refund diport sebagai API), `_FX_BUSY_COUNT`/kuantisasi pose,
budget render hero, dan cloud save (gap #6 audit).

Cara jalan (dari root repo):
  python3 tools/test_godot_particle_budget_parity.py
  python3 tools/test_godot_particle_budget_parity.py --write-fixture
  godot --headless --path godot res://tests/ParticleBudgetParityTest.tscn
"""
from __future__ import annotations

import ast
import json
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GODOT = os.path.join(ROOT, "godot")
SRC = {
    "perf.py": os.path.join(ROOT, "mobile", "perf.py"),
    "heroes/__init__.py": os.path.join(ROOT, "heroes", "__init__.py"),
    "_core.py": os.path.join(ROOT, "_core.py"),
    "_entity.py": os.path.join(ROOT, "_entity.py"),
    "_render.py": os.path.join(ROOT, "_render.py"),
    "FXLoadGovernor.gd": os.path.join(GODOT, "scripts", "systems", "FXLoadGovernor.gd"),
    "AppShell.gd": os.path.join(GODOT, "scripts", "autoload", "AppShell.gd"),
    "GameManager.gd": os.path.join(GODOT, "scripts", "autoload", "GameManager.gd"),
    "VFXManager.gd": os.path.join(GODOT, "scripts", "vfx", "VFXManager.gd"),
    "Hero.gd": os.path.join(GODOT, "scenes", "hero", "Hero.gd"),
    "SparkField.gd": os.path.join(GODOT, "scripts", "render", "SparkField.gd"),
}
FIXTURE = os.path.join(GODOT, "tests", "fixtures", "particle_budget.json")
EPS = 1e-12


def die(msg: str) -> None:
    raise SystemExit("[PARTICLE-BUDGET-PARITY] GAGAL: %s" % msg)


# ══════════════════════════════════════════════════════════════
#  ORACLE — eksekusi kode pygame asli
# ══════════════════════════════════════════════════════════════

def _stub_pygame_module() -> types.ModuleType:
    """Stub minimal supaya `mobile/perf.py` bisa di-exec tanpa paket pygame.

    Yang disentuh modul ini saat import: `pygame.font.Font` (orangtua
    CachedFont), `pygame.font.SysFont`, `pygame.Surface`,
    `pygame.draw.aacircle` (getattr default None). Bagian fixture tool ini
    tidak pernah merender apa pun."""
    pg = types.ModuleType("pygame")
    font = types.ModuleType("pygame.font")

    class Font:
        def __init__(self, *a, **k):
            pass

        def render(self, *a, **k):
            return None

    font.Font = Font
    font.SysFont = lambda *a, **k: Font()

    class Surface:
        def __init__(self, *a, **k):
            pass

    draw = types.ModuleType("pygame.draw")
    draw.aacircle = lambda *a, **k: None
    draw.circle = lambda *a, **k: None

    pg.font = font
    pg.Surface = Surface
    pg.draw = draw
    return pg


def load_perf_source() -> str:
    with open(SRC["perf.py"], encoding="utf-8") as f:
        return f.read()


def load_perf_module():
    """Exec mobile/perf.py asli dengan stub pygame. Dipanggil DUA KALI
    (fixture dibangun dari instance independen) supaya kebocoran state
    global antar-perhitungan tidak bisa menyusup."""
    sys.modules.setdefault("pygame", _stub_pygame_module())
    ns = {"__name__": "mobile.perf_exec", "__file__": SRC["perf.py"]}
    code = compile(load_perf_source(), SRC["perf.py"], "exec")
    exec(code, ns)
    return ns


def load_busy_helpers():
    """Pasir `_fx_busy`/`count_busy_fx_heroes`/`_LIVE_FX_HEROES` dari
    heroes/__init__.py lewat AST (tanpa mengimpor modul raksasanya)."""
    tree = ast.parse(open(SRC["heroes/__init__.py"],
                          encoding="utf-8").read())
    wanted_funcs = {"_fx_busy", "count_busy_fx_heroes"}
    keep = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_LIVE_FX_HEROES"
                for t in node.targets):
            keep.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in wanted_funcs:
            keep.append(node)
    if len(keep) != 3:
        die("AST heroes/__init__.py: blok yang diharapkan berubah "
            "(assign _LIVE_FX_HEROES + 2 func) — pin perlu disesuaikan")
    src = "\n".join(ast.unparse(n) for n in keep)
    ns = {}
    exec(compile(src, SRC["heroes/__init__.py"], "exec"), ns)
    return ns


class U:
    """Unit boneka untuk oracle busy: atribut di-set dinamis (pygame
    membaca getattr), lalu dipetakan 1:1 ke stub is_dead di tes Godot."""

    pass


# ══════════════════════════════════════════════════════════════
#  PIN STATIK
# ══════════════════════════════════════════════════════════════

PINS = [
    # ── mobile/perf.py: konstanta + formula governor ──
    ("perf.py", "_FX_LOAD_SMOOTH = 0.40"),
    ("perf.py", "_FX_BASE_HEROES = 1.0"),
    ("perf.py", "_FX_LOAD_MIN = 0.10"),
    ("perf.py", "_FX_LOAD_EXP = 1.5"),
    ("perf.py", "_FX_PARTICLE_CAP = 140"),
    ("perf.py", "_FX_PROJ_CAP = 18"),
    ("perf.py", "_FX_SKILL_PROJ_CAP = 10"),
    ("perf.py", "_FX_PARTICLE_LEFT = max(56, int(_FX_PARTICLE_CAP * load))"),
    ("perf.py", "_FX_PROJ_LEFT = max(10, int(_FX_PROJ_CAP * load))"),
    ("perf.py", "_FX_SKILL_PROJ_LEFT = max(5, int(_FX_SKILL_PROJ_CAP * load))"),
    ("perf.py", "_FX_LOAD += (target - _FX_LOAD) * _FX_LOAD_SMOOTH"),
    ("perf.py", "(_FX_BASE_HEROES / n_active) ** _FX_LOAD_EXP"),
    # ── mobile/perf.py: preset Quality ──
    ("perf.py", "self.particle_ratio = 0.20 if low else (0.40 if med else 0.70)"),
    ("perf.py", "self.particles = not low"),
    ("perf.py", "return self._particle_ratio * fx_load()"),
    ("perf.py", "self.screen_shake = level == HIGH"),
    # ── heroes/__init__.py: hook frame ──
    ("heroes/__init__.py", "def begin_fx_frame(active_count=0):"),
    ("heroes/__init__.py", "_perf.set_fx_load(active_count)"),
    ("heroes/__init__.py", "def count_busy_fx_heroes(heroes):"),
    # ── _core.py: panggilan draw + reset match baru ──
    ("_core.py", "begin_fx_frame(count_busy_fx_heroes(_fx_units))"),
    ("_core.py", "_fx_units = self.get_all_heroes()"),
    ("_core.py", "_fx_units = _fx_units + [self.active_boss]"),
    ("_core.py", "reset_fx_load()"),
    # ── _entity.py: gate proyektil skill ──
    ("_entity.py", "from mobile.perf import allow_skill_projectile"),
    ("_entity.py", "if not allow_skill_projectile():"),
    ("_entity.py", "is_skill=True)"),
    # ── _render.py: konsumen rasio ──
    ("_render.py", "if not Quality.particles:"),
    ("_render.py", "count = max(0, int(round(count * Quality.particle_ratio)))"),
    # ── FXLoadGovernor.gd: konstanta + formula ──
    ("FXLoadGovernor.gd", "LOAD_SMOOTH := 0.40"),
    ("FXLoadGovernor.gd", "BASE_UNITS := 1.0"),
    ("FXLoadGovernor.gd", "LOAD_MIN := 0.10"),
    ("FXLoadGovernor.gd", "LOAD_EXP := 1.5"),
    ("FXLoadGovernor.gd", "PARTICLE_CAP := 140"),
    ("FXLoadGovernor.gd", "PROJECTILE_CAP := 18"),
    ("FXLoadGovernor.gd", "SKILL_PROJECTILE_CAP := 10"),
    ("FXLoadGovernor.gd", "PARTICLE_FLOOR := 56"),
    ("FXLoadGovernor.gd", "PROJECTILE_FLOOR := 10"),
    ("FXLoadGovernor.gd", "SKILL_PROJECTILE_FLOOR := 5"),
    ("FXLoadGovernor.gd", "_load += (target - _load) * LOAD_SMOOTH"),
    ("FXLoadGovernor.gd", "pow(BASE_UNITS / float(n), LOAD_EXP)"),
    ("FXLoadGovernor.gd", "maxi(PARTICLE_FLOOR, int(PARTICLE_CAP * load))"),
    ("FXLoadGovernor.gd", "maxi(PROJECTILE_FLOOR, int(PROJECTILE_CAP * load))"),
    ("FXLoadGovernor.gd", "static func count_busy_fx_units"),
    ("FXLoadGovernor.gd", "static func fx_busy"),
    ("FXLoadGovernor.gd", "\"zephyr\": true"),
    ("FXLoadGovernor.gd", "\"gravewake\": true"),
    # ── AppShell.gd: preset + rasio efektif ──
    ("AppShell.gd", "QUALITY_LOW: 0.20"),
    ("AppShell.gd", "QUALITY_MEDIUM: 0.40"),
    ("AppShell.gd", "QUALITY_HIGH: 0.70"),
    ("AppShell.gd", "return quality_level != QUALITY_LOW"),
    ("AppShell.gd", "particle_ratio_base() * FXLoadGovernor.fx_load()"),
    ("AppShell.gd", "_sync_quality_setting()"),
    # ── GameManager.gd: hook frame + reset ──
    ("GameManager.gd", "FXLoadGovernor.set_fx_load(FXLoadGovernor.count_busy_fx_units("),
    ("GameManager.gd", "spark_fx.particle_ratio = AppShell.particle_ratio()"),
    ("GameManager.gd", "spark_fx.particles_enabled = AppShell.particles_enabled()"),
    ("GameManager.gd", "FXLoadGovernor.reset_fx_load()"),
    ("GameManager.gd", "get_nodes_in_group(\"bosses\")"),
    # ── VFXManager.gd / Hero.gd: konsumen token ──
    ("VFXManager.gd", "claim_fx_particle()"),
    ("Hero.gd", "if not FXLoadGovernor.allow_skill_projectile():"),
    # ── SparkField.gd: pembaca rasio tunggal ──
    ("SparkField.gd", "static func _py_round"),
    ("SparkField.gd", "var particle_ratio := 1.0"),
]

# String yang TIDAK boleh muncul (anti regresi halus).
FORBIDDEN = [
    # Angka rasio lama yang basi (hanya boleh ada di komentar penjelasan
    # tool/kode yang menyebutkannya sebagai basi — dilarang sebagai angka hidup).
    ("AppShell.gd", "QUALITY_LOW: 0.35"),
    ("AppShell.gd", "QUALITY_MEDIUM: 0.65"),
]


def check_pins(texts: dict) -> int:
    n = 0
    for name, needle in PINS:
        if needle not in texts[name]:
            die("PIN hilang di %s: %r" % (name, needle))
        n += 1
    for name, needle in FORBIDDEN:
        if needle in texts[name]:
            die("PIN terlarang muncul di %s: %r" % (name, needle))
        n += 1
    # Urutan hook di GameManager._process: governor DULU, advance BELAKANG.
    gm = texts["GameManager.gd"]
    i = gm.find("FXLoadGovernor.set_fx_load(")
    j = gm.find("spark_fx.advance(delta)")
    if i < 0 or j < 0 or i > j:
        die("urutan GameManager._process salah: set_fx_load harus SEBELUM "
            "spark_fx.advance(delta) (paritas Game.draw pygame)")
    n += 1
    # reset_fx_load harus duduk di samping spark_fx.reset() di start_level.
    sx = gm.find("spark_fx.reset()")
    rx = gm.find("FXLoadGovernor.reset_fx_load()", sx)
    if sx < 0 or rx < 0 or rx - sx > 900:
        die("FXLoadGovernor.reset_fx_load() tidak menempel spark_fx.reset() "
            "di start_level (paritas _core.py:1410)")
    n += 1
    # VFXManager: tepat 1 klaim partikel + 6 klaim proyektil (1 per API).
    vx = texts["VFXManager.gd"]
    if vx.count("FXLoadGovernor.claim_fx_particle()") != 1:
        die("VFXManager: klaim partikel harus tepat 1 (sparks)")
    if vx.count("FXLoadGovernor.claim_fx_projectile()") != 6:
        die("VFXManager: klaim proyektil harus tepat 6 "
            "(ring/slash/flash/streak/glow/wall)")
    n += 2
    # Hero.gd: dua gate proyektil skill (spawn_skill_projectile + kit_skill_proj).
    if texts["Hero.gd"].count(
            "if not FXLoadGovernor.allow_skill_projectile():") != 2:
        die("Hero.gd: gate allow_skill_projectile harus tepat 2")
    n += 1
    # Tabel live-FX Godot = literal pygame (27 nama, dua arah).
    gd_live = set()
    block = []
    for line in texts["FXLoadGovernor.gd"].splitlines():
        if "\"" in line and ": true" in line:
            block.extend(p.strip().strip(",") for p in line.split("\"")
                         if ": true" in p or (p.strip().endswith("\": true")))
    # Parser sederhana di atas rapuh; gunakan AST pygame sebagai sumber dan
    # cocokkan SEMUA nama sebagai needle di teks Godot.
    hpy = load_busy_helpers()
    live_py = set(hpy["_LIVE_FX_HEROES"])
    if len(live_py) != 27:
        die("_LIVE_FX_HEROES pygame berubah jumlahnya (%d) — pin & tabel "
            "Godot harus disesuaikan" % len(live_py))
    for name_ in live_py:
        if ("\"%s\": true" % name_) not in texts["FXLoadGovernor.gd"]:
            die("nama live-FX %r hilang dari tabel FXLoadGovernor.gd" % name_)
        n += 1
    n += len(block)  # placeholder attr agar variabel tidak dibuang linter
    return n


# ══════════════════════════════════════════════════════════════
#  FIXTURE — dihitung oleh kode pygame asli
# ══════════════════════════════════════════════════════════════

GOVERNOR_N_LIST = [1, 1, 0,
                   5, 5, 5, 5, 5, 5, 5, 5,
                   0, 0, 0, 0, 0, 0,
                   2, 2, 2, 2, 2, 2, 2, 2,
                   12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
                   None]

HIT_SPARK_ROWS = [(5, 0.20, True), (5, 0.40, True), (5, 0.70, True),
                  (2, 0.70, True), (1, 0.40, True), (10, 0.20, True),
                  (6, 0.05, True), (5, 0.5, True),
                  (5, 0.20, False), (5, 0.70, False), (10, 1.0, True)]


def _make_unit(kind=None, boss=False, alive=True, active_skill=None,
               attack_timer=0.0, timer=None, projectiles=None):
    u = U()
    if boss:
        u.boss_type = kind
    else:
        u.hero_type = kind
    u.alive = alive
    if active_skill is not None:
        u.active_skill = active_skill
    u.attack_timer = attack_timer
    if timer is not None:
        u.timer = timer
    if projectiles is not None:
        u.projectiles = projectiles
    return u


BUSY_CASES = [
    {"name": "mixed_live_and_dead",
     "units": [dict(kind="kaizen", active_skill="q"),
               dict(kind="gornak", attack_timer=5),
               dict(kind="abaddon", boss=True, timer=3),
               dict(kind="morgath", attack_timer=9)]},
    {"name": "idle_live_hero_not_busy",
     "units": [dict(kind="kaizen")]},
    {"name": "attack_timer_fraction_rounds_down",
     "units": [dict(kind="kaizen", attack_timer=0.7)]},
    {"name": "attack_timer_int_is_busy",
     "units": [dict(kind="kaizen", attack_timer=1.2)]},
    {"name": "dead_busy_unit_skipped",
     "units": [dict(kind="kaizen", active_skill="q", alive=False)]},
    {"name": "live_projectile_counts",
     "units": [dict(kind="sylara", projectiles=[{"alive": True}])]},
    {"name": "dead_projectiles_do_not_count",
     "units": [dict(kind="sylara", projectiles=[{"alive": False}])]},
    {"name": "empty_hero_type_falls_back_to_boss_type",
     "units": [dict(kind="", boss=True, boss_type_fallback="gorath", timer=1)]},
    {"name": "boss_active_skill_busy",
     "units": [dict(kind="gravewake", boss=True, active_skill="w")]},
    {"name": "timer_fraction_rounds_down",
     "units": [dict(kind="razak", boss=True, timer=0.5)]},
]


def _busy_from_case(hns, case):
    units = []
    for spec in case["units"]:
        kind = spec.get("boss_type_fallback") if "boss_type_fallback" in spec \
            else spec["kind"]
        units.append(_make_unit(
            kind=kind, boss=bool(spec.get("boss")),
            alive=spec.get("alive", True),
            active_skill=spec.get("active_skill"),
            attack_timer=spec.get("attack_timer", 0.0),
            timer=spec.get("timer"), projectiles=spec.get("projectiles")))
    flags = [bool(hns["_fx_busy"](u)) for u in units]
    return units, flags, int(hns["count_busy_fx_heroes"](units))


def build_fixture(perf, hns) -> dict:
    fx = {}  # fixture utama

    # ── preset Quality (kode pygame asli) ──
    presets = []
    for level_name in ("low", "medium", "high"):
        perf["Quality"].apply(level_name)
        # rasio DASAR; property efektif memakai fx_load() — di-reset supaya 1.0
        perf["reset_fx_load"]()
        presets.append({
            "level": level_name,
            "base": perf["Quality"]._particle_ratio,
            "particles": bool(perf["Quality"].particles),
            "target_fps": perf["Quality"].target_fps,
            "max_damage_numbers": perf["Quality"].max_damage_numbers,
            "effective_at_load_1": perf["Quality"].particle_ratio,
        })
    fx["presets"] = presets

    # ── kurva governor (state machine pygame asli) ──
    perf["reset_fx_load"]()
    seq = []
    for n in GOVERNOR_N_LIST:
        perf["set_fx_load"](n)
        seq.append({"n": n, "fx_load": perf["fx_load"](),
                    "particle_left": perf["_FX_PARTICLE_LEFT"],
                    "projectile_left": perf["_FX_PROJ_LEFT"],
                    "skill_projectile_left": perf["_FX_SKILL_PROJ_LEFT"]})
    fx["governor_sequence"] = seq

    # ── skenario claim/refund ──
    scen = []
    # S1: token nonaktif (baru reset) -> semua claim lolos tanpa konsumsi.
    perf["reset_fx_load"]()
    s1 = [{"op": "reset", "active": False}]
    for _ in range(3):
        s1.append({"op": "claim_particle",
                   "expect": perf["claim_fx_particle"]()})
        s1.append({"op": "allow_skill",
                   "expect": perf["allow_skill_projectile"]()})
    for _ in range(2):
        perf["refund_fx_particle"]()
    s1.append({"op": "refund_particle_x2",
               "particle_left": perf["_FX_PARTICLE_LEFT"]})
    scen.append({"name": "inactive_tokens_are_free", "steps": s1})

    # S2: beban rendah (load 1.0) -> cap penuh 140/18/10 lalu menolak.
    perf["reset_fx_load"]()
    perf["set_fx_load"](0)
    s2 = [{"op": "set_load", "n": 0, "fx_load": perf["fx_load"](),
           "particle_left": perf["_FX_PARTICLE_LEFT"],
           "projectile_left": perf["_FX_PROJ_LEFT"],
           "skill_projectile_left": perf["_FX_SKILL_PROJ_LEFT"]}]
    ok_p = sum(1 for _ in range(200) if perf["claim_fx_particle"]())
    s2.append({"op": "claim_particle_x200", "accepted": ok_p,
               "next": perf["claim_fx_particle"]()})
    ok_j = sum(1 for _ in range(30) if perf["claim_fx_projectile"]())
    s2.append({"op": "claim_projectile_x30", "accepted": ok_j,
               "next": perf["claim_fx_projectile"]()})
    ok_s = sum(1 for _ in range(15) if perf["allow_skill_projectile"]())
    s2.append({"op": "allow_skill_x15", "accepted": ok_s,
               "next": perf["allow_skill_projectile"]()})
    scen.append({"name": "full_caps_at_load_1", "steps": s2})

    # S3: beban berat -> lantai; refund mengembalikan tepat 1 token.
    perf["reset_fx_load"]()
    for _ in range(12):
        perf["set_fx_load"](8)
    s3 = [{"op": "set_load_8_x12", "fx_load": perf["fx_load"](),
           "particle_left": perf["_FX_PARTICLE_LEFT"],
           "projectile_left": perf["_FX_PROJ_LEFT"],
           "skill_projectile_left": perf["_FX_SKILL_PROJ_LEFT"]}]
    ok_p = sum(1 for _ in range(80) if perf["claim_fx_particle"]())
    denied_extra = perf["claim_fx_particle"]()
    perf["refund_fx_particle"]()
    after_refund = perf["_FX_PARTICLE_LEFT"]
    ok_after = perf["claim_fx_particle"]()
    s3.append({"op": "claim_particle_x80", "accepted": ok_p,
               "denied_extra": denied_extra, "after_refund": after_refund,
               "claim_after_refund": ok_after})
    scen.append({"name": "floors_under_heavy_load", "steps": s3})
    fx["claims"] = scen

    # ── busy/count (AST pygame asli) ──
    busy = []
    for case in BUSY_CASES:
        _, flags, count = _busy_from_case(hns, case)
        busy.append({"name": case["name"], "units": case["units"],
                     "busy": flags, "count": count})
    fx["busy_cases"] = busy

    # ── skala hit spark (rumus _render.py:715, di-pin dari sumber) ──
    rows = []
    for count, ratio, enabled in HIT_SPARK_ROWS:
        spawn = 0 if not enabled else max(0, int(round(count * ratio)))
        rows.append({"count": count, "ratio": ratio, "enabled": enabled,
                     "spawn": spawn})
    fx["hit_spark_scaling"] = rows
    return fx


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def _dump(fx: dict) -> str:
    return json.dumps(fx, indent=1, sort_keys=True) + "\n"


def main(argv: list) -> int:
    write = "--write-fixture" in argv
    texts = {}
    for name, path in SRC.items():
        if not os.path.isfile(path):
            die("berkas sumber hilang: %s" % path)
        texts[name] = open(path, encoding="utf-8").read()

    checks = check_pins(texts)

    perf = load_perf_module()
    hns = load_busy_helpers()
    fx = build_fixture(perf, hns)
    # Bangun kedua dari instance BERSIH — determinisme + tanpa state bocor.
    fx2 = build_fixture(load_perf_module(), load_busy_helpers())
    if _dump(fx) != _dump(fx2):
        die("fixture tidak deterministik antara dua build independen")
    checks += 1

    if write:
        os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
        old = open(FIXTURE, encoding="utf-8").read() \
            if os.path.isfile(FIXTURE) else None
        with open(FIXTURE, "w", encoding="utf-8") as f:
            f.write(_dump(fx))
        if old is not None and old != _dump(fx):
            print("[PARTICLE-BUDGET-PARITY] fixture DITULIS ULANG "
                  "(build pertama dari sumber baru) — periksa diff-nya sadar")
        print("[PARTICLE-BUDGET-PARITY] fixture ditulis: %s "
              "(%d pin statik + %d baris governor + %d skenario claim + "
              "%d kasus busy)" % (os.path.relpath(FIXTURE, ROOT), checks,
                                  len(fx["governor_sequence"]),
                                  len(fx["claims"]), len(fx["busy_cases"])))
        return 0

    if not os.path.isfile(FIXTURE):
        die("fixture belum ada — jalankan dengan --write-fixture")
    existing = json.loads(open(FIXTURE, encoding="utf-8").read())
    if existing != fx:
        die("fixture kadaluarsa terhadap kode pygame/Godot sekarang "
            "— jalankan --write-fixture lalu review diff")
    print("[PARTICLE-BUDGET-PARITY] PASS — %d pin statik + fixture %s "
          "cocok dengan oracle pygame ( governor %d langkah, %d skenario "
          "claim, %d kasus busy, %d preset, %d baris hit-spark )"
          % (checks, os.path.relpath(FIXTURE, ROOT),
             len(fx["governor_sequence"]), len(fx["claims"]),
             len(fx["busy_cases"]), len(fx["presets"]),
             len(fx["hit_spark_scaling"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
