# HeroDB.gd — Database 200+ hero, port dari _core.py + hero_archetypes.json
# Di Pygame: dict HERO_TYPES + ARCHETYPES. Di Godot: Resource + JSON loader.
extends Node

# Struktur data hero (mirip _core.py HERO_TYPES)
# Akan di-load dari res://data/heroes.json (hasil convert tools/convert_to_godot.py)
var heroes: Dictionary = {}
var archetypes: Dictionary = {}
## Kurva level hero (HERO_LEVELS pygame) + MAX_HERO_LEVEL
var hero_levels: Dictionary = {}
var max_hero_level: int = 15
var boss_hero_upgrade_mult: float = 1.6

## Fallback HERO_LEVELS 1-5 (_core.py 557-568) kalau hero_levels.json belum ada
const FALLBACK_HERO_LEVELS: Dictionary = {
	1: {"hp_mult": 1.0, "dmg_mult": 1.0, "skill_mult": 1.0, "upgrade_cost": 300},
	2: {"hp_mult": 1.3, "dmg_mult": 1.25, "skill_mult": 1.2, "upgrade_cost": 500},
	3: {"hp_mult": 1.65, "dmg_mult": 1.55, "skill_mult": 1.45, "upgrade_cost": 800},
	4: {"hp_mult": 2.1, "dmg_mult": 1.9, "skill_mult": 1.75, "upgrade_cost": 1200},
	5: {"hp_mult": 2.7, "dmg_mult": 2.4, "skill_mult": 2.1, "upgrade_cost": 1800},
}

func _ready():
	load_heroes()
	load_archetypes()
	load_hero_levels()


func load_hero_levels():
	var path = "res://data/hero_levels.json"
	if not FileAccess.file_exists(path):
		push_warning("[HeroDB] hero_levels.json belum ada — upgrade hero dibatasi level 5")
		for k in FALLBACK_HERO_LEVELS:
			hero_levels[str(k)] = FALLBACK_HERO_LEVELS[k]
		max_hero_level = 5
		return
	var f = FileAccess.open(path, FileAccess.READ)
	var parsed = JSON.parse_string(f.get_as_text())
	if parsed is Dictionary:
		var lvls = parsed.get("levels")
		if lvls is Dictionary:
			hero_levels = lvls
		max_hero_level = int(parsed.get("max_level", 15))
		boss_hero_upgrade_mult = float(parsed.get("boss_hero_upgrade_cost_mult", 1.6))
	print("[HeroDB] Loaded %d hero levels (max %d)" % [hero_levels.size(), max_hero_level])


## {hp_mult, dmg_mult, skill_mult, upgrade_cost} untuk satu level hero
func level_data(level: int) -> Dictionary:
	var d = hero_levels.get(str(clampi(level, 1, max_hero_level)))
	if d is Dictionary:
		return d
	return FALLBACK_HERO_LEVELS.get(clampi(level, 1, 5), FALLBACK_HERO_LEVELS[1])


## Biaya upgrade hero ke level berikutnya (boss hero ×1.6)
func upgrade_cost(hero_type: String, level: int) -> int:
	if level >= max_hero_level:
		return 0
	var base := int(level_data(level).get("upgrade_cost", 0))
	if bool(get_hero(hero_type).get("is_boss_hero", false)):
		base = int(base * boss_hero_upgrade_mult)
	return base

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


## Katalog MENTAH heroes.json untuk HeroSkillKit (paritas
## settings.get_all_hero_types() — dipanggil handler lewat h.kit_catalog_all()).
func catalog_all() -> Dictionary:
	return heroes


## HERO_LEVELS pygame sebagai Dictionary INT-keyed (pygame index level-nya
## int; `hero_levels` hasil JSON loader string-keyed). Lewat h.kit_hero_levels().
func hero_levels_int() -> Dictionary:
	if not _levels_int_cache.is_empty():
		return _levels_int_cache
	for k in hero_levels.keys():
		_levels_int_cache[int(k)] = hero_levels[k]
	if _levels_int_cache.is_empty():
		for k in FALLBACK_HERO_LEVELS:
			_levels_int_cache[int(k)] = FALLBACK_HERO_LEVELS[k]
	return _levels_int_cache

var _levels_int_cache: Dictionary = {}

func get_all_types() -> Array:
	return heroes.keys()

## round() Python: half-to-even pada selisih > eps, dan untuk 0.5 eksak
## mengikuti perilaku data (floor di .5 — terverifikasi nol selisih pada
## seluruh katalog lewat tools/parity audit, 2026-09).
static func _py_round(v: float) -> int:
	var f := floorf(v)
	var diff := v - f
	if diff > 0.5:
		return int(f) + 1
	if diff < 0.5:
		return int(f)
	return int(f) if int(f) % 2 == 0 else int(f) + 1


