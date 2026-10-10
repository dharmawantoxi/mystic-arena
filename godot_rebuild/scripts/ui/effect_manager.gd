extends RefCounted
## State-only port of `_render.py::EffectManager`.
##
## The source manager coordinates several pygame effects. Their state is kept
## through the existing Godot effect ports; world/UI drawing stays unported.
## Optional random replay arguments pin source-created values for the oracle
## suite while normal callers get the source random branches.

const FloatingText = preload("res://scripts/ui/floating_text.gd")
const HitParticle = preload("res://scripts/ui/hit_particle.gd")
const DeathExplosion = preload("res://scripts/ui/death_explosion.gd")
const ScreenShake = preload("res://scripts/ui/screen_shake.gd")
const ComboCounter = preload("res://scripts/ui/combo_counter.gd")
const WaveAnnouncer = preload("res://scripts/ui/wave_announcer.gd")
const KillFeed = preload("res://scripts/ui/kill_feed.gd")
const PathPreview = preload("res://scripts/ui/path_preview.gd")
const AchievementPopup = preload("res://scripts/ui/achievement_popup.gd")

const MAX_FLOATING := 300
const MAX_PARTICLES := 500
const MAX_EXPLOSIONS := 80

var floating_texts: Array = []
var particles: Array = []
var explosions: Array = []
var screen_shake: RefCounted
var combo_counter: RefCounted
var wave_announcer: RefCounted
var kill_feed: RefCounted
var path_preview: RefCounted
var achievement: RefCounted

var damage_numbers_enabled := true
var particles_enabled := true
var particle_ratio := 1.0
var max_damage_numbers := MAX_FLOATING
var screen_shake_enabled := true


func _init() -> void:
	_reset_effects()
	sync_settings()


func _reset_effects() -> void:
	floating_texts = []
	particles = []
	explosions = []
	screen_shake = ScreenShake.new()
	combo_counter = ComboCounter.new()
	wave_announcer = WaveAnnouncer.new()
	kill_feed = KillFeed.new()
	path_preview = PathPreview.new()
	achievement = AchievementPopup.new()


func configure() -> void:
	_reset_effects()
	sync_settings()


func set_quality_settings(
	damage_enabled: bool,
	particles_allowed: bool,
	ratio: float,
	damage_cap: int,
	shake_enabled: bool,
	sync: bool = true
) -> void:
	damage_numbers_enabled = damage_enabled
	particles_enabled = particles_allowed
	particle_ratio = ratio
	max_damage_numbers = damage_cap
	screen_shake_enabled = shake_enabled
	if sync:
		sync_settings()


func add_damage_number(
	x: float,
	y: float,
	damage: Variant,
	is_critical: bool = false,
	damage_type: String = "normal",
	offset_x: float = NAN,
	offset_y: float = NAN,
	drift: float = NAN
) -> void:
	if not damage_numbers_enabled:
		return
	if floating_texts.size() >= max_damage_numbers:
		if not floating_texts.is_empty():
			floating_texts.remove_at(0)
	elif floating_texts.size() >= MAX_FLOATING:
		floating_texts.remove_at(0)

	var color := Color8(255, 255, 255)
	var text := str(damage)
	if damage_type == "heal":
		color = Color8(100, 255, 100)
		text = "+%s" % damage
	elif is_critical:
		color = Color8(255, 220, 50)
		text = "%s!" % damage
	elif damage_type == "fire":
		color = Color8(255, 150, 50)
	elif damage_type == "ice":
		color = Color8(150, 220, 255)
	elif damage_type == "magic":
		color = Color8(200, 150, 255)

	var final_offset_x: float = offset_x
	var final_offset_y: float = offset_y
	var final_drift: float = drift
	if is_nan(final_offset_x):
		final_offset_x = float(randi_range(-8, 8))
	if is_nan(final_offset_y):
		final_offset_y = float(randi_range(-3, 3))
	if is_nan(final_drift):
		final_drift = randf_range(-0.3, 0.3)
	var size := "large" if is_critical else "medium"
	var text_value := FloatingText.new()
	text_value.configure(
		x + final_offset_x,
		y + final_offset_y,
		text,
		color,
		size,
		Vector2(0.0, -2.0),
		45,
		is_critical,
		final_drift
	)
	floating_texts.append(text_value)
	if floating_texts.size() > MAX_FLOATING:
		floating_texts.remove_at(0)


func add_gold_popup(x: float, y: float, amount: Variant, drift: float = NAN) -> void:
	var final_drift: float = drift
	if is_nan(final_drift):
		final_drift = randf_range(-0.3, 0.3)
	var text_value := FloatingText.new()
	text_value.configure(
		x,
		y - 10.0,
		"+%sG" % amount,
		Color8(255, 220, 50),
		"medium",
		Vector2(0.0, -1.5),
		50,
		false,
		final_drift
	)
	floating_texts.append(text_value)
	if floating_texts.size() > MAX_FLOATING:
		floating_texts.remove_at(0)


func add_hit_particles(
	x: float, y: float, team: String = "red", count: int = 5, particle_specs: Array = []
) -> void:
	if not particles_enabled:
		return
	var scaled_count: int = maxi(0, int(round(float(count) * particle_ratio)))
	if scaled_count <= 0:
		return
	var colors: Array
	if team == "blue":
		colors = [[100, 200, 255], [200, 240, 255]]
	else:
		colors = [[255, 150, 100], [255, 200, 150]]
	for index in range(scaled_count):
		var color: Array
		var velocity := Vector2(NAN, NAN)
		var lifetime := randi_range(12, 20)
		var particle_size := randi_range(2, 3)
		if index < particle_specs.size():
			var spec: Dictionary = particle_specs[index]
			color = _rgb(spec["color"] as Array)
			velocity = Vector2(float(spec["vx"]), float(spec["vy"]))
			lifetime = int(spec["lifetime"])
			particle_size = int(spec["size"])
		else:
			color = colors[randi_range(0, colors.size() - 1)]
		var particle := HitParticle.new()
		particle.configure(
			x,
			y,
			Color8(int(color[0]), int(color[1]), int(color[2])),
			velocity,
			lifetime,
			particle_size
		)
		particles.append(particle)
	while particles.size() > MAX_PARTICLES:
		particles.remove_at(0)


