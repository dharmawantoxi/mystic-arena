extends RefCounted
## Layer 9bv20: `mobile/platform_utils.py` as a native screen/platform layer.
##
## The source module owns four things: platform detection, the display mode
## that is persisted between launches (`scaled_vsync` / `scaled` / `native`),
## the notch/gesture-bar safe area, and the mapping between window pixels and
## the 1280x720 logical space every piece of game code uses. The Godot port
## had none of it: `DisplayServer`/`OS` were only touched for the touchscreen
## flag, so the HUD could not sit inside the safe area, nothing kept the
## screen awake, and there was no persisted display mode.
##
## Everything here is a pure function of its arguments (`window_scale_offset`,
## `window_to_logical`, `finger_to_logical`, `pointer_to_logical`,
## `safe_area`, `panel_popup_pos`, `panel_pos_bawah`, `resolve_display_mode`)
## so `tests/mobile_platform_checks.gd` can replay the values recorded from the
## real source by `tests/mobile_platform_source_oracle.py`. The IO wrappers
## (`load_display_mode` / `save_display_mode`) read the same file name.
##
## The dock width rule (`display_width` / `panel_rect` / 120 px minimum) lives
## in `scripts/ui/side_panel_layout.gd` and is not duplicated here.
##
## Deliberate deviations:
## * `enable_immersive_mode()` has no runtime equivalent: Godot's Android
##   export preset owns immersive mode, so the port documents the preset
##   instead of poking `View.SYSTEM_UI_FLAG_*` from GDScript.
## * `present()` (blit/scale per frame) is engine work: Godot's
##   `canvas_items` stretch does it, so no port is needed.
## * `get_writable_dir()` returns `OS.get_user_data_dir()`, the Android
##   private files dir equivalent.

const LOGICAL_WIDTH := 1280
const LOGICAL_HEIGHT := 720

## `platform_utils.DISPLAY_MODES`, in the source's button order.
const DISPLAY_MODES: Array[String] = ["scaled_vsync", "scaled", "native"]
const DEFAULT_MODE := "scaled_vsync"
const MODE_FILE := "display_mode.txt"
const MODE_ENV := "MYSTIC_DISPLAY_MODE"

## `platform_utils.FORCE_TOUCH` (`MYSTIC_FORCE_TOUCH=1`) plus the project switch
## `game/mobile_composition`, which defaults to **true**: the shipped game is the Android
## build, so the PC run composes the mobile HUD, the touch prompts and the right dock
## instead of switching to a desktop-only layout. `MYSTIC_FORCE_TOUCH=1` forces it on;
## `false` in the project setting restores the old desktop composition.
const FORCE_ENV := "MYSTIC_FORCE_TOUCH"
const MOBILE_COMPOSITION_SETTING := "game/mobile_composition"

## `platform_utils._SAFE_MARGIN_LOGICAL`.
const SAFE_MARGIN := 28
const SAFE_TOP := 10
const SAFE_BOTTOM := 20

## Right-panel popup lanes (`ZONA_POPUP_Y`, `ZONA_BAWAH_H`).
const ZONA_POPUP_Y := 430
const ZONA_BAWAH_H := 120
const PANEL_POPUP_MARGIN := 8
const PANEL_PANEL_EDGE := 8


## `_detect_android`: the shipped build is the Android one.
static func is_android() -> bool:
	return OS.has_feature("android")


## `MYSTIC_FORCE_TOUCH == "1"` wins, then the project switch; the default is mobile.
static func forced_touch() -> bool:
	if OS.get_environment(FORCE_ENV) == "1":
		return true
	var configured: Variant = ProjectSettings.get_setting(MOBILE_COMPOSITION_SETTING, true)
	return bool(configured)


## `TOUCH_MODE = IS_ANDROID or FORCE_TOUCH`; the rebuild treats an available
## touchscreen as the same layout switch (the user's touch PC hits this too).
static func is_touch_mode() -> bool:
	return is_android() or forced_touch() or DisplayServer.is_touchscreen_available()


## `get_safe_area`: notch / punch-hole / gesture bar insets in logical space.
static func safe_area(touch_mode: bool) -> Rect2i:
	if not touch_mode:
		return Rect2i(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT)
	return Rect2i(
		SAFE_MARGIN,
		SAFE_TOP,
		LOGICAL_WIDTH - 2 * SAFE_MARGIN,
		LOGICAL_HEIGHT - SAFE_TOP - SAFE_BOTTOM
	)


## `_refresh_display_metrics`: the scale and letterbox offset the source derives
## from the real window size (`min` of both ratios, centred).
static func window_scale_offset(window: Vector2i) -> Dictionary:
	var scale := minf(
		float(window.x) / float(LOGICAL_WIDTH), float(window.y) / float(LOGICAL_HEIGHT)
	)
	var offset := Vector2(
		(float(window.x) - float(LOGICAL_WIDTH) * scale) * 0.5,
		(float(window.y) - float(LOGICAL_HEIGHT) * scale) * 0.5
	)
	return {"scale": scale, "offset": offset}


