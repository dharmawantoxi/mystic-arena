extends RefCounted
## Arena hero silhouettes: the readable per-hero outline plus the placeholder
## shape contract the roster suite still locks.

const HeroMarker = preload("res://scripts/ui/hero_marker.gd")

const SAMPLE: Array[String] = ["kaizen", "thorne", "grimjaw", "vex", "sylara", "zephyr"]
const ROSTER := "res://tests/fixtures/hero_marker_source.json"
const QUANTUM := 10000.0


func run(check: Callable) -> void:
	_placeholder_contract(check)
	_silhouettes(check)
	_fills(check)
	_roster(check)


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


func _roster(check: Callable) -> void:
	# Layer 9aj: the golden fixture is written by
	# `tests/hero_marker_source_oracle.py` (222 heroes, quantised vertex hashes)
	# so the arena art of every hero is pinned, not just the six samples above.
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(ROSTER))
	check.call(fixture is Dictionary and fixture.has("roster"), "hero marker golden fixture parses")
	if not fixture is Dictionary:
		return
	var entries: Dictionary = fixture["roster"]
	var shape: Dictionary = fixture["shape"]
	check.call(int(shape.get("roster", 0)) == 222, "the golden roster keeps 222 heroes")
	var seen := {}
	var widest := 0
	for hero_type in entries:
		var entry: Dictionary = entries[hero_type]
		var points := HeroMarker.silhouette(Vector2.ZERO, 1.0, String(hero_type))
		check.call(
			points.size() == int(entry["sides"]), "roster silhouette vertex count: %s" % hero_type
		)
		var xs: Array[int] = []
		var ys: Array[int] = []
		var reach := 0.0
		for vertex in points:
			xs.append(floori(vertex.x * QUANTUM + 0.5))
			ys.append(floori(vertex.y * QUANTUM + 0.5))
			reach = maxf(reach, vertex.length())
		check.call(_hash(xs) == int(entry["x_hash"]), "roster silhouette x hash: %s" % hero_type)
		check.call(_hash(ys) == int(entry["y_hash"]), "roster silhouette y hash: %s" % hero_type)
		check.call(
			roundi(reach * 1000.0) == int(entry["reach_milli"]),
			"roster silhouette reach: %s" % hero_type
		)
		widest = maxi(widest, int(entry["reach_milli"]))
		seen["%d|%d|%d" % [points.size(), int(entry["x_hash"]), int(entry["y_hash"])]] = hero_type
	check.call(seen.size() == 222, "every roster silhouette is distinct")
	check.call(
		widest <= int(HeroMarker.MAX_REACH * 1000.0), "the whole roster stays inside the team ring"
	)


func _hash(values: Array[int]) -> int:
	var digest := 0
	for value in values:
		digest = (digest * 31 + (value % 1000003 + 1000003) % 1000003) % 1000003
	return digest
