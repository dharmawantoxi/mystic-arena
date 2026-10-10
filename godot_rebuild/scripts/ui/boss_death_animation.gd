extends RefCounted
## Boss death presentation state, ported from `_render.py::BossDeathAnimation`.
##
## The pygame `draw()` methods stay out of the port. Callers get the cached boss
## data, wave/particle state, lifecycle flags and draw-local presentation values
## through getters. The optional particle arrays are the source-oracle replay
## seam; an empty array follows the source random initialisers.

const TRUE_DURATION := 90
const MINI_DURATION := 60
const CELEBRATION_DURATION := 120
const FLASH_WINDOW := 15
const WAVE_DURATION := 40

const DEFAULT_BOSS_COLOR := [150, 100, 200]
const DEFAULT_DARK_COLOR := [75, 50, 100]

var screen_w := 1280
var screen_h := 720

var boss_x := 0.0
var boss_y := 0.0
var boss_name := "Unknown"
var boss_title := "The Boss"
var boss_class := "mini"
var boss_color: Array = DEFAULT_BOSS_COLOR.duplicate()
var boss_color_dark: Array = DEFAULT_DARK_COLOR.duplicate()
var entrance_color: Array = DEFAULT_BOSS_COLOR.duplicate()
var boss_gold_reward := 0
var boss_radius := 40.0

var active := true
var duration := MINI_DURATION
var show_celebration := false
var timer := MINI_DURATION
var explosion_waves: Array = []
var fragments: Array = []
var rising_particles: Array = []
var fragment_colors: Array = []
var rising_colors: Array = []
var sound_played := false
var celebration_timer := 0
var celebration_duration := CELEBRATION_DURATION
var celebration_active := false


## `particle_specs` and `rising_specs` replay the source-created dictionaries.
## Omit them for the source random branches.
func configure(
	boss: Dictionary, width: int, height: int, particle_specs: Array = [], rising_specs: Array = []
) -> void:
	screen_w = width
	screen_h = height
	boss_x = float(boss.get("x", 0.0))
	boss_y = float(boss.get("y", 0.0))
	boss_name = String(boss.get("name", "Unknown"))
	boss_title = String(boss.get("title", "The Boss"))
	boss_class = String(boss.get("boss_class", "mini"))
	boss_color = _to_rgb(boss.get("color", null), DEFAULT_BOSS_COLOR)
	boss_color_dark = _to_rgb(boss.get("color_dark", null), DEFAULT_DARK_COLOR)
	entrance_color = _to_rgb(boss.get("entrance_color", null), DEFAULT_BOSS_COLOR)
	boss_gold_reward = int(boss.get("gold_reward", 0))
	boss_radius = float(boss.get("radius", 40.0))

	if boss_class == "true":
		duration = TRUE_DURATION
		show_celebration = true
	else:
		duration = MINI_DURATION
		show_celebration = false
	timer = duration
	explosion_waves = _make_waves()
	fragments = _make_fragments(particle_specs)
	rising_particles = _make_rising_particles(rising_specs)
	_cache_particle_colors()
	sound_played = false
	celebration_timer = 0
	celebration_duration = CELEBRATION_DURATION
	celebration_active = false


func update() -> void:
	if not active:
		if celebration_active:
			celebration_timer -= 1
			if celebration_timer <= 0:
				celebration_active = false
		return

	timer -= 1
	if not sound_played:
		sound_played = true

	for index in range(fragments.size()):
		var fragment: Dictionary = fragments[index]
		fragment["x"] = float(fragment["x"]) + float(fragment["vx"])
		fragment["y"] = float(fragment["y"]) + float(fragment["vy"])
		fragment["vy"] = float(fragment["vy"]) + float(fragment["gravity"])
		fragment["rotation"] = float(fragment["rotation"]) + float(fragment["rot_speed"])
		fragment["life"] = int(fragment["life"]) - 1
		fragments[index] = fragment

	for index in range(rising_particles.size()):
		var particle: Dictionary = rising_particles[index]
		particle["x"] = float(particle["x"]) + float(particle["vx"])
		particle["y"] = float(particle["y"]) + float(particle["vy"])
		particle["phase"] = float(particle["phase"]) + 0.1
		particle["x"] = float(particle["x"]) + sin(float(particle["phase"])) * 0.5
		particle["life"] = int(particle["life"]) - 1
		rising_particles[index] = particle

	if timer <= 0:
		active = false
		if show_celebration:
			celebration_active = true
			celebration_timer = celebration_duration


