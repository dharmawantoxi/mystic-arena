extends RefCounted
## Layer 9cc: the live overlay half of `minions/base_renderer.py`.
##
## The bodies of the five minions are already native as baked atlases
## (`minion_art.gd`): `bake/bake_minion_atlas.py` drives the real `Minion.draw`
## for every (type, team, nexus level, pose, facing) and packs the cropped
## sprites. What the source draws *around* those sprites is still behaviour:
##
## * `draw_hp_bar` - eight pixels tall, team-tinted background and border, three
##   fill colours on the 0.6 / 0.3 thresholds, skipped while rendering to cache;
## * `draw_slow_effect` - one ice circle of `radius + 2` plus three 2x2 sparks
##   orbiting at `timer * 0.1 + i * 2.1` on `radius + 3`;
## * `draw_slash_effects` - two seven-point arcs (white 3 px, cream 1 px) whose
##   radius grows by `progress * 6` and whose alpha fades from 220;
## * `apply_hurt_flash` - `+90` per channel, clamped, while the hurt timer runs;
## * `_minion_cache_key` - the ten-part key, pose included;
## * `MINION_RENDERERS` / `render_minion` - the five-type registry.
##
## Two helpers of the source are dead (`draw_shadow` with its `_SHADOW_CACHE`,
## and `calculate_animation_offsets`): each namespace carries its own
## `_draw_ground_shadow`, and the bob/sway already live inside the baked frames.
## They are classified in `tests/minions_source_oracle.py`, not ported.
##
## Every function returns plain draw operations so the suite can compare them
## with the ones the Pygame source asks for, pixel for pixel:
## `{"kind": "rect", "rect": [x, y, w, h], "color": [r, g, b, a], "width": n}`
## and the same shape for `circle`, `ellipse` and `lines` (points in
## micro-pixels, `round(x * 10_000)` truncated, so no float formatting drifts).

## `base_renderer.OUTLINE` / `SHADOW`.
const OUTLINE := [24, 20, 25, 255]
const SHADOW := [0, 0, 0, 255]
## `_CANVAS_W` / `_CANVAS_H`.
const CANVAS := Vector2i(120, 120)
const HP_BAR_HEIGHT := 4
const HP_BLUE_BG := [12, 22, 44, 255]
const HP_BLUE_BORDER := [90, 165, 255, 255]
const HP_RED_BG := [44, 12, 10, 255]
const HP_RED_BORDER := [255, 95, 85, 255]
const HP_FILL_HIGH := [70, 200, 80, 255]
const HP_FILL_MID := [225, 190, 60, 255]
const HP_FILL_LOW := [215, 60, 55, 255]
const HP_HIGH_THRESHOLD := 0.6
const HP_LOW_THRESHOLD := 0.3
const SLOW_AURA := [150, 220, 255, 70]
const SLOW_SPARK := [200, 240, 255, 255]
const SLOW_SPARK_SIZE := 2
const SLOW_ORBIT := 3
const SLOW_SPARK_STEP := 2.1
const SLASH_MAX_ALPHA := 220
const SLASH_SPAN := 1.1
const SLASH_STEPS := 7
const SLASH_GROW := 6.0
const SLASH_DEFAULT_DISTANCE := 18.0
const SLASH_DEFAULT_MAX_LIFE := 12
const SLASH_OUTER := [255, 255, 255]
const SLASH_INNER := [255, 230, 180]
## `MINION_RENDERERS` keys.
const TYPES := ["goblin", "orc", "troll", "undead", "dark_rider"]
const POINT_SCALE := 10000

static var _rendering_to_cache := false
static var _cache_enabled := true


## `_RENDERING_TO_CACHE`: the HP bar and the slash arcs are live overlays, so
## they disappear while a body is rendered into the sprite cache.
static func set_rendering_to_cache(value: bool) -> void:
	_rendering_to_cache = value


static func rendering_to_cache() -> bool:
	return _rendering_to_cache


## `MINION_CACHE_ENABLED`.
static func cache_enabled() -> bool:
	return _cache_enabled


static func set_cache_enabled(value: bool) -> void:
	_cache_enabled = value


static func has_type(minion_type: String) -> bool:
	return TYPES.has(minion_type)


## `draw_hp_bar`: background, fill on the source thresholds, then the border.
static func hp_bar_ops(x: int, y: int, width: int, hp_ratio: float, team: String) -> Array:
	if _rendering_to_cache:
		return []
	var ratio := clampf(hp_ratio, 0.0, 1.0)
	var left := x - int(floor(float(width) / 2.0))
	var blue := team == "blue"
	var ops: Array = [_rect([left, y, width, HP_BAR_HEIGHT],
		HP_BLUE_BG if blue else HP_RED_BG, 0)]
	var fill := int(float(width) * ratio)
	if fill > 0:
		var ink: Array = HP_FILL_HIGH
		if ratio <= HP_LOW_THRESHOLD:
			ink = HP_FILL_LOW
		elif ratio <= HP_HIGH_THRESHOLD:
			ink = HP_FILL_MID
		ops.append(_rect([left, y, fill, HP_BAR_HEIGHT], ink, 0))
	ops.append(_rect([left, y, width, HP_BAR_HEIGHT],
		HP_BLUE_BORDER if blue else HP_RED_BORDER, 1))
	return ops


