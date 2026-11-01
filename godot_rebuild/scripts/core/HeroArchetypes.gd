class_name HeroArchetypes
extends RefCounted

## Native port of hero_archetypes.py. Tables are baked by
## tools/prepare_godot_archetypes.py; the analyzer remains the Python oracle.
const DEFAULT_PATH := "res://data/hero_archetypes.json"
const DEFAULT_DMG_TYPE := "PHYSICAL"
const ARMOR_FACTOR := 0.06
const ARMOR_MAX := 40
const MR_MAX := 0.45
const BOSS_RESIST_BASE := {"mini": [12, 0.10], "true": [18, 0.20]}
const BOSS_RESIST_PROFILE_MODS := {
	"armored": [10.0, -0.040],
	"brute": [3.0, 0.020],
	"balanced": [0.0, 0.0],
	"soft": [-2.0, -0.020],
	"magic": [-4.0, 0.060],
}
const BOSS_RESIST_SCALE := {
	"mini": {"armor": 1.32, "mr": 1.8},
	"true": {"armor": 1.272, "mr": 1.8},
}
const BOSS_RESIST_TARGET_RATIO := 1.0

var archetypes: Dictionary = {}
var boss_resistances: Dictionary = {}
var default_dmg_type := DEFAULT_DMG_TYPE
var resist_base: Dictionary = BOSS_RESIST_BASE.duplicate(true)
var resist_profile_mods: Dictionary = BOSS_RESIST_PROFILE_MODS.duplicate(true)
var resist_scale: Dictionary = BOSS_RESIST_SCALE.duplicate(true)
var resist_target_ratio := BOSS_RESIST_TARGET_RATIO
var load_error := ""


func _init(path := DEFAULT_PATH) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		load_error = "Invalid archetype JSON: %s" % path
		return
	if int(parsed.get("schema", 0)) != 1:
		load_error = "Unsupported archetype schema: %s" % path
		return
	for key: String in [
		"archetypes",
		"boss_resistances",
		"boss_resist_base",
		"boss_resist_profile_mods",
		"boss_resist_scale"
	]:
		if not (parsed.get(key) is Dictionary) or parsed[key].is_empty():
			load_error = "Missing archetype table: %s" % key
			return
	for key: String in ["armor_factor", "armor_max", "mr_max", "boss_resist_target_ratio"]:
		if not parsed.has(key):
			load_error = "Missing archetype constant: %s" % key
			return
	archetypes = parsed.archetypes
	boss_resistances = parsed.boss_resistances
	default_dmg_type = str(parsed.get("default_dmg_type", DEFAULT_DMG_TYPE))
	resist_base = parsed.boss_resist_base
	resist_profile_mods = parsed.boss_resist_profile_mods
	resist_scale = parsed.boss_resist_scale
	resist_target_ratio = float(parsed.boss_resist_target_ratio)
	if not is_equal_approx(float(parsed.armor_factor), ARMOR_FACTOR):
		load_error = "Armor factor disagrees with native combat formula"
	elif int(parsed.armor_max) != ARMOR_MAX or not is_equal_approx(float(parsed.mr_max), MR_MAX):
		load_error = "Resistance clamps disagree with native combat formula"


func valid() -> bool:
	return load_error.is_empty() and not archetypes.is_empty() and not boss_resistances.is_empty()


func get_archetype(hero_type: String, stats: Dictionary = {}) -> Dictionary:
	if not stats.is_empty():
		var forced: Variant = stats.get("dmg_type")
		if _truthy(forced):
			var entry: Dictionary = archetypes.get(hero_type, {}).duplicate(true)
			var school := str(forced).to_upper()
			entry["dmg_type"] = school if school in ["PHYSICAL", "MAGIC"] else default_dmg_type
			if not entry.has("playstyle"):
				entry["playstyle"] = "FIGHTER"
			return entry
	var known: Variant = archetypes.get(hero_type)
	if known is Dictionary and not known.is_empty():
		return known.duplicate(true)
	return {
		"dmg_type": default_dmg_type,
		"playstyle": "FIGHTER",
		"tier": "",
		"power": 0,
		"derived": true
	}


