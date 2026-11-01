class_name SpatialGrid
extends RefCounted

## Native _system.SpatialGrid: uniform grid, cell_size 60, one bucket per entity.
## Query order matches pygame: cx outer, cy inner, bucket insertion order.
const DEFAULT_CELL_SIZE := 60
var cell_size := DEFAULT_CELL_SIZE
var grid: Dictionary = {}


func _init(size := DEFAULT_CELL_SIZE) -> void:
	cell_size = size


func clear() -> void:
	grid.clear()


func insert(entity: BattleUnit) -> void:
	var key := Vector2i(floori(entity.pos.x / cell_size), floori(entity.pos.y / cell_size))
	if grid.has(key):
		grid[key].append(entity)
	else:
		grid[key] = [entity]


func query_range(x: float, y: float, radius: float, team := "") -> Array[BattleUnit]:
	var results: Array[BattleUnit] = []
	var r2 := radius * radius
	var x0 := x - radius
	var x1 := x + radius
	var y0 := y - radius
	var y1 := y + radius
	var min_cx := floori(x0 / cell_size)
	var max_cx := floori(x1 / cell_size)
	var min_cy := floori(y0 / cell_size)
	var max_cy := floori(y1 / cell_size)
	for cx in range(min_cx, max_cx + 1):
		for cy in range(min_cy, max_cy + 1):
			var bucket: Array = grid.get(Vector2i(cx, cy), [])
			for entity: BattleUnit in bucket:
				var pos := entity.pos
				if pos.x < x0 or pos.x > x1 or pos.y < y0 or pos.y > y1:
					continue
				if not team.is_empty() and (entity.team == team or not entity.alive):
					continue
				var dx := pos.x - x
				var dy := pos.y - y
				if dx * dx + dy * dy <= r2:
					results.append(entity)
	return results


func bucket_count() -> int:
	return grid.size()
