extends RefCounted
## Native port of `ui_components/_bundle.py::PopupRenderer` for `popup_type == "tower"`.
##
## The source popup is one `draw()` that (a) clamps the 380x440 panel to the mobile dock
## width, (b) relocates it into the right panel when `_popup_di_panel` has room, otherwise
## anchors it on the map with the connector line, (c) paints the premium panel, the gold
## corner ticks and the shared close button, then (d) dispatches to `_draw_tower_content`.
## The tower body is a fixed vertical flow: title, HP label + bar, two stat lines, the
## specials line, the early "Enemy Tower" return, the regen-shield section at `py + 300`,
## then MAX LEVEL + sell, the four path buttons (level 1) or upgrade + sell (level 2+).
##
## Every string, colour and y-step below is pinned by `tests/ui_components_source_oracle.py`,
## which runs the real source methods under the recording pygame shim.
##
## Tower type names, specials, colours and the per-level upgrade stats live in
## `data/towers/upgrade_paths.json` (generated from `_core.py` by the same oracle).

const UiComponentBase = preload("res://scripts/ui/ui_component_base.gd")
const UiTheme = preload("res://scripts/ui/ui_theme.gd")

const DATA_PATH := "res://data/towers/upgrade_paths.json"
const POPUP_W := 380
const POPUP_H := 440
const CLOSE_SIZE := 22
const CLOSE_INSET := 26
const CLOSE_TOP := 6
const TOP_BAR_HEIGHT := 40
const SCREEN_W := 1280
const SCREEN_H := 720
const CONNECTOR_GAP := 40
const CONNECTOR_OFFSET := 10
const REGEN_MIN_LEVEL := 4
const REGEN_SECTION_Y := 300
const EDGE_MARGIN := 10
const PANEL_MARGIN := 3
const TITLE_SIZE := 28
const TITLE_MAX_INSET := 90
const STAT_SIZE := 18
const STAT_STEP := 21
const SPECIAL_STEP := 22
const SPECIAL_GAP := 10
const HP_STEP := 24
const BAR_STEP := 20
const BAR_H := 8
const ENEMY_SIZE := 14
const MAX_LEVEL_SIZE := 22
const MAX_LEVEL_STEP := 36
const SELL_W := 150
const SELL_H := 34
const PATH_TITLE_SIZE := 20
const PATH_TITLE_STEP := 26
const PATH_BTN_H := 68
const PATH_GAP_X := 12
const PATH_GAP_Y := 8
const PATH_NAMES := ["archer", "cannon", "ice", "mage"]
const UPGRADE_BTN_H := 40
const UPGRADE_TEXT_SIZE := 18
const UPGRADE_SELL_INSET := 12
const PILL_FONT := "body_bold"
const PILL_SIZE := 17
const PILL_BTN_SIZE := 18
const ELLIPSIS := "..."

const GOLD := [255, 200, 50, 255]
## `ui_theme.GOLD` - the theme gold is a few shades lighter than `_core.GOLD`.
const UI_GOLD := [255, 205, 85]
const GOLD_BRIGHT := [255, 233, 158]
const GOLD_TEXT := [255, 220, 110, 255]
const CYAN_SOFT := [165, 220, 255, 255]
const TEXT_BODY := [198, 207, 230, 255]
const TEXT_DIM := [132, 142, 170, 255]
const WHITE := [255, 255, 255, 255]
const GRAY := [150, 150, 150, 255]
const RED_LIGHT := [255, 150, 150, 255]
# `_vgrad`/`_radial` take RGB (the recorder stores them without alpha).
const PANEL_TOP := [34, 40, 68]
const PANEL_BOTTOM := [16, 19, 36]
const FLAT_PANEL := [25, 30, 45, 255]
const LOCKED_EDGE := [70, 70, 80, 255]
const PATH_DESC := [215, 222, 240, 255]
const HP_GOOD := [120, 220, 120]
const HP_MID := [255, 200, 80]
const HP_LOW := [255, 100, 100]