func handle_skip(keycode: int = -1, click: bool = false) -> bool:
	if celebration_active:
		if keycode == KEY_SPACE or keycode == KEY_ESCAPE or click:
			celebration_active = false
			return true
	return false


func is_active() -> bool:
	return active or celebration_active


func is_death_active() -> bool:
	return active


func get_state() -> Dictionary:
	return {
		"active": active,
		"timer": timer,
		"duration": duration,
		"show_celebration": show_celebration,
		"celebration_active": celebration_active,
		"celebration_timer": celebration_timer,
		"sound_played": sound_played,
		"fragment_count": fragments.size(),
		"rising_particle_count": rising_particles.size(),
	}


func get_explosion_waves() -> Array:
	return explosion_waves.duplicate(true)


func get_fragment_count() -> int:
	return fragments.size()


func get_fragment_snapshot(index: int) -> Dictionary:
	var snapshot: Dictionary = (fragments[index] as Dictionary).duplicate(true)
	snapshot["color"] = (fragment_colors[index] as Array).duplicate()
	return snapshot


func get_rising_particle_count() -> int:
	return rising_particles.size()


func get_rising_particle_snapshot(index: int) -> Dictionary:
	var snapshot: Dictionary = (rising_particles[index] as Dictionary).duplicate(true)
	snapshot["color"] = (rising_colors[index] as Array).duplicate()
	return snapshot


## Values calculated in `_draw_death_sequence`, without drawing pygame pixels.
func get_death_visual_state() -> Dictionary:
	var elapsed: int = duration - timer
	var progress: float = float(elapsed) / float(duration)
	var flash_alpha := 0
	if elapsed < FLASH_WINDOW:
		flash_alpha = int(200.0 * (1.0 - float(elapsed) / float(FLASH_WINDOW)))

	var waves: Array = []
	for wave_value in explosion_waves:
		var wave: Dictionary = wave_value
		var wave_elapsed: int = elapsed - int(wave["start_frame"])
		if wave_elapsed < 0 or wave_elapsed >= WAVE_DURATION:
			continue
		var wave_progress: float = float(wave_elapsed) / float(WAVE_DURATION)
		var radius: int = int(float(wave["max_radius"]) * wave_progress)
		var alpha: int = int(220.0 * (1.0 - wave_progress))
		if alpha <= 0 or radius <= 0:
			continue
		(
			waves
			. append(
				{
					"start_frame": int(wave["start_frame"]),
					"max_radius": int(wave["max_radius"]),
					"wave_elapsed": wave_elapsed,
					"wave_progress": wave_progress,
					"radius": radius,
					"alpha": alpha,
					"color": (wave["color"] as Array).duplicate(),
				}
			)
		)

	var body_visible := progress < 0.5
	var dissolve_alpha := 0
	var dissolve_size := 0
	if body_visible:
		dissolve_alpha = int(255.0 * (1.0 - progress * 2.0))
		dissolve_size = int(boss_radius * (1.0 - progress * 0.5))
	return {
		"elapsed": elapsed,
		"progress": progress,
		"flash_visible": elapsed < FLASH_WINDOW,
		"flash_alpha": flash_alpha,
		"waves": waves,
		"body_visible": body_visible,
		"dissolve_alpha": dissolve_alpha,
		"dissolve_size": dissolve_size,
	}


## Values calculated in `_draw_celebration`, without drawing pygame pixels.
func get_celebration_visual_state(time_ticks: int = 0) -> Dictionary:
	if not celebration_active:
		return {"visible": false}
	var elapsed: int = celebration_duration - celebration_timer
	var progress: float = float(elapsed) / float(celebration_duration)
	var overlay_alpha: int
	if progress < 0.15:
		overlay_alpha = int(180.0 * (progress / 0.15))
	elif progress > 0.85:
		overlay_alpha = int(180.0 * (1.0 - (progress - 0.85) / 0.15))
	else:
		overlay_alpha = 180

	var text_alpha := 255
	var text_offset_y := 0
	if progress < 0.3:
		var bounce_prog: float = progress / 0.3
		var eased: float = 1.0 - pow(1.0 - bounce_prog, 3.0)
		text_alpha = int(255.0 * eased)
		text_offset_y = int((1.0 - eased) * 60.0)
	elif progress > 0.85:
		text_alpha = int(255.0 * (1.0 - (progress - 0.85) / 0.15))

	var reward_visible := progress > 0.3
	var reward_alpha := 0
	if reward_visible:
		reward_alpha = mini(255, int(255.0 * (progress - 0.3) / 0.3))
	var hint_visible := progress > 0.5
	var hint_alpha := 0
	if hint_visible:
		var hint_pulse: float = sin(float(time_ticks) * 0.005) * 0.3 + 0.7
		hint_alpha = int(180.0 * hint_pulse)
	return {
		"visible": true,
		"elapsed": elapsed,
		"progress": progress,
		"overlay_alpha": overlay_alpha,
		"tint_visible": progress < 0.85,
		"text_alpha": text_alpha,
		"text_offset_y": text_offset_y,
		"reward_visible": reward_visible,
		"reward_alpha": reward_alpha,
		"hint_visible": hint_visible,
		"hint_alpha": hint_alpha,
	}


