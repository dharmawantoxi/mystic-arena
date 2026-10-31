extends RefCounted
## Whole `bosses/` folder coverage, proven from the source inventory.
##
## `tests/fixtures/bosses_folder_source.json` is re-derived from the 61 Pygame
## files by `tests/bosses_folder_source_oracle.py`. This suite walks that map
## and asks the native project to account for every entry:
##
## * all 216 boss ids exist in `boss_stats.json` with the source class (162
##   mini / 54 true) and keep the source `hero_unlock.cost` on their hero
##   resource;
## * all 79 source smart-AI bosses have a dispatch arm in `boss_ai.gd`;
## * all 216 boss ids resolve to exactly one skill home through the same
##   resolver the match uses (`SourceSharedBossSkills.IDS`, else
##   `BossRecipeRegistry.handler(id, NATIVE_SKILLS)`) - none homeless, none in
##   two homes;
## * every baked body in `data/art/bosses.json` is one of those ids, with the
##   same class, and the manifest's smart list is the same 79.

const FIXTURE := "res://tests/fixtures/bosses_folder_source.json"
const STATS := "res://data/bosses/boss_stats.json"
const AI := "res://scripts/match/boss_ai.gd"
const ART := "res://data/art/bosses.json"
const SharedSkills = preload("res://scripts/combat/source_shared_boss_skills.gd")
const RecipeRegistry = preload("res://scripts/combat/boss_recipe_registry.gd")
const MinionBattle = preload("res://scripts/combat/minion_battle.gd")
const HeroRoster = preload("res://scripts/data/hero_roster.gd")


func run(check: Callable) -> void:
	var source := _fixture()
	check.call(not source.is_empty(), "The bosses/ inventory fixture parses")
	if source.is_empty():
		return
	_check_counts(check, source)
	_check_catalog(check, source)
	_check_smart_ai(check, source)
	_check_skill_homes(check, source)
	_check_art(check, source)


func _fixture() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	return parsed if parsed is Dictionary else {}


func _stats() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(STATS))
	var table: Dictionary = parsed if parsed is Dictionary else {}
	var rows: Dictionary = table.get("bosses", {})
	return rows


## The fixture's own numbers must add up before anything is compared to it.
func _check_counts(check: Callable, source: Dictionary) -> void:
	var counts: Dictionary = source.get("counts", {})
	var files: Dictionary = source.get("files", {})
	var index: Dictionary = source.get("index", {})
	var draws: Dictionary = source.get("draw_functions", {})
	var classes: Dictionary = source.get("boss_classes", {})
	var smart: Array = source.get("smart_ai", [])
	check.call(files.size() == 61, "The folder holds 61 Python files: %d" % files.size())
	check.call(int(counts.get("level_modules", 0)) == 54, "54 level draw modules")
	check.call(
		int(counts.get("structural", 0)) == 4, "4 structural modules: package, index, base, data"
	)
	check.call(int(counts.get("renderers", 0)) == 3, "3 procedural v4 renderers")
	check.call(int(counts.get("files", 0)) == files.size(), "The file count matches the file table")
	check.call(
		int(counts.get("index_entries", 0)) == index.size(),
		"The index count matches the index table"
	)
	check.call(
		int(counts.get("smart_ai", 0)) == smart.size(),
		"The smart-AI count matches the dispatch list"
	)
	var draw_total := 0
	var draw_seen := {}
	for module in draws:
		for draw in draws[module]:
			draw_total += 1
			draw_seen["%s.%s" % [module, draw]] = true
	check.call(
		draw_total == int(counts.get("draw_definitions", -1)),
		"The raw draw definitions match the per-module tables: %d" % draw_total
	)
	check.call(
		draw_seen.size() == int(counts.get("draw_functions", -1)),
		"Unique draw bodies after shadowing: %d" % draw_seen.size()
	)
	var shadowed: Array = source.get("shadowed_draw_functions", [])
	check.call(
		shadowed == ["level47.draw_kaizoku_raijin", "level48.draw_ursath"],
		"Two source modules define one body twice and shadow the first: %s" % str(shadowed)
	)
	var mini := 0
	var true_boss := 0
	for boss_id in classes:
		var boss_class := String(classes[boss_id])
		if boss_class == "mini":
			mini += 1
		elif boss_class == "true":
			true_boss += 1
	check.call(
		mini == 162 and true_boss == 54,
		"Source split is 162 mini / 54 true: %d / %d" % [mini, true_boss]
	)
	check.call(mini + true_boss == index.size(), "Every indexed boss carries a class")
	check.call(index.size() == 216, "The source index names 216 bosses: %d" % index.size())
	var orphan: Array = source.get("unindexed_draw_functions", [])
	check.call(
		orphan == ["level5.draw_morgath"],
		"The only unindexed draw function is the dead level5 morgath body: %s" % str(orphan)
	)
	var shared: Array = source.get("shared_draw_functions", [])
	check.call(shared.is_empty(), "No two boss ids share one draw function: %s" % str(shared))
	var unused: Array = source.get("unused_level_modules", [])
	check.call(unused.is_empty(), "Every level module is indexed: %s" % str(unused))
	var namespaces: Dictionary = source.get("draw_namespaces", {})
	var namespaced := 0
	for module in namespaces:
		namespaced += (namespaces[module] as Array).size()
	var renderer_spaces: Dictionary = source.get("renderer_namespaces", {})
	for renderer in renderer_spaces:
		namespaced += (renderer_spaces[renderer] as Array).size()
	check.call(namespaced == 216, "One _NS_ body class per source boss: %d" % namespaced)