func school_of(hero_type: String, stats: Dictionary = {}) -> String:
	return str(get_archetype(hero_type, stats).dmg_type).to_lower()


func get_boss_resistances(boss_type: String, boss_class := "mini") -> Array:
	var entry: Dictionary = boss_resistances.get(boss_type, {})
	if not entry.is_empty():
		return [int(entry.armor), float(entry.magic_resist)]
	var scale: Dictionary = resist_scale.get(boss_class, {})
	return resist_from_profile(
		"balanced", boss_class, {}, {}, float(scale.get("armor", 1.0)), float(scale.get("mr", 1.0))
	)


func resist_from_profile(
	profile: String,
	boss_class: String,
	base: Dictionary = {},
	mods: Dictionary = {},
	armor_scale := 1.0,
	mr_scale := 1.0,
	armor_off := 0.0
) -> Array:
	var bases := base if not base.is_empty() else resist_base
	var modifiers := mods if not mods.is_empty() else resist_profile_mods
	var baseline: Array = bases.get(boss_class, bases.get("mini", [12, 0.10]))
	var delta: Array = modifiers.get(profile, [0.0, 0.0])
	var raw_armor := float(baseline[0]) + float(delta[0]) * armor_scale + armor_off
	var armor := clampi(_round_half_even(raw_armor), 0, ARMOR_MAX)
	var mr := clampf(float(baseline[1]) + float(delta[1]) * mr_scale, 0.0, MR_MAX)
	return [armor, mr]


func boss_resistances_for(
	boss_type: String, boss_class: String, stats: Dictionary = {}
) -> Dictionary:
	var defaults := get_boss_resistances(boss_type, boss_class)
	var armor_value: Variant = stats.get("armor", defaults[0])
	var mr_value: Variant = stats.get("magic_resist", defaults[1])
	if armor_value == null:
		armor_value = defaults[0]
	if mr_value == null:
		mr_value = defaults[1]
	return {
		"armor": clampi(int(armor_value), 0, ARMOR_MAX),
		"magic_resist": clampf(float(mr_value), 0.0, MR_MAX),
		"profile": profile_for_boss(boss_type, stats),
	}


func profile_for_boss(boss_type: String, stats: Dictionary = {}) -> String:
	var forced: Variant = stats.get("resist_profile")
	if _truthy(forced):
		return str(forced)
	return str(boss_resistances.get(boss_type, {}).get("profile", "balanced"))


static func physical_mitigation(armor_value: float) -> float:
	var armor := maxf(0.0, armor_value)
	return 1.0 - armor * ARMOR_FACTOR / (1.0 + armor * ARMOR_FACTOR)


func short_label(hero_type: String, stats: Dictionary = {}) -> String:
	var entry := get_archetype(hero_type, stats)
	var label := "MAG" if str(entry.dmg_type) == "MAGIC" else "PHY"
	if str(entry.get("playstyle", "")) == "TANK":
		label += "·TNK"
	return label


func detail_label(hero_type: String, stats: Dictionary = {}) -> String:
	var entry := get_archetype(hero_type, stats)
	var school := "MAGIC" if str(entry.dmg_type) == "MAGIC" else "PHYSICAL"
	var suffix := "default"
	if not str(entry.get("tier", "")).is_empty():
		suffix = "Tier %s · Power %d" % [entry.tier, int(entry.power)]
	return "%s · %s · %s" % [school, entry.get("playstyle", "FIGHTER"), suffix]


static func school_color(school: String, playstyle := "") -> Color:
	if playstyle == "TANK":
		return Color("82e2a8")
	return Color("96c4ff") if school == "MAGIC" else Color("ffb25c")


static func _round_half_even(value: float) -> int:
	var lower := floorf(value)
	if value - lower == 0.5:
		var low := int(lower)
		return low if low % 2 == 0 else low + 1
	return int(roundf(value))


static func _truthy(value: Variant) -> bool:
	if value == null:
		return false
	if value is bool:
		return value
	if value is int or value is float:
		return float(value) != 0.0
	if value is String or value is Array or value is Dictionary:
		return not value.is_empty()
	return true
