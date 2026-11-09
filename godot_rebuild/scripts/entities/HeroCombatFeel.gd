class_name HeroCombatFeel
extends RefCounted

## Native heroes/combat_feel.py bus. One instance per match, never per unit.
## The camera signal forwards once to CombatEffects; do not also add offset().
signal camera_shake(strength: float)

const FIXED_DT := 1.0 / 60.0
const HIT_STOP_MIN := 0.03
const HIT_STOP_MAX := 0.08
const MAX_FRAMES := 5
const DT_MIN := 1.0 / 240.0
const DT_MAX := 1.0 / 20.0
var hit_stop_enabled := true
var shake_enabled := true
var frames := 0
var total := 0
var shake_strength := 0.0
var shake_duration := 0.0
var max_duration := 0.0001
var threshold := 1.0
var frame_ms := -1
var cached_dt := 0.0


static func _python_round(value: float) -> int:
	# Python round uses ties-to-even, unlike Godot roundi.
	var lower := int(floor(value))
	var fraction := value - lower
	if fraction == 0.5:
		return lower if lower % 2 == 0 else lower + 1
	return int(floor(value + 0.5))


func hit_stop(seconds: Variant = 0.045) -> void:
	if not hit_stop_enabled:
		return
	if seconds is String and not seconds.is_valid_float():
		return
	if not (seconds is float or seconds is int or seconds is bool or seconds is String):
		return
	var value := float(seconds)
	# Python max(MIN, min(MAX, nan)) selects MAX in this operand order.
	if is_nan(value):
		value = HIT_STOP_MAX
	value = clampf(value, HIT_STOP_MIN, HIT_STOP_MAX)
	var requested := mini(MAX_FRAMES, maxi(1, _python_round(value / FIXED_DT)))
	if requested > frames:
		frames = requested
		total = requested


func should_freeze_frame() -> bool:
	if not hit_stop_enabled:
		frames = 0
		return false
	if frames > 0:
		frames -= 1
		return true
	total = 0
	return false


func progress() -> float:
	return 1.0 if total <= 0 else 1.0 - float(frames) / total


func add_shake(strength: float, duration := 0.22) -> void:
	if not shake_enabled or strength <= 0.0 or duration <= 0.0:
		return
	if strength <= shake_strength and duration <= shake_duration:
		return
	shake_strength = maxf(shake_strength, strength)
	shake_duration = maxf(shake_duration, duration)
	max_duration = maxf(max_duration, shake_duration)


func shake(strength := 5.0, duration := 0.22, forward_to_camera := true) -> void:
	if strength < 4.0:
		return
	var scaled := strength * 0.5
	add_shake(scaled, maxf(0.0, duration) * 0.7)
	if forward_to_camera:
		camera_shake.emit(scaled * 0.5)


func update_shake(dt: float) -> void:
	if shake_duration <= 0.0:
		shake_strength = 0.0
		return
	shake_duration -= dt
	if shake_duration <= 0.0:
		shake_duration = 0.0
		shake_strength = 0.0
		max_duration = 0.0001


func amount() -> float:
	if shake_duration <= 0.0 or shake_strength <= 0.0:
		return 0.0
	return shake_strength * shake_duration / maxf(0.0001, max_duration)


func offset(rng: RandomNumberGenerator) -> Vector2:
	var strength := amount()
	if strength <= threshold:
		return Vector2.ZERO
	return Vector2(rng.randf_range(-strength, strength), rng.randf_range(-strength, strength))


func frame_dt(now_ms: int) -> float:
	if frame_ms < 0:
		frame_ms = now_ms
		cached_dt = 0.0
		return 0.0
	var elapsed := now_ms - frame_ms
	if elapsed > 0:
		frame_ms = now_ms
		cached_dt = clampf(elapsed / 1000.0, DT_MIN, DT_MAX)
		update_shake(cached_dt)
	return cached_dt


func fx_dt(now_ms: int) -> float:
	var dt := frame_dt(now_ms)
	return dt * 0.18 if dt > 0.0 and frames > 0 else dt


func reset() -> void:
	frames = 0
	total = 0
	shake_strength = 0.0
	shake_duration = 0.0
	max_duration = 0.0001
	frame_ms = -1
	cached_dt = 0.0


func stats() -> Dictionary:
	return {"hitstop_frames": frames, "hitstop_total": total, "shake": amount()}
