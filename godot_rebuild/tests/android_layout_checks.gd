extends RefCounted
## Layer 9bt: the Android screenshots as a layout oracle.
##
## `docs/screenshots/android-2026-10-30/{menu,match}.jpg` are 2436x1080 captures of the
## real Pygame APK, and `tools/measure_android_screenshot.py` turns them into
## `tests/fixtures/android_screenshot_reference.json`: device scale, dock rect, HUD boxes,
## tactical button rows and the eight main-menu buttons, each as `expect` (what the source
## layout says) plus `measured` (what the image shows, within 3 px).
##
## This suite replays those numbers through the Godot layout classes, so "it looks like the
## phone screenshots" is a test instead of an opinion.

const Layout = preload("res://scripts/ui/side_panel_layout.gd")
const PanelStone = preload("res://scripts/ui/panel_stone.gd")
const PanelBackdrop = preload("res://scripts/ui/panel_backdrop.gd")
const MenuBackdrop = preload("res://scripts/ui/menu_backdrop.gd")
const MainMenuScript = preload("res://scenes/menu/main_menu.gd")
const FIXTURE := "res://tests/fixtures/android_screenshot_reference.json"
const TOLERANCE := 3.0
const SCREEN_ORIGIN := 1280
const MENU_NODES := {
	"continue": "ContinueButton",
	"play": "PlayButton",
	"hero_shop": "HeroShopButton",
	"input": "InputButton",
	"how_to_play": "HowToPlayButton",
	"settings": "SettingsButton",
	"credits": "CreditsButton",
	"quit": "QuitButton",
}
const BOX_SCREEN_X := 1294
const BOX_LOCAL_X := 14
const BOX_W := 316


func _fixture() -> Dictionary:
	if not FileAccess.file_exists(FIXTURE):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	return parsed if parsed is Dictionary else {}


static func _near(got: float, want: float) -> bool:
	return absf(got - want) <= TOLERANCE


static func _rect_near(got: Array, want: Array) -> bool:
	if got.size() != 4 or want.size() != 4:
		return false
	for index in range(4):
		if not _near(float(got[index]), float(want[index])):
			return false
	return true


static func _measure(text: String, size: int) -> int:
	# Stand-in for the source's 7 px glyphs: only text widths depend on it.
	return int(round(float(text.length()) * float(size) * 0.6))


func run(check: Callable) -> void:
	var fixture := _fixture()
	check.call(not fixture.is_empty(), "The Android screenshot fixture is present: %s" % FIXTURE)
	if fixture.is_empty():
		return
	_check_device(fixture, check)
	_check_arena(fixture, check)
	_check_stone(check)
	_check_dock(fixture, check)
	_check_menu(fixture, check)


## 2436x1080 at 1.5x is a 1624x720 surface with a 344 px dock - `create_display`.
func _check_device(fixture: Dictionary, check: Callable) -> void:
	var device: Dictionary = fixture.get("device", {})
	var px: Array = device.get("px", [])
	var logical: Array = device.get("logical", [])
	check.call(
		px.size() == 2 and int(px[0]) == 2436 and int(px[1]) == 1080,
		"The oracle really is the 2436x1080 phone capture: %s" % [px]
	)
	check.call(
		(
			_near(float(device.get("scale", 0.0)), 1.5)
			and logical.size() == 2
			and int(logical[0]) == 1624
			and int(logical[1]) == 720
		),
		"Screenshot pixels are 1.5x logical on a 1624x720 surface: %s" % [logical]
	)
	var ratio := float(device.get("ratio", 0.0))
	check.call(
		Layout.display_width(ratio) == 1624, "create_display widens the surface to %d" % 1624
	)
	check.call(
		int(device.get("panel_width", 0)) == 344,
		(
			"The leftover 344 px are the dock, not a centred letterbox: %d"
			% int(device.get("panel_width", 0))
		)
	)
	check.call(
		Layout.panel_rect(1624) == Rect2i(SCREEN_ORIGIN, 0, 344, 720),
		"panel_rect(1624) is the dock rect the screenshot shows"
	)
	check.call(
		Layout.panel_rect(1280) == Rect2i() and Layout.panel_rect(1280 + 119) == Rect2i(),
		"Under 120 px of leftover width there is no dock"
	)
	check.call(
		(
			Layout.display_width(16.0 / 9.0) == 1280
			and Layout.display_width(3.0) == 2160
			and Layout.display_width(4.0) == 2200
		),
		"display_width keeps 16:9 at 1280, follows the ratio and caps at 2200"
	)


