class_name KaizenSweep
extends VFXBase
## Sweep impact VFX — a half-circle ground slam that ripples outward.

@export var color: Color = Color(0.847, 0.949, 1.0)
@export var color_mid: Color = Color(0.439, 0.698, 0.902)
@export var color_dark: Color = Color(0.149, 0.353, 0.690)
@export var max_radius: float = 110.0
@export var arc_deg: float = 180.0

var _ring1: Polygon2D
var _ring2: Polygon2D
var _ring3: Polygon2D


func _animate() -> void:
	_build_shape()
	# All rings start small and grow outward, fading in sequence.
	for ring in [_ring1, _ring2, _ring3]:
		ring.scale = Vector2(0.4, 0.4)
		ring.modulate = Color(1, 1, 1, 0.0)
	# Ring 1.
	var t1 := create_tween()
	t1.tween_property(_ring1, "scale", Vector2.ONE, lifetime * 0.7)\
		.set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	t1.parallel().tween_property(_ring1, "modulate:a", 1.0, 0.08)\
		.from(Color(1, 1, 1, 0.0))
	t1.chain().tween_property(_ring1, "modulate:a", 0.0, lifetime * 0.5)
	# Ring 2.
	var t2 := create_tween()
	t2.tween_interval(0.06)
	t2.tween_property(_ring2, "scale", Vector2.ONE, lifetime * 0.7)\
		.set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	t2.parallel().tween_property(_ring2, "modulate:a", 0.85, 0.08)\
		.from(Color(1, 1, 1, 0.0))
	t2.chain().tween_property(_ring2, "modulate:a", 0.0, lifetime * 0.5)
	# Ring 3.
	var t3 := create_tween()
	t3.tween_interval(0.12)
	t3.tween_property(_ring3, "scale", Vector2.ONE, lifetime * 0.8)\
		.set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	t3.parallel().tween_property(_ring3, "modulate:a", 0.7, 0.08)\
		.from(Color(1, 1, 1, 0.0))
	t3.chain().tween_property(_ring3, "modulate:a", 0.0, lifetime * 0.5)


func _build_shape() -> void:
	var pts := PackedVector2Array()
	var steps := 28
	var half := deg_to_rad(arc_deg * 0.5)
	for i in range(steps + 1):
		var t := float(i) / float(steps)
		var a := -half + t * 2.0 * half
		pts.append(Vector2(cos(a) * max_radius, sin(a) * max_radius))
	# Bottom edge: a chord.
	pts.append(Vector2(cos(-half) * max_radius, 0))
	pts.append(Vector2(cos(half) * max_radius, 0))
	_ring1 = Polygon2D.new()
	_ring1.polygon = pts
	_ring1.color = color
	_ring1.modulate.a = 0.9
	add_child(_ring1)
	_ring2 = Polygon2D.new()
	_ring2.polygon = pts.duplicate()
	_ring2.color = color_mid
	_ring2.modulate.a = 0.6
	_ring2.scale = Vector2(0.85, 0.85)
	add_child(_ring2)
	_ring3 = Polygon2D.new()
	_ring3.polygon = pts.duplicate()
	_ring3.color = color_dark
	_ring3.modulate.a = 0.5
	_ring3.scale = Vector2(0.7, 0.7)
	add_child(_ring3)
