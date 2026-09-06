extends Node
## VFX manager — single point of entry for spawning visual effects.
##
## All gameplay code calls something like:
##     VFXManager.spawn("slash", position, rotation)
## instead of instancing PackedScenes directly. This:
##   * centralises pooling (no per-frame allocations),
##   * keeps the visual hierarchy 70/20/10 (primary shape > secondary > accent),
##   * lets us tweak the entire feel from one place.
##
## Each effect is a PackedScene registered in [member _registry] under a
## string key. Effects that spawn frequently (slash, hit spark, projectile
## trail) are pooled.
##

const DEFAULT_POOL_SIZE := 4

## Effect name -> PackedScene. Populated by [method register] from Main.tscn.
var _registry: Dictionary[String, PackedScene] = {}
## Effect name -> array of currently-free instances (the pool).
var _free: Dictionary[String, Array] = {}
## All currently-active effect root nodes (for fast iteration / cleanup).
var _active: Array[Node] = []
## Per-instance metadata: instance id -> { "key": StringName, "lifetime": float }.
## Used to look up which pool a recycled instance belongs to.
var _meta: Dictionary = {}

func _ready() -> void:
	# Auto-register the built-in effects shipped with the project.
	_register_built_in()


## Register a PackedScene under a key. [param pool_size] is the number of
## pre-warmed instances kept in [member _free]. Set to 0 for one-shot effects
## that should be freed instead of pooled.
func register(key: StringName, scene: PackedScene, pool_size: int = DEFAULT_POOL_SIZE) -> void:
	_registry[key] = scene
	if pool_size > 0:
		_free[key] = []
		for i in pool_size:
			_free[key].append(_instantiate_keyed(key))


func _register_built_in() -> void:
	# Effects are looked up via ResourceLoader — they must exist on disk.
	# The Main scene adds them to the registry at runtime so this stays
	# decoupled from the autoload load order.
	pass


## Spawn an effect at [param pos], rotated to [param rotation] (radians).
## The effect is detached (free after [param lifetime] seconds) unless it
## implements [code]vfx_poolable[/code], in which case it is returned to
## the pool when it calls [method release].
func spawn(key: StringName, pos: Vector2, rotation: float = 0.0,
		lifetime: float = 1.0) -> Node:
	if not _registry.has(key):
		push_warning("VFXManager: unknown effect '%s'" % key)
		return null
	var inst: Node = _take(key)
	if inst == null:
		return null
	add_child(inst)
	inst.global_position = pos
	# Initial rotation is set on the Node2D so child polygons inherit it.
	if inst is Node2D:
		(inst as Node2D).rotation = rotation
	# Track metadata so we know which pool a recycled instance belongs to.
	_meta[inst.get_instance_id()] = {"key": key, "lifetime": lifetime}
	# If this instance was recycled from the pool, kick its animation again.
	# A fresh instance is identified by its _fresh property (set to true on
	# first ready, false on subsequent pool recycles).
	if inst.has_method("play") and inst.get("_fresh") == false:
		inst.play()
	# Schedule lifetime cleanup. The instance's poolable flag controls whether
	# the cleanup recycles or frees.
	var t := get_tree().create_timer(lifetime, false, false)
	t.timeout.connect(_on_effect_timeout.bind(inst, key))
	return inst


## Return a node to the pool. Called by poolable effects when they finish.
func release(key: StringName, inst: Node) -> void:
	if not _free.has(key):
		_free[key] = []
	_free[key].append(inst)
	_active.erase(inst)
	_meta.erase(inst.get_instance_id())
	inst.visible = false
	if inst.get_parent() == self:
		remove_child(inst)


## Tear down all live effects (scene transitions).
func clear_active() -> void:
	for n in _active:
		if is_instance_valid(n):
			n.queue_free()
	_active.clear()


func _take(key: StringName) -> Node:
	if not _free.has(key):
		_free[key] = []
	if _free[key].is_empty():
		return _instantiate_keyed(key)
	var n: Node = _free[key].pop_back()
	n.visible = true
	# Reset to default state in case previous user left dirty state.
	if n.has_method("reset"):
		n.reset()
	# Clean up any leftover meta from the previous use.
	var old_id := n.get_instance_id()
	_meta.erase(old_id)
	return n


func _instantiate_keyed(key: StringName) -> Node:
	var scene: PackedScene = _registry[key]
	return scene.instantiate()


func _on_effect_timeout(inst: Node, key: StringName) -> void:
	if not is_instance_valid(inst):
		return
	if _active.has(inst):
		if inst.get("poolable") == true:
			# Poolable: return to the pool.
			release(key, inst)
			return
		_active.erase(inst)
		_meta.erase(inst.get_instance_id())
		if inst.get_parent() == self:
			remove_child(inst)
		inst.queue_free()
