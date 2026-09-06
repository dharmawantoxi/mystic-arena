# SaveManager.gd — Port dari mobile/cloud_save.py + storage_paths.py
# Di Godot: pakai user:// + Google Play Games via plugin (godot Google Play Games)
extends Node

const SAVE_PATH := "user://mystic_save.json"
var data: Dictionary = {
	"unlocked_heroes": ["kaizen","grimjaw","sylara","thorne","vex","zephyr"],
	"completed_levels": [],
	"gold": 0,
	"settings": {"sfx": 1.0, "bgm": 0.8, "quality": "medium"}
}

func _ready():
	load_save()

func load_save():
	if FileAccess.file_exists(SAVE_PATH):
		var f = FileAccess.open(SAVE_PATH, FileAccess.READ)
		var parsed = JSON.parse_string(f.get_as_text())
		if parsed is Dictionary:
			data.merge(parsed, true)
			print("[SaveManager] Loaded save: ", data)
	else:
		print("[SaveManager] No save, using defaults")

func save():
	var f = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	f.store_string(JSON.stringify(data, "\t"))
	print("[SaveManager] Saved")
	# TODO: integrate godot Google Play Games plugin for cloud save
	# if OS.has_feature("android"):
	#     GooglePlayGames.save_snapshot("mystic_save", data)

func unlock_hero(hero_type: String):
	if hero_type not in data["unlocked_heroes"]:
		data["unlocked_heroes"].append(hero_type)
		save()

func complete_level(lv: int):
	if lv not in data["completed_levels"]:
		data["completed_levels"].append(lv)
		save()

func is_unlocked(hero_type: String) -> bool:
	return hero_type in data["unlocked_heroes"]
