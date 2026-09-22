extends Node
## Langkah 11-12: state global + save progres.

var levels: Array = [
	"res://data/level1.json",
	"res://data/level2.json",
	"res://data/level3.json",
]
var level_index: int = 0
const SAVE_PATH = "user://save.cfg"
var unlocked: int = 1


func _ready() -> void:
	load_progress()


func load_progress() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) == OK:
		unlocked = clampi(int(cfg.get_value("progress", "unlocked", 1)), 1, levels.size())


func save_progress() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("progress", "unlocked", unlocked)
	cfg.save(SAVE_PATH)


func register_win() -> void:
	if level_index + 1 == unlocked and unlocked < levels.size():
		unlocked += 1
		save_progress()
		print("[App] Level %d terbuka!" % unlocked)


func level_path() -> String:
	return str(levels[level_index])


func start_level(i: int) -> void:
	level_index = clampi(i, 0, levels.size() - 1)
	get_tree().paused = false
	get_tree().change_scene_to_file("res://scenes/Main.tscn")


func restart_level() -> void:
	get_tree().paused = false
	get_tree().change_scene_to_file("res://scenes/Main.tscn")


func next_level() -> bool:
	if level_index + 1 >= levels.size():
		return false
	level_index += 1
	get_tree().paused = false
	get_tree().change_scene_to_file("res://scenes/Main.tscn")
	return true


func to_menu() -> void:
	get_tree().paused = false
	get_tree().change_scene_to_file("res://scenes/Menu.tscn")
