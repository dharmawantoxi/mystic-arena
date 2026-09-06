class_name SkillBase
extends Node
## Abstract base for a single skill slot (Q / W / E / R).
##
## Each skill lives as a child of the character and implements its own
## [method cast], [method on_cast_start], [method tick], [method on_cast_end].
## The character iterates over its skills every frame to keep timers ticking.
##
## Lifecycle:
##   1. Player presses the skill button.
##   2. Skill's [method can_cast] returns true.
##   3. Skill's [method cast] runs (deals damage, spawns projectiles, etc).
##   4. Skill goes on cooldown.
##   5. While cooling down, [method tick] decrements [member cooldown_remaining]
##      and may drive any in-flight FX (charge-up, channel, etc).
##

## Emitted when this skill successfully starts casting. UI listens to this to
## trigger its cooldown indicator and audio.
signal cast_started(skill: SkillBase)
## Emitted when the skill goes on cooldown.
signal cooldown_set(skill: SkillBase, seconds: float)
## Emitted every frame the skill has live state (e.g. dash in progress).
signal active_state_changed(skill: SkillBase, is_active: bool)

@export var key: StringName = &"q"          ## Logical slot — q/w/e/r.
@export var display_name: String = "Skill"
@export var cooldown_max: float = 5.0
@export var cast_time: float = 0.0           ## Lockout before the skill fires.
@export var active_time: float = 0.0         ## Window during which tick() is meaningful.

## Reference to the character that owns this skill. Set by the character.
var owner_character: Character = null

## Cooldown remaining in seconds. 0 = ready.
var cooldown_remaining: float = 0.0
## Cast timer — counts up to [member cast_time]. While > 0, the character is
## locked into the cast animation.
var cast_timer: float = 0.0
## Active timer — counts DOWN from [member active_time]. While > 0, [method tick]
## is called every frame.
var active_timer: float = 0.0
## True while casting (cast_timer > 0).
var is_casting: bool = false:
	set(v):
		if v != is_casting:
			is_casting = v
			active_state_changed.emit(self, v)
## True while the active window is open.
var is_active: bool = false:
	set(v):
		if v != is_active:
			is_active = v
			active_state_changed.emit(self, v)


func _ready() -> void:
	# Make sure signals exist even before the skill has an owner.
	pass


## Per-frame update. Decrements timers; subclasses override and call super().
func tick(delta: float) -> void:
	if cooldown_remaining > 0.0:
		cooldown_remaining = max(0.0, cooldown_remaining - delta)
	if cast_timer > 0.0:
		cast_timer = max(0.0, cast_timer - delta)
		if cast_timer <= 0.0:
			is_casting = false
			_on_cast_finished()
	if active_timer > 0.0:
		active_timer = max(0.0, active_timer - delta)
		if active_timer <= 0.0:
			is_active = false
			_on_active_finished()
		_tick_active(delta)


## Try to cast this skill. Returns true if it started.
## Subclasses can override to add pre-conditions (range, target, etc).
func try_cast(cast_pos: Vector2 = Vector2.ZERO) -> bool:
	if cooldown_remaining > 0.0:
		return false
	if is_casting or is_active:
		return false
	_begin_cast(cast_pos)
	return true


## Default cast flow: trigger cast animation, then run the skill logic.
func _begin_cast(cast_pos: Vector2) -> void:
	cooldown_remaining = cooldown_max
	cooldown_set.emit(self, cooldown_max)
	cast_timer = max(0.0001, cast_time)
	is_casting = true
	cast_started.emit(self)
	# If there's no cast time, fire the skill immediately.
	if cast_time <= 0.0:
		is_casting = false
		_on_cast_finished()
	else:
		# Schedule a deferred fire at the end of the cast window.
		var t := get_tree().create_timer(cast_time, false, false)
		t.timeout.connect(_on_cast_finished)


## Subclass hook: when the cast animation completes, deal damage / spawn FX.
func _on_cast_finished() -> void:
	# Default: just open the active window.
	if active_time > 0.0:
		active_timer = active_time
		is_active = true
	else:
		active_timer = 0.0
		is_active = false


## Subclass hook: while the active window is open, do per-frame work.
func _tick_active(_delta: float) -> void:
	pass


## Subclass hook: when the active window ends.
func _on_active_finished() -> void:
	pass


## Helper: is the skill ready to fire?
func can_cast() -> bool:
	return cooldown_remaining <= 0.0 and not is_casting and not is_active


## Helper: fraction of cooldown remaining (0 = just fired, 1 = full cooldown).
func cooldown_fraction() -> float:
	if cooldown_max <= 0.0:
		return 0.0
	return clampf(cooldown_remaining / cooldown_max, 0.0, 1.0)
