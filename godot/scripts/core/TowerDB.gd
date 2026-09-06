# TowerDB.gd — Autoload. Port tabel menara + castle dari _core.py.
#
# Sumber kebenaran: godot/data/towers.json + godot/data/nexus.json
# (hasil `python tools/convert_to_godot.py`). Konstanta di bawah hanyalah
# FALLBACK supaya project tetap jalan kalau JSON belum di-generate.
#
# Satuan: pygame menyimpan cooldown/durasi dalam FRAME @60fps. Semua getter
# di sini sudah mengembalikan DETIK, karena Godot berjalan delta-time.
extends Node

const FPS := 60.0

const TOWERS_PATH := "res://data/towers.json"
const NEXUS_PATH := "res://data/nexus.json"

# ═══ FALLBACK — salinan ARCHER/CANNON/ICE/MAGE_LEVELS (_core.py 638-716) ═══
const FALLBACK_PATHS: Dictionary = {
	"archer": {
		1: {"hp": 800, "damage": 20, "range": 180, "cd": 35, "cost": 0},
		2: {"hp": 1050, "damage": 33, "range": 190, "cd": 32, "cost": 175},
		3: {"hp": 1350, "damage": 50, "range": 200, "cd": 30, "cost": 325},
		4: {"hp": 1750, "damage": 72, "range": 210, "cd": 27, "cost": 550},
		5: {"hp": 2200, "damage": 98, "range": 220, "cd": 24, "cost": 850},
		6: {"hp": 2800, "damage": 130, "range": 230, "cd": 22, "cost": 1300,
			"double_shot": true},
	},
	"cannon": {
		2: {"hp": 1200, "damage": 42, "range": 165, "cd": 44, "cost": 175,
			"splash": 45, "burn_dps": 8, "burn_duration": 120},
		3: {"hp": 1500, "damage": 60, "range": 175, "cd": 40, "cost": 325,
			"splash": 55, "burn_dps": 12, "burn_duration": 150},
		4: {"hp": 1900, "damage": 84, "range": 185, "cd": 36, "cost": 550,
			"splash": 65, "burn_dps": 16, "burn_duration": 150},
		5: {"hp": 2400, "damage": 116, "range": 195, "cd": 32, "cost": 850,
			"splash": 80, "burn_dps": 22, "burn_duration": 180},
		6: {"hp": 3000, "damage": 155, "range": 210, "cd": 28, "cost": 1300,
			"splash": 100, "burn_dps": 30, "burn_duration": 180},
	},
	"ice": {
		2: {"hp": 950, "damage": 20, "range": 170, "cd": 26, "cost": 175,
			"slow": 0.25, "slow_duration": 90, "atk_slow": 0.15},
		3: {"hp": 1250, "damage": 32, "range": 180, "cd": 22, "cost": 325,
			"slow": 0.35, "slow_duration": 100, "atk_slow": 0.20},
		4: {"hp": 1600, "damage": 45, "range": 190, "cd": 18, "cost": 550,
			"slow": 0.45, "slow_duration": 110, "atk_slow": 0.25},
		5: {"hp": 2050, "damage": 60, "range": 200, "cd": 16, "cost": 850,
			"slow": 0.55, "slow_duration": 120, "atk_slow": 0.30},
		6: {"hp": 2600, "damage": 78, "range": 220, "cd": 14, "cost": 1300,
			"slow": 0.65, "slow_duration": 150, "slow_aoe": 80, "atk_slow": 0.40},
	},
	"mage": {
		2: {"hp": 850, "damage": 17, "range": 180, "cd": 20, "cost": 175,
			"chain": 2, "skill_down": 0.20, "anti_heal": 0.40, "debuff_duration": 120},
		3: {"hp": 1100, "damage": 26, "range": 190, "cd": 18, "cost": 325,
			"chain": 2, "skill_down": 0.25, "anti_heal": 0.50, "debuff_duration": 130},
		4: {"hp": 1450, "damage": 39, "range": 200, "cd": 16, "cost": 550,
			"chain": 3, "skill_down": 0.30, "anti_heal": 0.60, "debuff_duration": 140},
		5: {"hp": 1850, "damage": 55, "range": 210, "cd": 14, "cost": 850,
			"chain": 3, "skill_down": 0.40, "anti_heal": 0.75, "debuff_duration": 150},
		6: {"hp": 2350, "damage": 70, "range": 230, "cd": 12, "cost": 1300,
			"chain": 4, "skill_down": 0.50, "anti_heal": 1.00, "debuff_duration": 180},
	},
}

