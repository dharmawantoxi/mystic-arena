class_name FpsCounter
extends RefCounted

## Native _system.FPSCounter: history 120, display window 30, refresh every 10.
const HISTORY_SIZE := 120
const DISPLAY_WINDOW := 30
const REFRESH_FRAMES := 10
var enabled := false
var fps_history: PackedFloat32Array = PackedFloat32Array()
var frame_count := 0
var display_fps := 0.0
var display_avg := 0.0
var display_min := 0.0
var display_max := 0.0


func toggle() -> void:
	enabled = not enabled


func update(fps: float) -> void:
	fps_history.append(fps)
	if fps_history.size() > HISTORY_SIZE:
		fps_history.remove_at(0)
	frame_count += 1
	if frame_count >= REFRESH_FRAMES:
		frame_count = 0
		if fps_history.is_empty():
			return
		var start := maxi(0, fps_history.size() - DISPLAY_WINDOW)
		var recent := fps_history.slice(start)
		display_fps = recent[recent.size() - 1]
		var total := 0.0
		display_min = recent[0]
		display_max = recent[0]
		for sample: float in recent:
			total += sample
			display_min = minf(display_min, sample)
			display_max = maxf(display_max, sample)
		display_avg = total / recent.size()


func status() -> String:
	if display_fps >= 55.0:
		return "SMOOTH"
	if display_fps >= 40.0:
		return "OK"
	if display_fps >= 25.0:
		return "SLOW"
	return "LAG!"


func status_color() -> Color:
	if display_fps >= 55.0:
		return Color(0.39, 1.0, 0.39)
	if display_fps >= 40.0:
		return Color(1.0, 1.0, 0.39)
	if display_fps >= 25.0:
		return Color(1.0, 0.59, 0.2)
	return Color(1.0, 0.24, 0.24)


func draw(canvas: CanvasItem) -> void:
	if not enabled:
		return
	var origin := Vector2(10, 45)
	var panel := Rect2(origin, Vector2(200, 95))
	canvas.draw_rect(panel, Color(0, 0, 0, 0.78))
	canvas.draw_rect(panel, Color(0.24, 0.27, 0.35), false, 1.0)
	var color := status_color()
	RenderCache.text(
		canvas, origin + Vector2(12, 38), str(int(display_fps)), 40, color, "body_bold"
	)
	RenderCache.text(canvas, origin + Vector2(70, 30), "FPS", 16, Color(0.63, 0.67, 0.75))
	RenderCache.text(canvas, origin + Vector2(140, 20), status(), 15, color)
	RenderCache.text(
		canvas, origin + Vector2(10, 60), "AVG %d" % int(display_avg), 14, Color(0.71, 0.78, 0.86)
	)
	RenderCache.text(
		canvas, origin + Vector2(80, 60), "MIN %d" % int(display_min), 14, Color(0.71, 0.78, 0.86)
	)
	RenderCache.text(
		canvas, origin + Vector2(145, 60), "MAX %d" % int(display_max), 14, Color(0.71, 0.78, 0.86)
	)
	var graph := Rect2(origin + Vector2(10, 65), Vector2(180, 22))
	canvas.draw_rect(graph, Color(0.06, 0.08, 0.14))
	canvas.draw_rect(graph, Color(0.2, 0.24, 0.31), false, 1.0)
	var line60 := graph.position.y + graph.size.y - graph.size.y * minf(60.0, 80.0) / 80.0
	var line30 := graph.position.y + graph.size.y - graph.size.y * minf(30.0, 80.0) / 80.0
	canvas.draw_line(
		Vector2(graph.position.x, line60), Vector2(graph.end.x, line60), Color(0.24, 0.31, 0.24)
	)
	canvas.draw_line(
		Vector2(graph.position.x, line30), Vector2(graph.end.x, line30), Color(0.31, 0.16, 0.16)
	)
	if fps_history.size() > 1:
		var num_bars := mini(fps_history.size(), int(graph.size.x))
		var bar_w := maxf(1.0, graph.size.x / num_bars)
		var start_idx := maxi(0, fps_history.size() - num_bars)
		for index in range(num_bars):
			var fps := fps_history[start_idx + index]
			var height := graph.size.y * minf(fps, 80.0) / 80.0
			var bar := Rect2(
				graph.position + Vector2(index * bar_w, graph.size.y - height),
				Vector2(maxf(1.0, bar_w - 1.0), height)
			)
			var bar_color := Color(0.2, 0.63, 0.2)
			if fps < 55.0:
				bar_color = Color(0.63, 0.63, 0.2)
			if fps < 40.0:
				bar_color = Color(0.63, 0.35, 0.16)
			if fps < 25.0:
				bar_color = Color(0.63, 0.16, 0.16)
			canvas.draw_rect(bar, bar_color)