static var _catalog: Dictionary = {}


## `_core.py` tower tables, shipped as data so the popup does not hard-code balance numbers.
static func catalog() -> Dictionary:
	if _catalog.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
		if parsed is Dictionary:
			_catalog = parsed
	return _catalog


static func type_info(tower_type: String) -> Dictionary:
	var types: Dictionary = catalog().get("types", {})
	return types.get(tower_type, {})


static func upgrade_stats(tower_type: String, level: int) -> Dictionary:
	var paths: Dictionary = catalog().get("paths", {})
	var per_type: Dictionary = paths.get(tower_type, {})
	return per_type.get(str(level), {})


## Panel geometry: dock relocation first (`_popup_di_panel`), else the map anchor with the
## source's four clamps.
static func geometry(state: Dictionary) -> Dictionary:
	var panel := _panel_rect(state)
	var popup_w := int(state.get("popup_w", POPUP_W))
	if panel.size.x > 0:
		popup_w = mini(popup_w, maxi(1, panel.size.x - 16))
	var popup_h := int(state.get("popup_h", POPUP_H))
	var px := 0
	var py := 0
	var in_panel := false
	if panel.size.x > 0:
		var placed := UiComponentBase.panel_position(popup_w, popup_h, panel)
		if not placed.is_empty():
			px = int(placed["x"])
			py = int(placed["y"])
			in_panel = true
	if not in_panel:
		var target := _point(state.get("target", [0, 0]))
		var screen := _point(state.get("screen", [SCREEN_W, SCREEN_H]))
		px = target.x - popup_w / 2
		py = target.y - popup_h - CONNECTOR_GAP
		if px < EDGE_MARGIN:
			px = EDGE_MARGIN
		if px + popup_w > screen.x - EDGE_MARGIN:
			px = screen.x - popup_w - EDGE_MARGIN
		if py < TOP_BAR_HEIGHT + EDGE_MARGIN:
			py = target.y + CONNECTOR_GAP
		if py + popup_h > screen.y - EDGE_MARGIN:
			py = screen.y - popup_h - EDGE_MARGIN
		if py < TOP_BAR_HEIGHT + EDGE_MARGIN:
			py = TOP_BAR_HEIGHT + EDGE_MARGIN
	return {
		"popup_w": popup_w,
		"popup_h": popup_h,
		"px": px,
		"py": py,
		"in_panel": in_panel,
	}


## `PopupRenderer.draw` for `popup_type == "tower"`; `ops` is the paint list.
static func ops(state: Dictionary, measure: Callable) -> Array:
	return build(state, measure)["ops"]


## Paint list plus the clickable rects the source writes into `game.ui_buttons`
## (`popup_close`, `popup_upgrade_path_*`, `popup_upgrade_tower`, `popup_sell_tower`,
## `popup_regen_shield`). `regen_shield_on` is a status pill with no registered button.
static func build(state: Dictionary, measure: Callable) -> Dictionary:
	var tower: Dictionary = state.get("tower", {})
	if tower.is_empty():
		return {"ops": [], "buttons": {}}
	var geo := geometry(state)
	var px := int(geo["px"])
	var py := int(geo["py"])
	var popup_w := int(geo["popup_w"])
	var popup_h := int(geo["popup_h"])
	var panel := Rect2i(px, py, popup_w, popup_h)
	var ops: Array = []
	if not bool(geo["in_panel"]):
		var target := _point(state.get("target", [0, 0]))
		ops.append({
			"kind": "line",
			"a": [px + popup_w / 2, py + popup_h],
			"b": [target.x, target.y - CONNECTOR_OFFSET],
			"color": GOLD,
			"width": 2,
		})
	if bool(state.get("cheap_alpha", true)):
		ops.append({
			"kind": "shadow",
			"rect": [
				px - PANEL_MARGIN,
				py - PANEL_MARGIN,
				popup_w + 8,
				popup_h + 8,
			],
			"radius": 10,
			"alpha": 150,
		})
		ops.append({
			"kind": "vgrad",
			"rect": _rect_array(panel),
			"top": PANEL_TOP,
			"bottom": PANEL_BOTTOM,
			"radius": 10,
		})
	else:
		ops.append(_rect_op(panel, FLAT_PANEL, 0, 10))
	ops.append(_rect_op(panel, GOLD, 2, 10))
	ops.append({
		"kind": "corner_ticks",
		"rect": _rect_array(panel),
		"color": GOLD_BRIGHT,
		"length": 12,
		"width": 2,
		"inset": 2,
	})
	var close_box := Rect2i(px + popup_w - CLOSE_INSET, py + CLOSE_TOP, CLOSE_SIZE, CLOSE_SIZE)
	var mouse := _point(state.get("mouse", [0, 0]))
	var buttons := {"popup_close": _rect_array(close_box)}
	ops.append(_section("_draw_close_button"))
	ops.append_array(
		UiComponentBase.close_button_ops(close_box, close_box.has_point(mouse), "rect", measure)
	)
	ops.append(_section("_draw_tower_content"))
	ops.append_array(_content_ops(state, measure, geo, buttons))
	return {"ops": ops, "buttons": buttons}