const FALLBACK_COLORS: Dictionary = {
	"archer": {"main": Color("#64dc78"), "dark": Color("#328c46")},
	"cannon": {"main": Color("#c8643c"), "dark": Color("#8c3c1e")},
	"ice": {"main": Color("#78c8ff"), "dark": Color("#3c82c8")},
	"mage": {"main": Color("#b450dc"), "dark": Color("#6e2896")},
}

# NEXUS_LEVELS (_core.py 366-423) — castle/nexus, bukan "level peta"
const FALLBACK_NEXUS: Dictionary = {
	1: {"hp": 4000, "damage": 35, "range": 150, "attack_cooldown": 45,
		"minion_scale": 1.0, "upgrade_cost": 500, "color_accent": Color(1, 1, 1)},
	2: {"hp": 6000, "damage": 55, "range": 165, "attack_cooldown": 40,
		"minion_scale": 1.2, "upgrade_cost": 900, "color_accent": Color(0.588, 1, 0.588)},
	3: {"hp": 8500, "damage": 80, "range": 180, "attack_cooldown": 35,
		"minion_scale": 1.4, "upgrade_cost": 1500, "color_accent": Color(0.392, 0.784, 1)},
	4: {"hp": 11500, "damage": 115, "range": 195, "attack_cooldown": 30,
		"minion_scale": 1.7, "upgrade_cost": 2400, "color_accent": Color(1, 0.392, 1)},
	5: {"hp": 15000, "damage": 160, "range": 210, "attack_cooldown": 25,
		"minion_scale": 2.0, "upgrade_cost": 0, "color_accent": Color(1, 0.784, 0.196)},
}

const FALLBACK_SHIELD: Dictionary = {
	"enabled": true, "free_waves": 10, "cost": 850, "damage_reduction": 0.88,
	"hp_ratio": 1.0, "regen_delay_frames": 120, "regen_rate_per_frame": 3.5,
	"color_blue": Color("#64c8ff"), "color_red": Color("#ff7878"),
}

var data: Dictionary = {}
var nexus_data: Dictionary = {}


func _ready() -> void:
	load_all()


func load_all() -> void:
	data = _read_json(TOWERS_PATH)
	nexus_data = _read_json(NEXUS_PATH)
	if data.is_empty():
		push_warning("[TowerDB] towers.json belum ada — pakai fallback. "
			+ "Jalankan tools/convert_to_godot.py")
	if nexus_data.is_empty():
		push_warning("[TowerDB] nexus.json belum ada — pakai fallback.")
	print("[TowerDB] tower types %d · nexus levels %d" % [
		_paths().size(), _nexus_levels().size()])


static func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if parsed is Dictionary else {}


# ══════════════════════════════════════════════════════════
#  MENARA (Tower)
# ══════════════════════════════════════════════════════════

func _paths() -> Dictionary:
	var p = data.get("paths")
	if p is Dictionary and not p.is_empty():
		return p
	# fallback: kunci int (JSON memakai kunci string)
	var out: Dictionary = {}
	for ttype in FALLBACK_PATHS:
		var lvls: Dictionary = {}
		for lv in FALLBACK_PATHS[ttype]:
			lvls[str(lv)] = FALLBACK_PATHS[ttype][lv]
		out[ttype] = lvls
	return out


