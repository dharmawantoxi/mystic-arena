# gdlint:disable=max-public-methods
extends RefCounted
## Port of `_render.py::LevelIntroScreen` — state and derived getters only;
## the pygame blits (darken, tint, vignette, boss silhouette, text) stay
## behind and a later renderer reads the getters.
##
## `level_intro_screen_source_oracle.py` slices the real class out of
## `_render.py`, runs it headless against pygame/mobile.perf/_core shims and
## reads the draw-time locals (fade ramp, theme tint, difficulty branch, bar
## colours, gold fallbacks) off the frames with `sys.settrace`;
## `level_intro_screen_checks.gd` replays that fixture through this class.

## pygame key constants used by the source's skip test.
const KEY_SPACE := 32
const KEY_RETURN := 13

## Top edge of the left-hand level info column (`cy_start` in the source).
const CY_START := 130

## `_core.py:215` — the constant behind the source's passive-income fallback
## line (the in-game path uses `_core.compute_gold_per_second`, which this
## state port does not reach; see the fixture's `income` value).
const GOLD_PER_SECOND := 3

## Theme tints from the source `draw()` if/elif chain, as 8-bit RGB. Unknown
## themes fall back to the source's `else` branch (forest).
const THEME_TINTS := {
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
	"forest": [20, 40, 20],
}

var level_config: Dictionary = {}
var screen_w := 0
var screen_h := 0

var active := true
var timer := 0
var fade_in_duration := 30

var level_num := 1
var level_name := ""
var level_desc := ""
var hp_mult := 1.0
var dmg_mult := 1.0
var reward := 500
var map_theme := "forest"

var boss_type := "abaddon"
var boss_name := "Unknown"
var boss_title := "The Boss"
var boss_color := Color8(150, 100, 200)
var boss_color_dark := Color8(75, 50, 100)
var boss_entrance_color := Color8(150, 100, 200)
var boss_class := "true"

## GameSettings().difficulty equivalent: the source reads it from `_core`
## inside `_draw_level_info`; here it is injected so the three branches stay
## testable without the Python module.
var difficulty := "normal"

## Recorded side effect of `update()` (source plays 'wave_start' once via
## SoundManager); the Godot caller decides how to honour it.
var sound_requests: PackedStringArray = PackedStringArray()

var _sound_played := false


func _init(
	config: Dictionary, screen_width: int, screen_height: int, boss_data: Dictionary = {}
) -> void:
	level_config = config
	screen_w = screen_width
	screen_h = screen_height

	active = true
	timer = 0
	fade_in_duration = 30

	level_num = int(config.get("level_number", 1))
	level_name = str(config.get("name", ""))
	level_desc = str(config.get("description", ""))
	hp_mult = float(config.get("enemy_hp_mult", 1.0))
	dmg_mult = float(config.get("enemy_damage_mult", 1.0))
	reward = int(config.get("meta_gold_reward_win", 500))
	map_theme = str(config.get("map_theme", "forest"))

	boss_type = str(config.get("true_boss", "abaddon"))
	boss_name = str(boss_data.get("name", "Unknown"))
	boss_title = str(boss_data.get("title", "The Boss"))
	boss_color = _color_from(boss_data.get("color", [150, 100, 200]))
	boss_color_dark = _color_from(boss_data.get("color_dark", [75, 50, 100]))
	boss_entrance_color = _color_from(boss_data.get("entrance_color", [150, 100, 200]))
	boss_class = str(boss_data.get("boss_class", "true"))

	_sound_played = false


func _color_from(value: Variant) -> Color:
	if value is Array and value.size() >= 3:
		return Color8(int(value[0]), int(value[1]), int(value[2]))
	if value is Color:
		return value
	return Color8(150, 100, 200)


func update() -> void:
	if not active:
		return
	timer += 1
	if not _sound_played:
		_sound_played = true
		sound_requests.append("wave_start")


