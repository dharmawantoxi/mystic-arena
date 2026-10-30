extends RefCounted
## Port of `mobile/sidepanel.py` + the panel display rules of
## `mobile/platform_utils.py` (layer 9as): the wide-screen RIGHT PANEL.
##
## On screens wider than 16:9 the source collects the leftover width at the
## right (display width capped at 2200 px, panel only when >= 120 px are
## left) and fills it with: PAUSE button, STATUS box (gold / mode / level /
## wave), HEROES list (name, level, HP bar, Q/W/E/R dots) and the TACTICAL
## COMMANDS buttons. Notifications / kill feed were removed by the user (the
## source methods are no-ops), so nothing of them is ported.
##
## This class is the pure layout: `build()` turns a game snapshot into the
## exact draw list of the source (`_gambar_status/_gambar_hero/
## _gambar_tactical`, same numbers, strings and colours) plus the button hit
## boxes; `hit_test()` is `SidePanel.hit_test`. Text widths come from an
## injected `measure` callable so the suite can replay the oracle's 7 px
## glyphs while the Control uses the real font.

const LOGICAL_WIDTH := 1280
const LOGICAL_HEIGHT := 720
const MAX_DISPLAY_WIDTH := 2200
const MIN_PANEL_WIDTH := 120
const REFRESH_MS := 250
const MIN_TAP := 80
const PAD := 14
const TEXT_H := 12
## `_render._STYLE_FONT_MAP` styles used by the panel: the source calls
## `get_font(size, "body_bold")` for box titles, the gold amount, "LV n", hero
## names and the tactical labels, and the default `body` for everything else.
const STYLE_BODY := "body"
const STYLE_BOLD := "body_bold"
const STATUS_Y := 84
const STATUS_H := 96
const HERO_ROW := 42
const HERO_ROW_DENSE := 38
const HERO_BOX_MAX := 236
const HERO_CAP := 5
const TACTICAL_BTN_H := 32
const TACTICAL_GAP := 6
const TACTICAL_TAP_PAD := 3
const PAUSE_RECT := Rect2i(PAD, 14, 58, 58)

const FG := Color8(228, 230, 242)
const DIM := Color8(146, 150, 172)
const EMAS := Color8(255, 205, 90)
const OK := Color8(120, 235, 140)
const BAHAYA := Color8(255, 110, 110)
const BIRU := Color8(120, 200, 255)
const UNGU := Color8(190, 165, 255)
const SHIELD_BLUE := Color8(100, 200, 255)
const EASY_BLUE := Color8(100, 210, 255)
const BOX_FILL := Color8(22, 19, 32)
const BOX_LINE := Color8(64, 56, 86)
const BAR_BACK := Color8(48, 14, 14)
const BAR_LINE := Color8(90, 84, 110)
const DOT_OFF := Color8(60, 56, 78)
const BTN_OFF_BG := Color8(45, 45, 50)
const BTN_OFF_LINE := Color8(80, 80, 85)
const BTN_OFF_TEXT := Color8(120, 120, 125)
const CHIP_BG := Color8(20, 18, 30)
const WHITE := Color8(255, 255, 255)

const TACTICAL_KEYS := [
	"gather", "protect_tower", "protect_castle", "attack_boss", "attack_damage_dealer"
]
const TACTICAL_LABELS := {
	"gather": "GATHER [G]",
	"protect_tower": "PROTECT TOWER [T]",
	"protect_castle": "PROTECT CASTLE [C]",
	"attack_boss": "ATTACK BOSS [B]",
	"attack_damage_dealer": "ATTACK DMG DEALER [D]",
}
const TACTICAL_COLORS := {
	"gather": BIRU,
	"protect_tower": OK,
	"protect_castle": EMAS,
	"attack_boss": BAHAYA,
	"attack_damage_dealer": UNGU,
}


