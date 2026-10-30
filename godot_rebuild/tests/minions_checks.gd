extends RefCounted
## Whole `minions/` folder coverage, proven from the source inventory.
##
## `minions/` is two files (9.626 lines): the five body renderers merged into
## `_bundle.py` plus the shared `base_renderer` helpers and a 94-name shim.
## `tests/minions_source_oracle.py` imports the bundle against a **recording**
## pygame stub, so the real `draw_hp_bar`, `draw_slow_effect`,
## `draw_slash_effects`, `apply_hurt_flash` and `_minion_cache_key` run
## unmodified and their primitives are pinned in
## `tests/fixtures/minions_source.json`.
##
## This suite replays those primitives through `minion_overlay.gd`:
##
## * the HP bar: team background/border, the 0.6 and 0.3 fill thresholds,
##   `int(width * ratio)` truncation, and the cache guard;
## * the slow aura: `radius + 2` circle and three `timer * 0.1 + i * 2.1` sparks;
## * the slash arcs: seven points per arc, radius `dist + progress * 6`, alpha
##   fading from 220, at arbitrary angles rather than the 32 baked steps;
## * the hurt flash (`+90` clamped) and the ten-part cache key;
## * the 201-symbol classification, including the three helpers the source
##   defines but never calls (`draw_shadow`, `apply_hurt_flash`,
##   `calculate_animation_offsets`) and the two bar offsets each renderer asks
##   for when the sprite cache is off.

const FIXTURE := "res://tests/fixtures/minions_source.json"
const MANIFEST := "res://data/art/minions.json"
const FX_MANIFEST := "res://data/art/minion_combat_fx.json"
const SOURCE_LINES := 9626

const MinionOverlay = preload("res://scripts/ui/minion_overlay.gd")
const MinionArt = preload("res://scripts/ui/minion_art.gd")
const MinionAnim = preload("res://scripts/ui/minion_anim.gd")

const MODULE_ORDER := ["base_renderer", "goblin", "orc", "troll", "undead", "dark_rider"]
const MODULE_LINES := [302, 1897, 1798, 1905, 1850, 1746]
const METHOD_COUNTS := {"dark_rider": 34, "goblin": 37, "orc": 33, "troll": 36, "undead": 38}
const DEAD_HELPERS := ["apply_hurt_flash", "calculate_animation_offsets", "draw_shadow"]
const HP_PATHS := {
	"base_renderer": [6, 18], "goblin": [6, 18], "orc": [8, 18],
	"troll": [8, 18], "undead": [8, 18], "dark_rider": [12, 22],
}


func run(check: Callable) -> void:
	var source := _fixture()
	check.call(not source.is_empty(), "The minions/ inventory fixture parses")
	if source.is_empty():
		return
	_check_folder(check, source)
	_check_constants(check, source)
	_check_dead(check, source)
	_check_namespaces(check, source)
	_check_dispatch(check, source)
	_check_hp_bar(check, source)
	_check_slow(check, source)
	_check_slash(check, source)
	_check_effects(check, source)
	_check_keys(check, source)
	_check_art(check)
	_check_classification(check, source)


func _fixture() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	return parsed if parsed is Dictionary else {}


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


func _check_folder(check: Callable, source: Dictionary) -> void:
	var folder: Dictionary = source.get("folder", {})
	var files: Dictionary = folder.get("files", {})
	check.call(int(folder.get("count", 0)) == 2 and int(folder.get("lines", 0)) == SOURCE_LINES,
		"minions/ holds two files and %d lines" % SOURCE_LINES)
	check.call(int(files.get("_bundle.py", 0)) == 9531,
		"_bundle.py is the 9.531-line merged bundle")
	var modules: Array = source.get("modules", [])
	var names: Array = []
	var lines: Array = []
	var total := 0
	for entry in modules:
		var row: Dictionary = entry
		names.append(row.get("module", ""))
		lines.append(int(row.get("lines", 0)))
		total += int(row.get("lines", 0))
	var header := int(modules[0].get("start", 0)) - 1 if modules.size() > 0 else 0
	check.call(names == MODULE_ORDER,
		"the bundle keeps the six modules in source order: %s" % str(names))
	check.call(lines == MODULE_LINES and header + total == 9531,
		"the six ranges tile the bundle after its %d-line header: %d lines"
		% [header, total])


