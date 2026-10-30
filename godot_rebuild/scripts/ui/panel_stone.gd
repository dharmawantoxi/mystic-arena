extends RefCounted
## Port of `mobile/platform_utils._gambar_panel_samping`: the stone wall that
## fills the leftover width of the Android display surface.
##
## `create_display()` paints it ONCE when the display is created, before any
## screen draws, so the same wall is visible behind every screen - the match
## dock (`side_panel.gd`) and the main menu (`panel_backdrop.gd`). Keeping the
## numbers here means both painters stay identical.

const BASE := Color8(16, 14, 24)
const DARK := Color8(26, 23, 38)
const STONE := Color8(34, 30, 48)
const LINE := Color8(58, 50, 78)
const GOLD := Color8(150, 120, 60)
const BRICK_H := 34
const SHADE_STRIDE := 20
const GOLD_LINE_X := 1.5


## Staggered brick rows clipped to the panel, shade chosen by (row + x) % 3.
## Returned rects are panel-relative so a Control at the panel origin can draw
## them directly.
static func bricks(panel: Rect2i) -> Array:
	var out: Array = []
	if panel.size.x <= 0 or panel.size.y <= 0:
		return out
	var bw := maxi(28, panel.size.x / 4)
	var row := 0
	var y := -BRICK_H
	while y < panel.size.y + BRICK_H:
		var shift := (bw / 2) if (row % 2 == 1) else 0
		var x := panel.position.x - bw
		while x < panel.end.x + bw:
			var brick := Rect2i(x + shift + 1, y + 1, bw - 2, BRICK_H - 2).intersection(panel)
			if brick.size.x > 0 and brick.size.y > 0:
				var dark := (row + x) % 3 == 0
				(
					out
					. append(
						{
							"rect": Rect2i(brick.position - panel.position, brick.size),
							"color": DARK if dark else STONE,
						}
					)
				)
			x += bw
		y += BRICK_H
		row += 1
	return out


## `_gambar_panel_samping` draw order: base, bricks, 20 px dark gradient on the
## arena side, then the gold divider line.
static func paint(canvas: CanvasItem, panel_size: Vector2, stone: Array) -> void:
	canvas.draw_rect(Rect2(Vector2.ZERO, panel_size), BASE)
	for brick in stone:
		canvas.draw_rect(Rect2(brick["rect"]), brick["color"])
		canvas.draw_rect(Rect2(brick["rect"]), LINE, false, 1.0)
	for index in range(SHADE_STRIDE):
		var a := 1.0 - float(index) / float(SHADE_STRIDE)
		var shade := Color8(int(16.0 * a), int(14.0 * a), int(24.0 * a))
		canvas.draw_line(
			Vector2(float(index) + 0.5, 0.0), Vector2(float(index) + 0.5, panel_size.y), shade, 1.0
		)
	canvas.draw_line(Vector2(GOLD_LINE_X, 0.0), Vector2(GOLD_LINE_X, panel_size.y), GOLD, 2.0)
