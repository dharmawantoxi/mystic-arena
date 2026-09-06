class_name KaizenTornado
extends VFXBase
## Tornado VFX — primary effect for Kaizen's R.
##
## Three layers (visual hierarchy 70/20/10):
##   * Primary (70%): a tall, slowly-rotating funnel drawn with concentric
##     wind bands. This is what the player *sees* first.
##   * Secondary (20%): orbiting sparks — small dots cycling around the
##     funnel.
##   * Accent (10%): a brief inner core glow that pulses once on spawn.
##
## The whole thing is procedural — no textures, no shader compilation.

@export var height: float = 180.0
@export var top_radius: float = 28.0
@export var bottom_radius: float = 64.0
@export var bands: int = 6
@export var sparks: int = 8
@export var color_core: Color = Color(0.847, 0.949, 1.0)
@export var color_band: Color = Color(0.439, 0.698, 0.902)
@export var color_dark: Color = Color(0.149, 0.353, 0.690)

var _rotator: Node2D
var _bands: Array[Polygon2D] = []
var _sparks: Array[Polygon2D] = []
var _core: Polygon2D


func _animate() -> void:
	_build_shape()
	# Rotator spins the whole rig.
	_rotator = Node2D.new()
	add_child(_rotator)
	# Reparent bands + sparks under the rotator.
	for b in _bands:
		remove_child(b)
		_rotator.add_child(b)
	for s in _sparks:
		remove_child(s)
		_rotator.add_child(s)
	# Animate.
	var tween := create_tween()
	tween.tween_property(_rotator, "rotation", _rotator.rotation + TAU * 1.5, lifetime)\
		.set_trans(Tween.TRANS_LINEAR)
	tween.parallel().tween_property(self, "modulate:a", 1.0, 0.05)\
		.from(Color(1, 1, 1, 0.0))
	# Core flash decay.
	tween.parallel().tween_property(_core, "modulate:a", 0.6, 0.12)\
		.from(Color(1, 1, 1, 1.0))
	tween.chain().tween_property(self, "modulate:a", 0.0, lifetime * 0.5)\
		.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)


func _build_shape() -> void:
	# Wind bands: concentric ellipses stacked vertically.
	for i in range(bands):
		var t := float(i) / float(bands - 1)
		var y := -height * 0.5 + t * height
		var r := lerp(bottom_radius, top_radius, t)
		# Slight wave for organic feel.
		var pts := PackedVector2Array()
		var steps := 28
		for s in range(steps + 1):
			var a := float(s) / float(steps) * TAU
			# Add a subtle wobble.
			var wobble := sin(a * 3.0 + t * 4.0) * 2.0
			pts.append(Vector2(cos(a) * (r + wobble), sin(a) * (r * 0.4 + wobble * 0.4) + y))
		var band := Polygon2D.new()
		band.polygon = pts
		# Colour: dark at the bottom, mid in the middle, bright at the top.
		var col := color_dark.lerp(color_band, t)
		band.color = col
		band.modulate.a = 0.65
		add_child(band)
		_bands.append(band)
	# Sparks: small dots at varying heights.
	for i in range(sparks):
		var t := randf()
		var y := -height * 0.5 + t * height
		var r := lerp(bottom_radius, top_radius, t) + 6.0
		var ang := randf() * TAU
		var spark := Polygon2D.new()
		spark.polygon = PackedVector2Array([
			Vector2(-2, -2), Vector2(2, -2), Vector2(2, 2), Vector2(-2, 2)
		])
		spark.color = color_core
		spark.position = Vector2(cos(ang) * r, sin(ang) * r * 0.4 + y)
		spark.modulate.a = 0.9
		add_child(spark)
		_sparks.append(spark)
	# Core glow: a tall narrow ellipse at the centre.
	_core = Polygon2D.new()
	var core_pts := PackedVector2Array()
	var cs := 18
	for s in range(cs + 1):
		var a := float(s) / float(cs) * TAU
		core_pts.append(Vector2(cos(a) * 6.0, sin(a) * (height * 0.5)))
	_core.polygon = core_pts
	_core.color = color_core
	add_child(_core)
