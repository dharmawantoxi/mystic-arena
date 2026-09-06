# Main.gd — akar dari scenes/main.tscn
#
# Kenapa file ini ada: main.tscn sebelumnya tidak punya script root sama sekali.
# GameManagerConnector hanya menyambungkan container + memanggil start_level(),
# dan GameManager.start_level() hanya print + emit signal. Tidak ada satu node pun
# yang punya visual -> viewport menampilkan clear color (0.04, 0.04, 0.07) yang
# kelihatan sebagai "layar hitam" saat F5.
#
# Tugas Main.gd:
#   1. membingkai kamera ke arena 1280x720 (kamera di (0,0) membuat basis radiant
#      di y ~ 620 keluar layar),
#   2. menukar tema map dari levels.json["map_theme"],
#   3. men-spawn roster starter 6 hero + 1 mini boss supaya arena langsung hidup,
#   4. tombol debug: R = respawn roster, T = ganti tema, SPASI = beli 1 hero blue.
extends Node2D

## Roster radiant (kiri-bawah) — paritas SaveManager.unlocked_heroes
const STARTER_ROSTER: Array = ["kaizen", "grimjaw", "sylara", "thorne", "vex", "zephyr"]
## Roster dire (kanan-atas) — cerminan supaya brawl seimbang
const ENEMY_ROSTER: Array = ["grimjaw", "thorne", "vex", "zephyr", "sylara", "kaizen"]
## Mini boss pertama level 1 (levels.json["mini_bosses"]["10"]) — HP 7500, masih killable
const DEMO_BOSS: String = "gornak"
## Sebaran lane minion per index (biar arena kelihatan MOBA, bukan 1 garis lurus)
const LANES: Array = ["mid", "top", "bot"]

@export var spawn_demo_boss: bool = true
@export var respawn_after_wipe: bool = true
@export var respawn_delay: float = 3.0
## true = kamera mengikuti pusat pertempuran, false = kamera diam membingkai arena
@export var camera_follows_action: bool = false

var _arena_map = null
var _camera: Camera2D = null
var _respawn_pending: bool = false

func _enter_tree():
	# _enter_tree (bukan _ready): parent didahulukan, jadi kita tetap kebagian
	# signal level_started walau Connector memanggil start_level() di _ready()-nya.
	_connect_once(GameManager.level_started, _on_level_started)
	_connect_once(GameManager.wave_started, _on_wave_started)
	_connect_once(GameManager.hero_died, _on_hero_died)

func _exit_tree():
	# GameManager itu autoload -> umurnya lebih panjang dari scene. Putuskan supaya
	# reload scene tidak meninggalkan connection ganda / dangling reference.
	if GameManager.level_started.is_connected(_on_level_started):
		GameManager.level_started.disconnect(_on_level_started)
	if GameManager.wave_started.is_connected(_on_wave_started):
		GameManager.wave_started.disconnect(_on_wave_started)
	if GameManager.hero_died.is_connected(_on_hero_died):
		GameManager.hero_died.disconnect(_on_hero_died)

static func _connect_once(sig: Signal, p_callable: Callable) -> void:
	if not sig.is_connected(p_callable):
		sig.connect(p_callable)

func _ready():
	_arena_map = get_node_or_null(^"ArenaMap")
	_camera = get_node_or_null(^"Camera2D")
	_frame_camera()
	# Tetap dapat kunci walau SceneTree di-pause (P/ESC). Karena anak men-inherit,
	# node yang mensimulasikan unit harus dipaksa PAUSABLE supaya get_tree().paused
	# sungguh-sungguh membekukan hero/minion.
	process_mode = Node.PROCESS_MODE_ALWAYS
	for path in ["Containers", "ArenaMap"]:
		var node := get_node_or_null(path)
		if node != null:
			node.process_mode = Node.PROCESS_MODE_PAUSABLE

func _on_wave_started(wave_num: int) -> void:
	# Komposisi per wave ada di GameManager (port NEXUS_WAVE_COMPOSITION); Main yang
	# memutuskan POSISI-nya karena Main yang punya ArenaMap / layout lane.
	var comp: Array = GameManager.wave_composition(wave_num)
	var spawned := 0
	for i in range(comp.size()):
		var lane: String = LANES[i % LANES.size()]
		if GameManager.count_alive("minions", "blue") < GameManager.max_minions_per_team:
			GameManager.spawn_minion(comp[i], "blue", _spawn_point("blue", i, lane))
			spawned += 1
		if GameManager.count_alive("minions", "red") < GameManager.max_minions_per_team:
			GameManager.spawn_minion(comp[i], "red", _spawn_point("red", i, lane))
			spawned += 1
	print("[Main] wave %d -> %d minion (mid/top/bot)" % [wave_num, spawned])

func _on_level_started(level_num: int) -> void:
	var lv: Dictionary = BossDB.get_level(level_num)
	if not lv.is_empty() and _arena_map != null and _arena_map.has_method("apply_theme"):
		_arena_map.apply_theme(str(lv.get("map_theme", "forest")))
	# call_deferred: pastikan seluruh _ready (termasuk container si Connector) selesai
	_start_battle.call_deferred()

