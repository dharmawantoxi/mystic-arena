class_name RenderCinematics
extends RefCounted

## Native _render.LevelIntroScreen / BossIntroCinematic / BossDeathAnimation.
## Level intro and boss intro pause the fixed-step simulation until skipped or
## finished; boss death is a non-blocking overlay. Timings match _render.py.
const BOSS_INTRO_DURATION := 100
const BOSS_DEATH_TRUE := 90
const BOSS_DEATH_MINI := 60
const CELEBRATION_DURATION := 120
const LEVEL_FADE_IN := 30
var level_intro: Dictionary = {}
var boss_intro: Dictionary = {}
var boss_death: Dictionary = {}
var preview: BattleUnit


func start_level_intro(config: Dictionary, data: CoreData, difficulty: String) -> void:
	var boss_type := str(config.get("true_boss", "abaddon"))
	var boss := data.boss(boss_type)
	level_intro = {
		"active": true,
		"timer": 0,
		"level": int(config.get("level_number", 1)),
		"name": str(config.get("name", "Level")),
		"description": str(config.get("description", "")),
		"reward": int(config.get("meta_gold_reward_win", 500)),
		"difficulty": difficulty,
		"boss_type": boss_type,
		"boss_name": str(boss.get("name", boss_type.capitalize())),
		"boss_title": str(boss.get("title", "The Boss")),
		"boss_color":
		MapView.color_of(boss.get("entrance_color", boss.get("color", [150, 100, 200]))),
	}
	preview = BattleUnit.new()
	preview.setup_boss(data, boss_type, data.lane("mid"))
	preview.pos = Vector2(960, 330)


func start_boss_intro(unit: BattleUnit, data: CoreData) -> void:
	boss_intro = {
		"active": true,
		"timer": BOSS_INTRO_DURATION,
		"name": unit.display_name,
		"title": str(unit.stats.get("title", "")),
		"color": unit.color,
		"hp": unit.max_hp,
		"boss_class": str(unit.stats.get("boss_class", "mini")),
	}
	preview = BattleUnit.new()
	preview.setup_boss(data, unit.unit_type, data.lane("mid"))
	preview.pos = Vector2(430, 360)


func start_boss_death(unit: BattleUnit) -> void:
	var is_true := str(unit.stats.get("boss_class", "mini")) == "true"
	boss_death = {
		"active": true,
		"timer": BOSS_DEATH_TRUE if is_true else BOSS_DEATH_MINI,
		"duration": BOSS_DEATH_TRUE if is_true else BOSS_DEATH_MINI,
		"pos": unit.pos,
		"name": unit.display_name,
		"color": unit.color,
		"gold": unit.gold_reward,
		"celebration": CELEBRATION_DURATION if is_true else 0,
		"celebration_timer": 0,
		"is_true": is_true,
	}


func blocking() -> bool:
	return bool(level_intro.get("active", false)) or bool(boss_intro.get("active", false))


func any_active() -> bool:
	return blocking() or bool(boss_death.get("active", false))


func skip() -> void:
	if not level_intro.is_empty():
		level_intro.active = false
	if not boss_intro.is_empty():
		boss_intro.active = false
	if not boss_death.is_empty():
		boss_death.active = false
		boss_death.celebration_timer = 0


func update() -> void:
	if bool(level_intro.get("active", false)):
		level_intro.timer = int(level_intro.timer) + 1
	if bool(boss_intro.get("active", false)):
		boss_intro.timer = int(boss_intro.timer) - 1
		if int(boss_intro.timer) <= 0:
			boss_intro.active = false
	if bool(boss_death.get("active", false)):
		boss_death.timer = int(boss_death.timer) - 1
		if int(boss_death.timer) <= 0:
			boss_death.active = false
			boss_death.celebration_timer = int(boss_death.celebration)
	elif int(boss_death.get("celebration_timer", 0)) > 0:
		boss_death.celebration_timer = int(boss_death.celebration_timer) - 1


func draw(canvas: CanvasItem, frame: int) -> void:
	_draw_boss_death(canvas, frame)
	_draw_boss_intro(canvas, frame)
	_draw_level_intro(canvas, frame)


