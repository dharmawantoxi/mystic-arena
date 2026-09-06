# GameManagerConnector.gd — Jembatan Main.tscn -> GameManager (autoload)
# GameManager menyimpan referensi container (hero/boss/minion/tower) yang
# "di-set oleh Main.tscn". Node ini yang melakukannya saat scene siap,
# lalu memulai level pertama.
#
# Update sesi ini (menu utama + progresi level): starting_level TIDAK lagi
# hardcoded 1. Boot sekarang jatuh ke MENU UTAMA (GameManager.in_menu=true),
# jadi start_level_on_ready tidak menyala; MainMenu memanggil start_match(n)
# lewat grup "game_connector" — starting_level ikut tercatat di property ini
# supaya siapa pun yang memeriksa connector tahu level aktif.
extends Node

@export var containers_path: NodePath = ^"../Containers"
## Auto-start saat scene siap — DIMATIKAN kalau menu utama sedang terbuka
## (GameManager.in_menu). Dibiarkan true untuk scene uji tanpa menu
## (mis. menjalankan ulang connector sendiri).
@export var start_level_on_ready: bool = true
@export var starting_level: int = 1

var _containers: Node = null

func _ready():
	add_to_group("game_connector")
	_containers = get_node_or_null(containers_path)
	if _containers == null:
		push_warning("[GameManagerConnector] Node Containers tidak ditemukan: %s" % containers_path)
		return
	GameManager.hero_container = _containers.get_node_or_null(^"Heroes")
	GameManager.boss_container = _containers.get_node_or_null(^"Bosses")
	GameManager.minion_container = _containers.get_node_or_null(^"Minions")
	GameManager.tower_container = _containers.get_node_or_null(^"Towers")
	# FX (peluru menara, damage number) hidup di CanvasLayer sendiri supaya selalu
	# di atas unit — tanpa ini attach_fx() jatuh ke current_scene.
	GameManager.fx_container = _containers.get_parent().get_node_or_null(^"FX")
	if start_level_on_ready and not GameManager.in_menu:
		# call_deferred supaya level_started dipancarkan SETELAH seluruh _ready
		# selesai (parent/child) — pendengar signal (Main.gd, HUD.gd) dijamin siap.
		GameManager.start_level.call_deferred(starting_level)

## Dipanggil MainMenu (play_requested) via Main.gd: catat level pilihan pemain
## ke starting_level lalu mulai match. call_deferred supaya signal level_started
## tiba setelah seluruh pemicu input selesai (pola yang sama dengan _ready).
func start_match(level_num: int) -> void:
	starting_level = level_num
	GameManager.start_level.call_deferred(level_num, false)

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
