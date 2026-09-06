# Main.gd — akar dari scenes/main.tscn
#
# Kenapa file ini ada: main.tscn sebelumnya tidak punya script root sama sekali.
# GameManagerConnector hanya menyambungkan container + memanggil start_level(),
# dan GameManager.start_level() hanya print + emit signal. Tidak ada satu node pun
# yang punya visual -> viewport menampilkan clear color (0.04, 0.04, 0.07) yang
# kelihatan sebagai "layar hitam" saat F5.
#
# Tugas Main.gd sekarang (port sisi "Game" dari _core.py yang butuh pengetahuan
# layout map — GameManager tetap memegang state, Main yang memegang medan):
#   1. membingkai kamera ke arena 1280x720,
#   2. menukar tema map dari levels.json["map_theme"],
#   3. spawn 2 NEXUS (Radiant/Dire) -> match bisa MENANG/KALAH,
#   4. bangun 18 SLOT menara dari lane path (paritas
#      Game._generate_build_slots_from_lanes) + menggambarnya,
#   5. spawn roster starter 6 hero per tim, hero blue pertama jadi milik pemain
#      (QWER + toko),
#   6. jadwal boss: mini boss per wave (levels.json["mini_bosses"]) dan true boss
#      setelah 6 menara Dire hancur (paritas _core.py 2089),
#   7. AI tim red membangun/meng-upgrade menara memakai GameManager.ai_gold,
#   8. input: klik = pilih unit/slot, QWER = skill, B = toko, D = difficulty,
#      ENTER = mulai ulang setelah menang/kalah, P/ESC = pause,
#      F1 = debug respawn roster, T = ganti tema, SPASI = beli hero random.
extends Node2D

## Roster radiant (kiri-bawah) — paritas SaveManager.unlocked_heroes
const STARTER_ROSTER: Array = ["kaizen", "grimjaw", "sylara", "thorne", "vex", "zephyr"]
## Roster dire (kanan-atas) — cerminan supaya brawl seimbang
const ENEMY_ROSTER: Array = ["grimjaw", "thorne", "vex", "zephyr", "sylara", "kaizen"]
## Sebaran lane minion per index (biar arena kelihatan MOBA, bukan 1 garis lurus)
const LANES: Array = ["mid", "top", "bot"]
## Urutan lane saat membuat slot bangun (paritas pygame: top, mid, bot)
const LANE_ORDER: Array = ["top", "mid", "bot"]
## Fraksi posisi sepanjang lane path — angka persis dari _core.py 1660-1676
const LANE_SLOT_PCT := {
	"top": {"blue": [0.15, 0.30, 0.45], "red": [0.85, 0.70, 0.55]},
	"mid": {"blue": [0.10, 0.25, 0.40], "red": [0.90, 0.75, 0.60]},
	"bot": {"blue": [0.15, 0.30, 0.45], "red": [0.85, 0.70, 0.55]},
}
## Menara Dire yang harus hancur sebelum true boss turun (paritas _core.py 2089)
const TRUE_BOSS_TOWER_KILLS := 6

@export var respawn_after_wipe: bool = true
@export var respawn_delay: float = 3.0
## true = kamera mengikuti pusat pertempuran, false = kamera diam membingkai arena
@export var camera_follows_action: bool = false
## Selang antar keputusan AI (tim red) untuk membangun/meng-upgrade menara
@export var ai_think_interval: float = 5.0
## Peluang AI benar-benar memakai gold-nya tiap siklus (0..1)
@export var ai_aggression: float = 0.9
## Boss demo langsung turun saat battle mulai — dimatikan default karena sekarang
## ada jadwal mini boss/true boss sungguhan dari levels.json.
@export var spawn_demo_boss: bool = false
@export var demo_boss_type: String = "gornak"

var _arena_map = null
var _camera: Camera2D = null
## Node2D khusus menggambar slot bangun (anak Main digambar SETELAH Main, jadi
## _draw() milik Main sendiri akan tertutup ArenaMap)
var _slot_layer: Node2D = null
var _respawn_pending: bool = false
var _ai_timer: float = 0.0
var _slot_redraw_timer: float = 0.0
var _slot_pulse: float = 0.0