func _draw_level_intro(canvas: CanvasItem, frame: int) -> void:
	if not bool(level_intro.get("active", false)):
		return
	var alpha := clampf(float(level_intro.timer) / float(LEVEL_FADE_IN), 0.0, 1.0)
	canvas.draw_rect(Rect2(0, 0, 1280, 720), Color(0.01, 0.01, 0.03, 0.94 * alpha))
	var tint: Color = level_intro.boss_color
	canvas.draw_rect(
		Rect2(0, 0, 1280, 720), Color(tint.r * 0.1, tint.g * 0.1, tint.b * 0.1, 0.25 * alpha)
	)
	canvas.draw_line(Vector2(640, 100), Vector2(640, 620), Color(0.39, 0.39, 0.51, alpha), 2.0)
	for index in range(3):
		var y := 250.0 + index * 200.0
		canvas.draw_colored_polygon(
			PackedVector2Array(
				[Vector2(640, y - 8), Vector2(648, y), Vector2(640, y + 8), Vector2(632, y)]
			),
			Color(1, 0.86, 0.39, alpha)
		)
	var left := Vector2(320, 130)
	RenderCache.centered(canvas, left, "LEVEL", 32, Color(0.71, 0.78, 0.86, alpha), "body_semibold")
	RenderCache.centered(
		canvas,
		left + Vector2(0, 110),
		str(level_intro.level),
		160,
		Color(1, 0.86, 0.39, alpha),
		"title"
	)
	canvas.draw_line(
		left + Vector2(-150, 220), left + Vector2(150, 220), Color(1, 0.86, 0.39, alpha), 2.0
	)
	RenderCache.centered(
		canvas,
		left + Vector2(0, 265),
		str(level_intro.name),
		40,
		Color(0.94, 0.94, 0.98, alpha),
		"title"
	)
	RenderCache.centered(
		canvas,
		left + Vector2(0, 310),
		str(level_intro.description),
		20,
		Color(0.71, 0.78, 0.86, alpha)
	)
	var difficulty := str(level_intro.difficulty).to_upper()
	var diff_color := Color(0.39, 0.86, 0.59)
	if difficulty == "HARD":
		diff_color = Color(1, 0.47, 0.39)
	elif difficulty == "EASY":
		diff_color = Color(0.39, 0.82, 1)
	RenderCache.centered(
		canvas,
		left + Vector2(0, 370),
		"DIFFICULTY: %s" % difficulty,
		20,
		Color(diff_color.r, diff_color.g, diff_color.b, alpha)
	)
	RenderCache.centered(
		canvas, left + Vector2(0, 430), "VICTORY REWARD", 20, Color(0.59, 0.67, 0.75, alpha)
	)
	RenderCache.centered(
		canvas,
		left + Vector2(0, 465),
		"+%d GOLD" % int(level_intro.reward),
		28,
		Color(1, 0.86, 0.39, alpha),
		"body_bold"
	)
	var right := Vector2(960, 130)
	RenderCache.centered(
		canvas, right, "BOSS PREVIEW", 28, Color(0.71, 0.78, 0.86, alpha), "body_semibold"
	)
	if preview != null:
		EntityVisuals.draw_unit(canvas, preview, frame)
	RenderCache.centered(
		canvas,
		right + Vector2(0, 220),
		str(level_intro.boss_name),
		44,
		Color(tint.r, tint.g, tint.b, alpha),
		"title"
	)
	RenderCache.centered(
		canvas,
		right + Vector2(0, 265),
		'"%s"' % str(level_intro.boss_title),
		26,
		Color(0.78, 0.78, 0.86, alpha)
	)
	var pulse := sin(frame * 0.005) * 0.3 + 0.7
	RenderCache.centered(
		canvas,
		right + Vector2(0, 315),
		"PREPARE FOR BATTLE",
		22,
		Color(1, 0.43, 0.39, alpha * pulse),
		"body_medium"
	)
	if int(level_intro.timer) > LEVEL_FADE_IN:
		var prompt_pulse := sin(frame * 0.005) * 0.3 + 0.7
		var rect := Rect2(440, 637, 400, 45)
		canvas.draw_rect(rect, Color(0, 0, 0, 0.59 * prompt_pulse))
		canvas.draw_rect(rect, Color(1, 0.86, 0.39, 0.86 * prompt_pulse), false, 2.0)
		RenderCache.centered(
			canvas,
			Vector2(640, 667),
			"PRESS SPACE / TAP TO BEGIN",
			26,
			Color(1, 0.86, 0.39, prompt_pulse),
			"body_semibold"
		)