func handle_skip(key: int = -1, click: bool = false) -> bool:
	if not active:
		return false
	if key == KEY_SPACE or key == KEY_RETURN or click:
		active = false
		return true
	return false


func is_active() -> bool:
	return active


## `fade_alpha` from draw(): linear ramp over fade_in_duration, then 255.
func get_fade_alpha() -> int:
	if timer < fade_in_duration:
		return int(255.0 * (float(timer) / float(fade_in_duration)))
	return 255


## `darken(surface, min(255, fade_alpha + 30))`.
func get_darken_alpha() -> int:
	return mini(255, get_fade_alpha() + 30)


## `theme_tint_alpha = int(30 * (fade_alpha / 255))`.
func get_theme_tint_alpha() -> int:
	return int(30.0 * (float(get_fade_alpha()) / 255.0))


## The theme tint colour (8-bit RGB from the source chain) with the traced
## alpha applied.
func get_theme_tint() -> Color:
	var rgb: Array = THEME_TINTS.get(map_theme, THEME_TINTS["forest"])
	var tint := Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))
	tint.a = float(get_theme_tint_alpha()) / 255.0
	return tint


## "PRESS SPACE" prompt only appears once the fade-in is done.
func is_prompt_visible() -> bool:
	return timer > fade_in_duration


func divider_x() -> int:
	@warning_ignore("integer_division")
	return screen_w / 2


func level_cx() -> int:
	@warning_ignore("integer_division")
	return screen_w / 4


func boss_cx() -> int:
	@warning_ignore("integer_division")
	return screen_w * 3 / 4


func get_diamond_y(index: int) -> int:
	return 250 + index * 200


func get_boss_tag() -> Dictionary:
	if boss_class == "true":
		return {"text": "TRUE BOSS", "color": Color8(255, 80, 80)}
	return {"text": "MINI BOSS", "color": Color8(255, 200, 100)}


## Difficulty label / bar count / colour from `_draw_level_info`. The hard
## branch scales with the level's HP multiplier; the `int()` casts truncate
## exactly like Python's.
func get_difficulty_info() -> Dictionary:
	if difficulty == "hard":
		return {
			"title": "DIFFICULTY: HARD",
			"level": mini(5, maxi(1, int(hp_mult * 2.5))),
			"color": Color8(255, 120, 100),
		}
	if difficulty == "easy":
		return {
			"title": "DIFFICULTY: EASY",
			"level": 1,
			"color": Color8(100, 210, 255),
		}
	return {
		"title": "DIFFICULTY: NORMAL",
		"level": 1,
		"color": Color8(100, 220, 150),
	}


func get_bar_x(index: int) -> int:
	return level_cx() - 55 + index * 22


func get_bar_y() -> int:
	return CY_START + 370 + 20


func get_bar_color(index: int) -> Color:
	var info := get_difficulty_info()
	var level: int = int(info["level"])
	if index >= level:
		return Color8(60, 60, 70)
	if index >= 3:
		return Color8(255, 100, 80)
	if index >= 1:
		return Color8(255, 200, 80)
	return Color8(100, 220, 100)


## Source fallback `level_config.get("starting_gold", 1000)`. The in-game
## `_core.compute_starting_gold` path belongs to the caller (the match
## economy already ports it); this class mirrors the fallback the oracle can
## exercise.
func get_starting_gold() -> int:
	return int(level_config.get("starting_gold", 1000))


## Source fallback `PASSIVE +{GOLD_PER_SECOND}/s` (the `_core` import path is
## unreachable here, same as in the oracle).
func get_passive_label() -> String:
	return "PASSIVE +%d/s" % GOLD_PER_SECOND


func get_crown_spike_count() -> int:
	return 5 if boss_class == "true" else 3


func get_crown_spike_x(index: int, cx: int) -> int:
	if get_crown_spike_count() == 5:
		return cx - 40 + index * 20
	return cx - 20 + index * 20
