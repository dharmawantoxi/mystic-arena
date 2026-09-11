# HeroArchetypes.gd — Port 1:1 dari hero_archetypes.py (pygame).
#
# Kategori arketipe SEMUA hero yang bisa dimainkan (starter + 216 hero
# unlock dari mini boss & true boss):
#   dmg_type  : PHYSICAL / MAGIC  -> menentukan mitigasi lawan
#   playstyle : TANK / FIGHTER / CARRY -> label UI
#   tier      : S/A/B/C/D vs sesama kelas boss  (label UI)
#   power     : skor absolut 82% DPS + 18% EHP  (label UI)
#
# DATA tidak disalin ke GDScript: blok auto-generated pygame (ARCHETYPES,
# BOSS_RESISTANCES) diekspor tools/convert_to_godot.py ke
#   res://data/hero_archetypes.json   (hero_type -> {dmg_type, playstyle, tier, power})
#   res://data/boss_resistances.json  (boss_type -> {armor, magic_resist, profile, boss_class})
# sehingga regenerasi di sisi Python (tools/analyze_hero_archetypes.py)
# cukup diikuti `python3 tools/convert_to_godot.py`.
#
# Yang diport ke kode adalah KONSTANTA desain + HELPER-nya:
#   get_archetype / school_of            (_entity.Hero.__init__, _core.py:5150)
#   ARMOR_FACTOR/ARMOR_MAX/MR_MAX, BOSS_RESIST_BASE, BOSS_RESIST_PROFILE_MODS,
#   BOSS_RESIST_SCALE, BOSS_RESIST_TARGET_RATIO
#   resist_from_profile / physical_mitigation / get_boss_resistances
#                                        (bosses/base_boss.py:447-464)
#
# Kelas statis (RefCounted + class_name) supaya bisa dipanggil dari tools/tes
# tanpa autoload; data JSON dimuat malas (lazy) sekali per proses.
extends RefCounted
class_name HeroArchetypes

const ARCHETYPES_PATH := "res://data/hero_archetypes.json"
const BOSS_RESISTANCES_PATH := "res://data/boss_resistances.json"

# Hero tanpa entri eksplisit (mis. boss baru yang belum dianalisis)
# dianggap fisik supaya tidak tiba-tiba kebal armor.
const DEFAULT_DMG_TYPE := "PHYSICAL"
const DEFAULT_PLAYSTYLE := "FIGHTER"

# kurva mitigasi armor: red = armor*FACTOR/(1+armor*FACTOR)
const ARMOR_FACTOR := 0.06
const ARMOR_MAX := 40
const MR_MAX := 0.45

# armor/mitigasi dasar per kelas boss (rata-rata yang dijaga kalibrasi)
# boss_class -> [armor, magic_resist]
const BOSS_RESIST_BASE := {
	"mini": [12, 0.10],
	"true": [18, 0.20],
}

# ── BUKAN AUTO-GENERATED: desain dasar, diedit manual (ikuti pygame) ──
# modifier per profil tema boss [delta armor, delta magic_resist] relatif
# terhadap baseline kelas.
const BOSS_RESIST_PROFILE_MODS := {
	"armored": [10.0, -0.040],   # baja/batu/fortress: anti-fisik, tembus sihir
	"brute": [3.0, 0.020],       # petarung kasar: sedikit lebih tahan fisik
	"balanced": [0.0, 0.0],      # boss standar = baseline kelas
	"soft": [-2.0, -0.020],      # HP tipis: menahan sedikit lebih sedikit
	"magic": [-4.0, 0.060],      # caster/undead/void: sihir mental, fisik masuk
}

# hasil kalibrasi: pengali selisih profil per kelas boss
const BOSS_RESIST_SCALE := {
	"mini": {"armor": 1.3200, "mr": 1.8000},
	"true": {"armor": 1.2720, "mr": 1.8000},
}

# rasio target rata-rata (magic DPS efektif) / (fisik DPS efektif)
const BOSS_RESIST_TARGET_RATIO := 1.00

static var _archetypes: Dictionary = {}
static var _boss_resistances: Dictionary = {}
static var _archetypes_loaded := false
static var _boss_resistances_loaded := false


# ════════════════════════════════════════════════════════════════════════
# Loader data JSON (lazy, sekali per proses)
# ════════════════════════════════════════════════════════════════════════

