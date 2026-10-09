extends RefCounted
## Match-global source HitStop state. Requests share one capped freeze window.

const ENABLED := true
const MIN_SECONDS := 0.03
const MAX_SECONDS := 0.08
const FIXED_DT := 1.0 / 60.0
const MAX_FRAMES := 5

var frames := 0
var total := 0
var pending_frames := 0
var pending_total := 0


func trigger(seconds: float = 0.045) -> void:
	if not ENABLED:
		return
	var bounded := clampf(seconds, MIN_SECONDS, MAX_SECONDS)
	var requested := clampi(_round_ties_to_even(bounded / FIXED_DT), 1, MAX_FRAMES)
	if frames > 0:
		if requested > frames:
			frames = requested
			total = requested
	elif requested > pending_frames:
		pending_frames = requested
		pending_total = requested


func consume_frame() -> bool:
	if frames > 0:
		frames -= 1
		return true
	total = 0
	return false


func activate_pending() -> void:
	if pending_frames > frames:
		frames = pending_frames
		total = pending_total
	pending_frames = 0
	pending_total = 0


func is_active() -> bool:
	return frames > 0


func clear() -> void:
	frames = 0
	total = 0
	pending_frames = 0
	pending_total = 0


func _round_ties_to_even(value: float) -> int:
	var whole := floori(value)
	var fraction := value - float(whole)
	if is_equal_approx(fraction, 0.5):
		return whole if whole % 2 == 0 else whole + 1
	return whole + 1 if fraction > 0.5 else whole