static func _content_ops(
	state: Dictionary, measure: Callable, geo: Dictionary, buttons: Dictionary
) -> Array:
	var tower: Dictionary = state.get("tower", {})
	var px := int(geo["px"])
	var py := int(geo["py"])
	var popup_w := int(geo["popup_w"])
	var gold := int(state.get("gold", 0))
	var mouse := _point(state.get("mouse", [0, 0]))
	var level := int(tower.get("level", 1))
	var ops: Array = []
	ops.append({
		"kind": "text",
		"text": _title_text(tower, popup_w, measure),
		"size": TITLE_SIZE,
		"style": "title",
		"color": _rgba(_lighten(tower.get("color", [0, 0, 0]), 40)),
		"pos": [px + 15, py + 10],
	})
	var y := py + 46
	ops.append({
		"kind": "text",
		"text": "HP: %d/%d" % [int(tower.get("hp", 0)), int(tower.get("max_hp", 0))],
		"size": STAT_SIZE,
		"style": "body_semibold",
		"color": TEXT_BODY,
		"pos": [px + 15, y],
	})
	y += HP_STEP
	var ratio := maxf(0.0, _ratio(tower))
	ops.append({
		"kind": "hp_bar",
		"rect": [px + 15, y, popup_w - 30, BAR_H],
		"ratio": ratio,
		"color": _bar_color(ratio),
	})
	y += BAR_STEP
	for line in _stat_lines(tower):
		ops.append({
			"kind": "text",
			"text": ellipsis(line, STAT_SIZE, popup_w - 30, measure),
			"size": STAT_SIZE,
			"style": "body_medium",
			"color": TEXT_DIM,
			"pos": [px + 15, y],
		})
		y += STAT_STEP
	var specials := tower_specials(tower)
	if not specials.is_empty():
		ops.append({
			"kind": "text",
			"text": ellipsis(" | ".join(specials), STAT_SIZE, popup_w - 30, measure),
			"size": STAT_SIZE,
			"style": "body_medium",
			"color": GOLD_TEXT,
			"pos": [px + 15, y],
		})
		y += SPECIAL_STEP
	y += SPECIAL_GAP
	if not bool(tower.get("is_player_built", true)):
		var metrics: Vector2i = measure.call("Enemy Tower", ENEMY_SIZE)
		ops.append({
			"kind": "text",
			"text": "Enemy Tower",
			"size": ENEMY_SIZE,
			"style": "body_medium",
			"color": RED_LIGHT,
			"pos": [px + popup_w / 2 - int(metrics.x) / 2, y + 14 - int(metrics.y) / 2],
		})
		return ops
	if level >= REGEN_MIN_LEVEL:
		ops.append(_section("_draw_regen_shield_section"))
		ops.append_array(
			regen_section(tower, px, py + REGEN_SECTION_Y, popup_w, gold, mouse, buttons)
		)
	if not bool(tower.get("can_upgrade", false)):
		ops.append(_section("_draw_tower_max_level"))
		ops.append_array(max_level_ops(tower, px, popup_w, y, mouse, measure, buttons))
		return ops
	if level == 1:
		ops.append(_section("_draw_tower_path_buttons"))
		ops.append_array(
			path_buttons_ops(state, measure, px, popup_w, y, gold, mouse, buttons)
		)
	else:
		ops.append(_section("_draw_tower_upgrade_button"))
		ops.append_array(
			upgrade_button_ops(state, measure, px, popup_w, y, gold, mouse, buttons)
		)
	return ops


