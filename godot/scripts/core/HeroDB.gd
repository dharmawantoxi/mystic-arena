# HeroDB.gd — Database 200+ hero, port dari _core.py + hero_archetypes.json
# Di Pygame: dict HERO_TYPES + ARCHETYPES. Di Godot: Resource + JSON loader.
extends Node

# Struktur data hero (mirip _core.py HERO_TYPES)
# Akan di-load dari res://data/heroes.json (hasil convert tools/convert_to_godot.py)
var heroes: Dictionary = {}
var archetypes: Dictionary = {}

func _ready():
	load_heroes()
	load_archetypes()

func load_heroes():
	var path = "res://data/heroes.json"
	if not FileAccess.file_exists(path):
		push_warning("[HeroDB] heroes.json belum ada. Jalankan tools/convert_to_godot.py")
		# Fallback: 6 starter hero hardcode (paritas _core.py)
		heroes = {
			"kaizen": {"name":"Kaizen","title":"Wind Blade","role":"Carry","hp":850,"damage":72,"speed":2.8,"range":70,"attack_cooldown":32,"color":"#ff5544","dmg_type":"PHYSICAL"},
			"grimjaw": {"name":"Grimjaw","title":"Blade Fury","role":"Fighter","hp":950,"damage":68,"speed":2.4,"range":65,"attack_cooldown":38,"color":"#ff6600","dmg_type":"PHYSICAL"},
			"sylara": {"name":"Sylara","title":"Wind Ranger","role":"Carry","hp":780,"damage":65,"speed":2.9,"range":180,"attack_cooldown":40,"color":"#44ff88","dmg_type":"PHYSICAL"},
			"thorne": {"name":"Thorne","title":"Quill Spray","role":"Tank","hp":1100,"damage":58,"speed":2.2,"range":60,"attack_cooldown":42,"color":"#88aa44","dmg_type":"PHYSICAL"},
			"vex": {"name":"Vex","title":"Harbringer of Void","role":"Mage","hp":800,"damage":62,"speed":2.6,"range":170,"attack_cooldown":36,"color":"#aa55ff","dmg_type":"MAGIC"},
			"zephyr": {"name":"Zephyr","title":"Fey Trickster","role":"Support","hp":820,"damage":60,"speed":2.7,"range":160,"attack_cooldown":38,"color":"#ff88cc","dmg_type":"MAGIC"},
		}
		return
	var f = FileAccess.open(path, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	heroes = data if data is Dictionary else {}
	print("[HeroDB] Loaded %d heroes" % heroes.size())

func load_archetypes():
	var path = "res://data/hero_archetypes.json"
	if FileAccess.file_exists(path):
		var f = FileAccess.open(path, FileAccess.READ)
		var parsed = JSON.parse_string(f.get_as_text())
		archetypes = parsed if parsed is Dictionary else {}
		print("[HeroDB] Loaded %d archetypes" % archetypes.size())

func get_hero(hero_type: String) -> Dictionary:
	return heroes.get(hero_type, {})

func get_all_types() -> Array:
	return heroes.keys()

# Balance pasif: melee buff (mirip _entity.py Hero.__init__)
func get_balanced_stats(hero_type: String) -> Dictionary:
	var s = get_hero(hero_type).duplicate()
	if s.is_empty():
		return {}
	# Melee = range < 110 -> buff +15% HP, +20% damage, +18% speed
	if s.get("range", 70) < 110:
		s["range"] = 70
		s["hp"] = int(s["hp"] * 1.15)
		s["damage"] = int(s["damage"] * 1.20)
		s["speed"] = s["speed"] * 1.18
		s["attack_cooldown"] = max(18, int(s["attack_cooldown"] * 0.88))
	else:
		s["range"] = clamp(s["range"], 120, 220)
	# Archetype dmg_type
	if hero_type in archetypes:
		s["dmg_type"] = archetypes[hero_type].get("dmg_type", s.get("dmg_type","PHYSICAL"))
		s["dmg_school"] = s["dmg_type"].to_lower()
	return s

func get_hero_color(hero_type: String) -> Color:
	var h = get_hero(hero_type)
	var c = h.get("color", "#ffffff")
	return Color(c)
