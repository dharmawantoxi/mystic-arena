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