## `_get_tower_specials`: order and formats pinned by the oracle.
static func tower_specials(tower: Dictionary) -> Array:
	var specials: Array = []
	if int(tower.get("splash", 0)) > 0:
		specials.append("Splash %d" % int(tower.get("splash", 0)))
	if float(tower.get("slow", 0.0)) > 0.0:
		specials.append("Slow %d%%" % int(float(tower.get("slow", 0.0)) * 100.0))
	if int(tower.get("chain", 1)) > 1:
		specials.append("Chain x%d" % int(tower.get("chain", 1)))
	if bool(tower.get("double_shot", false)):
		specials.append("Double Shot")
	if int(tower.get("burn_dps", 0)) > 0:
		specials.append("Burn %d/s" % int(tower.get("burn_dps", 0)))
	if float(tower.get("atk_slow", 0.0)) > 0.0:
		specials.append("AtkSlow %d%%" % int(float(tower.get("atk_slow", 0.0)) * 100.0))
	if float(tower.get("skill_down", 0.0)) > 0.0:
		specials.append("SkillDown %d%%" % int(float(tower.get("skill_down", 0.0)) * 100.0))
	return specials


## `_draw_tower_content` title: `"{name} Lv.{level}"`, or `"Lv.{level} {Type}"` when the name
## does not fit `popup_w - TITLE_MAX_INSET`; the fallback string is ellipsised as well.
static func _title_text(tower: Dictionary, popup_w: int, measure: Callable) -> String:
	var level := int(tower.get("level", 1))
	var title := "%s Lv.%d" % [String(tower.get("name", "")), level]
	if int(measure.call(title, TITLE_SIZE).x) > popup_w - TITLE_MAX_INSET:
		var kind := String(tower.get("tower_type", "")).capitalize()
		title = "Lv.%d %s" % [level, kind]
	return ellipsis(title, TITLE_SIZE, popup_w - TITLE_MAX_INSET, measure)


## `hp_ratio = max(0, tower.hp / tower.max_hp)`; a zero maximum never divides.
static func _ratio(tower: Dictionary) -> float:
	var maximum := float(tower.get("max_hp", 0))
	if maximum <= 0.0:
		return 0.0
	return maxf(0.0, float(tower.get("hp", 0)) / maximum)


## Bar colour of `_draw_tower_content`: `> 0.5` green, `> 0.25` amber, else red.
static func _bar_color(ratio: float) -> Array:
	if ratio > 0.5:
		return HP_GOOD
	if ratio > 0.25:
		return HP_MID
	return HP_LOW


## The two stat lines of `_draw_tower_content`; the lane is uppercased, `-` when absent.
static func _stat_lines(tower: Dictionary) -> Array:
	var lane := String(tower.get("lane", ""))
	var lane_text := lane.to_upper() if lane != "" else "-"
	return [
		"DMG: %d  Range: %d" % [int(tower.get("damage", 0)), int(tower.get("range", 0))],
		"Kills: %d  Lane: %s" % [int(tower.get("kills", 0)), lane_text],
	]


