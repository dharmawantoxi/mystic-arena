class_name VFXBase
extends Node2D
## Base class for one-shot VFX scenes.
##
## Lifecycle:
##   1. Spawned by VFXManager.spawn(). Sets [member poolable] = false by default
##      so the manager frees us after [member lifetime] seconds.
##   2. [method _ready] kicks off the internal animation.
##   3. Internal tweens drive scale / alpha / color over [member lifetime].
##
## Subclasses override [method _animate] for custom behaviour.

## Lifetime in seconds. The manager uses this to schedule cleanup.
@export var lifetime: float = 0.6
## Set true if this effect should be returned to a pool instead of freed.
@export var poolable: bool = false

## Optional per-effect rotation in radians.
var initial_rotation: float = 0.0

## Reference to the registry key that spawned us, set by VFXManager.
var spawn_key: StringName = &""

## Tracks whether this is a fresh instance (true) or a recycled one (false).
## Reset by [method reset]. The manager uses this to decide whether to call
## [method play] (recycle) or let [method _ready] run (fresh).
var _fresh: bool = true


func _ready() -> void:
	# Only run the initial animation when this is a fresh instance.
	# When the manager pulls us from the pool, _ready is NOT called again —
	# the manager calls [method play] instead.
	if _fresh:
		rotation = initial_rotation
		_animate()
	# The manager's own lifetime timer drives cleanup for both poolable
	# and non-poolable effects, so we don't schedule anything here.


## Called by the manager when this instance is taken from the pool and
## about to be reused. Subclasses can override to restart tweens, etc.
func play() -> void:
	rotation = initial_rotation
	_animate()


func _on_lifetime_done() -> void:
	# Unused: the manager's timer handles cleanup. Kept as a no-op so
	# subclasses can still override it if they want custom cleanup.
	pass


## Override for custom animation.
func _animate() -> void:
	pass


## Called when the effect is reused from the pool.
func reset() -> void:
	modulate = Color(1, 1, 1, 1)
	scale = Vector2.ONE
	rotation = 0.0
	# Remove any in-flight tweens from a previous use.
	# (The simplest reliable way: nothing to do here; tweens complete on
	# their own and write to properties we just reset.)
	_fresh = false