## Jadwal boss level ini (port Game.pending_mini_bosses / true_boss_spawned)
var pending_mini_bosses: Array = []
var active_boss = null
var red_towers_destroyed: int = 0
var true_boss_spawned: bool = false

func _enter_tree():
	# _enter_tree (bukan _ready): parent didahulukan, jadi kita tetap kebagian
	# signal level_started walau Connector memanggil start_level() di _ready()-nya.
	_connect_once(GameManager.level_started, _on_level_started)
	_connect_once(GameManager.wave_started, _on_wave_started)
	_connect_once(GameManager.hero_died, _on_hero_died)
	_connect_once(GameManager.game_over, _on_game_over)
	_connect_once(GameManager.tower_destroyed, _on_tower_destroyed)
	_connect_once(GameManager.selection_changed, _on_selection_changed)
	add_to_group("main")

func _exit_tree():
	# GameManager itu autoload -> umurnya lebih panjang dari scene. Putuskan supaya
	# reload scene tidak meninggalkan connection ganda / dangling reference.
	for pair in [[GameManager.level_started, _on_level_started],
			[GameManager.wave_started, _on_wave_started],
			[GameManager.hero_died, _on_hero_died],
			[GameManager.game_over, _on_game_over],
			[GameManager.tower_destroyed, _on_tower_destroyed],
			[GameManager.selection_changed, _on_selection_changed]]:
		var sig: Signal = pair[0]
		if sig.is_connected(pair[1]):
			sig.disconnect(pair[1])

static func _connect_once(sig: Signal, p_callable: Callable) -> void:
	if not sig.is_connected(p_callable):
		sig.connect(p_callable)

func _ready():
	_arena_map = get_node_or_null(^"ArenaMap")
	_camera = get_node_or_null(^"Camera2D")
	_frame_camera()
	_build_slot_layer()
	# Tetap dapat kunci walau SceneTree di-pause (P/ESC). Karena anak men-inherit,
	# node yang mensimulasikan unit harus dipaksa PAUSABLE supaya get_tree().paused
	# sungguh-sungguh membekukan hero/minion.
	process_mode = Node.PROCESS_MODE_ALWAYS
	for path in ["Containers", "ArenaMap"]:
		var node := get_node_or_null(path)
		if node != null:
			node.process_mode = Node.PROCESS_MODE_PAUSABLE
	if _slot_layer != null:
		_slot_layer.process_mode = Node.PROCESS_MODE_PAUSABLE

func _build_slot_layer() -> void:
	_slot_layer = Node2D.new()
	_slot_layer.name = "SlotLayer"
	# di atas map (ArenaMap z 0), di bawah unit
	_slot_layer.z_index = 1
	# CanvasItem punya signal `draw` -> gambar slot tanpa perlu subclass baru
	_slot_layer.draw.connect(_draw_slots)
	add_child(_slot_layer)

# ══════════════════════════════════════════════════════════
#  LEVEL / BATTLE
# ══════════════════════════════════════════════════════════

func _on_level_started(level_num: int) -> void:
	var lv: Dictionary = BossDB.get_level(level_num)
	if not lv.is_empty() and _arena_map != null and _arena_map.has_method("apply_theme"):
		_arena_map.apply_theme(str(lv.get("map_theme", "forest")))
	# call_deferred: pastikan seluruh _ready (termasuk container si Connector) selesai
	_start_battle.call_deferred()

func _start_battle() -> void:
	_respawn_pending = false
	_clear_field()
	_reset_boss_schedule()
	_spawn_nexuses()
	_generate_build_slots()
	for i in range(STARTER_ROSTER.size()):
		GameManager.spawn_hero(STARTER_ROSTER[i], "blue", _base_spawn("blue", i))
	for i in range(ENEMY_ROSTER.size()):
		GameManager.spawn_hero(ENEMY_ROSTER[i], "red", _base_spawn("red", i))
	if spawn_demo_boss and not demo_boss_type.is_empty():
		active_boss = GameManager.spawn_boss(demo_boss_type, "red",
			_spawn_point("red", ENEMY_ROSTER.size() + 1))
	# Hero pertama Radiant = milik pemain (QWER + item + upgrade lewat toko)
	var first = _first_blue_hero()
	if first != null:
		GameManager.select_hero(first)
	else:
		GameManager.clear_selection()
	GameManager.close_shop()
	_on_selection_changed()
	print("[Main] battle siap: %d hero, 2 nexus, %d slot menara" % [
		STARTER_ROSTER.size() + ENEMY_ROSTER.size(), GameManager.build_slots.size()])

