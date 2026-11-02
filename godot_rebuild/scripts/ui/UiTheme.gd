class_name UiTheme
extends RefCounted

## Native port of ui_theme.py. All palette/layout numbers come from
## data/ui_theme.json; Python is the oracle, never a runtime dependency.
const DEFAULT_PATH := "res://data/ui_theme.json"
const ICON_COUNT := 29
const PALETTE_COUNT := 32

static var cfg: Dictionary = {}
static var palette: Dictionary = {}
static var defaults: Dictionary = {}
static var load_error := ""
static var quality_level := "high"
static var quality_override: Variant = null
static var _loaded := false


static func ensure_loaded() -> bool:
	if not _loaded:
		load_contract(DEFAULT_PATH)
	return valid()


static func load_contract(path: String) -> bool:
	_loaded = true
	cfg = {}
	palette = {}
	defaults = {}
	load_error = ""
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return false
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		load_error = "Invalid ui_theme contract: %s" % path
		return false
	var data: Dictionary = parsed
	if int(data.get("schema", 0)) != 1 or str(data.get("source", "")) != "ui_theme.py":
		load_error = "Invalid ui_theme contract schema/source"
		return false
	if not data.get("config") is Dictionary or not data.get("palette") is Dictionary:
		load_error = "Invalid ui_theme contract config/palette"
		return false
	cfg = data.config
	palette = data.palette
	defaults = data.get("defaults", {})
	if palette.size() != PALETTE_COUNT or data.get("icons", []).size() != ICON_COUNT:
		load_error = "Invalid ui_theme contract coverage"
		cfg = {}
		return false
	return true


static func valid() -> bool:
	return load_error.is_empty() and not cfg.is_empty()


static func value(path: String) -> Variant:
	if not ensure_loaded():
		return null
	var node: Variant = cfg
	for part: String in path.split("."):
		if not node is Dictionary or not node.has(part):
			return null
		node = node[part]
	return node


static func number(path: String) -> float:
	var raw: Variant = value(path)
	return float(raw) if raw != null else 0.0


static func integer(path: String) -> int:
	return int(number(path))


static func color(name: String, alpha := 1.0) -> Color:
	if not ensure_loaded():
		return Color.TRANSPARENT
	return rgb(palette.get(name, [0, 0, 0]), alpha)


static func rgb(row: Array, alpha := -1.0) -> Color:
	var a := alpha
	if a < 0.0:
		a = float(row[3]) / 255.0 if row.size() > 3 else 1.0
	return Color(float(row[0]) / 255.0, float(row[1]) / 255.0, float(row[2]) / 255.0, a)


static func set_quality(level: String) -> void:
	quality_level = level


static func set_quality_override(enabled: Variant) -> void:
	quality_override = enabled


static func cheap_alpha() -> bool:
	if quality_override != null:
		return bool(quality_override)
	# RenderQuality.cheap_alpha is the inverse budget flag: true means the
	# device is slow. ui_theme.cheap_alpha true means alpha effects are safe.
	return not bool(RenderQuality.preset(quality_level).get("cheap_alpha", true))


static func rect(x: float, y: float, w: float, h: float) -> Rect2i:
	return Rect2i(int(x), int(y), int(w), int(h))


static func rect_row(r: Rect2i) -> Array:
	return [r.position.x, r.position.y, r.size.x, r.size.y]


static func center(r: Rect2i) -> Vector2:
	return Vector2(r.position.x + floori(r.size.x / 2.0), r.position.y + floori(r.size.y / 2.0))


static func inflate(r: Rect2i, dx: int, dy: int) -> Rect2i:
	return Rect2i(
		r.position.x - floori(dx / 2.0),
		r.position.y - floori(dy / 2.0),
		r.size.x + dx,
		r.size.y + dy
	)


static func moved(r: Rect2i, dx: int, dy: int) -> Rect2i:
	return Rect2i(r.position + Vector2i(dx, dy), r.size)


static func dim(row: Array, factor: float) -> Array:
	var result: Array = []
	for component: Variant in row:
		result.append(int(float(component) * factor))
	return result


static func lighten(row: Array, amount: int) -> Array:
	var result: Array = []
	for component: Variant in row:
		result.append(mini(255, int(component) + amount))
	return result
