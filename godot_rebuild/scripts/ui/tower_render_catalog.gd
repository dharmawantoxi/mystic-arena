extends RefCounted
## Layer 9cd: the live half of the Pygame `towers/` folder.
##
## The four tower bodies are native as baked sheets (layer 9bl, 42 sheets, 8 frames
## each: 2 facings x 4 shoot-flash steps). What `towers/_bundle.py` still decided at
## run time, and what this module ports, is geometry and data:
##
## * `_get_palette(team)` per tower - the colour table the bake reads, kept
##   inspectable so a repaint can be diffed against the source;
## * `LEVEL_CONFIGS[1..6]` per tower - `tower_h` and the `*_tier` labels that every
##   anchor formula below consumes;
## * `get_archer_bow_position`, `get_cannon_muzzle_position(recoil)`,
##   `get_ice_crystal_position`, `get_mage_crystal_position` - bullet spawn points;
## * `get_<type>_top_y` - where the HP bar sits above the tower origin;
## * `TOWER_RENDERERS` / `render_tower` - the dispatch chain, here a type lookup.
##
## All four source helpers share one canvas: 140x165 drawn at `SCALE = 0.7`, ground
## at `GROUND_CY = 153`, and a final `-int(165 * 0.7) + int(30 * 0.7) = -94` offset.
## Every value is `int()`-truncated by the source, so the results stay integers.
## `tower_y` is added *before* truncation, exactly like the source, which matters
## for fractional origins.

const CATALOG := "res://data/towers/render_catalog.json"
## `TOWER_RENDERERS` order, and the only four types the source dispatches.
const TYPES := ["archer", "cannon", "ice", "mage"]
const BLUE := "blue"
## `SCALE` in every `get_*_position` / `get_*_top_y`.
const SCALE := 0.7
const CANVAS_W := 140
const CANVAS_H := 165
## `canvas_cy = ch - 12`.
const GROUND_CY := 153
## `final_y_offset = -int(ch * SCALE) + int(30 * SCALE)`.
const FINAL_Y_OFFSET := -94
## `77 - cw // 2` and `63 - cw // 2`: the bow sits 7px either side of centre.
const BOW_SIDE := 7.0
## `-4` for `_render_cannon` plus `barrel_y = cy - 3` in the barrel itself.
const CANNON_BARREL_OFFSET := -7.0
## `get_cannon_muzzle_position`: barrel length per `cannon_tier`.
const BARREL_LENGTH := {"basic": 20, "bronze": 22, "twin": 18, "iron": 24, "legendary": 26}
## `get_cannon_top_y`: barrel height per `cannon_tier`.
const BARREL_HEIGHT := {"basic": 10, "bronze": 11, "twin": 11, "iron": 12, "legendary": 13}
## `get_ice_top_y`: crystal height per `crystal_tier`.
const ICE_CRYSTAL_HEIGHT := {"small": 16, "medium": 22, "twin": 18, "legendary": 32}
## `get_mage_top_y`: crystal height per `crystal_tier`.
const MAGE_CRYSTAL_HEIGHT := {"small": 22, "medium": 26, "twin": 24, "legendary": 34}
static var _catalog: Dictionary = {}


static func catalog() -> Dictionary:
	if _catalog.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
		if parsed is Dictionary:
			_catalog = parsed
	return _catalog


static func palettes() -> Dictionary:
	var listed: Dictionary = catalog().get("palettes", {})
	return listed


## `_NS_<type>_tower._get_palette(team)`: anything but "blue" is the red table.
static func palette(tower_type: String, team: String) -> Dictionary:
	var rows: Dictionary = palettes().get(tower_type, {})
	var table: Dictionary = rows.get(BLUE if team == BLUE else "red", {})
	return table


static func level_configs(tower_type: String) -> Dictionary:
	var listed: Dictionary = catalog().get("level_configs", {})
	var rows: Dictionary = listed.get(tower_type, {})
	return rows


## `lvl = max(1, min(6, level))` in every helper.
static func clamp_level(level: int) -> int:
	return clampi(level, 1, 6)


static func config(tower_type: String, level: int) -> Dictionary:
	var rows: Dictionary = level_configs(tower_type)
	var row: Dictionary = rows.get(str(clamp_level(level)), {})
	return row


## `LEVEL_CONFIGS[lvl]['tower_h']`; also `bow_platform_height` in `data/structures`.
static func tower_h(tower_type: String, level: int) -> int:
	return int(config(tower_type, level).get("tower_h", 0))


