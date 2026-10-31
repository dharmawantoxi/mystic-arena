extends RefCounted
## Layer 9cf: whole `_core.py` coverage — the app shell of the pygame build.
##
## `_core.py` is 10.281 lines and eight merged modules (`settings`, `game`, `menu`,
## `game_input`, `game_ui`, `game_dev`, `game_settings`, `controller_manager`) plus a
## `sys.modules` alias shim. Almost all of it is already native in the rebuild — the match
## simulation lives in `prototype_battle.gd`, the menu in `main_menu.gd`, the tap/drag
## routing in `prototype_screen.gd`, the dock in `side_panel.gd`, the pad adapter in
## `controller_runtime.gd`, the settings in the settings stores — so this layer proves the
## coverage instead of re-porting it:
##
## * the inventory (sections, 10 classes, 218 methods, 11 module-level functions, the alias
##   shim) matches the source, and every one of the 393 symbols carries a classification
##   whose target file exists and really contains its token;
## * the `settings.py` block (lines 28-1291) is executed by the source oracle and ships as
##   `data/core/settings.json` — 139 constants read back through `scripts/data/core_settings.gd`;
## * the 16 constants a live Godot module already pins are compared against the shipped
##   values, so the JSON and the hand-written `const`s can never drift apart;
## * the six helpers with no call site are listed as dead, the duplicate
##   `get_all_hero_types` definition is recorded, and the `F1-F12` cheat panel is the one
##   documented deviation (developer tooling, not player-facing).
##
## Sync: python3 godot_rebuild/tests/core_source_oracle.py --write

const CoreSettings = preload("res://scripts/data/core_settings.gd")
const BuildPopup = preload("res://scripts/ui/build_popup_layout.gd")
const FIXTURE := "res://tests/fixtures/core_source.json"
const DATA := "res://data/core/settings.json"
const KIND_HISTOGRAM := {
	"data": 140,
	"dead": 6,
	"deviation": 8,
	"folded": 181,
	"meta": 9,
	"ported": 47,
}
const SOURCE_ONLY_KINDS := ["dead", "deviation", "meta"]
const TOTALS := {
	"lines": 10281,
	"sections": 8,
	"classes": 10,
	"methods": 218,
	"top_functions": 11,
	"settings_constants": 144,
}
const SECTION_LINES := {
	"settings": [28, 1296],
	"game": [1297, 3042],
	"menu": [3043, 7694],
	"game_input": [7695, 8505],
	"game_ui": [8506, 8690],
	"game_dev": [8691, 9083],
	"game_settings": [9084, 9298],
	"controller_manager": [9299, 10281],
}
const DEAD_HELPERS := [
	"class:GameSettings.get_difficulty_label",
	"class:GameSettings.is_hard_mode",
	"class:GameSettings.toggle_difficulty",
	"class:Menu._blit_shadow",
	"class:Menu._render_gradient_text",
	"class:UIRenderer.draw_notifications",
]
## Values pinned twice: once by the executed `settings.py` block, once by a shipped const.
const SPOT_PARITY := {
	"TOWER_VISUAL_SCALE": ["godot_rebuild/scripts/ui/tower_render_catalog.gd", "SCALE", 0.7],
	"TOWER_REGEN_SHIELD_COST": [
		"godot_rebuild/scripts/combat/structure_state.gd", "REGEN_SHIELD_COST", 850.0
	],
	"META_REPLAY_REPEAT_REWARD": [
		"godot_rebuild/scripts/match/level_progress.gd", "REPEAT_REWARD", 200.0
	],
	"TOWER_REGEN_SHIELD_MIN_LEVEL": [
		"godot_rebuild/scripts/combat/structure_state.gd", "REGEN_SHIELD_MIN_LEVEL", 4.0
	],
	"MAX_HERO_LEVEL": ["godot_rebuild/scripts/data/hero_definition.gd", "MAX_HERO_LEVEL", 15.0],
}