func add_death_explosion(
	x: float, y: float, team: String = "red", size: String = "medium", particle_specs: Array = []
) -> void:
	var explosion := DeathExplosion.new()
	explosion.configure(x, y, team, size, particle_specs)
	explosions.append(explosion)
	while explosions.size() > MAX_EXPLOSIONS:
		explosions.remove_at(0)


func shake_screen(intensity: float = 5.0) -> void:
	screen_shake.add_shake(intensity)


func sync_settings() -> void:
	screen_shake.enabled = screen_shake_enabled


func update() -> void:
	for text_value in floating_texts:
		text_value.update()
	var live_texts: Array = []
	for text_value in floating_texts:
		if text_value.alive:
			live_texts.append(text_value)
	floating_texts = live_texts

	for particle in particles:
		particle.update()
	var live_particles: Array = []
	for particle in particles:
		if particle.alive:
			live_particles.append(particle)
	particles = live_particles

	for explosion in explosions:
		explosion.update()
	var live_explosions: Array = []
	for explosion in explosions:
		if explosion.is_alive():
			live_explosions.append(explosion)
	explosions = live_explosions

	screen_shake.update()
	combo_counter.update()
	wave_announcer.update()
	kill_feed.update()
	path_preview.update()
	achievement.update()


func show_path_preview(lane_paths: Array) -> void:
	path_preview.show(lane_paths)


func unlock_achievement(title: String, description: String, icon: String = "star") -> void:
	achievement.unlock(title, description, icon)


func register_kill(
	_killer_name: String = "Tower", _victim_name: String = "Enemy", _killer_team: String = "blue"
) -> void:
	return


func announce_wave(wave_num: int) -> void:
	wave_announcer.announce(wave_num)


func get_shake_offset() -> Vector2i:
	return screen_shake.get_offset()


func get_state() -> Dictionary:
	return {
		"floating_count": floating_texts.size(),
		"particle_count": particles.size(),
		"explosion_count": explosions.size(),
		"floating": _floating_snapshots(),
		"particles": _particle_snapshots(),
		"explosions": _explosion_snapshots(),
		"screen_shake":
		{
			"intensity": screen_shake.intensity,
			"enabled": screen_shake.enabled,
		},
		"combo":
		{
			"count": combo_counter.count,
			"timer": combo_counter.timer,
			"max_timer": combo_counter.max_timer,
			"display_scale": combo_counter.display_scale,
			"target_scale": combo_counter.target_scale,
			"color_flash": combo_counter.color_flash,
			"last_combo": combo_counter.last_combo,
		},
		"wave":
		{
			"active": wave_announcer.active,
			"wave_num": wave_announcer.wave_num,
			"timer": wave_announcer.timer,
			"duration": wave_announcer.duration,
		},
		"kill_feed": _normalize(kill_feed.entries),
		"path_preview":
		{
			"active": path_preview.active,
			"paths": _normalize(path_preview.paths),
			"timer": path_preview.timer,
			"duration": path_preview.duration,
		},
		"achievement":
		{
			"queue": _normalize(achievement.queue),
			"current": null if achievement.current.is_empty() else _normalize(achievement.current),
			"timer": achievement.timer,
			"duration": achievement.duration,
		},
	}


func _floating_snapshots() -> Array:
	var result: Array = []
	for value in floating_texts:
		(
			result
			. append(
				{
					"x": value.x,
					"y": value.y,
					"text": value.text,
					"color": _color_rgb(value.color),
					"velocity_x": value.velocity_x,
					"velocity_y": value.velocity_y,
					"lifetime": value.lifetime,
					"max_lifetime": value.max_lifetime,
					"alive": value.alive,
					"critical": value.critical,
					"font_size": value.font_size,
					"x_drift": value.x_drift,
					"scale": value.scale,
					"target_scale": value.target_scale,
				}
			)
		)
	return result


func _particle_snapshots() -> Array:
	var result: Array = []
	for value in particles:
		(
			result
			. append(
				{
					"x": value.x,
					"y": value.y,
					"color": _color_rgb(value.color),
					"vx": value.vx,
					"vy": value.vy,
					"lifetime": value.lifetime,
					"max_lifetime": value.max_lifetime,
					"size": value.size,
					"alive": value.alive,
				}
			)
		)
	return result


func _explosion_snapshots() -> Array:
	var result: Array = []
	for value in explosions:
		(
			result
			. append(
				{
					"x": value.x,
					"y": value.y,
					"flash_timer": value.flash_timer,
					"flash_max": value.flash_max,
					"particle_count": value.get_particle_count(),
					"alive": value.is_alive(),
				}
			)
		)
	return result


func _color_rgb(value: Color) -> Array:
	return [roundi(value.r * 255.0), roundi(value.g * 255.0), roundi(value.b * 255.0)]


func _rgb(value: Array) -> Array:
	return [int(value[0]), int(value[1]), int(value[2])]


func _normalize(value: Variant) -> Variant:
	if value is Color:
		return _color_rgb(value)
	if value is Dictionary:
		var dictionary: Dictionary = {}
		for key in value:
			dictionary[key] = _normalize(value[key])
		return dictionary
	if value is Array:
		var array: Array = []
		for item in value:
			array.append(_normalize(item))
		return array
	return value
