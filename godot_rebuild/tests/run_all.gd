extends SceneTree
## Native, dependency-free headless regression runner. Exit code 1 means failure.

const ThorneChecks = preload("res://tests/thorne_checks.gd")
const GrimjawChecks = preload("res://tests/grimjaw_checks.gd")
const AlchemistChecks = preload("res://tests/alchemist_checks.gd")
const SourceSharedBossChecks = preload("res://tests/source_shared_boss_checks.gd")
const HeroStatusChecks = preload("res://tests/hero_status_checks.gd")
const BossLevelOneChecks = preload("res://tests/boss_level_one_checks.gd")
const BossLevelThreeChecks = preload("res://tests/boss_level_three_checks.gd")
const BossLevelFourChecks = preload("res://tests/boss_level_four_checks.gd")
const BossLevelFiveChecks = preload("res://tests/boss_level_five_checks.gd")
const BossLevelSixChecks = preload("res://tests/boss_level_six_checks.gd")
const BossLevelSevenChecks = preload("res://tests/boss_level_seven_checks.gd")
const BossLevelNineChecks = preload("res://tests/boss_level_nine_checks.gd")
const BossLevelTenChecks = preload("res://tests/boss_level_ten_checks.gd")
const BossLevelElevenChecks = preload("res://tests/boss_level_eleven_checks.gd")
const BossLevelTwelveChecks = preload("res://tests/boss_level_twelve_checks.gd")
const BossLevelThirteenChecks = preload("res://tests/boss_level_thirteen_checks.gd")
const BossLevelFourteenChecks = preload("res://tests/boss_level_fourteen_checks.gd")
const BossLevelFifteenChecks = preload("res://tests/boss_level_fifteen_checks.gd")
const BossLevelSixteenChecks = preload("res://tests/boss_level_sixteen_checks.gd")
const BossLevelSeventeenChecks = preload("res://tests/boss_level_seventeen_checks.gd")
const BossLevelEighteenChecks = preload("res://tests/boss_level_eighteen_checks.gd")
const BossLevelNineteenChecks = preload("res://tests/boss_level_nineteen_checks.gd")
const BossLevelTwentyChecks = preload("res://tests/boss_level_twenty_checks.gd")
const StarterFinishChecks = preload("res://tests/starter_finish_checks.gd")
const SylaraChecks = preload("res://tests/sylara_checks.gd")
const AIRecruitChecks = preload("res://tests/ai_recruit_checks.gd")
const PlayerRecruitChecks = preload("res://tests/player_recruit_checks.gd")
const PlayerRecruitSceneChecks = preload("res://tests/player_recruit_scene_checks.gd")
const MetaHeroUnlockChecks = preload("res://tests/meta_hero_unlock_checks.gd")
const MetaHeroUnlockSceneChecks = preload("res://tests/meta_hero_unlock_scene_checks.gd")
const AIBuildChecks = preload("res://tests/ai_build_checks.gd")
const AIShieldChecks = preload("res://tests/ai_shield_checks.gd")
const AIShieldSceneChecks = preload("res://tests/ai_shield_scene_checks.gd")
const AIUpgradeChecks = preload("res://tests/ai_upgrade_checks.gd")
const AIPriorityChecks = preload("res://tests/ai_priority_checks.gd")
const AIItemChecks = preload("res://tests/ai_item_checks.gd")
const ForgeSceneChecks = preload("res://tests/forge_scene_checks.gd")
const AIDraftChecks = preload("res://tests/ai_draft_checks.gd")
const AIPolicyChecks = preload("res://tests/ai_policy_checks.gd")
const AIControlTickChecks = preload("res://tests/ai_control_tick_checks.gd")
const AIRosterChecks = preload("res://tests/ai_roster_checks.gd")
const CannonSceneChecks = preload("res://tests/cannon_scene_checks.gd")
const IceSceneChecks = preload("res://tests/ice_scene_checks.gd")
const MageSceneChecks = preload("res://tests/mage_scene_checks.gd")
const KaizenSceneChecks = preload("res://tests/kaizen_scene_checks.gd")
const NexusSceneChecks = preload("res://tests/nexus_scene_checks.gd")
const NexusChecks = preload("res://tests/nexus_checks.gd")
const CannonChecks = preload("res://tests/cannon_checks.gd")
const IceChecks = preload("res://tests/ice_checks.gd")
const MageChecks = preload("res://tests/mage_checks.gd")
const KaizenChecks = preload("res://tests/kaizen_checks.gd")
const UpgradeSceneChecks = preload("res://tests/upgrade_scene_checks.gd")
const UpgradeChecks = preload("res://tests/upgrade_checks.gd")
const PrototypeChecks = preload("res://tests/prototype_checks.gd")
const BossCoreChecks = preload("res://tests/boss_core_checks.gd")
const BossAbilityChecks = preload("res://tests/boss_ability_checks.gd")
const BossMatchChecks = preload("res://tests/boss_match_checks.gd")
const BossMotionChecks = preload("res://tests/boss_motion_checks.gd")
const BossClockChecks = preload("res://tests/boss_clock_checks.gd")
const BossDebuffClockChecks = preload("res://tests/boss_debuff_clock_checks.gd")
const BossKillCreditChecks = preload("res://tests/boss_kill_credit_checks.gd")
const BossStructureTargetsChecks = preload("res://tests/boss_structure_targets_checks.gd")
const BossMinionTargetsChecks = preload("res://tests/boss_minion_targets_checks.gd")
const BossPhaseOrderChecks = preload("res://tests/boss_phase_order_checks.gd")
const BossIceAoeChecks = preload("res://tests/boss_ice_aoe_checks.gd")
const BossTowerDamageChecks = preload("res://tests/boss_tower_damage_checks.gd")
const BossCannonSplashChecks = preload("res://tests/boss_cannon_splash_checks.gd")
const BossIceMainSlowChecks = preload("res://tests/boss_ice_main_slow_checks.gd")
const BossTowerVolleyChecks = preload("res://tests/boss_tower_volley_checks.gd")
const BossAbilitySourceAttributionChecks = preload(
	"res://tests/boss_ability_source_attribution_checks.gd"
)
const BossItemStunChecks = preload("res://tests/boss_item_stun_checks.gd")
const BossItemSilenceChecks = preload("res://tests/boss_item_silence_checks.gd")
const BossItemSlowChecks = preload("res://tests/boss_item_slow_checks.gd")
const BossItemAuraChecks = preload("res://tests/boss_item_aura_checks.gd")
const BossPolycephalyChecks = preload("res://tests/boss_polycephaly_checks.gd")
const BossMiasmaChecks = preload("res://tests/boss_miasma_checks.gd")
const BossMiasmaBlindChecks = preload("res://tests/boss_miasma_blind_checks.gd")
const BossMiasmaKillCreditChecks = preload("res://tests/boss_miasma_kill_credit_checks.gd")
const BossItemCleaveChainChecks = preload("res://tests/boss_item_cleave_chain_checks.gd")
const BossItemCleaveDamageChecks = preload("res://tests/boss_item_cleave_damage_checks.gd")
const BossItemBashDamageChecks = preload("res://tests/boss_item_bash_damage_checks.gd")
const BossItemMagicDamageChecks = preload("res://tests/boss_item_magic_damage_checks.gd")
const BossItemAutoMagicDamageChecks = preload("res://tests/boss_item_auto_magic_damage_checks.gd")
const BossItemReflectCarapaceChecks = preload("res://tests/boss_item_reflect_carapace_checks.gd")
const BossHeroAIChecks = preload("res://tests/boss_hero_ai_checks.gd")
const BossPresentationChecks = preload("res://tests/boss_presentation_checks.gd")
const SiegeChecks = preload("res://tests/siege_checks.gd")
const CombatChecks = preload("res://tests/combat_checks.gd")
const LevelCatalogChecks = preload("res://tests/level_catalog_checks.gd")
const LevelThemeChecks = preload("res://tests/level_theme_checks.gd")
const RiverTilesChecks = preload("res://tests/river_tiles_checks.gd")
const LaneTilesChecks = preload("res://tests/lane_tiles_checks.gd")
const WallTilesChecks = preload("res://tests/wall_tiles_checks.gd")
const TerrainTilesChecks = preload("res://tests/terrain_tiles_checks.gd")
const LevelProgressChecks = preload("res://tests/level_progress_checks.gd")
const LevelProgressStoreChecks = preload("res://tests/level_progress_store_checks.gd")
const LevelProgressStore = preload("res://scripts/match/level_progress_store.gd")
const SCENE_PROGRESS_PATH := "user://level_progress_scene_test.json"
const APP = preload("res://app/App.tscn")
const SIMULATION = preload("res://scripts/simulation/sandbox_simulation.gd")

