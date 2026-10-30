extends Control
## Layer 9bs: the main menu draws the baked source background (`Menu._build_main_background`,
## `bake/bake_menu_background.py`). While that sheet is not imported the older decorative
## artwork in `_draw_fallback` (new, deterministic, not a port) still draws.
##
## The source menu blits its art into the 1280x720 render subsurface, and
## `platform_utils.create_display` puts that subsurface at the display origin, so on a
## 2436x1080 phone the art sits at (0, 0) at 1:1 and the leftover 344 px on the right stay
## stone (see `panel_backdrop.gd`). It is never centred and never scaled up: `arena_rect()`
## is the frame the art is drawn into, and `main_menu.gd` sizes this node to it.

const BACKGROUND := "res://assets/art/menu/main_background.png"
const SOURCE_SIZE := Vector2(1280, 720)
static var _texture: Texture2D = null
var background_draws := 0


static func texture() -> Texture2D:
	if _texture == null and ResourceLoader.exists(BACKGROUND):
		_texture = load(BACKGROUND) as Texture2D
	return _texture


## Where the 1280x720 arena lands on a surface of `window`: pinned to the left edge
## (the source never splits the leftover width), scaled down only when the surface is
## smaller than the arena, and centred vertically for the letterbox of tall surfaces.
static func arena_rect(window: Vector2) -> Rect2:
	var factor := minf(1.0, minf(window.x / SOURCE_SIZE.x, window.y / SOURCE_SIZE.y))
	var scaled := SOURCE_SIZE * factor
	return Rect2(Vector2(0.0, (window.y - scaled.y) * 0.5), scaled)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)


func _draw() -> void:
	var baked := texture()
	if baked != null:
		draw_texture_rect(baked, Rect2(Vector2.ZERO, size), false)
		background_draws += 1
		return
	_draw_fallback()


func _draw_fallback() -> void:
	var scale_factor := size / Vector2(1280, 720)
	draw_set_transform(Vector2.ZERO, 0.0, scale_factor)
	draw_rect(Rect2(0, 0, 1280, 720), Color("0b171e"))
	for index in range(18):
		var x := 470.0 + index * 55.0
		draw_line(Vector2(x, 0), Vector2(x - 280, 720), Color("14272d"), 1.0)
	var center := Vector2(947, 348)
	for radius in [125, 177, 220, 268]:
		draw_arc(center, radius, 0, TAU, 100, Color("29453e"), 1.0, true)
	for index in range(12):
		var angle := index * TAU / 12.0
		var direction := Vector2.from_angle(angle)
		draw_line(center + direction * 211, center + direction * 229, Color("b59e67"), 2, true)
	var diamond := PackedVector2Array(
		[
			center + Vector2(0, -160),
			center + Vector2(124, 0),
			center + Vector2(0, 160),
			center + Vector2(-124, 0),
			center + Vector2(0, -160)
		]
	)
	draw_colored_polygon(diamond.slice(0, 4), Color("122b30"))
	draw_polyline(diamond, Color("bda66f"), 2.0, true)
	# An abstract fortress, deliberately distinct from production castle art.
	for offset in [-62, 0, 62]:
		var height := 106.0 if offset == 0 else 65.0
		draw_rect(Rect2(center.x + offset - 16, center.y - height / 2, 32, height), Color("40756d"))
		draw_line(
			Vector2(center.x + offset - 16, center.y - height / 2),
			Vector2(center.x + offset + 16, center.y - height / 2),
			Color("cfbb83"),
			3
		)
	draw_circle(center + Vector2(0, -81), 6, Color("78d8c2"))
	for index in range(24):
		var point := Vector2(660 + (index * 137) % 590, 90 + (index * 89) % 560)
		draw_circle(point, 1.4, Color("66816e"))
	draw_set_transform(Vector2.ZERO)