func _check_constants(check: Callable, source: Dictionary) -> void:
	var constants: Dictionary = source.get("constants", {})
	check.call(constants.size() == 7, "base_renderer keeps seven module constants")
	check.call(_same(constants.get("OUTLINE", []), [24, 20, 25])
		and _same(MinionOverlay.OUTLINE, [24, 20, 25, 255]),
		"OUTLINE is (24, 20, 25) on both sides")
	check.call(_same(MinionOverlay.SHADOW, [0, 0, 0, 255]),
		"SHADOW stays pure black")
	check.call(int(constants.get("_CANVAS_W", 0)) == 120
		and int(constants.get("_CANVAS_H", 0)) == 120
		and MinionOverlay.CANVAS == Vector2i(120, 120),
		"the sprite canvas is 120 x 120")
	check.call(bool(constants.get("MINION_CACHE_ENABLED", false))
		and MinionOverlay.cache_enabled(),
		"the sprite cache is on by default")
	check.call(not bool(constants.get("_RENDERING_TO_CACHE", true))
		and not MinionOverlay.rendering_to_cache(),
		"the cache-render guard starts off")
	var overlay: Dictionary = source.get("overlay", {})
	check.call(MinionOverlay.POINT_SCALE == int(overlay.get("scale", 0)),
		"points are pinned in the same micro-pixel scale")


func _check_dead(check: Callable, source: Dictionary) -> void:
	var dead: Dictionary = source.get("dead", {})
	var flagged: Array = source.get("dead_helpers", [])
	check.call(flagged == DEAD_HELPERS,
		"three base_renderer helpers are never called: %s" % str(flagged))
	var unnamed: Array = []
	for name in ["draw_hp_bar", "draw_slow_effect", "draw_slash_effects",
			"_minion_cache_key", "cached_minion_draw"]:
		var rows: Dictionary = dead.get(name, {})
		if rows.get("inside", []).is_empty():
			unnamed.append(name)
	check.call(unnamed.is_empty(),
		"the five live helpers are called inside the bundle: %s" % str(unnamed))
	var leaked: Array = []
	for name in DEAD_HELPERS:
		var rows: Dictionary = dead.get(name, {})
		if not rows.get("inside", []).is_empty() or not rows.get("outside", []).is_empty():
			leaked.append(name)
	check.call(leaked.is_empty(),
		"the dead helpers have no call site anywhere: %s" % str(leaked))


func _check_namespaces(check: Callable, source: Dictionary) -> void:
	var counts: Dictionary = source.get("method_counts", {})
	check.call(_same(counts, METHOD_COUNTS),
		"the five namespaces keep 37/33/36/38/34 methods: %s" % str(counts))
	var total := 0
	for key in counts:
		total += int(counts[key])
	check.call(total == 178, "178 renderer methods live in the namespaces")
	var aliases: Dictionary = source.get("aliases", {})
	var aliased: Array = aliases.get("aliased", [])
	check.call(aliased == ["goblin", "orc", "troll", "undead", "dark_rider", "base_renderer"],
		"__init__.py re-registers five namespaces plus base_renderer: %s" % str(aliased))
	var reexports: Array = aliases.get("reexports", [])
	check.call(reexports == ["draw_dark_rider", "draw_goblin", "draw_orc",
			"draw_troll", "draw_undead"],
		"the shim re-exports the five draw functions: %s" % str(reexports))
	var registry: Array = aliases.get("registry", [])
	check.call(registry == ["goblin", "orc", "troll", "undead", "dark_rider"]
		and MinionOverlay.TYPES == registry,
		"MINION_RENDERERS keys are the five minion types")


func _check_dispatch(check: Callable, source: Dictionary) -> void:
	var dispatch: Dictionary = source.get("dispatch", {})
	check.call(bool(dispatch.get("cache_hook", false)),
		"render_minion tries the sprite-cache hook first")
	check.call(bool(dispatch.get("direct_call", false)),
		"render_minion falls back to the renderer itself")
	check.call(bool(dispatch.get("warns_on_unknown", false)),
		"an unknown minion type only warns and draws nothing")
	var types := MinionOverlay.TYPES
	var resolved: Array = []
	for type_id in types:
		if MinionOverlay.has_type(String(type_id)):
			resolved.append(type_id)
	check.call(resolved.size() == 5 and not MinionOverlay.has_type("dragon"),
		"the native registry resolves five types and rejects a sixth")
	var manifest: Dictionary = _json(MANIFEST)
	check.call(_same(manifest.get("types", []), types),
		"the baked atlas manifest lists the same five types")