var failures: Array[String] = []
var checks := 0
# Per-prefix failure histogram printed after the final summary so the CI
# annotation (which keeps the last 60 log lines) names every failing area.
var failure_groups: Dictionary = {}


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		printerr("FAIL: " + message)
		var key := _failure_key(message)
		failure_groups[key] = int(failure_groups.get(key, 0)) + 1


func _failure_key(message: String) -> String:
	var words: PackedStringArray = message.split(" ", false)
	var head: Array[String] = []
	for index in range(mini(3, words.size())):
		head.append(words[index])
	return " ".join(head)


func _settle() -> void:
	await process_frame
	await process_frame
	await process_frame


func _physics_steps(count: int) -> void:
	for index in range(count):
		await physics_frame
	await process_frame


func _run() -> void:
	_check(Engine.physics_ticks_per_second == 60, "physics frequency is 60 Hz")
	LevelCatalogChecks.new().run(_check)
	LevelThemeChecks.new().run(_check)
	RiverTilesChecks.new().run(_check)
	LaneTilesChecks.new().run(_check)
	WallTilesChecks.new().run(_check)
	TerrainTilesChecks.new().run(_check)
	LevelProgressChecks.new().run(_check)
	LevelProgressStoreChecks.new().run(_check)
	ThorneChecks.new().run(_check)
	GrimjawChecks.new().run(_check)
	SylaraChecks.new().run(_check)
	StarterFinishChecks.new().run(_check)
	BossLevelOneChecks.new().run(_check)
	BossLevelThreeChecks.new().run(_check)
	BossLevelFourChecks.new().run(_check)
	BossLevelFiveChecks.new().run(_check)
	BossLevelSixChecks.new().run(_check)
	BossLevelSevenChecks.new().run(_check)
	BossLevelNineChecks.new().run(_check)
	BossLevelTenChecks.new().run(_check)
	BossLevelElevenChecks.new().run(_check)
	BossLevelTwelveChecks.new().run(_check)
	BossLevelThirteenChecks.new().run(_check)
	BossLevelFourteenChecks.new().run(_check)
	BossLevelFifteenChecks.new().run(_check)
	BossLevelSixteenChecks.new().run(_check)
	BossLevelSeventeenChecks.new().run(_check)
	BossLevelEighteenChecks.new().run(_check)
	BossLevelNineteenChecks.new().run(_check)
	BossLevelTwentyChecks.new().run(_check)
	HeroStatusChecks.new().run(_check)
	SourceSharedBossChecks.new().run(_check)
	AlchemistChecks.new().run(_check)
	AIRecruitChecks.new().run(_check)
	PlayerRecruitChecks.new().run(_check)
	MetaHeroUnlockChecks.new().run(_check)
	AIBuildChecks.new().run(_check)
	AIShieldChecks.new().run(_check)
	AIUpgradeChecks.new().run(_check)
	AIPriorityChecks.new().run(_check)
	AIItemChecks.new().run(_check)
	AIDraftChecks.new().run(_check)
	AIPolicyChecks.new().run(_check)
	AIControlTickChecks.new().run(_check)
	AIRosterChecks.new().run(_check)
	_test_simulation()
	CombatChecks.new().run(_check)
	SiegeChecks.new().run(_check)
	BossCoreChecks.new().run(_check)
	BossAbilityChecks.new().run(_check)
	BossMatchChecks.new().run(_check)
	BossMotionChecks.new().run(_check)
	BossClockChecks.new().run(_check)
	BossDebuffClockChecks.new().run(_check)
	BossKillCreditChecks.new().run(_check)
	BossStructureTargetsChecks.new().run(_check)
	BossMinionTargetsChecks.new().run(_check)
	BossPhaseOrderChecks.new().run(_check)
	BossIceAoeChecks.new().run(_check)
	BossTowerDamageChecks.new().run(_check)
	BossCannonSplashChecks.new().run(_check)
	BossIceMainSlowChecks.new().run(_check)
	BossTowerVolleyChecks.new().run(_check)
	BossAbilitySourceAttributionChecks.new().run(_check)
	BossItemStunChecks.new().run(_check)
	BossItemSilenceChecks.new().run(_check)
	BossItemSlowChecks.new().run(_check)
	BossItemAuraChecks.new().run(_check)
	BossItemCleaveChainChecks.new().run(_check)
	BossItemCleaveDamageChecks.new().run(_check)
	BossItemBashDamageChecks.new().run(_check)
	BossItemMagicDamageChecks.new().run(_check)
	BossItemAutoMagicDamageChecks.new().run(_check)
	BossItemReflectCarapaceChecks.new().run(_check)
	BossPolycephalyChecks.new().run(_check)
	BossMiasmaChecks.new().run(_check)
	BossMiasmaBlindChecks.new().run(_check)
	BossMiasmaKillCreditChecks.new().run(_check)
	BossHeroAIChecks.new().run(_check)
	BossPresentationChecks.new().run(_check)
	PrototypeChecks.new().run(_check)
	UpgradeChecks.new().run(_check)
	NexusChecks.new().run(_check)
	CannonChecks.new().run(_check)
	IceChecks.new().run(_check)
	MageChecks.new().run(_check)
	KaizenChecks.new().run(_check)
	var app = APP.instantiate()
	root.add_child(app)
	await _settle()
	_check(app.current_screen.name == "MainMenu", "application boots into menu")
	var menu_child_count: int = app.current_screen.get_child_count()
	var menu_tree_count: int = root.get_tree().get_node_count()
	for cycle in range(10):
		app.current_screen.get_node("%PlayButton").pressed.emit()
		# Double activation in the same frame must not install two screens.
		app.current_screen.get_node("%PlayButton").pressed.emit()
		await _settle()
		_check(app.screen_root.get_child_count() == 1, "single match screen, cycle %d" % cycle)
		_check(app.current_screen.name == "Match", "play opens match, cycle %d" % cycle)
		var match_screen = app.current_screen
		var sim = match_screen.simulation
		sim.set_physics_process(false)
		_check(sim.probe_position == SIMULATION.SPAWN, "fresh probe position")
		_check(not sim.is_selected and not sim.has_move_target, "fresh input state")
		sim.select_at(sim.probe_position)
		_check(sim.command_move(Vector2(600, 400)), "selected marker accepts destination")
		sim.set_physics_process(true)
		var before: int = sim.tick_count
		await _physics_steps(4)
		_check(sim.tick_count > before, "physics advances while running")
		match_screen.get_node("%PauseButton").pressed.emit()
		_check(paused and match_screen.pause_overlay.visible, "pause shows overlay and stops tree")
		_check(not sim.has_move_target, "pause cancels pending movement")
		before = sim.tick_count
		await _physics_steps(4)
		_check(sim.tick_count == before, "physics does not advance during pause")
		match_screen.get_node("%ResumeButton").pressed.emit()
		_check(
			not paused and not match_screen.pause_overlay.visible, "resume clears overlay and pause"
		)
		await _physics_steps(4)
		_check(sim.tick_count > before, "physics resumes")
		# Background notification must have the same cleanup policy as manual pause.
		app.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
		_check(paused, "focus loss pauses match")
		var old_id: int = match_screen.get_instance_id()
		var old_sim_id: int = sim.get_instance_id()
		match_screen.get_node("%RestartButton").pressed.emit()
		await _settle()
		_check(not paused, "restart clears global pause")
		_check(not is_instance_id_valid(old_id), "old match freed on restart")
		_check(not is_instance_id_valid(old_sim_id), "old simulation freed on restart")
		_check(
			app.current_screen.simulation.probe_position == SIMULATION.SPAWN,
			"restart resets movement"
		)
		_check(not app.current_screen.simulation.is_selected, "restart resets selection")
		_check(app.screen_root.get_child_count() == 1, "restart leaves one screen")
		app.current_screen.pause_match()
		old_id = app.current_screen.get_instance_id()
		app.current_screen.get_node("%MenuButton").pressed.emit()
		await _settle()
		_check(not paused, "return to menu unpauses tree")
		_check(not is_instance_id_valid(old_id), "match freed on return to menu")
		_check(app.current_screen.name == "MainMenu", "menu restored")
		_check(app.current_screen.get_child_count() == menu_child_count, "menu structure stable")
		_check(app.screen_root.get_child_count() == 1, "single menu instance")
		_check(
			root.get_tree().get_node_count() == menu_tree_count,
			"node count stable after full cycle"
		)
	await _test_input(app)
	await _test_combat_scene(app)
	await _test_siege_scene(app)
	await _test_prototype_scene(app)
	await _test_level_selection_scene(app)
	await MetaHeroUnlockSceneChecks.new().run(self, app, _check)
	await PlayerRecruitSceneChecks.new().run(self, app, _check)
	await ForgeSceneChecks.new().run(self, app, _check)
	await AIShieldSceneChecks.new().run(self, app, _check)
	await UpgradeSceneChecks.new().run(self, app, _check)
	await NexusSceneChecks.new().run(self, app, _check)
	await CannonSceneChecks.new().run(self, app, _check)
	await IceSceneChecks.new().run(self, app, _check)
	await MageSceneChecks.new().run(self, app, _check)
	await KaizenSceneChecks.new().run(self, app, _check)
	app.queue_free()
	await _settle()
	_check(not paused, "app exit does not leave tree paused")
	if failures.is_empty():
		print(
			(
				"PASS: %d checks; fixed ticks, source parity, combat/siege/prototype, input and lifecycle."
				% checks
			)
		)
		quit(0)
	else:
		printerr("FAILED: %d of %d checks" % [failures.size(), checks])
		_report_failure_groups()
		quit(1)


