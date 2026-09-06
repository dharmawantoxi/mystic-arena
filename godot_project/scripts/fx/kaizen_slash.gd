class_name KaizenSlash
extends VFXBase
## Crescent slash effect.
##
## Primary effect: a single readable crescent shape (Polygon2D) that draws
## from one end of the swing to the other.
## Secondary: a thin trail of small particles.
## Accent: a brief white flash at the centre on impact.
##
## The crescent is built procedurally so we get the wind-blade look
## without needing a sprite. The shape is a hollow crescent (filled +
## inner cutout) so it reads cleanly against any background.

@export var color_inner: Color = Color(0.847, 0.949, 1.0)         # wind_bright
@export var color_mid: Color = Color(0.439, 0.698, 0.902)          # wind_mid
@export var color_outer: Color = Color(0.227, 0.451, 0.690)        # wind_dark
@export var arc_deg: float = 120.0
@export var outer_radius: float = 64.0
@export var thickness: float = 16.0

var _ring: Polygon2D
var _glow: Polygon2D
var _flash: Polygon2D


func _animate() -> void:
	_build_shape()
	# Animate: scale up + fade out, with a brief "snap" at the start.
	scale = Vector2(0.6, 0.6)
	modulate = Color(1, 1, 1, 0.0)
	var tween := create_tween()
	tween.set_parallel(true)
	# Quick pop-in.
	tween.tween_property(self, "scale", Vector2(1.0, 1.0), 0.06)\
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "modulate:a", 1.0, 0.06)
	# Brief flash on the inner.
	tween.tween_property(_flash, "modulate:a", 0.0, 0.18)\
		.from(Color(1, 1, 1, 1))
	# Slow fade out and outward growth.
	tween.chain().tween_property(self, "scale", Vector2(1.18, 1.18), lifetime)\
		.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(self, "modulate:a", 0.0, lifetime)\
		.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tween.parallel().tween_property(_ring, "modulate:a", 0.0, lifetime)


func _build_shape() -> void:
	# Crescent: outer arc + inner arc, connected.
	var pts := PackedVector2Array()
	var steps := 24
	var half := deg_to_rad(arc_deg * 0.5)
	for i in range(steps + 1):
		var t := float(i) / float(steps)
		var a := -half + t * 2.0 * half
		pts.append(Vector2(cos(a), sin(a)) * outer_radius)
	# Inner arc (reverse).
	for i in range(steps + 1):
		var t := float(i) / float(steps)
		var a := half - t * 2.0 * half
		pts.append(Vector2(cos(a), sin(a)) * (outer_radius - thickness))
	_ring = Polygon2D.new()
	_ring.polygon = pts
	_ring.color = color_mid
	_ring.modulate = Color(1, 1, 1, 1)
	add_child(_ring)

	# Glow ring (larger, more transparent, behind the main ring).
	var glow_pts := PackedVector2Array()
	for i in range(steps + 1):
		var t := float(i) / float(steps)
		var a := -half + t * 2.0 * half
		glow_pts.append(Vector2(cos(a), sin(a)) * (outer_radius + 18.0))
	for i in range(steps + 1):
		var t := float(i) / float(steps)
		var a := half - t * 2.0 * half
		glow_pts.append(Vector2(cos(a), sin(a)) * (outer_radius - thickness - 18.0))
	_glow = Polygon2D.new()
	_glow.polygon = glow_pts
	_glow.color = color_outer
	_glow.modulate = Color(1, 1, 1, 0.45)
	add_child(_glow)
	move_child(_glow, 0)

	# Inner flash: a small bright wedge at the centre. The "accent".
	_flash = Polygon2D.new()
	var inner_pts := PackedVector2Array()
	for i in range(steps + 1):
		var t := float(i) / float(steps)
		var a := -half * 0.4 + t * 2.0 * half * 0.4
		inner_pts.append(Vector2(cos(a), sin(a)) * (outer_radius - thickness - 4.0))
	for i in range(steps + 1):
		var t := float(i) / float(steps)
		var a := half * 0.4 - t * 2.0 * half * 0.4
		inner_pts.append(Vector2(cos(a), sin(a)) * 4.0)
	_flash.polygon = inner_pts
	_flash.color = color_inner
	add_child(_flash)
