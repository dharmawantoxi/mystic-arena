# gdlint:disable=unused-argument
extends RefCounted
## Layer 9bq6: the rest of urgharun's FX - LAYER 1 plus the Q/W/E skill FX.
##
## `bosses/level40.py::_NS_urgharun.draw_urgharun` paints, in this order:
##   LAYER 1  `_draw_fury_aura(surface, x, y, pulse, enraged=active_skill == "r")` then
##            `_draw_ground_ring(surface, x, y + 50, pulse, active_skill)`,
##   LAYER 2  skill ground FX (Q `_draw_earthshock_ground`, R `_draw_enrage_ground`),
##   LAYER 3  the body pose,
##   LAYER 4  skill foreground FX (Q `_draw_earthshock_fx`, W `_draw_overpower_fx`,
##            E `_draw_furyswipes_fx`, R `_draw_enrage_fx`).
## 9bq4 pinned the R foreground and 9bq5 the R ground FX; this layout owns LAYER 1 and the
## Q/W/E skill FX. Everything is anchored on the int `(x, y)` `Boss.draw` passes in.
##
## Both aura surfaces are drawn off-screen and blitted, so the recorded ops are already in
## screen space: the 220x180 fury aura is blitted at `(x - 110, y - 90)` around its
## `(110, 90)` centre, and the 170x54 ground ring at `(x - 85, y - 27)` around `(85, 30)`.
##
## Quirks kept: the aura embers, the ground-ring runes and W/E's bright tips use raw palette
## tuples, so their alpha stays 255 while the layered shapes fade; the Q ground FX draws
## nothing on its first tick (`progress == 0`), and E draws nothing once `slash_t > 1.2`.

const BOSS_TYPE := "urgharun"
const SKILL_Q := "q"
const SKILL_W := "w"
const SKILL_E := "e"
const SKILL_R := "r"
## The source normalises each skill by its own cast window.
const Q_DURATION := 55
const W_DURATION := 50
const E_DURATION := 40
const AURA_ORIGIN := [110, 90]
const RING_ORIGIN := [85, 30]
## The 170x54 ring surface is blitted at `(x - 85, y - 27)`.
const RING_BLIT := [85, 27]
## Ground ring anchor offset from `draw_urgharun`: `_draw_ground_ring(surface, x, y + 50, ...)`.
const RING_Y_OFFSET := 50
const FURY_DARKEST := [35, 3, 3]
const FURY_DARK := [130, 15, 15]
const FURY_MID := [230, 40, 40]
const FURY_LIGHT := [255, 110, 90]
const FURY_HOT := [255, 180, 140]
const FURY_SHINE := [255, 230, 200]
const FUR_DARKEST := [8, 8, 12]
const FUR_MID := [55, 55, 65]
const SHADOW_DEEP := [2, 1, 1]


static func active(boss_type: String) -> bool:
	return boss_type == BOSS_TYPE


## LAYER 1: `_draw_fury_aura` + `_draw_ground_ring`. `enraged` is `active_skill == "r"`
## and `skill_active` is `active_skill != ""` (the source passes the raw string).
static func layer_one_ops(x: int, y: int, phase: float, enraged: bool, skill_active: bool) -> Array:
	var out: Array = aura_ops(x, y, phase, enraged)
	out.append_array(ground_ring_ops(x, y + RING_Y_OFFSET, phase, skill_active))
	return out


static func aura_ops(x: int, y: int, phase: float, enraged: bool) -> Array:
	var pulse := sin(phase * 0.5) * 0.25 + 0.75
	var strength := 1.6 if enraged else 1.0
	var out: Array = []
	# `_aacircle(aura, fury_darkest, (110, 90), radius)` blitted at `(x - 110, y - 90)`.
	for radius in range(90, 5, -5):
		var alpha := _alpha((90.0 - float(radius)) * 1.2 * pulse * strength)
		if alpha > 0:
			out.append(_circle([x, y], radius, FURY_DARKEST, alpha, 0))
	for radius in range(50, 5, -3):
		var alpha := _alpha((50.0 - float(radius)) * 1.4 * pulse * strength)
		if alpha > 0:
			out.append(_circle([x, y], radius, FURY_DARK, alpha, 0))
	# Rage embers on the screen surface, so their raw palette alpha stays 255.
	var num_embers := 16 if enraged else 12
	var half := float(num_embers) / 2.0
	for index in range(num_embers):
		var angle := phase * 0.3 + float(index) * PI / half
		var radius := 40 + int(sin(phase + float(index)) * 12.0)
		var sx := x + int(cos(angle) * float(radius))
		var sy := y + int(sin(angle) * float(radius) * 0.4)
		out.append(_rect([sx, sy, 2, 2], FURY_MID, 255))
		out.append(_rect([sx, sy, 1, 1], FURY_HOT, 255))
	return out


