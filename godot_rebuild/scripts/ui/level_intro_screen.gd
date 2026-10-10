extends RefCounted
## Level intro card, ported from `_render.py::LevelIntroScreen`.
##
## `update()` counts the fade-in ticks and reports the first tick (the source
## plays `wave_start` then). `handle_skip()` ends the card on space / enter or
## a click. `get_fade_alpha()` / `get_theme_tint_alpha()` expose the fade-in
## curve the source computes inside `draw()`, `get_difficulty_info()` and
## `get_bar_color()` the difficulty bars, and the gold / passive / boss-tag /
## prompt getters the text the source renders. All of them are read straight
## off the source by `level_intro_screen_source_oracle.py`, which runs the real
## `draw()` and reads the locals with `sys.settrace`.
##
## Left unported: every `draw()` / `_draw_*` body (the vignette, divider,
## silhouette, aura rays, eye glow, arrows, shadows) and the `pygame.time`
## pulses that drive them. The starting gold and passive income come from
## `_core.compute_starting_gold` / `compute_gold_per_second`, which are not
## part of this slice, so the port uses the source's own `except` fallbacks.

const FADE_IN_DURATION := 30
const GOLD_PER_SECOND := 3
const PROMPT_TEXT := "PRESS SPACE TO BEGIN"
const TOUCH_PROMPT_TEXT := "TAP TO BEGIN"
const WARNING_TEXT := "PREPARE FOR BATTLE"
const DEFAULT_RGB := [150, 100, 200]
const DEFAULT_DARK_RGB := [75, 50, 100]
const FALLBACK_STARTING_GOLD := 1000
const FALLBACK_REWARD := 500

const THEME_TINT_RGB := {
	"desert": [100, 60, 20],
	"ice": [40, 80, 130],
	"ocean": [30, 70, 120],
	"abyss": [40, 10, 10],
	"nethervenom": [25, 55, 15],
	"spectral": [15, 50, 55],
	"sundered": [70, 30, 8],
	"empyrean": [70, 55, 15],
	"solaris": [85, 50, 10],
	"abysstide": [10, 50, 50],
	"crimsonmatriarch": [60, 10, 15],
	"astral": [15, 25, 60],
	"shadowchain": [45, 12, 60],
	"frostveil": [25, 45, 85],
	"warshade": [10, 40, 48],
	"outlaw": [80, 45, 35],
	"hexbound": [55, 25, 75],
	"voidbound": [45, 18, 70],
	"earthborn": [45, 55, 25],
	"heartbane": [60, 18, 55],
	"sunfist": [80, 55, 12],
	"voidwing": [45, 15, 65],
	"crimsondevourer": [60, 10, 15],
	"elementweave": [55, 30, 75],
	"tempest": [20, 40, 90],
	"sawmill": [70, 45, 18],
	"croweye": [55, 12, 18],
	"crystalstorm": [30, 45, 85],
	"eternalwarlord": [70, 15, 20],
	"explosiveart": [70, 18, 18],
	"sandshadow": [85, 35, 22],
	"emberweaver": [95, 28, 22],
	"skyfury": [70, 45, 20],
}
const FOREST_TINT_RGB := [20, 40, 20]

var active := true
var timer := 0
var sound_played := false
var screen_w := 1280
var screen_h := 720

var level_num := 0
var level_name := ""
var level_desc := ""
var hp_mult := 1.0
var dmg_mult := 1.0
var reward := FALLBACK_REWARD
var map_theme := "forest"
var starting_gold := FALLBACK_STARTING_GOLD

var boss_type := ""
var boss_name := "Unknown"
var boss_title := "The Boss"
var boss_color: Array = DEFAULT_RGB.duplicate()
var boss_color_dark: Array = DEFAULT_DARK_RGB.duplicate()
var boss_entrance_color: Array = DEFAULT_RGB.duplicate()
var boss_class := "true"