## The menu art is blitted into the 1280x720 arena subsurface, so the frame is
## anchored left at 1:1 - never centred, never upscaled.
func _check_arena(_fixture: Dictionary, check: Callable) -> void:
	check.call(
		MenuBackdrop.arena_rect(Vector2(1280, 720)) == Rect2(0, 0, 1280, 720),
		"A 16:9 surface shows the source frame at 1:1"
	)
	check.call(
		MenuBackdrop.arena_rect(Vector2(1624, 720)) == Rect2(0, 0, 1280, 720),
		"The phone surface keeps the frame at 1:1 in the arena, left aligned"
	)
	check.call(
		MenuBackdrop.arena_rect(Vector2(1280, 960)) == Rect2(0, 120, 1280, 720),
		"A tall surface letterboxes the frame vertically instead of growing it"
	)
	check.call(
		MenuBackdrop.arena_rect(Vector2(800, 600)) == Rect2(0, 75, 800, 450),
		"Only a surface smaller than the arena scales the frame down"
	)
	var sane := true
	var left_aligned := true
	for window in [
		Vector2(1280, 720),
		Vector2(1624, 720),
		Vector2(2200, 720),
		Vector2(1280, 960),
		Vector2(800, 600)
	]:
		var rect := MenuBackdrop.arena_rect(window)
		sane = sane and rect.size.x <= 1280.0 + 0.01 and rect.size.y <= 720.0 + 0.01
		sane = sane and rect.end.x <= window.x + 0.01 and rect.end.y <= window.y + 0.01
		left_aligned = left_aligned and rect.position.x == 0.0
	check.call(sane, "The frame never upscales and never spills outside the surface")
	check.call(left_aligned, "The frame is pinned to the left edge on every surface")


## `_gambar_panel_samping`: the same stone wall sits behind the menu and the dock.
func _check_stone(check: Callable) -> void:
	var panel := Rect2i(SCREEN_ORIGIN, 0, 344, 720)
	var bricks := PanelStone.bricks(panel)
	check.call(bricks.size() == 99, "The 344x720 wall is 99 bricks, as the source paints it")
	check.call(
		PanelStone.BRICK_H == 34 and PanelStone.GOLD_LINE_X == 1.5,
		"Brick pitch 34 px and the gold divider at x=1.5 match the source"
	)
	var inside := true
	var shades := {}
	for brick in bricks:
		var rect: Rect2i = brick["rect"]
		var shade: Color = brick["color"]
		inside = inside and rect.position.x >= 0 and rect.position.y >= 0
		inside = inside and rect.end.x <= 344 and rect.end.y <= 720
		inside = inside and rect.size.y <= 32
		shades[shade.to_html(false)] = true
	check.call(inside, "Every brick is clipped to the dock rect")
	check.call(
		shades.size() == 2, "Bricks alternate the two source stones, not a single flat colour"
	)
	var backdrop := PanelBackdrop.new()
	backdrop.size = Vector2(1624, 720)
	backdrop.call("_refresh")
	check.call(
		backdrop.panel == panel and backdrop.stone.size() == 99,
		"The menu backdrop covers exactly the dock rect of the 1624 px surface"
	)
	backdrop.size = Vector2(1280, 720)
	backdrop.call("_refresh")
	check.call(
		backdrop.panel == Rect2i() and not backdrop.visible,
		"On a 16:9 surface the menu backdrop draws nothing"
	)
	backdrop.free()