## `free()` langsung (bukan `queue_free()`): arena harus sudah bersih SEBELUM
## unit baru di-spawn pada frame yang sama, kalau tidak _first_blue_hero() bisa
## memilih hero lama yang masih menunggu dihapus di akhir frame.
## Aman karena _start_battle selalu jalan dari deferred call / input / timer,
## tidak pernah dari dalam _physics_process unit.
func _clear_field() -> void:
	for group in ["heroes", "bosses", "minions", "towers", "nexus", "bullets"]:
		for n in get_tree().get_nodes_in_group(group):
			if is_instance_valid(n):
				n.free()
	GameManager.blue_nexus = null
	GameManager.red_nexus = null
	GameManager.clear_selection()

func _reset_boss_schedule() -> void:
	pending_mini_bosses.clear()
	active_boss = null
	red_towers_destroyed = 0
	true_boss_spawned = false
	_ai_timer = 0.0

## Nexus = kondisi menang/kalah (paritas Castle di _entity.py)
func _spawn_nexuses() -> void:
	for team in ["blue", "red"]:
		var nexus = GameManager.spawn_nexus(team, _base_center(team))
		GameManager.register_nexus(nexus)

## Slot bangun menara: 3 lane x 3 slot x 2 tim = 18 slot
func _generate_build_slots() -> void:
	GameManager.clear_build_slots()
	if _arena_map == null or not _arena_map.has_method("get_lane_path"):
		return
	for lane in LANE_ORDER:
		var path: PackedVector2Array = _arena_map.get_lane_path(str(lane))
		if path.size() == 0:
			continue
		var pct_table: Dictionary = LANE_SLOT_PCT.get(str(lane), {})
		for team in ["blue", "red"]:
			for pct in pct_table.get(team, []):
				var idx := clampi(int(path.size() * float(pct)), 0, path.size() - 1)
				GameManager.add_build_slot(path[idx], str(team), str(lane))

func _on_wave_started(wave_num: int) -> void:
	# Komposisi per wave ada di GameManager (port NEXUS_WAVE_COMPOSITION); Main yang
	# memutuskan POSISI-nya karena Main yang punya ArenaMap / layout lane.
	var comp: Array = GameManager.wave_composition(wave_num)
	var scale := GameManager.minion_scale_for(wave_num)
	var spawned := 0
	for i in range(comp.size()):
		var lane: String = LANES[i % LANES.size()]
		if GameManager.count_alive("minions", "blue") < GameManager.max_minions_per_team:
			GameManager.spawn_minion(comp[i], "blue", _spawn_point("blue", i, lane), scale)
			spawned += 1
		if GameManager.count_alive("minions", "red") < GameManager.max_minions_per_team:
			GameManager.spawn_minion(comp[i], "red", _spawn_point("red", i, lane), scale)
			spawned += 1
	_queue_mini_boss(wave_num)
	print("[Main] wave %d -> %d minion (skala %.2fx) | menara hancur: %d" % [
		wave_num, spawned, scale, red_towers_destroyed])

## Mini boss level ini masuk antrean begitu wave-nya lewat (paritas _core 1745)
func _queue_mini_boss(wave_num: int) -> void:
	var lv: Dictionary = BossDB.get_level(GameManager.level_number)
	var mini: Dictionary = lv.get("mini_bosses", {})
	var key := str(wave_num)
	if not mini.has(key):
		return
	var boss_type := str(mini[key])
	if boss_type.is_empty() or pending_mini_bosses.has(boss_type):
		return
	pending_mini_bosses.append(boss_type)
	print("[Main] mini boss %s masuk antrean (wave %d)" % [boss_type, wave_num])

