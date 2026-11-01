class_name CombatEffects
extends RefCounted

## Native _render.EffectManager: floating text, hit sparks, death explosions,
## screen shake, combo, wave banner, path preview, achievements and popup easing.
## KillFeed is intentionally present but disabled, matching draw_ui() in _core.py.
const MAX_FLOATING := 300
const MAX_PARTICLES := 500
const MAX_EXPLOSIONS := 80
const COMBO_DURATION := 120
const WAVE_DURATION := 120
const PATH_DURATION := 120
const ACHIEVEMENT_DURATION := 180
var floating_texts: Array[Dictionary] = []
var particles: Array[Dictionary] = []
var explosions: Array[Dictionary] = []
var rings: Array[Dictionary] = []
var shake_intensity := 0.0
var shake_enabled := true
var damage_numbers_enabled := true
var quality: Dictionary = RenderQuality.preset("high")
var combo_count := 0
var combo_timer := 0
var combo_scale := 1.0
var wave_number := 0
var wave_timer := 0
var path_timer := 0
var paths: Array = []
var achievement_queue: Array[Dictionary] = []
var achievement_current: Dictionary = {}
var achievement_timer := 0
var kill_feed_entries: Array[Dictionary] = []
var kill_feed_enabled := false
var popup_progress := 1.0
var popup_target := 1.0
var rng := RandomNumberGenerator.new()


func configure(values: Dictionary) -> void:
	quality = RenderQuality.from_settings(values)
	shake_enabled = bool(values.get("screen_shake_enabled", false))
	damage_numbers_enabled = bool(values.get("damage_numbers_enabled", true))
	rng.seed = 20261101


func add_damage_number(
	pos: Vector2, damage: int, critical := false, damage_type := "normal"
) -> void:
	if not damage_numbers_enabled:
		return
	var color := Color.WHITE
	var label := str(damage)
	match damage_type:
		"heal":
			color = Color(0.39, 1.0, 0.39)
			label = "+%d" % damage
		"fire":
			color = Color(1.0, 0.59, 0.2)
		"ice":
			color = Color(0.59, 0.86, 1.0)
		"magic":
			color = Color(0.78, 0.59, 1.0)
	if critical:
		color = Color(1.0, 0.86, 0.2)
		label = "%d!" % damage
	var offset := Vector2(rng.randi_range(-8, 8), rng.randi_range(-3, 3))
	_push_floating(
		{
			"pos": pos + offset,
			"text": label,
			"color": color,
			"vel": Vector2(0, -2),
			"life": 45,
			"max_life": 45,
			"size": 24 if critical else 18,
			"critical": critical,
			"scale": 0.3,
		}
	)


func add_gold_popup(pos: Vector2, amount: int) -> void:
	_push_floating(
		{
			"pos": pos + Vector2(0, -10),
			"text": "+%dG" % amount,
			"color": Color(1.0, 0.86, 0.2),
			"vel": Vector2(0, -1.5),
			"life": 50,
			"max_life": 50,
			"size": 18,
			"critical": false,
			"scale": 0.3,
		}
	)


func add_popup(pos: Vector2, label: String, color: Color) -> void:
	_push_floating(
		{
			"pos": pos,
			"text": label,
			"color": color,
			"vel": Vector2(0, -1.0),
			"life": 60,
			"max_life": 60,
			"size": 18,
			"critical": false,
			"scale": 0.3,
		}
	)


func _push_floating(entry: Dictionary) -> void:
	var cap := mini(MAX_FLOATING, int(quality.get("max_damage_numbers", MAX_FLOATING)))
	while floating_texts.size() >= cap:
		floating_texts.pop_front()
	floating_texts.append(entry)


func add_hit_particles(pos: Vector2, color: Color, count := 6) -> void:
	var scaled := maxi(0, int(round(count * float(quality.get("particle_ratio", 1.0)))))
	for index in range(scaled):
		var angle := rng.randf() * TAU
		var speed := rng.randf_range(1.0, 3.0)
		(
			particles
			. append(
				{
					"pos": pos,
					"vel": Vector2(cos(angle), sin(angle)) * speed,
					"color": color,
					"life": 15,
					"max_life": 15,
					"size": rng.randi_range(1, 3),
				}
			)
		)
	_trim_particles()