func _report_failure_groups() -> void:
	var keys: Array = failure_groups.keys()
	keys.sort()
	for key: String in keys:
		printerr("FAIL-GROUP: %s x%d" % [key, int(failure_groups[key])])


func _test_simulation() -> void:
	var first = SIMULATION.new()
	var second = SIMULATION.new()
	_check(not first.command_move(Vector2(400, 300)), "unselected probe rejects move")
	first.select_at(SIMULATION.SPAWN)
	_check(first.is_selected, "select within hit radius")
	_check(not first.command_move(Vector2(-10, -10)), "out of bounds move rejected")
	_check(first.command_move(SIMULATION.SPAWN + Vector2(30, 0)), "valid move accepted")
	for index in range(10):
		first.step_tick()
	_check(
		first.probe_position == SIMULATION.SPAWN + Vector2(30, 0),
		"3 pixels per tick, 10 ticks = 30 pixels"
	)
	_check(not first.has_move_target, "movement stops exactly at target")
	for index in range(590):
		first.step_tick()
	_check(first.tick_count == 600, "600 explicit steps are 600 ticks")
	_check(
		second.tick_count == 0 and second.probe_position == SIMULATION.SPAWN,
		"instances have independent state"
	)
	first.select_at(Vector2(1000, 400))
	_check(not first.is_selected, "click away deselects")
	first.free()
	second.free()


