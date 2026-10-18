extends RefCounted
## Layer 9bi: the paint order of the world layers and the screen overlays.
## `draw_order_source_oracle.py` reads the order straight from the source with `ast`
## (`_core.py::Game.draw`, `_render.py::EffectManager.draw` / `draw_ui`), so the
## fixture holds the source's stack, not a hand-written list. The prototype view
## paints from the two order constants these checks read back.

const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/draw_order_source.json"


## Screen overlays in source order: `effects_ui` expands to `effects.draw_ui`'s layers.
static func _expected_overlays(data: Dictionary) -> Array:
	var expected: Array = []
	for token_value in data["game_draw"]:
		var token := String(token_value)
		if token == "effects_ui":
			expected.append_array(data["effects_draw_ui"])
		elif token in ["boss_intro", "level_intro", "boss_death"]:
			expected.append(token)
	return expected


## World layers in source order: `effects.draw` starts with the path preview.
static func _expected_world(data: Dictionary) -> Array:
	var expected: Array = []
	for token_value in data["game_draw"]:
		var token := String(token_value)
		if token == "effects":
			expected.append(data["effects_draw"][0])
			expected.append("effects")
		elif token == "tactical_world":
			expected.append("tactical")
	return expected


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Draw order fixture parses")
	if not (data is Dictionary):
		return
	var view := PrototypeView.new()
	_check_overlays(check, data, view.overlay_paint_order())
	_check_world(check, data, view.world_layer_order())
	view.free()


func _check_overlays(check: Callable, data: Dictionary, order: Array) -> void:
	var expected := _expected_overlays(data)
	check.call(
		expected == ["boss_intro", "wave_announcer", "achievement", "level_intro", "boss_death"],
		"The source stacks boss intro, announcer, achievement, level intro, boss death"
	)
	var live: Array = []
	for layer in order:
		if expected.has(layer):
			live.append(layer)
	check.call(
		live == expected, "The view paints the live overlays in source order: %s" % str(live)
	)
	check.call(
		order.find("boss_intro") < order.find("wave_announcer"),
		"The boss banner is painted BEFORE the wave announcer, so it never covers it"
	)
	check.call(order.back() == "boss_death", "The boss death animation is painted last")
	check.call(
		(
			order.find("combo_counter") > order.find("wave_announcer")
			and order.find("kill_feed") < order.find("achievement")
		),
		"Layers the source never draws keep their old slot between announcer and popup"
	)
	var seen := {}
	for layer in order:
		seen[layer] = true
	check.call(seen.size() == order.size(), "No overlay is painted twice")


func _check_world(check: Callable, data: Dictionary, order: Array) -> void:
	check.call(
		data["effects_draw"] == ["path_preview", "explosions", "particles", "floating_texts"],
		"EffectManager.draw paints path preview, explosions, particles, floating texts"
	)
	check.call(
		order == _expected_world(data),
		"The view paints path preview, effects, then tactical world visuals: %s" % str(order)
	)
