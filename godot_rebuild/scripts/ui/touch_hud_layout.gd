extends RefCounted
## Layer 9bv21: `mobile/hud.py` (`TouchHUD`) as a native layout + input layer.
##
## The source touch HUD is what a phone player actually presses: PAUSE (`II`)
## and the FPS/debug capsule sit under the gold chip (or disappear when the
## right panel takes them over), SKIP appears during a cinematic, and
## REPLAY / NEXT LEVEL / MENU capsules appear on the victory/defeat screen,
## all inside the safe area. The Godot rebuild drew a container-based desktop
## bar instead, so these buttons and their exact geometry were missing.
##
## This module ports the parts that decide behaviour: `_build_layout`,
## `sync`, `hit_test`/`blocks` and `apply_hud_action`. Every number comes from
## the real source through `tests/touch_hud_source_oracle.py`; the painter is
## the next layer and is not claimed here.
##
## Source quirks kept on purpose:
## * `sync` never touches `back` - the BACK capsule stays hidden unless
##   another call site shows it (`main.py`).
## * `debug` is visible outside gameplay too, because the source rule only
##   checks cinematic and dock presence.
## * `hit_test` pushes the button's press animation as a side effect, so
##   `blocks()` (used to swallow arena taps) also animates it.

const LOGICAL_WIDTH := 1280
const MIN_TAP := 80
const TAP_PAD := 24
const PRESS_DECAY := 0.12
const PAUSE_Y := 158
const ROUND_SIZE := 52
const PAUSE_X_MIN := 22
const SAFE_PAD_X := 6
const DEBUG_GAP := 84
const CAPSULE_H := 58
const SKIP_INSET_RIGHT := 170
const SKIP_INSET_BOTTOM := 74
const CAPSULE_END_H := 62
const END_INSET_BOTTOM := 100
const END_GAP := 115

const KEYS: Array[String] = ["pause", "debug", "skip", "replay", "next_level", "menu", "back"]

const GOLD := Color8(255, 200, 70)
const DEBUG_BLUE := Color8(120, 200, 255)
const NEXT_GREEN := Color8(120, 230, 140)
const WHITE := Color8(235, 235, 245)
const GREY := Color8(120, 120, 135)

const TACTICAL_ACTIONS: Array[String] = [
	"gather", "protect_tower", "protect_castle", "attack_boss", "attack_damage_dealer"
]


static func _inflate(rect: Rect2i, dx: int, dy: int) -> Rect2i:
	@warning_ignore("integer_division")
	var hx := dx / 2
	@warning_ignore("integer_division")
	var hy := dy / 2
	return Rect2i(rect.position.x - hx, rect.position.y - hy, rect.size.x + dx, rect.size.y + dy)


static func _button(
	action: String, rect: Rect2i, label: String, shape: String, color: Color,
	font_size: int, visible: bool
) -> Dictionary:
	var hit := _inflate(rect, TAP_PAD, TAP_PAD)
	if hit.size.x < MIN_TAP or hit.size.y < MIN_TAP:
		hit = _inflate(
			rect, maxi(0, MIN_TAP - rect.size.x), maxi(0, MIN_TAP - rect.size.y)
		)
	return {
		"action": action,
		"rect": rect,
		"hit_rect": hit,
		"label": label,
		"sub": "",
		"shape": shape,
		"color": color,
		"font_size": font_size,
		"visible": visible,
		"enabled": true,
		"cooldown": 0.0,
		"press_anim": 0.0,
	}


## `TouchHUD._build_layout`: every button in the source's dict order.
## `safe` is `mobile_platform.safe_area()`. Whether the right panel exists only
## changes visibility (`sync`'s `panel_present`), never the geometry - the
## source stores it and checks it in `sync` alone.
static func build(safe: Rect2i) -> Dictionary:
	var right := safe.position.x + safe.size.x
	var bottom := safe.position.y + safe.size.y
	var bx := maxi(PAUSE_X_MIN, safe.position.x + SAFE_PAD_X)
	var mid: int = LOGICAL_WIDTH / 2
	var out := {}
	out["pause"] = _button(
		"pause",
		Rect2i(bx, PAUSE_Y, ROUND_SIZE, ROUND_SIZE),
		"II",
		"round",
		GOLD,
		22,
		true
	)
	out["debug"] = _button(
		"debug",
		Rect2i(bx + DEBUG_GAP, PAUSE_Y, ROUND_SIZE, ROUND_SIZE),
		"FPS",
		"round",
		DEBUG_BLUE,
		16,
		true
	)
	out["skip"] = _button(
		"skip",
		Rect2i(right - SKIP_INSET_RIGHT, bottom - SKIP_INSET_BOTTOM, 160, CAPSULE_H),
		"SKIP  >>",
		"capsule",
		GOLD,
		20,
		false
	)
	out["replay"] = _button(
		"replay",
		Rect2i(mid - 310, bottom - END_INSET_BOTTOM, 165, CAPSULE_END_H),
		"REPLAY",
		"capsule",
		GOLD,
		20,
		false
	)
	out["next_level"] = _button(
		"next_level",
		Rect2i(mid - END_GAP, bottom - END_INSET_BOTTOM, 200, CAPSULE_END_H),
		"NEXT LEVEL",
		"capsule",
		NEXT_GREEN,
		18,
		false
	)
	out["menu"] = _button(
		"menu",
		Rect2i(mid + END_GAP, bottom - END_INSET_BOTTOM, 165, CAPSULE_END_H),
		"MENU",
		"capsule",
		GOLD,
		22,
		false
	)
	out["back"] = _button(
		"back",
		Rect2i(safe.position.x + 8, safe.position.y + 6, 104, CAPSULE_H),
		"< BACK",
		"capsule",
		GOLD,
		20,
		false
	)
	return out


