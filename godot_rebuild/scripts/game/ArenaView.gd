class_name ArenaView
extends Control

## Native immediate-mode arena renderer using baked _entity.py sprite strips.
var game: CoreGame
var font: Font


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	font = RenderCache.font()


func _draw() -> void:
	if game == null or font == null:
		return
	var model := game.model
	var shake := game.effects.shake_offset()
	draw_set_transform(shake)
	game.map_view.draw_static(self)
	if game.map_view.missing_texture:
		_draw_lanes(model)
	_draw_slots(model)
	for tower: BattleUnit in model.towers:
		_draw_unit(tower, true)
	_draw_unit(model.blue_base, true)
	_draw_unit(model.red_base, true)
	model.hero_fx.draw_ground(self)
	for minion: BattleUnit in model.minions:
		_draw_unit(minion, false)
	for hero: BattleUnit in model.heroes + model.enemy_heroes:
		_draw_unit(hero, true)
	if model.active_boss != null and model.active_boss.alive:
		_draw_unit(model.active_boss, true)
	model.hero_fx.draw_trails(self)
	EntityVisuals.draw_projectiles(self, model)
	model.hero_fx.draw(self)
	game.map_view.draw_dynamic(self, model.frame)
	game.effects.draw(self)
	draw_set_transform(Vector2.ZERO)
	_draw_top_bar(model)
	_draw_boss_resistances(model)
	_draw_selection(model)
	_draw_notifications(model)
	if game.dev.show_debug:
		_draw_dev_debug(model)
	if game.dev.panel_open:
		_draw_dev_panel()
	if game.build_popup:
		_draw_build_popup()
	elif game.shop_open:
		_draw_shop()
	elif game.item_shop_open:
		_draw_item_shop()
	if game.result_visible:
		_draw_result()
	game.cinematics.draw(self, model.frame)


func _draw_lanes(model: MatchModel) -> void:
	var river := model.data.lane("river")
	if river.size() > 1:
		draw_polyline(river, Color("1d3a52"), 34.0, true)
	for lane: String in ["top", "mid", "bot"]:
		var path := model.data.lane(lane)
		if path.size() > 1:
			draw_polyline(path, Color("3a3f2e"), 26.0, true)
			draw_polyline(path, Color("6b6f4e"), 18.0, true)


func _draw_slots(model: MatchModel) -> void:
	for slot: Dictionary in model.build_slots_blue:
		if not bool(slot.taken):
			draw_circle(slot.pos, 18.0, Color(0.3, 0.8, 1.0, 0.18))
			draw_arc(slot.pos, 18.0, 0, TAU, 24, Color(0.3, 0.8, 1.0, 0.6), 2.0)
			draw_string(
				font, slot.pos + Vector2(-5, 6), "+", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE
			)


func _draw_unit(unit: BattleUnit, show_bar: bool) -> void:
	if not unit.alive or not FrustumCuller.is_visible(unit.pos, unit.radius):
		return
	var color := unit.color if unit.team == "blue" else unit.color.lerp(Color("ff4444"), 0.35)
	if unit.selected or unit == game.model.selected_tower or unit == game.model.selected_hero:
		draw_arc(unit.pos, unit.radius + 8, 0, TAU, 32, Ui.GOLD, 2.0)
		draw_circle(unit.pos, unit.attack_range, Color(color.r, color.g, color.b, 0.06))
	if unit.kind == BattleUnit.Kind.BOSS:
		BossVisuals.draw_under(self, unit)
		if unit.entrance_timer > 0:
			return
	if not EntityVisuals.draw_unit(self, unit, game.model.frame):
		draw_circle(unit.pos, unit.radius, color)
		draw_arc(unit.pos, unit.radius, 0, TAU, 24, Color(0, 0, 0, 0.5), 2.0)
	if unit.kind == BattleUnit.Kind.BOSS:
		BossVisuals.draw_over(self, unit, font)
		return
	if unit.shield_active and unit.shield > 0:
		draw_arc(unit.pos, unit.radius + 4, 0, TAU, 24, Color(0.4, 0.8, 1.0, 0.8), 2.0)
	if show_bar:
		var width := unit.radius * 2.4
		var rect := Rect2(unit.pos + Vector2(-width / 2, -unit.radius - 14), Vector2(width, 6))
		draw_rect(rect, Color(0, 0, 0, 0.6))
		draw_rect(
			Rect2(rect.position, Vector2(width * clampf(unit.hp / maxf(1, unit.max_hp), 0, 1), 6)),
			Color("58d68d")
		)
		if unit.shield_max > 0 and unit.shield > 0:
			draw_rect(
				Rect2(
					rect.position + Vector2(0, -4),
					Vector2(width * clampf(unit.shield / unit.shield_max, 0, 1), 3)
				),
				Color("66ccff")
			)
		var label := "%s L%d" % [unit.display_name, unit.level]
		draw_string(
			font,
			unit.pos + Vector2(-width / 2, -unit.radius - 18),
			label,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			12,
			Ui.TEXT
		)


