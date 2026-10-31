extends RefCounted
## Layer 9cg: whole `_entity.py` coverage — the five merged entity modules.
##
## `_entity.py` is 6.536 lines: `tower.py`, `castle.py`, `hero.py`, `minion.py` and
## `ai_player.py` merged into one file plus a short damage-credit/damage-school prelude.
## The rebuild has carried these classes for many layers (`structure_state.gd`,
## `hero_state.gd`, `minion_battle.gd`, `projectile_state.gd`, `siege_battle.gd`,
## `ai_policy.gd`, the baked atlases), so this layer proves the coverage instead of
## re-porting it:
##
## * the inventory (five modules, seven classes, 125 `def`s, 35 module-level functions,
##   ten module caches) matches the source, and every one of the 179 symbols carries a
##   classification whose target file exists and really contains its token;
## * `tests/entity_source_oracle.py` imports the REAL module (stub `pygame`, `_core`
##   settings namespace, `_system`, `_render`) and executes `Tower`, `Castle`, `Minion`
##   and `Bullet`, so the tower/nexus/minion tables and the sale quotes below are the
##   pygame numbers. This suite compares every row against the shipped `.tres` catalogs,
##   so a hand-edited definition cannot drift from `_entity.py` unnoticed;
## * three source quirks get their own check: the level-1 sell refund (the source
##   `Tower.sell_value()` is 0, the `_core` sell path substitutes 50), the nexus HP
##   upgrade that keeps the ratio and adds a flat 500, and the shield capacity that
##   stays at the spawn value after a free upgrade (only a purchased shield follows HP);
## * eight symbols are dead (four never called, the disabled castle ground, the level-6
##   castle art above `MAX_NEXUS_LEVEL`) and four `Hero` properties are getter/setter
##   pairs, which is why 125 `def`s become 121 classified methods.
##
## Sync: python3 godot_rebuild/tests/entity_source_oracle.py --write

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const NexusUpgrades = preload("res://scripts/match/nexus_upgrades.gd")
const Projectile = preload("res://scripts/combat/projectile_state.gd")
const Siege = preload("res://scripts/combat/siege_battle.gd")
const Damage = preload("res://scripts/combat/damage_rules.gd")
const FIXTURE := "res://tests/fixtures/entity_source.json"

const ARCHER := [
	preload("res://data/structures/archer_level_1.tres"),
	preload("res://data/structures/archer_level_2.tres"),
	preload("res://data/structures/archer_level_3.tres"),
	preload("res://data/structures/archer_level_4.tres"),
	preload("res://data/structures/archer_level_5.tres"),
	preload("res://data/structures/archer_level_6.tres"),
]
const CANNON := [
	preload("res://data/structures/cannon_level_2.tres"),
	preload("res://data/structures/cannon_level_3.tres"),
	preload("res://data/structures/cannon_level_4.tres"),
	preload("res://data/structures/cannon_level_5.tres"),
	preload("res://data/structures/cannon_level_6.tres"),
]
const ICE := [
	preload("res://data/structures/ice_level_2.tres"),
	preload("res://data/structures/ice_level_3.tres"),
	preload("res://data/structures/ice_level_4.tres"),
	preload("res://data/structures/ice_level_5.tres"),
	preload("res://data/structures/ice_level_6.tres"),
]
const MAGE := [
	preload("res://data/structures/mage_level_2.tres"),
	preload("res://data/structures/mage_level_3.tres"),
	preload("res://data/structures/mage_level_4.tres"),
	preload("res://data/structures/mage_level_5.tres"),
	preload("res://data/structures/mage_level_6.tres"),
]
const NEXUS := [
	preload("res://data/structures/nexus_level_1.tres"),
	preload("res://data/structures/nexus_level_2.tres"),
	preload("res://data/structures/nexus_level_3.tres"),
	preload("res://data/structures/nexus_level_4.tres"),
	preload("res://data/structures/nexus_level_5.tres"),
]
const MINIONS := {
	"goblin": preload("res://data/minions/goblin.tres"),
	"orc": preload("res://data/minions/orc.tres"),
	"troll": preload("res://data/minions/troll.tres"),
	"undead": preload("res://data/minions/undead.tres"),
	"dark_rider": preload("res://data/minions/dark_rider.tres"),
}

