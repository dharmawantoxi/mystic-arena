extends RefCounted
## A single logical hit in flight; the renderer only reads its position.

var id: int
var source_id: int
var target_id: int
var team: int
var damage: int
var position := Vector2.ZERO
var speed := 8.0
var hit_radius := 4.0
var ttl_ticks := 180
var active := true
var kind := "normal"
var splash_radius := 0.0
var burn_dps := 0.0
var burn_duration := 0
var slow_amount := 0.0
var slow_duration := 0
var atk_slow_amount := 0.0
var slow_aoe := 0.0
var skill_down_amount := 0.0
var anti_heal_amount := 0.0
var debuff_duration := 0
