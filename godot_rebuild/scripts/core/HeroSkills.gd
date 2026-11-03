class_name HeroSkills
extends RefCounted

## Native registry and contract facade for the hero_skills/ closed world.
## The bespoke Q/W/E/R implementations remain in the transpiled HeroSkillKit;
## this module validates the exported source contract, exposes the pure
## BaseSkill helpers and is the only runtime entry point to the generated kit.

const DEFAULT_PATH := "res://data/hero_skills.json"
const KIT := preload("res://scripts/entities/generated/HeroSkillKit.gd")

static var _shared: HeroSkills

var load_error := ""
var contract: Dictionary = {}
var starters: Array = []
var skill_keys: Array = []
var handler_map: Dictionary = {}
var registry: Dictionary = {}
var visual_duration_table: Dictionary = {}
var boss_visual_duration: Dictionary = {}
var default_visual_duration: Dictionary = {}
var cooldown_fields: Dictionary = {}
var cooldown_max_fields: Dictionary = {}
var trigger_shake: Dictionary = {}
var trigger_sound_volume: Dictionary = {}
var state_keys: Array = []
var counts: Dictionary = {}
var target_range_slack := 1.15
var skill_range_fallback := 200.0
var require_target := true


func _init(path := DEFAULT_PATH) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary or int(parsed.get("schema", 0)) != 1:
		load_error = "Invalid hero skills JSON: %s" % path
		return
	for key: String in [
		"schema",
		"source",
		"source_sha256",
		"source_files",
		"tooling_sha256",
		"generated_kit",
		"counts",
		"starters",
		"skill_keys",
		"base_modules",
		"legacy_aliases",
		"auto_register",
		"handler_map",
		"registry",
		"recipe_methods",
		"visual_duration",
		"boss_hero_visual_duration",
		"default_visual_duration",
		"state_keys",
		"methods",
		"bridge_methods",
		"base",
		"runtime"
	]:
		if not parsed.has(key):
			load_error = "Missing hero skills field: %s" % key
			return
	contract = parsed
	starters = parsed.get("starters", [])
	skill_keys = parsed.get("skill_keys", [])
	handler_map = parsed.get("handler_map", {})
	registry = parsed.get("registry", {})
	visual_duration_table = parsed.get("visual_duration", {})
	boss_visual_duration = parsed.get("boss_hero_visual_duration", {})
	default_visual_duration = parsed.get("default_visual_duration", {})
	state_keys = parsed.get("state_keys", [])
	counts = parsed.get("counts", {})
	var base: Dictionary = parsed.get("base", {})
	cooldown_fields = base.get("cooldown_fields", {})
	cooldown_max_fields = base.get("cooldown_max_fields", {})
	trigger_shake = base.get("trigger_shake", {})
	trigger_sound_volume = base.get("trigger_sound_volume", {})
	target_range_slack = float(base.get("target_range_slack", 1.15))
	skill_range_fallback = float(base.get("skill_range_fallback", 200.0))
	require_target = bool(base.get("require_target", true))
	if (
		handler_map.is_empty()
		or registry.is_empty()
		or default_visual_duration.is_empty()
		or cooldown_fields.size() != 4
		or state_keys.is_empty()
	):
		load_error = "Hero skills contract requires handlers, recipes and BaseSkill helpers"


static func shared() -> HeroSkills:
	if _shared == null:
		_shared = HeroSkills.new()
	return _shared


func valid() -> bool:
	return load_error.is_empty()


func hero_kind(hero_type: String) -> String:
	var handler := handler_class(hero_type)
	if handler.is_empty():
		return "unknown"
	if starters.has(hero_type):
		return "starter"
	return "boss"


func handler_class(hero_type: String) -> String:
	return str(handler_map.get(hero_type, ""))


func is_starter(hero_type: String) -> bool:
	return starters.has(hero_type)


func has_recipe(hero_type: String) -> bool:
	return registry.has(hero_type)


func recipe_method(hero_type: String, key: String) -> String:
	var recipe = registry.get(hero_type, {})
	return str(recipe.get(key, ""))


func visual_duration(hero_type: String, key: String) -> int:
	if not default_visual_duration.has(key):
		return -1
	var per_hero = boss_visual_duration.get(hero_type, {})
	if per_hero is Dictionary and per_hero.has(key):
		return int(per_hero[key])
	var starter_table = visual_duration_table.get(hero_type, {})
	if starter_table is Dictionary and starter_table.has(key):
		return int(starter_table[key])
	return int(default_visual_duration.get(key, -1))


func cooldown_ready(key: String, timer: int) -> bool:
	if not cooldown_fields.has(key):
		return false
	return timer <= 0


func trigger_plan(hero_type: String, key: String, cooldown_max: int) -> Dictionary:
	if handler_class(hero_type).is_empty() or not cooldown_fields.has(key):
		return {}
	return {
		"cooldown_field": str(cooldown_fields.get(key, "")),
		"cooldown": cooldown_max,
		"active_skill": key,
		"active_skill_timer": visual_duration(hero_type, key),
		"shake": float(trigger_shake.get(key, 0.0)),
		"sound_volume": float(trigger_sound_volume.get(key, 0.0)),
		"max_field": str(cooldown_max_fields.get(key, ""))
	}


func skill_range(
	attack_range: float,
	hero_skill_range: Variant,
	hero_skill_data: Variant,
	fallback: float = 200.0
) -> float:
	var value: Variant = hero_skill_range
	var use_skill_data := false
	if value == null:
		use_skill_data = true
	elif value is bool and not value:
		use_skill_data = true
	elif (value is int or value is float) and float(value) == 0.0:
		use_skill_data = true
	elif value is String and value.is_empty():
		use_skill_data = true
	elif value is Array and value.is_empty():
		use_skill_data = true
	elif value is Dictionary and value.is_empty():
		use_skill_data = true
	if use_skill_data:
		if hero_skill_data is Dictionary:
			value = hero_skill_data.get("skill_range", fallback)
		else:
			value = fallback
	var radius := fallback
	if value is int or value is float:
		radius = float(value)
	elif value is String and value.is_valid_float():
		radius = float(value)
	return maxf(attack_range, radius)


func target_reach(range_value: float) -> float:
	return range_value * target_range_slack


func enemies_in_range(center: Vector2, range_value: float, units: Array) -> Array:
	var result: Array = []
	for index in range(units.size()):
		var unit: Variant = units[index]
		var point: Variant = null
		if unit is Dictionary:
			point = Vector2(float(unit.get("x", 0.0)), float(unit.get("y", 0.0)))
		elif unit is Vector2:
			point = unit
		elif unit is Object:
			point = unit.get("pos")
		if not point is Vector2:
			continue
		var vector: Vector2 = point
		var distance := center.distance_to(vector)
		if distance <= range_value:
			result.append([index, distance])
	return result


func aoe_damage(skill_damage: float, multiplier: float) -> int:
	return int(skill_damage * multiplier)


func init_state(hero) -> void:
	if not valid():
		return
	KIT.init_state(hero)


func update_timers(hero, units: Array, towers: Array, bases: Array) -> void:
	if not valid():
		return
	KIT.update_timers(hero, units, towers, bases)


func cast(hero, key: String, units: Array, towers: Array, bases: Array) -> bool:
	if not valid() or handler_class(str(hero.hero_type)).is_empty():
		return false
	match key:
		"q":
			return KIT.cast_q(hero, units, towers, bases)
		"w":
			return KIT.cast_w(hero, units, towers, bases)
		"e":
			return KIT.cast_e(hero, units, towers, bases)
		"r":
			return KIT.cast_r(hero, units, towers, bases)
	return false