const TOTALS := {
	"lines": 6536,
	"sections": 6,
	"classes": 7,
	"methods": 125,
	"top_functions": 35,
	"assigns": 10,
}
const SECTION_LINES := {
	"prelude": [1, 18],
	"tower": [19, 1385],
	"castle": [1386, 3207],
	"hero": [3208, 5388],
	"minion": [5389, 5991],
	"ai_player": [5992, 6536],
}
const KIND_HISTOGRAM := {"bake": 52, "dead": 8, "folded": 4, "ported": 115}
const SOURCE_ONLY_KINDS := ["dead", "deviation", "meta"]
const DEAD_HELPERS := [
	"class:Castle.get_minion_composition",
	"class:Hero.count_enemies_in_range",
	"class:Hero.end_damage_scope",
	"class:Hero.get_skill_cooldowns",
	"class:Minion._get_lane_y",
	"top:_draw_castle_ground@1970",
	"top:_draw_center_royal_tower@2996",
	"top:_render_castle_lvl6@2967",
]
const PROPERTY_PAIRS := {
	"class:Hero.skill_damage": [3240, 3261],
	"class:Hero.direction": [5303, 5308],
	"class:Hero.timer": [5312, 5317],
	"class:Hero.attack_cooldown": [5333, 5339],
}


func run(check: Callable) -> void:
	var data: Dictionary = _json(FIXTURE)
	check.call(not data.is_empty(), "_entity fixture parses")
	if data.is_empty():
		return
	_check_inventory(check, data)
	_check_classification(check, data)
	_check_evidence(check, data)
	_check_towers(check, data)
	_check_nexus(check, data)
	_check_minions(check, data)
	_check_quirks(check, data)
	_check_school(check, data)
	_check_projectiles(check, data)


## The file really is the five-module bundle this layer claims.
func _check_inventory(check: Callable, data: Dictionary) -> void:
	var file: Dictionary = data["file"]
	for key in TOTALS:
		check.call(
			int(file.get(key, -1)) == TOTALS[key],
			"_entity.py %s is %s (got %s)" % [key, TOTALS[key], str(file.get(key))]
		)
	check.call(String(file.get("file", "")) == "_entity.py", "the oracle reads the source file")
	var sections: Array = data["sections"]
	check.call(sections.size() == SECTION_LINES.size(), "all five modules plus the prelude map")
	for row in sections:
		var name := String(row["name"])
		var want: Array = SECTION_LINES[name]
		check.call(
			int(row["start"]) == want[0] and int(row["end"]) == want[1],
			"%s spans lines %s-%s" % [name, str(want[0]), str(want[1])]
		)
	var duplicates: Dictionary = data["duplicates"]
	for name in PROPERTY_PAIRS:
		check.call(
			(duplicates.get(name, {}) as Dictionary).get("lines", []) == PROPERTY_PAIRS[name],
			"%s is defined twice (getter/setter)" % name
		)


## Every symbol is classified, and every kind that points at Godot lands on a real token.
func _check_classification(check: Callable, data: Dictionary) -> void:
	var symbols: Dictionary = data["symbols"]
	check.call(int(symbols["count"]) == 179, "179 symbols are classified")
	for kind in KIND_HISTOGRAM:
		check.call(
			int((symbols["kinds"] as Dictionary).get(kind, -1)) == KIND_HISTOGRAM[kind],
			"kind %s covers %d symbols (got %s)" % [
				kind, KIND_HISTOGRAM[kind],
				str((symbols["kinds"] as Dictionary).get(kind))
			]
		)
	var entries: Dictionary = data["classification"]
	check.call(entries.size() == 179, "the classification names every symbol once")
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


