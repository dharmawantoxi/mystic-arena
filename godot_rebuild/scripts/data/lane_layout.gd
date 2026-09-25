extends RefCounted
## Port of PathGenerator.generate_lanes/make_curved_path, 1280x720 source space.

const BLUE_BASE := Vector2(100, 620)
const RED_BASE := Vector2(1180, 100)
const NAMES := ["top", "mid", "bot"]


static func create_paths() -> Array[PackedVector2Array]:
	return [
		curved_path(
			PackedVector2Array(
				[
					Vector2(90, 590),
					Vector2(85, 460),
					Vector2(95, 340),
					Vector2(120, 220),
					Vector2(170, 180),
					Vector2(240, 100),
					Vector2(380, 75),
					Vector2(550, 70),
					Vector2(720, 75),
					Vector2(880, 85),
					Vector2(1030, 110),
					Vector2(1180, 180)
				]
			),
			10
		),
		curved_path(
			PackedVector2Array(
				[
					Vector2(170, 550),
					Vector2(300, 420),
					Vector2(440, 320),
					Vector2(580, 400),
					Vector2(640, 360),
					Vector2(700, 320),
					Vector2(840, 400),
					Vector2(980, 300),
					Vector2(1110, 170)
				]
			),
			8
		),
		curved_path(
			PackedVector2Array(
				[
					Vector2(130, 630),
					Vector2(260, 650),
					Vector2(420, 660),
					Vector2(600, 660),
					Vector2(780, 655),
					Vector2(940, 645),
					Vector2(1070, 620),
					Vector2(1170, 500),
					Vector2(1190, 340),
					Vector2(1195, 250),
					Vector2(1180, 180)
				]
			),
			10
		)
	]


static func curved_path(waypoints: PackedVector2Array, smoothness: int) -> PackedVector2Array:
	if waypoints.size() < 2 or smoothness <= 0:
		return waypoints.duplicate()
	var padded := PackedVector2Array([waypoints[0]])
	padded.append_array(waypoints)
	padded.append(waypoints[-1])
	var result := PackedVector2Array()
	for index in range(padded.size() - 3):
		for step in range(smoothness):
			# Scalar float arithmetic preserves Python double precision before int truncation.
			# Vector2 arithmetic can round a value just below an integer up to that integer.
			var t := float(step) / smoothness
			var x := _coordinate(
				padded[index].x, padded[index + 1].x, padded[index + 2].x, padded[index + 3].x, t
			)
			var y := _coordinate(
				padded[index].y, padded[index + 1].y, padded[index + 2].y, padded[index + 3].y, t
			)
			result.append(Vector2(int(x), int(y)))
	result.append(waypoints[-1])
	return result


static func _coordinate(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
	var t2 := t * t
	var t3 := t * t * t
	return (
		0.5
		* (
			(2 * p1)
			+ (-p0 + p2) * t
			+ (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
			+ (-p0 + 3 * p1 - 3 * p2 + p3) * t3
		)
	)