func _start_battle() -> void:
	_clear_field()
	for i in range(STARTER_ROSTER.size()):
		GameManager.spawn_hero(STARTER_ROSTER[i], "blue", _spawn_point("blue", i))
	for i in range(ENEMY_ROSTER.size()):
		GameManager.spawn_hero(ENEMY_ROSTER[i], "red", _spawn_point("red", i))
	var bosses := 0
	if spawn_demo_boss and not DEMO_BOSS.is_empty():
		GameManager.spawn_boss(DEMO_BOSS, "red", _spawn_point("red", ENEMY_ROSTER.size() + 1))
		bosses = 1
	print("[Main] spawn %d hero + %d boss (arena harusnya tidak hitam lagi)" % [
		STARTER_ROSTER.size() + ENEMY_ROSTER.size(), bosses])

func _clear_field() -> void:
	for group in ["heroes", "bosses"]:
		for n in get_tree().get_nodes_in_group(group):
			if is_instance_valid(n):
				n.queue_free()

func _spawn_point(team: String, index: int, lane: String = "mid") -> Vector2:
	if _arena_map != null and _arena_map.has_method("get_spawn_point"):
		return _arena_map.get_spawn_point(team, index, lane)
	# fallback kalau ArenaMap tidak ada (scene ditelakkan sendiri di project lain)
	var side := Vector2(260, 480) if team == "blue" else Vector2(1020, 240)
	return side + Vector2(0, float(index % 3) * 26.0)

func _frame_camera() -> void:
	if _camera == null:
		return
	var size := _arena_size()
	# Viewport selalu berpusat di kamera -> pusatkan ke arena, lalu kunci limit
	# supaya kamera tidak bisa keluar dari map.
	_camera.position = size / 2.0
	_camera.limit_left = 0
	_camera.limit_top = 0
	_camera.limit_right = int(size.x)
	_camera.limit_bottom = int(size.y)
	_camera.reset_smoothing()

## ArenaMap.arena_size, dengan fallback — `.get()` dipakai (bukan `"x" in node`)
## supaya tidak bergantung pada operator `in` untuk Object.
func _arena_size() -> Vector2:
	if _arena_map != null:
		var got = _arena_map.get("arena_size")
		if got is Vector2:
			return got
	return Vector2(1280, 720)

func _process(_delta: float) -> void:
	if camera_follows_action and not get_tree().paused:
		_follow_action()

func _follow_action() -> void:
	if _camera == null:
		return
	var center := Vector2.ZERO
	var n := 0
	for hero in get_tree().get_nodes_in_group("heroes"):
		if is_instance_valid(hero) and not hero.is_dead:
			center += hero.global_position
			n += 1
	if n == 0:
		return
	var size := _arena_size()
	var focus := center / float(n)
	_camera.global_position = focus.clamp(
		Vector2(size.x / 2.0 - 120.0, size.y / 2.0 - 60.0),
		Vector2(size.x / 2.0 + 120.0, size.y / 2.0 + 60.0))

# ═══ respawn roster setelah satu tim disapu bersih (arena tidak pernah kosong) ═══
func _on_hero_died(_hero: Node) -> void:
	if not respawn_after_wipe or _respawn_pending:
		return
	var blue := _alive_count("blue")
	var red := _alive_count("red")
	if blue > 0 and red > 0:
		return
	_respawn_pending = true
	var loser := "Radiant (blue)" if blue == 0 else "Dire (red)"
	print("[Main] %s habis — roster di-respawn dalam %.1fs" % [loser, respawn_delay])
	await get_tree().create_timer(respawn_delay).timeout
	_respawn_pending = false
	if is_inside_tree():
		_start_battle()

func _alive_count(team: String) -> int:
	var n := 0
	for hero in get_tree().get_nodes_in_group("heroes"):
		if is_instance_valid(hero) and hero.has_method("take_damage") and not hero.is_dead \
				and hero.team == team:
			n += 1
	return n

# ═══ tombol debug (sengaja keycode mentah, tidak mengubah input map project.godot) ═══
func _unhandled_key_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed:
		return
	match key.keycode:
		KEY_R:
			_start_battle()
		KEY_T:
			_cycle_theme()
		KEY_SPACE:
			_buy_random_hero()
		KEY_P, KEY_ESCAPE:
			_toggle_pause()

func _toggle_pause() -> void:
	get_tree().paused = not get_tree().paused
	GameManager.set_paused(get_tree().paused)
	print("[Main] %s" % ("PAUSE (tree beku)" if get_tree().paused else "RESUME"))

func _cycle_theme() -> void:
	if _arena_map == null or not _arena_map.has_method("cycle_theme"):
		return
	print("[Main] tema map -> %s" % _arena_map.cycle_theme())

func _buy_random_hero() -> void:
	var types: Array = HeroDB.get_all_types()
	if types.is_empty():
		return
	var pick: String = types[randi() % types.size()]
	var cost := int(HeroDB.get_hero(pick).get("cost", 400))
	if not GameManager.spend_gold(cost):
		print("[Main] gold tidak cukup: %s butuh %d" % [pick, cost])
		return
	GameManager.spawn_hero(pick, "blue", _spawn_point("blue", 0))
	print("[Main] beli %s (-%d gold)" % [pick, cost])