## The dead-helpers evidence, including the level-6 castle art.
func _check_evidence(check: Callable, data: Dictionary) -> void:
	var dead: Array = data["dead_helpers"]
	check.call(dead == DEAD_HELPERS, "eight symbols are dead: %s" % str(dead))
	check.call(
		NexusUpgrades.LEVELS.size() == 5,
		"MAX_NEXUS_LEVEL is 5, so `_render_castle_lvl6` never runs"
	)
	var levels: Dictionary = data["towers"]["levels"]
	var bake := 0
	for row in levels:
		bake += 1 if String(row["path"]) == "archer" else 0
	check.call(bake == 6, "the archer table spans six levels")
	var kinds: Dictionary = data["symbols"]["kinds"]
	check.call(
		int(kinds["bake"]) == 52,
		"52 symbols are baked art (castle, tower body, bullets, heroes, minions)"
	)


## 21 executed tower rows against `data/structures/<path>_level_<n>.tres`.
func _check_towers(check: Callable, data: Dictionary) -> void:
	var tables := {"archer": ARCHER, "cannon": CANNON, "ice": ICE, "mage": MAGE}
	var rows: Array = data["towers"]["levels"]
	check.call(rows.size() == 21, "21 tower rows were executed")
	var broken: Array = []
	for row in rows:
		var path := String(row["path"])
		var level := int(row["level"])
		var table: Array = tables[path]
		var offset := 1 if path == "archer" else 2
		var definition = table[level - offset]
		if not _matches(definition, row):
			broken.append("%s lv%d" % [path, level])
	check.call(broken.is_empty(), "every tower row matches its shipped .tres: %s" % str(broken))
	var switch: Dictionary = data["towers"]["path_switch_cost"]
	var world := _rich_world()
	world.build_tower(Prototype.BLUE, 0)
	var built = world.get_unit(world.slots[0].structure_id)
	for path in ["archer", "cannon", "ice", "mage"]:
		if built == null or int(world.upgrade_price(built.id, path)) != int(switch[path]):
			broken.append("switch %s" % path)
	check.call(
		int(switch["archer"]) == 175 and int(switch["cannon"]) == 175,
		"a level-1 tower pays the 175 target-path price to switch"
	)


func _matches(definition, row: Dictionary) -> bool:
	return (
		definition.max_hp == int(row["max_hp"])
		and definition.damage == int(row["damage"])
		and is_equal_approx(definition.attack_range_px, float(row["range"]))
		and definition.attack_cooldown_ticks == int(row["cd"])
		and is_equal_approx(definition.armor, float(row["armor"]))
		and is_equal_approx(definition.magic_resist, float(row["magic_resist"]))
		and is_equal_approx(definition.shield_capacity, float(row["shield_max"]))
		and definition.sale_refund == int(row["transaction_refund"])
	)


## Five executed nexus rows against `nexus_level_<n>.tres`.
func _check_nexus(check: Callable, data: Dictionary) -> void:
	var rows: Array = data["nexus"]["levels"]
	check.call(rows.size() == 5, "five nexus rows were executed")
	var broken: Array = []
	for row in rows:
		var definition = NEXUS[int(row["level"]) - 1]
		if not (
			definition.max_hp == int(row["max_hp"])
			and definition.damage == int(row["damage"])
			and is_equal_approx(definition.attack_range_px, float(row["range"]))
			and definition.attack_cooldown_ticks == int(row["cd"])
			and is_equal_approx(definition.shield_capacity, float(row["max_hp"]))
		):
			broken.append("nexus %d" % int(row["level"]))
	check.call(broken.is_empty(), "every nexus row matches its shipped .tres: %s" % str(broken))
	check.call(
		int(rows[0]["shield_cost"]) == 850 and int(rows[0]["upgrade_cost"]) == 500,
		"castle shield costs 850 and the first nexus upgrade 500"
	)
	var world := _rich_world()
	var nexus = world.nexuses[Prototype.BLUE]
	check.call(
		nexus.sale_value() == 0,
		"the nexus refunds nothing (source `sale_refund = 0`)"
	)


