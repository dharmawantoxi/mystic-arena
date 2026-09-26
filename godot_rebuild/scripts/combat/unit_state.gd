extends RefCounted

const Definition = preload("res://scripts/data/minion_definition.gd")

var id: int
var team: int
var lane: int
var definition: Definition
var position := Vector2.ZERO
var waypoint_index := 0
var hp := 0.0
var cooldown_ticks := 0
var target_id := -1
var alive := true
var is_hero := false
var facing := 1.0
var ai_level := 1
var burn_dps := 0.0
var burn_timer := 0
var burn_accum := 0.0
var burn_tick_cd := 0
var burn_team := -1
var slow_amount := 0.0
var slow_timer := 0
var atk_slow_amount := 0.0
var atk_slow_timer := 0
var skill_down_amount := 0.0
var skill_down_timer := 0
var anti_heal_amount := 0.0
var anti_heal_timer := 0
