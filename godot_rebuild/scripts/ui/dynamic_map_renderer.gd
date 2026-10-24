extends RefCounted
## Layer 9d0: state and fixed-step update for the source DynamicRenderer.
## Drawing is split into source-ordered ops (`dynamic_map_layout.gd`) and native
## CanvasItem primitives (`dynamic_map_painter.gd`). Initial states for all 54
## themes and all three source quality presets come from the source oracle.

const MANIFEST := "res://data/art/map_dynamic.json"
const Layout = preload("res://scripts/ui/dynamic_map_layout.gd")
const Painter = preload("res://scripts/ui/dynamic_map_painter.gd")
const DEFAULT_QUALITY := {
	"level": "high",
	"particle_ratio": 0.70,
	"particles": true,
	"fog": true,
	"floating_decor": true,
}

static var _manifest: Dictionary = {}

var theme_name := ""
var theme: Dictionary = {}
var map_width := 1280
var map_height := 720
var radiant_shop_pos: Array = [340, 540]
var dire_shop_pos: Array = [940, 180]
var river_points: Array = []
var torch_stones: Array = []
var bones: Array = []
var rocks_mossy: Array = []
var gravestones: Array = []
var particles: Array = []
var fog_particles: Array = []
var quality: Dictionary = DEFAULT_QUALITY.duplicate()
var random_replay: Array = []
var draw_count := 0
var _replay_index := 0
var _rng := RandomNumberGenerator.new()


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest


static func themes() -> Array:
	var listed: Dictionary = manifest().get("themes", {})
	var names: Array = listed.keys()
	names.sort()
	return names


static func has_theme(requested: String) -> bool:
	var listed: Dictionary = manifest().get("themes", {})
	return listed.has(requested)


func configure(requested: String, level: String = "high") -> void:
	var key := requested if has_theme(requested) else "forest"
	var listed: Dictionary = manifest()["themes"]
	var entry: Dictionary = listed[key]
	var preset := level if manifest()["quality"].has(level) else "high"
	var layout: Dictionary = manifest()["layout"]
	var state: Dictionary = entry["states"][preset]
	configure_state(
		{
			"map_width": int(manifest()["screen"][0]),
			"map_height": int(manifest()["screen"][1]),
			"theme": entry["theme"],
			"radiant_shop_pos": manifest()["shop_positions"]["radiant"],
			"dire_shop_pos": manifest()["shop_positions"]["dire"],
			"river_points": layout["river_points"],
			"torch_stones": layout["torch_stones"],
			"bones": layout["bones"],
			"rocks_mossy": layout["rocks_mossy"],
			"gravestones": layout["gravestones"],
			"quality": manifest()["quality"][preset],
			"particles": state["particles"],
			"fog_particles": state["fog_particles"],
		}
	)
	theme_name = key


## Replay seam for source fixtures. Production uses `configure()` instead.
func configure_state(state: Dictionary) -> void:
	map_width = int(state.get("map_width", 1280))
	map_height = int(state.get("map_height", 720))
	theme = (state.get("theme", {}) as Dictionary).duplicate(true)
	radiant_shop_pos = (state.get("radiant_shop_pos", [340, 540]) as Array).duplicate(true)
	dire_shop_pos = (state.get("dire_shop_pos", [940, 180]) as Array).duplicate(true)
	river_points = (state.get("river_points", []) as Array).duplicate(true)
	torch_stones = (state.get("torch_stones", []) as Array).duplicate(true)
	bones = (state.get("bones", []) as Array).duplicate(true)
	rocks_mossy = (state.get("rocks_mossy", []) as Array).duplicate(true)
	gravestones = (state.get("gravestones", []) as Array).duplicate(true)
	quality = (state.get("quality", DEFAULT_QUALITY) as Dictionary).duplicate(true)
	particles = (state.get("particles", []) as Array).duplicate(true)
	fog_particles = (state.get("fog_particles", []) as Array).duplicate(true)
	_rng.seed = hash("dynamic:%s" % String(theme.get("name", theme_name)))
	set_random_replay([])


func set_random_replay(values: Array) -> void:
	random_replay = values.duplicate(true)
	_replay_index = 0