## `platform_utils.create_display`: full width from the device ratio, never
## below the arena, capped at 2200 and made even.
static func display_width(ratio: float) -> int:
	var proposed := int(roundf(LOGICAL_HEIGHT * ratio))
	var width := maxi(LOGICAL_WIDTH, mini(MAX_DISPLAY_WIDTH, proposed))
	return width - width % 2


## Panel rect on the full surface, or an empty rect when fewer than 120 px
## are left of the arena.
static func panel_rect(full_width: int) -> Rect2i:
	var leftover := maxi(0, full_width - LOGICAL_WIDTH)
	if leftover < MIN_PANEL_WIDTH:
		return Rect2i()
	return Rect2i(LOGICAL_WIDTH, 0, leftover, LOGICAL_HEIGHT)


static func in_gameplay(state: String) -> bool:
	return state in ["playing", "victory", "defeat"]


static func format_gold(gold: int) -> String:
	if gold >= 10000:
		return "%.1fK" % (float(gold) / 1000.0)
	var digits := str(gold)
	var out := ""
	var count := 0
	for index in range(digits.length() - 1, -1, -1):
		out = digits[index] + out
		count += 1
		if count % 3 == 0 and index > 0:
			out = "," + out
	return out


static func hp_color(ratio: float) -> Color:
	if ratio > 0.5:
		return OK
	return EMAS if ratio > 0.25 else BAHAYA


static func _quarter(color: Color) -> Color:
	return Color8(color.r8 / 4, color.g8 / 4, color.b8 / 4)


static func _pressed(color: Color, press: float) -> Color:
	var k := int(25.0 * press)
	return Color8(color.r8 / 3 + k, color.g8 / 3 + k, color.b8 / 3 + k)


static func _held(color: Color) -> Color:
	return Color8(color.r8 / 2 + 26, color.g8 / 2 + 26, color.b8 / 2 + 26)


static func _inflate(rect: Rect2i, dx: int, dy: int) -> Rect2i:
	# pygame Rect.inflate: integer half-steps toward the centre.
	@warning_ignore("integer_division")
	var hx := dx / 2
	@warning_ignore("integer_division")
	var hy := dy / 2
	return Rect2i(rect.position.x - hx, rect.position.y - hy, rect.size.x + dx, rect.size.y + dy)


## Build the source draw list for one panel frame.
## snapshot keys: state, gold, difficulty, wave (-1 = None), level (-1 =
## None), shield_active, heroes [{name, alive, level, hp, max_hp, ready}],
## has_boss, has_enemy_hero, held, press {action: 0..1}.
## `measure` sizes the regular strings and `measure_bold` the ones the source
## renders with `body_bold` (Barlow-Bold): the gold amount, "LV n" and the
## tactical labels. Right-aligned and centred bold text therefore uses the
## bold width, exactly like `SidePanel` (`font.render(...).get_width()`).
## Result: texts/rects/circles in panel-local coordinates, buttons keyed by
## action with screen rects, and the y after each section.
static func build(
	snapshot: Dictionary, panel: Rect2i, measure: Callable, measure_bold := Callable()
) -> Dictionary:
	var measure_strong: Callable = measure_bold if measure_bold.is_valid() else measure
	var out := {
		"texts": [],
		"rects": [],
		"circles": [],
		"buttons": {},
		"y_after_status": 0,
		"y_after_heroes": 0,
		"y_after_tactical": 0,
	}
	var state := String(snapshot.get("state", "playing"))
	var pause_visible := in_gameplay(state)
	out["buttons"]["pause"] = _button(
		"pause",
		Rect2i(panel.position.x + PAUSE_RECT.position.x, PAUSE_RECT.position.y, 58, 58),
		"",
		EMAS,
		pause_visible,
		-1
	)
	if not pause_visible:
		for key in TACTICAL_KEYS:
			out["buttons"][key] = _placeholder(key, panel)
		return out
	var y := _status(out, snapshot, panel, measure, measure_strong, STATUS_Y)
	out["y_after_status"] = y
	y = _heroes(out, snapshot, panel, measure, y)
	out["y_after_heroes"] = y
	y = _tactical(out, snapshot, panel, measure, measure_strong, y)
	out["y_after_tactical"] = y
	return out


