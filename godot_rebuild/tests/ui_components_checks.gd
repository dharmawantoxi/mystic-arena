extends RefCounted
## Layer 9ce: whole `ui_components/` folder coverage, proven from the source inventory.
##
## `ui_components/` is two files (4.300 lines): eleven UI components merged into
## `_bundle.py` (4.160 lines) plus a 140-line `sys.modules` shim. Most of the folder was
## already native from earlier layers, so this suite proves the inventory and replays the
## two pieces that were still missing:
##
## * `BaseUIComponent`'s shared toolbox (`_draw_shadow_rect`, `_draw_hp_bar`,
##   `_draw_close_button`) and `_popup_di_panel`/`panel_popup_pos` placement;
## * `PopupRenderer.draw` for `popup_type == "tower"`: the 380x440 panel frame, connector
##   line, premium gradient/flat branch, gold ticks, close button, then `_draw_tower_content`
##   with the HP bar, stat lines, specials, the `py + 300` regen-shield section, MAX LEVEL +
##   sell, the four path cards and the upgrade/sell pair.
##
## `tests/ui_components_source_oracle.py` runs the REAL source classes under the recording
## pygame shim, so every op, string, colour and clickable rect below is what pygame asks for.
## The suite also checks that all 122 symbols of the folder carry a classification whose
## target file exists and contains its token.