func _boss_tick(_delta: float) -> void:
	if GameManager.state != "playing":
		return
	if active_boss != null:
		if not is_instance_valid(active_boss) or bool(active_boss.get("is_dead")):
			active_boss = null
		else:
			return # satu boss aktif pada satu waktu, sama seperti pygame
	if not pending_mini_bosses.is_empty():
		var boss_type: String = pending_mini_bosses.pop_front()
		active_boss = GameManager.spawn_boss(boss_type, "red",
			_spawn_point("red", ENEMY_ROSTER.size() + 1))
		print("[Main] MINI BOSS %s turun ke mid lane" % boss_type)
		return
	if not true_boss_spawned and red_towers_destroyed >= TRUE_BOSS_TOWER_KILLS:
		var lv: Dictionary = BossDB.get_level(GameManager.level_number)
		var true_boss := str(lv.get("true_boss", ""))
		if true_boss.is_empty():
			return
		active_boss = GameManager.spawn_boss(true_boss, "red",
			_spawn_point("red", ENEMY_ROSTER.size() + 1))
		true_boss_spawned = true
		print("[Main] TRUE BOSS %s turun (%d menara Dire hancur)" % [
			true_boss, red_towers_destroyed])

## AI tim red: menabung di GameManager.ai_gold, dibelanjakan di sini
func _ai_tick(delta: float) -> void:
	if GameManager.state != "playing":
		return
	_ai_timer += delta
	if _ai_timer < ai_think_interval:
		return
	_ai_timer = 0.0
	if randf() > ai_aggression:
		return
	GameManager.ai_try_build_or_upgrade()

# ══════════════════════════════════════════════════════════
#  POSISI
# ══════════════════════════════════════════════════════════

func _base_center(team: String) -> Vector2:
	if _arena_map != null and _arena_map.has_method("get_own_base"):
		return _arena_map.get_own_base(team)
	return Vector2(150, 590) if team == "blue" else Vector2(1130, 130)

func _spawn_point(team: String, index: int, lane: String = "mid") -> Vector2:
	if _arena_map != null and _arena_map.has_method("get_spawn_point"):
		return _arena_map.get_spawn_point(team, index, lane)
	# fallback kalau ArenaMap tidak ada (scene ditelakkan sendiri di project lain)
	var side := Vector2(260, 480) if team == "blue" else Vector2(1020, 240)
	return side + Vector2(0, float(index % 3) * 26.0)

## Formasi setengah lingkaran di depan base sendiri (bukan menumpuk di 1 titik)
func _base_spawn(team: String, index: int) -> Vector2:
	var center := _base_center(team)
	var dir := Vector2(1, -0.45).normalized() if team == "blue" else Vector2(-1, 0.45).normalized()
	var spread := float(index) * 0.42 - 1.05
	var angle := spread * 0.9
	var offset := dir.rotated(angle) * (74.0 + float(index % 2) * 22.0)
	return center + offset

func _first_blue_hero():
	for h in get_tree().get_nodes_in_group("heroes"):
		if is_instance_valid(h) and str(h.get("team")) == "blue" and not bool(h.get("is_dead")):
			return h
	return null

# ══════════════════════════════════════════════════════════
#  KAMERA
# ══════════════════════════════════════════════════════════

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

func _process(delta: float) -> void:
	# Main PROCESS_MODE_ALWAYS (supaya P/ESC bisa resume) -> jadwal boss, AI, dan
	# redraw slot harus ikut beku saat pause.
	if get_tree().paused:
		return
	_boss_tick(delta)
	_ai_tick(delta)
	_slot_pulse += delta
	# redraw slot 10x/detik: cukup halus untuk pulse, jauh lebih murah dari 60fps
	_slot_redraw_timer += delta
	if _slot_layer != null and _slot_redraw_timer >= 0.1:
		_slot_redraw_timer = 0.0
		_slot_layer.queue_redraw()
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

# ══════════════════════════════════════════════════════════
#  GAMBAR SLOT BANGUN
# ══════════════════════════════════════════════════════════