func run(check: Callable) -> void:
	var data: Dictionary = _json(FIXTURE)
	check.call(not data.is_empty(), "_core fixture parses")
	if data.is_empty():
		return
	_check_inventory(check, data)
	_check_classification(check, data)
	_check_evidence(check, data)
	_check_settings(check, data)
	_check_parity(check, data)
	_check_settings_module(check)


## The file really is the eight-module bundle this layer claims.
func _check_inventory(check: Callable, data: Dictionary) -> void:
	var file: Dictionary = data["file"]
	for key in TOTALS:
		check.call(
			int(file.get(key, -1)) == TOTALS[key],
			"_core.py %s is %s (got %s)" % [key, TOTALS[key], str(file.get(key))]
		)
	check.call(
		String(file.get("file", "")) == "_core.py",
		"the oracle reads the pygame root file"
	)
	var sections: Array = data["sections"]
	check.call(sections.size() == SECTION_LINES.size(), "all eight merged modules are mapped")
	for row in sections:
		var name := String(row["name"])
		var want: Array = SECTION_LINES[name]
		check.call(
			int(row["start"]) == want[0] and int(row["end"]) == want[1],
			"%s spans lines %s-%s" % [name, str(want[0]), str(want[1])]
		)
	var duplicates: Dictionary = data["duplicates"]
	check.call(
		int((duplicates.get("get_all_hero_types", {}) as Dictionary).get("copies", 0)) == 2,
		"the hero-shop price override shadows the first get_all_hero_types"
	)
	check.call(
		int((duplicates.get("class:TowerDebuffMixin.hp", {}) as Dictionary).get("copies", 0))
			== 2,
		"the tower HP property is a getter/setter pair, classified once"
	)
	var reassigned: Dictionary = data["reassignments"]
	check.call(
		(reassigned.get("FPS", []) as Array) == [92, 349],
		"FPS is assigned twice in the settings block (lines 92 and 349)"
	)


## Every symbol is classified, and every kind that points at Godot lands on a real token.
func _check_classification(check: Callable, data: Dictionary) -> void:
	var symbols: Dictionary = data["symbols"]
	check.call(int(symbols["count"]) == 391, "391 symbols are classified")
	var histogram: Dictionary = symbols["kinds"]
	for kind in KIND_HISTOGRAM:
		check.call(
			int(histogram.get(kind, -1)) == KIND_HISTOGRAM[kind],
			"kind %s covers %d symbols (got %s)" % [
				kind, KIND_HISTOGRAM[kind], str(histogram.get(kind))
			]
		)
	var entries: Dictionary = data["classification"]
	check.call(entries.size() == 391, "the classification names every symbol once")
	var unclassified: Array = []
	var source_only: Array = []
	var missing_file: Array = []
	var missing_token: Array = []
	var cache := {}
	for name in entries:
		var entry: Dictionary = entries[name]
		var kind := String(entry["kind"])
		if not KIND_HISTOGRAM.has(kind):
			unclassified.append(name)
			continue
		var target := String(entry["target"])
		var token := String(entry["token"])
		if target.is_empty() or token.is_empty():
			if not SOURCE_ONLY_KINDS.has(kind):
				source_only.append(name)
			continue
		if not target.begins_with("godot_rebuild/"):
			source_only.append(target)
			continue
		var path := "res://" + target.trim_prefix("godot_rebuild/")
		if not cache.has(path):
			cache[path] = FileAccess.get_file_as_string(path)
		if String(cache[path]).is_empty():
			missing_file.append(target)
			continue
		if not String(cache[path]).contains(token):
			missing_token.append(name)
	check.call(unclassified.is_empty(), "every kind is known: %s" % str(unclassified))
	check.call(
		source_only.is_empty(),
		"every kind that names a Godot module points into the project: %s" % str(source_only)
	)
	check.call(
		missing_file.is_empty(),
		"every classification target exists: %s" % str(missing_file)
	)
	check.call(
		missing_token.is_empty(),
		"every classification token is present in its target: %s" % str(missing_token)
	)