static func _load_json_dict(path: String, label: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_warning("[HeroArchetypes] %s belum ada (%s). Jalankan tools/convert_to_godot.py"
			% [label, path])
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_warning("[HeroArchetypes] gagal membuka %s" % path)
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if parsed is Dictionary else {}


## Tabel ARCHETYPES pygame: hero_type -> {dmg_type, playstyle, tier, power}.
static func archetypes() -> Dictionary:
	if not _archetypes_loaded:
		_archetypes = _load_json_dict(ARCHETYPES_PATH, "hero_archetypes.json")
		_archetypes_loaded = true
	return _archetypes


## Tabel BOSS_RESISTANCES pygame:
## boss_type -> {armor, magic_resist, profile, boss_class}.
static func boss_resistances() -> Dictionary:
	if not _boss_resistances_loaded:
		_boss_resistances = _load_json_dict(BOSS_RESISTANCES_PATH, "boss_resistances.json")
		_boss_resistances_loaded = true
	return _boss_resistances


## Untuk tes/tools: paksa muat ulang dari disk (atau injeksi tabel).
static func reset_cache(arch: Dictionary = {}, res: Dictionary = {}) -> void:
	_archetypes = arch
	_archetypes_loaded = not arch.is_empty()
	_boss_resistances = res
	_boss_resistances_loaded = not res.is_empty()


# ════════════════════════════════════════════════════════════════════════
# Helper arketipe (hero_archetypes.py get_archetype / school_of)
# ════════════════════════════════════════════════════════════════════════

## Dict arketipe hero (SALINAN — aman diubah pemanggil).
##
## Kalau `stats` punya kunci `dmg_type` (override manual di
## boss_data['hero_unlock']), kunci itu menang - desainer bisa menimpa hasil
## analisis per hero tanpa regenerasi data. Nilai selain PHYSICAL/MAGIC
## jatuh ke DEFAULT_DMG_TYPE; playstyle diisi FIGHTER kalau kosong.
## Hero tanpa entri: {dmg_type: PHYSICAL, playstyle: FIGHTER, tier: "",
## power: 0, derived: true}.
static func get_archetype(hero_type: String, stats: Dictionary = {}) -> Dictionary:
	var table := archetypes()
	if not stats.is_empty():
		var forced_raw = stats.get("dmg_type")
		# Python: `if forced:` — None/"" (falsy) tidak dianggap override.
		if forced_raw != null and str(forced_raw) != "":
			var forced := str(forced_raw).to_upper()
			var entry: Dictionary = {}
			if hero_type in table:
				entry = (table[hero_type] as Dictionary).duplicate()
			entry["dmg_type"] = forced if forced in ["PHYSICAL", "MAGIC"] else DEFAULT_DMG_TYPE
			if not entry.has("playstyle"):
				entry["playstyle"] = DEFAULT_PLAYSTYLE
			return entry
	if hero_type in table:
		return (table[hero_type] as Dictionary).duplicate()
	return {"dmg_type": DEFAULT_DMG_TYPE, "playstyle": DEFAULT_PLAYSTYLE,
		"tier": "", "power": 0, "derived": true}


## 'physical' | 'magic' - bentuk lowercase untuk pipeline damage.
static func school_of(hero_type: String, stats: Dictionary = {}) -> String:
	return str(get_archetype(hero_type, stats)["dmg_type"]).to_lower()


# ════════════════════════════════════════════════════════════════════════
# RESISTANSI BOSS PER PROFIL (armor vs magic resist)
# ════════════════════════════════════════════════════════════════════════

## [armor:int, magic_resist:float] satu profil boss pada kelas `boss_class`.
##
## Baseline kelas (mini 12/0.10, true 18/0.20) adalah PUSAT sebarannya;
## yang diskalakan hanya selisih antar profil. Port `_resist_from_profile`
## (parameter base/mods opsional dipertahankan untuk tools kalibrasi).
static func resist_from_profile(profile: String, boss_class: String,
		base: Dictionary = {}, mods: Dictionary = {},
		armor_scale: float = 1.0, mr_scale: float = 1.0,
		armor_off: float = 0.0) -> Array:
	var b: Dictionary = base if not base.is_empty() else BOSS_RESIST_BASE
	var m: Dictionary = mods if not mods.is_empty() else BOSS_RESIST_PROFILE_MODS
	var bpair: Array = b.get(boss_class, b.get("mini", [12, 0.10]))
	var dpair: Array = m.get(profile, [0.0, 0.0])
	var armor := float(bpair[0]) + float(dpair[0]) * armor_scale + armor_off
	# Python round() = half-to-even; lalu clamp 0..ARMOR_MAX sebagai int.
	var armor_i := int(clampf(DamageSchool.py_round(armor), 0.0, float(ARMOR_MAX)))
	var mr := float(bpair[1]) + float(dpair[1]) * mr_scale
	mr = clampf(mr, 0.0, MR_MAX)
	return [armor_i, mr]


## Fraksi damage fisik yang LOLOS armor (0..1).
static func physical_mitigation(armor: float) -> float:
	var a := maxf(0.0, armor)
	return 1.0 - a * ARMOR_FACTOR / (1.0 + a * ARMOR_FACTOR)


## [armor:int, magic_resist:float] untuk satu boss; boss tanpa entri
## (boss baru yang belum dianalisis) memakai profil "balanced" kelasnya
## dengan skala kalibrasi kelas tsb.
static func get_boss_resistances(boss_type: String, boss_class: String = "mini") -> Array:
	var table := boss_resistances()
	if boss_type in table:
		var e: Dictionary = table[boss_type]
		return [int(e.get("armor", 0)), float(e.get("magic_resist", 0.0))]
	var sc: Dictionary = BOSS_RESIST_SCALE.get(boss_class, {})
	return resist_from_profile("balanced", boss_class, {}, {},
		float(sc.get("armor", 1.0)), float(sc.get("mr", 1.0)))


## Profil tema boss ("armored"/"brute"/"balanced"/"soft"/"magic");
## paritas Boss.__init__ base_boss.py:458-464 (fallback "balanced").
static func get_boss_profile(boss_type: String) -> String:
	var table := boss_resistances()
	if boss_type in table:
		return str((table[boss_type] as Dictionary).get("profile", "balanced"))
	return "balanced"
