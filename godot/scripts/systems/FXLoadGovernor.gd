extends RefCounted
class_name FXLoadGovernor
## FXLoadGovernor.gd — Fase 34 (gap #9 docs/AUDIT_ULANG_DARI_AWAL.md).
##
## Port 1:1 governor beban FX `mobile/perf.py` (bagian "GOVERNOR BEBAN FX
## COMBAT", `mobile/perf.py:591-723`) + penghitung unit sibuk
## `count_busy_fx_heroes`/`_fx_busy` (`heroes/__init__.py:961-997`).
##
## ── MODEL PYGAME ───────────────────────────────────────────
## Sekali per frame (`heroes.begin_fx_frame`, dipanggil `Game.draw`
## `_core.py:2888-2893`) jumlah hero/Boss live-FX yang sedang bertarung
## dilaporkan ke `set_fx_load(n)`. `fx_load` menurun mulus (smoothing
## 0.40) menuju `(1/n)^1.5`, lantai 0.10 — makin ramai combat, makin
## sedikit partikel per unit; efek TIDAK PERNAH hilang total.
## Rasio partikel EFektif = `Quality._particle_ratio` (0.20/0.40/0.70
## per preset, `mobile/perf.py:508`) × `fx_load()` — dibaca setiap spawn.
##
## Di atas rasio ada ANGGARAN KERAS per frame: token spawn direset tiap
## `set_fx_load` ke `cap * load` (lantai 56/10/5) dan dikonsumsi lewat
## `claim_fx_particle/projectile` + `allow_skill_projectile`. `refund_*`
## mengembalikan token bila spawn asli menolak. Kalau token TIDAK aktif
## (belum ada frame match / setelah `reset_fx_load`), semua claim lolos
## (paritas `_FX_TOKENS_ACTIVE` — tes unit pygame tidak kehabisan token).
##
## ── PADANAN GODOT ──────────────────────────────────────────
## `GameManager._process` memanggil `set_fx_load(count_busy_fx_units(..))`
## sekali per frame saat state playing, lalu meneruskan rasio efektif ke
## `SparkField` (= satu-satunya pembaca rasio, paritas `add_hit_particles`
## `_render.py:712-718`). Konsumen token, satu-satu dengan pygame:
##   * `claim_fx_particle`      -> `VFXManager.sparks`  (padanan spawn*
##                                  ParticleSystem modul heroes/*_fx.py)
##   * `claim_fx_projectile`    -> bentuk VFXManager lain (ring/slash/
##                                  flash/streak/glow/wall; padanan spawn*
##                                  ProjectileSystem)
##   * `allow_skill_projectile` -> `Hero.spawn_skill_projectile` +
##                                  `Hero.kit_skill_proj` (padanan gate
##                                  `is_skill` di `_entity.py:4466-4472`
##                                  — `_spawn_skill_projectile` pygame
##                                  mendelegasi ke `_spawn_projectile(
##                                  is_skill=True)`, jadi SEMUA proyektil
##                                  skill kena gate, basic attack tidak).
##
## Deviasi yang dicatat (dengan alasan, bukan bug):
##   1. `_wrap_fx_spawn` pygame membungkus metode spawn* tiap modul FX dan
##      ME-REFUND token bila spawn menolak menambah partikel baru. Godot
##      tidak punya 27 modul per-boss (gap #11 — aproksimasi generik), jadi
##      claim dipasang di choke point `_acquire` VFXManager yang selalu
##      berhasil (pool mencuri actor tertua); refund tetap diport utuh
##      sebagai API + diuji, meski saat ini belum ada pemanggil produksi.
##   2. `pygame count_busy` membaca `alive` (`getattr(h,"alive",True)`);
##      unit Godot memakai `is_dead` — dipetakan `not is_dead`.
##   3. `heroes.begin_fx_frame` juga mengisi `_FX_BUSY_COUNT` (kuantisasi
##      pose `_skill_quant`) + budget render hero; keduanya plumbing cache
##      spesifik-pygame (gap #10) dan TIDAK diport — status sama dengan
##      bagian lain `_skill_quant` yang belum punya padanan.
##   4. pygame menghitung THE active boss (`[self.active_boss]`); Godot
##      menghitung seluruh grup "bosses" — predikat sibuk menyaring boss
##      mati/idle, dan penelusuran repo tidak menemukan dua boss hidup
##      sekaligus, jadi hasilnya setara.
##
## Dikunci: tools/test_godot_particle_budget_parity.py (oracle = kode pygame
## ASLI di-exec dengan stub pygame + pin statis dua arah) dan
## godot/tests/ParticleBudgetParityTest.tscn (replay fixture).