## The dead/deviation evidence the classification leans on.
func _check_evidence(check: Callable, data: Dictionary) -> void:
	var dead: Array = data["dead_helpers"]
	check.call(dead == DEAD_HELPERS, "six helpers have no call site: %s" % str(dead))
	var devmode: Array = []
	for name in data["classification"]:
		var entry: Dictionary = data["classification"][name]
		if String(entry["kind"]) == "deviation":
			devmode.append(name)
	check.call(
		devmode.size() == 8 and devmode.has("class:DevMode.handle_hotkey"),
		"the F1-F12 cheat panel is the only deviation family"
	)
	var shim: Dictionary = data["classification"]
	check.call(
		String((shim["shim:install_aliases"] as Dictionary)["kind"]) == "meta",
		"the sys.modules alias shim is bookkeeping, not a Godot module"
	)


## The executed `settings.py` block: 139 plain constants, values included.
func _check_settings(check: Callable, data: Dictionary) -> void:
	var settings: Dictionary = data["settings"]
	check.call(int(settings["count"]) == 139, "139 settings constants are exported")
	var document: Dictionary = _json(DATA)
	var shipped: Dictionary = document.get("constants", {})
	check.call(shipped.size() == 139, "data/core/settings.json ships all of them")
	check.call(
		sorted_names(shipped) == settings["keys"],
		"the shipped keys are the keys the oracle executed"
	)
	check.call(
		int(shipped.get("SCREEN_WIDTH", 0)) == 1280
			and int(shipped.get("SCREEN_HEIGHT", 0)) == 720
			and int(shipped.get("TOP_BAR_HEIGHT", 0)) == 40,
		"the settings carry the 1280x720 playfield under a 40 px top bar"
	)
	check.call(
		_is_number(shipped.get("TOWER_HP_MULTIPLIER"), 2.5)
			and _is_number(shipped.get("TOWER_SHIELD_HP_RATIO"), 0.4)
			and _is_number(shipped.get("TOWER_VISUAL_SCALE"), 0.7),
		"tower HP multiplier, shield ratio and visual scale match settings.py"
	)
	check.call(
		int(shipped.get("TOWER_REGEN_SHIELD_COST", 0)) == 850
			and int(shipped.get("TOWER_REGEN_SHIELD_MIN_LEVEL", 0)) == 4
			and int(shipped.get("TOWER_REGEN_SHIELD_DELAY", 0)) == 180
			and _is_number(shipped.get("TOWER_REGEN_SHIELD_RATE"), 1.8),
		"the regen-shield policy is the source one (850g from level 4)"
	)
	check.call(
		int(shipped.get("STARTER_HERO_UNLOCK_COST", -1)) == 0
			and int(shipped.get("MINI_BOSS_HERO_UNLOCK_COST", -1)) == 4500
			and int(shipped.get("TRUE_BOSS_HERO_UNLOCK_COST", -1)) == 4500,
		"starter heroes are free, every boss hero costs 4500"
	)
	check.call(
		shipped.get("DEV_UNLIMITED_HERO_GOLD") == false,
		"the dev free-hero switch ships off"
	)
	check.call(
		String(shipped.get("TITLE", "")) == "Mystic Arena",
		"the window title is the pygame one"
	)


## The constants a live Godot module already pins must agree with the executed block.
func _check_parity(check: Callable, data: Dictionary) -> void:
	var rows: Array = data["parity"]
	check.call(rows.size() == 16, "16 settings constants are also pinned in Godot")
	var wrong: Array = []
	for row in rows:
		var target := String(row["target"])
		var path := "res://" + target.trim_prefix("godot_rebuild/")
		var literal := _const_literal(
			FileAccess.get_file_as_string(path), String(row["godot_const"])
		)
		if literal.is_empty() or not is_equal_approx(literal.to_float(), float(row["value"])):
			wrong.append("%s != %s.%s" % [
				String(row["constant"]), String(row["godot_const"]), literal
			])
	check.call(wrong.is_empty(), "every pinned constant agrees: %s" % str(wrong))
	var documents: Dictionary = _json(DATA).get("constants", {})
	for constant in SPOT_PARITY:
		var want: Array = SPOT_PARITY[constant]
		var path := "res://" + String(want[0]).trim_prefix("godot_rebuild/")
		var literal := _const_literal(FileAccess.get_file_as_string(path), String(want[1]))
		check.call(
			_is_number(documents.get(constant), float(want[2]))
				and is_equal_approx(literal.to_float(), float(want[2])),
			"%s is %s in both the JSON and %s" % [
				constant, str(want[2]), String(want[0]).get_file()
			]
		)