## Enam starter pygame (hero_balance.py:102 STARTER_HEROES). HANYA mereka
## yang mendapat catch-up, dan mereka TIDAK dihitung sebagai "unlock" di
## boss_unlocks_for_purchases (hero_balance.py:257-260) — dipakai juga oleh
## GameManager.boss_unlocks_for_purchases.
const STARTER_HEROES: Array = ["kaizen", "grimjaw", "sylara", "thorne",
	"vex", "zephyr"]


## hero_balance.starter_catchup (hero_balance.py 226-246): pengali
## (hp, damage) — SATU-SATUNYA jalur base_hp/base_damage hero. Mendelegasikan
## ke HeroBalance (satu-satunya sumber kebenaran rumus balance).
## PENTING (temuan audit 2026-09): di _entity.py Hero.__init__, blok melee
## (x1.15 HP / x1.20 dmg) DITIMPA ulang oleh panggilan catchup yang membaca
## katalog MENTAH — jadi untuk semua hero non-starter hasilnya = angka mentah
## (x1.0), dan untuk starter = bonus catch-up. Speed/range/cd melee TETAP
## ter-buff. Karena itu get_balanced_stats di bawah tidak lagi mengubah
## hp/damage; nilai final datang dari catchup_base().
static func starter_catchup_mults(hero_type: String, boss_unlocks: int,
		level: int) -> Vector2:
	return HeroBalance.starter_catchup(hero_type, boss_unlocks, level)


## (base_hp, base_damage) final ala starter_catchup_stats pygame — inputnya
## katalog MENTAH heroes.json (bukan hasil buff melee). Instance method
## karena membaca `heroes` autoload. Mendelegasikan ke HeroBalance.
func catchup_base(hero_type: String, boss_unlocks: int, level: int) -> Vector2i:
	var raw: Dictionary = heroes.get(hero_type, {})
	if raw.is_empty():
		return Vector2i(1, 1)
	return HeroBalance.starter_catchup_stats(hero_type, raw, boss_unlocks,
		level)


# Balance pasif: melee buff (mirip _entity.py Hero.__init__)
func get_balanced_stats(hero_type: String) -> Dictionary:
	var s = get_hero(hero_type).duplicate()
	if s.is_empty():
		return {}
	# Melee = range < 110 -> buff speed/range/cd SAJA (hp/damage ditimpa
	# catchup_base — lihat komentar starter_catchup_mults di atas).
	if s.get("range", 70) < 110:
		s["range"] = 70
		# Mirror PERSIS `round(speed * 1.18, 2)` di _entity.py:3308 —
		# Python membulat pembulatan desimal dari nilai biner produk
		# (1.25*1.18 = 1.4749999999999999777 -> 1.47). Pendekatan lama
		# `_py_round(speed*118)/100` membulatkan 147.5 -> 148 -> 1.48
		# (bug khalros final.speed di HeroSkillParityTest, 2026-09-08).
		# String.num(prec=2) memakai dtoa yang sama dgn CPython
		# (round-half-even atas nilai desimal eksak double tsb).
		s["speed"] = String.num(float(s["speed"]) * 1.18, 2).to_float()
		s["attack_cooldown"] = maxi(18, _py_round(float(s["attack_cooldown"]) * 0.88))
	else:
		s["range"] = clampf(float(s["range"]), 120.0, 220.0)
	# Archetype dmg_type -> dmg_school (dipakai CombatSystem/DamageSchool dan
	# ItemInventory.is_magic untuk item magic_only). heroes.json sendiri selalu
	# "PHYSICAL"; sekolah sihir yang benar ada di tabel arketipe (120 MAGIC).
	# Port hero_archetypes.get_archetype(hero_type) TANPA stats: "dmg_type" di
	# heroes.json hanyalah default converter, BUKAN override desain — kalau
	# diteruskan sebagai `stats`, semua hero MAGIC terpaksa jadi PHYSICAL.
	var _arch: Dictionary = HeroArchetypes.get_archetype(hero_type)
	s["dmg_type"] = str(_arch.get("dmg_type", "PHYSICAL"))
	# Selalu isi dmg_school walau hero tidak ada di archetype (entry default
	# berisi PHYSICAL — jangan biarkan pemanggil bergantung pada kunci yang
	# bisa hilang).
	s["dmg_school"] = s["dmg_type"].to_lower()
	return s

func get_hero_color(hero_type: String) -> Color:
	var h = get_hero(hero_type)
	var c = h.get("color", "#ffffff")
	return Color(c)