func _draw_top_bar(model: MatchModel) -> void:
	draw_rect(Rect2(0, 0, size.x, 54), Color(0.02, 0.03, 0.06, 0.88))
	var text := (
		"LEVEL %02d  •  WAVE %d  •  GOLD %d  •  %s  •  SCORE %d"
		% [
			model.level_number,
			model.wave_number,
			model.gold,
			model.difficulty.to_upper(),
			model.score
		]
	)
	draw_string(font, Vector2(24, 35), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Ui.GOLD)
	var state := "PLAYING" if model.state == "playing" else model.state.to_upper()
	draw_string(font, Vector2(size.x - 220, 35), state, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Ui.TEXT)


func _draw_boss_resistances(model: MatchModel) -> void:
	var boss := model.active_boss
	if boss == null or not boss.alive:
		return
	var rect := Rect2(size.x - 344, 62, 320, 58)
	draw_rect(rect, Color(0.02, 0.03, 0.06, 0.82))
	draw_string(
		font,
		rect.position + Vector2(12, 23),
		"%s · %s" % [boss.display_name, boss.resist_profile.to_upper()],
		HORIZONTAL_ALIGNMENT_LEFT,
		rect.size.x - 24,
		15,
		Ui.GOLD
	)
	draw_string(
		font,
		rect.position + Vector2(12, 45),
		"ARMOR %d · MAGIC RESIST %.1f%%" % [int(boss.armor), boss.magic_resist * 100.0],
		HORIZONTAL_ALIGNMENT_LEFT,
		rect.size.x - 24,
		14,
		Ui.TEXT
	)


func _draw_selection(model: MatchModel) -> void:
	if model.selected_tower != null and model.selected_tower.alive:
		var tower := model.selected_tower
		var info := (
			"%s L%d  HP %d/%d" % [tower.display_name, tower.level, int(tower.hp), int(tower.max_hp)]
		)
		draw_string(font, Vector2(24, 210), info, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Ui.TEXT)
		for name: String in game.button_rects:
			if (
				name.begins_with("tower_path:")
				or name in ["upgrade", "sell", "castle_shield", "regen_shield"]
			):
				_draw_button(name, game.button_rects[name])
	elif model.selected_hero != null and model.selected_hero.alive:
		var hero := model.selected_hero
		var info := (
			"%s L%d  HP %d/%d  DMG %d  ·  %s"
			% [
				hero.display_name,
				hero.level,
				int(hero.hp),
				int(hero.max_hp),
				int(hero.damage),
				game.model.data.archetypes.short_label(hero.unit_type, hero.stats),
			]
		)
		draw_string(font, Vector2(24, 210), info, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Ui.TEXT)
		if game.button_rects.has("upgrade"):
			_draw_button("upgrade", game.button_rects.upgrade)


func _draw_button(name: String, rect: Rect2) -> void:
	draw_rect(rect, Color("1d2733"))
	draw_rect(rect, Ui.GOLD, false, 1.5)
	var label := name
	if name.begins_with("buy_hero:"):
		var hero_type := name.get_slice(":", 1)
		var stats := game.model.data.hero(hero_type)
		label = "%s\n%dG" % [stats.get("name", hero_type), int(stats.get("cost", 0))]
	elif name.begins_with("build:"):
		label = name.get_slice(":", 1).capitalize() + "\n100G"
	elif name.begins_with("buy_item:"):
		var item := game.model.data.item(name.get_slice(":", 1))
		label = "%s\n%dG" % [item.get("name", "?"), int(item.get("cost", 0))]
	elif name.begins_with("tower_path:"):
		label = name.get_slice(":", 1).capitalize()
	else:
		label = (
			{
				"upgrade": "UPGRADE",
				"sell": "SELL",
				"close": "CLOSE",
				"item_page": "NEXT PAGE",
				"castle_shield": "CASTLE SHIELD",
				"regen_shield": "REGEN SHIELD",
				"next": "NEXT LEVEL",
				"replay": "REPLAY",
				"menu": "MENU"
			}
			. get(name, name.to_upper())
		)
	var lines := label.split("\n")
	for index in range(lines.size()):
		draw_string(
			font,
			rect.position + Vector2(10, 24 + index * 20),
			lines[index],
			HORIZONTAL_ALIGNMENT_LEFT,
			rect.size.x - 20,
			16,
			Ui.TEXT
		)


