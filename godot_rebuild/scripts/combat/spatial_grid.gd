class_name SpatialGrid
extends RefCounted
## Layer 9ci: port of `_system.py::SpatialGrid` and the two module helpers that
## drive it (`update_spatial_grid`, `query_enemies_in_range`).
##
## Every entity is inserted into **exactly one** bucket — the cell of its centre —
## so a query can never return the same entity twice and needs no `seen` set. The
## query mirrors the source loop order (cx outer, cy inner, insertion order inside a
## bucket), the cheap axis-aligned prefilter and then the squared-distance test, so
## the returned order matches pygame: `system_source_oracle.py` pins the order of every
## query and `system_checks.gd` replays it.
##
## `cell_size` stays 60: the source dropped from 100 to 60 after measuring ~2x faster
## crowds. Only minions and heroes (bosses travel through `heroes`) are indexed;
## towers and the nexus are few enough that pygame checks them directly, and so does
## the rebuild.

const DEFAULT_CELL_SIZE := 60


static var _shared: SpatialGrid

var cell_size := DEFAULT_CELL_SIZE
var grid := {}


## `_pos_of`: dictionaries carry the source `x`/`y`, Godot nodes their `position`.
static func _pos_of(entity) -> Vector2:
	if entity is Dictionary:
		return Vector2(float(entity.get("x", 0.0)), float(entity.get("y", 0.0)))
	if entity is Object and "position" in entity:
		return entity.position
	return Vector2.ZERO


static func _team_of(entity) -> Variant:
	if entity is Dictionary:
		return entity.get("team")
	if entity is Object and "team" in entity:
		return entity.team
	return null


static func _alive_of(entity) -> bool:
	if entity is Dictionary:
		return bool(entity.get("alive", false))
	if entity is Object and "alive" in entity:
		return bool(entity.alive)
	return false



func _init(size_value: int = DEFAULT_CELL_SIZE) -> void:
	cell_size = maxi(1, int(size_value))


func clear() -> void:
	grid.clear()


## `int(x // cell_size)` in the source: floor, not truncation, for coordinates < 0.
func bucket_of(x: float, y: float) -> Vector2i:
	return Vector2i(floori(x / float(cell_size)), floori(y / float(cell_size)))


func insert(entity) -> void:
	var point := _pos_of(entity)
	var key := bucket_of(point.x, point.y)
	if grid.has(key):
		var bucket: Array = grid[key]
		bucket.append(entity)
		return
	grid[key] = [entity]


## Entities within `radius` of (x, y). With `team` given, only living enemies of that
## team are returned (`entity.team != team and entity.alive`), filtered inside the same
## loop — the source folded that filter in to avoid a second pass over the candidates.
func query_range(x: float, y: float, radius: float, team: Variant = null) -> Array:
	var results: Array = []
	var cs := float(cell_size)
	var r2 := radius * radius
	var x0 := x - radius
	var x1 := x + radius
	var y0 := y - radius
	var y1 := y + radius
	var min_cx := floori(x0 / cs)
	var max_cx := floori(x1 / cs)
	var min_cy := floori(y0 / cs)
	var max_cy := floori(y1 / cs)
	for cx in range(min_cx, max_cx + 1):
		for cy in range(min_cy, max_cy + 1):
			var key := Vector2i(cx, cy)
			if not grid.has(key):
				continue
			var bucket: Array = grid[key]
			for entity in bucket:
				var point := _pos_of(entity)
				if point.x < x0 or point.x > x1 or point.y < y0 or point.y > y1:
					continue
				if team != null:
					if _team_of(entity) == team or not _alive_of(entity):
						continue
				var dx := point.x - x
				var dy := point.y - y
				if dx * dx + dy * dy <= r2:
					results.append(entity)
	return results


func bucket_count() -> int:
	return grid.size()


# ── module-level helpers (`_grid`, `update_spatial_grid`, `query_enemies_in_range`) ──
## The source's `_grid` singleton (cell_size 60).
static func shared() -> SpatialGrid:
	if _shared == null:
		_shared = SpatialGrid.new(DEFAULT_CELL_SIZE)
	return _shared


static func reset_shared() -> void:
	_shared = null


## `update_spatial_grid(minions, heroes)`: rebuild the grid with the living units only.
static func update_spatial_grid(minions: Array, heroes: Array) -> void:
	var cache: SpatialGrid = shared()
	cache.clear()
	for minion in minions:
		if _alive_of(minion):
			cache.insert(minion)
	for hero in heroes:
		if _alive_of(hero):
			cache.insert(hero)


## `query_enemies_in_range(x, y, radius, team)`: the enemy half of `query_range`.
static func query_enemies_in_range(x: float, y: float, radius: float, team) -> Array:
	return shared().query_range(x, y, radius, team)