func _check_hp_bar(check: Callable, source: Dictionary) -> void:
	var overlay: Dictionary = source.get("overlay", {})
	var cases: Array = overlay.get("hp_bar", [])
	var drifting: Array = []
	for raw in cases:
		var row: Dictionary = raw
		var case: Dictionary = row.get("case", {})
		var ops := MinionOverlay.hp_bar_ops(
			int(case.get("x", 0)), int(case.get("y", 0)), int(case.get("w", 0)),
			float(case.get("ratio", 0.0)), String(case.get("team", ""))
		)
		if not _same(ops, row.get("ops", [])):
			drifting.append(case)
	check.call(cases.size() == 8 and drifting.is_empty(),
		"all eight HP-bar replays match the source primitives: %s" % str(drifting))
	var full := MinionOverlay.hp_bar_ops(100, 50, 26, 1.0, "blue")
	check.call(full.size() == 3 and int(full[1]["rect"][2]) == 26,
		"a full bar fills the whole width")
	var empty := MinionOverlay.hp_bar_ops(100, 50, 26, 0.0, "red")
	check.call(empty.size() == 2, "an empty bar keeps only background and border")
	var clamped := MinionOverlay.hp_bar_ops(100, 50, 26, 1.8, "blue")
	check.call(_same(clamped, full), "an over-full ratio clamps to one")
	var guarded: Array = overlay.get("cache_guarded", [])
	MinionOverlay.set_rendering_to_cache(true)
	var hidden := MinionOverlay.hp_bar_ops(100, 50, 26, 0.5, "blue")
	MinionOverlay.set_rendering_to_cache(false)
	check.call(guarded.is_empty() and hidden.is_empty(),
		"the HP bar disappears while a sprite is being cached")
	var paths: Dictionary = source.get("hp_bar_paths", {})
	check.call(_same(paths, HP_PATHS),
		"each renderer keeps its own bar offsets: %s" % str(paths))


func _check_slow(check: Callable, source: Dictionary) -> void:
	var overlay: Dictionary = source.get("overlay", {})
	var cases: Array = overlay.get("slow_aura", [])
	var drifting: Array = []
	for raw in cases:
		var row: Dictionary = raw
		var case: Dictionary = row.get("case", {})
		var ops := MinionOverlay.slow_aura_ops(
			int(case.get("x", 0)), int(case.get("y", 0)),
			int(case.get("radius", 0)), int(case.get("timer", 0))
		)
		if not _same(ops, row.get("ops", [])):
			drifting.append(case)
	check.call(cases.size() == 4 and drifting.is_empty(),
		"all four slow-aura replays match the source primitives: %s" % str(drifting))
	var aura := MinionOverlay.slow_aura_ops(100, 200, 14, 0)
	check.call(aura.size() == 4 and int(aura[0]["radius"]) == 16,
		"the aura is one radius+2 circle plus three sparks")
	MinionOverlay.set_rendering_to_cache(true)
	var guarded := MinionOverlay.slow_aura_ops(100, 200, 14, 0)
	MinionOverlay.set_rendering_to_cache(false)
	check.call(guarded.size() == 4,
		"the aura is NOT cache-guarded, exactly like the source")


func _check_slash(check: Callable, source: Dictionary) -> void:
	var overlay: Dictionary = source.get("overlay", {})
	var cases: Array = overlay.get("slash", [])
	var drifting: Array = []
	var shapes: Array = []
	for raw in cases:
		var row: Dictionary = raw
		var effects: Array = row.get("effects", [])
		var ops := MinionOverlay.slash_ops(100, 200, effects)
		shapes.append(ops.size())
		if not _same(ops, row.get("ops", [])):
			drifting.append(row.get("name", "?"))
	check.call(cases.size() == 7 and drifting.is_empty(),
		"all seven slash replays match, arbitrary angles included: %s" % str(drifting))
	check.call(shapes == [0, 2, 2, 2, 0, 0, 4],
		"an arc is two lines, expired and empty arcs draw nothing: %s" % str(shapes))
	var fresh := MinionOverlay.slash_ops(100, 200, [
		{"life": 12, "max_life": 12, "angle": 0.0, "distance": 18},
	])
	check.call(fresh.size() == 2 and int(fresh[0]["points"][0].size()) == 2
		and int(fresh[0]["color"][3]) == 220 and int(fresh[1]["color"][3]) == 220,
		"a fresh arc is white 3 px plus cream 1 px at alpha 220")
	var faded := MinionOverlay.slash_ops(100, 200, [
		{"life": 6, "max_life": 12, "angle": 0.0, "distance": 18},
	])
	check.call(int(faded[0]["color"][3]) == 110, "half a life fades the arc to 110")
	var composed := MinionOverlay.overlay_ops(100, 200, 14, 0.5, "blue", [
		{"life": 6, "max_life": 12, "angle": 1.0, "distance": 20},
	])
	var expected: Array = MinionOverlay.slash_ops(100, 200, [
		{"life": 6, "max_life": 12, "angle": 1.0, "distance": 20},
	])
	expected.append_array(MinionOverlay.hp_bar_ops(100, 200 - 14 - 18, 14 * 2 + 6, 0.5, "blue"))
	check.call(_same(composed, expected),
		"the overlay tail is slash arcs then the +6/18 HP bar")


