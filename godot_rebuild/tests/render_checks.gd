extends RefCounted
## Layer 9ch: whole `_render.py` coverage — the seven merged render modules.
##
## `_render.py` is 3.671 lines: `map_renderer.py`, `effects.py`, `effects_death.py`,
## `effects_intro.py`, `effects_level_intro.py`, `sprite_cache.py` and
## `render_cache.py` merged into one file plus the bundled font system. The rebuild
## has carried these classes for many layers, so this layer proves the coverage
## instead of re-porting it:
##
## * the inventory (eight sections, 17 classes, 108 `def`s, 16 module functions,
##   seven module assigns) matches the source, and all 156 symbols are classified
##   with a target file that really contains their token — reachability is computed
##   from each class's `self.x()` edges, so the five boss-intro draw helpers that
##   `draw()` never calls are `dead` instead of a silent "ported";
## * `tests/render_source_oracle.py` runs the REAL module (stub `pygame`, `_core`
##   settings namespace) and this suite replays what no per-class oracle covers: the
##   style→file font table, the clamp inside `RenderCache.get_font`, the four easing
##   curves, the two input-mode labels and the two module singletons;
## * every classification token is present in its target, and the 17 per-class
##   oracle/checks pairs are named so a regression cannot hide behind this file;
## * `_skip_button_label()` is player-facing on Android. pygame shows "TAP" in touch
##   mode and the controller button in controller mode; the celebration layout used
##   to hardcode "SPACE" (layer 9ch wires `skip_hint.gd` through `PrototypeView`).
##
## Sync: python3 godot_rebuild/tests/render_source_oracle.py --write