const Base = preload("res://scripts/ui/ui_component_base.gd")
const TowerPopup = preload("res://scripts/ui/tower_popup_layout.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/ui_components_source.json"
const TOWER_DATA := "res://data/towers/upgrade_paths.json"
const TOWER_PATHS := ["archer", "cannon", "ice", "mage"]
const KIND_HISTOGRAM := {
	"bake": 5, "dead": 13, "deviation": 1, "meta": 6, "native": 17, "ported": 80
}
const SOURCE_ONLY_KINDS := ["dead", "deviation", "meta"]


## The oracle's text metrics: `int(size * 0.55)` px per glyph, `size` px tall.
static func _fake_measure(text: String, font_size: int) -> Vector2i:
	return Vector2i(int(font_size * 0.55) * text.length(), font_size)


static func _value_equal(actual: Variant, expected: Variant) -> bool:
	if expected is Array:
		if not (actual is Array) or actual.size() != expected.size():
			return false
		for index in range(expected.size()):
			if not _value_equal(actual[index], expected[index]):
				return false
		return true
	if expected is Dictionary:
		if not (actual is Dictionary):
			return false
		var want: Dictionary = expected
		var got: Dictionary = actual
		if want.size() != got.size():
			return false
		for key in want:
			if not got.has(key) or not _value_equal(got[key], want[key]):
				return false
		return true
	if expected is float or expected is int:
		if not (actual is float or actual is int):
			return false
		return absf(float(actual) - float(expected)) < 1e-6
	return str(actual) == str(expected)


static func _first_mismatch(actual: Array, expected: Array) -> int:
	if actual.size() != expected.size():
		return mini(actual.size(), expected.size())
	for index in range(expected.size()):
		if not _value_equal(actual[index], expected[index]):
			return index
	return -1


func run(check: Callable) -> void:
	var data: Dictionary = _json(FIXTURE)
	check.call(not data.is_empty(), "ui_components fixture parses")
	if data.is_empty():
		return
	_check_inventory(check, data)
	_check_classification(check, data)
	_check_evidence(check, data)
	_check_base(check, data)
	_check_tower_popup(check, data)
	_check_view_wiring(check, data)


## Two files, 4.300 lines, eleven contiguous module blocks inside `_bundle.py`.
func _check_inventory(check: Callable, data: Dictionary) -> void:
	var folder: Dictionary = data["folder"]
	check.call(
		int(folder["count"]) == 2 and int(folder["lines"]) == 4300,
		"ui_components/ is two files and 4.300 lines: %s" % str(folder)
	)
	check.call(
		int(folder["files"]["_bundle.py"]) == 4160 and int(folder["files"]["__init__.py"]) == 140,
		"the bundle carries 4.160 lines and the shim 140"
	)
	var modules: Array = data["modules"]
	check.call(modules.size() == 11, "eleven merged modules are mapped: %d" % modules.size())
	var contiguous := true
	var total := 0
	for index in range(modules.size()):
		var row: Dictionary = modules[index]
		total += int(row["lines"])
		if index + 1 < modules.size():
			var next: Dictionary = modules[index + 1]
			if int(row["end"]) + 1 != int(next["start"]):
				contiguous = false
	check.call(contiguous, "the module ranges are contiguous")
	check.call(
		int(modules[modules.size() - 1]["end"]) == 4160 and total == 4118,
		"the mapped blocks run to the end of the bundle (%d lines)" % total
	)
	check.call(
		String(modules[0]["module"]) == "base_ui"
			and String(modules[10]["module"]) == "shop_hints",
		"the blocks start at base_ui and end at shop_hints"
	)


## 122 symbols, each with a kind, a target that exists and a token that target contains.
func _check_classification(check: Callable, data: Dictionary) -> void:
	var symbols: Dictionary = data["symbols"]
	check.call(
		int(symbols["count"]) == 122
			and int(symbols["modules"]) == 11
			and int(symbols["classes"]) == 14
			and int(symbols["methods"]) == 88,
		"the folder defines 11 modules, 14 classes and 88 methods: %s" % str(symbols)
	)
	var entries: Dictionary = data["classification"]
	check.call(entries.size() == 122, "all 122 symbols carry a classification")
	var kinds: Dictionary = data["classification_kinds"]
	var same := true
	for name in KIND_HISTOGRAM:
		if int(kinds.get(name, -1)) != int(KIND_HISTOGRAM[name]):
			same = false
	check.call(same, "the kind histogram is 80/17/13/6/5/1: %s" % str(kinds))
	var native: Array = []
	var deviations: Array = []
	for name in entries:
		var entry: Dictionary = entries[name]
		var kind := String(entry["kind"])
		if kind == "native":
			native.append(String(name))
		elif kind == "deviation":
			deviations.append(String(name))
	native.sort()
	check.call(
		native.size() == 17 and native.has("base_ui:BaseUIComponent._draw_hp_bar")
			and native.has("popup_renderer:PopupRenderer._draw_tower_content"),
		"17 native symbols cover the toolbox and the tower popup: %s" % str(native)
	)
	check.call(
		deviations == ["hero_portraits:HeroPortraits._apply_grayscale"],
		"one documented deviation: the un-owned portrait desaturation: %s" % str(deviations)
	)
	var cache := {}
	var missing_file: Array = []
	var missing_token: Array = []
	var source_only: Array = []
	for name in entries:
		var entry: Dictionary = entries[name]
		var target := String(entry["target"])
		var token := String(entry["token"])
		if target.is_empty() or token.is_empty():
			if not SOURCE_ONLY_KINDS.has(String(entry["kind"])):
				source_only.append(name)
			continue
		if not target.begins_with("godot_rebuild/"):
			source_only.append(name)
			continue
		var path := "res://" + target.trim_prefix("godot_rebuild/")
		if not cache.has(path):
			cache[path] = FileAccess.get_file_as_string(path)
			if String(cache[path]).is_empty():
				missing_file.append(target)
		var body: String = cache[path]
		if not missing_file.has(target) and not body.contains(token):
			missing_token.append(name)
	check.call(
		source_only.is_empty(),
		"every kind that names a Godot module points into the project: %s" % str(source_only)
	)
	check.call(
		missing_file.is_empty(),
		"every classification target exists in the Godot tree: %s" % str(missing_file)
	)
	check.call(
		missing_token.is_empty(),
		"every classification token is present in its target: %s" % str(missing_token)
	)


## The dead/stub evidence the classification leans on.
func _check_evidence(check: Callable, data: Dictionary) -> void:
	var stubs: Array = data["stubs"]
	var names: Array = []
	for row in stubs:
		names.append(String(row["name"]))
	check.call(
		names == ["draw", "draw", "draw"],
		"three whole-body stubs: BaseUIComponent.draw and both Notification.draw copies: %s"
		% str(names)
	)
	var duplicates: Dictionary = data["duplicates"]
	var notification: Dictionary = duplicates["Notification"]
	check.call(
		int(notification["copies"]) == 2 and bool(notification["identical"]),
		"the two Notification copies are byte-identical: %s" % str(notification)
	)
	for name in ["_FakeEntity", "_make_fake_boss", "_make_fake_hero"]:
		var entry: Dictionary = duplicates[name]
		check.call(
			int(entry["copies"]) == 2 and not bool(entry["identical"]),
			"%s exists twice and the panel copy diverged: %s" % [name, str(entry)]
		)
	var dead: Array = []
	for row in data["dead_helpers"]:
		dead.append(String(row["symbol"]))
	check.call(
		dead.has("base_ui:BaseUIComponent._draw_shadow_rect"),
		"the shared shadow helper is never called by the folder: %s" % str(dead)
	)
	check.call(
		(data["notifications"]["lines"] as Array).size() == 3,
		"the notification subsystem is documented as removed in `_core.UI`"
	)


## `BaseUIComponent` toolbox + `_popup_di_panel`, replayed from the source ops.
func _check_base(check: Callable, data: Dictionary) -> void:
	var base: Dictionary = data["base"]
	check.call(
		base["green"] == [50, 200, 50] and base["yellow"] == [255, 220, 0]
			and base["red"] == [220, 50, 50],
		"the HP-bar thresholds use the source GREEN/YELLOW/RED"
	)
	for row in base["shadow"]:
		var case: Dictionary = row["case"]
		var rect: Array = case["rect"]
		var ops := Base.shadow_ops(
			Rect2i(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])),
			int(case["alpha"]),
			int(case["border_radius"])
		)
		check.call(
			_first_mismatch(ops, row["ops"]) == -1,
			"_draw_shadow_rect alpha %d radius %d matches the source op"
			% [int(case["alpha"]), int(case["border_radius"])]
		)
	for row in base["hp_bar"]:
		var case: Dictionary = row["case"]
		var box := Rect2i(int(case["x"]), int(case["y"]), int(case["w"]), int(case["h"]))
		var ops := Base.hp_bar_ops(box, float(case["ratio"]), bool(case["show_bg"]))
		check.call(
			_first_mismatch(ops, row["ops"]) == -1,
			"_draw_hp_bar ratio %.2f (bg %s) matches the source ops"
			% [float(case["ratio"]), str(case["show_bg"])]
		)
	for row in base["close_button"]:
		var case: Dictionary = row["case"]
		var box := Rect2i(int(case["x"]), int(case["y"]), int(case["size"]), int(case["size"]))
		var ops := Base.close_button_ops(
			box, bool(case["hover"]), String(case["style"]), _fake_measure
		)
		check.call(
			_first_mismatch(ops, row["ops"]) == -1,
			"_draw_close_button %s size %d hover %s matches the source ops"
			% [String(case["style"]), int(case["size"]), str(case["hover"])]
		)
		check.call(
			_value_equal(row["rect"], [box.position.x, box.position.y, box.size.x, box.size.y]),
			"the close button registers exactly its source rect"
		)
	for row in data["popup_panel"]:
		var case: Dictionary = row["case"]
		var panel := Rect2i()
		if case["panel"] != null:
			var raw: Array = case["panel"]
			panel = Rect2i(int(raw[0]), int(raw[1]), int(raw[2]), int(raw[3]))
		var placed := Base.panel_position(int(case["w"]), int(case["h"]), panel)
		var result: Variant = row["result"]
		if result == null:
			check.call(
				placed.is_empty(),
				"panel_popup_pos rejects the %s popup" % String(case["label"])
			)
		else:
			check.call(
				placed == {"x": int(result["x"]), "y": int(result["y"])},
				"panel_popup_pos places the %s popup at %s"
				% [String(case["label"]), str(result)]
			)