func _check_catalog(check: Callable, source: Dictionary) -> void:
	var index: Dictionary = source.get("index", {})
	var classes: Dictionary = source.get("boss_classes", {})
	var costs: Dictionary = source.get("hero_unlock_costs", {})
	var stats := _stats()
	check.call(
		stats.size() == index.size(),
		"boss_stats.json holds every source boss: %d of %d" % [stats.size(), index.size()]
	)
	var missing_stats: Array = []
	var wrong_class: Array = []
	var missing_resource: Array = []
	var wrong_cost: Array = []
	var not_boss_hero: Array = []
	var parked := HeroRoster.DEFINITIONS
	for boss_id in index:
		var key := String(boss_id)
		if not stats.has(key):
			missing_stats.append(key)
			continue
		var row: Dictionary = stats[key]
		if String(row.get("boss_class", "")) != String(classes.get(key, "")):
			wrong_class.append(key)
		if not parked.has(key):
			missing_resource.append(key)
			continue
		var definition: Variant = parked[key]
		if not bool(definition.is_boss_hero):
			not_boss_hero.append(key)
		if int(definition.cost) != int(costs.get(key, -1)):
			wrong_cost.append(key)
	check.call(
		missing_stats.is_empty(),
		(
			"Every source boss has a stat row: %d missing %s"
			% [missing_stats.size(), str(missing_stats)]
		)
	)
	check.call(
		wrong_class.is_empty(), "Every stat row keeps its source class: %s" % str(wrong_class)
	)
	check.call(
		missing_resource.is_empty(),
		(
			"Every source boss has a hero resource: %d missing %s"
			% [missing_resource.size(), str(missing_resource)]
		)
	)
	check.call(
		not_boss_hero.is_empty(),
		"Every boss hero resource is flagged as one: %s" % str(not_boss_hero)
	)
	check.call(
		wrong_cost.is_empty(), "Every boss hero keeps its source summon cost: %s" % str(wrong_cost)
	)


## Arms are `"<id>":` on one line and `<id>(world, boss, ...)` on the next; the
## `_:` arm is the generic ability path the other 136 bosses take.
func _check_smart_ai(check: Callable, source: Dictionary) -> void:
	var lines := FileAccess.get_file_as_string(AI).split("\n")
	var smart: Array = source.get("smart_ai", [])
	var methods: Array = source.get("smart_ai_methods", [])
	var dispatch: Array = source.get("smart_ai_dispatch", [])
	check.call(smart.size() == 79, "The source dispatches 79 smart AIs: %d" % smart.size())
	check.call(dispatch.size() == 79, "All 79 arms sit in Boss.update: %d" % dispatch.size())
	var prefixed := 0
	for handler in methods:
		if not String(handler).begins_with("_smart_ai_"):
			prefixed += 1
	check.call(
		methods.size() == 79 and prefixed == 0,
		"Every source handler is a _smart_ai_* method: %d / %d" % [methods.size(), prefixed]
	)
	check.call(methods.size() == smart.size(), "One handler per dispatched boss")
	var arms: Array = []
	for i in range(lines.size() - 1):
		var line := lines[i]
		if not line.begins_with('\t\t"') or not line.ends_with('":'):
			continue
		var next := lines[i + 1]
		if not next.begins_with("\t\t\t_"):
			continue
		var arm := line.substr(3, line.length() - 5)
		if next.contains("\t\t\t%s(" % arm):
			arms.append(arm)
	var expected := dispatch.duplicate()
	expected.sort()
	var found := arms.duplicate()
	found.sort()
	check.call(arms.size() == 80, "boss_ai.gd holds 80 dispatch arms: %d" % arms.size())
	check.call(
		found == expected,
		(
			"The native arms are exactly the source dispatch: %d vs %d"
			% [found.size(), expected.size()]
		)
	)
	var extra: Array = []
	for arm in arms:
		if not smart.has(arm):
			extra.append(arm)
	check.call(
		extra == ["urgharun"],
		"The one native-only arm is urgharun, whose recipe has no source arm: %s" % str(extra)
	)
	check.call(
		FileAccess.get_file_as_string(AI).contains("\t\t_:\n\t\t\t_generic("),
		"Unlisted bosses fall through to the generic ability path"
	)


