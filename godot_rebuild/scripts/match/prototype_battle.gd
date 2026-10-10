# gdlint:disable=max-file-lines,max-line-length,class-definitions-order,unused-argument,max-public-methods
extends "res://scripts/combat/siege_battle.gd"
## Playable normal/level-1 subset. Wave/ledger/build rules are separate from the old manual labs.

const Upgrades = preload("res://scripts/match/archer_upgrades.gd")
const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")
const CannonUpgrades = preload("res://scripts/match/cannon_upgrades.gd")
const IceUpgrades = preload("res://scripts/match/ice_upgrades.gd")
const MageUpgrades = preload("res://scripts/match/mage_upgrades.gd")
const NexusUpgrades = preload("res://scripts/match/nexus_upgrades.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const Forge = preload("res://scripts/match/forge.gd")
const AiHeroControl = preload("res://scripts/match/ai_hero_control.gd")
const AiController = preload("res://scripts/match/ai_controller.gd")
const AiBuild = preload("res://scripts/match/ai_build.gd")
const AiRecruitment = preload("res://scripts/match/ai_recruitment.gd")
const AiUpgrades = preload("res://scripts/match/ai_upgrades.gd")
const AiItems = preload("res://scripts/match/ai_items.gd")
const AiShields = preload("res://scripts/match/ai_shields.gd")
const AiDraft = preload("res://scripts/match/ai_draft.gd")
const ItemShopUI = preload("res://scripts/match/item_shop_ui.gd")
const TacticalCommands = preload("res://scripts/match/tactical_commands.gd")
const HitStopRuntime = preload("res://scripts/match/hit_stop_runtime.gd")
const BossDeathAnimation = preload("res://scripts/ui/boss_death_animation.gd")
const BossIntroCinematic = preload("res://scripts/ui/boss_intro_cinematic.gd")
const EffectManager = preload("res://scripts/ui/effect_manager.gd")
const LevelIntroScreen = preload("res://scripts/ui/level_intro_screen.gd")
const MapRenderer = preload("res://scripts/ui/map_renderer.gd")
const SpriteCache = preload("res://scripts/ui/sprite_cache.gd")
const RenderCache = preload("res://scripts/ui/render_cache.gd")
const TerrainPalette = preload("res://scripts/ui/terrain_palette.gd")
const Scheduler = preload("res://scripts/match/wave_scheduler.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const BossAI = preload("res://scripts/match/boss_ai.gd")
# Layer 7c: level-1 config generated from levels/level_data.py by the oracle.
const LevelCatalog = preload("res://scripts/match/level_catalog.gd")
const LevelProgress = preload("res://scripts/match/level_progress.gd")
const LevelStats = preload("res://scripts/match/level_stats.gd")
const LevelProgressStore = preload("res://scripts/match/level_progress_store.gd")
const SaveSlotStore = preload("res://scripts/match/save_slot_store.gd")
const BOSS_DATA := "res://data/bosses/boss_stats.json"
const RANGED_BOSS_KITERS := [
	"ancient_apparition",
	"morgath",
	"razak",
	"varkul",
	"xerathis",
	"nyzrak",
	"syrentha",
	"thalgryn",
	"nyxarath",
	"malzareth",
	"akashari",
	"vorenmarr"
]
const SlotLayout = preload("res://scripts/match/slot_layout.gd")
const Slot = preload("res://scripts/match/build_slot.gd")
const ItemEffects = preload("res://scripts/match/item_effects.gd")
const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const ReflectItemEffects = preload("res://scripts/match/reflect_item_effects.gd")
const MINIONS := {
	"goblin": preload("res://data/minions/goblin.tres"),
	"orc": preload("res://data/minions/orc.tres"),
	"troll": preload("res://data/minions/troll.tres"),
	"undead": preload("res://data/minions/undead.tres"),
	"dark_rider": preload("res://data/minions/dark_rider.tres")
}
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const THORNE = preload("res://data/heroes/thorne.tres")
const GRIMJAW = preload("res://data/heroes/grimjaw.tres")
const SYLARA = preload("res://data/heroes/sylara.tres")
const VEX = preload("res://data/heroes/vex.tres")
const ZEPHYR = preload("res://data/heroes/zephyr.tres")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS
# Exact source Kaizen/Grimjaw/Sylara/Vex FX-director on_cast requests. Other
# visual-only FX callbacks stay out of the gameplay hit-stop port.
const SOURCE_CAST_HIT_STOP_SECONDS := {
	"kaizen": {"q": 0.021, "e": 0.024, "r": 0.04},
	"grimjaw": {"q": 0.027, "e": 0.024, "r": 0.04},
	"sylara": {"q": 0.02},
	"vex": {"q": 0.021, "w": 0.025, "r": 0.04}
}
# Source KaizenFXDirector.on_dash fires on the Q2 dash-state edge. Its
# on_impact hook is not a live gameplay request in the current Python attack path.
const SOURCE_DASH_HIT_STOP_SECONDS := {"kaizen": {"q": 0.027}}
# Python BossDeathAnimation pauses gameplay for its active 60/90-frame phase.
const BOSS_DEATH_PAUSE_TICKS := {"mini": 60, "true": 90}
# Kept as an alias because the red recruitment adapters predate the player shop.
const PLAYABLE_AI_HEROES = HERO_ROSTER
const STARTER_HEROES: Array[String] = ["thorne", "grimjaw", "vex", "sylara", "kaizen", "zephyr"]
const DEFAULT_PURCHASED_HEROES: Array[String] = ["kaizen"]
const MAX_HEROES_OWNED := 5
const HERO_SPAWN := Vector2(220, 540)
# Source MapRenderer.radiant_shop_pos. Game.try_buy_hero adds (80 + n*30 - 30, 10).
const PLAYER_HERO_SHOP := Vector2(340, 540)
# Source AIPlayer: RED_BASE_X - 60, RED_BASE_Y + 30. Not a shop purchase.
const RED_HERO_SPAWN := Vector2(1120, 130)
const HERO_HUNT_RANGE := 900.0
const HERO_RETREAT_HP := 0.2
const HERO_HEAL_RATIO := 0.8
const HERO_BASE_HEAL := 3.0
const HERO_PASSIVE_HEAL := 0.15
const HERO_BASE_NEAR := 100.0
# Source Minion.__init__: every fresh minion gets a small random offset on both
# axes (random.uniform(-8, 8)) before the per-lane Y spread, so wave units do
# not stack on one pixel. The match seeds the draws so a restarted run replays;
# the Python stream itself is not reproduced.
const SPAWN_JITTER := 8.0
const SPAWN_SEED := 20260929
const HERO_DEATH_REWARD := 150

var economy := Economy.new()
var effects := EffectManager.new()
var level_intro := LevelIntroScreen.new()
var boss_intro: BossIntroCinematic = null
var boss_death: BossDeathAnimation = null
var map_renderer := MapRenderer.new()
var sprite_cache: SpriteCache = SpriteCache.get_shared()
var render_cache: RenderCache = RenderCache.get_shared()
# Layer 5f: Forge shop transactions (buy for a dead hero queues the order).
var forge := Forge.new()
# Layer 5f-2: ITEM FORGE panel state + click routing (drawing lives in the UI).
var item_shop := ItemShopUI.new()
# Source TacticalCommandManager: fixed-tick player squad orders and hold state.
var tactical := TacticalCommands.new()
# Layer 6a: per-tick control for the explicitly owned AI hero roster.
var ai_heroes := AiHeroControl.new()
# Layer 6b: scheduling wrapper (source AIPlayer.update). Layer 6e: set_ai_enabled()
# is the only switch; with it off the red side stays idle.
var ai_controller := AiController.new()
var ai_enabled := false
var ai_hero_control_enabled := false
# Ownership is explicit: the free mirrored red Kaizen is not an AIPlayer hero.
var ai_hero_ids: Array[int] = []
# The blue mirror is the prototype's already-active Kaizen. It occupies the
# source five-hero roster so player purchases cannot duplicate or exceed cap.
var player_hero_ids: Array[int] = []
# Layer 6c: the action adapters and the persistent draft target the red side.
var ai_draft := AiDraft.new()
var ai_build := AiBuild.new()
var ai_recruitment := AiRecruitment.new()
var ai_upgrades := AiUpgrades.new()
var ai_items := AiItems.new()
var ai_shields := AiShields.new()
# Source Hero.aggro_range: an auto destination is abandoned inside this radius.
const HERO_AGGRO_RANGE := 250.0
var scheduler := Scheduler.new()
var slots: Array[Slot] = []
var transaction_error := ""
# Layer 7b: seeded stream for the source spawn jitter (match-reproducible).
var spawn_rng := RandomNumberGenerator.new()
# Layer 7c: level-1 config and the source difficulty rule (Game.reset).
var level_config: Dictionary = {}
var level_number := 1
var _level_result_claimed := false
var difficulty := "normal"
var enemy_scaling_enabled := false
var enemy_hp_mult := 1.0
var enemy_damage_mult := 1.0
var enemy_speed_mult := 1.0
# Layers 8b/8c/8d/8e/8f/8i/8j: match combat, boss movement, clocks and
# presentation payloads. Rendering remains in prototype_view.gd.
var boss_table: Dictionary = {}
var boss_rng := RandomNumberGenerator.new()
var active_boss: BossState = null
# Layer 9b: all hero inventories in this match share the source's target-keyed
# Miasma registry; tracker owner fields retain last-applier credit.
var _miasma_registry: Dictionary = {}
var pending_mini_bosses: Array[Dictionary] = []
var true_boss_spawned := false
var red_towers_destroyed := 0
var _pending_red_tower_deaths := 0
var _mini_boss_schedule: Dictionary = {}
var bosses_defeated_this_run := 0
var bosses_defeated_this_match: Array[String] = []
var unlocked_bosses: Array[String] = []
# Source auto-grants only Kaizen; the other free starters must first be claimed
# from the permanent Hero Shop before the in-match shop can summon them.
var purchased_heroes: Array[String] = DEFAULT_PURCHASED_HEROES.duplicate()
var heroes_unlocked_this_match: Array[String] = []
var boss_rewards: Array[Dictionary] = []
# Layer 8l: source Game.miniboss_kill_count / trueboss_kill_count. Only a real
# enemy hero landing the last hit moves them; the achievement banner they feed
# in the source is presentation and stays outside this port.
var miniboss_kill_count := 0
var trueboss_kill_count := 0
var achievements_unlocked: Dictionary = {}
# Layer 8f: death FX survives registry retirement, like source EffectManager.
var boss_death_presentations: Array[Dictionary] = []
var boss_death_pause_ticks := 0
var boss_death_froze_last_step := false
var hit_stop_state = HitStopRuntime.new()
var hit_stop_froze_last_step := false
var boss_screen_shake_intensity := 0.0
var boss_screen_shake_timer := 0
var score := 0
var total_kills := 0
var max_combo := 0
var combo_count: int:
	get:
		return effects.combo_counter.count
	set(value):
		effects.combo_counter.count = value
var combo_timer: int:
	get:
		return effects.combo_counter.timer
	set(value):
		effects.combo_counter.timer = value
var last_combo: int:
	get:
		return effects.combo_counter.last_combo
	set(value):
		effects.combo_counter.last_combo = value
var match_started_msec := Time.get_ticks_msec()
var match_finished_msec := -1
var match_time_override_seconds := -1
var _victory_unlocks_granted := false
var _audio_result_announced := false


func _init() -> void:
	spawn_rng.seed = SPAWN_SEED
	level_config = LevelCatalog.get_level_config(level_number)
	_configure_map_renderer()
	slots = SlotLayout.create(_lane_paths_from_renderer())
	var boss_parsed = JSON.parse_string(FileAccess.get_file_as_string(BOSS_DATA))
	boss_table = boss_parsed if boss_parsed is Dictionary else {}
	_configure_level_intro()
	boss_rng.randomize()
	_mini_boss_schedule = _roll_mini_boss_schedule()
	_apply_difficulty()


## Data-only level selection before setup_arena. No menu/save progression is
## wired yet: the playable scene still starts at level 1.
func configure_level(number: int) -> bool:
	if _arena_initialized or not structures.is_empty() or not units.is_empty():
		return false
	if economy.spent != [0, 0] or economy.earned != [0, 0] or economy.refunded != [0, 0]:
		return false
	if economy.passive != [0, 0] or economy.income_ticks != 0 or economy.income_milli != 0:
		return false
	var config := LevelCatalog.get_level_config(number)
	if config.is_empty():
		return false
	level_number = number
	level_config = config
	_configure_map_renderer()
	_configure_level_intro()
	slots = SlotLayout.create(_lane_paths_from_renderer())
	ai_controller.policy.level_number = number
	ai_draft.level_number = number
	_apply_difficulty()
	_apply_opening_economy()
	_mini_boss_schedule = _roll_mini_boss_schedule()
	return true


func _configure_level_intro() -> void:
	level_intro = LevelIntroScreen.new()
	var bosses: Dictionary = boss_table.get("bosses", {}) as Dictionary
	var true_boss_id := String(level_config.get("true_boss", "abaddon"))
	var boss_entry: Dictionary = bosses.get(true_boss_id, {}) as Dictionary
	level_intro.setup(level_config, boss_entry, MapRenderer.MAP_WIDTH, MapRenderer.MAP_HEIGHT)


func step_level_intro() -> bool:
	if level_intro == null or not level_intro.is_active():
		return false
	var play_sound := level_intro.update()
	if play_sound:
		AudioRuntime.play("wave_start")
	return play_sound


func skip_level_intro(keycode: int = -1, click: bool = false) -> bool:
	if level_intro == null:
		return false
	return level_intro.handle_skip(keycode, click)


func level_intro_state(touch_mode: bool = false) -> Dictionary:
	if level_intro == null:
		return {}
	return {
		"active": level_intro.is_active(),
		"timer": level_intro.timer,
		"level_num": level_intro.level_num,
		"level_name": level_intro.level_name,
		"level_desc": level_intro.level_desc,
		"map_theme": level_intro.map_theme,
		"boss_type": level_intro.boss_type,
		"boss_name": level_intro.boss_name,
		"boss_title": level_intro.boss_title,
		"boss_tag": level_intro.get_boss_tag(),
		"fade_alpha": level_intro.get_fade_alpha(),
		"theme_tint_rgba": level_intro.get_theme_tint_rgba(),
		"difficulty": level_intro.get_difficulty_info(difficulty),
		"starting_gold_text": level_intro.get_starting_gold_text(),
		"passive_text": level_intro.get_passive_text(),
		"reward_text": level_intro.get_reward_text(),
		"show_prompt": level_intro.get_show_prompt(),
		"prompt_text": level_intro.get_begin_prompt(touch_mode),
		"warning_text": level_intro.get_warning_text(),
	}


func _configure_boss_intro(boss: BossState) -> void:
	if boss == null:
		return
	boss_intro = BossIntroCinematic.new()
	(
		boss_intro
		. setup(
			{
				"name": boss.display_name,
				"title": boss.title,
				"boss_class": boss.boss_class,
				"color": [int(boss.color.r8), int(boss.color.g8), int(boss.color.b8)],
				"color_dark":
				[int(boss.color_dark.r8), int(boss.color_dark.g8), int(boss.color_dark.b8)],
				"entrance_color":
				[
					int(boss.entrance_color.r8),
					int(boss.entrance_color.g8),
					int(boss.entrance_color.b8),
				],
			},
			MapRenderer.MAP_WIDTH,
			MapRenderer.MAP_HEIGHT
		)
	)


func step_boss_intro() -> bool:
	if boss_intro == null or not boss_intro.is_active():
		return false
	var play_sound := boss_intro.update()
	if play_sound:
		AudioRuntime.play("nexus_hit")
	return play_sound


func skip_boss_intro(keycode: int = -1, click: bool = false) -> bool:
	if boss_intro == null:
		return false
	return boss_intro.handle_skip(keycode, click)


func boss_intro_state() -> Dictionary:
	if boss_intro == null:
		return {"active": false}
	return {
		"active": boss_intro.is_active(),
		"timer": boss_intro.timer,
		"elapsed": boss_intro.get_elapsed(),
		"boss_name": boss_intro.boss_name,
		"boss_title": boss_intro.boss_title,
		"boss_class": boss_intro.boss_class,
		"tag": boss_intro.get_tag(),
		"alpha": boss_intro.get_alpha(),
		"background_alpha": boss_intro.get_background_alpha(),
		"border_alpha": boss_intro.get_border_alpha(),
		"entrance_color": boss_intro.get_entrance_color(),
		"slide_offset": boss_intro.get_slide_offset(),
		"banner_x": boss_intro.get_banner_x(),
		"banner_y": boss_intro.get_banner_y(),
		"banner_width": boss_intro.get_banner_width(),
		"hp_progress": boss_intro.get_hp_progress(),
		"hp_fill_width": boss_intro.get_hp_fill_width(),
		"hp_bar_rect": boss_intro.get_hp_bar_rect(),
	}


func _configure_boss_death(boss: BossState) -> void:
	if boss == null:
		return
	boss_death = BossDeathAnimation.new()
	(
		boss_death
		. configure(
			{
				"x": boss.position.x,
				"y": boss.position.y,
				"name": boss.display_name,
				"title": boss.title,
				"boss_class": boss.boss_class,
				"color": [int(boss.color.r8), int(boss.color.g8), int(boss.color.b8)],
				"color_dark":
				[int(boss.color_dark.r8), int(boss.color_dark.g8), int(boss.color_dark.b8)],
				"entrance_color":
				[
					int(boss.entrance_color.r8),
					int(boss.entrance_color.g8),
					int(boss.entrance_color.b8),
				],
				"gold_reward": boss.gold_reward,
				"radius": boss.radius,
			},
			MapRenderer.MAP_WIDTH,
			MapRenderer.MAP_HEIGHT
		)
	)


func step_boss_death() -> bool:
	if boss_death == null or not boss_death.is_active():
		return false
	var was_sound_played := boss_death.sound_played
	boss_death.update()
	var play_sound := not was_sound_played and boss_death.sound_played
	if play_sound:
		AudioRuntime.play("victory")
	return play_sound


func skip_boss_death(keycode: int = -1, click: bool = false) -> bool:
	if boss_death == null:
		return false
	return boss_death.handle_skip(keycode, click)


func boss_death_state() -> Dictionary:
	if boss_death == null:
		return {"active": false, "death_active": false, "celebration_active": false}
	var state := boss_death.get_state()
	state["death_active"] = boss_death.is_death_active()
	state["boss_name"] = boss_death.boss_name
	state["boss_title"] = boss_death.boss_title
	state["boss_class"] = boss_death.boss_class
	state["gold_reward"] = boss_death.boss_gold_reward
	state["death_visual"] = boss_death.get_death_visual_state()
	state["celebration_visual"] = boss_death.get_celebration_visual_state(tick_count)
	return state


func _configure_map_renderer() -> void:
	sprite_cache = SpriteCache.get_shared()
	render_cache = RenderCache.get_shared()
	effects.sprite_cache = sprite_cache
	effects.render_cache = render_cache
	var requested_theme := String(level_config.get("map_theme", "forest"))
	var theme_data := TerrainPalette.for_theme(requested_theme)
	theme_data["name"] = requested_theme
	if not theme_data.has("ambient_tint"):
		theme_data["ambient_tint"] = null
	(
		map_renderer
		. configure(
			requested_theme,
			{
				"top": _packed_to_pairs(paths[0]),
				"mid": _packed_to_pairs(paths[1]),
				"bot": _packed_to_pairs(paths[2]),
			},
			_packed_to_pairs(TerrainPalette.river_path()),
			{},
			theme_data
		)
	)
	map_renderer.cache_theme_assets(sprite_cache, render_cache)


func cache_stats() -> Dictionary:
	return {
		"sprite_cache": sprite_cache.get_state(),
		"render_cache": render_cache.get_state(),
	}


func _cache_hero_assets(hero: HeroState) -> void:
	if hero == null or hero.definition == null:
		return
	var hero_id := String(hero.definition.id)
	var team_name := "blue" if hero.team == BLUE else "red"
	var radius := int(round(hero.settings().radius_px))
	var extent := maxi(32, radius * 2 + 12)
	sprite_cache.get_or_render(
		["hero", hero_id, team_name],
		extent,
		extent,
		func(surface: Variant) -> void:
			if surface is Dictionary:
				var dict: Dictionary = surface
				dict["marker"] = "hero:%s:%s" % [hero_id, team_name]
				dict["bounds"] = [0, 0, extent, extent]
	)
	var ring_rgb: Array = [115, 203, 187] if hero.team == BLUE else [215, 133, 121]
	render_cache.get_circle_surface(radius, ring_rgb, 2)


func _cache_boss_assets(boss: BossState) -> void:
	if boss == null:
		return
	var radius := int(round(boss.radius))
	var extent := maxi(48, radius * 2 + 16)
	sprite_cache.get_or_render(
		["boss", boss.boss_type, boss.boss_class],
		extent,
		extent,
		func(surface: Variant) -> void:
			if surface is Dictionary:
				var dict: Dictionary = surface
				dict["marker"] = "boss:%s:%s" % [boss.boss_type, boss.boss_class]
				dict["bounds"] = [0, 0, extent, extent]
	)
	render_cache.get_glow_surface(
		radius, [int(boss.color.r8), int(boss.color.g8), int(boss.color.b8)], 5
	)


func _packed_to_pairs(points: PackedVector2Array) -> Array:
	var pairs: Array = []
	for point in points:
		pairs.append([int(point.x), int(point.y)])
	return pairs


func _pairs_to_packed(pairs: Array, fallback: PackedVector2Array) -> PackedVector2Array:
	if pairs.is_empty():
		return fallback
	var packed := PackedVector2Array()
	for entry in pairs:
		if entry is Array and (entry as Array).size() >= 2:
			var pair: Array = entry
			packed.append(Vector2(float(pair[0]), float(pair[1])))
		elif entry is Vector2:
			packed.append(entry as Vector2)
	return packed if not packed.is_empty() else fallback


func _lane_paths_from_renderer() -> Array[PackedVector2Array]:
	return [
		_pairs_to_packed(map_renderer.get_lane_path("top"), paths[0]),
		_pairs_to_packed(map_renderer.get_lane_path("mid"), paths[1]),
		_pairs_to_packed(map_renderer.get_lane_path("bot"), paths[2]),
	]


func is_click_on_shop(point: Vector2) -> bool:
	return map_renderer.is_click_on_shop(point.x, point.y)


func clicked_shop_at(point: Vector2) -> Variant:
	return map_renderer.get_clicked_shop(point.x, point.y)


func configure_player_profile(state: Dictionary) -> bool:
	# Profile data must be installed before setup so no live roster can be
	# relabelled as purchased. Source grants Kaizen to an empty legacy profile.
	if _arena_initialized or not structures.is_empty() or not units.is_empty():
		return false
	var bought: Variant = state.get("purchased_heroes", [])
	var defeated: Variant = state.get("unlocked_bosses", [])
	if not (bought is Array) or not (defeated is Array):
		return false
	var next_purchased: Array[String] = DEFAULT_PURCHASED_HEROES.duplicate()
	var next_unlocked: Array[String] = []
	for value in bought:
		var hero_type := String(value)
		if not HERO_ROSTER.has(hero_type):
			return false
		if not next_purchased.has(hero_type):
			next_purchased.append(hero_type)
	for value in defeated:
		var hero_type := String(value)
		var definition: HeroDefinition = HERO_ROSTER.get(hero_type) as HeroDefinition
		if definition == null or not definition.is_boss_hero:
			return false
		if not next_unlocked.has(hero_type):
			next_unlocked.append(hero_type)
	purchased_heroes = next_purchased
	unlocked_bosses = next_unlocked
	return true


func player_profile_state(state: Dictionary) -> Dictionary:
	var merged := state.duplicate(true)
	var bought: Array = merged.get("purchased_heroes", [])
	var defeated: Array = merged.get("unlocked_bosses", [])
	for hero_type in purchased_heroes:
		if not bought.has(hero_type):
			bought.append(hero_type)
	for hero_type in unlocked_bosses:
		if not defeated.has(hero_type):
			defeated.append(hero_type)
	merged["purchased_heroes"] = bought
	merged["unlocked_bosses"] = defeated
	return merged


func match_stats_snapshot() -> Dictionary:
	var finished := match_finished_msec
	if finished < 0:
		finished = Time.get_ticks_msec()
	var elapsed_seconds := maxi(0, int((finished - match_started_msec) / 1000))
	if match_time_override_seconds >= 0:
		elapsed_seconds = match_time_override_seconds
	return {
		"won": winner == BLUE,
		"score": score,
		"time_seconds": elapsed_seconds,
		"kills": total_kills,
		"combo": max_combo,
		"playtime_seconds": elapsed_seconds,
	}


func _result_transaction(state: Dictionary, is_replay: bool) -> Dictionary:
	var result := LevelProgress.apply_result(
		state, level_number, winner == BLUE, is_replay, difficulty
	)
	if result.is_empty():
		return {}
	if match_finished_msec < 0:
		match_finished_msec = Time.get_ticks_msec()
	var match_stats := match_stats_snapshot()
	var profile := player_profile_state(result.state)
	var stats := LevelStats.update_level_stats(profile, level_number, match_stats)
	if stats.is_empty():
		return {}
	result["state"] = stats.state
	result["match_stats"] = match_stats
	result["is_new_best_score"] = stats.is_new_best_score
	result["is_new_best_time"] = stats.is_new_best_time
	result["level_stats"] = stats.new_stats
	return result


## Explicit in-memory result boundary. It is not called from step_tick: only
## the owning scene/store may commit the returned copy.
func claim_level_result(state: Dictionary, is_replay: bool = false) -> Dictionary:
	if _level_result_claimed or winner not in [BLUE, RED]:
		return {}
	var result := _result_transaction(state, is_replay)
	if result.is_empty():
		return {}
	_level_result_claimed = true
	return result


## Atomic save transaction. Unlike claim_level_result, this consumes the claim
## only AFTER a verified write, so the playable result screen can retry safely.
func commit_level_result(
	path: String = LevelProgressStore.PATH,
	is_replay: bool = false,
	slot_path_template: String = SaveSlotStore.PATH_TEMPLATE
) -> Dictionary:
	if _level_result_claimed or winner not in [BLUE, RED]:
		return {}
	if FileAccess.file_exists(path + ".bak"):
		return {}  # Explicit recovery first; never overwrite the older save.
	var state := LevelProgressStore.load_state(path)
	if FileAccess.file_exists(path) and state.is_empty():
		return {}  # Invalid/version-mismatched save is not a fresh account.
	var result := _result_transaction(state, is_replay)
	if result.is_empty():
		return {}
	if not SaveSlotStore.save_path(result.state, path, -1.0, slot_path_template):
		return {}
	_level_result_claimed = true
	return result


func structure_limit() -> int:
	return 20  # Nine slots per team plus two nexuses.


func setup_arena() -> bool:
	if _arena_initialized or not is_running() or not structures.is_empty() or not units.is_empty():
		return false
	_arena_initialized = true
	spawn_structure(NEXUS, BLUE, LaneLayout.BLUE_BASE)
	spawn_structure(NEXUS, RED, LaneLayout.RED_BASE)
	_apply_castle_start_levels()
	# Keep the existing free mirror for prototype compatibility, but register
	# blue Kaizen as the first player-roster slot. The red mirror remains outside
	# AIPlayer ownership.
	var blue_kaizen := spawn_hero(KAIZEN, BLUE, HERO_SPAWN)
	if blue_kaizen == null:
		return false
	player_hero_ids.append(blue_kaizen.id)
	_cache_hero_assets(blue_kaizen)
	var red_kaizen := spawn_hero(KAIZEN, RED, RED_HERO_SPAWN)
	if red_kaizen == null:
		return false
	_cache_hero_assets(red_kaizen)
	AudioRuntime.play("hero_spawn")
	return true


func spawn_wave(_definition: Definition) -> bool:
	return false  # The scheduler, not a lab button, owns waves here.


func spawn_assault_wave(_definition: Definition, _team_mode: int) -> bool:
	return false


func spawn_unit(definition: Definition, team: int, lane: int) -> UnitState:
	if team not in [BLUE, RED]:
		return super.spawn_unit(definition, team, lane)
	var current := nexus_level(team)
	var target: Definition = definition
	if current > 1:
		target = scaled_minion_definition(definition, current)
		if target == null:
			return null
	# Source update_waves: hard mode scales the red minions on top of the
	# nexus tier (hp/damage truncate, speed keeps its fraction).
	if team == RED and enemy_scaling_enabled:
		target = _enemy_scaled_definition(target)
	var unit := super.spawn_unit(target, team, lane)
	if unit != null:
		unit.ai_level = 1 if current <= 1 else NexusUpgrades.MINION_AI[current - 1]
	return unit


func _enemy_scaled_definition(base: Definition) -> Definition:
	# Port of the red-minion block in Game.update_waves.
	var copy := base.duplicate() as Definition
	copy.max_hp = int(copy.max_hp * enemy_hp_mult)
	copy.damage = int(copy.damage * enemy_damage_mult)
	copy.speed_px_per_tick = copy.speed_px_per_tick * enemy_speed_mult
	return copy


func set_difficulty(value: String) -> void:
	# Source Game.reset: only "hard" turns enemy scaling on; any other value
	# (including an unknown one) leaves every multiplier at 1.0.
	difficulty = value
	_apply_difficulty()
	_apply_opening_economy()
	# A new source run rolls its schedule after difficulty is fixed. Re-roll
	# here too for callers that configure the rebuild before setup_arena().
	_mini_boss_schedule = _roll_mini_boss_schedule()


func _apply_difficulty() -> void:
	enemy_scaling_enabled = difficulty == "hard"
	if enemy_scaling_enabled:
		enemy_hp_mult = float(level_config.get("enemy_hp_mult", 1.0)) * 1.15
		enemy_damage_mult = float(level_config.get("enemy_damage_mult", 1.0)) * 1.10
		enemy_speed_mult = float(level_config.get("enemy_speed_mult", 1.0))
	else:
		enemy_hp_mult = 1.0
		enemy_damage_mult = 1.0
		enemy_speed_mult = 1.0


func _apply_opening_economy() -> void:
	# Source compute_starting_gold / compute_gold_per_second. Only replace the
	# untouched opening ledger: reconfiguring difficulty during a live match
	# must never erase purchases, earned gold or fractional income.
	if _arena_initialized or not structures.is_empty() or not units.is_empty():
		return
	if economy.spent != [0, 0] or economy.earned != [0, 0] or economy.refunded != [0, 0]:
		return
	if economy.passive != [0, 0] or economy.income_ticks != 0 or economy.income_milli != 0:
		return
	var gold := Economy.starting_gold(
		int(level_config.get("starting_gold", 1000)), level_number, difficulty
	)
	economy.opening[BLUE] = gold
	economy.gold[BLUE] = gold
	economy.income_per_second = Economy.passive_rate(level_number, difficulty)


func _apply_castle_start_levels() -> void:
	# Source Game.reset: the player castle climbs to cfg["starting_castle_level"]
	# for free while the red castle only climbs to cfg["castle_start_level"] when
	# hard-mode enemy scaling is on (otherwise it stays at level 1).
	var blue_target := int(level_config.get("starting_castle_level", 1))
	while nexuses[BLUE] != null and nexuses[BLUE].settings().level < blue_target:
		_raise_nexus_level(BLUE)
	var red_target := 1
	if enemy_scaling_enabled:
		red_target = int(level_config.get("castle_start_level", 1))
	while nexuses[RED] != null and nexuses[RED].settings().level < red_target:
		_raise_nexus_level(RED)


func _raise_nexus_level(team: int) -> void:
	# Castle.upgrade() is free and reuses _apply_level_stats through the shared
	# helper, so a configured start level never touches the ledger.
	var nexus := nexuses[team]
	if nexus == null or nexus.settings().level >= NexusUpgrades.LEVELS.size():
		return
	# The catalog index is the current level: entry i holds the stats of i + 1.
	_apply_nexus_stats(nexus, NexusUpgrades.LEVELS[nexus.settings().level])


func scaled_minion_definition(base: Definition, nexus_level: int) -> Definition:
	if base == null or nexus_level <= 1:
		return base
	if nexus_level < 1 or nexus_level > NexusUpgrades.MINION_SCALES.size():
		return null
	var scale: float = NexusUpgrades.MINION_SCALES[nexus_level - 1]
	var copy := base.duplicate() as Definition
	copy.max_hp = int(base.max_hp * scale)
	copy.damage = int(base.damage * scale)
	copy.speed_px_per_tick = base.speed_px_per_tick * (1.0 + (scale - 1.0) * 0.3)
	var haste := 1.0 + (scale - 1.0) * 0.2
	copy.attack_cooldown_ticks = maxi(10, int(base.attack_cooldown_ticks / haste))
	copy.gold_reward = int(base.gold_reward * scale)
	copy.regen_per_tick = base.regen_per_tick * scale
	return copy


func _spawn_match_minion(definition: Definition, team: int, lane: int) -> UnitState:
	# Port of the Minion.__init__ spread statements: uniform(-8, 8) on x and y
	# after the waypoint placement, then the lane Y offset (already applied by
	# spawn_unit). Wave construction only; the lab entry stays exact so the
	# existing contract tests can place units on demand.
	var unit := spawn_unit(definition, team, lane)
	if unit != null:
		unit.position += Vector2(
			spawn_rng.randf_range(-SPAWN_JITTER, SPAWN_JITTER),
			spawn_rng.randf_range(-SPAWN_JITTER, SPAWN_JITTER)
		)
	return unit


func nexus_level(team: int) -> int:
	if team not in [BLUE, RED] or nexuses[team] == null:
		return 1
	return nexuses[team].settings().level


func step_tick() -> void:
	hit_stop_froze_last_step = false
	boss_death_froze_last_step = false
	if not is_running():
		return
	_tick_boss_death_presentations()
	if hit_stop_state.consume_frame():
		hit_stop_froze_last_step = true
		_tick_hit_stop_hero_clocks()
		return
	if boss_death_pause_ticks > 0:
		boss_death_pause_ticks -= 1
		if boss_death != null and boss_death.is_death_active():
			step_boss_death()
		boss_death_froze_last_step = true
		return
	# Input transactions are handled by the session before this method.
	economy.step_tick(wave_count)
	step_level_intro()
	step_boss_intro()
	if boss_death != null and boss_death.is_active():
		step_boss_death()
	# Source wave gate ignores heroes; only living minions hold the field.
	var field_clear := living_minion_count() == 0
	var batch := scheduler.step_tick(
		field_clear, MAX_UNITS - units.size(), nexus_level(BLUE), nexus_level(RED)
	)
	wave_count = scheduler.wave
	if batch.started:
		AudioRuntime.play("wave_start")
		effects.announce_wave(wave_count)
		if wave_count == 1:
			(
				effects
				. show_path_preview(
					[
						map_renderer.get_lane_path("top"),
						map_renderer.get_lane_path("mid"),
						map_renderer.get_lane_path("bot"),
					]
				)
			)
		for nexus in nexuses:
			if nexus != null:
				nexus.set_wave(wave_count)
		# Source update_waves queues the scheduled boss before it fills the
		# ordinary minion queues. A live boss does not block later waves.
		_queue_scheduled_mini_boss(wave_count)
		_try_spawn_pending_mini_boss()
		# Source update_waves: the AI castle auto-levels while the wave starts.
		_auto_scale_ai_castle()
	for spawn in batch.spawns:
		_spawn_match_minion(MINIONS[spawn.kind], spawn.team, spawn.lane)
	super.step_tick()
	if winner in [BLUE, RED] and not _audio_result_announced:
		AudioRuntime.play("victory" if winner == BLUE else "defeat")
		_audio_result_announced = true
	# Source Game.update runs living Hero.update calls before Boss.update. Keep
	# the boss's target/attack phase after hero hits and movement from this tick.
	if is_running():
		_step_hero_act()
	# The Python true-boss check runs before the death-reward pass. Keep tower
	# deaths in a pending counter so a sixth tower triggers on the next tick,
	# exactly after the source reward loop has committed the event.
	_spawn_true_boss_if_ready()
	_step_active_boss()
	_process_boss_result()
	_flush_red_tower_deaths()
	if winner == BLUE and not _victory_unlocks_granted:
		_auto_unlock_defeated_boss_heroes()
		_victory_unlocks_granted = true
	_step_combo_clock()
	if is_running():
		_tick_auras_and_items()
		_tick_item_debuffs()
		_step_hero_respawns()
		# The active AI controller owns hero control through its per-tick
		# callback. Keep standalone hero control available when only that flag
		# is enabled, but never dispatch it twice in one production tick.
		if ai_enabled:
			_step_ai()
		elif ai_hero_control_enabled:
			_step_ai_heroes()
		# Source updates the tactical timers after the frame's unit actions.
		tactical.step_tick(self)


func activate_pending_hit_stop() -> void:
	hit_stop_state.activate_pending()


func _tick_hit_stop_hero_clocks() -> void:
	# Source _core.Game.update exception: keep hero skill clocks and debuffs
	# moving while the ordinary match simulation stays frozen.
	for unit in units:
		if not unit.is_hero:
			continue
		var hero := unit as HeroState
		if hero.active_skill_timer > 0:
			hero.active_skill_timer -= 1
			if hero.active_skill_timer <= 0:
				hero.active_skill = ""
		if hero.skill_timer > 0:
			hero.skill_timer -= 1
		if hero.w_cooldown > 0:
			hero.w_cooldown -= 1
		if hero.e_cooldown > 0:
			hero.e_cooldown -= 1
		if hero.r_cooldown > 0:
			hero.r_cooldown -= 1
		if hero.stun_timer > 0:
			hero.stun_timer -= 1
		_tick_debuffs(hero)
		hero.tick_item_debuffs()


func get_slot(id: int) -> Slot:
	return slots[id] if id >= 0 and id < slots.size() else null


func slot_at(point: Vector2) -> int:
	var closest := -1
	var distance := 24.0
	for slot in slots:
		var candidate := point.distance_to(slot.position)
		if candidate < distance:
			closest = slot.id
			distance = candidate
	return closest


func build_tower(team: int, slot_id: int, tower_path: String = "archer") -> bool:
	# Player and tests use this public transaction boundary; AI adds its reserve
	# through _build_tower_for. The source build popup offers all four Lv1 paths.
	return _build_tower_for(team, slot_id, tower_path)


func _build_tower_for(team: int, slot_id: int, path: String, reserve: int = 0) -> bool:
	transaction_error = ""
	var slot := get_slot(slot_id)
	if not is_running() or team not in [BLUE, RED]:
		transaction_error = "finished"
	elif slot == null or slot.id != slot_id or slot.team != team:
		transaction_error = "owner"
	elif slot.lane not in [0, 1, 2] or not slot.position.is_finite():
		transaction_error = "owner"
	elif slot.structure_id != -1:
		transaction_error = "occupied"
	elif path not in ["archer", "cannon", "ice", "mage"]:
		transaction_error = "path"
	elif economy.gold[team] < Economy.BUILD_COST + maxi(0, reserve):
		transaction_error = "gold"
	elif structures.size() >= structure_limit() or _next_id <= 0 or _by_id.has(_next_id):
		transaction_error = "capacity"
	if not transaction_error.is_empty():
		return false
	# Python constructs an Archer Lv1, then changes tower_type and reapplies
	# stats. Missing non-Archer Lv1 stats fall back to Archer Lv1, but path
	# identity (and thus projectile kind/muzzle and later upgrade) stays distinct.
	var definition: StructureDefinition = ARCHER
	if path != "archer":
		definition = ARCHER.duplicate() as StructureDefinition
		definition.id = path + "_level_1"
		definition.display_name = path.capitalize() + " Lv.1"
		definition.tower_path = path
	var tower := spawn_structure(definition, team, slot.position, slot.lane)
	if tower == null:
		transaction_error = "capacity"
		return false
	# No callbacks/await between validation and debit. Never put side effects in assert().
	economy.spend(team, Economy.BUILD_COST)
	slot.structure_id = tower.id
	_record({"kind": "build", "team": team, "slot_id": slot.id, "target_id": tower.id})
	return true


func player_roster() -> Array:
	# Source game.heroes contains paid player heroes in summon order and keeps
	# dead/respawning entries. Explicit IDs prevent enemy/free entities from
	# leaking into duplicate checks or the five-hero cap.
	var result: Array = []
	for hero_id in player_hero_ids:
		var hero := get_unit(hero_id) as HeroState
		if hero != null and hero.team == BLUE:
			result.append(hero)
	return result


func player_hero_spawn_position(owned_count: int) -> Vector2:
	# Game.try_buy_hero: radiant shop + (80 + len(heroes)*30 - 30, 10).
	var shop_pos: Array = map_renderer.radiant_shop_pos
	var shop := (
		Vector2(float(shop_pos[0]), float(shop_pos[1]))
		if shop_pos.size() >= 2
		else PLAYER_HERO_SHOP
	)
	return shop + Vector2(50 + owned_count * 30, 10)


func buy_player_hero(hero_type: String) -> bool:
	# Atomic port of Game.try_buy_hero. Permanent unlock currency is separate;
	# this transaction spends only match gold and summons one real native kit.
	transaction_error = ""
	var kit: HeroDefinition = HERO_ROSTER.get(hero_type) as HeroDefinition
	var roster := player_roster()
	if not is_running():
		transaction_error = "finished"
	elif hero_type not in purchased_heroes:
		transaction_error = "locked"
	elif kit == null or kit.id != hero_type or kit.cost <= 0:
		transaction_error = "kit"
	elif roster.size() != player_hero_ids.size():
		transaction_error = "registry"
	else:
		for hero in roster:
			if get_unit(hero.id) != hero or hero.definition == null:
				transaction_error = "registry"
				break
			if hero.definition.id == hero_type:
				transaction_error = "owned"
				break
		if transaction_error.is_empty() and roster.size() >= MAX_HEROES_OWNED:
			transaction_error = "capacity"
		elif transaction_error.is_empty() and economy.gold[BLUE] < kit.cost:
			transaction_error = "gold"
		elif (
			transaction_error.is_empty()
			and (units.size() >= MAX_UNITS or _next_id <= 0 or _by_id.has(_next_id))
		):
			transaction_error = "capacity"
	if not transaction_error.is_empty():
		return false
	var position := player_hero_spawn_position(roster.size())
	var hero := spawn_hero(kit, BLUE, position)
	if hero == null:
		transaction_error = "capacity"
		return false
	player_hero_ids.append(hero.id)
	_cache_hero_assets(hero)
	economy.spend(BLUE, kit.cost)
	_record({"kind": "hero_buy", "team": BLUE, "target_id": hero.id, "hero_type": hero_type})
	AudioRuntime.play("hero_spawn")
	return true


func _buy_ai_hero(hero_type: String, cost: int, pos: Vector2) -> bool:
	# Draft callback: synchronous atomic red purchase, not a UI command.
	# Unregistered catalog entries have metadata only, not native kits yet.
	transaction_error = ""
	var kit: HeroDefinition = PLAYABLE_AI_HEROES.get(hero_type) as HeroDefinition
	if not is_running():
		transaction_error = "finished"
	elif kit == null or kit.id != hero_type or cost != kit.cost or cost <= 0:
		transaction_error = "kit"
	elif not pos.is_finite():
		transaction_error = "position"
	elif economy.gold[RED] < cost:
		transaction_error = "gold"
	elif units.size() >= MAX_UNITS or _next_id <= 0 or _by_id.has(_next_id):
		transaction_error = "capacity"
	else:
		var roster := _ai_roster()
		if roster.size() != ai_hero_ids.size():
			transaction_error = "registry"
		else:
			for unit in roster:
				if get_unit(unit.id) != unit or unit.definition == null:
					transaction_error = "registry"
					break
				if unit.definition.id == hero_type:
					transaction_error = "owned"
					break
			if transaction_error.is_empty() and roster.size() >= 5:
				transaction_error = "capacity"
			elif (
				transaction_error.is_empty()
				and pos != RED_HERO_SPAWN + Vector2(0, roster.size() * 40 - 40)
			):
				transaction_error = "position"
	if not transaction_error.is_empty():
		return false
	var hero := spawn_hero(kit, RED, pos)
	if hero == null:
		transaction_error = "capacity"
		return false
	ai_hero_ids.append(hero.id)
	economy.spend(RED, cost)
	_record({"kind": "hero_buy", "team": RED, "target_id": hero.id, "hero_type": hero_type})
	return true


func sell_tower(team: int, entity_id: int) -> bool:
	transaction_error = ""
	var tower := get_unit(entity_id) as StructureState
	var slot: Slot = null
	for candidate in slots:
		if candidate.structure_id == entity_id:
			slot = candidate
	if not is_running():
		transaction_error = "finished"
	elif team != BLUE or tower == null or not tower.alive or tower.team != team:
		transaction_error = "owner"
	elif tower.settings().structure_kind != "tower" or slot == null or slot.team != team:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	# Selling is NOT a death: no kill event, enemy credit, or death rewards.
	tower.alive = false
	_retire_dead()
	var flying: Array[Projectile] = []
	for shot in projectiles:
		if shot.source_id == entity_id or shot.target_id == entity_id:
			shot.active = false
		else:
			flying.append(shot)
	projectiles = flying
	economy.credit_sale(team, tower.sale_value())
	_record({"kind": "sale", "team": team, "target_id": entity_id})
	return true


func _on_death(source_team: int, target: UnitState) -> void:
	var before := credited_gold[source_team]
	super._on_death(source_team, target)
	var team_name := "blue" if target.team == BLUE else "red"
	var explosion_size := (
		"large" if target is StructureState else ("medium" if target is HeroState else "small")
	)
	effects.add_death_explosion(target.position.x, target.position.y, team_name, explosion_size)
	# Source Game's reward pass gives every enemy hero death a fixed 150 G;
	# HeroDefinition.gold_reward intentionally remains zero for base combat.
	if target is HeroState:
		credited_gold[source_team] += HERO_DEATH_REWARD
	var reward := credited_gold[source_team] - before
	economy.credit_kill(source_team, reward)
	if target.team == RED:
		if target is HeroState:
			effects.add_gold_popup(target.position.x, target.position.y, HERO_DEATH_REWARD)
			score += HERO_DEATH_REWARD
		elif target is StructureState:
			var scored_structure := target as StructureState
			if scored_structure.settings().structure_kind == "tower":
				effects.add_gold_popup(
					target.position.x, target.position.y, target.definition.gold_reward
				)
				score += target.definition.gold_reward
		else:
			# The source counts only defeated red minions for this statistic.
			effects.add_gold_popup(
				target.position.x, target.position.y, target.definition.gold_reward
			)
			score += target.definition.gold_reward
			total_kills += 1
			if combo_count > max_combo:
				max_combo = combo_count
			effects.combo_counter.add_kill()
	# The source increments red_towers_destroyed in its later reward loop,
	# not inside Tower.take_damage. Defer the counter until after the true-boss
	# check in this tick.
	if target is StructureState and target.team == RED:
		var structure := target as StructureState
		if structure.settings().structure_kind == "tower":
			_pending_red_tower_deaths += 1
	if not is_running():
		scheduler.cancel()


func _step_combo_clock() -> void:
	effects.update()


func _mini_boss_entries() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var source: Dictionary = level_config.get("mini_bosses", {})
	# Dictionary iteration preserves the source level literal order; the
	# source rolls waves independently, then zips them to these values.
	for raw_key in source.keys():
		result.append({"wave": int(raw_key), "boss_type": String(source[raw_key])})
	return result


func _roll_mini_boss_schedule() -> Dictionary:
	# Port of Game._roll_mini_boss_schedule: sample unique wave numbers, sort
	# them, then zip them to the source dictionary's boss order.
	var entries: Array[Dictionary] = _mini_boss_entries()
	if entries.is_empty():
		return {}
	var boss_count: int = entries.size()
	var low: int = 20 if difficulty == "easy" else 11
	var high: int = 40 if difficulty == "easy" else 30
	if high - low + 1 < boss_count:
		high = low + boss_count * 5
	var candidates: Array[int] = []
	for wave in range(low, high + 1):
		candidates.append(wave)
	var picked: Array[int] = []
	for index in range(boss_count):
		var selected_index: int = boss_rng.randi_range(index, candidates.size() - 1)
		var selected_wave: int = candidates[selected_index]
		candidates[selected_index] = candidates[index]
		candidates[index] = selected_wave
		picked.append(selected_wave)
	picked.sort()
	var schedule: Dictionary = {}
	for index in range(boss_count):
		schedule[picked[index]] = String(entries[index]["boss_type"])
	return schedule


func _queue_scheduled_mini_boss(wave: int) -> void:
	var boss_value: Variant = _mini_boss_schedule.get(wave, null)
	if boss_value == null:
		return
	pending_mini_bosses.append({"wave": wave, "boss_type": String(boss_value)})


func _spawn_boss(boss_type: String) -> BossState:
	if active_boss != null or boss_type.is_empty():
		return null
	var boss := BossState.new()
	var mid_lane := _pairs_to_packed(map_renderer.get_lane_path("mid"), paths[1])
	if not boss.setup(boss_type, mid_lane, boss_table):
		return null
	boss.id = _next_id
	_next_id += 1
	_by_id[boss.id] = boss
	if enemy_scaling_enabled:
		boss.apply_scaling(enemy_hp_mult, enemy_damage_mult, enemy_speed_mult)
	active_boss = boss
	_cache_boss_assets(boss)
	_configure_boss_intro(boss)
	return boss


func _find_target(unit: UnitState) -> UnitState:
	# Layer 8n: port of the boss arm of `Minion._get_enemies`. The source reads
	# its candidates from the spatial grid, and `Game.update` indexes the live
	# boss there (`spatial_heroes = spatial_heroes + [self.active_boss]`), so a
	# minion sees the boss inside `self.range + 30` (inclusive squared radius)
	# and `_find_target_smart` may return it. The native registry never holds
	# the boss (`active_boss` only lives in `_by_id`), so minions used to walk
	# straight through a boss without ever swinging at it.
	#
	# Order matters: the boss is the LAST indexed entry, while towers and bases
	# are appended by `_get_enemies` only after the grid results. The candidate
	# list is therefore units, boss, structures - which is what the source siege
	# group (`max_hp >= 1500`, first match wins) observes.
	var boss := active_boss
	if boss == null or not boss.alive or boss.team == unit.team:
		return super._find_target(unit)
	if unit.position.distance_to(boss.position) > unit.definition.attack_range_px + 30.0:
		return super._find_target(unit)
	var ordered: Array[UnitState] = []
	for candidate in units:
		if candidate.alive and candidate.team != unit.team:
			ordered.append(candidate)
	ordered.append(boss)
	for structure in structures:
		if structure.alive and structure.team != unit.team:
			ordered.append(structure)
	return _select_ai_target(unit, ordered)


func _structure_target(structure: StructureState) -> UnitState:
	# Port of the boss scan that `Tower.update` and `Castle.update` run after
	# their spatial-grid query in the source:
	#
	#     for u in all_units:
	#         if not getattr(u, "boss_type", None): continue
	#         if not u.alive or u.team == self.team: continue
	#         if math.hypot(u.x - self.x, u.y - self.y) <= self.range:
	#             if u not in enemies: enemies.append(u)
	#
	# That scan appends the boss LAST and `_find_target` keeps the later
	# candidate on an exact tie (`dist <= best_dist`), so an in-range boss wins
	# ties. The native base only scans `units`, which never holds the boss (it
	# is registered as `active_boss` in `_by_id`), so towers and the nexus used
	# to ignore a boss walking right past them. Range is inclusive, and only a
	# living enemy boss is appended, exactly like the source loop.
	var target := super._structure_target(structure)
	var boss := active_boss
	if boss == null or not boss.alive or boss.team == structure.team:
		return target
	var distance := structure.position.distance_to(boss.position)
	if distance > structure.definition.attack_range_px:
		return target
	if target == null or distance <= structure.position.distance_to(target.position):
		return boss
	return target


func _projectile_school(target: UnitState, school: String) -> String:
	# Layer 8q: port of `_entity.resolve_damage_school` for a structure shot that
	# lands on the boss. `Bullet._on_hit` calls
	# `target.take_damage(damage, team, damage_type='projectile')` with no
	# `school=` and no `source=`, and the resolver returns None for that
	# combination, so `Boss.take_damage` skips BOTH the armor and the
	# magic-resist branch - only resilience and the anti-burst cap apply. The
	# native path handed the shooter's declared school ("physical"/"magic") to
	# the boss instead, so every tower and nexus hit was cut by the boss armor
	# (8..32 armor -> 32%..66% less damage than the source).
	# Hero and minion targets keep the declared school: their callers and their
	# recorded mitigation are different code paths.
	if target is BossState:
		return "neutral"
	return school


func _cannon_splash(shot: Projectile, main: UnitState) -> void:
	# Layer 8r: port of the boss arm of the cannon splash. `Bullet._on_hit` runs
	# its splash loop over `all_units`, whose last element is the live boss
	# (`all_units = all_units + [self.active_boss]`), so a boss standing inside
	# `d <= splash_radius` of the impact point takes `int(damage * 0.6)` and
	# burns. The native registry never holds the boss (`active_boss` only lives
	# in `_by_id`), so cannon splash used to scorch every minion around a boss
	# while the boss itself took nothing.
	#
	# The source splash hit passes neither school nor source
	# (`u.take_damage(int(self.damage * 0.6), self.team)`), so the hit resolves
	# school-free and a lethal splash writes `_killed_by = None`: `-1` keeps that
	# attribution, exactly like the source-omitted cleave from layer 8k. The burn
	# goes through `BossState.apply_debuff`, whose alive guard is why a boss the
	# splash just killed stays unburned.
	super._cannon_splash(shot, main)
	var boss := active_boss
	if shot.splash_radius <= 0.0 or boss == null or boss == main:
		return
	if not boss.alive or boss.team == shot.team:
		return
	if boss.position.distance_to(main.position) > shot.splash_radius:
		return
	var splash_damage := int(float(shot.damage) * 0.6)
	if splash_damage <= 0:
		return
	_deliver_hit(
		-1, shot.team, boss, splash_damage, _projectile_school(boss, "physical"), shot.position
	)
	if boss.alive and shot.burn_dps > 0.0:
		boss.apply_debuff("burn", shot.burn_dps, shot.burn_duration, shot.team)


func _ice_main(shot: Projectile, main: UnitState) -> void:
	# Layer 8s: port of the polymorphic main-target arm of the ice impact. The
	# source calls `self.target.apply_slow(...)` /
	# `self.target.apply_debuff('atk_slow', ...)`, so a boss primary target runs
	# `Boss.apply_slow` / `Boss.apply_debuff`: tenacity (0.50) halves magnitude
	# AND duration and caps the magnitude at 0.35 (ice L6: 0.65/150 becomes
	# 0.325/75, atk 0.40 becomes 0.20). The world-level `apply_slow` stores the
	# raw mixin values instead, so an ice tower that aimed at the boss used to
	# freeze it twice as hard and twice as long as the source does.
	# Non-boss targets keep the base path untouched; the boss methods carry the
	# source `alive` guard themselves.
	var boss := main as BossState
	if boss == null:
		super._ice_main(shot, main)
		return
	boss.apply_slow(shot.slow_amount, shot.slow_duration)
	if shot.atk_slow_amount > 0.0:
		boss.apply_debuff("atk_slow", shot.atk_slow_amount, shot.slow_duration)


func _ice_aoe(shot: Projectile, main: UnitState) -> void:
	# Layer 8p: port of the boss arm of the ice level-6 freeze AOE. The source
	# loop runs over `all_units`, whose last element is the live boss
	# (`all_units = all_units + [self.active_boss]`), and slows each victim
	# polymorphically: `u.apply_slow(...)` plus `u.apply_debuff('atk_slow', ...)`.
	# A boss therefore runs `Boss.apply_slow` / `Boss.apply_debuff`, which cut
	# magnitude AND duration by tenacity (0.50) and cap the magnitude at 0.35.
	# The native registry never holds the boss (`active_boss` only lives in
	# `_by_id`), so the AOE froze every minion around a boss while the boss kept
	# full speed and full attack speed. Same-team, dead and primary-target
	# bosses stay out, exactly like the source `continue` guard.
	super._ice_aoe(shot, main)
	var boss := active_boss
	if shot.slow_aoe <= 0.0 or boss == null or boss == main:
		return
	if not boss.alive or boss.team == shot.team:
		return
	if boss.position.distance_to(main.position) > shot.slow_aoe:
		return
	boss.apply_slow(shot.slow_amount, shot.slow_duration)
	if shot.atk_slow_amount > 0.0:
		boss.apply_debuff("atk_slow", shot.atk_slow_amount, shot.slow_duration)


func _append_volley_targets(
	source: StructureState, target: UnitState, targets: Array[UnitState], count: int
) -> void:
	# Layer 8t: port of the boss arm of `Tower._shoot_archer` (level 5/6 volley)
	# and `Tower._shoot_mage` (level 2..6 chain bolts). `Tower.update` appends
	# the living in-range enemy boss to `enemies` after the spatial-grid unit
	# query and passes that same `enemies` list to `self._shoot(enemies)`, so
	# both `_shoot_archer` and `_shoot_mage` pick up the boss as a secondary
	# target once ordinary in-range enemy units have been added and
	# `len(targets) < num_shots` / `self.chain`. The native `units` array never
	# holds `active_boss` (`active_boss` only lives in `_by_id`), so an archer
	# volley used to refill its extra arrow(s) onto the primary target and a
	# mage tower used to drop the chain bolt to the boss completely.
	super._append_volley_targets(source, target, targets, count)
	var boss := active_boss
	if targets.size() >= count or boss == null or boss == target:
		return
	if not boss.alive or boss.team == source.team:
		return
	if source.position.distance_to(boss.position) <= source.definition.attack_range_px:
		targets.append(boss)


func _boss_enemies() -> Array[UnitState]:
	# Source Boss.update order: living units, then enemy towers, then enemy
	# bases. Nexuses are kept separate because `structures` stores them first.
	var enemies: Array[UnitState] = []
	if active_boss == null:
		return enemies
	for unit in units:
		if unit.alive and unit.team != active_boss.team:
			enemies.append(unit)
	for structure in structures:
		if (
			structure.alive
			and structure.team != active_boss.team
			and structure.settings().structure_kind == "tower"
		):
			enemies.append(structure)
	for nexus in nexuses:
		if nexus != null and nexus.alive and nexus.team != active_boss.team:
			enemies.append(nexus)
	return enemies


func _boss_target(enemies: Array[UnitState]) -> UnitState:
	if active_boss == null:
		return null
	var target: UnitState = null
	var best_distance := active_boss.attack_range + 100.0
	for enemy in enemies:
		var distance := active_boss.position.distance_to(enemy.position)
		if distance < best_distance:
			best_distance = distance
			target = enemy
	return target


func _boss_basic_attack(target: UnitState, enemies: Array[UnitState]) -> void:
	if active_boss == null:
		return
	var boss := active_boss
	boss.basic_attack_seq += 1
	boss.attack_facing = boss.facing
	boss.attack_lock_timer = mini(15, maxi(6, int(boss.attack_cooldown / 3)))
	# Boss.update passes source=self for its primary hit. Preserve the live
	# attacker ID so hero blind/evasion, reactive damage and item hooks can
	# resolve the boss; source cleave deliberately omits source.
	_deliver_hit(boss.id, boss.team, target, boss.damage, "physical", boss.position)
	var cleave_damage := int(boss.damage * boss.cleave_ratio)
	if cleave_damage > 0:
		for enemy in enemies:
			if (
				enemy != target
				and enemy.alive
				and boss.position.distance_to(enemy.position) <= boss.cleave_radius
			):
				# The source omits a school on cleave. Heroes still resolve that
				# normal hit through their physical armor/evasion path; the
				# generic unit path remains neutral when no school exists.
				var cleave_school := "physical" if enemy is HeroState else "neutral"
				_deliver_hit(-1, boss.team, enemy, cleave_damage, cleave_school, boss.position)
	boss.timer = boss.effective_attack_cooldown()


func _step_active_boss() -> void:
	# Layer 8e owns the source entrance gate and one-shot enrage transition;
	# Layer 8f view code consumes the stored intro/death presentation state.
	if active_boss == null or not active_boss.alive:
		return
	var boss := active_boss
	boss.advance_animation_clock()
	boss.begin_motion_tick()
	var burn_from_team := boss.burn_source_team()
	var burn_damage := boss.tick_tower_debuffs()
	if burn_damage > 0:
		var dealt := boss.take_damage(null, burn_damage, "fire", "neutral", burn_from_team)
		if dealt > 0:
			var boss_team := "blue" if boss.team == BLUE else "red"
			effects.add_damage_number(
				boss.position.x, boss.position.y - boss.radius, dealt, dealt > 100, "fire"
			)
			effects.add_hit_particles(boss.position.x, boss.position.y, boss_team, 6)
		boss.last_hit_source_id = -1
		if not boss.alive:
			_queue_boss_death_presentation(boss)
	if boss.stun_timer > 0:
		return
	if not boss.advance_combat_clock():
		return
	boss.timer = maxi(0, boss.timer - 1)
	if boss.ability_timer > 0:
		boss.ability_timer -= 1
	if boss.ability2_timer > 0:
		boss.ability2_timer -= 1
	if boss.ability_active_timer > 0:
		boss.ability_active_timer -= 1
		if boss.ability_active_timer <= 0:
			boss.ability_active = false
	var enemies := _boss_enemies()
	var target := _boss_target(enemies)
	if target == null:
		boss.target_id = -1
		boss.move_forward()
		BossAI.tick(self, boss, enemies, null, INF)
		return
	boss.target_id = target.id
	var distance := boss.position.distance_to(target.position)
	var ai_target: UnitState = target
	var ai_distance := distance
	if boss.is_in_attack_range(distance):
		boss.face_motion(target.position.x - boss.position.x, target.position.y - boss.position.y)
		if boss.timer == 0:
			_boss_basic_attack(target, enemies)
	else:
		if boss.boss_type in RANGED_BOSS_KITERS:
			boss.move_ranged_kite(target.position)
		else:
			boss.move_toward(target.position)
		# Source Boss.update only dispatches smart AI from its in-range branch.
		# Null still preserves the true-boss heal checked before target handling.
		ai_target = null
		ai_distance = INF
	BossAI.tick(self, boss, enemies, ai_target, ai_distance)


func _try_spawn_pending_mini_boss() -> bool:
	# Port of Game._try_spawn_pending_mini_boss: an active living boss holds
	# the queue; a dead one is cleared before the oldest pending wave is used.
	if active_boss != null:
		if active_boss.alive:
			return false
		_by_id.erase(active_boss.id)
		active_boss = null
	if pending_mini_bosses.is_empty():
		return false
	var entry: Dictionary = pending_mini_bosses.pop_front()
	var spawned := _spawn_boss(String(entry["boss_type"]))
	return spawned != null


func _spawn_true_boss_if_ready() -> bool:
	# Port of the true-boss condition in Game.update. The source threshold is
	# an event count, not the current number of missing red towers.
	if true_boss_spawned or red_towers_destroyed < 6 or active_boss != null:
		return false
	var boss_type := String(level_config.get("true_boss", ""))
	if boss_type.is_empty():
		return false
	var spawned := _spawn_boss(boss_type)
	if spawned == null:
		return false
	true_boss_spawned = true
	return true


func _queue_boss_death_presentation(boss: BossState) -> void:
	var snapshot := boss.death_presentation()
	if not snapshot.is_empty():
		boss_death_presentations.append(snapshot)
		var shake := float(snapshot.get("shake_intensity", 0))
		boss_screen_shake_intensity = maxf(boss_screen_shake_intensity, shake)
		boss_screen_shake_timer = maxi(boss_screen_shake_timer, 8)
		effects.add_death_explosion(
			boss.position.x,
			boss.position.y,
			String(snapshot.get("explosion_team", "red")),
			String(snapshot.get("explosion_size", "large"))
		)
		effects.shake_screen(shake)


func boss_presentation_offset() -> Vector2:
	if boss_screen_shake_timer <= 0 or boss_screen_shake_intensity <= 0.0:
		return Vector2.ZERO
	var phase := float(tick_count) * 1.7
	return Vector2(cos(phase), sin(phase * 1.23)) * boss_screen_shake_intensity


func _tick_boss_death_presentations() -> void:
	# DeathExplosion owns 20–35 tick sparks and an 8 tick central flash in the
	# source. Keep the payload independent from active_boss retirement.
	boss_screen_shake_timer = maxi(0, boss_screen_shake_timer - 1)
	boss_screen_shake_intensity *= 0.85
	if boss_screen_shake_intensity < 0.5:
		boss_screen_shake_intensity = 0.0
	var standing: Array[Dictionary] = []
	for snapshot in boss_death_presentations:
		var timer := int(snapshot.get("timer", 0))
		var flash := int(snapshot.get("flash_timer", 0))
		snapshot["timer"] = maxi(0, timer - 1)
		snapshot["flash_timer"] = maxi(0, flash - 1)
		if int(snapshot.get("timer", 0)) > 0 or int(snapshot.get("flash_timer", 0)) > 0:
			standing.append(snapshot)
	boss_death_presentations = standing


func _unlock_achievement(
	achievement_id: String,
	title: String,
	description: String,
	icon_type: String = "star",
	x: Variant = null,
	y: Variant = null
) -> bool:
	if achievements_unlocked.has(achievement_id):
		return false
	achievements_unlocked[achievement_id] = true
	effects.unlock_achievement(title, description, icon_type)
	if x != null and y != null:
		effects.add_damage_number(float(x), float(y) - 35.0, "🏆 %s" % title, false, "gold")
	return true


func _process_boss_kill(boss: BossState) -> void:
	# Port of Game._process_boss_kill: the boss kill is credited only when the
	# last hit came from a real hero of the other team (not None, not the
	# victim, not a tower/minion/castle). Source reads `boss._killed_by`, which
	# `Boss.take_damage` writes only on the lethal blow; the native boundary is
	# the attacker ID that `_deliver_hit` stores on every damaging hit (boss
	# basic hit with source in layer 8k, source-omitted cleave/burn in 8g),
	# which is the same blow because a missed hit never kills. Dead heroes stay
	# addressable in the registry, so a killer that died in the same tick still
	# resolves. Source also guards `killer is victim`, impossible here: a
	# BossState can never come back from the HeroState cast.
	if boss.last_hit_is_miasma_tick:
		return
	var killer := get_unit(boss.last_hit_source_id) as HeroState
	if killer == null or killer.team == boss.team:
		return
	# Source `_killer_is_hero` requires `hero_type` and `skills`; HeroState is
	# the only native unit carrying both, so the cast above is the whole gate.
	killer.kills += 1
	if killer.team != BLUE:
		return
	if boss.boss_class == "true":
		trueboss_kill_count += 1
		_unlock_achievement(
			"trueboss_kill_%d" % trueboss_kill_count,
			"TRUE BOSS SLAYER!",
			"%s slew TRUE BOSS %s" % [killer.settings().display_name, boss.display_name],
			"skull",
			boss.position.x,
			boss.position.y
		)
	else:
		miniboss_kill_count += 1
		_unlock_achievement(
			"miniboss_kill_%d" % miniboss_kill_count,
			"MINI BOSS SLAYER!",
			"%s slew %s" % [killer.settings().display_name, boss.display_name],
			"skull",
			boss.position.x,
			boss.position.y
		)


func _process_boss_result() -> void:
	# Port of the source defeated-boss reward/unlock pass. The death
	# presentation payload has already been copied before registry retirement.
	if active_boss == null or active_boss.alive or not active_boss.defeated:
		return
	var boss := active_boss
	var boss_type := boss.boss_type
	# Source runs the kill-attribution pass before it starts the boss-death
	# gameplay pause and pays out the reward.
	_process_boss_kill(boss)
	_configure_boss_death(boss)
	boss_death_pause_ticks = maxi(
		boss_death_pause_ticks, int(BOSS_DEATH_PAUSE_TICKS.get(boss.boss_class, 0))
	)
	economy.credit_kill(BLUE, boss.gold_reward)
	score += boss.gold_reward
	effects.add_gold_popup(boss.position.x, boss.position.y, boss.gold_reward)
	effects.register_kill("Allies", boss.display_name, "blue")
	boss_rewards.append({"boss_type": boss_type, "gold": boss.gold_reward})
	bosses_defeated_this_run += 1
	if not bosses_defeated_this_match.has(boss_type):
		bosses_defeated_this_match.append(boss_type)
	if not unlocked_bosses.has(boss_type):
		unlocked_bosses.append(boss_type)
		effects.unlock_achievement(
			"%s Defeated!" % boss.display_name, "Boss unlocked for Hero Shop!", "star"
		)
	_by_id.erase(boss.id)
	active_boss = null
	_try_spawn_pending_mini_boss()


func _flush_red_tower_deaths() -> void:
	if _pending_red_tower_deaths <= 0:
		return
	red_towers_destroyed += _pending_red_tower_deaths
	_pending_red_tower_deaths = 0


func _auto_unlock_defeated_boss_heroes() -> Array[String]:
	# Source _auto_unlock_defeated_boss_heroes: victory makes every boss
	# defeated during this match a free permanent hero unlock. The match-local
	# purchased list is merged into the profile only at the level-result save
	# boundary.
	for boss_type in bosses_defeated_this_match:
		if not unlocked_bosses.has(boss_type):
			unlocked_bosses.append(boss_type)
		if purchased_heroes.has(boss_type):
			continue
		purchased_heroes.append(boss_type)
		heroes_unlocked_this_match.append(boss_type)
		var hero_def: HeroDefinition = HERO_ROSTER.get(boss_type) as HeroDefinition
		var hero_name := hero_def.display_name if hero_def != null else boss_type.capitalize()
		effects.unlock_achievement(
			"BOSS HERO UNLOCKED!", "%s is now yours to command!" % hero_name, "crown"
		)
	return heroes_unlocked_this_match


func _on_hero_death(hero: HeroState, source_id: int) -> void:
	super._on_hero_death(hero, source_id)
	# Source Hero.take_damage death branch (_entity.py:4742): the inventory
	# destroys Holy Rapier for good. The source does not recalculate max HP
	# there and the rapier carries no HP stat, so HP math stays untouched.
	hero.items.clear_on_death()
	# Source Game._process_hero_kill: credit only when the last hit came from a
	# real enemy hero (not the victim, not a tower/minion/castle). No popup.
	var killer := get_unit(source_id) as HeroState
	var killer_name := killer.settings().display_name if killer != null else "Tower"
	var killer_team := "blue" if hero.team == RED else "red"
	effects.register_kill(killer_name, hero.settings().display_name, killer_team)
	if killer == null or killer == hero or killer.team == hero.team:
		return
	killer.kills += 1


func _retire_dead() -> void:
	super._retire_dead()
	# Intentional fix: destroyed slots are released, not left permanently 'taken'.
	for slot in slots:
		var tower := get_unit(slot.structure_id)
		if tower == null or not tower.alive:
			slot.structure_id = -1


func set_hero_destination(hero_id: int, point: Vector2) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	hero.has_destination = true
	hero.destination = point
	hero.destination_auto = false
	hero.follow_id = -1
	return true


func _set_hero_autocast(hero_id: int) -> bool:
	# Port of the source toggle_autocast button (v29): the flag can only
	# be forced true, there is no off path. Blue only, like other orders.
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	hero.auto_cast_enabled = true
	return true


func _set_hero_follow(hero_id: int, target_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	var target := get_unit(target_id)
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	elif target == null or not target.alive or target.team == BLUE or target.id == hero.id:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	hero.follow_id = target.id
	hero.has_destination = false
	return true


func _step_hero_act() -> void:
	# Port living Hero.update states 1–6. Source runs this before Boss.update.
	var roster: Array = []
	for unit in units:
		if unit.is_hero and unit.alive:
			roster.append(unit)
	for entry in roster:
		_step_one_hero(entry as HeroState)


func _step_hero_respawns() -> void:
	# Source processes respawn timers after Boss.update and its reward pass.
	for unit in units:
		if unit.is_hero and not unit.alive:
			_step_hero_respawn(unit as HeroState)


func _step_one_hero(hero: HeroState) -> void:
	if not hero.alive:
		_step_hero_respawn(hero)
	elif hero.stun_timer > 0 or hero.is_dashing:
		pass
	else:
		_hero_passive_heal(hero)
		_step_hero_auto_cast(hero)
		var ratio := hero.hp / maxf(1.0, hero.max_hp)
		if ratio < HERO_RETREAT_HP:
			hero.is_retreating = true
		if hero.is_retreating and ratio >= HERO_HEAL_RATIO:
			hero.is_retreating = false
		if hero.has_destination and hero.destination_auto and hero_aggro_target(hero) != null:
			# Source: an AI destination yields to an enemy in aggro range in
			# the same frame; a manual destination is obeyed in full.
			hero.has_destination = false
			hero.destination_auto = false
		if hero.is_retreating:
			_step_hero_retreat(hero)
		elif hero.has_destination:
			_step_hero_destination(hero)
		elif _step_hero_follow(hero):
			pass
		else:
			var melee := _hero_pick_target(hero, hero.eff_attack_range(), true)
			if melee != null:
				if hero.attack_timer == 0:
					hero_basic_attack(hero.id, melee.id)
			else:
				var hunted := _hero_pick_target(hero, HERO_HUNT_RANGE, false)
				if hunted != null:
					_move_toward(hero, hunted.position)
				else:
					_move_toward(hero, _hero_push_point(hero))


func _step_hero_respawn(hero: HeroState) -> void:
	# Source: first sighting sets 600, then the same frame decrements.
	if hero.respawn_timer <= 0:
		hero.respawn_timer = 600
	hero.respawn_timer -= 1
	if hero.respawn_timer > 0:
		return
	hero.slow_amount = 0.0
	hero.slow_timer = 0
	hero.atk_slow_amount = 0.0
	hero.atk_slow_timer = 0
	hero.skill_down_amount = 0.0
	hero.skill_down_timer = 0
	hero.anti_heal_amount = 0.0
	hero.anti_heal_timer = 0
	hero.burn_dps = 0.0
	hero.burn_timer = 0
	hero.burn_accum = 0.0
	hero.alive = true
	hero.hp = hero.max_hp
	hero.killed_by = -1
	hero.position = _hero_spawn_point(hero)
	hero.has_destination = false
	hero.follow_id = -1
	hero.skill_timer = 0
	# Source Hero.respawn clears Q timer, not universal W/E/R cooldowns.
	# Preserve the original Kaizen rebuild contract; new kits follow source.
	if hero.settings().id == "kaizen":
		hero.w_cooldown = 0
		hero.e_cooldown = 0
		hero.r_cooldown = 0
	if hero.settings().id in ["kaizen", "thorne", "grimjaw", "sylara"]:
		hero.attack_timer = 0
	hero.q_stack = 0
	hero.q_reset_timer = 0
	hero.wind_wall_timer = 0
	hero.ulti_active = false
	hero.ulti_timer = 0
	hero.active_skill = ""
	hero.active_skill_timer = 0
	hero.is_dashing = false
	hero.dash_timer = 0
	hero.stun_timer = 0
	hero.target_id = -1
	hero.target_struct = null
	hero.is_retreating = false
	hero.respawn_timer = 0
	# Layer 5f (source Hero.respawn -> deliver_pending_forge_items): Forge
	# orders placed while the hero was dead land in the inventory now.
	forge.deliver_pending_forge_items(hero)


func try_auto_cast(hero: HeroState) -> void:
	# Port of Hero._try_auto_cast: only with a living enemy inside skill_range.
	# Priority R, then E (2+), W (HP < 40%), Q. The AI path calls this directly
	# (source _control_heroes), while the player path adds its own gating in
	# _step_hero_auto_cast.
	var nearby := _hero_skill_nearby(hero)
	if nearby <= 0:
		return
	var used := false
	if hero.r_cooldown <= 0:
		used = _cast_hero_r(hero.id, structures)
	if not used and hero.e_cooldown <= 0 and nearby >= 2:
		used = cast_hero_e(hero.id, structures)
	if not used and hero.w_cooldown <= 0 and hero.hp / maxf(1.0, hero.max_hp) < 0.4:
		used = cast_hero_w(hero.id)
	if not used and hero.skill_timer <= 0:
		used = cast_hero_q(hero.id, structures)
	if used:
		hero.spell_vamp_heal()


func _step_hero_auto_cast(hero: HeroState) -> void:
	# Player auto-cast: every 20 ticks, opt-in flag and no stun.
	if hero.auto_cast_enabled and hero.stun_timer <= 0:
		hero.auto_cast_check_timer -= 1
		if hero.auto_cast_check_timer <= 0:
			hero.auto_cast_check_timer = 20
			try_auto_cast(hero)


func move_to(hero: HeroState, point: Vector2, auto: bool) -> void:
	# Port of Hero.move_to: a new destination cancels follow and retreat.
	hero.has_destination = true
	hero.destination = point
	hero.destination_auto = auto
	hero.follow_id = -1
	hero.is_retreating = false


func hero_aggro_target(hero: HeroState) -> UnitState:
	# Port of Hero._find_aggro_target: nearest enemy inside HERO_AGGRO_RANGE
	# (the source updates on `<=`, so an equidistant later unit wins).
	var best: UnitState = null
	var best_dist := HERO_AGGRO_RANGE
	for unit in units:
		if not unit.alive or unit.team == hero.team or unit.id == hero.id:
			continue
		var dist := hero.position.distance_to(unit.position)
		if dist <= best_dist:
			best_dist = dist
			best = unit
	if active_boss != null and active_boss.alive and active_boss.team != hero.team:
		var boss_dist := hero.position.distance_to(active_boss.position)
		if boss_dist <= best_dist:
			best_dist = boss_dist
			best = active_boss
	return best


func _tick_item_debuffs() -> void:
	# Layer 5b-3: every ordinary unit decays its target-side item debuffs.
	# BossState ticks both item and tower debuffs inside _step_active_boss(),
	# before its stun/entrance gates, so it must not be advanced a second time.
	for unit in units:
		unit.tick_item_debuffs()


func apply_slow(target_id: int, amount: float, duration: int) -> bool:
	# Layer 5b-2: port of TowerDebuffMixin.apply_slow's item gate — slow resist
	# (Abyss Breaker) scales the incoming slow before the strongest-wins store.
	var target := get_unit(target_id)
	if target is HeroState:
		var resist := (target as HeroState).items.get_slow_resist()
		if resist > 0.0:
			amount *= 1.0 - resist
	return super.apply_slow(target_id, amount, duration)


func set_ai_enabled(enabled: bool) -> void:
	# Layer 6e: single switch for the match. The real AI owns the red side and
	# the red heroes; with the switch off (a test or scene that wants a manual
	# red side) no red transaction ever happens.
	ai_enabled = enabled
	ai_hero_control_enabled = enabled


func reset_ai(seed_value: int = -1) -> void:
	# Source Game.reset() constructs a new AIPlayer: think clock, adapter
	# counters, hero-skill counter and the persistent draft all return to their
	# opening state. One seed drives every AI stream so a restart replays.
	ai_controller.reset(seed_value)
	# Restore the selected level, never a stale elite policy or recruitment pool.
	# The playable scene keeps the default selection of level 1.
	ai_controller.policy.level_number = level_number
	ai_draft.level_number = level_number
	ai_heroes.total_skills_cast = 0
	ai_build.total_built = 0
	ai_upgrades.total_upgraded = 0
	ai_upgrades.total_nexus_upgrades = 0
	ai_upgrades.total_hero_upgrades = 0
	ai_draft.purchase_target = ""
	ai_draft.purchase_target_cost = 0
	ai_draft.total_heroes_bought = 0
	ai_draft.source_levels = {}
	if seed_value >= 0:
		ai_build.rng.seed = seed_value + 1
		ai_draft.rng.seed = seed_value + 2
	else:
		ai_build.rng.randomize()
		ai_draft.rng.randomize()


func _step_ai() -> void:
	# Source Game.update: the AI runs once per tick, right after the entities.
	if not ai_enabled:
		return
	ai_controller.tick(Callable(self, "_step_ai_heroes"), Callable(self, "_ai_perform_step"))


func _ai_perform_step() -> bool:
	# Source _ai_step: one ordered priority scan. Gates and rolls live in
	# ai_policy.choose_step; every action goes through the real ledger adapter.
	return ai_controller.policy.choose_step(
		_ai_state(), Callable(self, "_ai_attempt"), Callable(ai_controller, "draw")
	)


func _ai_state() -> Dictionary:
	# Source _ai_step locals: empty build slots, purse, full AI-owned roster (dead
	# heroes included), own living towers that can still upgrade, and living towers.
	return {
		"empty_slots": _ai_empty_slots(),
		"gold": economy.gold[RED],
		"hero_count": _ai_roster().size(),
		"upgradeable_towers": ai_upgrades.tower_candidates(self).size(),
		"living_towers": _ai_living_towers().size(),
	}


func _ai_empty_slots() -> int:
	var count := 0
	for slot in slots:
		if slot != null and slot.team == RED and slot.structure_id == -1 and slot.lane in [0, 1, 2]:
			count += 1
	return count


func _ai_roster() -> Array:
	# Match AIPlayer.heroes, not every red HeroState in the scene. In particular,
	# setup_arena's free mirrored Kaizen is a combat fixture, not AI-owned.
	var heroes: Array = []
	for hero_id in ai_hero_ids:
		var hero := get_unit(hero_id) as HeroState
		if hero != null and hero.team == RED:
			heroes.append(hero)
	return heroes


func _ai_living_towers() -> Array:
	var towers: Array = []
	for structure in structures:
		if (
			structure.alive
			and structure.team == RED
			and structure.settings().structure_kind == "tower"
		):
			towers.append(structure)
	return towers


func _ai_attempt(step: String) -> bool:
	# Adapter per source priority; a false answer moves the scan to the next
	# priority, exactly like the source returning from _ai_step.
	var done := false
	if step == "build":
		done = ai_build.try_build(self, ai_draft)
	elif step == "buy_hero":
		done = ai_recruitment.try_buy(self, ai_draft)
	elif step == "upgrade_hero":
		done = ai_upgrades.try_hero_priority(self, ai_draft)
	elif step == "buy_item":
		done = ai_items.try_buy_priority(self, ai_draft)
	elif step == "upgrade_tower":
		done = ai_upgrades.try_tower_priority(self, ai_draft)
	elif step == "regen_shield":
		done = ai_shields.try_regen_priority(self, ai_draft)
	elif step == "castle_shield" or step == "upgrade_nexus":
		done = _ai_nexus_attempt(step)
	return done


func _ai_nexus_attempt(kind: String) -> bool:
	# Source passes my_nexus to both shield and upgrade actions; a destroyed
	# nexus simply fails the action.
	var nexus := nexuses[RED]
	if nexus == null or not nexus.alive:
		return false
	if kind == "castle_shield":
		return ai_shields.try_castle(self, ai_draft, nexus.id)
	return ai_upgrades.try_nexus(self, ai_draft, nexus.id)


func _step_ai_heroes() -> void:
	if not ai_hero_control_enabled:
		return
	var towers: Array = []
	for structure in structures:
		if structure.alive and structure.settings().structure_kind == "tower":
			towers.append(structure)
	ai_heroes.control_heroes(self, towers)


func _hero_skill_nearby(hero: HeroState) -> int:
	var reach: float = hero.skill_range
	var count := 0
	for unit in units:
		if not unit.alive or unit.team == hero.team or unit.id == hero.id:
			continue
		if hero.position.distance_to(unit.position) <= reach:
			count += 1
	for structure in structures:
		if not structure.alive or structure.team == hero.team:
			continue
		if hero.position.distance_to(structure.position) <= reach:
			count += 1
	if active_boss != null and active_boss.alive and active_boss.team != hero.team:
		if hero.position.distance_to(active_boss.position) <= reach:
			count += 1
	return count


func _deliver_hit(
	source_id: int,
	source_team: int,
	target: UnitState,
	raw_damage: int,
	school: String,
	origin: Vector2,
	damage_type: String = "normal"
) -> bool:
	# Layer 5b-4: port of the evasion/true-strike gate of Hero.take_damage.
	# Source `_school` is `resolve_damage_school`, which reads the attacker's
	# `dmg_school` first, so the incoming school is the right handle here.
	if (
		target is HeroState
		and _evaded(source_id, target as HeroState, raw_damage, school, damage_type)
	):
		return false
	if target is BossState:
		var boss := target as BossState
		if not is_running() or not boss.alive or source_team == boss.team:
			return false
		var attacker: Object = get_unit(source_id)
		var dealt := boss.take_damage(attacker, raw_damage, damage_type, school)
		if dealt < 0:
			return false
		if dealt > 0:
			var boss_team := "blue" if boss.team == BLUE else "red"
			effects.add_damage_number(
				boss.position.x, boss.position.y - boss.radius, dealt, dealt > 100, damage_type
			)
			effects.add_hit_particles(boss.position.x, boss.position.y, boss_team, 6)
		if attacker is HeroState and dealt > 0:
			(attacker as HeroState).damage_dealt += dealt
		boss.last_hit_source_id = source_id
		boss.last_hit_is_miasma_tick = false
		_record(
			{
				"kind": "hit",
				"source_id": source_id,
				"target_id": boss.id,
				"from": origin,
				"to": boss.position,
				"damage": dealt,
			}
		)
		if not boss.alive:
			_queue_boss_death_presentation(boss)
			_record({"kind": "death", "source_id": source_id, "target_id": boss.id})
		return true
	var before_hp := target.hp
	var before_shield := (target as StructureState).shield if target is StructureState else 0.0
	var landed := super._deliver_hit(
		source_id, source_team, target, raw_damage, school, origin, damage_type
	)
	if landed:
		var after_shield := (target as StructureState).shield if target is StructureState else 0.0
		var dealt := int(maxf(0.0, (before_hp - target.hp) + (before_shield - after_shield)))
		if dealt > 0:
			var unit_team := "blue" if target.team == BLUE else "red"
			var radius := target.definition.radius_px if target.definition != null else 0.0
			effects.add_damage_number(
				target.position.x, target.position.y - radius, dealt, dealt > 50, damage_type
			)
			effects.add_hit_particles(target.position.x, target.position.y, unit_team, 5)
	return landed


func _evaded(
	source_id: int, defender: HeroState, raw_damage: int, school: String, damage_type: String
) -> bool:
	# Source `_is_physical_hit`: only normal/projectile hits that are not magic
	# can miss. Blind (Solar Brand aura) has no setter in the source either, so
	# only evasion and true strike are live here.
	var physical := damage_type in ["normal", "projectile"] and school != "magic"
	if not physical or raw_damage <= 0:
		return false
	var attacker := get_unit(source_id)
	if attacker is HeroState and (attacker as HeroState).items.has_true_strike():
		return false
	var chance := defender.items.get_evasion()
	# Source: blind lives on the ATTACKER and shares one roll with evasion.
	if attacker != null and attacker.blind_timer > 0:
		chance = maxf(chance, attacker.blind_amount)
	return chance > 0.0 and _item_rng.randf() < chance


func _hero_passive_heal(hero: HeroState) -> void:
	if hero.hp < hero.max_hp:
		hero.heal_hp(HERO_PASSIVE_HEAL)


func _hero_home(hero: HeroState) -> Vector2:
	return LaneLayout.BLUE_BASE if hero.team == BLUE else LaneLayout.RED_BASE


func _hero_push_point(hero: HeroState) -> Vector2:
	return LaneLayout.RED_BASE if hero.team == BLUE else LaneLayout.BLUE_BASE


func _hero_spawn_point(hero: HeroState) -> Vector2:
	return HERO_SPAWN if hero.team == BLUE else RED_HERO_SPAWN


func _hero_near_own_base(hero: HeroState) -> bool:
	return hero.position.distance_to(_hero_home(hero)) < HERO_BASE_NEAR


func _step_hero_retreat(hero: HeroState) -> void:
	if _hero_near_own_base(hero):
		hero.heal_hp(HERO_BASE_HEAL)
	else:
		_move_toward(hero, _hero_home(hero))
	var melee := _hero_pick_target(hero, hero.eff_attack_range(), true)
	if melee != null and hero.attack_timer == 0:
		hero_basic_attack(hero.id, melee.id)


func _step_hero_destination(hero: HeroState) -> void:
	# Source: walk first, still swing if someone is in melee, then return
	# (hunt does not override a player click).
	var offset := hero.destination - hero.position
	var speed := _eff_speed(hero)
	if offset.length() <= speed:
		hero.position = hero.destination
		hero.has_destination = false
	else:
		_move_toward(hero, hero.destination)
	var melee := _hero_pick_target(hero, hero.eff_attack_range(), true)
	if melee != null and hero.attack_timer == 0:
		hero_basic_attack(hero.id, melee.id)


func _step_hero_follow(hero: HeroState) -> bool:
	if hero.follow_id < 0:
		return false
	var target := get_unit(hero.follow_id)
	if target == null or not target.alive or target.team == hero.team:
		hero.follow_id = -1
		return false
	var reach := hero.eff_attack_range()
	if hero.position.distance_to(target.position) <= reach:
		if hero.attack_timer == 0:
			hero_basic_attack(hero.id, target.id)
	else:
		_move_toward(hero, target.position)
	return true


func _hero_pick_target(hero: HeroState, reach: float, inclusive: bool) -> UnitState:
	var best: UnitState = null
	var best_dist := reach
	for unit in units:
		if not unit.alive or unit.team == hero.team or unit.id == hero.id:
			continue
		var distance := hero.position.distance_to(unit.position)
		if (distance <= best_dist) if inclusive else (distance < best_dist):
			best = unit
			best_dist = distance
	for structure in structures:
		if not structure.alive or structure.team == hero.team:
			continue
		var distance := hero.position.distance_to(structure.position)
		if (distance <= best_dist) if inclusive else (distance < best_dist):
			best = structure
			best_dist = distance
	if active_boss != null and active_boss.alive and active_boss.team != hero.team:
		var boss_distance := hero.position.distance_to(active_boss.position)
		if (boss_distance <= best_dist) if inclusive else (boss_distance < best_dist):
			best = active_boss
			best_dist = boss_distance
	return best


func upgrade_price(entity_id: int, target_path: String = "archer") -> int:
	var tower := _owned_tower(entity_id)
	if tower == null:
		return 0
	var level: int = tower.settings().level
	var path_now: String = tower.settings().tower_path
	var target: StructureDefinition = _upgrade_target(level, path_now, target_path)
	return target.upgrade_price if target != null else 0


func upgrade_tower(entity_id: int, expected_level: int, target_path: String = "archer") -> bool:
	return _upgrade_tower_for(BLUE, entity_id, expected_level, target_path)


func _upgrade_tower_for(
	team: int, entity_id: int, expected_level: int, target_path: String, reserve: int = 0
) -> bool:
	transaction_error = ""
	var tower := _owned_tower(entity_id, team)
	var target: StructureDefinition = null
	if tower != null:
		target = _upgrade_target(tower.settings().level, tower.settings().tower_path, target_path)
	var cost := target.upgrade_price if target != null else 0
	if not is_running():
		transaction_error = "finished"
	elif tower == null:
		transaction_error = "owner"
	elif tower.settings().level != expected_level:
		transaction_error = "stale"
	elif tower.settings().level == 1 and target == null:
		transaction_error = "path"
	elif cost <= 0:
		transaction_error = "max_level"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	# Source resets HP/shield fully but retains cooldown, target, regen timer and in-flight shots.
	economy.spend(team, cost)
	tower.definition = target
	tower.hp = tower.definition.max_hp
	tower.shield_max = tower.settings().shield_capacity
	tower.shield = tower.settings().shield_capacity
	_record({"kind": "upgrade", "target_id": tower.id, "level": tower.settings().level})
	return true


func _upgrade_target(current: int, current_path: String, target_path: String):
	# Source: level 1 requires an explicit valid path; later levels ignore
	# the argument and keep their path. Cannon, Ice and Mage start at level 2.
	if current < 1 or current >= 6:
		return null
	var path := current_path
	if current == 1:
		if target_path not in ["archer", "cannon", "ice", "mage"]:
			return null
		path = target_path
	if path == "cannon":
		return CannonUpgrades.LEVELS.get(current + 1) as StructureDefinition
	if path == "ice":
		return IceUpgrades.LEVELS.get(current + 1) as StructureDefinition
	if path == "mage":
		return MageUpgrades.LEVELS.get(current + 1) as StructureDefinition
	return Upgrades.LEVELS[current] as StructureDefinition


func nexus_upgrade_price(entity_id: int) -> int:
	var nexus := _owned_nexus(entity_id)
	if nexus == null or nexus.settings().level >= NexusUpgrades.LEVELS.size():
		return 0
	return NexusUpgrades.LEVELS[nexus.settings().level].upgrade_price


func upgrade_nexus(entity_id: int, expected_level: int) -> bool:
	return _upgrade_nexus_for(BLUE, entity_id, expected_level)


func _upgrade_nexus_for(team: int, entity_id: int, expected_level: int, reserve: int = 0) -> bool:
	transaction_error = ""
	var nexus := _owned_nexus(entity_id, team)
	var cost := 0
	if nexus != null and nexus.settings().level < NexusUpgrades.LEVELS.size():
		cost = NexusUpgrades.LEVELS[nexus.settings().level].upgrade_price
	if not is_running():
		transaction_error = "finished"
	elif nexus == null:
		transaction_error = "owner"
	elif nexus.settings().level != expected_level:
		transaction_error = "stale"
	elif cost <= 0:
		transaction_error = "max_level"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	economy.spend(team, cost)
	_apply_nexus_stats(nexus, NexusUpgrades.LEVELS[expected_level])
	_record({"kind": "nexus_upgrade", "target_id": nexus.id, "level": nexus.settings().level})
	return true


func _apply_nexus_stats(nexus: StructureState, target: StructureDefinition) -> void:
	# Port of Castle._apply_level_stats (and the tail of the paid upgrade):
	# the new HP keeps the old ratio plus the flat margin, and a purchased
	# castle shield keeps its percentage while the capacity follows the HP.
	var old_max: int = nexus.definition.max_hp
	var old_hp: float = nexus.hp
	var new_max: int = target.max_hp
	var ratio := old_hp / float(maxi(1, old_max))
	nexus.definition = target
	nexus.hp = mini(new_max, int(new_max * ratio) + (new_max - old_max) + 500)
	if nexus.castle_shield_purchased:
		var old_shield_max := maxf(1.0, nexus.shield_max)
		var shield_ratio := clampf(nexus.shield / old_shield_max, 0.0, 1.0)
		nexus.shield_max = target.shield_capacity
		nexus.shield = int(nexus.shield_max * shield_ratio)


func _auto_scale_ai_castle() -> void:
	# Port of Game._auto_scale_ai_castle: with every new wave the AI castle
	# levels on the source schedule (4/7/10/13 -> 2/3/4/5). The upgrade is
	# free — the source only calls Castle.upgrade(), which never touches gold;
	# the player still pays for its own nexus upgrades.
	var target_level := 1
	if wave_count >= 4:
		target_level = 2
	if wave_count >= 7:
		target_level = 3
	if wave_count >= 10:
		target_level = 4
	if wave_count >= 13:
		target_level = 5
	var nexus := nexuses[RED]
	while (
		nexus != null
		and nexus.alive
		and nexus.settings().level < target_level
		and nexus.settings().level < NexusUpgrades.LEVELS.size()
	):
		_apply_nexus_stats(nexus, NexusUpgrades.LEVELS[nexus.settings().level])


func _owned_nexus(entity_id: int, team: int = BLUE) -> StructureState:
	if team not in [BLUE, RED]:
		return null
	var nexus := get_unit(entity_id) as StructureState
	if nexus == null or not nexus.alive or nexus.team != team:
		return null
	if nexus.settings().structure_kind != "nexus":
		return null
	if nexuses[team] == null or nexuses[team].id != entity_id:
		return null
	return nexus


func _owned_tower(entity_id: int, team: int = BLUE) -> StructureState:
	if team not in [BLUE, RED]:
		return null
	var tower := get_unit(entity_id) as StructureState
	if tower == null or not tower.alive or tower.team != team:
		return null
	if tower.settings().structure_kind != "tower":
		return null
	for slot in slots:
		if slot.team == team and slot.structure_id == entity_id:
			return tower
	return null


func blue_hero() -> HeroState:
	for unit in units:
		if unit.is_hero and unit.team == BLUE:
			return unit as HeroState
	return null


func cast_hero_q(hero_id: int, structures: Array = []) -> bool:
	var hero := get_unit(hero_id) as HeroState
	var source_q2 := hero != null and hero.settings().id == "kaizen" and hero.q_stack == 1
	var cast := super.cast_hero_q(hero_id, structures)
	if cast:
		_trigger_source_cast_hit_stop(hero_id, "q")
		if source_q2 and hero != null and hero.is_dashing:
			_trigger_source_dash_hit_stop(hero_id, "q")
	return cast


func cast_hero_w(hero_id: int) -> bool:
	var cast := super.cast_hero_w(hero_id)
	if cast:
		_trigger_source_cast_hit_stop(hero_id, "w")
	return cast


func cast_hero_e(hero_id: int, structures: Array = []) -> bool:
	var cast := super.cast_hero_e(hero_id, structures)
	if cast:
		_trigger_source_cast_hit_stop(hero_id, "e")
	return cast


func _cast_hero_r(hero_id: int, structures: Array = []) -> bool:
	var cast := super._cast_hero_r(hero_id, structures)
	if cast:
		_trigger_source_cast_hit_stop(hero_id, "r")
	return cast


func _trigger_source_cast_hit_stop(hero_id: int, skill: String) -> void:
	var hero := get_unit(hero_id) as HeroState
	if hero == null:
		return
	var requests: Dictionary = SOURCE_CAST_HIT_STOP_SECONDS.get(hero.settings().id, {})
	if requests.has(skill):
		hit_stop_state.trigger(float(requests[skill]))


func _trigger_source_dash_hit_stop(hero_id: int, skill: String) -> void:
	var hero := get_unit(hero_id) as HeroState
	if hero == null or not hero.is_dashing:
		return
	var requests: Dictionary = SOURCE_DASH_HIT_STOP_SECONDS.get(hero.settings().id, {})
	if requests.has(skill):
		hit_stop_state.trigger(float(requests[skill]))


func blue_q_ready(hero_id: int = -1) -> bool:
	var hero := blue_hero() if hero_id < 0 else get_unit(hero_id) as HeroState
	return hero != null and hero.team == BLUE and can_cast_hero_q(hero.id, structures)


func cast_blue_q(hero_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	if not cast_hero_q(hero.id, structures):
		transaction_error = "skill"
		return false
	hero.spell_vamp_heal()
	_record({"kind": "skill_q", "target_id": hero.id})
	return true


func _cast_blue_w(hero_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	if not cast_hero_w(hero.id):
		transaction_error = "skill"
		return false
	hero.spell_vamp_heal()
	_record({"kind": "skill_w", "target_id": hero.id})
	return true


func _cast_blue_e(hero_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	if not cast_hero_e(hero.id, structures):
		transaction_error = "skill"
		return false
	hero.spell_vamp_heal()
	_record({"kind": "skill_e", "target_id": hero.id})
	return true


func _cast_blue_r(hero_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	if not _cast_hero_r(hero.id, structures):
		transaction_error = "skill"
		return false
	hero.spell_vamp_heal()
	_record({"kind": "skill_r", "target_id": hero.id})
	return true


func _upgrade_blue_hero(hero_id: int, expected_level: int) -> bool:
	return _upgrade_hero_for(BLUE, hero_id, expected_level)


func _upgrade_hero_for(team: int, hero_id: int, expected_level: int, reserve: int = 0) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	var cost := 0
	if hero != null:
		cost = hero.upgrade_cost()
	if not is_running():
		transaction_error = "finished"
	elif team not in [BLUE, RED] or hero == null or hero.team != team:
		transaction_error = "owner"
	elif team == BLUE and not hero.alive:
		transaction_error = "owner"
	elif hero.level != expected_level:
		transaction_error = "stale"
	elif cost <= 0:
		transaction_error = "max_level"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	economy.spend(team, cost)
	upgrade_hero(hero.id)
	_record({"kind": "hero_upgrade", "target_id": hero.id, "level": hero.level})
	return true


func activate_player_regen_shield(entity_id: int) -> bool:
	return _activate_regen_shield_for(BLUE, entity_id)


func activate_player_castle_shield(entity_id: int) -> bool:
	return _activate_castle_shield_for(BLUE, entity_id)


func _activate_regen_shield_for(team: int, entity_id: int, reserve: int = 0) -> bool:
	return _purchase_shield_for(team, entity_id, false, reserve)


func _activate_castle_shield_for(team: int, entity_id: int, reserve: int = 0) -> bool:
	return _purchase_shield_for(team, entity_id, true, reserve)


func _purchase_shield_for(team: int, entity_id: int, castle: bool, reserve: int) -> bool:
	transaction_error = ""
	var target := _owned_nexus(entity_id, team) if castle else _owned_tower(entity_id, team)
	var cost := StructureState.CASTLE_SHIELD_COST if castle else StructureState.REGEN_SHIELD_COST
	if not is_running():
		transaction_error = "finished"
	elif target == null:
		transaction_error = "owner"
	elif (
		not target.can_activate_castle_shield()
		if castle
		else not target.can_activate_regen_shield()
	):
		transaction_error = "shield"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	# No await/callback between eligibility, activation and the ledger debit.
	if castle:
		target.activate_castle_shield()
		if team == BLUE:
			effects.add_damage_number(
				target.position.x, target.position.y - 40.0, "CASTLE SHIELD!", false, "heal"
			)
	else:
		target.activate_regen_shield()
		if team == BLUE:
			effects.add_damage_number(
				target.position.x, target.position.y - 25.0, "SHIELD!", false, "heal"
			)
	economy.spend(team, cost)
	_record({"kind": "castle_shield" if castle else "regen_shield", "target_id": entity_id})
	return true


func _buy_item_for(team: int, hero_id: int, item_id: String, reserve: int = 0) -> bool:
	# Port of the AIPlayer._try_buy_item transaction half: eligibility, equip
	# and ledger debit stay atomic, price comes from the item catalog metadata.
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	var cost := 0
	if hero != null:
		cost = int(hero.items.item(item_id).get("cost", 0))
	if not is_running():
		transaction_error = "finished"
	elif team not in [BLUE, RED] or hero == null or hero.team != team:
		transaction_error = "owner"
	elif not hero.alive:
		transaction_error = "owner"
	elif item_id == "" or cost <= 0:
		transaction_error = "catalog"
	elif hero.items.used_slots() >= hero.items.max_slots():
		transaction_error = "slots"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	# The melee_only/magic_only gate is the only way the equip can still fail.
	if not hero.items.add(item_id):
		transaction_error = "gate"
		return false
	# Source HeroItemInventory.add recalculates max HP and heal amp inline.
	hero.apply_item_change()
	economy.spend(team, cost)
	_record({"kind": "hero_item", "target_id": hero.id, "item": item_id, "cost": cost})
	return true


# ── Item wiring (layer 5c-2): tick_timers + auto-triggers + damage notify ──
# ── Item wiring (layer 5c-2): tick_timers + auto-triggers + damage notify ──
var _item_rng := RandomNumberGenerator.new()


func _hero_enemy_list() -> Array:
	# Source _get_all_enemies returns alive enemies (units+towers+bases); this
	# rebuild only tracks units so far (towers/bases are StructureState and
	# included later by 5d auras).
	var enemies: Array = []
	for unit in units:
		if not unit.alive:
			continue
		# Layer 5e-3: heroes carry their scaled max_hp, minions their
		# definition max_hp (source minion.max_hp), so Miasma uses the real
		# % Max HP damage instead of falling to its 6-damage floor.
		var raw_max: Variant = unit.get("max_hp")
		if raw_max == null:
			raw_max = unit.definition.max_hp
		(
			enemies
			. append(
				{
					"id": unit.id,
					"pos": unit.position,
					"team": unit.team,
					"alive": true,
					"max_hp": 0 if raw_max == null else int(raw_max),
				}
			)
		)
	if active_boss != null and active_boss.alive:
		(
			enemies
			. append(
				{
					"id": active_boss.id,
					"pos": active_boss.position,
					"team": active_boss.team,
					"alive": true,
					"max_hp": active_boss.max_hp,
				}
			)
		)
	return enemies


func _bind_miasma_registry(hero: HeroState) -> void:
	var inventory_miasma: Dictionary = hero.items.miasma
	for key in inventory_miasma.keys():
		var target_id: int = int(key)
		var local_tracker: Dictionary = inventory_miasma[target_id]
		var shared_tracker: Dictionary = _miasma_registry.get(target_id, {})
		var source_id: int = int(local_tracker.get("source_id", hero.id))
		var source_team: int = int(local_tracker.get("source_team", hero.team))
		var source_pos: Vector2 = local_tracker.get("source_pos", hero.position) as Vector2
		if source_id < 0:
			source_id = hero.id
			source_team = hero.team
			source_pos = hero.position
		if shared_tracker.is_empty():
			local_tracker["source_id"] = source_id
			local_tracker["source_team"] = source_team
			local_tracker["source_pos"] = source_pos
			_miasma_registry[target_id] = local_tracker
			continue
		shared_tracker["source_id"] = source_id
		shared_tracker["source_team"] = source_team
		shared_tracker["source_pos"] = source_pos
		shared_tracker["damage"] = maxi(
			int(shared_tracker.get("damage", 0)), int(local_tracker.get("damage", 0))
		)
		shared_tracker["timer"] = maxi(
			int(shared_tracker.get("timer", 0)), int(local_tracker.get("timer", 0))
		)
		shared_tracker["tick_cd"] = mini(
			int(shared_tracker.get("tick_cd", 0)), int(local_tracker.get("tick_cd", 0))
		)
	hero.items.miasma = _miasma_registry


func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
	_bind_miasma_registry(source_hero)
	source_hero.items.miasma = _miasma_registry
	var bus := BattleItemEffects.new()
	bus.world = self
	bus.dealer_id = source_hero.id
	bus.dealer_team = source_hero.team
	bus.dealer_pos = source_hero.position
	return bus


func _aura_item_effects() -> BattleItemEffects:
	# Layer 8y: enemy unit auras (Everfrost Freezing Aura, Solar Brand
	# Scorched Earth, Searbrand Cauterize) call `u.apply_debuff(...)` /
	# `u.apply_miss_chance(...)` on every living unit in the source, so the
	# aura debuff arms go through the item bus where a BossState target runs
	# `BossState.apply_debuff`. Dealer identity is unused by the debuff
	# methods, so the bus only needs the world.
	var bus := BattleItemEffects.new()
	bus.world = self
	return bus


func _reflect_item_effects(_defender_team: int) -> ReflectItemEffects:
	var bus := ReflectItemEffects.new()
	bus.world = self
	bus.defender_team = _defender_team
	return bus


func _tick_hero_items(hero: HeroState) -> void:
	# Called every tick (dt=1) after skill ticks. First decrement timers
	# (tick_timers ported in 5c-1), then run auto-triggers.
	hero.items.tick_timers(1)
	(
		hero
		. items
		. set_hero_runtime(
			hero.id,
			hero.alive,
			hero.hp,
			int(hero.max_hp),
			hero.team,
			hero.facing,
			hero.position,
			hero.target_id,
		)
	)
	var enemies: Array = _hero_enemy_list()
	_bind_miasma_registry(hero)
	hero.items.tick_miasma(1, enemies, _battle_item_effects(hero))
	hero.items.tick_auto(1, enemies, _battle_item_effects(hero), _item_rng)
	# Apply HP regen result back to hero.
	hero.hp = hero.items.hero_hp


func _notify_item_damage(source_id: int, source_team: int, target: Object, damage: int) -> void:
	# Port of the post-mitigation notify hook in Hero.take_damage. Only hero
	# targets carry an inventory.
	if not (target is HeroState) or damage <= 0:
		return
	var src_alive := false
	var src_team := source_team
	if source_id >= 0:
		var src: Object = get_unit(source_id)
		if src != null:
			src_alive = src.alive
	var h: HeroState = target as HeroState
	h.items.set_hero_runtime(
		h.id, h.alive, h.hp, int(h.max_hp), h.team, h.facing, h.position, h.target_id
	)
	h.items.notify_damage_taken(
		damage, source_id, src_team, src_alive, _item_rng, _reflect_item_effects(h.team)
	)


# ── Layer 5d: aura + update_auras (hero_items.py ~2760) ──
const AURA_DEBUFF_DURATION := 30


func _tick_auras_and_items() -> void:
	# Source calls update_auras() once per frame from Game.update, then each
	# hero's tick timers/auto-triggers advance. Minions are exposed through
	# the live unit list so Everfrost/Solar/Sear auras can reach them.
	_update_auras()
	for unit in units:
		if (unit is HeroState) and unit.alive:
			_tick_hero_items(unit as HeroState)


func _collect_all_units() -> Array:
	# Source _collect_all_units: all living heroes + minions + active boss.
	var out: Array = []
	for unit in units:
		if unit != null and unit.alive:
			out.append(unit)
	if active_boss != null and active_boss.alive:
		out.append(active_boss)
	return out


func _update_auras() -> void:
	# Reset aura fields on every hero inventory first.
	var all_heroes: Array = []
	for unit in units:
		if (unit is HeroState) and unit.alive:
			var h: HeroState = unit as HeroState
			all_heroes.append(h)
			h.items.aura_armor = 0
			h.items.aura_as = 0
			h.items.aura_armor_reduction = 0
			h.items.aura_guard_block = 0

	# ── Scarlet Bulwark: Bulwark Guard ally aura (active-gated) ──
	var guards: Array = []
	var guard_active: Dictionary = _aura_catalog("scarlet_bulwark").get("active", {})
	var g_radius := float(guard_active.get("ally_radius", 0))
	var g_base := float(guard_active.get("base_block", 0))
	var g_hp_pct := float(guard_active.get("max_hp_block_pct", 0.0))
	for h in all_heroes:
		if h.items.has("scarlet_bulwark") and h.items.guard_timer > 0:
			guards.append(h)
	for h in all_heroes:
		for src in guards:
			if src.team != h.team:
				continue
			if src.position.distance_to(h.position) <= g_radius:
				var blk: int = int(g_base + int(src.max_hp) * g_hp_pct)
				if blk > h.items.aura_guard_block:
					h.items.aura_guard_block = blk

	# ── Everfrost / Solar Brand / Searbrand enemy unit auras ──
	var frost_src: Array = []
	var solar_src: Array = []
	var sear_src: Array = []
	for h in all_heroes:
		if h.items.has("everfrost_guard"):
			frost_src.append(h)
		if h.items.has("solar_brand"):
			solar_src.append(h)
		if h.items.has("searbrand"):
			sear_src.append(h)
	if not (frost_src.is_empty() and solar_src.is_empty() and sear_src.is_empty()):
		var f_cat: Dictionary = _aura_catalog("everfrost_guard").get("aura", {})
		var s_cat: Dictionary = _aura_catalog("solar_brand").get("aura", {})
		var se_cat: Dictionary = _aura_catalog("searbrand").get("aura", {})
		var f_r := float(f_cat.get("enemy_radius", 0))
		var f_as := float(f_cat.get("enemy_atk_slow", 0.0))
		var f_heal := float(f_cat.get("enemy_anti_heal", 0.0))
		var s_r := float(s_cat.get("enemy_radius", 0))
		var s_burn := float(s_cat.get("burn_dps", 0.0))
		var s_blind := float(s_cat.get("blind", 0.0))
		var se_r := float(se_cat.get("enemy_radius", 0))
		var se_heal := float(se_cat.get("enemy_anti_heal", 0.0))
		var se_burn := float(se_cat.get("burn_dps", 0.0))
		var aura_bus := _aura_item_effects()
		for u in _collect_all_units():
			if u is HeroState and (u as HeroState).shadow_realm_timer > 0:
				continue
			for src in frost_src:
				if u.team == src.team:
					continue
				if src.position.distance_to(u.position) <= f_r:
					# Layer 8y: the source Freezing Aura calls
					# `u.apply_debuff('atk_slow', f_as, 30)`
					# (`hero_items.py:2843-2844`), so a boss inside the 300 px
					# radius has to run the boss store (tenacity 0.50 cuts the
					# 0.30 payload to 0.15 and the 30 tick payload to 15)
					# instead of the world store the aura used before.
					# Minions/heroes keep the identical world path.
					aura_bus.apply_atk_slow(u.id, f_as, AURA_DEBUFF_DURATION)
					apply_anti_heal(u.id, f_heal, AURA_DEBUFF_DURATION)
					break
			for src in solar_src:
				if u.team == src.team:
					continue
				if src.position.distance_to(u.position) <= s_r:
					apply_burn(u.id, s_burn, AURA_DEBUFF_DURATION, src.team)
					# Source Scorched Earth also blinds: incoming physical
					# hits of the unit inside the aura can miss.
					u.apply_miss_chance(s_blind, AURA_DEBUFF_DURATION)
					break
			for src in sear_src:
				if u.team == src.team:
					continue
				if src.position.distance_to(u.position) <= se_r:
					apply_anti_heal(u.id, se_heal, AURA_DEBUFF_DURATION)
					apply_burn(u.id, se_burn, AURA_DEBUFF_DURATION, src.team)
					break

	_aura_steel_aegis(all_heroes)


func _aura_steel_aegis(all_heroes: Array) -> void:
	var sources: Array = []
	for h in all_heroes:
		if h.items.has("steel_aegis"):
			sources.append(h)
	if sources.is_empty():
		return
	var data: Dictionary = _aura_catalog("steel_aegis").get("aura", {})
	var ally_r := float(data.get("ally_radius", 0))
	var enemy_r := float(data.get("enemy_radius", 0))
	var a_armor: int = int(data.get("ally_armor", 0))
	var a_as: int = int(data.get("ally_attack_speed", 0))
	var e_red: int = int(data.get("enemy_armor_reduction", 0))
	for h in all_heroes:
		for src in sources:
			if src == h:
				continue
			var d: float = src.position.distance_to(h.position)
			if h.team == src.team:
				if d <= ally_r:
					h.items.aura_armor += a_armor
					h.items.aura_as += a_as
			else:
				if d <= enemy_r:
					h.items.aura_armor_reduction += e_red


func _aura_catalog(item_id: String) -> Dictionary:
	# Aura/active sub-tables live on the shared catalog already loaded into
	# each inventory; any alive hero's inventory returns the same dict.
	if units.is_empty():
		return {}
	for unit in units:
		if unit is HeroState:
			return (unit as HeroState).items.item(item_id)
	return {}


# ── Layer 5e: on-hit wiring (crit + lifesteal + cleave + on-hit procs) ──


func hero_basic_attack(hero_id: int, target_id: int) -> bool:
	# Override parent to apply item crit, bonus damage, ranged lifesteal and
	# melee/ranged on-hit procs. Base validation/cooldown/timers mirror the
	# parent; we patch the raw damage and add post-hit callbacks.
	var hero: HeroState = get_unit(hero_id) as HeroState
	var target: Object = get_unit(target_id)
	if not is_running() or hero == null or target == null:
		return false
	if not hero.alive or not target.alive:
		return false
	if hero.stun_timer > 0 or hero.items.is_veiled():
		return false
	if hero.position.distance_to(target.position) > hero.eff_attack_range():
		return false
	if hero.attack_timer != 0:
		return false
	var dx: float = target.position.x - hero.position.x
	if dx != 0.0:
		hero.facing = 1.0 if dx > 0.0 else -1.0
	hero.attack_facing = hero.facing
	hero.attack_seq += 1
	hero.attack_timer = hero.eff_attack_cd(hero.attack_cd_base)
	var raw: int = hero.damage + int(hero.items.get_bonus_damage())
	if hero.settings().id == "grimjaw" and hero.grimjaw_crit_timer > 0:
		raw *= 2
	hero.items.set_hero_runtime(
		hero.id,
		hero.alive,
		hero.hp,
		int(hero.max_hp),
		hero.team,
		hero.facing,
		hero.position,
		hero.target_id
	)
	var is_crit := false
	var rend: Variant = hero.items.get_rend_crit()
	if rend != null and target.id == hero.items.rend_target:
		raw = int(float(raw) * float(rend))
		is_crit = true
	if not is_crit:
		var cr: Array = hero.items.roll_crit(_item_rng)
		if bool(cr[0]):
			raw = int(float(raw) * float(cr[1]))
			is_crit = true
	_bind_miasma_registry(hero)
	var bus := _battle_item_effects(hero)
	if not hero.is_melee and hero.settings().id != "morgath":
		_hero_ranged_spawn(hero, target, raw)
		var ls: float = hero.items.get_lifesteal_pct()
		if ls > 0.0:
			hero.hp = minf(hero.max_hp, hero.hp + float(raw) * ls)
		hero.items.on_ranged_attack_hit(target.id, raw, _hero_enemy_list(), _item_rng, bus)
	else:
		var landed := _deliver_hit(hero.id, hero.team, target, raw, hero.dmg_school, hero.position)
		if landed and target.alive:
			hero.items.on_basic_attack_hit(target.id, raw, _hero_enemy_list(), _item_rng, bus)
	hero.hp = hero.items.hero_hp
	return true


func _hero_ranged_spawn(hero: HeroState, target: Object, damage: int) -> void:
	HeroProjectiles.spawn(hero_projectiles, hero, target, damage)
