extends RefCounted
## Whole `towers/` folder coverage, proven from the source inventory.
##
## `towers/` is two files (7.368 lines): the four tower renderers merged into
## `_bundle.py`, the shared `base_renderer` block and a 94-name shim.
## `tests/towers_source_oracle.py` imports the bundle against a stub pygame, so
## the real `get_*_position` / `get_*_top_y` helpers run unmodified and their
## integer output is pinned in `tests/fixtures/towers_source.json`.
##
## This suite replays that geometry through `tower_render_catalog.gd`:
##
## * 192 spawn points (four types, levels 0-7, both facings, two origins, cannon
##   recoil 0/3/7) and 64 HP-bar anchors, compared exactly;
## * the `max(1, min(6, level))` clamp, and the `y - 26` HP-bar fallback
##   `_entity.py` uses for a type without a helper;
## * the four palettes and four `LEVEL_CONFIGS` tables the bake reads;
## * the 14 symbols the source defines but never reaches - ten `base_renderer`
##   helpers (each namespace has its own private `_draw_torch`, `_draw_shield`,
##   `_draw_shadow`, `_get_palette`, ...), the superseded `_draw_cannon` and the
##   ice cluster trio replaced by `_draw_cluster_tier*`;
## * the in-match bindings: `TowerFxLayout.BOW_HEIGHTS`, `SiegeBattle.CANNON_MUZZLE`,
##   `ICE_CRYSTAL`, `MAGE_CRYSTAL` and the `bow_platform_height` in
##   `data/structures/archer_level_*.tres` must all agree with the catalog.

const FIXTURE := "res://tests/fixtures/towers_source.json"
const CATALOG := "res://data/towers/render_catalog.json"
const STRUCTURES := "res://data/art/structures.json"
const STRUCTURE_ART_DIR := "res://assets/art/structures/"
const STRUCTURE_DATA_DIR := "res://data/structures/"
const SOURCE_LINES := 7368
const BUNDLE_LINES := 7274
const SHIM_LINES := 94
const HEADER_LINES := 29

const MODULE_ORDER := ["base_renderer", "archer_tower", "cannon_tower", "ice_tower", "mage_tower"]
const MODULE_LINES := [379, 1786, 1771, 1709, 1600]
const METHOD_COUNTS := {"archer": 37, "cannon": 27, "ice": 34, "mage": 31}
const DEAD_HELPERS := [
	"base:draw_aura", "base:draw_ground_shadow", "base:draw_metal_plate",
	"base:draw_muzzle_flash", "base:draw_rivet", "base:draw_shield_emblem",
	"base:draw_sparks", "base:draw_stone_block_pattern", "base:draw_torch",
	"base:get_team_palette", "cannon:_draw_cannon", "ice:_draw_crystal_group",
	"ice:_draw_crystal_spike_detailed", "ice:_draw_floating_shards",
]
const TOWER_H := {
	"archer": [38, 42, 46, 52, 56, 62],
	"cannon": [38, 42, 46, 52, 56, 62],
	"ice": [40, 44, 48, 54, 58, 64],
	"mage": [45, 48, 52, 56, 60, 66],
}
const ARCHER_TIERS := ["basic", "ranger", "marksman", "elite", "elite_twin", "legendary"]
const CANNON_TIERS := ["basic", "basic", "bronze", "iron", "twin", "legendary"]
const CRYSTAL_TIERS := ["small", "small", "medium", "medium", "twin", "legendary"]
const PALETTE_SIZES := {"archer": 44, "cannon": 51, "ice": 39, "mage": 47}
## `data/art/structures.json::tower_top_y` - `get_<type>_top_y(0, 0, level)`.
const TOP_OFFSETS := {
	"archer": {"1": -28, "2": -31, "3": -33, "4": -40, "5": -43, "6": -50},
	"cannon": {"2": -31, "3": -34, "4": -39, "5": -41, "6": -50},
	"ice": {"2": -35, "3": -42, "4": -47, "5": -47, "6": -61},
	"mage": {"2": -42, "3": -48, "4": -51, "5": -52, "6": -63},
}

const TowerRenderCatalog = preload("res://scripts/ui/tower_render_catalog.gd")
const StructureArt = preload("res://scripts/ui/structure_art.gd")
const TowerFxLayout = preload("res://scripts/ui/tower_fx_layout.gd")
const SiegeBattle = preload("res://scripts/combat/siege_battle.gd")