func add_death_explosion(pos: Vector2, team := "red", size := "medium") -> void:
	var count := 8
	var spark_min := 2
	var spark_max := 4
	if size == "medium":
		count = 15
		spark_min = 3
		spark_max = 5
	elif size == "large":
		count = 25
		spark_min = 4
		spark_max = 6
	var palette := [Color(0.39, 0.78, 1.0), Color(0.59, 0.86, 1.0), Color(0.78, 0.94, 1.0)]
	if team != "blue":
		palette = [Color(1.0, 0.39, 0.39), Color(1.0, 0.59, 0.39), Color(1.0, 0.78, 0.39)]
	var sparks: Array[Dictionary] = []
	for index in range(count):
		var angle := rng.randf() * TAU
		var speed := rng.randf_range(1.5, 4.0)
		(
			sparks
			. append(
				{
					"pos": pos,
					"vel": Vector2(cos(angle), sin(angle)) * speed,
					"color": palette[rng.randi_range(0, palette.size() - 1)],
					"life": rng.randi_range(20, 35),
					"max_life": 35,
					"size": rng.randi_range(spark_min, spark_max),
				}
			)
		)
	explosions.append({"pos": pos, "sparks": sparks, "flash": 8})
	while explosions.size() > MAX_EXPLOSIONS:
		explosions.pop_front()


func add_effect(pos: Vector2, effect_type: String, color: Color, radius: int) -> void:
	if effect_type == "hit":
		add_hit_particles(pos, color, maxi(3, radius / 2))
	else:
		rings.append(
			{
				"pos": pos,
				"color": color,
				"radius": float(radius),
				"life": 24,
				"max_life": 24,
				"label": effect_type
			}
		)
		while rings.size() > 120:
			rings.pop_front()


func add_shake(amount: float) -> void:
	if shake_enabled:
		shake_intensity = maxf(shake_intensity, amount)


func register_kill(_killer: String, _victim: String, _team := "blue") -> void:
	# _core.draw_ui deliberately removed kill-feed/combo notifications; the feed
	# stays a no-op. Combo visuals are driven by register_combo_kill() instead.
	if not kill_feed_enabled:
		return
	kill_feed_entries.append({"text": "%s >> %s" % [_killer, _victim], "life": 180})
	while kill_feed_entries.size() > 5:
		kill_feed_entries.pop_front()


func register_combo_kill() -> void:
	combo_count += 1
	combo_timer = COMBO_DURATION
	combo_scale = 1.4


func announce_wave(number: int) -> void:
	wave_number = number
	wave_timer = WAVE_DURATION


func show_path_preview(lane_paths: Array) -> void:
	paths = lane_paths.duplicate()
	path_timer = PATH_DURATION


func unlock_achievement(title: String, description: String, icon := "star") -> void:
	achievement_queue.append({"title": title, "description": description, "icon": icon})


func popup_show() -> void:
	popup_progress = 0.0
	popup_target = 1.0


func popup_hide() -> void:
	popup_target = 0.0


func popup_scale() -> float:
	return RenderEasing.out_back(popup_progress)


func update() -> void:
	for entry: Dictionary in floating_texts:
		entry.pos = Vector2(entry.pos) + Vector2(entry.vel)
		entry.life = int(entry.life) - 1
		entry.scale = lerpf(float(entry.scale), 1.2 if bool(entry.critical) else 1.0, 0.25)
	floating_texts = floating_texts.filter(
		func(entry: Dictionary) -> bool: return int(entry.life) > 0
	)
	for particle: Dictionary in particles:
		_step_particle(particle)
	particles = particles.filter(func(particle: Dictionary) -> bool: return int(particle.life) > 0)
	for explosion: Dictionary in explosions:
		explosion.flash = maxi(0, int(explosion.flash) - 1)
		var sparks: Array = explosion.sparks
		for spark: Dictionary in sparks:
			_step_particle(spark)
		explosion.sparks = sparks.filter(
			func(spark: Dictionary) -> bool: return int(spark.life) > 0
		)
	explosions = explosions.filter(
		func(explosion: Dictionary) -> bool:
			return int(explosion.flash) > 0 or not Array(explosion.sparks).is_empty()
	)
	for ring: Dictionary in rings:
		ring.life = int(ring.life) - 1
	rings = rings.filter(func(ring: Dictionary) -> bool: return int(ring.life) > 0)
	shake_intensity *= 0.85
	if shake_intensity < 0.5:
		shake_intensity = 0.0
	if combo_timer > 0:
		combo_timer -= 1
		combo_scale = lerpf(combo_scale, 1.0, 0.2)
		if combo_timer == 0:
			combo_count = 0
	if wave_timer > 0:
		wave_timer -= 1
	if path_timer > 0:
		path_timer -= 1
		if path_timer == 0:
			paths.clear()
	if not achievement_current.is_empty():
		achievement_timer -= 1
		if achievement_timer <= 0:
			achievement_current = {}
	if achievement_current.is_empty() and not achievement_queue.is_empty():
		achievement_current = achievement_queue.pop_front()
		achievement_timer = ACHIEVEMENT_DURATION
	for entry: Dictionary in kill_feed_entries:
		entry.life = int(entry.life) - 1
	kill_feed_entries = kill_feed_entries.filter(
		func(entry: Dictionary) -> bool: return int(entry.life) > 0
	)
	var diff := popup_target - popup_progress
	popup_progress += diff * 0.15
	if absf(diff) < 0.01:
		popup_progress = popup_target


