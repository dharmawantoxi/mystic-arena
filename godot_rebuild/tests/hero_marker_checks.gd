extends RefCounted
## Arena hero silhouettes: the readable per-hero outline plus the placeholder
## shape contract the roster suite still locks.

const HeroMarker = preload("res://scripts/ui/hero_marker.gd")

const SAMPLE: Array[String] = ["kaizen", "thorne", "grimjaw", "vex", "sylara", "zephyr"]


func run(check: Callable) -> void:
	_placeholder_contract(check)
	_silhouettes(check)
	_fills(check)


func _placeholder_contract(check: Callable) -> void:
	for hero_type in SAMPLE:
		var points := HeroMarker.body(Vector2(10, 20), 16, hero_type)
		check.call(
			points.size() >= 4 and points.size() <= 6, "Placeholder stays 4-6 sided: %s" % hero_type
		)
		check.call(
			points == HeroMarker.body(Vector2(10, 20), 16, hero_type),
			"Placeholder is stable: %s" % hero_type
		)


func _silhouettes(check: Callable) -> void:
	var point := Vector2(120, 240)
	var radius := 16.0
	for hero_type in SAMPLE:
		var shape := HeroMarker.silhouette(point, radius, hero_type)
		check.call(shape.size() >= 6, "Silhouette is readable: %s" % hero_type)
		check.call(
			shape == HeroMarker.silhouette(point, radius, hero_type),
			"Silhouette is stable: %s" % hero_type
		)
		check.call(
			_reach(shape, point, radius) <= HeroMarker.MAX_REACH,
			"Silhouette stays inside the team ring: %s" % hero_type
		)
	check.call(
		_width("kaizen", point, radius) < _width("thorne", point, radius),
		"Assassin silhouette is slimmer than the bruiser"
	)
	check.call(
		(
			HeroMarker.silhouette(point, radius, "kaizen")
			!= HeroMarker.silhouette(point, radius, "thorne")
		),
		"Starter silhouettes differ"
	)


func _fills(check: Callable) -> void:
	for hero_type in SAMPLE:
		var fill := HeroMarker.fill(hero_type)
		check.call(fill.a == 1.0, "Hero fill is opaque: %s" % hero_type)
		check.call(fill == HeroMarker.fill(hero_type), "Hero fill is stable: %s" % hero_type)
	check.call(
		HeroMarker.fill("kaizen") == HeroMarker.KAIZEN_FILL, "Kaizen keeps its signature colour"
	)
	check.call(
		HeroMarker.fill("thorne") == HeroMarker.THORNE_FILL, "Thorne keeps its signature colour"
	)
	check.call(HeroMarker.fill("kaizen") != HeroMarker.fill("thorne"), "Starter fills differ")


func _width(hero_type: String, point: Vector2, radius: float) -> float:
	var widest := 0.0
	for vertex in HeroMarker.silhouette(point, radius, hero_type):
		widest = maxf(widest, absf(vertex.x - point.x))
	return widest


func _reach(shape: PackedVector2Array, point: Vector2, radius: float) -> float:
	var farthest := 0.0
	for vertex in shape:
		farthest = maxf(farthest, vertex.distance_to(point))
	return farthest / radius