## The match resolves a boss hero's kit in `minion_battle.gd`: the audited
## shared source fallback, else `BossRecipeRegistry.handler(id, NATIVE_SKILLS)`
## (levels 1-9 in the dict, levels 10-20 in the registry handlers). Every
## source boss must resolve through one of those, and nothing may resolve twice.
func _check_skill_homes(check: Callable, source: Dictionary) -> void:
	var index: Dictionary = source.get("index", {})
	var shared: Array = SharedSkills.IDS
	var native := MinionBattle.NATIVE_SKILLS
	var starters := ["grimjaw", "sylara", "thorne", "vex", "zephyr"]
	var native_boss: Array = []
	var starter_only: Array = []
	for hero_id in native:
		if index.has(String(hero_id)):
			native_boss.append(String(hero_id))
		else:
			starter_only.append(String(hero_id))
	check.call(
		shared.size() == 150, "The audited shared fallback keeps 150 bosses: %d" % shared.size()
	)
	check.call(
		native_boss.size() == 22, "NATIVE_SKILLS carries 22 boss recipes: %d" % native_boss.size()
	)
	starter_only.sort()
	check.call(
		starter_only == starters,
		"NATIVE_SKILLS' other entries are the five non-boss starters: %s" % str(starter_only)
	)
	var double_home: Array = []
	for boss_id in native_boss:
		if shared.has(boss_id):
			double_home.append(boss_id)
	check.call(
		double_home.is_empty(), "No boss is both a recipe kit and shared: %s" % str(double_home)
	)
	var homeless: Array = []
	var wrong_type: Array = []
	var recipes := 0
	for boss_id in index:
		var key := String(boss_id)
		var handler: Variant = null
		if shared.has(key):
			handler = SharedSkills
		else:
			handler = RecipeRegistry.handler(key, native)
			if handler != null:
				recipes += 1
		if handler == null:
			homeless.append(key)
		elif not (handler is Script):
			wrong_type.append(key)
	check.call(
		homeless.is_empty(),
		(
			"Every source boss reaches a skill home: %d homeless %s"
			% [homeless.size(), str(homeless.slice(0, 12))]
		)
	)
	check.call(wrong_type.is_empty(), "Every resolved skill home is a script: %s" % str(wrong_type))
	check.call(recipes == 66, "The recipe homes cover 66 bosses: %d" % recipes)
	check.call(
		shared.size() + recipes == index.size(),
		"Skill homes add up to the whole roster: %d + %d" % [shared.size(), recipes]
	)
	check.call(RecipeRegistry.handler("gornak", native) != null, "A level-one recipe resolves")
	check.call(RecipeRegistry.handler("kenshiro", native) != null, "A level-nine recipe resolves")
	check.call(
		RecipeRegistry.handler("kaelvyrn", native) != null, "A registry-level recipe resolves"
	)
	check.call(
		RecipeRegistry.handler("aelyrion", native) == null,
		"A shared-fallback boss resolves to no registry recipe"
	)
	check.call(
		RecipeRegistry.handler("not_a_boss", native) == null,
		"An unknown id never resolves to a kit"
	)


func _check_art(check: Callable, source: Dictionary) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ART))
	var manifest: Dictionary = parsed if parsed is Dictionary else {}
	var bodies: Dictionary = manifest.get("bosses", {})
	var classes: Dictionary = source.get("boss_classes", {})
	var smart: Array = source.get("smart_ai", [])
	check.call(bodies.size() == 216, "Every boss body is baked: %d" % bodies.size())
	var unknown: Array = []
	var wrong_class: Array = []
	for boss_id in bodies:
		var key := String(boss_id)
		if not classes.has(key):
			unknown.append(key)
			continue
		if String((bodies[boss_id] as Dictionary).get("class", "")) != String(classes[key]):
			wrong_class.append(key)
	check.call(unknown.is_empty(), "No baked body names an unknown boss: %s" % str(unknown))
	check.call(
		wrong_class.is_empty(), "Every baked body keeps its source class: %s" % str(wrong_class)
	)
	var baked_smart: Array = (manifest.get("smart_bosses", []) as Array).duplicate()
	baked_smart.sort()
	var source_smart := smart.duplicate()
	source_smart.sort()
	check.call(
		baked_smart == source_smart,
		(
			"The baked smart-AI list is the source list: %d vs %d"
			% [baked_smart.size(), source_smart.size()]
		)
	)
