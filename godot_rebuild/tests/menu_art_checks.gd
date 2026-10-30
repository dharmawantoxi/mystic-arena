extends RefCounted
## Layer 9bs: the baked main-menu background (`bake/bake_menu_background.py`) and the scenes
## recoloured to the `ui_theme.py` palette. The drawn-pixels proof (`background_draws`) lives
## in `run_all.gd`, where the real main menu is on screen.

const MenuBackdrop = preload("res://scripts/ui/menu_backdrop.gd")
const UiSkin = preload("res://scripts/ui/ui_skin.gd")
const MANIFEST := "res://data/art/menu.json"
const SCENES_DIR := "res://scenes/"
# Teal literals the earlier scenes used for text and dim overlays.
const OLD_LITERALS := [
	"Color(0.59, 0.67, 0.66, 1)",
	"Color(0.68, 0.78, 0.75, 1)",
	"Color(0.55, 0.64, 0.63, 1)",
	"Color(0.47, 0.85, 0.76, 1)",
	"Color(0.83, 0.72, 0.46, 1)",
	"Color(0.015, 0.03, 0.04, 0.88)",
]


func run(check: Callable) -> void:
	var manifest: Dictionary = {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if parsed is Dictionary:
		manifest = parsed
	check.call(not manifest.is_empty(), "The menu background manifest parses")
	_check_sheet(check, manifest)
	_check_cover(check)
	_check_scenes(check)


func _check_sheet(check: Callable, manifest: Dictionary) -> void:
	var entry: Dictionary = manifest.get("background", {})
	var size: Array = entry.get("size", [0, 0])
	var image := Image.load_from_file(MenuBackdrop.BACKGROUND)
	var decodes := image != null and image.get_size() == Vector2i(int(size[0]), int(size[1]))
	check.call(decodes, "The menu background decodes at its manifest size")
	# JSON numbers are floats and Array == Array does not equate 1280.0 with 1280.
	var is_frame := int(size[0]) == 1280 and int(size[1]) == 720
	check.call(is_frame, "It is the 1280x720 frame the pygame menu blits")
	var texture := MenuBackdrop.texture()
	check.call(texture != null, "The menu background loads from the imported sheet")
	if image == null:
		return
	var probes: Array = manifest.get("probes", [])
	check.call(probes.size() >= 8, "The bake recorded source pixels: %d" % probes.size())
	var wrong: Array = []
	for row in probes:
		var want := Color8(int(row[2]), int(row[3]), int(row[4]))
		if image.get_pixel(int(row[0]), int(row[1])).to_html(false) != want.to_html(false):
			wrong.append(row)
	check.call(
		wrong.is_empty(), "Every recorded pixel is what the source surface held: %s" % [wrong]
	)


func _check_cover(check: Callable) -> void:
	var same := MenuBackdrop.cover_rect(Vector2(1280, 720))
	check.call(same == Rect2(0, 0, 1280, 720), "A 16:9 window shows the frame 1:1")
	var wide := MenuBackdrop.cover_rect(Vector2(1600, 720))
	check.call(wide.size == Vector2(1600, 900), "A wider window scales the frame up uniformly")
	check.call(wide.position == Vector2(0, -90), "and crops it equally above and below")
	var tall := MenuBackdrop.cover_rect(Vector2(1280, 900))
	check.call(tall.size == Vector2(1600, 900), "A taller window scales by height")
	check.call(tall.position == Vector2(-160, 0), "and crops it equally left and right")
	var covers := true
	for window in [Vector2(800, 600), Vector2(1920, 1080), Vector2(1000, 1400)]:
		var rect := MenuBackdrop.cover_rect(window)
		covers = covers and rect.position.x <= 0.01 and rect.position.y <= 0.01
		covers = covers and rect.end.x >= window.x - 0.01 and rect.end.y >= window.y - 0.01
	check.call(covers, "The frame always covers the window")


func run_scene(menu: Node, check: Callable) -> void:
	check.call(
		(
			menu.get_node("%Title").text == "MYSTIC ARENA"
			and menu.get_node("%Subtitle").text == "B A T T L E   A R E N A"
			and menu.get_node("%Scope").text == "Dark Fantasy MOBA  •  Tower Defense"
		),
		"MainMenu uses the source title, subtitle and tagline rather than rebuild marketing copy"
	)
	var expected := {
		"ContinueButton": Rect2(320.0, 311.0, 300.0, 50.0),
		"PlayButton": Rect2(660.0, 311.0, 300.0, 50.0),
		"HeroShopButton": Rect2(460.0, 364.0, 360.0, 50.0),
		"InputButton": Rect2(460.0, 417.0, 360.0, 50.0),
		"HowToPlayButton": Rect2(460.0, 470.0, 360.0, 50.0),
		"SettingsButton": Rect2(460.0, 523.0, 360.0, 50.0),
		"CreditsButton": Rect2(460.0, 576.0, 360.0, 50.0),
		"QuitButton": Rect2(460.0, 629.0, 360.0, 50.0),
	}
	# The source frame is laid out with `fit` around a centred origin (stretch aspect
	# `expand`), so the proof is the 1280x720 source rect reproduced at the live
	# viewport rather than a hard-coded 1:1 assumption.
	var viewport_size: Vector2 = menu.size
	var fit := minf(viewport_size.x / 1280.0, viewport_size.y / 720.0)
	var origin := (viewport_size - Vector2(1280.0, 720.0) * fit) * 0.5
	var misplaced: Array = []
	for button_name in expected:
		var button := menu.get_node("%" + button_name) as Control
		var rect: Rect2 = expected[button_name]
		var want := Rect2(origin + rect.position * fit, rect.size * fit)
		var placed := (
			is_equal_approx(button.position.x, want.position.x)
			and is_equal_approx(button.position.y, want.position.y)
			and is_equal_approx(button.size.x, want.size.x)
			and is_equal_approx(button.size.y, want.size.y)
		)
		if not button.visible or not placed:
			(
				misplaced
				. append(
					(
						"%s visible=%s position=%s size=%s want=%s viewport=%s"
						% [
							button_name,
							button.visible,
							button.position,
							button.size,
							want,
							menu.size,
						]
					)
				)
			)
	check.call(
		misplaced.is_empty(),
		(
			"MainMenu buttons match the source two-button row and six-button vertical stack: %s"
			% [misplaced]
		)
	)
	check.call(
		(
			menu.get_node("%ContinueButton").text == "CONTINUE"
			and menu.get_node("%PlayButton").text in ["PLAY GAME", "MULAI GAME"]
			and menu.get_node("%HeroShopButton").text == "HERO SHOP"
			and menu.get_node("%InputButton").text == "INPUT"
			and menu.get_node("%HowToPlayButton").text == "HOW TO PLAY"
			and menu.get_node("%CreditsButton").text == "CREDITS"
		),
		"MainMenu exposes the source action labels and preserves localization for Play Game"
	)
	check.call(
		not menu.get_node("LegacyControls").visible and not menu.get_node("LevelPicker").visible,
		"Godot-only lab shortcuts and prototype selectors stay off the source main menu"
	)


func _check_scenes(check: Callable) -> void:
	var dim := UiSkin.palette("TEXT_DIM")
	var muted := "Color(%s, %s, %s, 1)" % [_f(dim.r), _f(dim.g), _f(dim.b)]
	var gold := UiSkin.palette("GOLD")
	var cyan := UiSkin.palette("CYAN")
	var found := {"muted": 0, "gold": 0, "cyan": 0, "dim": 0}
	var stale: Array = []
	var dir := DirAccess.open(SCENES_DIR)
	for folder in dir.get_directories():
		var scene_dir := DirAccess.open(SCENES_DIR + folder)
		for file in scene_dir.get_files():
			if not file.ends_with(".tscn"):
				continue
			var text := FileAccess.get_file_as_string(SCENES_DIR + folder + "/" + file)
			for literal in OLD_LITERALS:
				if text.contains(literal):
					stale.append("%s/%s %s" % [folder, file, literal])
			found["muted"] += text.count(muted)
			found["gold"] += text.count(
				"Color(%s, %s, %s, 1)" % [_f(gold.r), _f(gold.g), _f(gold.b)]
			)
			found["cyan"] += text.count(
				"Color(%s, %s, %s, 1)" % [_f(cyan.r), _f(cyan.g), _f(cyan.b)]
			)
			found["dim"] += text.count("Color(0.0392, 0.0392, 0.0784, 0.7843)")
	check.call(stale.is_empty(), "No scene keeps the old teal literals: %s" % [stale])
	# Layer 9bv18 ported the source main menu and dropped the experimental cyan
	# eyebrow, so the pinned literals are the source dim/gold palette only.
	check.call(found["muted"] == 6, "Muted labels use TEXT_DIM: %d" % found["muted"])
	check.call(found["gold"] >= 1, "The gold counter uses GOLD: %d" % found["gold"])
	check.call(
		found["cyan"] == 0, "No scene keeps the experimental cyan eyebrow: %d" % found["cyan"]
	)
	check.call(found["dim"] == 4, "Pause dims are the source (10, 10, 20, 200): %d" % found["dim"])


## A colour channel the way the scene files print it (four decimals, no trailing zeros).
func _f(channel: float) -> String:
	var text := "%.4f" % channel
	while text.contains(".") and (text.ends_with("0") or text.ends_with(".")):
		text = text.substr(0, text.length() - 1)
	return text