static func _button(
	action: String, rect: Rect2i, label: String, color: Color, visible: bool, tap_pad: int
) -> Dictionary:
	var hit := rect
	if tap_pad < 0:
		hit = _inflate(rect, maxi(0, MIN_TAP - rect.size.x), maxi(0, MIN_TAP - rect.size.y))
	else:
		hit = _inflate(rect, tap_pad * 2, tap_pad * 2)
	return {
		"action": action,
		"rect": rect,
		"hit_rect": hit,
		"label": label,
		"color": color,
		"visible": visible,
	}


static func _placeholder(action: String, panel: Rect2i) -> Dictionary:
	# `_rebuild` placeholders: present but hidden until really drawn.
	var index := TACTICAL_KEYS.find(action)
	var base_y := 84 + 96 + 10 + 236 + 10
	var rect := Rect2i(
		panel.position.x + PAD + 6,
		panel.position.y + base_y + index * (TACTICAL_BTN_H + TACTICAL_GAP),
		panel.size.x - PAD * 2 - 12,
		TACTICAL_BTN_H
	)
	return _button(
		action,
		rect,
		String(TACTICAL_LABELS[action]),
		TACTICAL_COLORS[action],
		false,
		TACTICAL_TAP_PAD
	)


static func _text(
	out: Dictionary, text: String, color: Color, size: int, pos: Vector2i, bold := false
) -> void:
	out["texts"].append(
		{
			"text": text,
			"color": color,
			"size": size,
			"pos": pos,
			"bold": bold,
			"style": STYLE_BOLD if bold else STYLE_BODY,
		}
	)


static func _rect(out: Dictionary, color: Color, rect: Rect2i, width: int, radius: int) -> void:
	out["rects"].append({"color": color, "rect": rect, "width": width, "radius": radius})


static func _box(out: Dictionary, x: int, y: int, w: int, h: int, title: String) -> void:
	_rect(out, BOX_FILL, Rect2i(x, y, w, h), 0, 8)
	_rect(out, BOX_LINE, Rect2i(x, y, w, h), 1, 8)
	if not title.is_empty():
		_text(out, title, DIM, 13, Vector2i(x + 8, y + 5), true)


static func _width(measure: Callable, text: String, size: int) -> int:
	return int(measure.call(text, size))


static func _status(
	out: Dictionary,
	snapshot: Dictionary,
	panel: Rect2i,
	measure: Callable,
	measure_bold: Callable,
	y: int
) -> int:
	var w := panel.size.x - PAD * 2
	var x := PAD
	_box(out, x, y, w, STATUS_H, "STATUS")
	var gold := int(snapshot.get("gold", 0))
	var gold_text := format_gold(gold)
	var gold_size := 22
	if _width(measure_bold, gold_text, gold_size) > int(float(w) * 0.55):
		gold_size = 18
	_text(out, gold_text, EMAS, gold_size, Vector2i(x + 10, y + 22), true)
	_text(out, "GOLD", DIM, 13, Vector2i(x + 10, y + 46))
	var difficulty := String(snapshot.get("difficulty", "normal"))
	match difficulty:
		"easy":
			_text(out, "EASY", EASY_BLUE, 12, Vector2i(x + 10, y + 68))
		"hard":
			_text(out, "HARD", BAHAYA, 12, Vector2i(x + 10, y + 68))
		_:
			_text(out, "NORMAL", OK, 12, Vector2i(x + 10, y + 68))
	var wave := int(snapshot.get("wave", -1))
	var level := int(snapshot.get("level", -1))
	var right := x + w - 10
	var ry := y + 24
	if level >= 0:
		var shielded: bool = bool(snapshot.get("shield_active", false)) and wave >= 0 and wave < 10
		if shielded:
			var text := "LV %d [SHIELDED]" % level
			_text(out, text, SHIELD_BLUE, 12, Vector2i(right - _width(measure, text, 12), ry))
		else:
			var text := "LV %d" % level
			_text(out, text, FG, 16, Vector2i(right - _width(measure_bold, text, 16), ry), true)
		ry += 20
	if wave >= 0:
		var wave_text := "Wave %d (Shield)" % wave if wave < 10 else "Wave %d" % wave
		var wave_color := SHIELD_BLUE if wave < 10 else DIM
		_text(out, wave_text, wave_color, 13, Vector2i(right - _width(measure, wave_text, 13), ry))
	return y + STATUS_H + 10