const SkipHint = preload("res://scripts/ui/skip_hint.gd")
const CelebrationLayout = preload("res://scripts/ui/boss_celebration_layout.gd")
const BossDeath = preload("res://scripts/ui/boss_death_animation.gd")
const SourceFonts = preload("res://scripts/ui/source_fonts.gd")
const LevelIntro = preload("res://scripts/ui/level_intro_screen.gd")
const Popup = preload("res://scripts/ui/popup_animation.gd")
const WaveAnnouncer = preload("res://scripts/ui/wave_announcer.gd")
const SpriteCacheScript = preload("res://scripts/ui/sprite_cache.gd")
const RenderCacheScript = preload("res://scripts/ui/render_cache.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/render_source.json"

const TOTALS := {
	"lines": 3671,
	"sections": 8,
	"classes": 17,
	"methods": 108,
	"top_functions": 16,
	"assigns": 7,
}
const SECTION_NAMES := [
	"font_system",
	"map_renderer",
	"effects",
	"effects_death",
	"effects_intro",
	"effects_level_intro",
	"sprite_cache",
	"render_cache",
]
const KINDS := {"data": 7, "dead": 8, "deviation": 1, "folded": 0, "ported": 140}
const SYMBOL_COUNT := 156
const DEAD_SYMBOLS := [
	"class:BossIntroCinematic._draw_boss_silhouette",
	"class:BossIntroCinematic._draw_boss_text",
	"class:BossIntroCinematic._draw_hp_preview",
	"class:BossIntroCinematic._draw_mini_boss_silhouette",
	"class:BossIntroCinematic._draw_skip_hint",
	"class:BossIntroCinematic._draw_true_boss_silhouette",
	"top:_ease_out_cubic@1255",
	"top:_ease_out_elastic@1260",
]
const TARGET_SOURCE_ONLY := ["dead", "deviation", "meta"]


static func _json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


## Fixture targets stay repo-relative; the suite prefixes them with the project root alias.
static func _target_text(path: String) -> String:
	if not path.begins_with("godot_rebuild/"):
		return ""
	var local: String = "res://" + path.trim_prefix("godot_rebuild/")
	if not FileAccess.file_exists(local):
		return ""
	return FileAccess.get_file_as_string(local)


func run(check: Callable) -> void:
	var data: Dictionary = _json(FIXTURE)
	check.call(not data.is_empty(), "_render fixture parses")
	if data.is_empty():
		return
	_check_inventory(check, data)
	_check_classification(check, data)
	_check_suites(check, data)
	_check_easing(check, data)
	_check_prompts(check, data)
	_check_fonts(check, data)
	_check_caches(check, data)
	_check_skip_hint(check, data)
	# Leave the module singletons pristine for the suites that run after this one.
	SpriteCacheScript.reset_shared()
	RenderCacheScript.reset_shared()


## The file really is the seven-module render bundle this layer claims.
func _check_inventory(check: Callable, data: Dictionary) -> void:
	var file: Dictionary = data["file"]
	for key in TOTALS:
		check.call(
			int(file.get(key, -1)) == TOTALS[key],
			"_render.py %s is %s (got %s)" % [key, TOTALS[key], str(file.get(key))]
		)
	check.call(String(file.get("file", "")) == "_render.py", "the oracle reads the source file")
	var sections: Array = data["sections"]
	check.call(sections.size() == 8, "the render bundle keeps its eight sections")
	var names: Array = []
	for index in range(sections.size()):
		var row: Dictionary = sections[index]
		names.append(String(row["name"]))
		check.call(
			int(row["lines"]) == int(row["end"]) - int(row["start"]) + 1,
			"section %s spans its own range" % row["name"]
		)
		if index + 1 < sections.size():
			check.call(
				int(sections[index + 1]["start"]) == int(row["end"]) + 1,
				"sections stay contiguous after %s" % row["name"]
			)
	check.call(names == SECTION_NAMES, "the merged modules keep the source order")
	check.call(
		int(sections[0]["start"]) == 1 and int(sections[7]["end"]) == 3671,
		"the sections cover the whole file"
	)


## Every symbol of `_render.py` is classified and its target really has the token.
func _check_classification(check: Callable, data: Dictionary) -> void:
	var symbols: Dictionary = data["symbols"]
	check.call(
		int(symbols["count"]) == SYMBOL_COUNT,
		"%d symbols are classified (got %s)" % [SYMBOL_COUNT, str(symbols["count"])]
	)
	var kinds: Dictionary = symbols["kinds"]
	for kind in KINDS:
		check.call(
			int(kinds.get(kind, -1)) == KINDS[kind],
			"kind %s counts %s (got %s)" % [kind, KINDS[kind], str(kinds.get(kind))]
		)
	var rows: Dictionary = data["classification"]
	check.call(rows.size() == SYMBOL_COUNT, "every symbol has one classification row")
	var broken: Array = []
	var untargeted: Array = []
	for symbol in rows:
		var row: Dictionary = rows[symbol]
		var target := String(row["target"])
		var token := String(row["token"])
		if target.is_empty() or token.is_empty():
			if not TARGET_SOURCE_ONLY.has(String(row["kind"])):
				untargeted.append(symbol)
			continue
		if not _target_text(target).contains(token):
			broken.append(symbol)
	check.call(
		broken.is_empty(),
		"every classification token is present in its target (broken: %s)" % str(broken)
	)
	check.call(
		untargeted.is_empty(),
		"only dead/deviation/meta rows may skip a Godot target (%s)" % str(untargeted)
	)
	var dead: Array = data["dead_helpers"]
	check.call(
		dead == DEAD_SYMBOLS,
		"the six unreachable boss-intro helpers and two unused easings stay dead"
	)
	check.call(
		data["duplicates"] is Dictionary and (data["duplicates"] as Dictionary).is_empty(),
		"_render.py has no duplicated symbol"
	)


## The 17 per-class oracle/checks pairs still exist, so this suite cannot mask them.
func _check_suites(check: Callable, data: Dictionary) -> void:
	var suites: Dictionary = data["suites"]
	check.call(suites.size() == 17, "seventeen classes carry a per-class suite row")
	var missing: Array = []
	for suite_name in suites:
		var row: Dictionary = suites[suite_name]
		for key in ["oracle", "checks"]:
			var path: String = String(row[key])
			if path.is_empty() or _target_text(path).is_empty():
				missing.append("%s %s" % [suite_name, key])
	check.call(
		missing.is_empty(),
		"every class keeps its per-class oracle and native suite (%s)" % str(missing)
	)


## The four easing helpers, replayed from the real source values.
func _check_easing(check: Callable, data: Dictionary) -> void:
	var easing: Dictionary = data["easing"]
	var inputs: Array = easing["inputs"]
	check.call(inputs.size() == 11, "eleven easing samples came out of the oracle")
	var out_back: Array = easing["_ease_out_back"]
	var in_back: Array = easing["_ease_in_back"]
	var drift: Array = []
	for index in range(inputs.size()):
		var t: float = float(inputs[index])
		if absf(float(Popup._ease_out_back(t)) - float(out_back[index])) > 1e-9:
			drift.append("out_back %.4f" % t)
		if absf(float(WaveAnnouncer._ease_in_back(t)) - float(in_back[index])) > 1e-9:
			drift.append("in_back %.4f" % t)
	check.call(drift.is_empty(), "the easing curves keep the source values (%s)" % str(drift))
	check.call(
		absf(float(Popup._ease_out_back(0.25)) - 0.817409688) < 1e-9
		and absf(float(Popup._ease_out_back(0.5)) - 1.0876975) < 1e-8,
		"ease-out-back overshoots exactly like pygame"
	)
	check.call(
		absf(float(WaveAnnouncer._ease_in_back(0.1)) - (-0.01431422)) < 1e-8,
		"ease-in-back dips below zero like pygame"
	)


## `_begin_prompt_text()` and `_skip_button_label()` in every input mode.
func _check_prompts(check: Callable, data: Dictionary) -> void:
	var prompts: Dictionary = data["prompts"]
	var intro = LevelIntro.new()
	check.call(
		intro.get_begin_prompt(false) == String(prompts["begin_prompt_keyboard"]),
		"the keyboard intro prompt matches pygame"
	)
	check.call(
		intro.get_begin_prompt(true) == String(prompts["begin_prompt_touch"]),
		"the touch intro prompt matches pygame"
	)
	check.call(
		SkipHint.label(false) == String(prompts["skip_label_keyboard"]),
		"a keyboard-only build shows SPACE"
	)
	check.call(
		SkipHint.label(true) == String(prompts["skip_label_touch"]),
		"touch mode shows TAP, like platform_utils.TOUCH_MODE"
	)
	check.call(
		SkipHint.label(false, true, "A") == String(prompts["skip_label_controller_A"])
		and SkipHint.label(false, true, "Cross")
		== String(prompts["skip_label_controller_Cross"]),
		"controller mode shows the bound button"
	)
	check.call(
		SkipHint.label(false, true, "") == String(prompts["skip_label_no_manager"])
		and SkipHint.label(false, false, "A") == String(prompts["skip_label_controller_mode_off"]),
		"no controller runtime falls back to SPACE"
	)
	check.call(
		SkipHint.label(true, true, "A") == String(prompts["skip_label_touch"]),
		"touch mode wins over the controller, as in the source order"
	)


## `_STYLE_FONT_MAP`, the resolver and the 8..220 font clamp.
func _check_fonts(check: Callable, data: Dictionary) -> void:
	var fonts: Dictionary = data["fonts"]
	var styles: Dictionary = fonts["styles"]
	for style in styles:
		if style == "unknown":
			continue
		check.call(
			SourceFonts.file_for_style(style) == String(styles[style]),
			"style %s keeps the source TTF" % style
		)
	check.call(
		SourceFonts.file_for_style("nope") == String(styles["unknown"]),
		"an unknown style falls back to Barlow-Regular.ttf"
	)
	check.call(
		SourceFonts.file_for_style("title") == String(fonts["title_file"]),
		"the title style is Cinzel, like _TITLE_FONT_FILE"
	)
	var make_font: Dictionary = fonts["make_font"]
	check.call(
		int(make_font["resolved_size"]) == 24
		and String(make_font["resolved_file"]) == "Barlow-Regular.ttf",
		"_make_font resolves size + bundled file"
	)
	var title_font: Dictionary = fonts["title_font"]
	check.call(
		int(title_font["resolved_size"]) == 66
		and String(title_font["resolved_file"]) == "Cinzel.ttf"
		and bool(title_font["bold"]),
		"title_font uses Cinzel at the requested size, bold"
	)
	var clamp: Dictionary = fonts["title_clamp"]
	check.call(
		int(clamp["resolved_size"]) == RenderCacheScript.FONT_MAX,
		"title_font clamps to 220 like the source"
	)
	var cache = RenderCacheScript.get_shared()
	var clamp_rows: Array = (data["caches"]["render"]["font_clamp"] as Array).duplicate()
	check.call(
		int(cache.get_font(400, "body", false)["size"]) == int(clamp_rows[1])
		and int(cache.get_font(1, "body", false)["size"]) == int(clamp_rows[0]),
		"RenderCache.get_font clamps into 8..220 like the source"
	)
	check.call(
		SourceFonts.file_for_style("body") == "Barlow-Regular.ttf"
		and SourceFonts.file_for_style("body_bold") == "Barlow-Bold.ttf",
		"the four Barlow weights stay distinct"
	)


## The module singletons behind the global shortcuts.
func _check_caches(check: Callable, data: Dictionary) -> void:
	var caches: Dictionary = data["caches"]
	var sprite_expected: Dictionary = caches["sprite"]
	SpriteCacheScript.reset_shared()
	var sprite = SpriteCacheScript.get_shared()
	check.call(sprite == SpriteCacheScript.get_shared(), "SpriteCache stays a singleton")
	check.call(
		int(sprite.max_cache) == int(sprite_expected["max_cache"]),
		"the sprite cache keeps its 2000 entry ceiling"
	)
	var calls := [0]
	var paint := func(surface: Dictionary) -> void:
		calls[0] += 1
		surface["painted"] = true
	var first = SpriteCacheScript.get_cached_sprite(["idle", "blue", 1, "walk"], 40, 40, paint)
	var second = SpriteCacheScript.get_cached_sprite(["idle", "blue", 1, "walk"], 40, 40, paint)
	check.call(first == second, "the same key returns the same cached surface")
	check.call(calls[0] == 1, "the render callback runs once per miss")
	var stats: Dictionary = sprite.get_stats()
	check.call(
		int(stats["hits"]) == 1 and int(stats["misses"]) == 1 and int(stats["cached"]) == 1,
		"one miss then one hit, like the source counters"
	)
	check.call(
		String(stats["hit_rate"]).ends_with("%"),
		"the hit rate keeps the source %.1f%% formatting (got " + str(stats["hit_rate"]) + ")"
	)
	var cropped = SpriteCacheScript.get_cached_sprite_cropped(
		["idle", "red", 1, "walk"], 40, 40, paint, Vector2i(20, 36)
	)
	check.call(
		cropped is Array and (cropped as Array).size() == 3,
		"the cropped path returns surface + anchor, like the source tuple"
	)
	SpriteCacheScript.clear_sprite_cache()
	check.call(
		int(sprite.get_stats()["cached"]) == 0,
		"clear_sprite_cache empties both tables but keeps the counters"
	)
	check.call(
		int(sprite.get_stats()["hits"]) == 1,
		"the counters survive a clear, like the source"
	)

	var render_expected: Dictionary = caches["render"]
	RenderCacheScript.reset_shared()
	var render_cache = RenderCacheScript.get_shared()
	check.call(render_cache == RenderCacheScript.get_shared(), "RenderCache stays a singleton")
	var font_a = RenderCacheScript.get_cached_font(20, "title", true)
	var font_b = RenderCacheScript.get_cached_font(20, "title", true)
	check.call(
		(font_a == font_b) == bool(render_expected["same_font"]),
		"the same font key returns the same entry"
	)
	check.call(
		String(font_a["style"]) == "title"
		and bool(font_a["bold"]) == bool(render_expected["font_bold"])
		and int(font_a["size"]) == int(render_expected["font_size"]),
		"the cached font keeps size, style and bold"
	)
	var circle_a = RenderCacheScript.get_cached_circle(10, [255, 0, 0], 0)
	var circle_b = RenderCacheScript.get_cached_circle(10, [255, 0, 0], 0)
	check.call(
		(circle_a == circle_b) == bool(render_expected["same_circle"]),
		"the same circle key returns the same entry"
	)
	var glow_a = RenderCacheScript.get_cached_glow(12, [0, 255, 0], 3)
	var glow_b = RenderCacheScript.get_cached_glow(12, [0, 255, 0], 3)
	check.call(
		(glow_a == glow_b) == bool(render_expected["same_glow"]),
		"the same glow key returns the same entry"
	)
	var glow_px: Array = render_expected["glow_size"]
	check.call(
		int(glow_a["width"]) == int(glow_px[0]) and int(glow_a["height"]) == int(glow_px[1]),
		"a glow surface is radius*2+4 like the source"
	)
	check.call(int(glow_a["layers"]) == 3, "the glow keeps its layer count")
	var render_stats: Dictionary = render_cache.get_stats()
	check.call(
		int(render_stats["fonts"]) == 1 and int(render_stats["circles"]) == 1
		and int(render_stats["surfaces"]) == 1,
		"font clamp, circle and glow fill the three tables (got %s)" % str(render_stats)
	)
	RenderCacheScript.clear_shared_cache()
	var cleared: Dictionary = render_cache.get_stats()
	check.call(
		int(cleared["fonts"]) == 1 and int(cleared["circles"]) == 0
		and int(cleared["surfaces"]) == 0,
		"clear_cache keeps fonts, like the source comment says"
	)


## `_skip_button_label()` reaches the celebration banner, not a hardcoded SPACE.
func _check_skip_hint(check: Callable, data: Dictionary) -> void:
	var prompts: Dictionary = data["prompts"]
	check.call(
		SkipHint.hint("TAP", "continue") == String(prompts["hint_continue_touch"]),
		"the hint line matches f\"[{label}] to continue\""
	)
	check.call(
		SkipHint.hint("SPACE", "continue") == String(prompts["hint_continue_keyboard"]),
		"the keyboard hint line matches pygame"
	)
	check.call(
		SkipHint.hint("TAP", "skip") == String(prompts["hint_skip_touch_line"]),
		"the dead intro hint uses the same line builder"
	)

	var anim = BossDeath.new()
	anim.configure({"name": "Test", "boss_class": "true"}, 1280, 720)
	anim.celebration_active = true
	anim.celebration_timer = int(anim.celebration_duration) - int(
		float(anim.celebration_duration) * 0.6
	)
	var measure := func(text: String, font_size: int) -> Vector2i:
		return Vector2i(int(float(font_size) * 0.55) * text.length(), font_size)
	var touch_ops: Array = CelebrationLayout.ops(anim, 0, measure, true, "TAP")
	var keyboard_ops: Array = CelebrationLayout.ops(anim, 0, measure, true, "SPACE")
	check.call(
		_has_text(touch_ops, "[TAP] to continue"),
		"the celebration draws the touch hint on Android"
	)
	check.call(
		_has_text(keyboard_ops, "[SPACE] to continue"),
		"the keyboard build keeps the SPACE hint"
	)
	check.call(
		not _has_text(touch_ops, "[SPACE] to continue"),
		"a touch build never says SPACE"
	)
	var default_ops: Array = CelebrationLayout.ops(anim, 0, measure)
	check.call(
		_has_text(default_ops, "[SPACE] to continue"),
		"the layout default stays the keyboard label"
	)

	var view = PrototypeView.new()
	check.call(view.skip_hint_label() == "SPACE", "a view without runtimes says SPACE")
	view.skip_hint_touch_mode = true
	check.call(view.skip_hint_label() == "TAP", "the view follows the touch mode the screen pushes")
	view.skip_hint_touch_mode = false
	view.skip_hint_controller_label = "Cross"
	check.call(view.skip_hint_label() == "Cross", "the view follows the controller label")
	view.free()
	var screen_source := FileAccess.get_file_as_string("res://scenes/prototype/prototype_screen.gd")
	check.call(
		screen_source.contains("skip_hint_touch_mode")
		and screen_source.contains('get_action_label("skip")'),
		"the screen pushes the input mode into the arena"
	)


static func _has_text(ops: Array, needle: String) -> bool:
	for op in ops:
		if op is Dictionary and String(op.get("kind", "")) == "text":
			if String(op.get("text", "")) == needle:
				return true
	return false
