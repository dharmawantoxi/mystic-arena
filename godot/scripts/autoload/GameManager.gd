# GameManager.gd — Autoload, port dari _core.py Game class
# Menggantikan Game loop pygame (60 FPS) dengan Godot SceneTree
extends Node

signal level_started(level_num: int)
signal wave_started(wave_num: int)
signal boss_spawned(boss_type: String)
signal hero_died(hero: Node)
signal gold_changed(new_gold: int)
signal minion_died(minion: Node, killer_team: String)

# ═══ MINION_TYPES — port persis dari _core.py (warna = GRASS/GOBLIN_COLOR dkk) ═══
const MINION_TYPES: Dictionary = {
	"goblin": {"name": "Goblin", "hp": 45, "damage": 5, "speed": 1.5, "range": 25,
		"attack_cooldown": 45, "gold_reward": 8, "radius": 9, "color": "#64b450"},
	"orc": {"name": "Orc", "hp": 110, "damage": 13, "speed": 0.95, "range": 30,
		"attack_cooldown": 60, "gold_reward": 18, "radius": 12, "color": "#c8643c"},
	"troll": {"name": "Troll", "hp": 320, "damage": 18, "speed": 0.65, "range": 28,
		"attack_cooldown": 75, "gold_reward": 45, "radius": 14, "color": "#648caa",
		"armor": 2, "magic_resist": 0.05},
	"undead": {"name": "Undead", "hp": 65, "damage": 11, "speed": 0.85, "range": 100,
		"attack_cooldown": 60, "gold_reward": 16, "radius": 10, "color": "#c8c8dc",
		"armor": 0, "magic_resist": 0.15},
	"dark_rider": {"name": "Dark Rider", "hp": 280, "damage": 32, "speed": 2.0, "range": 35,
		"attack_cooldown": 50, "gold_reward": 65, "radius": 13, "color": "#643c8c",
		"armor": 1, "magic_resist": 0.05},
}

# ═══ NEXUS_WAVE_COMPOSITION — port dari _core.py (wave 1-5; setelahnya di-scale) ═══
const WAVE_COMPOSITION: Dictionary = {
	1: ["goblin", "goblin", "goblin"],
	2: ["goblin", "goblin", "goblin", "orc"],
	3: ["goblin", "orc", "goblin", "orc", "undead"],
	4: ["orc", "goblin", "orc", "undead", "goblin", "goblin"],
	5: ["orc", "orc", "undead", "troll", "goblin", "goblin"],
}
## Wave > 5: komposisi di-mirror dari wave 5 + dark_rider (mirip "minion_scale naik")
const LATE_WAVE_MIX: Array = ["orc", "undead", "troll", "goblin", "dark_rider", "orc"]

# State global (mirip _core.Game)
var level_number: int = 1
var wave_number: int = 1
var gold: int = 1000:
	set(v):
		gold = v
		gold_changed.emit(v)
var is_paused: bool = false

# Referensi node yang di-set oleh Main.tscn (lewat GameManagerConnector)
var hero_container: Node
var boss_container: Node
var minion_container: Node
var tower_container: Node

# Config dari levels (port dari _core.NEXUS_LEVELS)
var starting_gold: int = 1000
var gold_per_second: float = 2.0

# Gelombang minion — paritas _core.MINION_WAVE_INTERVAL = 1500 frame @60fps
@export var waves_enabled: bool = true
@export var wave_interval: float = 25.0
@export var max_minions_per_team: int = 24

var _gold_timer: float = 0.0
var _wave_timer: float = 0.0
var _hit_stop_active: bool = false
var _hit_stop_until_ms: int = 0

func _ready():
	# Autoload harus tetap jalan walau SceneTree di-pause (P/ESC dari Main.gd):
	# watchdog Engine.time_scale tinggal di sini. Flag is_paused sudah menahan
	# timer gold/wave, jadi "pause" tetap benar.
	process_mode = Node.PROCESS_MODE_ALWAYS

func _process(delta):
	# Watchdog hit-stop DULU: Engine.time_scale tidak boleh bisa "nyangkut" kecil
	_watch_hit_stop()
	if is_paused:
		return
	# Passive gold (mirip _core.compute_gold_per_second)
	_gold_timer += delta
	if _gold_timer >= 1.0:
		_gold_timer = 0.0
		gold += int(gold_per_second)
	# Wave timer -> emit wave_started, yang spawn-nya ditangani scene (Main.gd)
	if waves_enabled and get_tree().current_scene != null:
		_wave_timer += delta
		if _wave_timer >= wave_interval:
			_wave_timer = 0.0
			next_wave()