func _test_input(app: Node) -> void:
	app.start_match()
	await _settle()
	var match_screen = app.current_screen
	var sim = match_screen.simulation
	sim.set_physics_process(false)
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = SIMULATION.SPAWN
	root.push_input(click, true)
	await _settle()
	_check(sim.is_selected, "viewport mouse input selects marker")
	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_RIGHT
	click.pressed = true
	click.position = Vector2(600, 400)
	root.push_input(click, true)
	await _settle()
	_check(
		sim.has_move_target and sim.move_target == Vector2(600, 400),
		"viewport right click sends move command"
	)
	sim.cancel_pending_input()
	# A HUD panel consumes world clicks even when they are not on a button.
	click = InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = Vector2(500, 50)
	root.push_input(click, true)
	await _settle()
	_check(sim.is_selected, "HUD click does not deselect world marker")
	var key := InputEventKey.new()
	key.physical_keycode = KEY_ESCAPE
	key.pressed = true
	root.push_input(key, true)
	await _settle()
	_check(paused, "Escape pauses through real input routing")
	var tap := InputEventScreenTouch.new()
	tap.pressed = true
	tap.position = Vector2(700, 350)
	root.push_input(tap, true)
	await _settle()
	_check(not sim.has_move_target, "pause overlay prevents world commands")
	key = InputEventKey.new()
	key.physical_keycode = KEY_ESCAPE
	key.pressed = true
	root.push_input(key, true)
	await _settle()
	_check(not paused, "Escape resumes through real input routing")
	# Test native touch adapter without requiring physical touchscreen hardware.
	tap = InputEventScreenTouch.new()
	tap.pressed = true
	tap.position = Vector2(700, 350)
	match_screen._unhandled_input(tap)
	_check(
		sim.has_move_target and sim.move_target == tap.position,
		"touch dispatches selected marker movement"
	)
	sim.cancel_pending_input()
	click = InputEventMouseButton.new()
	click.device = InputEvent.DEVICE_ID_EMULATION
	click.button_index = MOUSE_BUTTON_RIGHT
	click.pressed = true
	click.position = Vector2(800, 400)
	match_screen._unhandled_input(click)
	_check(not sim.has_move_target, "synthetic mouse does not duplicate touch")
	app.show_menu()
	await _settle()