## `_draw_regen_shield_section`: status pill when active, buy button when unlocked,
## nothing otherwise (the section marker still lands in the op stream).
static func regen_section(
	tower: Dictionary, px: int, y: int, popup_w: int, gold: int, mouse: Vector2i,
	buttons: Dictionary
) -> Array:
	var box := Rect2i(px + 15, y, popup_w - 30, 36)
	if bool(tower.get("regen_shield_active", false)):
		return [
			_pill("regen_shield_on", "REGEN SHIELD: ON", box, "success", false, "shield", PILL_SIZE)
		]
	if not bool(tower.get("can_activate_regen_shield", false)):
		return []
	var cost := int(tower.get("regen_shield_cost", 0))
	var can_buy := gold >= cost
	buttons["popup_regen_shield"] = _rect_array(box)
	return [
		_pill(
			"popup_regen_shield",
			"REGEN SHIELD (%dG)" % cost,
			box,
			"gold" if can_buy else "locked",
			can_buy and box.has_point(mouse),
			"shield",
			PILL_SIZE
		)
	]


## `_draw_tower_max_level`: letter-spaced MAX LEVEL + the sell pill.
static func max_level_ops(
	tower: Dictionary, px: int, popup_w: int, y: int, mouse: Vector2i, measure: Callable,
	buttons: Dictionary
) -> Array:
	var label := letter("MAX LEVEL")
	var metrics: Vector2i = measure.call(label, MAX_LEVEL_SIZE)
	var ops: Array = [
		{
			"kind": "text",
			"text": label,
			"size": MAX_LEVEL_SIZE,
			"style": PILL_FONT,
			"color": GOLD_TEXT,
			"pos": [px + popup_w / 2 - int(metrics.x) / 2, y + 14 - int(metrics.y) / 2],
		}
	]
	var sell_val := int(tower.get("sell_value", 0))
	if sell_val > 0:
		var box := Rect2i(px + (popup_w - SELL_W) / 2, y + MAX_LEVEL_STEP, SELL_W, SELL_H)
		buttons["popup_sell_tower"] = _rect_array(box)
		ops.append(
			_pill(
				"popup_sell_tower",
				"SELL %dG" % sell_val,
				box,
				"danger",
				box.has_point(mouse),
				"minus",
				PILL_SIZE
			)
		)
	return ops


## `_draw_tower_path_buttons`: gold "CHOOSE PATH" title + the 2x2 path grid.
static func path_buttons_ops(
	state: Dictionary, measure: Callable, px: int, popup_w: int, y: int, gold: int, mouse: Vector2i,
	buttons: Dictionary
) -> Array:
	var tower: Dictionary = state.get("tower", {})
	var cheap: bool = bool(state.get("cheap_alpha", true))
	var ops: Array = [
		{
			"kind": "text",
			"text": letter("CHOOSE PATH"),
			"size": PATH_TITLE_SIZE,
			"style": PILL_FONT,
			"color": GOLD_TEXT,
			"pos": [px + 15, y],
		}
	]
	var top := y + PATH_TITLE_STEP
	var btn_w := (popup_w - 46) / 2
	for index in range(PATH_NAMES.size()):
		var path_type := String(PATH_NAMES[index])
		var col := index % 2
		var row := index / 2
		var box := Rect2i(
			px + 15 + col * (btn_w + PATH_GAP_X),
			top + row * (PATH_BTN_H + PATH_GAP_Y),
			btn_w,
			PATH_BTN_H
		)
		buttons["popup_upgrade_path_" + path_type] = _rect_array(box)
		ops.append(_section("_draw_single_path_button"))
		ops.append_array(path_button_ops(measure, tower, path_type, box, gold, mouse, cheap))
	return ops