func _tower_base() -> Dictionary:
	return {
		"name": "Archer Tower",
		"level": 3,
		"tower_type": "archer",
		"color": [100, 220, 120],
		"hp": 620.0,
		"max_hp": 1100,
		"damage": 26,
		"range": 190,
		"kills": 7,
		"lane": "mid",
		"is_player_built": true,
		"regen_shield_active": false,
		"regen_shield_cost": 300,
		"splash": 0,
		"slow": 0.0,
		"chain": 1,
		"double_shot": false,
		"burn_dps": 0,
		"atk_slow": 0.0,
		"skill_down": 0.0,
		"upgrade_cost": 325,
		"path_costs": {"archer": 325, "cannon": 325, "ice": 325, "mage": 325},
	}


func _frame_tower(overrides: Dictionary) -> Dictionary:
	var tower := _tower_base()
	tower.merge(overrides, true)
	tower["can_activate_regen_shield"] = bool(tower.get("regen_shield_ready", false))
	tower["can_upgrade"] = int(tower["level"]) < 6
	tower["sell_value"] = 40 + int(tower["level"]) * 25
	return tower


func _frame_state(frame: Dictionary) -> Dictionary:
	var panel: Variant = frame["panel"]
	var state := {
		"tower": _frame_tower(frame["tower"]),
		"gold": int(frame["gold"]),
		"mouse": Vector2i(int(frame["mouse"][0]), int(frame["mouse"][1])),
		"target": [640, 420],
		"cheap_alpha": bool(frame["cheap_alpha"]),
	}
	if panel is Array and panel.size() >= 4:
		state["panel"] = panel
	return state