## `window_to_logical`: window pixels -> 1280x720 logical space. The source
## divides by a scale that is never 0 (it is at least one pixel wide); the
## guard keeps headless calls honest.
static func window_to_logical(point: Vector2, scale: float, offset: Vector2) -> Vector2:
	var divisor := scale if scale != 0.0 else 1.0
	return Vector2((point.x - offset.x) / divisor, (point.y - offset.y) / divisor)


## `finger_to_logical`: Android FINGER events are normalised 0..1.
static func finger_to_logical(
	finger: Vector2, window: Vector2i, scale: float, offset: Vector2
) -> Vector2:
	return window_to_logical(
		Vector2(finger.x * float(window.x), finger.y * float(window.y)), scale, offset
	)


## `pointer_to_logical`: in `scaled_*` modes SDL already translated the point,
## so the source returns it untouched; only `native` needs the mapping.
static func pointer_to_logical(
	mode: String, point: Vector2, scale: float, offset: Vector2
) -> Vector2:
	if mode == "native":
		return window_to_logical(point, scale, offset)
	return point


## Python's `//` floors; GDScript's `/` truncates toward zero.
static func _floor_div(value: int, divisor: int) -> int:
	var quotient := value / divisor
	if value % divisor != 0 and (value < 0) != (divisor < 0):
		quotient -= 1
	return quotient


## `panel_popup_pos`: popup centred in the right panel, vertically clamped.
## Returns `null` when the panel is missing or the popup is wider than it.
static func panel_popup_pos(panel: Rect2i, width: int, height: int, top := 12) -> Variant:
	if panel.size.x <= 0 or width > panel.size.x - PANEL_POPUP_MARGIN:
		return null
	var x := panel.position.x + _floor_div(panel.size.x - width, 2)
	# The source keeps this y panel-local (the panel starts at y=0 in
	# `create_display`), so it is not offset by `panel.position.y`.
	var y := maxi(top, mini(panel.size.y - height - 12, _floor_div(panel.size.y - height, 2)))
	return Vector2i(x, y)


## `panel_pos_bawah`: fixed popup lane at `ZONA_POPUP_Y`, pushed up when the
## panel is too short to keep the notification lane free.
static func panel_pos_bawah(panel: Rect2i, width: int, height: int) -> Variant:
	if panel.size.x <= 0 or width > panel.size.x - PANEL_POPUP_MARGIN:
		return null
	var x := panel.position.x + _floor_div(panel.size.x - width, 2)
	var y := panel.position.y + ZONA_POPUP_Y
	if y + height > panel.position.y + panel.size.y - ZONA_BAWAH_H:
		y = maxi(
			panel.position.y + PANEL_PANEL_EDGE,
			panel.position.y + panel.size.y - ZONA_BAWAH_H - height
		)
	return Vector2i(x, y)


## `load_display_mode` without IO: env var, then the stored file, then default.
static func resolve_display_mode(env_mode: String, file_text: String) -> String:
	if DISPLAY_MODES.has(env_mode):
		return env_mode
	var stored := file_text.strip_edges()
	if DISPLAY_MODES.has(stored):
		return stored
	return DEFAULT_MODE


## `get_writable_dir`: Android's private files dir equivalent.
static func writable_dir() -> String:
	return OS.get_user_data_dir()


static func mode_path() -> String:
	return writable_dir().path_join(MODE_FILE)


## `load_display_mode`.
static func load_display_mode() -> String:
	var stored := ""
	if FileAccess.file_exists(mode_path()):
		stored = FileAccess.get_file_as_string(mode_path())
	return resolve_display_mode(OS.get_environment(MODE_ENV).strip_edges(), stored)


## `save_display_mode`: writes the file and reports success.
static func save_display_mode(mode: String) -> bool:
	var file := FileAccess.open(mode_path(), FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(mode)
	file.close()
	return true


## `keep_screen_on(enable)`; the source can only do this on Android.
static func keep_screen_on(enable := true) -> bool:
	DisplayServer.screen_set_keep_on(enable)
	return is_android()


## `vibrate(ms)`: `Input.vibrate_handheld` is the engine call.
static func vibrate(ms := 25) -> bool:
	Input.vibrate_handheld(ms)
	return is_android()


## `get_device_info`: the fields the debug overlay prints.
static func device_info() -> Dictionary:
	return {
		"platform": "android" if is_android() else OS.get_name().to_lower(),
		"engine": String(Engine.get_version_info().get("string", "")),
		"model": OS.get_model_name(),
		"version": OS.get_version(),
		"screen": DisplayServer.screen_get_size(),
		"window": DisplayServer.window_get_size(),
		"locale": OS.get_locale(),
	}