func _check_effects(check: Callable, source: Dictionary) -> void:
	var overlay: Dictionary = source.get("overlay", {})
	var hurt: Array = overlay.get("hurt_flash", [])
	var drifting: Array = []
	for raw in hurt:
		var row: Dictionary = raw
		var case: Dictionary = row.get("case", {})
		var color := MinionOverlay.hurt_color(case.get("color", []), int(case.get("timer", 0)))
		if not _same(color, row.get("color", [])):
			drifting.append(case)
	check.call(hurt.size() == 4 and drifting.is_empty(),
		"the +90 hurt flash matches on all four replays: %s" % str(drifting))
	var offsets: Array = overlay.get("offsets", [])
	check.call(offsets.size() == 5,
		"the dead bob/sway helper is still recorded as source evidence")
	var minion := MinionArt.manifest()
	check.call(int(minion.get("states", {}).get("walk", 0)) == MinionAnim.WALK_POSES
		and int(minion.get("states", {}).get("idle", 0)) == MinionAnim.IDLE_POSES
		and int(minion.get("attack_anim_max", 0)) == MinionAnim.ATTACK_ANIM_MAX,
		"the atlas pose counts match the source animation clocks")


func _check_keys(check: Callable, source: Dictionary) -> void:
	var overlay: Dictionary = source.get("overlay", {})
	var cases: Array = overlay.get("cache_keys", [])
	var drifting: Array = []
	for raw in cases:
		var row: Dictionary = raw
		var case: Dictionary = row.get("case", {})
		if not _same(MinionOverlay.cache_key(case), row.get("key", [])):
			drifting.append(case)
	check.call(cases.size() == 5 and drifting.is_empty(),
		"all five cache keys match the ten-part source tuple: %s" % str(drifting))
	var attack := MinionOverlay.cache_key({"minion_type": "orc", "team": "red",
		"nexus_level": 3, "attack_anim_timer": 7, "is_moving": true,
		"walk_cycle": 0.25, "anim_time": 12, "direction": -1})
	check.call(_same(attack[3], ["atk", 3]) and int(attack[4]) == -1,
		"attack keys use timer >> 1 and keep the facing")
	var moving := MinionOverlay.cache_key({"minion_type": "goblin", "team": "blue",
		"nexus_level": 1, "is_moving": true, "walk_cycle": 1.75})
	check.call(_same(moving[3], ["walk", 3]), "walk keys use int(2 * cycle) % 8")
	var idle := MinionOverlay.cache_key({"minion_type": "goblin", "team": "blue",
		"nexus_level": 1, "anim_time": 137})
	check.call(_same(idle[3], ["idle", 2]), "idle keys use int(0.05 * t) % 4")
	check.call(_same(MinionAnim.pose_key(7, true, 1.75, 137), "atk3"),
		"minion_anim keeps the same pose precedence")


func _check_art(check: Callable) -> void:
	var manifest: Dictionary = _json(MANIFEST)
	var atlases: Dictionary = manifest.get("atlases", {})
	check.call(atlases.size() == 50 and MinionArt.atlases().size() == 50,
		"fifty body atlases cover 5 types x 2 teams x 5 levels")
	check.call(_same(manifest.get("teams", []), ["blue", "red"])
		and _same(manifest.get("levels", []), [1, 2, 3, 4, 5]),
		"the atlas grid is two teams over five nexus levels")
	var missing: Array = []
	for type_id in manifest.get("types", []):
		for team in manifest.get("teams", []):
			for level in manifest.get("levels", []):
				var name := MinionArt.atlas_name(String(type_id),
					MinionArt.BLUE if String(team) == "blue" else 1, int(level))
				if not atlases.has(name):
					missing.append(name)
	check.call(missing.is_empty(),
		"every (type, team, level) resolves to an atlas: %s" % str(missing))
	var fx: Dictionary = _json(FX_MANIFEST)
	var fx_cases: Array = fx.get("key_cases", [])
	check.call(atlases.size() == 50 and fx_cases.size() == 75
		and int(fx.get("angle_steps", 0)) == 32
		and int(fx.get("slash_life", 0)) == 12,
		"slash arcs stay baked over 75 cases and 32 angle steps")


func _check_classification(check: Callable, source: Dictionary) -> void:
	var entries: Dictionary = source.get("classification", {})
	check.call(int(source.get("symbol_count", 0)) == 201 and entries.size() == 201,
		"all 201 symbols of the folder carry a classification")
	var kinds: Dictionary = source.get("classification_kinds", {})
	check.call(_same(kinds, {"bake": 184, "dead": 3, "delegated": 1,
			"meta": 1, "native": 12}),
		"the kind histogram is 184/12/3/1/1: %s" % str(kinds))
	var delegated := 0
	var dead_rows: Array = []
	for name in entries:
		var entry: Dictionary = entries[name]
		if String(entry.get("kind", "")) == "delegated":
			delegated += 1
		if String(entry.get("kind", "")) == "dead":
			dead_rows.append(name)
	check.call(delegated == 1 and dead_rows.size() == 3,
		"one delegated helper and three dead ones: %s" % str(dead_rows))
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