## `draw_slow_effect`: one translucent circle plus three orbiting sparks.
## The source does not guard this with `_RENDERING_TO_CACHE`; the aura ends up
## frozen in the cached sprite instead, which is a documented deviation.
static func slow_aura_ops(x: int, y: int, radius: int, timer: int) -> Array:
	var ops: Array = [{
		"kind": "circle",
		"center": [x, y],
		"radius": radius + 2,
		"color": SLOW_AURA,
		"width": 0,
	}]
	for index in range(SLOW_ORBIT):
		var angle := float(timer) * 0.1 + float(index) * SLOW_SPARK_STEP
		var ix := x + int(cos(angle) * float(radius + 3))
		var iy := y + int(sin(angle) * float(radius + 3))
		ops.append(_rect([ix, iy, SLOW_SPARK_SIZE, SLOW_SPARK_SIZE], SLOW_SPARK, 0))
	return ops


## `draw_slash_effects`: two arcs per live slash, replaced by returned gaps.
static func slash_ops(cx: int, cy: int, effects: Array) -> Array:
	if _rendering_to_cache:
		return []
	var ops: Array = []
	for raw in effects:
		var effect: Dictionary = raw
		var life := int(effect.get("life", 0))
		var max_life := maxi(1, int(effect.get("max_life", SLASH_DEFAULT_MAX_LIFE)))
		if life <= 0:
			continue
		var progress := 1.0 - float(life) / float(max_life)
		var alpha := int(float(SLASH_MAX_ALPHA) * (1.0 - progress))
		if alpha <= 0:
			continue
		var angle := float(effect.get("angle", 0.0))
		var distance := float(effect.get("distance", SLASH_DEFAULT_DISTANCE))
		var size := int(distance * 2.0 + 24.0)
		if size <= 0:
			continue
		var points: Array = []
		for step in range(SLASH_STEPS):
			var sweep := angle - SLASH_SPAN / 2.0 \
				+ SLASH_SPAN * float(step) / float(SLASH_STEPS - 1)
			var reach := distance + progress * SLASH_GROW
			points.append([
				int((float(cx) + cos(sweep) * reach) * float(POINT_SCALE)),
				int((float(cy) + sin(sweep) * reach) * float(POINT_SCALE)),
			])
		ops.append(_lines(points, SLASH_OUTER + [alpha], 3))
		ops.append(_lines(points, SLASH_INNER + [alpha], 1))
	return ops


## `apply_hurt_flash`: brightness lift while `hurt_flash_timer > 0`.
static func hurt_color(color: Array, timer: int) -> Array:
	if timer > 0:
		return [
			mini(int(color[0]) + 90, 255),
			mini(int(color[1]) + 90, 255),
			mini(int(color[2]) + 90, 255),
		]
	return [int(color[0]), int(color[1]), int(color[2])]


## `_minion_cache_key`, with booleans flattened to 1/0 so JSON and GDScript
## compare the same shape.
static func cache_key(state: Dictionary) -> Array:
	var attack := int(state.get("attack_anim_timer", 0))
	var pose: Array = ["idle", 0]
	if attack > 0:
		pose = ["atk", attack >> 1]
	elif bool(state.get("is_moving", false)):
		pose = ["walk", int(float(state.get("walk_cycle", 0.0)) * 2.0) % 8]
	else:
		pose = ["idle", int(float(state.get("anim_time", 0)) * 0.05) % 4]
	var level := int(state.get("nexus_level", 1))
	if level == 0:
		level = 1
	return [
		String(state.get("minion_type", "")),
		String(state.get("team", "")),
		level,
		pose,
		1 if int(state.get("direction", 1)) >= 0 else -1,
		1 if int(state.get("hurt_flash_timer", 0)) > 0 else 0,
		int(state.get("bleed_stacks", 0)),
		1 if bool(state.get("death_charge_active", false)) else 0,
		1 if bool(state.get("regen_active", false)) else 0,
		1 if int(state.get("slow_timer", 0)) > 0 else 0,
	]


## The tail of `cached_minion_draw`: slash arcs first, then the HP bar placed at
## `y - radius - 18` with `radius * 2 + 6` width.
static func overlay_ops(
	x: int, y: int, radius: int, hp_ratio: float, team: String, effects: Array
) -> Array:
	var ops: Array = []
	if not effects.is_empty():
		ops.append_array(slash_ops(x, y, effects))
	ops.append_array(hp_bar_ops(x, y - radius - 18, radius * 2 + 6, hp_ratio, team))
	return ops


static func _rect(rect: Array, color: Array, width: int) -> Dictionary:
	return {"kind": "rect", "rect": rect, "color": color, "width": width}


static func _lines(points: Array, color: Array, width: int) -> Dictionary:
	return {"kind": "lines", "points": points, "color": color, "width": width}