func _check_tower_popup(check: Callable, data: Dictionary) -> void:
	var frames: Array = data["tower_popup"]
	check.call(frames.size() == 10, "the oracle pins ten tower-popup frames")
	var ops_total := 0
	var buttons_total := 0
	for frame in frames:
		ops_total += (frame["ops"] as Array).size()
		buttons_total += (frame["buttons"] as Dictionary).size()
	check.call(
		ops_total == 253 and buttons_total == 32,
		"the frames carry %d draw ops and %d clickable rects" % [ops_total, buttons_total]
	)
	for frame in frames:
		var built := TowerPopup.build(_frame_state(frame), _fake_measure)
		var mismatch := _first_mismatch(built["ops"], frame["ops"])
		check.call(
			mismatch == -1,
			"tower popup %s matches the source ops (first mismatch %d)"
			% [String(frame["label"]), mismatch]
		)
		check.call(
			_first_mismatch([built["buttons"]], [frame["buttons"]]) == -1,
			"tower popup %s registers the source button rects" % String(frame["label"])
		)
	for row in data["specials"]:
		var tower := _tower_base()
		var case: Dictionary = row["case"]
		tower.merge(case["tower"], true)
		check.call(
			_value_equal(TowerPopup.tower_specials(tower), row["specials"]),
			"_get_tower_specials %s -> %s" % [String(case["label"]), str(row["specials"])]
		)
	_check_tower_data(check, data)
	_check_tower_popup_helpers(check)


