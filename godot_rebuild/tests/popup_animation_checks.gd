extends RefCounted
## Replays the `_render.py::PopupAnimation` source oracle fixture through the
## native port. `popup_animation_source_oracle.py` executes the real source
## block (including the module-level `_ease_out_back` it calls), so the easing
## curve is the source's, not a re-implementation.

const PopupAnimation = preload("res://scripts/ui/popup_animation.gd")
const HeroShopPanel = preload("res://scripts/ui/hero_shop_panel.gd")
const ItemForgePanel = preload("res://scripts/ui/item_forge_panel.gd")
const MetaHeroShopPanel = preload("res://scripts/ui/meta_hero_shop_panel.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/popup_animation_source.json"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Popup animation fixture parses")
	if not (data is Dictionary):
		return
	check.call(
		is_equal_approx(float(data["speed"]), PopupAnimation.SPEED), "Popup speed matches source"
	)
	var cases: Array = data["cases"]
	check.call(cases.size() == 2, "Source fixture covers show and hide")
	for entry in cases:
		_replay(entry as Dictionary, check)
	_check_runtime_wiring(check)


func _replay(entry: Dictionary, check: Callable) -> void:
	var label: String = entry["name"]
	var item := PopupAnimation.new()
	item.show()
	for _warmup in range(int(entry["warmup"])):
		item.update()
	if String(entry["action"]) == "hide":
		item.hide()
	var steps: Array = entry["steps"]
	for index in range(steps.size()):
		item.update()
		var expected: Array = steps[index]
		check.call(
			is_equal_approx(item.progress, float(expected[0])),
			"Progress matches source step %d: %s" % [index, label]
		)
		check.call(
			is_equal_approx(item.get_scale(), float(expected[1])),
			"Eased scale matches source step %d: %s" % [index, label]
		)
		check.call(
			item.get_offset_y() == int(expected[2]),
			"Slide offset matches source step %d: %s" % [index, label]
		)


func _check_runtime_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()

	var hero_shop := HeroShopPanel.new()
	hero_shop._build()
	hero_shop.bind(world)
	check.call(
		(
			not hero_shop.is_open
			and is_zero_approx(hero_shop.popup_animation.progress)
			and is_zero_approx(hero_shop.popup_animation.target)
		),
		"HeroShopPanel starts with closed PopupAnimation state"
	)
	hero_shop.set_open(true)
	hero_shop._process(1.0 / 60.0)
	var hero_open_state: Dictionary = hero_shop.popup_animation_state()
	check.call(
		(
			bool(hero_open_state.get("is_open", false))
			and is_equal_approx(float(hero_open_state.get("target", 0.0)), 1.0)
			and float(hero_open_state.get("progress", 0.0)) > 0.0
		),
		"HeroShopPanel.set_open(true) triggers PopupAnimation.show and advances on _process"
	)
	hero_shop.set_open(false)
	hero_shop._process(1.0 / 60.0)
	check.call(
		is_zero_approx(float(hero_shop.popup_animation_state().get("target", 1.0))),
		"HeroShopPanel.set_open(false) triggers PopupAnimation.hide"
	)
	hero_shop.free()

	var forge_panel := ItemForgePanel.new()
	forge_panel.bind(world)
	forge_panel.set_open(true)
	forge_panel._process(1.0 / 60.0)
	var forge_open_state: Dictionary = forge_panel.popup_animation_state()
	check.call(
		(
			bool(forge_open_state.get("is_open", false))
			and is_equal_approx(float(forge_open_state.get("target", 0.0)), 1.0)
			and float(forge_open_state.get("progress", 0.0)) > 0.0
		),
		"ItemForgePanel.set_open(true) triggers PopupAnimation.show and advances on _process"
	)
	forge_panel.press("itemshop_close")
	check.call(
		(
			not bool(forge_panel.popup_animation_state().get("is_open", true))
			and is_zero_approx(float(forge_panel.popup_animation_state().get("target", 1.0)))
		),
		"Closing ItemForgePanel via button press triggers PopupAnimation.hide"
	)
	forge_panel.free()

	var meta_shop := MetaHeroShopPanel.new()
	meta_shop._build()
	meta_shop.open_with_state({"meta_gold": 1000, "purchased_heroes": ["kaizen"]})
	meta_shop._process(1.0 / 60.0)
	var meta_open_state: Dictionary = meta_shop.popup_animation_state()
	check.call(
		(
			bool(meta_open_state.get("is_open", false))
			and is_equal_approx(float(meta_open_state.get("target", 0.0)), 1.0)
			and float(meta_open_state.get("progress", 0.0)) > 0.0
		),
		"MetaHeroShopPanel.open_with_state triggers PopupAnimation.show and advances on _process"
	)
	meta_shop.set_open(false)
	check.call(
		is_zero_approx(float(meta_shop.popup_animation_state().get("target", 1.0))),
		"MetaHeroShopPanel.set_open(false) triggers PopupAnimation.hide"
	)
	meta_shop.free()