func start_level(lv: int):
	level_number = lv
	var lv_data = BossDB.get_level(lv)
	starting_gold = lv_data.get("starting_gold", 1000)
	gold_per_second = lv_data.get("gold_per_second", 2.0)
	gold = starting_gold
	wave_number = 0
	_gold_timer = 0.0
	_wave_timer = 0.0
	print("[GameManager] Start Level %d — gold %d" % [lv, gold])
	level_started.emit(lv)
	next_wave() # wave 1 langsung jalan -> arena terisi begitu scene siap

func next_wave() -> void:
	wave_number += 1
	print("[GameManager] Wave %d" % wave_number)
	wave_started.emit(wave_number)

## Komposisi minion untuk wave ini (sudah di-scale untuk wave > 5)
func wave_composition(wave: int) -> Array:
	if WAVE_COMPOSITION.has(wave):
		return WAVE_COMPOSITION[wave].duplicate()
	# Late game: ulang LATE_WAVE_MIX, tambah 1 unit tiap 2 wave (maks 10 per tim)
	var reps := clampi(1 + (wave - 5) / 2, 1, 2)
	var out: Array = []
	for _r in reps:
		out.append_array(LATE_WAVE_MIX)
	while out.size() > 10:
		out.remove_at(out.size() - 1)
	return out

func spend_gold(amount: int) -> bool:
	if gold >= amount:
		gold -= amount
		return true
	return false

func award_kill(killer_team: String, amount: int) -> void:
	# Hanya tim pemain (blue/radiant) yang menabung — paritas _core.py
	if killer_team == "blue":
		gold += amount

func spawn_hero(hero_type: String, team: String, pos: Vector2):
	var hero_scene = preload("res://scenes/hero/Hero.tscn")
	var hero = hero_scene.instantiate()
	hero.hero_type = hero_type
	hero.team = team
	hero.position = pos
	(container_or_root(hero_container)).add_child(hero)
	return hero

func spawn_boss(boss_type: String, team: String, pos: Vector2):
	var boss_scene = preload("res://scenes/boss/Boss.tscn")
	var boss = boss_scene.instantiate()
	boss.boss_type = boss_type
	boss.team = team
	boss.position = pos
	(container_or_root(boss_container)).add_child(boss)
	boss_spawned.emit(boss_type)
	return boss

func spawn_minion(minion_type: String, team: String, pos: Vector2) -> Node2D:
	var minion_scene = preload("res://scenes/minion/Minion.tscn")
	var m = minion_scene.instantiate()
	m.minion_type = minion_type
	m.team = team
	m.position = pos
	(container_or_root(minion_container)).add_child(m)
	return m

## Container dari Main.tscn bisa belum terpasang (scene lain / sebelum Connector
## jalan). Jangan pernah null-crash: fallback ke current_scene, lalu root.
func container_or_root(container: Node) -> Node:
	if container != null and is_instance_valid(container):
		return container
	var scene := get_tree().current_scene
	if scene != null:
		return scene
	return get_tree().root

func count_alive(group: String, team: String) -> int:
	var n := 0
	for node in get_nodes_in_group(group):
		if is_instance_valid(node) and node.get("team") == team and not bool(node.get("is_dead")):
			n += 1
	return n

# ═══ Hit-stop service (dipakai Hero/Boss; TIDAK await di node unit) ═══
# Kalau time-scale diputar di node yang lalu queue_free (mati saat attack),
# Engine.time_scale bisa tertinggal 0.05 -> game kelihatan freeze. Di autoload
# ini selalu ada watchdog real-time, jadi tidak mungkin macet.
func request_hit_stop(duration: float = 0.03, scale: float = 0.05) -> void:
	if _hit_stop_active:
		return
	_hit_stop_active = true
	_hit_stop_until_ms = Time.get_ticks_msec() + maxi(5, int(duration * 1000.0))
	Engine.time_scale = scale

func _watch_hit_stop() -> void:
	if not _hit_stop_active:
		return
	if Time.get_ticks_msec() >= _hit_stop_until_ms:
		_hit_stop_active = false
		Engine.time_scale = 1.0

## Dipanggil Main.gd (P / ESC). Yang membekukan simulasi adalah SceneTree, jadi
## flag ini cuma status untuk yang butuh tahu (mis. HUD / audio).
func set_paused(value: bool) -> void:
	is_paused = value