## The HUD rows and buttons the match screenshot shows, replayed from the source layout.
func _check_dock(fixture: Dictionary, check: Callable) -> void:
	var match_block: Dictionary = fixture.get("match", {})
	var panel := Layout.panel_rect(1624)
	check.call(
		panel == Rect2i(SCREEN_ORIGIN, 0, 344, 720),
		"The dock under test is the one the capture shows"
	)
	var hud: Dictionary = match_block.get("hud", {})
	var snapshot := {
		"state": "playing",
		"gold": int(hud.get("gold", 0)),
		"difficulty": String(hud.get("difficulty", "normal")),
		"wave": int(hud.get("wave", -1)),
		"level": int(hud.get("level", -1)),
		"shield_active": bool(hud.get("shield_active", false)),
		"heroes": [],
		"has_boss": false,
		"has_enemy_hero": false,
		"held": "",
		"press": {},
	}
	var layout := Layout.build(snapshot, panel, _measure)
	check.call(
		layout["y_after_status"] == 190 and layout["y_after_heroes"] == 264,
		"STATUS ends at 190 and the empty HEROES box (64 px) ends at 264"
	)
	check.call(
		layout["y_after_tactical"] == 484, "The 210 px TACTICAL box ends at 474 plus its 10 px gap"
	)
	var boxes: Dictionary = match_block.get("boxes", {})
	var found := {}
	for entry in layout["rects"]:
		var entry_color: Color = entry["color"]
		if entry_color != Layout.BOX_FILL:
			continue
		var rect: Rect2i = entry["rect"]
		found["%d_%d" % [rect.position.y, rect.size.y]] = rect
	var expect_rows := {"status": 84, "heroes": 190, "tactical": 264}
	var boxes_ok := true
	for name in expect_rows:
		var expect: Array = (boxes.get(name, {}) as Dictionary).get("expect", [])
		var rect: Rect2i = found.get(
			"%d_%d" % [int(expect_rows[name]), int(expect[3]) if expect.size() == 4 else -1],
			Rect2i(-1, -1, 0, 0)
		)
		boxes_ok = boxes_ok and rect.position.x == BOX_LOCAL_X and rect.size.x == BOX_W
		boxes_ok = (
			boxes_ok
			and _rect_near(
				[
					float(rect.position.x + SCREEN_ORIGIN),
					float(rect.position.y),
					float(rect.size.x),
					float(rect.size.y)
				],
				expect
			)
		)
	check.call(boxes_ok, "STATUS/HEROES/TACTICAL boxes land on the captured 1294 x 316 columns")
	var pause: Dictionary = layout["buttons"]["pause"]
	check.call(
		pause["rect"] == Rect2i(1294, 14, 58, 58) and bool(pause["visible"]),
		"The gold PAUSE ring is at (1294, 14) 58x58 with an 80 px hit box"
	)
	check.call(
		(pause["hit_rect"] as Rect2i) == Rect2i(1283, 3, 80, 80),
		"PAUSE keeps the source's 80 px minimum tap target"
	)
	var buttons: Array = match_block.get("tactical_buttons", [])
	var rows_ok := buttons.size() == 5
	var disabled := true
	for index in range(buttons.size()):
		var entry: Dictionary = buttons[index]
		var button: Dictionary = layout["buttons"][Layout.TACTICAL_KEYS[index]]
		var rect: Rect2i = button["rect"]
		rows_ok = (
			rows_ok
			and _rect_near(
				[
					float(rect.position.x),
					float(rect.position.y),
					float(rect.size.x),
					float(rect.size.y)
				],
				entry["expect"]
			)
		)
		rows_ok = (
			rows_ok
			and _rect_near(
				[float(rect.position.y), float(rect.position.y + rect.size.y), 0.0, 0.0],
				[
					float(entry["measured"][1]),
					float(entry["measured"][1] + entry["measured"][3]),
					0.0,
					0.0
				]
			)
		)
		disabled = disabled and not bool(button["visible"])
	check.call(
		rows_ok,
		"All five tactical rows are 304x32 at a 38 px step, exactly where the phone shows them"
	)
	check.call(
		disabled, "With no heroes, no boss and no enemy hero every tactical command stays disabled"
	)
	var texts: Array = []
	for entry in layout["texts"]:
		texts.append(String(entry["text"]))
	for want in [
		"STATUS", "1,106", "GOLD", "NORMAL", "LV 2 [SHIELDED]", "Wave 0 (Shield)", "HEROES"
	]:
		check.call(texts.has(want), "The dock prints %s, as the capture does" % want)
	check.call(
		texts.has("No heroes") and texts.has("TACTICAL COMMANDS (HOLD)"),
		"The empty hero list and the tactical header read like the source"
	)
	check.call(
		(
			texts.has("GATHER [G]")
			and texts.has("PROTECT TOWER [T]")
			and texts.has("PROTECT CASTLE [C]")
			and texts.has("ATTACK BOSS [B]")
			and texts.has("ATTACK DMG DEALER [D]")
		),
		"The five tactical labels are the source strings in source order"
	)