func _nexus_levels() -> Dictionary:
	var lv = nexus_data.get("levels")
	if lv is Dictionary and not lv.is_empty():
		return lv
	var out: Dictionary = {}
	for k in FALLBACK_NEXUS:
		out[str(k)] = FALLBACK_NEXUS[k]
	return out


func tower_types() -> Array:
	return ["archer", "cannon", "ice", "mage"]


func max_level() -> int:
	return int(data.get("max_level", 6))


func hp_multiplier() -> float:
	return float(data.get("hp_multiplier", 2.5))


func shield_hp_ratio() -> float:
	return float(data.get("shield_hp_ratio", 0.4))


## Biaya membangun menara level 1 (paritas Game.try_build_tower: 100 gold)
func build_cost() -> int:
	return int(data.get("build_cost", 100))


func slot_size() -> float:
	return float(data.get("slot_size", 40))


## BULLET_SPEED pygame 8 px/frame -> 480 px/s
func bullet_speed() -> float:
	return float(data.get("bullet_speed", 8)) * FPS


func bullet_radius() -> float:
	return float(data.get("bullet_radius", 4))


func regen_shield_cost() -> int:
	return int(data.get("regen_shield_cost", 850))


func regen_shield_min_level() -> int:
	return int(data.get("regen_shield_min_level", 4))


func hp_regen_cfg() -> Dictionary:
	var cfg = data.get("hp_regen")
	if cfg is Dictionary:
		return cfg
	return {"enabled": true, "delay_frames": 300, "rate_per_frame": 0.3,
		"max_ratio": 1.0}


## Shield regen berbayar (TOWER_REGEN_SHIELD_* di _core.py 65-69)
func regen_shield_cfg() -> Dictionary:
	var cfg = data.get("regen_shield")
	if cfg is Dictionary:
		return cfg
	return {"enabled": true, "delay_frames": 180, "rate_per_frame": 1.8}


func type_color(ttype: String) -> Color:
	return _color_from(data.get("colors", {}).get(ttype, {}).get("main", ""),
		FALLBACK_COLORS.get(ttype, {}).get("main", Color("#c8c8c8")))


func type_color_dark(ttype: String) -> Color:
	return _color_from(data.get("colors", {}).get(ttype, {}).get("dark", ""),
		FALLBACK_COLORS.get(ttype, {}).get("dark", Color("#646464")))


func type_info(ttype: String) -> Dictionary:
	var info = data.get("info", {}).get(ttype)
	if info is Dictionary:
		return info
	return {"name": ttype.capitalize(), "icon": "", "desc": "", "special": ""}


## Statistik mentah satu level (dict pygame apa adanya; kunci frame belum dikonversi)
func raw_level_stats(ttype: String, level: int) -> Dictionary:
	var paths := _paths()
	var table = paths.get(ttype)
	if table is Dictionary and table.has(str(level)):
		return table[str(level)]
	# paritas Tower._apply_level_stats: level yang tidak ada di jalur non-archer
	# jatuh ke ARCHER_LEVELS[1]
	var archer = paths.get("archer")
	if archer is Dictionary:
		if archer.has(str(level)):
			return archer[str(level)]
		if archer.has("1"):
			return archer["1"]
	return FALLBACK_PATHS["archer"][1]