func _cache_particle_colors() -> void:
	fragment_colors.clear()
	for value in fragments:
		var fragment: Dictionary = value
		fragment_colors.append((fragment["color"] as Array).duplicate())
	rising_colors.clear()
	for value in rising_particles:
		var particle: Dictionary = value
		rising_colors.append((particle["color"] as Array).duplicate())


func _make_waves() -> Array:
	if boss_class == "true":
		return [
			{"start_frame": 0, "max_radius": 60, "color": entrance_color.duplicate()},
			{"start_frame": 15, "max_radius": 120, "color": [255, 200, 100]},
			{"start_frame": 30, "max_radius": 200, "color": [255, 255, 200]},
		]
	return [
		{"start_frame": 0, "max_radius": 50, "color": entrance_color.duplicate()},
		{"start_frame": 15, "max_radius": 100, "color": [255, 220, 150]},
	]


func _make_fragments(specs: Array) -> Array:
	if not specs.is_empty():
		var replay: Array = []
		for value in specs:
			replay.append(_fragment_from_spec(value))
		return replay
	var result: Array = []
	var count: int = 25 if boss_class == "true" else 15
	var choices: Array = [boss_color, boss_color_dark, entrance_color]
	for _index in range(count):
		var angle: float = randf_range(0.0, TAU)
		var speed: float = randf_range(2.0, 6.0)
		(
			result
			. append(
				{
					"x": boss_x + randf_range(-15.0, 15.0),
					"y": boss_y + randf_range(-15.0, 15.0),
					"vx": cos(angle) * speed,
					"vy": sin(angle) * speed - 2.0,
					"size": randi_range(3, 8),
					"color": (choices[randi_range(0, choices.size() - 1)] as Array).duplicate(),
					"rotation": randf_range(0.0, TAU),
					"rot_speed": randf_range(-0.3, 0.3),
					"gravity": 0.2,
					"life": 60,
					"max_life": 60,
				}
			)
		)
	return result


func _make_rising_particles(specs: Array) -> Array:
	if not specs.is_empty():
		var replay: Array = []
		for value in specs:
			replay.append(_rising_from_spec(value))
		return replay
	var result: Array = []
	var count: int = 30 if boss_class == "true" else 15
	for _index in range(count):
		(
			result
			. append(
				{
					"x": boss_x + randf_range(-30.0, 30.0),
					"y": boss_y + randf_range(-10.0, 10.0),
					"vx": randf_range(-0.5, 0.5),
					"vy": randf_range(-3.0, -1.0),
					"size": randi_range(2, 5),
					"color": entrance_color.duplicate(),
					"life": randi_range(60, 100),
					"max_life": 100,
					"phase": randf_range(0.0, TAU),
				}
			)
		)
	return result


func _fragment_from_spec(value: Variant) -> Dictionary:
	var spec: Dictionary = value
	return {
		"x": float(spec["x"]),
		"y": float(spec["y"]),
		"vx": float(spec["vx"]),
		"vy": float(spec["vy"]),
		"size": int(spec["size"]),
		"color": _to_rgb(spec.get("color", null), DEFAULT_BOSS_COLOR),
		"rotation": float(spec["rotation"]),
		"rot_speed": float(spec["rot_speed"]),
		"gravity": float(spec["gravity"]),
		"life": int(spec["life"]),
		"max_life": int(spec["max_life"]),
	}


func _rising_from_spec(value: Variant) -> Dictionary:
	var spec: Dictionary = value
	return {
		"x": float(spec["x"]),
		"y": float(spec["y"]),
		"vx": float(spec["vx"]),
		"vy": float(spec["vy"]),
		"size": int(spec["size"]),
		"color": _to_rgb(spec.get("color", null), entrance_color),
		"life": int(spec["life"]),
		"max_life": int(spec["max_life"]),
		"phase": float(spec["phase"]),
	}


func _to_rgb(value: Variant, fallback: Array) -> Array:
	if value is Array and value.size() >= 3:
		return [int(value[0]), int(value[1]), int(value[2])]
	return fallback.duplicate()
