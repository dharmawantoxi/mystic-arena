extends RefCounted
## Port of the startup banner `main.py` prints before the loop (layer 9cn).
##
## The source prints one eight-line block: a 60-character rule, the build name,
## device model, Android release + API level, the save directory, the active
## input mode and the quality preset. The block is console only (logcat on
## Android), but it is the first thing anyone debugging a device build looks at,
## so the native shell writes the same lines with the same spacing.

## `print("=" * 60)`.
const RULE := "============================================================"
const TITLE_LINE := "  MYSTIC ARENA - MOBILE BUILD"


## The exact eight lines the source prints. `api_level` is passed through as text
## because the source formats it with `%s`.
static func lines(
	device: String,
	android_release: String,
	api_level: String,
	save_dir: String,
	touch_mode: bool,
	quality: String
) -> PackedStringArray:
	return PackedStringArray([
		RULE,
		TITLE_LINE,
		"  device : %s" % device,
		"  android: %s (API %s)" % [android_release, api_level],
		"  save   : %s" % save_dir,
		"  input  : %s" % input_mode(touch_mode),
		"  quality: %s" % quality,
		RULE,
	])


## `"TOUCH" if plat.TOUCH_MODE else "MOUSE/KEYBOARD"`.
static func input_mode(touch_mode: bool) -> String:
	return "TOUCH" if touch_mode else "MOUSE/KEYBOARD"


## Live values for the running build. Android does not expose the numeric API
## level to GDScript, so that field carries `-` (deviation D3).
static func collect(tree: SceneTree) -> PackedStringArray:
	var quality := "HIGH"
	if tree != null and tree.root != null:
		var adaptive := tree.root.get_node_or_null("AdaptiveQuality")
		if adaptive != null:
			quality = String(adaptive.get("quality_level"))
	return lines(
		OS.get_model_name(),
		OS.get_version(),
		"-",
		ProjectSettings.globalize_path("user://"),
		OS.has_feature("android"),
		quality,
	)