static func _heroes(
	out: Dictionary, snapshot: Dictionary, panel: Rect2i, measure: Callable, y: int
) -> int:
	var w := panel.size.x - PAD * 2
	var x := PAD
	var all_heroes: Array = snapshot.get("heroes", [])
	var heroes := all_heroes.slice(0, HERO_CAP)
	var more := maxi(0, all_heroes.size() - HERO_CAP)
	var row := HERO_ROW_DENSE if (heroes.size() >= HERO_CAP or more > 0) else HERO_ROW
	var h := 22 + maxi(1, heroes.size()) * row
	if more > 0:
		h += 14
	h = mini(h, HERO_BOX_MAX)
	if h < 40:
		return y
	_box(out, x, y, w, h, "HEROES")
	if heroes.is_empty():
		_text(out, "No heroes", DIM, 14, Vector2i(x + 10, y + 30))
		return y + h + 10
	var by := y + 22
	for hero_value in heroes:
		var hero: Dictionary = hero_value
		if by + row > y + h:
			break
		var hero_name := String(hero.get("name", "?")).left(12)
		var alive := bool(hero.get("alive", true))
		_text(out, hero_name, FG if alive else BAHAYA, 15, Vector2i(x + 9, by), true)
		var level := int(hero.get("level", -1))
		if level >= 0:
			var level_text := "Lv%d" % level
			_text(
				out,
				level_text,
				EMAS,
				12,
				Vector2i(x + w - 10 - _width(measure, level_text, 12), by + 2)
			)
		var bx := x + 9
		var bw := w - 18
		var byy := by + 19
		_rect(out, BAR_BACK, Rect2i(bx, byy, bw, 6), 0, 0)
		var max_hp := float(hero.get("max_hp", 0.0))
		var ratio := 0.0
		if max_hp > 0.0:
			ratio = clampf(float(hero.get("hp", 0.0)) / max_hp, 0.0, 1.0)
		if ratio > 0.0:
			_rect(out, hp_color(ratio), Rect2i(bx, byy, int(float(bw) * ratio), 6), 0, 0)
		_rect(out, BAR_LINE, Rect2i(bx, byy, bw, 6), 1, 0)
		var ready: Array = hero.get("ready", [])
		var dx := bx
		for key in ["q", "w", "e", "r"]:
			var color := UNGU if ready.has(key) else DOT_OFF
			out["circles"].append(
				{"color": color, "center": Vector2i(dx + 5, byy + 13), "radius": 4}
			)
			dx += 14
		by += row
	if more > 0 and by + 14 <= y + h:
		_text(out, "+%d more" % more, DIM, 12, Vector2i(x + 9, by - 2))
	return y + h + 10


