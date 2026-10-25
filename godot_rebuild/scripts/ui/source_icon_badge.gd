extends Control
## Premium menu-button icon badge; its vector glyph comes from ui_theme.py's baked icon atlas.

const UiSkin = preload("res://scripts/ui/ui_skin.gd")

var icon_name := ""
var accent := Color.WHITE


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	queue_redraw()


func _draw() -> void:
	var center := size * 0.5
	draw_circle(center, 17.0, Color8(12, 14, 26))
	draw_arc(center, 17.0, 0.0, TAU, 48, accent, 2.0, true)
	var atlas := UiSkin.icons_texture()
	var frame := UiSkin.icon_frame(icon_name)
	if atlas != null and frame.size.x > 0.0 and frame.size.y > 0.0:
		draw_texture_rect_region(
			atlas, Rect2(Vector2(1.0, 1.0), Vector2(32.0, 32.0)), frame, accent, false, true
		)