func _draw_boss_intro(canvas: CanvasItem, frame: int) -> void:
	if not bool(boss_intro.get("active", false)):
		return
	var elapsed := BOSS_INTRO_DURATION - int(boss_intro.timer)
	var alpha := clampf(float(elapsed) / 15.0, 0.0, 1.0)
	if int(boss_intro.timer) < 20:
		alpha = float(boss_intro.timer) / 20.0
	canvas.draw_rect(Rect2(0, 0, 1280, 720), Color(0, 0, 0, 0.65 * alpha))
	var slide := (
		(1.0 - RenderEasing.out_cubic(clampf(float(elapsed - 15) / 30.0, 0.0, 1.0))) * -400.0
	)
	if preview != null:
		preview.pos = Vector2(430 + slide, 360)
		EntityVisuals.draw_unit(canvas, preview, frame)
	var color: Color = boss_intro.color
	var text_alpha := clampf(float(elapsed - 45) / 20.0, 0.0, 1.0) * alpha
	RenderCache.centered(
		canvas,
		Vector2(820, 300),
		str(boss_intro.name),
		60,
		Color(color.r, color.g, color.b, text_alpha),
		"title"
	)
	RenderCache.centered(
		canvas, Vector2(820, 350), str(boss_intro.title), 28, Color(0.85, 0.85, 0.9, text_alpha)
	)
	var hp_progress := clampf(float(elapsed) / float(BOSS_INTRO_DURATION) * 0.85, 0.0, 1.0)
	canvas.draw_rect(Rect2(620, 400, 400, 18), Color(0.1, 0.1, 0.12, text_alpha))
	canvas.draw_rect(Rect2(620, 400, 400 * hp_progress, 18), Color(0.8, 0.2, 0.2, text_alpha))
	RenderCache.centered(
		canvas, Vector2(640, 660), "TAP / SPACE TO SKIP", 20, Color(1, 1, 1, 0.6 * alpha)
	)


func _draw_boss_death(canvas: CanvasItem, frame: int) -> void:
	if boss_death.is_empty():
		return
	var pos: Vector2 = boss_death.pos
	var color: Color = boss_death.color
	if bool(boss_death.get("active", false)):
		var elapsed := int(boss_death.duration) - int(boss_death.timer)
		var progress := float(elapsed) / float(boss_death.duration)
		var waves := 3 if bool(boss_death.is_true) else 2
		for index in range(waves):
			var start := index * 15
			if elapsed < start:
				continue
			var wave_progress := clampf(float(elapsed - start) / 40.0, 0.0, 1.0)
			var radius := (60.0 + index * 70.0) * RenderEasing.out_cubic(wave_progress)
			var wave_color := (
				color if index == 0 else Color(1, 0.78 + index * 0.1, 0.39 + index * 0.3)
			)
			canvas.draw_arc(
				pos,
				radius,
				0,
				TAU,
				48,
				Color(wave_color.r, wave_color.g, wave_color.b, 1.0 - wave_progress),
				6.0
			)
		if progress < 0.15:
			canvas.draw_rect(Rect2(0, 0, 1280, 720), Color(1, 1, 1, (0.15 - progress) / 0.15 * 0.8))
		for index in range(12):
			var angle := float(index) / 12.0 * TAU + frame * 0.02
			var dist := progress * 180.0
			var frag := pos + Vector2(cos(angle), sin(angle)) * dist
			canvas.draw_rect(
				Rect2(frag, Vector2.ONE * 6.0 * (1.0 - progress)),
				Color(color.r, color.g, color.b, 1.0 - progress)
			)
	elif int(boss_death.get("celebration_timer", 0)) > 0:
		var alpha := clampf(float(boss_death.celebration_timer) / 30.0, 0.0, 1.0)
		RenderCache.centered(
			canvas, Vector2(640, 260), "BOSS DEFEATED!", 64, Color(1, 0.86, 0.39, alpha), "title"
		)
		RenderCache.centered(
			canvas,
			Vector2(640, 320),
			"%s  +%d GOLD" % [str(boss_death.name), int(boss_death.gold)],
			28,
			Color(1, 1, 1, alpha),
			"body_semibold"
		)


func clear() -> void:
	level_intro = {}
	boss_intro = {}
	boss_death = {}
	preview = null
