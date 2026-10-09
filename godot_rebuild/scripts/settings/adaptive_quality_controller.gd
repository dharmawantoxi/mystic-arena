extends RefCounted
## Source-equivalent sample/cooldown state machine for AdaptiveQuality.update().

const LOW := "low"
const MEDIUM := "medium"
const HIGH := "high"
const COOLDOWN_AFTER_LOWER := 180
const COOLDOWN_AFTER_RAISE := 300

var enabled := true
var low_fps := 26.0
var high_fps := 52.0
var sample_window := 90
var samples: Array[float] = []
var cooldown := 0
var level := HIGH


func _init(
	enabled_value: bool = true,
	low_threshold: float = 26.0,
	high_threshold: float = 52.0,
	window: int = 90
) -> void:
	enabled = enabled_value
	low_fps = low_threshold
	high_fps = high_threshold
	sample_window = window


func configure(initial_level: String) -> void:
	level = initial_level if _is_valid_level(initial_level) else HIGH
	samples.clear()
	cooldown = 0


func update(fps: float) -> String:
	if not enabled:
		return level
	if cooldown > 0:
		cooldown -= 1
		return level

	samples.append(fps)
	if samples.size() < sample_window:
		return level
	var average := 0.0
	for sample in samples:
		average += sample
	average /= float(samples.size())
	samples.clear()

	if average < low_fps and level != LOW:
		level = LOW if level == MEDIUM else MEDIUM
		cooldown = COOLDOWN_AFTER_LOWER
	elif average > high_fps and level != HIGH:
		level = HIGH if level == MEDIUM else MEDIUM
		cooldown = COOLDOWN_AFTER_RAISE
	return level


func _is_valid_level(value: String) -> bool:
	return value in [LOW, MEDIUM, HIGH]