func _test_combat_scene(app: Node) -> void:
	var baseline_count: int = get_node_count()
	for cycle in range(3):
		app.current_screen.get_node("%CombatButton").pressed.emit()
		await _settle()
		await _physics_steps(2)
		var screen = app.current_screen
		var session = screen.simulation
		_check(screen.name == "MinionArena", "combat menu opens new lab")
		_check(session.world.units.size() == 6, "initial wave contains both teams in three lanes")
		_check(session.request_wave(1), "valid wave request queued")
		_check(not session.request_wave(1), "same-frame duplicate wave rejected")
		_check(session.world.units.size() == 6, "UI command does not mutate world before physics")
		await _physics_steps(2)
		_check(session.world.units.size() == 12, "queued wave consumed once on physics tick")
		_check(session.request_wave(0), "second wave can be queued")
		screen.pause_match()
		var ticks: int = session.world.tick_count
		_check(session.pending_wave == -1, "pause cancels queued spawn")
		_check(not session.request_wave(0), "paused session rejects new spawn")
		await _physics_steps(3)
		_check(
			session.world.tick_count == ticks and session.world.units.size() == 12,
			"pause freezes minion movement, combat, regen, cooldown and wave"
		)
		screen.resume_match()
		screen.arena.process_mode = Node.PROCESS_MODE_DISABLED
		await _physics_steps(3)
		_check(session.world.tick_count > ticks, "simulation runs with visual processing disabled")
		screen.arena.process_mode = Node.PROCESS_MODE_PAUSABLE
		session.set_physics_process(false)
		var unit = session.world.units[0]
		var click := InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = screen.arena.get_global_transform_with_canvas() * unit.position
		root.push_input(click, true)
		await _settle()
		_check(session.selected_id == unit.id, "scaled arena input maps to correct world unit")
		click = InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = Vector2(500, 50)
		root.push_input(click, true)
		await _settle()
		_check(session.selected_id == unit.id, "combat HUD click does not clear selection")
		var old_id: int = screen.get_instance_id()
		screen.pause_match()
		screen.get_node("%RestartButton").pressed.emit()
		await _settle()
		await _physics_steps(2)
		_check(not is_instance_id_valid(old_id), "restart frees prior combat screen")
		_check(
			not paused and app.current_screen.name == "MinionArena",
			"restart keeps correct arena type"
		)
		_check(app.current_screen.simulation.world.wave_count == 1, "restart resets waves")
		_check(app.current_screen.simulation.world.kills == [0, 0], "restart resets kill state")
		app.current_screen.pause_match()
		app.current_screen.get_node("%MenuButton").pressed.emit()
		await _settle()
		_check(
			not paused and app.current_screen.name == "MainMenu",
			"combat exits cleanly while paused"
		)
		_check(get_node_count() == baseline_count, "combat navigation does not accumulate nodes")


func _test_siege_scene(app: Node) -> void:
	var baseline: int = get_node_count()
	for cycle in range(3):
		app.current_screen.get_node("%SiegeButton").pressed.emit()
		await _settle()
		await _physics_steps(2)
		var screen = app.current_screen
		var session = screen.simulation
		var world = session.world
		_check(screen.name == "SiegeArena", "new siege menu opens correct scene")
		_check(
			world.structures.size() == 8 and world.units.size() == 6,
			"siege starts six towers, two nexuses, and one two-team wave"
		)
		screen.get_node("%TeamMode").select(1)
		screen.get_node("%SpawnButton").pressed.emit()
		screen.get_node("%SpawnButton").pressed.emit()
		_check(
			session.pending_team_mode == 0 and world.units.size() == 6,
			"UI captures blue-team command without immediate world mutation"
		)
		await _physics_steps(2)
		_check(world.units.size() == 9, "blue-only UI wave spawns once")
		var tower = world.structures[0]
		var victim = world.units[3]
		victim.position = tower.position + Vector2(60, 0)
		tower.cooldown_ticks = 0
		_check(world.fire_projectile(tower.id, victim.id), "scene can launch projectile")
		var shot = world.projectiles[-1]
		var position: Vector2 = shot.position
		var ticks: int = world.tick_count
		_check(session.request_assault(0, 1), "red-only wave queues before pause")
		screen.pause_match()
		await _physics_steps(3)
		_check(
			world.tick_count == ticks and shot.position == position,
			"pause freezes projectiles and structure clocks"
		)
		_check(
			session.pending_wave == -1 and session.pending_team_mode == -1,
			"pause clears both queued type and team"
		)
		_check(not session.request_assault(0, 0), "paused siege rejects waves")
		screen.resume_match()
		screen.arena.process_mode = Node.PROCESS_MODE_DISABLED
		await _physics_steps(2)
		_check(world.tick_count > ticks, "siege does not depend on visual processing")
		screen.arena.process_mode = Node.PROCESS_MODE_PAUSABLE
		session.set_physics_process(false)
		var click := InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = screen.arena.get_global_transform_with_canvas() * tower.position
		root.push_input(click, true)
		await _settle()
		_check(session.selected_id == tower.id, "scaled structure selection works")
		var old_id: int = screen.get_instance_id()
		screen.pause_match()
		screen.get_node("%RestartButton").pressed.emit()
		await _settle()
		await _physics_steps(2)
		_check(not is_instance_id_valid(old_id), "restart disposes siege scene")
		screen = app.current_screen
		session = screen.simulation
		world = session.world
		_check(not paused and screen.name == "SiegeArena", "restart retains siege mode")
		_check(
			world.is_running() and world.wave_count == 1 and world.structures.size() == 8,
			"restart resets structures, wave count and result"
		)
		_check(
			world.projectiles.is_empty() and world.credited_gold == [0, 0],
			"restart leaves no old projectiles or credit"
		)
		# Finish via a real minion hit against a deliberately weakened test nexus.
		var nexus = world.nexuses[1]
		nexus.shield_active = false
		nexus.shield = 0
		nexus.hp = 1
		var attacker = world.spawn_unit(session.DEFINITIONS[0], 0, 1)
		attacker.position = nexus.position - Vector2(20, 0)
		await _physics_steps(2)
		await _settle()
		_check(
			world.winner == 0 and screen.get_node("%ArenaTitle").text == "BIRU MENANG",
			"nexus defeat is presented in the UI"
		)
		_check(
			screen.get_node("%SpawnButton").disabled and not session.request_assault(0, 0),
			"finished scene cannot queue new combat"
		)
		ticks = world.tick_count
		await _physics_steps(3)
		_check(world.tick_count == ticks, "terminal siege stays frozen")
		screen.pause_match()
		_check(
			not screen.get_node("%ResumeButton").visible,
			"result menu offers restart/menu, not resume"
		)
		screen.get_node("%MenuButton").pressed.emit()
		await _settle()
		_check(not paused and app.current_screen.name == "MainMenu", "result exits cleanly to menu")
		_check(get_node_count() == baseline, "siege cycles leave no orphan scene nodes")


