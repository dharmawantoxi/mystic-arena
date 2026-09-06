# GameManagerConnector.gd — Jembatan Main.tscn -> GameManager (autoload)
# GameManager menyimpan referensi container (hero/boss/minion/tower) yang
# "di-set oleh Main.tscn". Node ini yang melakukannya saat scene siap,
# lalu memulai level pertama.
extends Node

@export var containers_path: NodePath = ^"../Containers"
@export var start_level_on_ready: bool = true
@export var starting_level: int = 1

var _containers: Node = null

func _ready():
	_containers = get_node_or_null(containers_path)
	if _containers == null:
		push_warning("[GameManagerConnector] Node Containers tidak ditemukan: %s" % containers_path)
		return
	GameManager.hero_container = _containers.get_node_or_null(^"Heroes")
	GameManager.boss_container = _containers.get_node_or_null(^"Bosses")
	GameManager.minion_container = _containers.get_node_or_null(^"Minions")
	GameManager.tower_container = _containers.get_node_or_null(^"Towers")
	if start_level_on_ready:
		# call_deferred supaya level_started dipancarkan SETELAH seluruh _ready
		# selesai (parent/child) — pendengar signal (Main.gd, HUD.gd) dijamin siap.
		GameManager.start_level.call_deferred(starting_level)

func _exit_tree():
	# Cegah dangling reference di autoload saat Main scene di-unload
	if not is_instance_valid(_containers):
		return
	var hc = GameManager.hero_container
	if is_instance_valid(hc) and hc.get_parent() == _containers:
		GameManager.hero_container = null
		GameManager.boss_container = null
		GameManager.minion_container = null
		GameManager.tower_container = null