static func ground_ring_ops(x: int, y: int, phase: float, skill_active: bool) -> Array:
	var pulse := sin(phase * 1.2) * 0.25 + 0.75
	var left: int = x - RING_BLIT[0]
	var top: int = y - RING_BLIT[1]
	var out: Array = [
		_ellipse([left + 5, top + 18, 160, 26], FURY_DARKEST, 200, 3),
		_ellipse([left + 14, top + 20, 142, 22], FUR_DARKEST, 220, 2),
		_ellipse([left + 25, top + 22, 120, 18], FURY_DARK, 220, 1),
	]
	var center_y: int = top + RING_ORIGIN[1]
	for index in range(10):
		var angle := phase * 0.3 + float(index) * PI / 5.0
		var x1: int = left + RING_ORIGIN[0] + int(cos(angle) * 46.0)
		var y1: int = center_y + int(sin(angle) * 8.0)
		var x2: int = left + RING_ORIGIN[0] + int(cos(angle) * 72.0)
		var y2: int = center_y + int(sin(angle) * 12.0)
		out.append(_line([x1, y1], [x2, y2], FURY_MID, 220, 1))
	if skill_active:
		out.append(_ellipse([left + 15, top + 12, 140, 38], FURY_HOT, _alpha(150.0 * pulse), 1))
	return out


## LAYER 2 (Q): `_draw_earthshock_ground`. The rings only appear once `r > 5`.
static func earthshock_ground_ops(x: int, y: int, timer: int, phase: float) -> Array:
	var progress := clampf(1.0 - float(timer) / float(Q_DURATION), 0.0, 1.0)
	var out: Array = []
	for index in range(3):
		var ring_t := maxf(0.0, progress - float(index) * 0.15)
		var radius := int(ring_t * 90.0)
		if radius <= 5:
			continue
		var alpha := _alpha(220.0 * (1.0 - ring_t))
		var top := y + 40 - floori(float(radius) / 3.0)
		var height := floori(float(radius * 2) / 3.0)
		out.append(_ellipse([x - radius, top, radius * 2, height], FURY_DARK, alpha, 3))
		out.append(
			_ellipse([x - radius + 3, top + 2, radius * 2 - 6, height - 4], FURY_MID, alpha, 2)
		)
		out.append(
			_ellipse([x - radius + 6, top + 4, radius * 2 - 12, height - 8], FURY_LIGHT, alpha, 1)
		)
	return out


