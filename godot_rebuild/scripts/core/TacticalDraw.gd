class_name TacticalDraw
extends RefCounted

## Draw geometry/status text from tactical_commands.py. The native overlay draws
## these primitives; parity tests compare them with the pygame draw spies.


static func command_color(cfg: Dictionary, active: String) -> Array:
	var colors: Dictionary = cfg.get("command_colors", {})
	return colors.get(active if not active.is_empty() else "none", [255, 220, 100])


static func world_data(
	cfg: Dictionary, active: String, gather_point: Variant, timer: int, heroes: Array, ticks_ms: int
) -> Dictionary:
	if gather_point == null or timer <= 0:
		return {}
	var point: Vector2 = gather_point
	var alpha_ratio := clampf(float(timer) / float(cfg.gather_point_duration), 0.0, 1.0)
	var pulse := (
		(
			sin(float(ticks_ms) * float(cfg.draw_pulse_rate)) * float(cfg.draw_pulse_amp)
			+ float(cfg.draw_pulse_base)
		)
		* alpha_ratio
	)
	var col := command_color(cfg, active)
	var circles: Array[Dictionary] = []
	var center := Vector2i(int(point.x), int(point.y))
	for radius in range(int(cfg.draw_ring_start), int(cfg.draw_ring_stop), int(cfg.draw_ring_step)):
		var alpha := int(
			(int(cfg.draw_ring_start) - radius) * int(cfg.draw_ring_alpha_mult) * pulse
		)
		if alpha > 0:
			circles.append(
				{
					"color": [col[0], col[1], col[2], alpha],
					"center": [center.x, center.y],
					"radius": radius,
					"width": 2
				}
			)
	circles.append(
		{
			"color": [col[0], col[1], col[2], 255],
			"center": [center.x, center.y],
			"radius": int(cfg.draw_center_radius),
			"width": 0
		}
	)
	circles.append(
		{
			"color": [255, 255, 255, 255],
			"center": [center.x, center.y],
			"radius": int(cfg.draw_center_dot),
			"width": 0
		}
	)
	var lines: Array[Dictionary] = []
	if active in ["gather", "protect_castle", "attack_boss", "protect_tower"]:
		for hero: BattleUnit in heroes:
			var delta := point - hero.pos
			var dist := delta.length()
			if dist > float(cfg.draw_line_min_dist):
				for seg in range(int(cfg.draw_line_segments)):
					var t1 := seg * float(cfg.draw_line_t_step)
					var t2 := t1 + float(cfg.draw_line_t_len)
					var start := hero.pos + delta * t1
					var finish := hero.pos + delta * t2
					lines.append(
						{
							"color":
							[col[0], col[1], col[2], int(int(cfg.draw_line_alpha) * pulse)],
							"start": [int(start.x), int(start.y)],
							"end": [int(finish.x), int(finish.y)],
							"width": int(cfg.draw_line_width)
						}
					)
	return {"circles": circles, "lines": lines}


static func ui_data(cfg: Dictionary, timer: int) -> Dictionary:
	if timer <= 0:
		return {}
	var alpha := 255
	var y_offset := 0
	if timer < int(cfg.draw_ui_fade_out):
		alpha = int(255.0 * (float(timer) / float(cfg.draw_ui_fade_out)))
	if timer > int(cfg.draw_ui_fade_in_start):
		var prog := clampf(
			(float(cfg.feedback_duration) - float(timer)) / float(cfg.draw_ui_fade_in_frames),
			0.0,
			1.0
		)
		alpha = int(255.0 * prog)
		y_offset = int((1.0 - prog) * int(cfg.draw_ui_y_offset))
	var center: Array = cfg.draw_ui_center
	return {
		"alpha": alpha,
		"y_offset": y_offset,
		"center": [int(center[0]), int(center[1]) + y_offset],
		"inflate": cfg.draw_ui_inflate,
		"bg_alpha": int(int(cfg.draw_ui_bg_alpha) * alpha / 255.0),
		"shadow_alpha": alpha / 2,
		"border_width": int(cfg.draw_ui_border_width),
		"border_radius": int(cfg.draw_ui_border_radius),
		"shadow_offset": int(cfg.draw_ui_shadow_offset),
	}


static func status_text(
	cfg: Dictionary, active: String, target_name: String, command_timer: int, held: String
) -> String:
	var hold_tag := " [HOLD]" if not held.is_empty() else ""
	if not active.is_empty():
		return (
			"%s %s (%ds)%s"
			% [active.to_upper(), target_name, command_timer / int(cfg.status_fps), hold_tag]
		)
	if not held.is_empty():
		return "%s [HOLD] (menunggu syarat)" % held.to_upper()
	return "No tactical command"