static func _tactical(
	out: Dictionary,
	snapshot: Dictionary,
	panel: Rect2i,
	measure: Callable,
	measure_bold: Callable,
	y: int
) -> int:
	var hidden := String(snapshot.get("state", "")) != "playing"
	var w := panel.size.x - PAD * 2
	var x := PAD
	var h := 26 + 5 * (TACTICAL_BTN_H + TACTICAL_GAP) - TACTICAL_GAP
	if hidden or y + h > panel.size.y - 24:
		for key in TACTICAL_KEYS:
			out["buttons"][key] = _placeholder(key, panel)
		return y
	var alive := 0
	for hero_value in snapshot.get("heroes", []):
		if bool((hero_value as Dictionary).get("alive", false)):
			alive += 1
	var has_boss := bool(snapshot.get("has_boss", false))
	var has_enemy_hero := bool(snapshot.get("has_enemy_hero", false))
	var enabled := {
		"gather": alive > 0,
		"protect_tower": alive >= 1,
		"protect_castle": alive > 0,
		"attack_boss": has_boss,
		"attack_damage_dealer": has_enemy_hero,
	}
	var held := String(snapshot.get("held", ""))
	var press: Dictionary = snapshot.get("press", {})
	_box(out, x, y, w, h, "TACTICAL COMMANDS (HOLD)")
	var by := y + 24
	for key in TACTICAL_KEYS:
		var action := String(key)
		var label := String(TACTICAL_LABELS[action])
		var color: Color = TACTICAL_COLORS[action]
		var is_enabled := bool(enabled[action])
		var screen_rect := Rect2i(
			panel.position.x + x + 6, panel.position.y + by, w - 12, TACTICAL_BTN_H
		)
		out["buttons"][action] = _button(
			action, screen_rect, label, color, is_enabled, TACTICAL_TAP_PAD
		)
		var buf_rect := Rect2i(x + 6, by, w - 12, TACTICAL_BTN_H)
		var bg := BTN_OFF_BG
		var border := BTN_OFF_LINE
		var text_color := BTN_OFF_TEXT
		if is_enabled:
			var press_value := float(press.get(action, 0.0))
			if press_value > 0.0:
				bg = _pressed(color, press_value)
				border = WHITE
				text_color = WHITE
			else:
				bg = _quarter(color)
				border = color
				text_color = color
		var on_hold := is_enabled and held == action
		if on_hold:
			bg = _held(color)
			border = WHITE
			text_color = WHITE
		_rect(out, bg, buf_rect, 0, 6)
		_rect(out, border, buf_rect, 2, 6)
		if on_hold:
			_rect(out, color, _inflate(buf_rect, -4, -4), 1, 4)
		var cx := buf_rect.position.x + buf_rect.size.x / 2
		var cy := buf_rect.position.y + buf_rect.size.y / 2
		_text(
			out,
			label,
			text_color,
			13,
			Vector2i(cx - _width(measure_bold, label, 13) / 2, cy - TEXT_H / 2),
			true
		)
		if on_hold:
			var chip_w := _width(measure, "HOLD", 11)
			var chip := Rect2i(buf_rect.end.x - 8 - chip_w, cy - TEXT_H / 2, chip_w, TEXT_H)
			var pad_rect := _inflate(chip, 8, 4)
			_rect(out, CHIP_BG, pad_rect, 0, 4)
			_rect(out, color, pad_rect, 1, 4)
			_text(out, "HOLD", WHITE, 11, chip.position)
		by += TACTICAL_BTN_H + TACTICAL_GAP
	return y + h + 10


## `SidePanel.hit_test`: while a game popup covers the panel only PAUSE
## answers; otherwise the first visible button whose padded box contains the
## point (buttons are visited in the source dict order).
static func hit_test(buttons: Dictionary, pos: Vector2i, popup_open: bool) -> String:
	var order := ["pause"]
	order.append_array(TACTICAL_KEYS)
	for key in order:
		if not buttons.has(key):
			continue
		var button: Dictionary = buttons[key]
		if popup_open and String(key) != "pause":
			continue
		if bool(button["visible"]) and (button["hit_rect"] as Rect2i).has_point(pos):
			return String(key)
	return ""


## `SidePanel.blocks`: the point belongs to the panel, not the arena.
static func blocks(panel: Rect2i, pos: Vector2i) -> bool:
	return panel.size.x > 0 and panel.has_point(pos)