func _step_particle(particle: Dictionary) -> void:
	particle.pos = Vector2(particle.pos) + Vector2(particle.vel)
	var vel: Vector2 = particle.vel
	vel.y += 0.15
	vel.x *= 0.95
	particle.vel = vel
	particle.life = int(particle.life) - 1


func _trim_particles() -> void:
	if particles.size() > MAX_PARTICLES:
		particles = particles.slice(particles.size() - MAX_PARTICLES)


func shake_offset() -> Vector2:
	if shake_intensity <= 0.0:
		return Vector2.ZERO
	var amount := int(shake_intensity)
	return Vector2(rng.randi_range(-amount, amount), rng.randi_range(-amount, amount))


func draw(canvas: CanvasItem) -> void:
	_draw_paths(canvas)
	for ring: Dictionary in rings:
		var progress := 1.0 - float(ring.life) / float(ring.max_life)
		var color: Color = ring.color
		color.a = 1.0 - progress
		canvas.draw_arc(ring.pos, float(ring.radius) * (0.5 + progress), 0, TAU, 24, color, 2.0)
		if not str(ring.label).is_empty() and str(ring.label) != "hit":
			RenderCache.centered(
				canvas,
				Vector2(ring.pos) + Vector2(0, -float(ring.radius)),
				str(ring.label),
				16,
				color,
				"body_bold"
			)
	for explosion: Dictionary in explosions:
		_draw_explosion(canvas, explosion)
	for particle: Dictionary in particles:
		_draw_particle(canvas, particle)
	for entry: Dictionary in floating_texts:
		_draw_floating(canvas, entry)
	_draw_combo(canvas)
	_draw_wave(canvas)
	_draw_achievement(canvas)
	_draw_kill_feed(canvas)


func _draw_particle(canvas: CanvasItem, particle: Dictionary) -> void:
	var alpha := clampf(float(particle.life) / float(particle.max_life), 0.0, 1.0)
	var color: Color = particle.color
	color.a = alpha
	canvas.draw_circle(particle.pos, float(particle.size), color)
	canvas.draw_circle(particle.pos, maxf(1.0, float(particle.size) * 0.5), Color(1, 1, 1, alpha))


func _draw_explosion(canvas: CanvasItem, explosion: Dictionary) -> void:
	var flash := int(explosion.flash)
	if flash > 0:
		var intensity := flash / 8.0
		var radius := 20.0 * intensity
		canvas.draw_circle(explosion.pos, radius * 1.5, Color(1, 1, 0.78, 0.78 * intensity))
		canvas.draw_circle(explosion.pos, radius * 0.5, Color(1, 1, 1, intensity))
	for spark: Dictionary in explosion.sparks:
		_draw_particle(canvas, spark)


func _draw_floating(canvas: CanvasItem, entry: Dictionary) -> void:
	var alpha := clampf(float(entry.life) / float(entry.max_life), 0.0, 1.0)
	var color: Color = entry.color
	color.a = alpha
	var font_size := int(float(entry.size) * float(entry.scale))
	var style := "body_bold" if bool(entry.critical) else "body_semibold"
	var pos: Vector2 = entry.pos
	RenderCache.centered(
		canvas,
		pos + Vector2(1, 1),
		str(entry.text),
		font_size,
		Color(0.03, 0.03, 0.05, alpha),
		style
	)
	RenderCache.centered(canvas, pos, str(entry.text), font_size, color, style)


