extends Node
## Game-feel bus.
##
## Hit-stop, screen-shake, screen-flash — all driven through this singleton so
## the rest of the game only needs to ask "give me that satisfying *thunk*".
##
## Design rules (from the master prompt):
##   * hit-stop is short and RARE (only for big hits)
##   * screen-shake is proportional to damage tier
##   * screen-flash is short, additive, never white-washes the screen
##
## The camera reads [member offset] every frame to apply shake; that keeps the
## logic here stateless and the rendering side just samples the offset.
##

## Emitted whenever the global clock should freeze for [param seconds].
signal hit_stop_requested(seconds: float)
## Emitted whenever a flash should play. [param color] is added additively.
## [param duration] is in seconds, default 0.08.
signal flash_requested(color: Color, duration: float)

## Shake amplitude in pixels (max displacement). Read by CameraRig.
var shake_amplitude: float = 0.0
## Remaining shake time in seconds.
var shake_time: float = 0.0
## Total shake duration (used to compute falloff).
var shake_total: float = 0.0

## Active hit-stop window in seconds (0 = no freeze).
var hit_stop_remaining: float = 0.0

func _process(delta: float) -> void:
	# Decay shake amplitude linearly over its total duration.
	if shake_time > 0.0:
		shake_time = max(0.0, shake_time - delta)
		var t := 0.0
		if shake_total > 0.0:
			t = 1.0 - (shake_time / shake_total)
		# Smooth-step falloff so big shakes taper gracefully.
		shake_amplitude = lerp(shake_amplitude, 0.0, clamp(t * 2.0, 0.0, 1.0))
	if hit_stop_remaining > 0.0:
		hit_stop_remaining = max(0.0, hit_stop_remaining - delta)


## Add a screen-shake. Higher tier = stronger + longer.
## Tier reference (matches Pygame kaizen_fx.py):
##   0 = micro     (regular attack hit)
##   1 = small     (skill E / W)
##   2 = medium    (skill R / heavy Q2)
##   3 = strong    (ultimate / boss impact)
func shake(tier: int = 0) -> void:
	var amp := [2.0, 4.0, 8.0, 14.0][clamp(tier, 0, 3)]
	var dur := [0.08, 0.14, 0.22, 0.32][clamp(tier, 0, 3)]
	# Always take the *stronger* of the two if we are mid-shake — never cancel
	# a stronger shake with a weaker one.
	if amp >= shake_amplitude:
		shake_amplitude = amp
		shake_total = dur
		shake_time = dur


## Freeze the global clock briefly to sell an impact.
## Do NOT use this for every hit — only for hero-killing strikes and ults.
func hit_stop(seconds: float = 0.05) -> void:
	if seconds > hit_stop_remaining:
		hit_stop_remaining = seconds
		hit_stop_requested.emit(seconds)


## Trigger a brief additive screen-flash.
## Color is added, never replaces — keep alpha low (0.05 – 0.15).
func flash(color: Color = Color(1, 1, 1, 0.1), duration: float = 0.08) -> void:
	flash_requested.emit(color, duration)


## Read by CameraRig every frame. Returns the current shake offset.
func get_shake_offset() -> Vector2:
	if shake_amplitude <= 0.1:
		return Vector2.ZERO
	# Random in a unit circle, scaled by amplitude.
	var dir := Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0))
	if dir.length() > 0.001:
		dir = dir.normalized()
	return dir * shake_amplitude


## Convenience query: is the game currently in a hit-stop window?
## Used by AnimationPlayer to slow its playback if we want maximum impact.
func is_frozen() -> bool:
	return hit_stop_remaining > 0.0
