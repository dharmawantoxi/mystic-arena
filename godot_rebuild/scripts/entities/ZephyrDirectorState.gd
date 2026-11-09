class_name ZephyrDirectorState
extends RefCounted

## Source director state/swing slice, not a full procedural animation director.
static var config: Dictionary = {}
var state := "IDLE"
var prev_state := "IDLE"
var state_time := 0.0
var anim_phase := "IDLE"
var swing_active := false
var swing_seen := false
var edge := ""
var bursts: Array = []


static func ensure_loaded() -> void:
	if config.is_empty():
		var file := FileAccess.open("res://data/zephyr_director.json", FileAccess.READ)
		if file != null:
			config = JSON.parse_string(file.get_as_text())


static func attack_phase(progress: float) -> String:
	ensure_loaded()
	var p := clampf(progress, 0.0, 1.0)
	for entry: Array in config.attack_phases:
		if float(entry[1]) <= p and p < float(entry[2]):
			return str(entry[0])
	return "RECOVERY"


func resolve(input: Dictionary) -> String:
	if not bool(input.get("alive", true)):
		return "DEATH"
	if float(input.get("hit_flash", 0.0)) > 0.0:
		return "HURT"
	var skill: Variant = input.get("active_skill")
	if skill != null and str(skill) != "":
		return "SPECIAL" if skill == "r" else "SKILL"
	if bool(input.get("_zp_attack_active", false)):
		var phase := attack_phase(float(input.get("_zp_attack_progress", 0.0)))
		if phase in ["ANTICIPATION", "WINDUP"]:
			return "CHARGE"
		if phase in ["SWING", "IMPACT"]:
			return "SWING"
		return "ATTACK"
	if bool(input.get("_moving_cached", false)):
		return "RUN" if float(input.get("speed", 1.0)) >= 2.2 else "WALK"
	return "IDLE"


func update(dt: float, input: Dictionary) -> void:
	ensure_loaded()
	bursts.clear()
	edge = ""
	var want := resolve(input)
	if want != state:
		var current_priority := int(config.priority.get(state, 0))
		var next_priority := int(config.priority.get(want, 0))
		if state != "DEATH" and (next_priority >= current_priority or state_time > 0.05):
			prev_state = state
			state = want
			state_time = 0.0
	state_time += dt
	anim_phase = attack_phase(float(input.get("_zp_attack_progress", 0.0)))
	var swinging := (
		anim_phase in ["SWING", "IMPACT"] and bool(input.get("_zp_attack_active", false))
	)
	if swinging and not swing_seen:
		edge = "start"
		swing_active = true
		ZephyrBolt.ensure_loaded()
		var p := ZephyrBolt.palette
		var facing := 1 if float(input.get("facing", 1)) >= 0.0 else -1
		bursts.append(
			{
				"position":
				[float(input.get("x", 0.0)) + facing * 6, float(input.get("y", 0.0)) + 42],
				"count": 2,
				"options":
				{
					"speed": [30, 90],
					"life": [0.2, 0.4],
					"size": [2, 4],
					"colors": [p.ash, p.smoke],
					"spread": 1.1,
					"direction": PI if facing > 0 else 0.0,
					"gravity": 90.0,
					"drag": 2.6,
					"shape": "pixel"
				}
			}
		)
	elif not swinging and swing_seen:
		edge = "end"
		swing_active = false
	swing_seen = swinging


func snapshot() -> Dictionary:
	return {
		"state":
		{
			"state": state,
			"prev_state": prev_state,
			"state_time": state_time,
			"anim_phase": anim_phase,
			"swing_active": swing_active,
			"_swing_seen": swing_seen
		},
		"edge": edge,
		"bursts": bursts
	}