func _draw_combo(canvas: CanvasItem) -> void:
	if combo_count < 2 or combo_timer <= 0:
		return
	var alpha := clampf(float(combo_timer) / 30.0, 0.0, 1.0)
	var size := int(36.0 * combo_scale)
	RenderCache.centered(
		canvas,
		Vector2(640, 110),
		"COMBO x%d" % combo_count,
		size,
		Color(1, 0.86, 0.2, alpha),
		"title"
	)


func _draw_wave(canvas: CanvasItem) -> void:
	if wave_timer <= 0:
		return
	var progress := 1.0 - float(wave_timer) / float(WAVE_DURATION)
	var alpha := 1.0
	if progress < 0.15:
		alpha = progress / 0.15
	elif progress > 0.85:
		alpha = (1.0 - progress) / 0.15
	var offset := (1.0 - RenderEasing.out_cubic(clampf(progress / 0.3, 0.0, 1.0))) * -80.0
	canvas.draw_rect(Rect2(0, 150 + offset, 1280, 70), Color(0.02, 0.03, 0.06, 0.7 * alpha))
	RenderCache.centered(
		canvas,
		Vector2(640, 195 + offset),
		"WAVE %d" % wave_number,
		44,
		Color(1, 0.86, 0.39, alpha),
		"title"
	)


func _draw_paths(canvas: CanvasItem) -> void:
	if path_timer <= 0:
		return
	var alpha_ratio := 1.0
	if path_timer > PATH_DURATION - 20:
		alpha_ratio = float(PATH_DURATION - path_timer) / 20.0
	elif path_timer < 40:
		alpha_ratio = float(path_timer) / 40.0
	var alpha := 200.0 / 255.0 * alpha_ratio
	for lane_path: PackedVector2Array in paths:
		for index in range(0, lane_path.size() - 1, 8):
			var pos := lane_path[index]
			var next := lane_path[mini(index + 4, lane_path.size() - 1)]
			var direction := (next - pos).normalized()
			if direction == Vector2.ZERO:
				direction = Vector2.RIGHT
			var side := Vector2(-direction.y, direction.x)
			var pulse := (index / 8) % 4
			var length := 8.0 if pulse == 0 else 5.0
			var color := Color(1, 0.39, 0.39, alpha if pulse == 0 else alpha * 0.5)
			var points := PackedVector2Array(
				[
					pos + direction * length,
					pos - direction * length * 0.5 + side * length * 0.5,
					pos - direction * length * 0.5 - side * length * 0.5
				]
			)
			canvas.draw_colored_polygon(points, color)


func _draw_achievement(canvas: CanvasItem) -> void:
	if achievement_current.is_empty():
		return
	var progress := 1.0 - float(achievement_timer) / float(ACHIEVEMENT_DURATION)
	var offset := 0.0
	var alpha := 1.0
	if progress < 0.15:
		offset = (1.0 - RenderEasing.out_back(progress / 0.15)) * 300.0
		alpha = progress / 0.15
	elif progress > 0.85:
		offset = ((progress - 0.85) / 0.15) * 300.0
		alpha = 1.0 - (progress - 0.85) / 0.15
	var rect := Rect2(930 + offset, 70, 320, 74)
	canvas.draw_rect(rect, Color(0.05, 0.06, 0.1, 0.92 * alpha))
	canvas.draw_rect(rect, Color(1, 0.86, 0.39, alpha), false, 2.0)
	RenderCache.text(
		canvas,
		rect.position + Vector2(14, 28),
		str(achievement_current.title),
		20,
		Color(1, 0.86, 0.39, alpha),
		"body_bold"
	)
	RenderCache.text(
		canvas,
		rect.position + Vector2(14, 54),
		str(achievement_current.description),
		16,
		Color(0.8, 0.85, 0.9, alpha)
	)


func _draw_kill_feed(canvas: CanvasItem) -> void:
	if not kill_feed_enabled:
		return
	var y := 80.0
	for entry: Dictionary in kill_feed_entries:
		RenderCache.text(
			canvas,
			Vector2(980, y),
			str(entry.text),
			16,
			Color(0.6, 0.8, 1.0, clampf(float(entry.life) / 60.0, 0, 1))
		)
		y += 20.0


func clear() -> void:
	floating_texts.clear()
	particles.clear()
	explosions.clear()
	rings.clear()
	achievement_queue.clear()
	achievement_current = {}
	kill_feed_entries.clear()
	paths.clear()
	shake_intensity = 0.0
	combo_count = 0
	combo_timer = 0
	wave_timer = 0
	path_timer = 0
	achievement_timer = 0
