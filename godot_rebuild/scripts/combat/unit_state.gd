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
var facing := 1.0
