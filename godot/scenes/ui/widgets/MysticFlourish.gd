# MysticFlourish.gd — garis pembatas emas (port ui_theme.flourish).
extends Control
class_name MysticFlourish

@export var line_color: Color = UiTheme.GOLD_DEEP:
	set(v):
		line_color = v
		queue_redraw()
@export var show_gem: bool = true:
	set(v):
		show_gem = v
		queue_redraw()


func _init(p_show_gem: bool = true) -> void:
	show_gem = p_show_gem
	custom_minimum_size = Vector2(80, 18)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)


func _draw() -> void:
	var cy := size.y * 0.5
	var col := line_color
	col.a = 0.55
	if show_gem:
		var cx := size.x * 0.5
		draw_line(Vector2(10, cy), Vector2(cx - 18, cy), col, 2.0)
		draw_line(Vector2(cx + 18, cy), Vector2(size.x - 10, cy), col, 2.0)
		# Wajik tengah + titik emas di kedua ujung.
		draw_colored_polygon(PackedVector2Array([
			Vector2(cx - 8, cy), Vector2(cx, cy - 7),
			Vector2(cx + 8, cy), Vector2(cx, cy + 7)]), UiTheme.GOLD)
		draw_circle(Vector2(4, cy), 3.0, UiTheme.GOLD_BRIGHT)
		draw_circle(Vector2(size.x - 4, cy), 3.0, UiTheme.GOLD_BRIGHT)
	else:
		draw_line(Vector2(0, cy), Vector2(size.x, cy), col, 1.0)