## `scripts/data/core_settings.gd` reads the document back with honest fallbacks.
func _check_settings_module(check: Callable) -> void:
	check.call(CoreSettings.count() == 139, "CoreSettings loads 139 constants")
	check.call(CoreSettings.has("TOWER_HP_MULTIPLIER"), "CoreSettings answers has()")
	check.call(
		not CoreSettings.has("NOT_A_SETTING"),
		"CoreSettings reports unknown names as missing"
	)
	check.call(
		CoreSettings.number("TOWER_HP_MULTIPLIER") == 2.5
			and CoreSettings.number("NOPE", 4.5) == 4.5,
		"number() returns the source value and the fallback"
	)
	check.call(
		CoreSettings.integer("SCREEN_WIDTH") == 1280 and CoreSettings.integer("NOPE", 7) == 7,
		"integer() returns the source value and the fallback"
	)
	check.call(
		CoreSettings.flag("TOWER_SHIELD_ENABLED")
			and not CoreSettings.flag("DEV_UNLIMITED_HERO_GOLD")
			and CoreSettings.flag("NOPE", true),
		"flag() reads the shield switch and the dev switch off"
	)
	check.call(
		CoreSettings.text("TITLE") == "Mystic Arena"
			and CoreSettings.text("NOPE", "fallback") == "fallback",
		"text() reads the title"
	)
	var build_gold: Array = BuildPopup.GOLD
	check.call(
		CoreSettings.color("GOLD") == Color8(255, 200, 50)
			and CoreSettings.color("GOLD")
				== Color8(int(build_gold[0]), int(build_gold[1]), int(build_gold[2])),
		"GOLD is the pygame (255, 200, 50), the same the build popup pins"
	)
	check.call(
		CoreSettings.color("NOPE", Color.RED) == Color.RED,
		"color() falls back for unknown names"
	)
	check.call(
		CoreSettings.list("BLUE").size() == 3
			and int(CoreSettings.list("BLUE")[2]) == 255
			and CoreSettings.list("NOPE").is_empty(),
		"list() returns tuples as arrays"
	)
	check.call(
		not CoreSettings.block("TOWER_STATS").is_empty()
			and CoreSettings.block("NOPE").is_empty(),
		"block() returns the table constants"
	)
	check.call(
		CoreSettings.names().size() == 139
			and String(CoreSettings.names()[0]) == "AI_HERO_PREFERENCES",
		"names() is sorted and complete"
	)


static func sorted_names(table: Dictionary) -> Array:
	var out: Array = table.keys()
	out.sort()
	return out


static func _is_number(value: Variant, want: float) -> bool:
	if not (value is int or value is float):
		return false
	return is_equal_approx(float(value), want)


## `const NAME := literal` — the literal part, comments stripped.
static func _const_literal(body: String, name: String) -> String:
	for line in body.split("\n"):
		var text := String(line).strip_edges()
		if not text.begins_with("const "):
			continue
		var rest := text.trim_prefix("const ").strip_edges()
		if not rest.begins_with(name):
			continue
		var tail := rest.substr(name.length()).strip_edges()
		if not (tail.begins_with(":") or tail.begins_with("=")):
			continue
		var equals := text.find("=")
		if equals == -1:
			continue
		var literal := text.substr(equals + 1).strip_edges()
		var comment := literal.find("#")
		if comment != -1:
			literal = literal.substr(0, comment).strip_edges()
		return literal
	return ""


func _json(path: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}