func _draw_slots() -> void:
	if _slot_layer == null:
		return
	var slot_r := maxf(14.0, TowerDB.slot_size())
	var pulse := 0.5 + 0.5 * sin(_slot_pulse * 3.2)
	for i in range(GameManager.build_slots.size()):
		var s: Dictionary = GameManager.build_slots[i]
		if bool(s["taken"]):
			continue # menara yang berdiri sudah menggambar dirinya sendiri
		var pos: Vector2 = s["pos"]
		var is_blue := str(s["team"]) == "blue"
		var col := Color(0.35, 0.68, 1.0, 0.55) if is_blue else Color(1.0, 0.35, 0.35, 0.4)
		_slot_layer.draw_arc(pos, slot_r, 0.0, TAU, 24, col, 2.0)
		# tanda "+" supaya jelas ini slot kosong, bukan dekorasi
		_slot_layer.draw_line(pos + Vector2(-slot_r * 0.5, 0), pos + Vector2(slot_r * 0.5, 0), col, 2.0)
		_slot_layer.draw_line(pos + Vector2(0, -slot_r * 0.5), pos + Vector2(0, slot_r * 0.5), col, 2.0)
		if i == GameManager.selected_slot:
			var glow := Color(1.0, 0.87, 0.35, 0.25 + 0.25 * pulse)
			_slot_layer.draw_circle(pos, slot_r + 3.0, glow)
			_slot_layer.draw_arc(pos, slot_r + 3.0, 0.0, TAU, 28,
				Color(1.0, 0.87, 0.35, 0.9), 2.5)

# ══════════════════════════════════════════════════════════
#  SELEKSI (klik) + INPUT
# ══════════════════════════════════════════════════════════

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			_on_click(get_global_mouse_position())
		return
	if event is InputEventKey:
		_on_key(event as InputEventKey)

func _on_key(key: InputEventKey) -> void:
	if not key.pressed or key.echo:
		return
	# P/ESC dicek paling awal: justru dibutuhkan untuk RESUME saat tree di-pause
	if key.keycode == KEY_P or key.keycode == KEY_ESCAPE:
		if GameManager.shop_open:
			GameManager.close_shop()
		else:
			_toggle_pause()
		return
	if get_tree().paused:
		return # sisa aksi adalah aksi gameplay -> ikut beku
	# Skill hero terpilih — action sudah ada di project.godot (Q/W/E/R)
	if key.is_action_pressed("skill_q"):
		_cast_skill("q")
		return
	if key.is_action_pressed("skill_w"):
		_cast_skill("w")
		return
	if key.is_action_pressed("skill_e"):
		_cast_skill("e")
		return
	if key.is_action_pressed("skill_r"):
		_cast_skill("r")
		return
	if key.is_action_pressed("toggle_shop"):
		GameManager.toggle_shop()
		print("[Main] toko %s" % ("dibuka (B)" if GameManager.shop_open else "ditutup"))
		return
	if key.is_action_pressed("cycle_difficulty"):
		print("[Main] difficulty -> %s" % GameManager.cycle_difficulty())
		return
	if key.is_action_pressed("restart_match"):
		if GameManager.state != "playing":
			GameManager.restart_match()
		return
	if key.is_action_pressed("debug_respawn"):
		# restart penuh: gold, wave, state menang/kalah, nexus, dan slot direset
		GameManager.restart_match()
		return
	match key.keycode:
		KEY_T:
			_cycle_theme()
		KEY_SPACE:
			_buy_random_hero()

func _cast_skill(slot_key: String) -> void:
	var h = GameManager.selected_hero
	if h == null or not is_instance_valid(h) or bool(h.get("is_dead")):
		print("[Main] pilih hero Radiant dulu (klik) sebelum memakai skill %s" % slot_key.to_upper())
		return
	if str(h.get("team")) != "blue":
		return
	if h.has_method("cast_" + slot_key):
		h.call("cast_" + slot_key)

func _on_click(pos: Vector2) -> void:
	if GameManager.state != "playing" or get_tree().paused:
		return
	# Prioritas klik: hero -> menara -> nexus -> slot bangun -> tanah kosong
	var h = _pick_in_group("heroes", pos, 10.0)
	if h != null:
		if str(h.get("team")) == "blue":
			GameManager.select_hero(h)
		else:
			GameManager.clear_selection() # hero musuh: lihat HP-nya saja, tidak dipilih
		return
	var t = _pick_in_group("towers", pos, 12.0)
	if t != null:
		GameManager.select_tower(t)
		if str(t.get("team")) == "blue":
			GameManager.open_shop()
		return
	var nx = _pick_in_group("nexus", pos, 0.0)
	if nx != null:
		GameManager.select_nexus(nx)
		if str(nx.get("team")) == "blue":
			GameManager.open_shop()
		return
	var slot_idx := _pick_slot(pos)
	if slot_idx >= 0:
		GameManager.select_slot_index(slot_idx)
		GameManager.open_shop()
		return
	GameManager.clear_selection()
	GameManager.close_shop()

