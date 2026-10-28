extends RefCounted
## Layer 9bq3: nyxareth's full-screen ultimate layer as a pure op list.
##
## `bosses/level17.py::_NS_nyxareth.draw_nyxareth` calls `_draw_astro_realm_bg` while the
## smart ultimate "4" is active: after the cosmic aura and ground ring, before the skill
## ground FX and the body. The layer covers the WHOLE render surface, so the boss atlas
## bake leaves it out (`SCREEN_LAYERS` in `bake/bake_boss_atlas.py`) and the view paints it
## from here, in screen space, just before the boss sprite.
##
## Ops use the `tests/draw_recorder.py` format, so `nyxareth_realm_draw_source_oracle.py`
## pins every one: a `fill` of the screen with `cosmic_darkest` whose alpha grows from 50 to
## 80 (an SRCALPHA layer blitted onto the screen, so it blends), then 60 stars as `rect`
## ops, every fifth one a bright cross. The stars carry the source RGBA, but `pygame.draw`
## writes onto the alpha-less XRGB render surface (`mobile/platform_utils.py`), which keeps
## the colour and drops the alpha, so `OPAQUE_STARS` tells the view to paint them solid.

const BOSS_TYPE := "nyxareth"
const SKILL := "4"
## The layer normalises by its own 120 ticks although the AI casts "4" for 95.
const DURATION := 120
const STAR_COUNT := 60
const LAYER_ALPHA := 80
const STAR_ALPHA := 230
const COSMIC_DARKEST := [25, 5, 55]
const STAR_MID := [230, 220, 255]
const STAR_BRIGHT := [255, 255, 255]
const OPAQUE_STARS := true
## `surface.get_size()` of the source render surface: the 1280x720 arena.
const SCREEN_SIZE := Vector2i(1280, 720)


static func active(boss_type: String, active_skill: String) -> bool:
	return boss_type == BOSS_TYPE and active_skill == SKILL


## Layer 9bv16: the source asks `surface.get_size()` every frame. On a widened
## window (project.godot uses `stretch/aspect="expand"`) that size is the live
## viewport, not the 1280x720 arena, so the star wrap must follow it. A detached
## node / zero-sized viewport keeps the baked default instead.
static func size_for_viewport(viewport_size: Vector2) -> Vector2i:
	var size := Vector2i(int(viewport_size.x), int(viewport_size.y))
	if size.x <= 0 or size.y <= 0:
		return SCREEN_SIZE
	return size


## `_draw_astro_realm_bg(surface, boss, x, y, timer, phase)`: `timer` is the boss's
## `active_skill_timer` and `phase` its `pulse`.
static func ops(timer: int, phase: float, size: Vector2i = SCREEN_SIZE) -> Array:
	var progress := clampf(1.0 - float(timer) / float(DURATION), 0.0, 1.0)
	var layer_alpha := _alpha(float(LAYER_ALPHA) * minf(1.0, progress * 3.0))
	var out: Array = [
		{
			"kind": "fill",
			"rect": [0, 0, size.x, size.y],
			"color": [COSMIC_DARKEST[0], COSMIC_DARKEST[1], COSMIC_DARKEST[2], layer_alpha],
			"mult": 255,
			"blend": 0,
		}
	]
	var star_fade := minf(1.0, progress * 2.0)
	for i in range(STAR_COUNT):
		# Python's float `%` keeps the divisor's sign, as `fposmod` does.
		var sx := int(fposmod(float(i * 37) + phase * 5.0, float(size.x)))
		var sy := int(fposmod(float(i * 71) + phase * 3.0, float(size.y)))
		var twinkle := sin(phase * 3.0 + float(i)) * 0.5 + 0.5
		var alpha := _alpha(float(STAR_ALPHA) * twinkle * star_fade)
		if i % 5 == 0:
			out.append(_star([sx, sy, 2, 2], STAR_BRIGHT, alpha))
			out.append(_star([sx - 1, sy, 1, 1], STAR_BRIGHT, alpha))
			out.append(_star([sx + 2, sy, 1, 1], STAR_BRIGHT, alpha))
			out.append(_star([sx, sy - 1, 1, 1], STAR_BRIGHT, alpha))
			out.append(_star([sx, sy + 2, 1, 1], STAR_BRIGHT, alpha))
		else:
			out.append(_star([sx, sy, 1, 1], STAR_MID, alpha))
	return out


static func _alpha(value: float) -> int:
	return clampi(int(value), 0, 255)


static func _star(rect: Array, rgb: Array, alpha: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": rect,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
		"mult": 255,
		"width": 0,
		"radius": 0,
	}