## 25 executed minion rows (five types, five nexus tiers) against the catalogs.
func _check_minions(check: Callable, data: Dictionary) -> void:
	var rows: Array = data["minions"]
	check.call(rows.size() == 25, "25 minion rows were executed")
	var scales := NexusUpgrades.MINION_SCALES
	var broken: Array = []
	for row in rows:
		var base = MINIONS[String(row["type"])]
		var tier := int(row["nexus"])
		var definition = base
		if tier > 1:
			var world := _rich_world()
			definition = world.scaled_minion_definition(base, tier)
		if definition == null:
			broken.append("%s/%d (null)" % [String(row["type"]), tier])
			continue
		if not (
			definition.max_hp == int(row["max_hp"])
			and definition.damage == int(row["damage"])
			and is_equal_approx(definition.speed_px_per_tick, float(row["speed"]))
			and definition.attack_cooldown_ticks == int(row["cd"])
			and definition.gold_reward == int(row["gold"])
			and is_equal_approx(definition.regen_per_tick, float(row["regen"]))
			and is_equal_approx(definition.armor, float(row["armor"]))
			and is_equal_approx(definition.magic_resist, float(row["magic_resist"]))
		):
			broken.append("%s/%d" % [String(row["type"]), tier])
	check.call(broken.is_empty(), "every scaled minion row matches: %s" % str(broken))
	check.call(
		is_equal_approx(scales[0], 1.0) and is_equal_approx(scales[4], 2.0),
		"the nexus tiers scale minions 1.0 -> 2.0"
	)


## The three source quirks this layer pins from the executed side.
func _check_quirks(check: Callable, data: Dictionary) -> void:
	var towers: Dictionary = data["towers"]
	check.call(
		int(towers["sell_value_without_shield"]) == int(towers["sell_value_with_shield"]) - 425,
		"an active regen shield adds exactly 425 to the sale quote"
	)
	check.call(
		int(towers["red_sell_value"]) == 0,
		"a red (AI) tower is worth nothing, the player only sells its own"
	)
	check.call(
		int(towers["transaction_refund_with_shield"]) == 950,
		"the executed level-4 shield quote is 950"
	)
	# Quirk 1: `Tower.sell_value()` is 0 at level 1 and `_core` substitutes 50.
	var world := _rich_world()
	check.call(world.build_tower(Prototype.BLUE, 0), "a level-1 tower builds")
	var tower = world.get_unit(world.slots[0].structure_id)
	check.call(
		tower != null and tower.settings().level == 1 and tower.sale_value() == 50,
		"level-1 sale refunds the source's substituted 50, not 0"
	)
	var before: int = world.economy.gold[Prototype.BLUE]
	check.call(world.sell_tower(Prototype.BLUE, tower.id), "the level-1 tower sells")
	check.call(
		world.economy.gold[Prototype.BLUE] == before + 50 and world.economy.is_balanced(),
		"the sell transaction pays exactly 50 and keeps the ledger balanced"
	)
	# Quirk 2: nexus HP keeps the ratio and gains a flat 500.
	var damaged: Dictionary = data["nexus"]["damaged_upgrade"]
	var other := _rich_world()
	var nexus = other.nexuses[Prototype.BLUE]
	nexus.hp = int(nexus.settings().max_hp) * 4 / 10
	var target = NexusUpgrades.LEVELS[1]
	other._apply_nexus_stats(nexus, target)
	check.call(
		int(damaged["max_hp"]) == target.max_hp
		and int(damaged["after"]) == int(nexus.hp)
		and int(nexus.hp) == mini(
			target.max_hp, int(target.max_hp * 0.4) + (target.max_hp - 4000) + 500
		),
		"the nexus upgrade keeps the HP ratio and adds the flat 500 margin"
	)
	# Quirk 3: an unpurchased shield keeps its spawn capacity through free upgrades.
	var third := _rich_world()
	var free_nexus = third.nexuses[Prototype.BLUE]
	for previous in range(3):
		third.upgrade_nexus(free_nexus.id, previous + 1)
	check.call(
		free_nexus.settings().level == 5
		and is_equal_approx(free_nexus.shield_max, 4000.0)
		and free_nexus.settings().shield_capacity == 15000.0,
		"a free nexus upgrade never grows the unpurchased shield (4000, not 15000)"
	)