func _draw_notifications(model: MatchModel) -> void:
	var y := 80.0
	for note: String in model.notifications:
		draw_string(font, Vector2(24, y), note, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Ui.GOLD)
		y += 24


func _draw_build_popup() -> void:
	draw_rect(Rect2(380, 260, 520, 210), Color(0.04, 0.06, 0.1, 0.95))
	draw_string(font, Vector2(400, 300), "BUILD TOWER", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Ui.GOLD)
	for name: String in game.button_rects:
		_draw_button(name, game.button_rects[name])


func _draw_shop() -> void:
	draw_rect(Rect2(210, 130, 860, 500), Color(0.04, 0.06, 0.1, 0.96))
	draw_string(
		font,
		Vector2(240, 175),
		"HERO SHOP — owned heroes",
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		26,
		Ui.GOLD
	)
	for name: String in game.button_rects:
		_draw_button(name, game.button_rects[name])


func _draw_item_shop() -> void:
	draw_rect(Rect2(200, 120, 880, 460), Color(0.04, 0.06, 0.1, 0.96))
	var meta: Dictionary = game.model.data.items.page_meta(game.item_page)
	var title := (
		"ITEM FORGE — %s %d/%d"
		% [
			str(meta.get("class", "")).to_upper(),
			int(meta.get("page", 1)),
			int(meta.get("pages", 1))
		]
	)
	draw_string(font, Vector2(230, 165), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 26, Ui.GOLD)
	var target := game.model.selected_hero
	var target_name: String = (
		str(target.stats.get("name", target.unit_type)) if target != null else "first hero"
	)
	draw_string(
		font,
		Vector2(230, 190),
		"BUY FOR: %s" % target_name,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		16,
		Ui.MUTED
	)
	for name: String in game.button_rects:
		_draw_button(name, game.button_rects[name])


func _draw_result() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.72))
	var title := "VICTORY" if game.result_victory else "DEFEAT"
	draw_string(
		font,
		Vector2(440, 260),
		title,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		64,
		Ui.GOLD if game.result_victory else Color("ff6666")
	)
	var summary := game.reward_summary
	var line := "Reward: %d gold" % int(summary.get("reward", 0))
	if not summary.get("new_heroes", []).is_empty():
		line += "  •  New heroes: %s" % ", ".join(summary.new_heroes)
	draw_string(font, Vector2(380, 330), line, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Ui.TEXT)
	var stats := game.model.match_stats()
	draw_string(
		font,
		Vector2(380, 370),
		(
			"Score %d  •  Kills %d  •  Time %ds  •  Combo %d"
			% [stats.score, stats.kills, stats.time_seconds, stats.combo]
		),
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		20,
		Ui.MUTED
	)
	for name: String in game.button_rects:
		_draw_button(name, game.button_rects[name])


func _draw_dev_debug(model: MatchModel) -> void:
	var lines := game.dev.debug_lines(model)
	var rect := Rect2(10, size.y - 24 - lines.size() * 18, 320, lines.size() * 18 + 16)
	draw_rect(rect, Color(0, 0, 0, 0.75))
	var y := rect.position.y + 20
	for line: String in lines:
		draw_string(
			font,
			Vector2(rect.position.x + 8, y),
			line,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			14,
			Color("aaffaa")
		)
		y += 18


func _draw_dev_panel() -> void:
	var rect := Rect2(size.x - 340, 90, 320, 420)
	draw_rect(rect, Color(0.05, 0.08, 0.12, 0.95))
	draw_rect(rect, Color("00ff66"), false, 2.0)
	var lines := [
		"DEV PANEL",
		"F1 toggle dev  •  F2 panel  •  F3 debug",
		"F5 +500  F6 +2000  F7 +10000",
		"F8 AI +2000  F9 skip wave",
		"F10 max towers  F11 max castle",
		"F12 max heroes",
		"K kill enemies  G god mode",
		"V victory  L defeat",
	]
	var y := rect.position.y + 34
	for line: String in lines:
		draw_string(
			font,
			Vector2(rect.position.x + 14, y),
			line,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			16,
			Color("ccffcc")
		)
		y += 28