## `level_config` is the level dictionary; `boss` is the entry the caller looked
## up in the boss table (an empty dictionary falls back to the source defaults).
func setup(level_config: Dictionary, boss: Dictionary, width: int, height: int) -> void:
	screen_w = width
	screen_h = height
	level_num = int(level_config["level_number"])
	level_name = String(level_config["name"])
	level_desc = String(level_config["description"])
	hp_mult = float(level_config.get("enemy_hp_mult", 1.0))
	dmg_mult = float(level_config.get("enemy_damage_mult", 1.0))
	reward = int(level_config.get("meta_gold_reward_win", FALLBACK_REWARD))
	map_theme = String(level_config.get("map_theme", "forest"))
	starting_gold = int(level_config.get("starting_gold", FALLBACK_STARTING_GOLD))

	boss_type = String(level_config.get("true_boss", "abaddon"))
	boss_name = String(boss.get("name", "Unknown"))
	boss_title = String(boss.get("title", "The Boss"))
	boss_color = _to_rgb(boss.get("color", null), DEFAULT_RGB)
	boss_color_dark = _to_rgb(boss.get("color_dark", null), DEFAULT_DARK_RGB)
	boss_entrance_color = _to_rgb(boss.get("entrance_color", null), DEFAULT_RGB)
	boss_class = String(boss.get("boss_class", "true"))


## Advances the fade clock. Returns true on the first tick only, which is the
## tick the source plays the `wave_start` sound.
func update() -> bool:
	if not active:
		return false
	timer += 1
	if sound_played:
		return false
	sound_played = true
	return true


## Space, enter or a click ends the card. Returns whether this input did it.
func handle_skip(keycode: int = -1, click: bool = false) -> bool:
	if not active:
		return false
	if keycode == KEY_SPACE or keycode == KEY_ENTER or click:
		active = false
		return true
	return false


func is_active() -> bool:
	return active


func get_fade_alpha() -> int:
	if timer < FADE_IN_DURATION:
		return int(255.0 * (float(timer) / float(FADE_IN_DURATION)))
	return 255


func get_theme_tint_alpha() -> int:
	return int(30.0 * (float(get_fade_alpha()) / 255.0))


## Tint as the source fills it: the theme's RGB plus the current tint alpha.
func get_theme_tint_rgba() -> Array:
	var rgb: Array = THEME_TINT_RGB.get(map_theme, FOREST_TINT_RGB)
	return [rgb[0], rgb[1], rgb[2], get_theme_tint_alpha()]


func get_show_prompt() -> bool:
	return timer > FADE_IN_DURATION


func get_begin_prompt(touch_mode: bool = false) -> String:
	if touch_mode:
		return TOUCH_PROMPT_TEXT
	return PROMPT_TEXT


func get_warning_text() -> String:
	return WARNING_TEXT


## Difficulty card: title, bar count and colour, as `_draw_level_info` picks them.
func get_difficulty_info(difficulty: String) -> Dictionary:
	if difficulty == "hard":
		return {
			"title": "DIFFICULTY: HARD",
			"level": clampi(int(hp_mult * 2.5), 1, 5),
			"color": [255, 120, 100],
		}
	if difficulty == "easy":
		return {"title": "DIFFICULTY: EASY", "level": 1, "color": [100, 210, 255]}
	return {"title": "DIFFICULTY: NORMAL", "level": 1, "color": [100, 220, 150]}


## Colour of bar `index` (0..4) when the card shows `level` filled bars.
func get_bar_color(index: int, level: int) -> Array:
	if index >= level:
		return [60, 60, 70]
	if index >= 3:
		return [255, 100, 80]
	if index >= 1:
		return [255, 200, 80]
	return [100, 220, 100]


func get_reward_text() -> String:
	return "+%d HERO GOLD" % reward


func get_starting_gold() -> int:
	return starting_gold


func get_starting_gold_text() -> String:
	return "%s GOLD" % _with_commas(starting_gold)


func get_passive_text() -> String:
	return "PASSIVE +%d/s" % GOLD_PER_SECOND


func get_boss_tag() -> Dictionary:
	if boss_class == "true":
		return {"text": "TRUE BOSS", "color": [255, 80, 80]}
	return {"text": "MINI BOSS", "color": [255, 200, 100]}


static func _to_rgb(value: Variant, fallback: Array) -> Array:
	if not (value is Array) or value.size() < 3:
		return fallback.duplicate()
	return [int(value[0]), int(value[1]), int(value[2])]


## Python's `f"{n:,}"`: thousands separated by commas.
static func _with_commas(value: int) -> String:
	var digits := str(absi(value))
	var out := ""
	var count := 0
	for i in range(digits.length() - 1, -1, -1):
		if count > 0 and count % 3 == 0:
			out = "," + out
		out = digits[i] + out
		count += 1
	if value < 0:
		return "-" + out
	return out