## `_draw_single_path_button`: tinted gradient card, gold ticks, name/cost/special.
static func path_button_ops(
	measure: Callable,
	tower: Dictionary,
	path_type: String,
	box: Rect2i,
	gold: int,
	mouse: Vector2i,
	cheap: bool
) -> Array:
	var info := type_info(path_type)
	var color: Array = [100, 100, 100]
	var types: Dictionary = catalog().get("types", {})
	if types.has(path_type):
		color = types[path_type].get("color", color)
	var costs: Dictionary = tower.get("path_costs", {})
	var cost := int(costs.get(path_type, 0))
	var can_afford := gold >= cost
	var hover := can_afford and box.has_point(mouse)
	var dark := _tint(color, 0.30, 18)
	var lighter := _tint(color, 0.45, 40, 255)
	var ops: Array = []
	if cheap:
		ops.append({
			"kind": "vgrad",
			"rect": _rect_array(box),
			"top": lighter if hover else dark,
			"bottom": _tint(color, 0.22, 12, 255),
			"radius": 8,
		})
		if hover:
			ops.append({
				"kind": "radial",
				"rect": [box.position.x - 8, box.position.y - 8, box.size.x + 16, box.size.y + 16],
				"color": color,
				"alpha": _radial_alpha(46),
			})
	else:
		ops.append(_rect_op(box, dark, 0, 8))
	ops.append(_rect_op(box, color if can_afford else LOCKED_EDGE, 2, 8))
	if can_afford:
		ops.append({
			"kind": "corner_ticks",
			"rect": _rect_array(box),
			"color": UI_GOLD,
			"length": 8,
			"width": 2,
			"inset": 2,
		})
	var name_text := String(info.get("name", "")).replace(" Tower", "")
	ops.append({
		"kind": "text",
		"text": ellipsis(name_text, PATH_TITLE_SIZE, box.size.x - 12, measure),
		"size": PATH_TITLE_SIZE,
		"style": PILL_FONT,
		"color": WHITE if can_afford else GRAY,
		"pos": [box.position.x + 8, box.position.y + 5],
	})
	ops.append({
		"kind": "icon",
		"name": "coin",
		"center": [box.position.x + 14, box.position.y + 36],
		"color": UI_GOLD,
		"s": 0.5,
	})
	ops.append({
		"kind": "text",
		"text": "%dG" % cost,
		"size": PILL_SIZE,
		"style": PILL_FONT,
		"color": GOLD_TEXT if can_afford else GRAY,
		"pos": [box.position.x + 25, box.position.y + 28],
	})
	var desc_size := 15
	ops.append({
		"kind": "text",
		"text": ellipsis(String(info.get("special", "")), desc_size, box.size.x - 14, measure),
		"size": desc_size,
		"style": "body_medium",
		"color": PATH_DESC if can_afford else GRAY,
		"pos": [box.position.x + 8, box.position.y + 48],
	})
	return ops


## `_draw_tower_upgrade_button`: preview + description + UPGRADE/SELL pills.
static func upgrade_button_ops(
	state: Dictionary, measure: Callable, px: int, popup_w: int, y: int, gold: int, mouse: Vector2i,
	buttons: Dictionary
) -> Array:
	var tower: Dictionary = state.get("tower", {})
	var tower_type := String(tower.get("tower_type", ""))
	var level := int(tower.get("level", 1))
	var cost := int(tower.get("upgrade_cost", 0))
	var can_up := gold >= cost
	var next_level := level + 1
	var next_stats := upgrade_stats(tower_type, next_level)
	var damage: Variant = next_stats.get("damage", "?")
	var hp: Variant = next_stats.get("hp", "?")
	var preview_text := "Lv%d: DMG %s HP %s" % [next_level, str(damage), str(hp)]
	var preview := ellipsis(preview_text, UPGRADE_TEXT_SIZE, popup_w - 30, measure)
	var ops: Array = [
		{
			"kind": "text",
			"text": preview,
			"size": UPGRADE_TEXT_SIZE,
			"style": "body_semibold",
			"color": CYAN_SOFT,
			"pos": [px + 15, y],
		}
	]
	var desc := ellipsis(
		String(next_stats.get("desc", "")), UPGRADE_TEXT_SIZE, popup_w - 30, measure
	)
	ops.append({
		"kind": "text",
		"text": desc,
		"size": UPGRADE_TEXT_SIZE,
		"style": "body_semibold",
		"color": GOLD_TEXT,
		"pos": [px + 15, y + HP_STEP],
	})
	var btn_w := (popup_w - 46) / 2
	var row := y + HP_STEP * 2
	var up_box := Rect2i(px + 15, row, btn_w, UPGRADE_BTN_H)
	buttons["popup_upgrade_tower"] = _rect_array(up_box)
	ops.append(
		_pill(
			"popup_upgrade_tower",
			"UPGRADE %dG" % cost,
			up_box,
			"success" if can_up else "locked",
			can_up and up_box.has_point(mouse),
			"plus",
			PILL_BTN_SIZE
		)
	)
	var sell_box := Rect2i(
		px + 15 + UPGRADE_SELL_INSET + btn_w, row, btn_w, UPGRADE_BTN_H
	)
	buttons["popup_sell_tower"] = _rect_array(sell_box)
	ops.append(
		_pill(
			"popup_sell_tower",
			"SELL %dG" % int(tower.get("sell_value", 0)),
			sell_box,
			"danger",
			sell_box.has_point(mouse),
			"minus",
			PILL_BTN_SIZE
		)
	)
	return ops