## ── Konstanta governor (mobile/perf.py:608-617) ─────────────
const LOAD_SMOOTH := 0.40     # _FX_LOAD_SMOOTH — kecepatan menyusul per frame
const BASE_UNITS := 1.0       # _FX_BASE_HEROES — masih intensitas penuh
const LOAD_MIN := 0.10        # _FX_LOAD_MIN — lantai intensitas
const LOAD_EXP := 1.5         # _FX_LOAD_EXP — agresivitas turun saat 2+ unit

## ── Anggaran keras per frame (mobile/perf.py:615-619 + lantai :625-627) ──
const PARTICLE_CAP := 140           # _FX_PARTICLE_CAP
const PROJECTILE_CAP := 18          # _FX_PROJ_CAP
const SKILL_PROJECTILE_CAP := 10    # _FX_SKILL_PROJ_CAP
const PARTICLE_FLOOR := 56          # max(56, int(CAP * load))
const PROJECTILE_FLOOR := 10        # max(10, int(18 * load))
const SKILL_PROJECTILE_FLOOR := 5   # max(5, int(10 * load))

## ── Tabel live-FX (_LIVE_FX_HEROES, heroes/__init__.py:699-705) ──
## SATU sumber nama unit yang menyumbang beban partikel, sama persis.
const LIVE_FX_TYPES := {
	"zephyr": true, "gornak": true, "grimjaw": true, "kaizen": true, "vex": true,
	"sylara": true, "abaddon": true, "gorath": true, "razak": true, "khalros": true,
	"alchemist": true, "ancient_apparition": true, "nyzrak": true,
	"xerathis": true, "varkul": true, "ignis_drachorn": true, "zharok": true,
	"vokrahn": true, "pyrenth": true, "krobellus": true, "vhalzun": true,
	"nyxara": true, "gravefang": true, "thalgryn": true, "kunkka": true,
	"syrentha": true, "gravewake": true,
}

static var _load: float = 1.0
static var _particle_left: int = PARTICLE_CAP
static var _projectile_left: int = PROJECTILE_CAP
static var _skill_projectile_left: int = SKILL_PROJECTILE_CAP
static var _tokens_active: bool = false


## Port `set_fx_load(n_active)` (`mobile/perf.py:632-656`): clamp int >= 0,
## target 1.0 selama n <= BASE_UNITS, selainnya max(LOAD_MIN,(BASE/n)^EXP),
## lalu smoothing LOAD_SMOOTH dan reset token frame.
static func set_fx_load(n_active) -> void:
	_tokens_active = true
	# `try: n_active = max(0, int(n_active or 0))` — int() pada None/junk di
	# pygame melempar lalu jatuh ke 0; GDScript int(null) = 0, jadi setara.
	var n: int = n_active if n_active is int or n_active is float else 0
	n = maxi(0, n)
	var target: float
	if float(n) <= BASE_UNITS:
		target = 1.0
	else:
		target = maxf(LOAD_MIN, pow(BASE_UNITS / float(n), LOAD_EXP))
	_load += (target - _load) * LOAD_SMOOTH
	_reset_tokens()


## Port `fx_load()` (`mobile/perf.py:659-661`).
static func fx_load() -> float:
	return _load


## Port `reset_fx_load()` (`mobile/perf.py:664-669`): intensitas kembali
## penuh + token nonaktif (dipanggil saat match baru — `_core.py:1410`,
## di Godot dari `GameManager.start_level` di samping `spark_fx.reset()`).
static func reset_fx_load() -> void:
	_load = 1.0
	_tokens_active = false
	_reset_tokens()