## Unit terdekat dalam radius klik. `pad` menambah radius bawaan unit.
func _pick_in_group(group: String, pos: Vector2, pad: float):
	var best = null
	var best_dist := 1e9
	for n in get_tree().get_nodes_in_group(group):
		if not is_instance_valid(n) or bool(n.get("is_dead")):
			continue
		var node := n as Node2D
		if node == null:
			continue
		var r := float(n.get("radius")) if n.get("radius") != null else 16.0
		var d := pos.distance_to(node.global_position)
		if d <= maxf(8.0, r + pad) and d < best_dist:
			best_dist = d
			best = n
	return best

func _pick_slot(pos: Vector2) -> int:
	var best := -1
	var best_dist := 1e9
	var reach := maxf(20.0, TowerDB.slot_size() + 8.0)
	for i in range(GameManager.build_slots.size()):
		var s: Dictionary = GameManager.build_slots[i]
		if bool(s["taken"]):
			continue # slot terisi -> kliknya ditangkap menara
		var d: float = pos.distance_to(s["pos"])
		if d <= reach and d < best_dist:
			best_dist = d
			best = i
	return best

## Sinkronkan flag `selected` di unit + highlight slot tiap kali pilihan berubah
func _on_selection_changed() -> void:
	var hero = GameManager.selected_hero
	if hero != null and not is_instance_valid(hero):
		hero = null
		GameManager.selected_hero = null
	for h in get_tree().get_nodes_in_group("heroes"):
		if not is_instance_valid(h) or not h.has_method("set_selected"):
			continue
		var is_pick := (h == hero)
		h.set_selected(is_pick)
		if "player_controlled" in h:
			h.player_controlled = is_pick and str(h.get("team")) == "blue"
	for t in get_tree().get_nodes_in_group("towers"):
		if is_instance_valid(t) and "selected" in t:
			t.selected = (t == GameManager.selected_tower)
	for n in get_tree().get_nodes_in_group("nexus"):
		if is_instance_valid(n) and "selected" in n:
			n.selected = (n == GameManager.selected_nexus)
	if _slot_layer != null:
		_slot_layer.queue_redraw()

# ══════════════════════════════════════════════════════════
#  EVENT PERTANDINGAN
# ══════════════════════════════════════════════════════════

func _on_tower_destroyed(tower: Node, _killer_team: String) -> void:
	if tower == null or not is_instance_valid(tower):
		return
	# Slot kembali kosong supaya bisa dibangun ulang (paritas pygame)
	for s in GameManager.build_slots:
		if s.get("tower") == tower:
			s["taken"] = false
			s["tower"] = null
	if GameManager.selected_tower == tower:
		GameManager.clear_selection()
	if str(tower.get("team")) == "red":
		red_towers_destroyed += 1
		print("[Main] menara Dire hancur: %d/%d menuju true boss" % [
			red_towers_destroyed, TRUE_BOSS_TOWER_KILLS])

func _on_game_over(victory: bool) -> void:
	_respawn_pending = true # jangan respawn roster lagi: match sudah selesai
	GameManager.clear_selection()
	GameManager.close_shop()
	print("[Main] %s — tekan ENTER untuk main lagi" % ("MENANG" if victory else "KALAH"))

# ═══ respawn roster setelah satu tim disapu bersih (arena tidak pernah kosong) ═══
func _on_hero_died(_hero: Node) -> void:
	if not respawn_after_wipe or _respawn_pending:
		return
	if GameManager.state != "playing":
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
	if is_inside_tree() and GameManager.state == "playing":
		_start_battle()

func _alive_count(team: String) -> int:
	var n := 0
	for hero in get_tree().get_nodes_in_group("heroes"):
		if is_instance_valid(hero) and hero.has_method("take_damage") and not hero.is_dead \
				and hero.team == team:
			n += 1
	return n

# ═══ debug / util ═══
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
	if GameManager.try_buy_hero(pick):
		return
	print("[Main] gagal beli %s (gold %d)" % [pick, GameManager.gold])
