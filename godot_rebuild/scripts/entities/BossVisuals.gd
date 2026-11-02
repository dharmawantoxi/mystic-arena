class_name BossVisuals
extends RefCounted

## Native Boss.draw overlay: aura layers, entrance ring/text, and the name/HP
## plate anchored by BOSS_LABEL_TOP. Body pixels come from baked sprite strips.


static func aura_phase(sin_value: float) -> int:
	return int((sin_value + 1.0) * 0.5 * 11.0 + 0.5)


static func draw_under(canvas: CanvasItem, boss: BattleUnit) -> void:
	if not boss.alive:
		return
	var pos := Vector2(int(boss.pos.x), int(boss.pos.y))
	var is_true := boss.boss_class == "true"
	if boss.entrance_timer > 0:
		draw_entrance(canvas, boss, pos)
		return
	if boss.ability_active:
		var pulse := sin(boss.anim_time * 0.2) * 0.3 + 0.7
		var radius := int(boss.ability_range * pulse)
		var color := _color(boss.stats.get("entrance_color", [170, 80, 210]))
		for ar in range(radius, radius - 20, -3):
			var alpha := clampi(int((radius - ar) * 8 * pulse), 0, 255)
			if alpha > 0 and ar > 0:
				canvas.draw_circle(pos, ar, Color(color.r, color.g, color.b, alpha / 255.0))
	if boss.is_enraged:
		var pulse := sin(boss.enrage_pulse) * 0.3 + 0.7
		var radius := int(boss.radius) + int(14 * pulse)
		var color := Color("ff3228") if is_true else Color("ff8c1e")
		for off in range(radius, maxi(5, radius - 18), -3):
			var alpha := clampi(int((radius - off) * 12 * pulse), 0, 200)
			if alpha > 0:
				canvas.draw_arc(
					pos, off, 0, TAU, 48, Color(color.r, color.g, color.b, alpha / 255.0), 2.0
				)
	if is_true:
		var pulse := sin(boss.pulse) * 0.3 + 0.7
		var radius := int(boss.radius) + 15
		for off in range(radius, radius - 15, -2):
			var alpha := clampi(int((radius - off) * 5 * pulse), 0, 255)
			if alpha > 0 and off > 0:
				canvas.draw_circle(
					pos, off, Color(boss.color.r, boss.color.g, boss.color.b, alpha / 255.0)
				)
	var shadow_w := int(boss.radius) * 2 + (10 if is_true else 0)
	var shadow := PackedVector2Array()
	for i in range(24):
		var angle := TAU * i / 24.0
		shadow.append(
			pos + Vector2(cos(angle) * shadow_w / 2.0, boss.radius - 5 + 6 + sin(angle) * 6.0)
		)
	canvas.draw_colored_polygon(shadow, Color(0, 0, 0, 120.0 / 255.0))


static func draw_entrance(canvas: CanvasItem, boss: BattleUnit, pos: Vector2) -> void:
	var is_true := boss.boss_class == "true"
	var max_timer := 180 if is_true else 120
	var progress := 1.0 - float(boss.entrance_timer) / max_timer
	var size := int(boss.radius * progress * 2)
	var color := _color(boss.stats.get("entrance_color", [170, 80, 210]))
	if size > 0:
		var alpha := clampi(int(200 * (1 - progress)), 0, 255)
		canvas.draw_circle(pos, size, Color(color.r, color.g, color.b, alpha / 255.0))
	if boss.entrance_timer > max_timer / 2:
		var pulse := sin(boss.anim_time * 0.2) * 0.3 + 0.7
		var alpha := clampi(int(255 * pulse), 0, 255) / 255.0
		var text := str(boss.stats.get("entrance_text", boss.display_name))
		RenderCache.centered(
			canvas,
			Vector2(640, 84),
			text,
			28 if is_true else 24,
			Color(color.r, color.g, color.b, alpha),
			"body_semibold"
		)


static func draw_over(canvas: CanvasItem, boss: BattleUnit, font: Font) -> void:
	if not boss.alive or boss.entrance_timer > 0:
		return
	var is_true := boss.boss_class == "true"
	var pos := Vector2(int(boss.pos.x), int(boss.pos.y))
	var head_top := boss.radius
	if boss.world != null:
		head_top = boss.world.data.bosses.label_top(boss.unit_type, boss.radius)
	var bar_w := 70 if is_true else 60
	var bar_h := 10 if is_true else 8
	var bar := Rect2(pos.x - bar_w / 2, pos.y - head_top - 6 - bar_h, bar_w, bar_h)
	canvas.draw_rect(bar, Color("280000"))
	var ratio := clampf(boss.hp / maxf(1.0, boss.max_hp), 0.0, 1.0)
	var fill := int(bar_w * ratio)
	if fill > 0:
		var hp_color := (
			Color("64dc64")
			if ratio > 0.5
			else (Color("f0dc3c") if ratio > 0.25 else Color("f03c3c"))
		)
		canvas.draw_rect(Rect2(bar.position, Vector2(fill, bar_h)), hp_color)
	var border := (
		Color("ff3c3c") if boss.is_enraged else (Color("ff6464") if is_true else Color("ffc832"))
	)
	canvas.draw_rect(bar, border, false, 1.0)
	var prefix := "TRUE BOSS" if is_true else "BOSS"
	var tag := (" [ENRAGED]" if is_true else " [FRENZY]") if boss.is_enraged else ""
	var label := "%s: %s%s" % [prefix, boss.display_name, tag]
	var size := 20 if is_true else 18
	var width := font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var rect := Rect2(pos.x - width / 2 - 4, bar.position.y - 5 - size - 2, width + 8, size + 4)
	rect.position.x = clampf(rect.position.x, 2.0, 1278.0 - rect.size.x)
	canvas.draw_rect(rect, Color(0, 0, 0, 0.85))
	canvas.draw_rect(rect, border, false, 1.0)
	canvas.draw_string(
		font,
		Vector2(rect.position.x + 4, rect.position.y + size - 2),
		label,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		size,
		border
	)


static func _color(value: Variant) -> Color:
	if value is Array and value.size() >= 3:
		return Color(float(value[0]) / 255.0, float(value[1]) / 255.0, float(value[2]) / 255.0)
	return Color.PURPLE