## Port `_reset_fx_tokens()` (`mobile/perf.py:623-629`): isi ulang token
## per frame = cap * load, masing-masing ber-lantai.
static func _reset_tokens() -> void:
	var load := maxf(LOAD_MIN, _load)
	_particle_left = maxi(PARTICLE_FLOOR, int(PARTICLE_CAP * load))
	_projectile_left = maxi(PROJECTILE_FLOOR, int(PROJECTILE_CAP * load))
	_skill_projectile_left = maxi(SKILL_PROJECTILE_FLOOR,
		int(SKILL_PROJECTILE_CAP * load))


## Port `claim_fx_particle()` (`mobile/perf.py:672-680`).
static func claim_fx_particle() -> bool:
	if not _tokens_active:
		return true
	if _particle_left <= 0:
		return false
	_particle_left -= 1
	return true


## Port `refund_fx_particle()` (`mobile/perf.py:683-688`).
static func refund_fx_particle() -> void:
	if not _tokens_active:
		return
	_particle_left += 1


## Port `claim_fx_projectile()` (`mobile/perf.py:691-699`).
static func claim_fx_projectile() -> bool:
	if not _tokens_active:
		return true
	if _projectile_left <= 0:
		return false
	_projectile_left -= 1
	return true


## Port `refund_fx_projectile()` (`mobile/perf.py:702-706`).
static func refund_fx_projectile() -> void:
	if not _tokens_active:
		return
	_projectile_left += 1


## Port `allow_skill_projectile()` (`mobile/perf.py:709-717`) — satu-satunya
## gate yang dipanggil BADAN GAME (`_entity.py:4469`), bukan wrap.
static func allow_skill_projectile() -> bool:
	if not _tokens_active:
		return true
	if _skill_projectile_left <= 0:
		return false
	_skill_projectile_left -= 1
	return true


# ══════════════════════════════════════════════════════════════
#  PENGHITUNG UNIT SIBUK — heroes/__init__.py:961-997
# ══════════════════════════════════════════════════════════════

## Port `_fx_busy(hero)` (`heroes/__init__.py:961-978`): sibuk = sedang
## skill, serangan aktif, timer boss jalan, atau masih ada proyektil hidup.
## `getattr(h, "attack_timer", 0) or 0` + `int(...)`: int() memotong float
## (0.9 -> 0) sama persis dengan int() Python; properti yang tidak ada
## (mis. boss tanpa `timer`/`projectiles`) jatuh ke null -> tidak sibuk,
## sama seperti default 0/None di getattr.
static func fx_busy(unit) -> bool:
	if unit.get("active_skill") != null:
		return true
	var atk = unit.get("attack_timer")
	if atk != null and int(atk) > 0:
		return true
	var tmr = unit.get("timer")
	if tmr != null and int(tmr) > 0:
		return true
	var projs = unit.get("projectiles")
	if projs != null:
		for p in projs:
			if bool(p.get("alive")):
				return true
	return false


## Port `count_busy_fx_heroes(heroes)` (`heroes/__init__.py:982-997`).
## `kind = hero_type or boss_type` — string kosong dianggap tidak ada
## (falsy di Python), sama seperti None.
static func count_busy_fx_units(units: Array) -> int:
	var n := 0
	for u in units:
		if u == null:
			continue
		var kind = str(u.get("hero_type")) if u.get("hero_type") != null else ""
		if kind == "":
			kind = str(u.get("boss_type")) if u.get("boss_type") != null else ""
		if not LIVE_FX_TYPES.has(kind):
			continue
		# `getattr(h, "alive", True)`: unit Godot memakai is_dead (deviasi #2).
		if bool(u.get("is_dead")):
			continue
		if fx_busy(u):
			n += 1
	return n


# ══════════════════════════════════════════════════════════════
#  INTROSPEKSI (hanya untuk test/debug — pygame membaca global
#  `_FX_*` langsung; di sini accessor supaya kapsul tetap utuh).
# ══════════════════════════════════════════════════════════════
static func tokens_active() -> bool:
	return _tokens_active


static func particle_left() -> int:
	return _particle_left


static func projectile_left() -> int:
	return _projectile_left


static func skill_projectile_left() -> int:
	return _skill_projectile_left