func _test_level_selection_scene(app: Node) -> void:
	var path := "user://level_selection_scene_test.json"
	for suffix in ["", ".tmp", ".bak"]:
		if FileAccess.file_exists(path + suffix):
			DirAccess.remove_absolute(path + suffix)
	_check(
		LevelProgressStore.save_state(
			{
				"meta_gold": 3000,
				"completed_levels": [1],
				"replay_reward_counts": {},
				"run_difficulty": "normal"
			},
			path
		),
		"Seed isolated level unlock state"
	)
	var menu = app.current_screen
	menu.progress_path = path
	menu.refresh_levels()
	_check(
		(
			menu.get_node("%LevelChoice").is_item_disabled(2)
			and not menu.get_node("%LevelChoice").is_item_disabled(1)
		),
		"Only completed predecessor unlocks next level in menu"
	)
	menu.get_node("%LevelChoice").select(2)
	menu.get_node("%PrototypeButton").pressed.emit()
	await _settle()
	_check(app.current_screen.name == "MainMenu", "Locked level cannot launch via forged selection")
	menu.get_node("%LevelChoice").select(1)
	menu.get_node("%PrototypeButton").pressed.emit()
	await _settle()
	var screen = app.current_screen
	screen.progress_path = path
	var world = screen.simulation.world
	_check(
		world.level_number == 2 and world.difficulty == "normal" and world.economy.gold[0] == 1100,
		"Level 2 selection reaches configured arena and opening economy"
	)
	_check(
		screen.arena.terrain_palette["radiant_grass_1"] == Color8(155, 115, 60),
		"Desert arena uses the source level 2 terrain palette"
	)
	_check(
		(
			screen.arena.terrain_river.size() == 61
			and screen.arena.terrain_river[0] == Vector2(0, 200)
			and screen.arena.terrain_river[60] == Vector2(1280, 520)
		),
		"Selected match view follows the source river spline"
	)
	_check(
		screen.arena.river_texture != null and screen.arena.cached_river_theme == "desert",
		"Selected map caches the source tiled river layer"
	)
	_check(screen.arena.lane_texture != null, "Selected map caches source cobblestone lanes")
	_check(screen.arena.wall_texture != null, "Selected map caches source border wall")
	_check(screen.arena.terrain_texture != null, "Selected map caches source terrain")
	screen.get_node("%RestartButton").pressed.emit()
	await _settle()
	_check(
		app.current_screen.simulation.world.level_number == 2, "Restart retains selected encounter"
	)
	app.current_screen.get_node("%BackButton").pressed.emit()
	await _settle()
	_check(app.current_screen.name == "MainMenu", "Selected level exits cleanly")
	for suffix in ["", ".tmp", ".bak"]:
		if FileAccess.file_exists(path + suffix):
			DirAccess.remove_absolute(path + suffix)