## The damage-school matrix: structure shots stay school-free, hero shots carry one.
func _check_school(check: Callable, data: Dictionary) -> void:
	var resolution: Array = data["school"]["resolution"]
	check.call(resolution.size() == 7, "seven school cases were executed")
	check.call(
		(resolution[0] as Dictionary)["school"] == "physical"
			and (resolution[2] as Dictionary)["school"] == null,
		"explicit school wins but fire/crit resolve to no school"
	)
	check.call(
		(resolution[5] as Dictionary)["school"] == null,
		"the active-hero context never leaks onto structures"
	)
	var gate: Array = data["school"]["physical_gate"]
	var magic_gate := 0
	for row in gate:
		if row["damage_type"] == "projectile" and row["school"] == "magic":
			magic_gate = 1 if bool(row["physical"]) else 0
	check.call(magic_gate == 0, "a magic projectile is not a physical hit")
	var siege := Siege.new()
	check.call(
		siege._projectile_school(null, "physical") == "neutral",
		"tower bolts resolve to a school-free hit, like `Bullet._on_hit`"
	)
	check.call(
		Damage.resolve(100, 2.0, 0.0, "magic") == 100
			and Damage.resolve(100, 2.0, 0.0, "physical") < 100,
		"magic ignores armour while physical is mitigated"
	)


## Bullet defaults and the impact factors the executed rows pin.
func _check_projectiles(check: Callable, data: Dictionary) -> void:
	var shot := Projectile.new()
	check.call(
		is_equal_approx(shot.speed, 8.0) and is_equal_approx(shot.hit_radius, 4.0),
		"BULLET_SPEED 8 and BULLET_RADIUS 4 are the projectile defaults"
	)
	var bullets: Array = data["bullets"]
	check.call(bullets.size() == 4, "four bullet cases were executed")
	var cannon: Dictionary = bullets[1]
	var units: Dictionary = cannon["units"]
	var main_hit: Array = (units["target"] as Dictionary)["hits"]
	var splash_hit: Array = (units["near"] as Dictionary)["hits"]
	check.call(
		not main_hit.is_empty() and not splash_hit.is_empty()
			and int(main_hit[0]["amount"]) == 50 and int(splash_hit[0]["amount"]) == 30,
		"cannon splash is 60% of 50 = 30 and the main target takes 50"
	)
	var splash_debuffs: Array = (units["near"] as Dictionary)["debuffs"]
	check.call(
		not splash_debuffs.is_empty() and splash_debuffs[0]["kind"] == "burn",
		"cannon splash also applies the burn debuff"
	)
	check.call(
		int(((bullets[0] as Dictionary)["ticks_to_hit"] as int)) == 12,
		"a bullet 100 px away needs 12 ticks at speed 8"
	)
	var text := FileAccess.get_file_as_string("res://scripts/combat/siege_battle.gd")
	check.call(
		text.contains("int(float(shot.damage) * 0.6)"),
		"the live splash arm keeps the source 0.6 factor"
	)


func _rich_world() -> Prototype:
	var world := Prototype.new()
	world.economy.gold[0] = 20000
	world.economy.opening[0] = 20000
	world.setup_arena()
	return world


func _json(path: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}