## LAYER 4 (Q): `_draw_earthshock_fx` - eight rock chunks, their fire glow, then the cracks
## that only exist while `progress < 0.5`.
static func earthshock_fx_ops(x: int, y: int, timer: int, phase: float) -> Array:
	var progress := clampf(1.0 - float(timer) / float(Q_DURATION), 0.0, 1.0)
	var debris := [
		[-55, 42], [-45, 45], [-38, 40], [55, 42], [45, 45], [38, 40], [-30, 48], [30, 48]
	]
	var out: Array = []
	for index in range(debris.size()):
		var dx: int = debris[index][0]
		var dy: int = debris[index][1]
		var delay := float(index) * 0.05
		var local_t := clampf((progress - delay) / (1.0 - delay), 0.0, 1.0)
		if local_t <= 0.0:
			continue
		var height := 0
		if local_t < 0.4:
			height = int((local_t / 0.4) * 22.0)
		else:
			height = int(22.0 * (1.0 - (local_t - 0.4) / 0.6))
		var cx := x + dx
		var cy := y + dy - height
		(
			out
			. append(
				_polygon(
					[
						[cx - 3, cy + 3],
						[cx + 4, cy + 3],
						[cx + 4, cy - 2],
						[cx - 3, cy - 2],
					],
					SHADOW_DEEP
				)
			)
		)
		(
			out
			. append(
				_polygon(
					[
						[cx - 3, cy + 2],
						[cx + 4, cy + 2],
						[cx + 4, cy - 3],
						[cx - 3, cy - 3],
					],
					FUR_DARKEST
				)
			)
		)
		(
			out
			. append(
				_polygon(
					[
						[cx - 2, cy + 1],
						[cx + 3, cy + 1],
						[cx + 3, cy - 2],
						[cx - 2, cy - 2],
					],
					FUR_MID
				)
			)
		)
		if local_t < 0.5:
			var alpha := _alpha(200.0 * (1.0 - local_t * 2.0))
			out.append(_rect([cx, y + dy, 2, 2], FURY_HOT, alpha))
			out.append(_rect([cx, y + dy, 1, 1], FURY_SHINE, alpha))
	if progress < 0.5:
		var crack_len := int(progress * 60.0)
		var alpha := _alpha(200.0 * (1.0 - progress))
		for index in range(8):
			var crack_angle := float(index) * PI / 4.0
			var step := 3
			while step < crack_len:
				var px := x + int(cos(crack_angle) * float(step))
				var py := y + 42 + int(sin(crack_angle) * float(step) * 0.4)
				out.append(_rect([px, py, 2, 2], FURY_HOT, alpha))
				out.append(_rect([px, py, 1, 1], FURY_SHINE, alpha))
				step += 3
	return out


## LAYER 4 (W): `_draw_overpower_fx`. The four "stun stars" over the target only appear while
## `progress > 0.5` and only when the source has a live `boss.target`.
static func overpower_ops(
	x: int, y: int, facing: int, timer: int, phase: float, target: Array
) -> Array:
	var progress := clampf(1.0 - float(timer) / float(W_DURATION), 0.0, 1.0)
	var out: Array = []
	var arms := [[-1, -8], [1, 10]]
	for side_index in range(2):
		var claw_cx := x + int(arms[side_index][1]) * facing
		var claw_cy := y + 8
		for trail_index in range(4):
			var trail_t := fposmod(
				phase * 3.0 + float(trail_index) * PI / 2.0 + float(side_index) * PI / 3.0, PI * 2.0
			)
			var start_a := trail_t
			var end_a := trail_t + PI / 2.0
			var previous: Array = []
			for step in range(7):
				var step_t := float(step) / 6.0
				var angle := start_a + (end_a - start_a) * step_t
				var px := claw_cx + int(cos(angle) * 12.0)
				var py := claw_cy + int(sin(angle) * 12.0)
				if step > 0:
					var alpha := _alpha(200.0 * step_t)
					out.append(_line(previous, [px, py], FURY_DARK, alpha, 2))
					out.append(_line(previous, [px, py], FURY_LIGHT, alpha, 1))
				previous = [px, py]
			var tip_x := claw_cx + int(cos(end_a) * 12.0)
			var tip_y := claw_cy + int(sin(end_a) * 12.0)
			out.append(_rect([tip_x, tip_y, 1, 1], FURY_SHINE, 255))
	for index in range(12):
		var angle := phase * 2.0 + float(index) * PI / 6.0
		var radius := 30 + int(sin(phase * 3.0 + float(index)) * 5.0)
		var sx := x + int(cos(angle) * float(radius))
		var sy := y + int(sin(angle) * float(radius) * 0.5)
		out.append(_rect([sx, sy, 2, 2], FURY_MID, 255))
		out.append(_rect([sx, sy, 1, 1], FURY_HOT, 255))
	if progress > 0.5 and target.size() >= 2:
		var tx: int = int(target[0])
		var ty: int = int(target[1]) - 20
		for index in range(4):
			var star_angle := phase * 3.0 + float(index) * PI / 2.0
			var sx := tx + int(cos(star_angle) * 15.0)
			var sy := ty + int(sin(star_angle) * 15.0 * 0.4)
			out.append(_line([sx - 2, sy], [sx + 2, sy], FURY_HOT, 255, 1))
			out.append(_line([sx, sy - 2], [sx, sy + 2], FURY_HOT, 255, 1))
			out.append(_rect([sx, sy, 1, 1], FURY_SHINE, 255))
	return out


