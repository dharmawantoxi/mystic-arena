# Flourish.gd — ornamen "garis - wajik - garis" (port ornamen
# ui_theme.screen_title + main menu 1:1).
#
# Lebar total 460px (dot di ±230), tinggi 16px. Center otomatis mengikuti
# lebar Control aktual (dipakai di dalam container: set
# size_flags_horizontal = EXPAND_FILL agar center = tengah layar).
extends Control
class_name Flourish

var line_color: Color = UiTheme.EDGE_GOLD
var gem_color: Color = UiTheme.GOLD
var dot_color: Color = UiTheme.GOLD_BRIGHT


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(460, 16)


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	var cx := size.x * 0.5
	var fy := size.y * 0.5
	draw_line(Vector2(cx - 220, fy), Vector2(cx - 18, fy), line_color, 2.0)
	draw_line(Vector2(cx + 18, fy), Vector2(cx + 220, fy), line_color, 2.0)
	draw_colored_polygon(PackedVector2Array([
		Vector2(cx - 8, fy), Vector2(cx, fy - 7),
		Vector2(cx + 8, fy), Vector2(cx, fy + 7)]), gem_color)
	draw_circle(Vector2(cx - 230, fy), 3.0, dot_color)
	draw_circle(Vector2(cx + 230, fy), 3.0, dot_color)