func run(check: Callable) -> void:
	var source := _json(FIXTURE)
	check.call(not source.is_empty(), "The towers/ inventory fixture parses")
	if source.is_empty():
		return
	_check_folder(check, source)
	_check_constants(check, source)
	_check_dead(check, source)
	_check_namespaces(check, source)
	_check_palettes(check)
	_check_level_configs(check)
	_check_positions(check, source)
	_check_top_y(check, source)
	_check_clamp(check)
	_check_dispatch(check, source)
	_check_art(check)
	_check_match_bindings(check)
	_check_classification(check, source)


func _json(path: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


func _sorted(value: Variant) -> Variant:
	if value is Dictionary:
		var source: Dictionary = value
		var keys: Array = source.keys()
		keys.sort()
		var ordered := {}
		for key in keys:
			ordered[key] = _sorted(source[key])
		return ordered
	if value is Array:
		var listed: Array = []
		for item in value:
			listed.append(_sorted(item))
		return listed
	return value


func _same(left: Variant, right: Variant) -> bool:
	return JSON.stringify(_sorted(left)) == JSON.stringify(_sorted(right))


## JSON numbers arrive as floats; the source and the .gd constants are ints.
func _ints(value: Variant) -> Variant:
	if value is Dictionary:
		var table: Dictionary = value
		var copy := {}
		for key in table:
			copy[key] = _ints(table[key])
		return copy
	if value is Array:
		var listed: Array = []
		for item in value:
			listed.append(_ints(item))
		return listed
	if value is float or value is int:
		return int(value)
	return value


func _check_folder(check: Callable, source: Dictionary) -> void:
	var folder: Dictionary = source.get("folder", {})
	var files: Dictionary = folder.get("files", {})
	check.call(int(folder.get("count", 0)) == 2 and int(folder.get("lines", 0)) == SOURCE_LINES,
		"towers/ holds two files and %d lines" % SOURCE_LINES)
	check.call(int(files.get("_bundle.py", 0)) == BUNDLE_LINES,
		"_bundle.py is the 7.274-line merged bundle")
	check.call(int(files.get("__init__.py", 0)) == SHIM_LINES,
		"__init__.py is the 94-line alias shim")
	var modules: Array = source.get("modules", [])
	var names: Array = []
	var lines: Array = []
	var contiguous := true
	var previous_end := HEADER_LINES
	for module in modules:
		names.append(String(module.get("module", "")))
		lines.append(int(module.get("lines", 0)))
		contiguous = contiguous and int(module.get("start", -1)) == previous_end + 1
		previous_end = int(module.get("end", -1))
	check.call(names == MODULE_ORDER, "the bundle keeps its five module sections: %s" % str(names))
	check.call(lines == MODULE_LINES, "each section keeps its line count: %s" % str(lines))
	check.call(contiguous and previous_end == BUNDLE_LINES,
		"the sections tile the bundle with a %d-line header" % HEADER_LINES)


func _check_constants(check: Callable, source: Dictionary) -> void:
	var expected := {
		"OUTLINE": [30, 25, 35], "FIRE_ORANGE": [255, 150, 40],
		"FIRE_YELLOW": [255, 220, 100], "FIRE_PURPLE": [200, 40, 100],
		"FIRE_PINK": [255, 100, 200],
	}
	check.call(_same(_ints(source.get("constants", {})), expected),
		"the five base_renderer colours are the source ones")
	var catalog: Dictionary = _json(CATALOG)
	check.call(_same(_ints(catalog.get("constants", {})), expected),
		"the data catalog ships the same colour constants")
	check.call(is_equal_approx(TowerRenderCatalog.SCALE, 0.7)
			and TowerRenderCatalog.CANVAS_W == 140 and TowerRenderCatalog.CANVAS_H == 165,
		"every helper draws on a 140x165 canvas scaled by 0.7")
	check.call(TowerRenderCatalog.GROUND_CY == 153
			and TowerRenderCatalog.FINAL_Y_OFFSET == -94,
		"ground at cy 153 and the -94 final offset of the source")
	check.call(is_equal_approx(TowerRenderCatalog.BOW_SIDE, 7.0)
			and is_equal_approx(TowerRenderCatalog.CANNON_BARREL_OFFSET, -7.0),
		"bow sits 7px off centre, cannon barrel 7px above its cy")


func _check_dead(check: Callable, source: Dictionary) -> void:
	var dead_rows: Dictionary = source.get("dead", {})
	var flagged: Array = source.get("dead_helpers", [])
	check.call(flagged == DEAD_HELPERS, "the 14 unreachable symbols are the expected ones")
	var still_reachable: Array = []
	for name in flagged:
		var row: Dictionary = dead_rows.get(name, {})
		if bool(row.get("reachable", true)):
			still_reachable.append(name)
	check.call(still_reachable.is_empty(), "no flagged symbol is reachable: %s" % str(still_reachable))
	var base_rows := 0
	for name in dead_rows:
		if String(name).begins_with("base:"):
			base_rows += 1
	check.call(base_rows == 10, "the whole base_renderer helper block is dead: %d rows" % base_rows)
	var bow: Dictionary = dead_rows.get("archer:get_archer_bow_position", {})
	check.call(bool(bow.get("reachable", false)) and int(bow.get("outside", 0)) == 3,
		"the archer bow helper is the live bullet-spawn entry point")
	var rivet: Dictionary = dead_rows.get("base:draw_rivet", {})
	check.call(int(rivet.get("inside", 0)) == 1 and not bool(rivet.get("reachable", true)),
		"draw_rivet is only called by the dead draw_metal_plate")
	var v2: Dictionary = dead_rows.get("cannon:_draw_cannon", {})
	check.call(not bool(v2.get("reachable", true)),
		"the first cannon body renderer is superseded by _draw_cannon_v2")


func _check_namespaces(check: Callable, source: Dictionary) -> void:
	var counts: Dictionary = _ints(source.get("method_counts", {}))
	check.call(_same(counts, METHOD_COUNTS), "namespace method counts: %s" % str(counts))
	var classes: Dictionary = source.get("classes", {})
	var listed: Array = []
	for namespace in classes:
		listed.append(String(namespace))
	listed.sort()
	check.call(listed == ["_NS_archer_tower", "_NS_cannon_tower", "_NS_ice_tower", "_NS_mage_tower"],
		"four wrapped namespaces, four renderers: %s" % str(listed))
	var missing: Array = []
	for tower_type in TowerRenderCatalog.TYPES:
		var methods: Array = classes.get("_NS_%s_tower" % tower_type, [])
		for entry in ["draw_%s" % tower_type, "get_%s_top_y" % tower_type, "_get_palette"]:
			if not methods.has(entry):
				missing.append("%s:%s" % [tower_type, entry])
	check.call(missing.is_empty(), "every namespace keeps its entry points: %s" % str(missing))
	var dispatch: Dictionary = source.get("dispatch", {})
	check.call(dispatch.get("registry", []) == TowerRenderCatalog.TYPES,
		"TOWER_RENDERERS order matches the catalog types")
	var spawn: Dictionary = dispatch.get("spawn_helpers", {})
	check.call(String(spawn.get("archer", "")) == "get_archer_bow_position"
			and String(spawn.get("cannon", "")) == "get_cannon_muzzle_position"
			and String(spawn.get("ice", "")) == "get_ice_crystal_position"
			and String(spawn.get("mage", "")) == "get_mage_crystal_position",
		"the four spawn helpers are the ones _entity.py imports")


func _check_palettes(check: Callable) -> void:
	var catalog: Dictionary = _json(CATALOG)
	var fixture: Dictionary = _json(FIXTURE)
	check.call(_same(catalog.get("palettes", {}), fixture.get("palettes", {})),
		"the shipped palettes are the sampled source tables")
	var wrong: Array = []
	for tower_type in TowerRenderCatalog.TYPES:
		var blue: Dictionary = TowerRenderCatalog.palette(tower_type, "blue")
		var red: Dictionary = TowerRenderCatalog.palette(tower_type, "red")
		if blue.size() != int(PALETTE_SIZES[tower_type]) or red.size() != blue.size():
			wrong.append("%s:%d/%d" % [tower_type, blue.size(), red.size()])
	check.call(wrong.is_empty(), "both teams share one palette size: %s" % str(wrong))
	var blue_fire: Array = _ints(TowerRenderCatalog.palette("archer", "blue").get("fire_dark", []))
	var red_fire: Array = _ints(TowerRenderCatalog.palette("archer", "red").get("fire_hot", []))
	check.call(blue_fire == [180, 45, 15], "the archer keeps its blue-team torch colours")
	check.call(red_fire == [255, 220, 255], "the red team swaps the torch for the pink flame")
	check.call(_same(_ints(TowerRenderCatalog.palette("cannon", "green")),
			_ints(TowerRenderCatalog.palette("cannon", "red"))),
		"`if team == \"blue\"` means every other team name falls through to red")


func _check_level_configs(check: Callable) -> void:
	var catalog: Dictionary = _json(CATALOG)
	var fixture: Dictionary = _json(FIXTURE)
	check.call(_same(catalog.get("level_configs", {}), fixture.get("level_configs", {})),
		"the shipped level configs are the source tables")
	var rows := 0
	var wrong: Array = []
	for tower_type in TowerRenderCatalog.TYPES:
		for level in range(1, 7):
			rows += 1
			var height := TowerRenderCatalog.tower_h(tower_type, level)
			if height != int(TOWER_H[tower_type][level - 1]):
				wrong.append("%s:%d=%d" % [tower_type, level, height])
	check.call(rows == 24 and wrong.is_empty(), "24 tower heights as in the source: %s" % str(wrong))
	var tiers: Array = []
	for level in range(1, 7):
		tiers.append(String(TowerRenderCatalog.config("cannon", level).get("cannon_tier", "")))
	check.call(tiers == CANNON_TIERS, "cannon tiers per level: %s" % str(tiers))
	var ice_tiers: Array = []
	var mage_tiers: Array = []
	for level in range(1, 7):
		ice_tiers.append(String(TowerRenderCatalog.config("ice", level).get("crystal_tier", "")))
		mage_tiers.append(String(TowerRenderCatalog.config("mage", level).get("crystal_tier", "")))
	check.call(ice_tiers == CRYSTAL_TIERS and mage_tiers == CRYSTAL_TIERS,
		"ice and mage share the crystal tiers: %s / %s" % [str(ice_tiers), str(mage_tiers)])
	var archer_tiers: Array = []
	for level in range(1, 7):
		archer_tiers.append(String(TowerRenderCatalog.config("archer", level).get("archer_tier", "")))
	check.call(archer_tiers == ARCHER_TIERS, "archer tiers per level: %s" % str(archer_tiers))
	check.call(_same(TowerRenderCatalog.config("cannon", 0), TowerRenderCatalog.config("cannon", 1))
			and _same(TowerRenderCatalog.config("cannon", 9), TowerRenderCatalog.config("cannon", 6)),
		"out-of-range levels clamp to 1 and 6")


func _check_positions(check: Callable, source: Dictionary) -> void:
	var cases: Array = source.get("anchors", {}).get("positions", [])
	var wrong: Array = []
	for case in cases:
		var tower_type := String(case.get("type", ""))
		var expected: Array = _ints(case.get("out", []))
		var got := TowerRenderCatalog.position(tower_type, float(case.get("x", 0.0)),
			float(case.get("y", 0.0)), int(case.get("level", 0)),
			int(case.get("face", 1)), int(case.get("recoil", 0)))
		if got != Vector2i(int(expected[0]), int(expected[1])):
			wrong.append("%s L%s f%s r%s -> %s vs %s" % [tower_type, case.get("level", 0),
				case.get("face", 1), case.get("recoil", 0), str(got), str(expected)])
	check.call(cases.size() == 192, "192 spawn cases pinned from the source: %d" % cases.size())
	check.call(wrong.is_empty(),
		"every bullet spawn point matches the source: %s" % str(wrong.slice(0, 4)))
	var bow_left := TowerRenderCatalog.archer_position(400.0, 300.0, 1, -1)
	var bow_right := TowerRenderCatalog.archer_position(400.0, 300.0, 1, 1)
	check.call(bow_left.x < 400 and bow_right.x > 400,
		"the bow flips side with the facing: %s / %s" % [str(bow_left), str(bow_right)])
	var recoiled := TowerRenderCatalog.cannon_position(400.0, 300.0, 6, 1, 7)
	var resting := TowerRenderCatalog.cannon_position(400.0, 300.0, 6, 1, 0)
	check.call(recoiled.x > resting.x,
		"the source's `recoil` shifts the canvas centre forward: %s vs %s"
			% [str(recoiled), str(resting)])


func _check_top_y(check: Callable, source: Dictionary) -> void:
	var cases: Array = source.get("anchors", {}).get("top_y", [])
	var wrong: Array = []
	for case in cases:
		var got := TowerRenderCatalog.top_y(String(case.get("type", "")),
			int(case.get("level", 0)), float(case.get("y", 0.0)))
		if got != int(case.get("out", 0)):
			wrong.append("%s L%s y%s -> %d vs %s" % [case.get("type", ""), case.get("level", 0),
				case.get("y", 0), got, str(case.get("out", 0))])
	check.call(cases.size() == 64, "64 HP-bar anchors pinned from the source: %d" % cases.size())
	check.call(wrong.is_empty(),
		"every HP-bar anchor matches the source: %s" % str(wrong.slice(0, 4)))
	var rows: Dictionary = _json(STRUCTURES).get("tower_top_y", {})
	check.call(_same(_ints(rows), TOP_OFFSETS),
		"the baked manifest pins the same offsets per level")
	var mismatched: Array = []
	for tower_type in TOP_OFFSETS:
		var levels: Dictionary = TOP_OFFSETS[tower_type]
		for level in levels:
			if TowerRenderCatalog.top_y(tower_type, int(level), 0.0) != int(levels[level]):
				mismatched.append("%s L%s" % [tower_type, level])
	check.call(mismatched.is_empty(),
		"catalog and manifest agree on the baked levels: %s" % str(mismatched))


func _check_clamp(check: Callable) -> void:
	var wrong: Array = []
	for tower_type in TowerRenderCatalog.TYPES:
		for face in [1, -1]:
			var low := TowerRenderCatalog.position(tower_type, 400.0, 300.0, 1, face, 0)
			var high := TowerRenderCatalog.position(tower_type, 400.0, 300.0, 6, face, 0)
			if TowerRenderCatalog.position(tower_type, 400.0, 300.0, 0, face, 0) != low:
				wrong.append("%s L0" % tower_type)
			if TowerRenderCatalog.position(tower_type, 400.0, 300.0, -3, face, 0) != low:
				wrong.append("%s L-3" % tower_type)
			if TowerRenderCatalog.position(tower_type, 400.0, 300.0, 9, face, 0) != high:
				wrong.append("%s L9" % tower_type)
	check.call(wrong.is_empty(), "levels clamp to 1..6 everywhere: %s" % str(wrong))
	check.call(TowerRenderCatalog.top_y("ice", 0, 0.0) == TowerRenderCatalog.top_y("ice", 1, 0.0)
			and TowerRenderCatalog.top_y("ice", 9, 0.0) == TowerRenderCatalog.top_y("ice", 6, 0.0),
		"the HP-bar anchor clamps the same way")
	check.call(not TowerRenderCatalog.has_type("dragon")
			and TowerRenderCatalog.position("dragon", 417.0, 285.0, 3) == Vector2i(417, 285)
			and TowerRenderCatalog.top_y("dragon", 3, 300.0) == 274,
		"an unknown type has no helper: origin spawn, y - 26 HP bar")
	check.call(TowerRenderCatalog.tower_h("cannon", 99) == 62
			and TowerRenderCatalog.tower_h("archer", -4) == 38,
		"tower_h clamps before it reads LEVEL_CONFIGS")


func _check_dispatch(check: Callable, source: Dictionary) -> void:
	var dispatch: Dictionary = source.get("dispatch", {})
	check.call(bool(dispatch.get("warns_on_unknown", false))
			and bool(dispatch.get("direct_call", false)),
		"render_tower warns on an unknown type and calls the renderer directly")
	check.call(dispatch.get("cache_hooks", []).size() == 4
			and int(dispatch.get("cache_hook_count", 0)) == 4,
		"all four body renderers go through the sprite cache")
	var entry: Dictionary = source.get("entry", {})
	var bow_entry: Dictionary = entry.get("get_archer_bow_position", {})
	check.call(bow_entry.get("calls", []).size() >= 3,
		"_entity.py imports the bow helper and uses it on every archer shot")
	var render_entry: Dictionary = entry.get("render_tower", {})
	check.call(render_entry.get("imports", []).has("_entity.py:1346"),
		"Tower.draw is the only render_tower caller")
	check.call(TowerRenderCatalog.atlas_key("archer", "blue", 1) == "archer_blue_1"
			and TowerRenderCatalog.atlas_key("mage", "red", 9) == "mage_red_6",
		"the manifest key is <type>_<team>_<clamped level>")


func _check_art(check: Callable) -> void:
	var manifest: Dictionary = _json(STRUCTURES)
	var towers: Dictionary = manifest.get("towers", {})
	var per_type := {}
	for key in towers:
		var name := String(key)
		var tower_type := name.split("_")[0]
		per_type[tower_type] = int(per_type.get(tower_type, 0)) + 1
	check.call(towers.size() == 42
			and _same(per_type, {"archer": 12, "cannon": 10, "ice": 10, "mage": 10}),
		"42 baked tower sheets, archer the only level 1: %s" % str(per_type))
	check.call(_same(manifest.get("tower_levels", {}), {"archer": [1, 2, 3, 4, 5, 6],
			"cannon": [2, 3, 4, 5, 6], "ice": [2, 3, 4, 5, 6], "mage": [2, 3, 4, 5, 6]}),
		"the bake covers exactly the upgrade paths the game can reach")
	var missing: Array = []
	for key in ["tower_archer_blue_1", "tower_cannon_red_6", "tower_ice_blue_3", "tower_mage_red_5"]:
		if not ResourceLoader.exists(STRUCTURE_ART_DIR + key + ".png"):
			missing.append(key)
	check.call(missing.is_empty(), "the baked sheets are on disk: %s" % str(missing))
	var wrong: Array = []
	for tower_type in TOP_OFFSETS:
		for level in TOP_OFFSETS[tower_type]:
			var baked := StructureArt.tower_top_y(tower_type, int(level))
			if baked != TowerRenderCatalog.top_y(tower_type, int(level), 0.0):
				wrong.append("%s L%s %d" % [tower_type, level, baked])
	check.call(wrong.is_empty(),
		"structure_art reads the same HP-bar offsets the catalog computes: %s" % str(wrong))


func _check_match_bindings(check: Callable) -> void:
	check.call(TowerFxLayout.BOW_HEIGHTS == TOWER_H["archer"],
		"the live archer muzzle glow uses the same platform heights")
	var rows: Array = SiegeBattle.CANNON_MUZZLE
	var wrong: Array = []
	for level in range(1, 7):
		var tier := String(TowerRenderCatalog.config("cannon", level).get("cannon_tier", "basic"))
		var forward := int(float(int(TowerRenderCatalog.BARREL_LENGTH[tier])) * 0.85)
		var expected := [int(TOWER_H["cannon"][level - 1]), forward]
		var actual: Array = _ints(rows[level - 1])
		if not _same(actual, expected):
			wrong.append("L%d %s vs %s" % [level, str(actual), str(expected)])
	check.call(wrong.is_empty(), "siege muzzle rows match the catalog: %s" % str(wrong))
	check.call(_same(_ints(SiegeBattle.ICE_CRYSTAL), TOWER_H["ice"])
			and _same(_ints(SiegeBattle.MAGE_CRYSTAL), TOWER_H["mage"]),
		"siege crystal rows match the ice/mage tower heights")
	var heights: Array = []
	for level in range(2, 7):
		var definition: Resource = load(STRUCTURE_DATA_DIR + "archer_level_%d.tres" % level)
		heights.append(int(definition.get("bow_platform_height")))
	check.call(heights == TOWER_H["archer"].slice(1),
		"the archer .tres platform heights agree with LEVEL_CONFIGS: %s" % str(heights))


func _check_classification(check: Callable, source: Dictionary) -> void:
	var entries: Dictionary = source.get("classification", {})
	check.call(int(source.get("symbol_count", 0)) == 163 and entries.size() == 163,
		"all 163 symbols of the folder carry a classification")
	var kinds: Dictionary = _ints(source.get("classification_kinds", {}))
	check.call(_same(kinds, {"bake": 125, "data": 13, "dead": 14, "meta": 1, "native": 10}),
		"the kind histogram is 125/13/14/10/1: %s" % str(kinds))
	var native_rows: Array = []
	for name in entries:
		var entry: Dictionary = entries[name]
		if String(entry.get("kind", "")) == "native":
			native_rows.append(String(name))
	check.call(native_rows.size() == 10,
		"ten native symbols: four spawn helpers, four top helpers, registry, dispatcher")
	var cache := {}
	var missing_file: Array = []
	var missing_token: Array = []
	var source_only: Array = []
	for name in entries:
		var entry: Dictionary = entries[name]
		var target := String(entry.get("target", ""))
		if not target.begins_with("godot_rebuild/"):
			source_only.append(name)
			continue
		var path := "res://" + target.trim_prefix("godot_rebuild/")
		if not cache.has(path):
			cache[path] = FileAccess.get_file_as_string(path)
			if String(cache[path]).is_empty():
				missing_file.append(target)
		var body: String = cache[path]
		if not missing_file.has(target) and not body.contains(String(entry.get("token", ""))):
			missing_token.append(name)
	check.call(source_only == ["shim:_install_aliases"],
		"only the shim entry lives outside the Godot project: %s" % str(source_only))
	check.call(missing_file.is_empty(),
		"every classification target exists in the Godot tree: %s" % str(missing_file))
	check.call(missing_token.is_empty(),
		"every classification token is present in its target: %s" % str(missing_token))