func _test_prototype_scene(app: Node) -> void:
	for path in [SCENE_PROGRESS_PATH, SCENE_PROGRESS_PATH + ".bak", SCENE_PROGRESS_PATH + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)
	var baseline: int = get_node_count()
	for cycle in range(3):
		app.current_screen.get_node("%PrototypeButton").pressed.emit()
		app.current_screen.get_node("%PrototypeButton").pressed.emit()
		await _settle()
		var screen = app.current_screen
		screen.progress_path = SCENE_PROGRESS_PATH
		var session = screen.simulation
		var world = session.world
		session.set_physics_process(false)
		_check(
			screen.name == "PrototypeMatch" and app.screen_root.get_child_count() == 1,
			"prototype has its own guarded menu route"
		)
		# Layer 6d: the real AI owns the red side from the first tick (layer 6e
		# dropped the temporary defender) and every battle tick reaches it.
		_check(
			(
				world.ai_enabled
				and world.ai_hero_control_enabled
				and world.ai_controller.ticks == world.tick_count
				and world.ai_controller.match_seed == session.AI_MATCH_SEED
			),
			"restarted match hands the red side to the seeded AI"
		)
		world.reset_ai(1234)
		_check(
			(
				world.ai_controller.ticks == 0
				and world.ai_controller.think_ticks == 0
				and world.ai_controller.match_seed == 1234
				and world.ai_controller.policy.think_timer == 90
				and world.ai_build.total_built == 0
				and world.ai_heroes.total_skills_cast == 0
			),
			"match reset clears the AI clock and counters"
		)
		world.reset_ai(session.AI_MATCH_SEED)
		_check(
			(
				world.structures.size() == 2
				and world.living_minion_count() == 0
				and world.blue_hero() != null
				and world.economy.gold == [1000, 350]
			),
			"playable match starts empty with source budgets"
		)
		var click := InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = screen.arena.get_global_transform_with_canvas() * world.slots[2].position
		root.push_input(click, true)
		await _settle()
		_check(session.selected_slot_id == 2, "scaled mouse input selects blue build slot")
		_check(
			(
				not screen.get_node("%BuildButton").disabled
				and screen.get_node("%SellButton").disabled
			),
			"empty owned slot enables build, not sale"
		)
		click = InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.position = Vector2(500, 50)
		root.push_input(click, true)
		await _settle()
		_check(session.selected_slot_id == 2, "match HUD consumes clicks without changing slot")
		screen.get_node("%BuildButton").pressed.emit()
		screen.get_node("%BuildButton").pressed.emit()
		_check(
			session.command.id == 2 and world.economy.gold[0] == 1000,
			"build UI captures one command with no immediate charge"
		)
		session.select_at(world.slots[5].position)
		session._physics_process(1.0 / 60.0)
		var old_tower_id: int = world.slots[2].structure_id
		_check(
			old_tower_id > 0 and world.slots[5].structure_id == -1 and world.economy.gold[0] == 900,
			"build uses captured slot, not later selection"
		)
		_check(
			session.selected_slot_id == 5 and session.selected_id == -1,
			"completed build does not steal a newer selection"
		)
		session._physics_process(1.0 / 60.0)
		_check(
			world.economy.gold[0] == 900 and session.command.is_empty(), "build is consumed once"
		)
		session.select_at(world.slots[2].position)
		await _settle()
		_check(
			(
				screen.get_node("%BuildButton").disabled
				and not screen.get_node("%SellButton").disabled
			),
			"built own tower enables sale only"
		)
		_check(session.request_sell(old_tower_id), "sale ID captured")
		# Simulate invalidation between request and execution; the new ID must remain untouched.
		world.sell_tower(0, old_tower_id)
		world.build_tower(0, 2)
		var replacement_id: int = world.slots[2].structure_id
		session._physics_process(1.0 / 60.0)
		_check(
			world.economy.gold[0] == 850 and world.slots[2].structure_id == replacement_id,
			"queued stale sale cannot refund or remove a replacement"
		)
		session.select_at(world.slots[2].position)
		await _settle()
		screen.get_node("%SellButton").pressed.emit()
		screen.get_node("%SellButton").pressed.emit()
		session._physics_process(1.0 / 60.0)
		_check(
			world.economy.gold[0] == 900 and world.slots[2].structure_id == -1,
			"sale UI refunds exactly once"
		)
		_check(session.request_build(2), "build queues before pause")
		var ticks: int = world.tick_count
		var remaining: int = world.scheduler.remaining_ticks
		var ai_ticks: int = world.ai_controller.ticks
		var ai_timer: int = world.ai_controller.policy.think_timer
		var ai_gold: int = world.economy.gold[1]
		session.set_physics_process(true)
		screen.pause_match()
		await _physics_steps(3)
		_check(
			(
				session.command.is_empty()
				and world.tick_count == ticks
				and world.scheduler.remaining_ticks == remaining
				and world.economy.gold[0] == 900
			),
			"pause cancels transactions and freezes income/wave clocks"
		)
		_check(
			(
				world.ai_controller.ticks == ai_ticks
				and world.ai_controller.policy.think_timer == ai_timer
				and world.economy.gold[1] == ai_gold
			),
			"pause freezes the AI clock, purse and schedule"
		)
		_check(
			not session.request_build(2) and not session.request_sell(replacement_id),
			"paused match rejects new transactions"
		)
		screen.resume_match()
		screen.arena.process_mode = Node.PROCESS_MODE_DISABLED
		await _physics_steps(3)
		_check(world.tick_count > ticks, "prototype simulation is independent of rendering")
		screen.arena.process_mode = Node.PROCESS_MODE_PAUSABLE
		session.set_physics_process(false)
		session.request_build(2)
		app._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
		_check(paused and session.command.is_empty(), "focus loss cancels match transaction")
		screen.resume_match()
		var tap := InputEventScreenTouch.new()
		tap.pressed = true
		tap.position = screen.arena.get_global_transform_with_canvas() * world.slots[9].position
		screen._unhandled_input(tap)
		await _settle()
		_check(
			session.selected_slot_id == 9 and screen.get_node("%BuildButton").disabled,
			"touch adapter can inspect enemy slot but cannot build there"
		)
		session.request_build(9)
		session._physics_process(1.0 / 60.0)
		_check(
			world.slots[9].structure_id == -1 and world.economy.gold[0] == 900,
			"execution rejects enemy slot even when UI is bypassed"
		)
		click = InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		click.device = InputEvent.DEVICE_ID_EMULATION
		click.position = screen.arena.get_global_transform_with_canvas() * world.slots[2].position
		screen._unhandled_input(click)
		_check(session.selected_slot_id == 9, "touch emulation does not double-dispatch selection")
		_check(world.economy.is_balanced(), "UI transactions preserve ledger invariant")
		_check(
			(
				screen.get_node("HUD/TopBar").get_global_rect().end.x <= 1280.0
				and screen.get_node("HUD/BottomBar").get_global_rect().end.y <= 720.0
			),
			"prototype HUD fits reference viewport"
		)
		var winner: int = cycle % 2
		var nexus = world.nexuses[1 - winner]
		nexus.shield_active = false
		nexus.shield = 0
		nexus.hp = 1
		var attacker = world.spawn_unit(session.DEFINITIONS[0], winner, 1)
		attacker.position = nexus.position - Vector2(20, 0)
		world.apply_hit(attacker.id, nexus.id)
		await _settle()
		var title := "BIRU MENANG" if winner == 0 else "MERAH MENANG"
		_check(
			(
				paused
				and screen.get_node("%PauseOverlay").visible
				and screen.get_node("%PauseTitle").text == title
			),
			"match result opens automatically for either team"
		)
		var progress := LevelProgressStore.load_state(SCENE_PROGRESS_PATH)
		var reward: int = [3000, 0, 1500][cycle]
		var total: int = [3000, 3000, 4500][cycle]
		_check(
			(
				progress.get("meta_gold", -1) == total
				and not screen.get_node("%SaveRetryButton").visible
				and screen.get_node("HUD/PauseOverlay/Center/Card/Column/Hint").text.contains(
					"+%d Meta Gold" % reward
				)
			),
			"match result commits one development reward per victory or defeat"
		)
		_check(
			(
				not screen.get_node("%ResumeButton").visible
				and screen.get_node("%BuildButton").disabled
				and screen.get_node("%SellButton").disabled
			),
			"result offers restart/menu, no resume or transactions"
		)
		screen.resume_match()
		_check(paused and not session.request_build(2), "result cannot resume or accept build")
		var old_screen_id: int = screen.get_instance_id()
		screen.get_node("%RestartButton").pressed.emit()
		await _settle()
		screen = app.current_screen
		session = screen.simulation
		world = session.world
		_check(
			(
				not is_instance_id_valid(old_screen_id)
				and not paused
				and screen.name == "PrototypeMatch"
			),
			"restart disposes old scene and retains prototype mode"
		)
		_check(
			(
				world.economy.gold == [1000, 350]
				and world.economy.spent == [0, 0]
				and world.structures.size() == 2
				and world.wave_count == 0
				and world.winner == -1
			),
			"restart resets economy, slots, waves and result"
		)
		_check(
			(
				session.selected_slot_id == -1
				and session.command.is_empty()
				and world.scheduler.pending_count() == 0
				and world.projectiles.is_empty()
			),
			"restart leaves no stale input, queue or projectile"
		)
		screen.pause_match()
		screen.get_node("%MenuButton").pressed.emit()
		await _settle()
		_check(
			not paused and app.current_screen.name == "MainMenu",
			"prototype exits paused/result cleanly"
		)
		_check(get_node_count() == baseline, "prototype cycles do not leak scene nodes")
	# Corrupt saves must not be overwritten; the result overlay allows retry
	# after the user restores/removes the corrupt development file.
	var corrupt_file := FileAccess.open(SCENE_PROGRESS_PATH, FileAccess.WRITE)
	corrupt_file.store_string("broken")
	corrupt_file.close()
	app.current_screen.get_node("%PrototypeButton").pressed.emit()
	await _settle()
	var retry_screen = app.current_screen
	retry_screen.progress_path = SCENE_PROGRESS_PATH
	var retry_session = retry_screen.simulation
	retry_session.set_physics_process(false)
	var retry_world = retry_session.world
	var enemy = retry_world.nexuses[1]
	enemy.shield_active = false
	enemy.shield = 0
	enemy.hp = 1
	var ally = retry_world.spawn_unit(retry_session.DEFINITIONS[0], 0, 1)
	ally.position = enemy.position - Vector2(20, 0)
	retry_world.apply_hit(ally.id, enemy.id)
	await _settle()
	_check(retry_screen.get_node("%SaveRetryButton").visible, "Corrupt save exposes retry")
	_check(
		FileAccess.get_file_as_string(SCENE_PROGRESS_PATH) == "broken",
		"Corrupt progress is never overwritten automatically"
	)
	DirAccess.remove_absolute(SCENE_PROGRESS_PATH)
	retry_screen.get_node("%SaveRetryButton").pressed.emit()
	_check(
		(
			LevelProgressStore.load_state(SCENE_PROGRESS_PATH).get("meta_gold", -1) == 3000
			and not retry_screen.get_node("%SaveRetryButton").visible
		),
		"Explicit retry commits after progress is repaired"
	)
	retry_screen.get_node("%MenuButton").pressed.emit()
	await _settle()
	_check(get_node_count() == baseline, "retry scene leaves no orphan nodes")
	for path in [SCENE_PROGRESS_PATH, SCENE_PROGRESS_PATH + ".bak", SCENE_PROGRESS_PATH + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)
