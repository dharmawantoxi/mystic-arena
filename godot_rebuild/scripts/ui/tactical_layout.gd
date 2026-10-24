extends RefCounted
## Layer 9bi2: the tactical command visuals of `tactical_commands.py` as pure op lists.
##
## `TacticalCommandManager.draw_world` (world layer, after `effects.draw`, shaken with the
## map) paints the gather marker: rings r = 50..26 (step -8) that only appear while their
## alpha `int((50 - r) * 4 * pulse)` is positive, a 6 px command-colour disc with a 2 px white
## core, and three dashes from every blue hero further than 80 px away while the command is
## GATHER / PROTECT_CASTLE / ATTACK_BOSS / PROTECT_TOWER. `pulse` follows the wall clock
## (`pygame.time.get_ticks() * 0.008`) and fades with `gather_point_timer / 150`.
##
## `TacticalCommandManager.draw_ui` (UI layer, right after `effects.draw_ui`) paints the
## feedback banner: 28 px `body_bold` text centred on (640, 90 + slide), a black box
## (`inflate(20, 8)`, alpha 160 * a / 255), a 2 px border with 6 px corners in the feedback
## colour and a black shadow at +2 px with half the alpha. It slides 20 px up while fading in
## over the first 30 ticks and fades out over the last 30.
##
## Ops use the `tests/draw_recorder.py` format so `tactical_draw_source_oracle.py` pins every
## one. They keep the source RGBA, but `pygame.draw` writes straight onto the alpha-less XRGB
## render surface (`mobile/platform_utils.py`), which keeps the colour and drops the alpha:
## the marker, the dashes and the banner border are painted solid (`SOLID_DRAWS`). Only the
## banner box and texts (blits of alpha surfaces) fade.

const COLORS := {
	"gather": [100, 220, 255],
	"protect_tower": [100, 255, 100],
	"protect_castle": [255, 220, 50],
	"attack_boss": [255, 100, 100],
	"attack_damage_dealer": [255, 130, 255],
}
const DEFAULT_COLOR := [255, 220, 100]
const DASHED_COMMANDS := ["gather", "protect_castle", "attack_boss", "protect_tower"]
const POINT_TICKS := 150.0
const DASH_MIN_DISTANCE := 80.0
const FEEDBACK_CENTER := Vector2i(640, 90)
const FEEDBACK_FONT_SIZE := 28
const FEEDBACK_STYLE := "body_bold"
const SOLID_DRAWS := true


static func command_rgb(command: String) -> Array:
	return COLORS.get(command, DEFAULT_COLOR)


## `draw_world()`: `heroes` holds the positions of the alive blue heroes and `ticks` the
## wall clock in milliseconds.
static func world_ops(
	command: String, point: Vector2, point_active: bool, timer: int, ticks: int, heroes: Array
) -> Array:
	if not point_active or timer <= 0:
		return []
	var alpha_ratio := clampf(float(timer) / POINT_TICKS, 0.0, 1.0)
	var pulse := (sin(float(ticks) * 0.008) * 0.3 + 0.7) * alpha_ratio
	var rgb := command_rgb(command)
	var gx := float(point.x)
	var gy := float(point.y)
	var center := [int(gx), int(gy)]
	var out: Array = []
	for radius in range(50, 20, -8):
		var alpha := int(float(50 - radius) * 4.0 * pulse)
		if alpha > 0:
			out.append(_circle(center, radius, rgb, alpha, 2))
	out.append(_circle(center, 6, rgb, 255, 0))
	out.append(_circle(center, 2, [255, 255, 255], 255, 0))
	if command not in DASHED_COMMANDS:
		return out
	var dash_alpha := int(120.0 * pulse)
	for hero_point in heroes:
		var hx := float(hero_point.x)
		var hy := float(hero_point.y)
		var dx := gx - hx
		var dy := gy - hy
		if sqrt(dx * dx + dy * dy) <= DASH_MIN_DISTANCE:
			continue
		for segment in range(3):
			var t1 := float(segment) * 0.33
			var t2 := t1 + 0.18
			(
				out
				. append(
					{
						"kind": "line",
						"a": [int(hx + dx * t1), int(hy + dy * t1)],
						"b": [int(hx + dx * t2), int(hy + dy * t2)],
						"color": [rgb[0], rgb[1], rgb[2], dash_alpha],
						"mult": 255,
						"width": 2,
					}
				)
			)
	return out


## `draw_ui()`: `measure(text, size) -> Vector2i` sizes the text (the view passes the real
## font, the checks the oracle's fake metrics).
static func feedback_ops(text: String, rgb: Array, timer: int, measure: Callable) -> Array:
	if timer <= 0:
		return []
	var alpha := 255
	if timer < 30:
		alpha = int(255.0 * (float(timer) / 30.0))
	var y_offset := 0
	if timer > 150:
		var progress := clampf(float(180 - timer) / 30.0, 0.0, 1.0)
		alpha = int(255.0 * progress)
		y_offset = int((1.0 - progress) * 20.0)
	var size: Vector2i = measure.call(text, FEEDBACK_FONT_SIZE)
	var x := FEEDBACK_CENTER.x - (size.x >> 1)
	var y := FEEDBACK_CENTER.y + y_offset - (size.y >> 1)
	var box := [x - 10, y - 4, size.x + 20, size.y + 8]
	return [
		{
			"kind": "fill",
			"rect": box,
			"color": [0, 0, 0, int(160.0 * float(alpha) / 255.0)],
			"mult": 255,
			"blend": 0,
		},
		{
			"kind": "rect",
			"rect": box,
			"color": [rgb[0], rgb[1], rgb[2], alpha],
			"mult": 255,
			"width": 2,
			"radius": 6,
		},
		_text(text, [0, 0, 0], alpha >> 1, [x + 2, y + 2]),
		_text(text, rgb, alpha, [x, y]),
	]


static func _circle(center: Array, radius: int, rgb: Array, alpha: int, width: int) -> Dictionary:
	return {
		"kind": "circle",
		"center": center,
		"radius": radius,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
		"mult": 255,
		"width": width,
	}


static func _text(text: String, rgb: Array, mult: int, pos: Array) -> Dictionary:
	return {
		"kind": "text",
		"text": text,
		"size": FEEDBACK_FONT_SIZE,
		"style": FEEDBACK_STYLE,
		"color": [rgb[0], rgb[1], rgb[2], 255],
		"mult": mult,
		"pos": pos,
	}
