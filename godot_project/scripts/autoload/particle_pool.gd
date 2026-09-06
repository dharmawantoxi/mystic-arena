extends Node
## Simple object pool for floating damage numbers.
##
## Damage numbers are spawned on every hit, often several per second during
## ultimate animations. Allocating a Label node every time is wasteful and
## triggers GC stutters. We pre-warm a small pool and recycle.
##

const POOL_SIZE := 12

const SCENE := preload("res://scenes/DamageNumber.tscn")

var _free: Array[Node] = []
var _active: Array[Node] = []


func _ready() -> void:
	for i in POOL_SIZE:
		_free.append(_make_one())


## Spawn a damage number at world position [param pos].
## [param value] is shown verbatim; [param crit] scales the size and color.
func spawn(pos: Vector2, value: int, crit: bool = false, kind: String = "normal") -> void:
	var inst: Node = _take()
	if inst == null:
		return
	add_child(inst)
	inst.global_position = pos
	if inst.has_method("set_value"):
		inst.set_value(value, crit, kind)


func _take() -> Node:
	while not _free.is_empty():
		var n: Node = _free.pop_back()
		if is_instance_valid(n):
			_active.append(n)
			return n
	# Pool exhausted — grow lazily. Limited to avoid memory blow-up on spam.
	if _active.size() + _free.size() < POOL_SIZE * 4:
		var extra := _make_one()
		_active.append(extra)
		return extra
	# Hard-cap: just drop the request silently.
	return null


func _make_one() -> Node:
	# The script is already attached on the DamageNumber scene.
	var n := SCENE.instantiate()
	return n


func release(inst: Node) -> void:
	if inst.get_parent() == self:
		remove_child(inst)
	_active.erase(inst)
	if is_instance_valid(inst):
		_free.append(inst)
