# Headless smoke: menu boot → start level 1 → heroes + wave minions + AI lane pick.
# godot --headless --path godot res://tests/BattleSmokeTest.tscn --quit-after 180
# Require "[BattleSmokeTest] PASS" and no SCRIPT ERROR / Parse Error / Compile Error.
extends Node

const MainScene = preload("res://scenes/main.tscn")
const AIPlayerScript = preload("res://scripts/systems/AIPlayer.gd")

var _failures: int = 0
var _main = null
var _frames: int = 0
var _done: bool = false


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	GameManager.in_menu = true
	GameManager.state = "idle"
	_main = MainScene.instantiate()
	add_child(_main)
	# Let Main + Connector + MainMenu finish _ready.
	await get_tree().process_frame
	await get_tree().process_frame

	var menu = get_tree().get_first_node_in_group("main_menu")
	_expect(menu != null, "Main menu node must exist")
	var ai = _main.get("_ai")
	_expect(is_instance_valid(ai), "AIPlayer must exist after Main._ready")
	_expect(ai.get_script() == AIPlayerScript, "AIPlayer script must load")

	# Start level 1 the same way the menu does (via connector / play_requested).
	var connector := get_tree().get_first_node_in_group("game_connector")
	_expect(connector != null, "GameManagerConnector must be in group")
	if connector != null and connector.has_method("start_match"):
		connector.start_match(1)
	else:
		GameManager.start_level(1, false)

	# Wait until battle is playing and wave 1 has spawned.
	var guard := 0
	while guard < 90:
		await get_tree().process_frame
		guard += 1
		if GameManager.state == "playing" and GameManager.wave_number >= 1:
			var heroes := _count_group("heroes")
			var minions := _count_group("minions")
			var nexus := _count_group("nexus")
			if heroes >= 10 and minions >= 2 and nexus >= 2:
				break

	_expect(GameManager.state == "playing", "Level 1 must enter playing state")

	# Fase 3: bake map statik (tekstur tunggal dari renderer pygame) harus
	# AKTIF — asetnya ikut repo, jadi headless CI pun wajib memakainya dan
	# bukan fallback prosedural.
	var amap = get_tree().get_first_node_in_group("arena_map")
	_expect(amap != null, "ArenaMap must be in group arena_map")
	if amap != null:
		_expect(amap.procedural_fallback == false,
				"static map bake must be active (procedural_fallback == false)")
		_expect(amap._baked_map != null and amap._baked_map.visible,
				"BakedMap sprite must exist and be visible")

	# Fase 5d: level intro kini membekukan gameplay sampai SPACE/ENTER/klik.
	# Smoke test butuh combat berjalan -> skip lewat jalur input Main.
	var intro = _main.get("_level_intro")
	if is_instance_valid(intro) and intro.cinematic_active():
		var ev: InputEventKey = InputEventKey.new()
		ev.keycode = KEY_SPACE
		ev.pressed = true
		_main._on_key(ev)
		await get_tree().process_frame
		_expect(not get_tree().paused, "Skipping level intro must unpause the tree")
		_expect(not GameManager.is_paused, "Skipping level intro must resume gold/wave")
	else:
		_expect(false, "Level intro should be active after start_level")
	_expect(GameManager.level_number == 1, "Level number must be 1")
	_expect(GameManager.wave_number >= 1, "Wave 1 must have started")
	_expect(_count_group("heroes") >= 10, "Starter + enemy rosters must spawn heroes")
	_expect(_count_group("nexus") == 2, "Both nexuses must spawn")
	_expect(_count_group("minions") >= 2, "Wave must spawn minions for both teams")

	# Lane tags on live minions must be top/mid/bot (not empty).
	var lane_ok := true
	var lanes_seen := {}
	for m in get_tree().get_nodes_in_group("minions"):
		if not is_instance_valid(m) or bool(m.get("is_dead")):
			continue
		var lane := str(m.get("lane"))
		if not ["top", "mid", "bot"].has(lane):
			lane_ok = false
		lanes_seen[lane] = true
	_expect(lane_ok, "Every live minion must carry a valid lane")
	_expect(lanes_seen.size() >= 1, "At least one lane must be occupied")

	# AI red heroes idle without destination should pick a lane when threats exist.
	if is_instance_valid(ai):
		for h in get_tree().get_nodes_in_group("heroes"):
			if not is_instance_valid(h) or str(h.get("team")) != "red" or bool(h.get("is_dead")):
				continue
			if h.get("target") == null and not h.has_destination():
				ai._assign_hero_lane(h)
			if h.has_destination() or h.get("target") != null:
				break
		var any_assigned := false
		for h in get_tree().get_nodes_in_group("heroes"):
			if not is_instance_valid(h) or str(h.get("team")) != "red":
				continue
			if h.has_destination() or h.get("target") != null:
				any_assigned = true
				break
		# With minions on field, at least one red hero should have a destination or target.
		_expect(any_assigned or _count_group("minions") == 0,
			"AI should assign a lane/destination when blue minions exist")

	# Run a few combat frames to catch runtime SCRIPT ERRORs in AI/combat.
	for _i in range(30):
		await get_tree().process_frame

	_finish()


func _finish() -> void:
	if _done:
		return
	_done = true
	get_tree().paused = false
	GameManager.set_paused(false)
	if is_instance_valid(_main):
		_main.free()
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print("[BattleSmokeTest] PASS: menu → level 1 → heroes/minions/wave/AI")
	get_tree().quit(0 if _failures == 0 else 1)


func _count_group(group: String) -> int:
	var n := 0
	for node in get_tree().get_nodes_in_group(group):
		if is_instance_valid(node) and not bool(node.get("is_dead")):
			n += 1
	return n


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error("[BattleSmokeTest] " + message)
