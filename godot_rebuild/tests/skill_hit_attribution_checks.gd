extends RefCounted
## 9y: the shared skill-delivery helper keeps the source attribution split.
##
## The source kits deliver damage through three shapes (`hero_skills/_bundle.py`):
## `BaseSkill._deal_aoe_damage` (`:105-119`) sends `source=self.hero` plus
## `school=<hero dmg_school>`, the kit tick loops send `source=h` (the school
## then resolves from `source.dmg_school`), and every other recipe call is the
## bare two positional arguments `take_damage(damage, team)` - no source, no
## school - so the victim never credits the caster and never cuts armour.
##
## The native port spells that out in `skill_common.gd::hit(..., attributed)`
## (`Common.hit(..., true)`) and `world._deal_hero_aoe(...)`. This suite recomputes
## the site tokens straight from the shipped scripts, checks the per-kit counts
## against the executed source rows, and replays the attributed and sourceless
## columns through production casts (Vex R, Thorne E, Gornak Q).
##
## Nothing here changes production code: several earlier layers (9m/9u/9v) already
## moved the kits onto these shapes, and this layer locks the split so a flipped
## flag or a new site cannot slip through.

const World = preload("res://scripts/match/prototype_battle.gd")
const VexSkills = preload("res://scripts/combat/vex_skills.gd")
const ThorneSkills = preload("res://scripts/combat/thorne_skills.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const TROLL = preload("res://data/minions/troll.tres")
# `prototype_battle.gd` exposes VEX/THORNE as definitions; gornak has no
# constant there, so the boss definition is preloaded here.
const THORNE = preload("res://data/heroes/thorne.tres")
const GORNAK = preload("res://data/heroes/gornak.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/skill_hit_attribution_source.json"
const POS := Vector2(600.0, 500.0)
const GAP := 60.0


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the skill attribution fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the skill attribution fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_tokens(fixture, check)
	_source_counts(fixture, check)
	_live_stats(fixture, check)
	_replay(fixture, check)


func _tokens(fixture: Dictionary, check: Callable) -> void:
	# Live substring counts of the shipped delivery sites, so a new
	# `Common.hit(` site or a flipped `, true)` breaks this immediately.
	var tokens: Dictionary = fixture.get("native_site_tokens", {})
	check.call(tokens.size() >= 20, "the fixture pins every delivery file")
	var mismatches := 0
	for path in tokens.keys():
		var row: Dictionary = tokens[path]
		if not FileAccess.file_exists(String(path)):
			mismatches += 1
			continue
		var text := FileAccess.get_file_as_string(String(path))
		if (
			text.count("Common.hit(") != int(row.get("common_hit", -1))
			or _hit_true_suffix(text) != int(row.get("hit_true_suffix", -1))
			or (
				text.count("_deal_hero_aoe(") - text.count("func _deal_hero_aoe(")
				!= int(row.get("aoe_calls", -1))
			)
		):
			mismatches += 1
	check.call(
		mismatches == 0, "every pinned delivery file keeps its site tokens (%d drift)" % mismatches
	)


func _hit_true_suffix(text: String) -> int:
	# Mirror of the oracle's `Common\.hit\((.*?)\)\n` scan: only the bodies of
	# `Common.hit(` calls ending in `true` are attributed.
	var count := 0
	var cursor := 0
	var token := "Common.hit("
	while true:
		var start := text.find(token, cursor)
		if start < 0:
			break
		var end := text.find(")\n", start)
		if end < 0:
			break
		var body := text.substr(start + token.length(), end - start - token.length())
		if body.strip_edges().ends_with("true"):
			count += 1
		cursor = end + 1
	return count


func _source_counts(fixture: Dictionary, check: Callable) -> void:
	var counts: Dictionary = fixture.get("source_counts", {})
	var expected := {
		"VexSkills": [3, 4],
		"ZephyrSkills": [4, 2],
		"ThorneSkills": [3, 1],
		"GrimjawSkills": [4, 1],
		"KaizenSkills": [4, 0],
	}
	for kit in expected.keys():
		var row: Dictionary = counts.get(kit, {})
		var want: Array = expected[kit]
		check.call(
			(
				int(row.get("attributed", -1)) == int(want[0])
				and int(row.get("sourceless", -1)) == int(want[1])
			),
			"%s keeps the source attribution split" % kit
		)
	var boss: Dictionary = counts.get("BossHeroSkills", {})
	check.call(
		int(boss.get("attributed", -1)) == 2 and int(boss.get("aoe_sites", -1)) == 0,
		"the boss recipes stay sourceless apart from the shared fallback"
	)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		(
			String(stats.get("vex_school", "")) == "magic"
			and String(stats.get("thorne_school", "")) == "physical"
		),
		"the fixture records the caster schools"
	)
	check.call(
		(
			int(ARCHER.armor) == int(stats.get("tower_armor", -1))
			and int(TROLL.armor) == int(stats.get("troll_armor", -1))
			and is_equal_approx(
				float(TROLL.magic_resist), float(stats.get("troll_magic_resist", -1.0))
			)
		),
		"the fixture mitigation stats are the live catalog values"
	)
	var world := World.new()
	world.setup_arena()
	var vex: HeroState = world.spawn_hero(World.VEX, World.BLUE, POS)
	var thorne: HeroState = world.spawn_hero(THORNE, World.BLUE, POS)
	var gornak: HeroState = world.spawn_hero(GORNAK, World.BLUE, POS)
	if vex == null or thorne == null or gornak == null:
		check.call(false, "the fixture casters spawn")
		return
	check.call(
		(
			int(vex.skill_damage()) == int(stats.get("vex_skill_base", -1))
			and int(thorne.skill_damage()) == int(stats.get("thorne_skill_base", -1))
			and int(gornak.skill_damage()) == int(stats.get("gornak_skill_base", -1))
		),
		"the fixture skill bases are the live level-1 values"
	)


func _replay(fixture: Dictionary, check: Callable) -> void:
	var rows: Dictionary = {}
	for row in fixture.get("cases", []) as Array:
		var data: Dictionary = row
		rows[String(data.get("name", ""))] = data
	check.call(rows.size() >= 4, "every fixture row is addressable")
	_vex_r(rows, check)
	_thorne_e(rows, check)
	_gornak_q(rows, check)


func _expected(rows: Dictionary, name: String) -> Dictionary:
	var data: Dictionary = rows.get(name, {})
	return data.get("expected", {})


func _vex_r(rows: Dictionary, check: Callable) -> void:
	# Attributed arm: `_deal_aoe_damage` sends the caster and its magic school,
	# so the troll's magic_resist cuts the hit and the caster is credited.
	var world := World.new()
	world.setup_arena()
	var troll: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if troll == null:
		check.call(false, "the vex victim spawns")
		return
	troll.position = POS
	var vex: HeroState = world.spawn_hero(World.VEX, World.BLUE, POS + Vector2(GAP, 0.0))
	if vex == null:
		check.call(false, "vex spawns")
		return
	vex.skill_timer = 0
	vex.target_id = troll.id
	var hp_before: float = troll.hp
	var credit_before: int = vex.damage_dealt
	check.call(VexSkills.cast(world, vex, "r", []), "the vex R cast lands")
	var live := {
		"hp_loss": int(hp_before - troll.hp),
		"credited_total": int(vex.damage_dealt - credit_before),
	}
	var attributed := _expected(rows, "vex_r_attributed_on_troll")
	var sourceless := _expected(rows, "vex_r_sourceless_on_troll")
	check.call(
		int(live["hp_loss"]) == int(attributed.get("hp_loss", -1)),
		"vex R applies the magic-school cut (%s)" % live["hp_loss"]
	)
	check.call(
		int(live["credited_total"]) == int(attributed.get("credited_total", -1)),
		"vex R credits the caster (%s)" % live["credited_total"]
	)
	check.call(
		(
			int(sourceless.get("hp_loss", -1)) > int(live["hp_loss"])
			and int(sourceless.get("credited_total", -1)) == 0
		),
		"the sourceless column stays the divergent control"
	)


func _thorne_e(rows: Dictionary, check: Callable) -> void:
	# Attributed arm on a structure: tower armour 3 cuts the physical hit and the
	# caster is credited the post-armour amount.
	var world := World.new()
	world.setup_arena()
	var tower: StructureState = world.spawn_structure(ARCHER, World.RED, POS)
	if tower == null:
		check.call(false, "the thorne tower spawns")
		return
	# `spawn_structure` hands the tower a free shield (layer 9m); the row
	# measures the armour question.
	tower.shield = 0.0
	tower.free_shield_active = false
	tower.shield_active = false
	var thorne: HeroState = world.spawn_hero(THORNE, World.BLUE, POS + Vector2(GAP, 0.0))
	if thorne == null:
		check.call(false, "thorne spawns")
		return
	thorne.skill_timer = 0
	thorne.target_struct = tower
	var hp_before: float = tower.hp
	var credit_before: int = thorne.damage_dealt
	check.call(ThorneSkills.cast(world, thorne, "e", [tower]), "the thorne E cast lands")
	var expected := _expected(rows, "thorne_e_attributed_on_tower")
	check.call(
		int(hp_before - tower.hp) == int(expected.get("hp_loss", -1)),
		"thorne E is cut by the tower armour (%d)" % int(hp_before - tower.hp)
	)
	check.call(
		int(thorne.damage_dealt - credit_before) == int(expected.get("credited_total", -1)),
		"thorne E credits the post-armour amount"
	)


func _gornak_q(rows: Dictionary, check: Callable) -> void:
	# Sourceless arm: the boss recipe sends only damage and team, so the troll's
	# magic_resist never cuts the magic-schooled payload and nothing is credited.
	var world := World.new()
	world.setup_arena()
	var troll: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if troll == null:
		check.call(false, "the gornak victim spawns")
		return
	troll.position = POS
	var gornak: HeroState = world.spawn_hero(GORNAK, World.BLUE, POS + Vector2(GAP, 0.0))
	if gornak == null:
		check.call(false, "gornak spawns")
		return
	gornak.skill_timer = 0
	var hp_before: float = troll.hp
	var credit_before: int = gornak.damage_dealt
	check.call(world.cast_hero_q(gornak.id, []), "the gornak Q cast lands")
	var expected := _expected(rows, "gornak_q_sourceless_on_troll")
	check.call(
		int(hp_before - troll.hp) == int(expected.get("hp_loss", -1)),
		"gornak Q lands raw on the troll (%d)" % int(hp_before - troll.hp)
	)
	check.call(
		int(gornak.damage_dealt - credit_before) == int(expected.get("credited_total", -1)),
		"gornak Q records no credit"
	)