## The eight main-menu buttons: the same rects the capture measured.
func _check_menu(fixture: Dictionary, check: Callable) -> void:
	var menu_block: Dictionary = fixture.get("menu", {})
	var buttons: Dictionary = menu_block.get("buttons", {})
	var source_rects: Dictionary = MainMenuScript.get_script_constant_map()["SOURCE_BUTTON_RECTS"]
	var ok := true
	for key in MENU_NODES:
		var node_name: String = MENU_NODES[key]
		var entry: Dictionary = buttons.get(key, {})
		var expect: Array = entry.get("expect", [])
		ok = ok and source_rects.has(node_name)
		if not source_rects.has(node_name) or expect.size() != 4:
			continue
		var rect: Rect2 = source_rects[node_name]
		ok = ok and _rect_near([rect.position.x, rect.position.y, rect.size.x, rect.size.y], expect)
		ok = ok and _rect_near(entry.get("measured", []), expect)
	check.call(ok, "The eight menu buttons sit on the rects the phone capture measured")
	var stack_ok := true
	for index in range(6):
		var entry: Dictionary = buttons.get(
			["hero_shop", "input", "how_to_play", "settings", "credits", "quit"][index], {}
		)
		var expect: Array = entry.get("expect", [])
		stack_ok = stack_ok and expect.size() == 4
		stack_ok = (
			stack_ok and int(expect[0]) == 460 and int(expect[2]) == 360 and int(expect[3]) == 50
		)
		stack_ok = stack_ok and int(expect[1]) == 364 + index * 53
	check.call(stack_ok, "The six-button stack is 360x50 at x=460 with a 53 px step")
	var row: Array = buttons.get("play", {}).get("expect", [])
	var cont: Array = buttons.get("continue", {}).get("expect", [])
	check.call(
		(
			row.size() == 4
			and cont.size() == 4
			and int(cont[0]) == 320
			and int(row[0]) == 660
			and int(cont[1]) == 311
			and int(cont[2]) == 300
		),
		"CONTINUE/PLAY are 300x50 at y=311, 340 px apart around the centre"
	)
	check.call(
		(
			Array(menu_block.get("fill_color", []) as Array).size() == 3
			and int(menu_block.get("frame_color", [])[0]) > 100
			and int(menu_block.get("accent_color", [])[0]) > 240
		),
		"The capture recorded the gold accent, grey frame and dark fill of a source button"
	)


## The live scene: the stone strip exists and stays out of the way on 16:9.
func run_scene(menu: Node, check: Callable) -> void:
	var stone := menu.get_node_or_null("PanelStone")
	check.call(stone != null, "The main menu carries the source stone dock backdrop")
	if stone == null:
		return
	var stone_panel: Rect2i = stone.get("panel")
	check.call(
		stone_panel.size.x == 0 and not stone.visible,
		"On a 16:9 window the backdrop stays invisible and silent"
	)
	check.call(
		(
			menu.get_node("Backdrop").get("background_draws") != null
			and menu.get_node("Ambient") != null
			and menu.get_node("Ornaments") != null
		),
		"Backdrop, fog and ornaments are still the three layers above the stone"
	)