func random_replay_complete() -> bool:
	return _replay_index == random_replay.size()


func frame(t: int) -> Array:
	update()
	return Layout.ops(self, t)


func draw(canvas: CanvasItem, t: int) -> void:
	Painter.draw(canvas, frame(t))
	draw_count += 1


func snapshot() -> Dictionary:
	return {"particles": particles.duplicate(true), "fog_particles": fog_particles.duplicate(true)}


func update() -> void:
	var particle_type := String(theme.get("particle_type", "firefly"))
	for index in range(particles.size()):
		var particle: Dictionary = particles[index]
		particle["x"] = float(particle["x"]) + float(particle["vx"])
		particle["y"] = float(particle["y"]) + float(particle["vy"])
		particle["phase"] = float(particle["phase"]) + 0.08
		if particle_type == "firefly":
			if float(particle["x"]) < 30.0 or float(particle["x"]) > float(map_width - 30):
				particle["vx"] = -float(particle["vx"])
			if float(particle["y"]) < 30.0 or float(particle["y"]) > float(map_height - 30):
				particle["vy"] = -float(particle["vy"])
			if _random() < 0.02:
				particle["vx"] = _uniform(-0.4, 0.4)
				particle["vy"] = _uniform(-0.4, 0.4)
		elif particle_type == "snow":
			if float(particle["y"]) > float(map_height + 10):
				particle["y"] = -10.0
				particle["x"] = _uniform(0.0, float(map_width))
			particle["x"] = float(particle["x"]) + sin(float(particle["phase"])) * 0.2
		elif particle_type == "sand":
			if float(particle["x"]) > float(map_width + 20):
				particle["x"] = -20.0
				particle["y"] = _uniform(50.0, float(map_height - 50))
			if float(particle["x"]) < -20.0:
				particle["x"] = float(map_width + 20)
			particle["y"] = float(particle["y"]) + sin(float(particle["phase"]) * 2.0) * 0.3
		elif particle_type == "ember":
			if float(particle["y"]) < -10.0:
				particle["y"] = float(map_height + 10)
				particle["x"] = _uniform(0.0, float(map_width))
			particle["x"] = float(particle["x"]) + sin(float(particle["phase"])) * 0.15
		particles[index] = particle
	for index in range(fog_particles.size()):
		var fog: Dictionary = fog_particles[index]
		fog["x"] = float(fog["x"]) + float(fog["vx"])
		if float(fog["x"]) < -100.0:
			fog["x"] = float(map_width + 100)
		elif float(fog["x"]) > float(map_width + 100):
			fog["x"] = -100.0
		fog_particles[index] = fog
	_update_boss_particles(particle_type)


func _update_boss_particles(particle_type: String) -> void:
	for index in range(particles.size()):
		var particle: Dictionary = particles[index]
		if particle_type == "acid":
			if float(particle["y"]) < 30.0:
				particle["y"] = float(map_height - 25)
				particle["x"] = _uniform(30.0, float(map_width - 30))
			particle["x"] = float(particle["x"]) + sin(float(particle["phase"])) * 0.18
		elif particle_type == "ash":
			if float(particle["y"]) > float(map_height - 20):
				particle["y"] = 28.0
				particle["x"] = _uniform(30.0, float(map_width - 30))
			particle["x"] = float(particle["x"]) + sin(float(particle["phase"]) * 0.7) * 0.12
		elif particle_type == "spirit":
			if float(particle["y"]) < 28.0:
				particle["y"] = float(map_height - 30)
				particle["x"] = _uniform(30.0, float(map_width - 30))
			particle["x"] = float(particle["x"]) + sin(float(particle["phase"])) * 0.22
		particles[index] = particle


func _random() -> float:
	if _replay_index < random_replay.size():
		var value := float(random_replay[_replay_index])
		_replay_index += 1
		return value
	return _rng.randf()


func _uniform(low: float, high: float) -> float:
	if _replay_index < random_replay.size():
		var value := float(random_replay[_replay_index])
		_replay_index += 1
		return value
	return _rng.randf_range(low, high)