static func _pill(
	id: String, text: String, box: Rect2i, style: String, hover: bool, icon: String, size: int
) -> Dictionary:
	return {
		"kind": "pill",
		"id": id,
		"text": text,
		"rect": _rect_array(box),
		"style": style,
		"hover": hover,
		"enabled": true,
		"icon": icon,
		"letter_gap": false,
		"size": size,
		"font": PILL_FONT,
	}


## `ui_theme.fit_ellipsis` with the popup's three-dot fallback: the recorder's fonts carry no
## glyph table, so the source's `…` probe resolves to `...` (the `ELLIPSIS` constant).
static func ellipsis(text: String, size: int, max_w: int, measure: Callable) -> String:
	return UiTheme.fit_ellipsis(measure, text, max_w, size, ELLIPSIS)


## `ui_theme.letter`: one space between characters (MAX LEVEL, CHOOSE PATH).
static func letter(text: String) -> String:
	return UiTheme.letter(text)


## Per-channel `int(c * factor) + add`, clamped at 255 when `clamp_top` is set.
static func _tint(color: Array, factor: float, add: int, clamp_top: int = 0) -> Array:
	var out: Array = []
	for channel in range(3):
		var value := int(float(color[channel]) * factor) + add
		if clamp_top > 0:
			value = mini(clamp_top, value)
		out.append(value)
	return out


## The oracle's `_radial` shim quantises alpha to eighths, capped at 120.
static func _radial_alpha(alpha: int) -> int:
	return maxi(4, mini(120, (alpha / 8) * 8))


static func _lighten(color: Array, add: int) -> Array:
	var out: Array = []
	for channel in range(len(color)):
		out.append(mini(255, int(color[channel]) + add))
	return out


static func _section(name: String) -> Dictionary:
	return {"kind": "section", "name": name}


static func _rect_array(box: Rect2i) -> Array:
	return [box.position.x, box.position.y, box.size.x, box.size.y]


static func _rect_op(box: Rect2i, color: Array, width: int, radius: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": _rect_array(box),
		"color": _rgba(color),
		"width": width,
		"radius": radius,
	}


## `pygame.draw.rect` colours carry an alpha the recorder appends; `_vgrad`/`_radial` do not.
static func _rgba(color: Array) -> Array:
	if color.size() >= 4:
		return color
	return [int(color[0]), int(color[1]), int(color[2]), 255]


static func _point(value: Variant) -> Vector2i:
	if value is Array and value.size() >= 2:
		return Vector2i(int(value[0]), int(value[1]))
	if value is Vector2i:
		return value
	return Vector2i.ZERO


static func _panel_rect(state: Dictionary) -> Rect2i:
	var value: Variant = state.get("panel", null)
	if value is Array and value.size() >= 4:
		return Rect2i(int(value[0]), int(value[1]), int(value[2]), int(value[3]))
	if value is Rect2i:
		return value
	return Rect2i()
