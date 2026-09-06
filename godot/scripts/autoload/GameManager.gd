# GameManager.gd — Autoload, port dari _core.py Game class
# Menggantikan Game loop pygame (60 FPS) dengan Godot SceneTree
extends Node

signal wave_started(wave_num: int)
signal boss_spawned(boss_type: String)
signal hero_died(hero: Node)
signal gold_changed(new_gold: int)

# State global (mirip _core.Game)
var level_number: int = 1
var wave_number: int = 1
var gold: int = 1000:
	set(v):
		gold = v
		gold_changed.emit(v)
var is_paused: bool = false

# Referensi node yang di-set oleh Main.tscn
var hero_container: Node
var boss_container: Node
var minion_container: Node
var tower_container: Node

# Config dari levels (port dari _core.NEXUS_LEVELS)
var starting_gold: int = 1000
var gold_per_second: float = 2.0

var _gold_timer: float = 0.0

func _process(delta):
	if is_paused:
		return
	# Passive gold (mirip _core.compute_gold_per_second)
	_gold_timer += delta
	if _gold_timer >= 1.0:
		_gold_timer = 0.0
		gold += int(gold_per_second)

func start_level(lv: int):
	level_number = lv
	var lv_data = BossDB.get_level(lv)
	starting_gold = lv_data.get("starting_gold", 1000)
	gold_per_second = lv_data.get("gold_per_second", 2.0)
	gold = starting_gold
	wave_number = 1
	print("[GameManager] Start Level %d — gold %d" % [lv, gold])

func spend_gold(amount: int) -> bool:
	if gold >= amount:
		gold -= amount
		return true
	return false

func spawn_hero(hero_type: String, team: String, pos: Vector2):
	var hero_scene = preload("res://scenes/hero/Hero.tscn")
	var hero = hero_scene.instantiate()
	hero.hero_type = hero_type
	hero.team = team
	hero.position = pos
	if hero_container:
		hero_container.add_child(hero)
	else:
		get_tree().current_scene.add_child(hero)
	return hero

func spawn_boss(boss_type: String, pos: Vector2):
	var boss_scene = preload("res://scenes/boss/Boss.tscn")
	var boss = boss_scene.instantiate()
	boss.boss_type = boss_type
	boss.position = pos
	if boss_container:
		boss_container.add_child(boss)
	else:
		get_tree().current_scene.add_child(boss)
	boss_spawned.emit(boss_type)
	return boss