## The ten recorded frames only reach the green bar, the short title and the `mid` lane.
## These are the branches `_draw_tower_content` can take in play but the oracle never
## exercised, so the helpers are pinned directly (layer 9cq).
func _check_tower_popup_helpers(check: Callable) -> void:
	var tower := _tower_base()
	tower["max_hp"] = 0
	check.call(
		is_equal_approx(TowerPopup._ratio(tower), 0.0),
		"_ratio must not divide by a zero max_hp"
	)
	tower["max_hp"] = 1100
	tower["hp"] = -50.0
	check.call(
		is_equal_approx(TowerPopup._ratio(tower), 0.0),
		"_ratio must clamp negative hp to zero"
	)
	tower["hp"] = 1100.0
	check.call(
		is_equal_approx(TowerPopup._ratio(tower), 1.0),
		"_ratio of a full tower is 1.0"
	)
	var bands := [
		[0.75, TowerPopup.HP_GOOD], [0.51, TowerPopup.HP_GOOD],
		[0.5, TowerPopup.HP_MID], [0.26, TowerPopup.HP_MID],
		[0.25, TowerPopup.HP_LOW], [0.0, TowerPopup.HP_LOW],
	]
	for band in bands:
		check.call(
			TowerPopup._bar_color(band[0]) == band[1],
			"_bar_color(%.2f) must be %s" % [band[0], str(band[1])]
		)
	var lines := TowerPopup._stat_lines(tower)
	check.call(
		lines == ["DMG: 26  Range: 190", "Kills: 7  Lane: MID"],
		"_stat_lines renders the recorded DMG/Kills pair: %s" % str(lines)
	)
	tower["lane"] = ""
	lines = TowerPopup._stat_lines(tower)
	check.call(
		String(lines[1]) == "Kills: 7  Lane: -",
		"_stat_lines falls back to '-' without a lane: %s" % str(lines)
	)
	tower["lane"] = "top"
	check.call(
		String(TowerPopup._stat_lines(tower)[1]) == "Kills: 7  Lane: TOP",
		"_stat_lines upper-cases the lane"
	)
	var title := TowerPopup._title_text(tower, 380, _fake_measure)
	check.call(
		title == "Archer Tower Lv.3",
		"_title_text keeps 'name Lv.N' when it fits: %s" % title
	)
	tower["name"] = "Reinforced Archer Tower"
	title = TowerPopup._title_text(tower, 380, _fake_measure)
	check.call(
		title == "Lv.3 Archer",
		"_title_text falls back to 'Lv.N Kind' before ellipsising: %s" % title
	)
	title = TowerPopup._title_text(tower, 164, _fake_measure)
	check.call(
		title.ends_with("...") and title.length() < 11,
		"_title_text ellipsises the fallback in a narrow dock: %s" % title
	)
	check.call(
		TowerPopup.letter("MAX") == "M A X",
		"letter must space the popup labels like ui_theme.letter"
	)


## The shipped tower tables are the ones `_core.py` gives the popup.
func _check_tower_data(check: Callable, data: Dictionary) -> void:
	var catalog := TowerPopup.catalog()
	check.call(not catalog.is_empty(), "the tower popup data catalog loads")
	var types: Array = (data["tower_data"]["types"] as Array).duplicate()
	var shipped: Array = (catalog.get("types", {}) as Dictionary).keys()
	shipped.sort()
	check.call(shipped == types, "the four tower types ship as data: %s" % str(shipped))
	for path_type in TOWER_PATHS:
		var levels: Array = data["tower_data"]["levels"][path_type]
		var shipped_levels: Array = (catalog["paths"][path_type] as Dictionary).keys()
		shipped_levels.sort()
		check.call(
			shipped_levels == levels,
			"%s ships levels %s" % [path_type, str(levels)]
		)
	check.call(
		String(TowerPopup.type_info("archer").get("name", "")) == "Archer Tower"
			and int(
				TowerPopup.upgrade_stats("archer", 4).get("damage", 0)
			) == 72,
		"archer level 4 is DMG 72, exactly like TOWER_UPGRADE_PATHS"
	)


## The view paints the popup between the build popup and the hero panel, and only when the
## screen hands over a tower snapshot.
func _check_view_wiring(check: Callable, data: Dictionary) -> void:
	var view := PrototypeView.new()
	var order: Array = view.overlay_paint_order()
	check.call(
		(
			order.find("tower_popup") == order.find("build_popup") + 1
			and order.find("tower_popup") < order.find("hero_panel")
		),
		"the tower popup paints right after the build popup and before the hero panel"
	)
	var world := Prototype.new()
	check.call(
		view.tower_popup_draw_ops(world, _fake_measure).is_empty(),
		"an empty tower snapshot paints nothing"
	)
	var frame: Dictionary = data["tower_popup"][3]
	view.tower_popup_state = _frame_state(frame)
	check.call(
		_first_mismatch(
			view.tower_popup_draw_ops(
				world,
				_fake_measure,
				Vector2i(int(frame["mouse"][0]), int(frame["mouse"][1]))
			),
			frame["ops"]
		) == -1,
		"the view paints the supplied tower popup frame for frame"
	)
	var expected_buttons: Dictionary = frame["buttons"]
	var registered: Dictionary = TowerPopup.build(view.tower_popup_state, _fake_measure)["buttons"]
	check.call(
		_value_equal(registered, expected_buttons),
		"the popup hands the dock the same button rects the source registers"
	)
	view.free()


func _json(path: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}