## Statistik siap pakai: HP sudah ×hp_multiplier, semua durasi DALAM DETIK.
func level_stats(ttype: String, level: int) -> Dictionary:
	var s := raw_level_stats(ttype, level).duplicate()
	var out := {
		"tower_type": ttype,
		"level": level,
		"hp": int(float(s.get("hp", 800)) * hp_multiplier()),
		"damage": float(s.get("damage", 20)),
		"range": float(s.get("range", 180)),
		"cooldown": float(s.get("cd", 35)) / FPS,
		"cost": int(s.get("cost", 0)),
		"desc": str(s.get("desc", "")),
		# kemampuan khusus
		"splash": float(s.get("splash", 0)),
		"slow": float(s.get("slow", 0)),
		"slow_duration": float(s.get("slow_duration", 0)) / FPS,
		"slow_aoe": float(s.get("slow_aoe", 0)),
		"atk_slow": float(s.get("atk_slow", 0)),
		"chain": int(s.get("chain", 1)),
		"double_shot": bool(s.get("double_shot", false)),
		"skill_down": float(s.get("skill_down", 0)),
		"anti_heal": float(s.get("anti_heal", 0)),
		"debuff_duration": float(s.get("debuff_duration", 0)) / FPS,
		"burn_dps": float(s.get("burn_dps", 0)),
		"burn_duration": float(s.get("burn_duration", 0)) / FPS,
		# paritas _entity.Tower: armor default 2 + level, magic_resist 0
		"armor": float(s.get("armor", 2 + level)),
		"magic_resist": float(s.get("magic_resist", 0.0)),
	}
	out["shield"] = int(out["hp"] * shield_hp_ratio())
	return out


## Biaya upgrade KE level berikutnya (0 kalau tidak ada jalur / sudah max)
func upgrade_cost(ttype: String, level: int) -> int:
	if level >= max_level():
		return 0
	return int(raw_level_stats(ttype, level + 1).get("cost", 0))


## Level 1 selalu archer; memilih jalur (cannon/ice/mage) = upgrade ke level 2.
func can_choose_path(level: int) -> bool:
	return level <= 1


func sell_value(ttype: String, level: int, regen_shield_active: bool) -> int:
	# paritas Tower.sell_value: separuh dari total biaya upgrade yang dibayar
	var total := 0
	for lv in range(2, level + 1):
		total += int(raw_level_stats(ttype, lv).get("cost", 0))
	if regen_shield_active:
		total += regen_shield_cost()
	return int(total * 0.5)


# ══════════════════════════════════════════════════════════
#  NEXUS / CASTLE
# ══════════════════════════════════════════════════════════

func nexus_max_level() -> int:
	return int(nexus_data.get("max_level", 5))


func base_radius() -> float:
	return float(nexus_data.get("base_radius", 45))


func nexus_raw(level: int) -> Dictionary:
	var lvls := _nexus_levels()
	var got = lvls.get(str(level))
	if got is Dictionary:
		return got
	if lvls.has("1"):
		return lvls["1"]
	return FALLBACK_NEXUS[1]


## Statistik nexus siap pakai (cooldown -> detik, warna -> Color)
func nexus_stats(level: int) -> Dictionary:
	var s := nexus_raw(level)
	return {
		"level": level,
		"hp": int(s.get("hp", 4000)),
		"damage": float(s.get("damage", 35)),
		"range": float(s.get("range", 150)),
		"cooldown": float(s.get("attack_cooldown", 45)) / FPS,
		"minion_scale": float(s.get("minion_scale", 1.0)),
		"minion_ai_level": int(s.get("minion_ai_level", 1)),
		"upgrade_cost": int(s.get("upgrade_cost", 0)),
		"description": str(s.get("description", "")),
		"color_accent": _color_from(s.get("color_accent", ""), Color(1, 1, 1)),
	}


func shield_cfg() -> Dictionary:
	var cfg = nexus_data.get("shield")
	if cfg is Dictionary and not cfg.is_empty():
		var out: Dictionary = cfg.duplicate()
		out["color_blue"] = _color_from(cfg.get("color_blue", ""), FALLBACK_SHIELD["color_blue"])
		out["color_red"] = _color_from(cfg.get("color_red", ""), FALLBACK_SHIELD["color_red"])
		return out
	return FALLBACK_SHIELD.duplicate()


# ══════════════════════════════════════════════════════════
static func _color_from(v, fallback: Color) -> Color:
	if v is Color:
		return v
	var s := str(v).strip_edges()
	if s.is_empty():
		return fallback
	if not s.begins_with("#"):
		s = "#" + s
	var c := Color(s)
	# Color("rrggbb") tanpa '#' menghasilkan alpha 0 -> warna tak valid
	if c.a == 0.0 and s != "#00000000":
		return fallback
	return c
