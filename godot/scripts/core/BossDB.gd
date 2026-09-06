# BossDB.gd — Port dari bosses/boss_data.py + levels/level_data.py
extends Node

var bosses: Dictionary = {}
var levels: Array = []

func _ready():
	load_bosses()
	load_levels()

func load_bosses():
	var path = "res://data/bosses.json"
	if not FileAccess.file_exists(path):
		push_warning("[BossDB] bosses.json belum ada. Jalankan tools/convert_to_godot.py")
		bosses = {
			"gornak": {"name":"Gornak","title":"Warrior Against Magic","hp":3000,"damage":55,"speed":1.2,"range":50,"boss_class":"mini","color":"#aa50d2"},
			"morgath": {"name":"Morgath","title":"Temporal Protector","hp":5000,"damage":60,"speed":0.7,"range":180,"boss_class":"mini","color":"#8c64dc"},
			"drakar": {"name":"Drakar","title":"Red Mist","hp":8000,"damage":80,"speed":1.0,"range":55,"boss_class":"mini","color":"#dc3c3c"},
		}
		return
	var f = FileAccess.open(path, FileAccess.READ)
	var parsed = JSON.parse_string(f.get_as_text())
	bosses = parsed if parsed is Dictionary else {}
	print("[BossDB] Loaded %d bosses" % bosses.size())

func load_levels():
	var path = "res://data/levels.json"
	if FileAccess.file_exists(path):
		var f = FileAccess.open(path, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		levels = data if data is Array else []
		print("[BossDB] Loaded %d levels" % levels.size())

func get_boss(boss_type: String) -> Dictionary:
	return bosses.get(boss_type, {})

func get_level(level_num: int) -> Dictionary:
	for lv in levels:
		if lv.get("level_number") == level_num:
			return lv
	return {}
