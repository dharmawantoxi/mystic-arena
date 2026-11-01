class_name AdaptiveQuality
extends RefCounted

## Native _system.AdaptiveQuality: 30-sample FPS average, thresholds 50/35.
const HISTORY_SIZE := 30
const HIGH_THRESHOLD := 50.0
const MEDIUM_THRESHOLD := 35.0
var fps_history: PackedFloat32Array = PackedFloat32Array()
var quality := "high"
var last_fps := 0.0


func tick(fps: float) -> String:
	last_fps = fps
	fps_history.append(fps)
	if fps_history.size() > HISTORY_SIZE:
		fps_history.remove_at(0)
	if fps_history.size() >= 10:
		var total := 0.0
		for sample: float in fps_history:
			total += sample
		var avg := total / fps_history.size()
		if avg >= HIGH_THRESHOLD:
			quality = "high"
		elif avg >= MEDIUM_THRESHOLD:
			quality = "medium"
		else:
			quality = "low"
	return quality


func get_fps() -> float:
	return last_fps


func reset() -> void:
	fps_history.clear()
	quality = "high"
	last_fps = 0.0