## `canvas_cy - config['tower_h'] - 5`: the tower top in canvas space.
static func tower_top(tower_type: String, level: int) -> int:
	return GROUND_CY - tower_h(tower_type, level) - 5


static func has_type(tower_type: String) -> bool:
	return TYPES.has(tower_type)


## `get_archer_bow_position`: `bow_x_canvas = 77` facing right, `63` facing left.
static func archer_position(x: float, y: float, level: int, face: int = 1) -> Vector2i:
	var archer_y := float(tower_top("archer", level) - 5)
	var bow_x := float(CANVAS_W / 2) + (BOW_SIDE if face > 0 else -BOW_SIDE)
	return _world(x, y, bow_x, archer_y - 1.0)


## `get_cannon_muzzle_position`: recoil pushes the barrel back by `int(recoil / SCALE)`.
static func cannon_position(x: float, y: float, level: int, face: int = 1,
		recoil: int = 0) -> Vector2i:
	var tier := String(config("cannon", level).get("cannon_tier", "basic"))
	var barrel := int(BARREL_LENGTH.get(tier, 20))
	var muzzle_x := float(CANVAS_W / 2) + float(int(float(recoil) / SCALE))
	muzzle_x += float(int(float(barrel) * 0.85) * face)
	var muzzle_y := float(tower_top("cannon", level) - 2) + CANNON_BARREL_OFFSET
	return _world(x, y, muzzle_x, muzzle_y)


## `get_ice_crystal_position`: dead centre, 5px above the tower top. `face` unused.
static func ice_position(x: float, y: float, level: int) -> Vector2i:
	return _world(x, y, float(CANVAS_W / 2), float(tower_top("ice", level) - 5))


## `get_mage_crystal_position`: dead centre, 10px above the tower top. `face` unused.
static func mage_position(x: float, y: float, level: int) -> Vector2i:
	return _world(x, y, float(CANVAS_W / 2), float(tower_top("mage", level) - 10))


## Bullet spawn point for any tower type; `{}`-style fallback is the origin itself.
static func position(tower_type: String, x: float, y: float, level: int,
		face: int = 1, recoil: int = 0) -> Vector2i:
	match tower_type:
		"archer":
			return archer_position(x, y, level, face)
		"cannon":
			return cannon_position(x, y, level, face, recoil)
		"ice":
			return ice_position(x, y, level)
		"mage":
			return mage_position(x, y, level)
	return Vector2i(int(x), int(y))


## `get_<type>_top_y`: world Y of the tower's highest pixel, for the HP bar.
static func top_y(tower_type: String, level: int, tower_y: float = 0.0) -> int:
	var lvl := clamp_level(level)
	var canvas_y := float(tower_top(tower_type, lvl))
	match tower_type:
		"archer":
			# `archer_y = tower_top - 5`, head at `-int(11 * 1.0)`.
			canvas_y = canvas_y - 5.0 - 11.0
			if lvl == 6:
				canvas_y -= 8.0
			elif lvl >= 4:
				canvas_y -= 4.0
		"cannon":
			var cannon_tier := String(config("cannon", lvl).get("cannon_tier", "basic"))
			var barrel := int(BARREL_HEIGHT.get(cannon_tier, 10))
			canvas_y = canvas_y - 2.0 - 4.0 - 3.0 - float(barrel / 2) - 3.0
			if cannon_tier == "legendary":
				canvas_y -= 6.0
		"ice":
			var ice_tier := String(config("ice", lvl).get("crystal_tier", "small"))
			canvas_y = canvas_y - 5.0 - float(ICE_CRYSTAL_HEIGHT.get(ice_tier, 16))
		"mage":
			var mage_tier := String(config("mage", lvl).get("crystal_tier", "small"))
			canvas_y = canvas_y - 5.0 - float(MAGE_CRYSTAL_HEIGHT.get(mage_tier, 22))
		_:
			# `_entity.py` falls back to `y - 26` for a type without a helper.
			return int(tower_y - 26.0)
	return int(tower_y + float(FINAL_Y_OFFSET) + canvas_y * SCALE)


## Manifest key the baked sheet is stored under (`data/art/structures.json`).
static func atlas_key(tower_type: String, team: String, level: int) -> String:
	return "%s_%s_%d" % [tower_type, BLUE if team == BLUE else "red", clamp_level(level)]


static func _world(x: float, y: float, canvas_x: float, canvas_y: float) -> Vector2i:
	var world_x := x + (canvas_x - float(CANVAS_W) / 2.0) * SCALE
	var world_y := y + float(FINAL_Y_OFFSET) + canvas_y * SCALE
	return Vector2i(int(world_x), int(world_y))