## `TouchHUD.sync`: visibility per match state plus the press-animation decay.
## `state` is the app screen ("game" / "menu"), `game_state` the match state
## ("playing" / "victory" / "defeat"). `has_next_level` mirrors
## `levels.get_next_level(game.level_number) is not None`.
static func sync(
	buttons: Dictionary,
	state: String,
	game_state: String,
	cinematic: bool,
	panel_present: bool,
	has_next_level: bool,
	show_debug := true
) -> void:
	var in_game := state == "game"
	var playing := in_game and game_state == "playing"
	var ended := in_game and (game_state == "victory" or game_state == "defeat")
	buttons["pause"]["visible"] = playing and not cinematic and not panel_present
	buttons["debug"]["visible"] = show_debug and not cinematic and not panel_present
	buttons["skip"]["visible"] = cinematic
	buttons["replay"]["visible"] = ended
	buttons["menu"]["visible"] = ended
	buttons["next_level"]["visible"] = ended and game_state == "victory" and has_next_level
	# `back` is deliberately untouched: the source never shows it from sync.
	for key in buttons:
		var press := float(buttons[key]["press_anim"])
		if press > 0.0:
			buttons[key]["press_anim"] = maxf(0.0, press - PRESS_DECAY)


## `TouchHUD.hit_test`: last drawn button wins (the source iterates the dict
## in reverse), a hidden button never answers, and a hit starts the press
## animation. Returns "" when nothing was hit.
static func hit_test(buttons: Dictionary, pos: Vector2i) -> String:
	for index in range(KEYS.size() - 1, -1, -1):
		var key := KEYS[index]
		if not buttons.has(key):
			continue
		var button: Dictionary = buttons[key]
		if not bool(button["visible"]):
			continue
		if (button["hit_rect"] as Rect2i).has_point(pos):
			button["press_anim"] = 1.0
			return key
	return ""


## `TouchHUD.blocks`: the point belongs to a button, so the arena ignores it.
static func blocks(buttons: Dictionary, pos: Vector2i) -> bool:
	return not hit_test(buttons, pos).is_empty()


## `apply_hud_action`: what the source does with a pressed action, expressed as
## intents instead of reaching into the game object. `has_game`/`has_tactical`
## mirror `ctx["game"]` and `game.tactical`, `has_menu` mirrors the menu being
## present, and `tower_team` is the selected tower's team (`""` = none).
static func action_intent(
	action: String,
	has_game := true,
	has_tactical := true,
	has_menu := true,
	tower_team := ""
) -> Dictionary:
	var intent := {
		"handled": false,
		"request_pause": false,
		"toggle_debug": false,
		"skip_cinematics": false,
		"replay_requested": false,
		"next_level_requested": false,
		"return_to_menu_requested": false,
		"menu_escape": false,
		"tactical_action": "",
		"tactical_tower": "",
	}
	match action:
		"pause":
			intent["handled"] = true
			intent["request_pause"] = true
			return intent
		"debug":
			intent["handled"] = true
			intent["toggle_debug"] = true
			return intent
	if action == "skip" and has_game:
		intent["handled"] = true
		intent["skip_cinematics"] = true
		return intent
	if action == "replay" and has_game:
		intent["handled"] = true
		intent["replay_requested"] = true
		return intent
	if action == "next_level" and has_game:
		intent["handled"] = true
		intent["next_level_requested"] = true
		return intent
	if action == "menu" and has_game:
		intent["handled"] = true
		intent["return_to_menu_requested"] = true
		return intent
	if action == "back" and has_menu:
		intent["handled"] = true
		intent["menu_escape"] = true
		return intent
	if has_game and has_tactical and TACTICAL_ACTIONS.has(action):
		intent["handled"] = true
		intent["tactical_action"] = action
		if action == "protect_tower" and tower_team == "blue":
			intent["tactical_tower"] = "blue"
		return intent
	return intent