## LAYER 4 (E): `_draw_furyswipes_fx`. `target` is `[x, y]`, or empty for the source fallback
## `(x + facing * 80, y)`; a target further than 100 px is pulled back to 80 px.
static func furyswipes_ops(
	x: int, y: int, facing: int, timer: int, phase: float, target: Array
) -> Array:
	var progress := clampf(1.0 - float(timer) / float(E_DURATION), 0.0, 1.0)
	var tx := x + facing * 80
	var ty := y
	if target.size() >= 2:
		tx = int(target[0])
		ty = int(target[1])
	var dx := tx - x
	var dy := ty - y
	var distance := sqrt(float(dx * dx + dy * dy))
	if distance > 100.0:
		tx = x + int(float(dx) / distance * 80.0)
		ty = y + int(float(dy) / distance * 80.0)
	var out: Array = []
	for slash_index in range(5):
		var slash_delay := float(slash_index) * 0.15
		var slash_t := maxf(0.0, (progress - slash_delay) / maxf(0.001, 0.3))
		if slash_t <= 0.0 or slash_t > 1.2:
			continue
		var fade := minf(1.0, slash_t * 2.0) * maxf(0.0, 1.0 - (slash_t - 0.5) * 2.0)
		var alpha := _alpha(240.0 * fade)
		var offset_angle := float(slash_index) * PI / 3.0 + progress * 2.0
		var offset_x := int(cos(offset_angle) * 10.0)
		var offset_y := int(sin(offset_angle) * 8.0)
		var slash_cx := tx + offset_x
		var slash_cy := ty + offset_y
		var slash_dir_x := float(facing)
		var slash_dir_y := -1.0 + float(slash_index) * 0.4
		for line_offset in [-4, 0, 4]:
			var perp_x := -slash_dir_y
			var perp_y := slash_dir_x
			var start_x := (
				slash_cx - int(slash_dir_x * 20.0 / 2.0) + int(perp_x * float(line_offset))
			)
			var start_y := (
				slash_cy - int(slash_dir_y * 20.0 / 2.0) + int(perp_y * float(line_offset))
			)
			var end_x := slash_cx + int(slash_dir_x * 20.0 / 2.0) + int(perp_x * float(line_offset))
			var end_y := slash_cy + int(slash_dir_y * 20.0 / 2.0) + int(perp_y * float(line_offset))
			out.append(_line([start_x, start_y], [end_x, end_y], FURY_DARKEST, alpha, 3))
			out.append(_line([start_x, start_y], [end_x, end_y], FURY_DARK, alpha, 2))
			out.append(_line([start_x, start_y], [end_x, end_y], FURY_MID, alpha, 1))
			out.append(_line([start_x + 2, start_y], [end_x - 2, end_y], FURY_LIGHT, alpha, 1))
		out.append(_rect([slash_cx + facing * 8, slash_cy, 2, 2], FURY_SHINE, alpha))
	return out


static func _alpha(value: float) -> int:
	return clampi(int(value), 0, 255)


static func _circle(center: Array, radius: int, rgb: Array, alpha: int, width: int) -> Dictionary:
	return {
		"kind": "circle",
		"center": center,
		"radius": radius,
		"width": width,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
	}


static func _ellipse(rect: Array, rgb: Array, alpha: int, width: int) -> Dictionary:
	return {
		"kind": "ellipse",
		"rect": rect,
		"width": width,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
	}


static func _rect(rect: Array, rgb: Array, alpha: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": rect,
		"width": 0,
		"radius": 0,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
	}


static func _line(a: Array, b: Array, rgb: Array, alpha: int, width: int) -> Dictionary:
	return {
		"kind": "line",
		"a": a,
		"b": b,
		"width": width,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
	}


static func _polygon(points: Array, rgb: Array) -> Dictionary:
	return {
		"kind": "polygon",
		"points": points,
		"width": 0,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], 255],
	}
