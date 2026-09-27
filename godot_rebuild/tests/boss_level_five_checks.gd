extends "res://tests/starter_finish_checks.gd"
## Krobellus + Vhalzun: real level-5 recipes, exact radius edges, recast ticks,
## self-heal HP-setter semantics, ranged homing attacks, respawn and roster.
const BOSS_FIXTURE := "res://tests/fixtures/boss_level_five_source.json"
const Skills = preload("res://scripts/combat/boss_level_five_skills.gd")
const Shared = preload("res://scripts/combat/source_shared_boss_skills.gd")
const BOSSES := {
	"krobellus": preload("res://data/heroes/krobellus.tres"),
	"vhalzun": preload("res://data/heroes/vhalzun.tres")
}
# Source BossHeroSkills._SKILL_REGISTRY method names, verbatim.
const RECIPES := {
	"krobellus":
	{
		"q": "_cast_q_krobellus_exorcism",
		"w": "_cast_w_krobellus_silence",
		"e": "_cast_e_krobellus_siphon",
		"r": "_cast_r_krobellus_crypt"
	},
	"vhalzun":
	{
		"q": "_cast_q_vhalzun_death_pulse",
		"w": "_cast_w_vhalzun_heartstopper",
		"e": "_cast_e_vhalzun_reapers_scythe",
		"r": "_cast_r_vhalzun_ghost_shroud"
	}
}


func _hero(world: Battle, kind: String) -> Battle.HeroState:
	return world.spawn_hero(BOSSES[kind], world.RED, Vector2(500, 340))


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(BOSS_FIXTURE))
	_catalog(fixture, check)
	for kind in BOSSES:
		_levels(kind, fixture.levels[kind], check)
	for row in fixture.casts:
		_cast(row, check)
	for row in fixture.traces:
		_trace(row, check)
	for row in fixture.recasts:
		_recast(row, check)
	for row in fixture.heals:
		_heal(row, check)
	for row in fixture.attacks:
		_attack(row, check)
	for row in fixture.respawn:
		_respawn(row, check)
	for kind in BOSSES:
		_lifecycle(kind, check)
	_roster(check)


func _catalog(fixture: Dictionary, check: Callable) -> void:
	for kind in BOSSES:
		var row: Dictionary = fixture.catalog[kind]
		var definition = BOSSES[kind]
		check.call(kind in Skills.IDS, kind + " native level5 handler membership")
		check.call(not Shared.IDS.has(kind), kind + " is not a _fallback_cast ID")
		check.call(definition.catalog_damage == row.damage, kind + " raw catalog damage")
		check.call(definition.cost == row.cost, kind + " source summon price")
		check.call(definition.dmg_school == str(row.school), kind + " source damage school")
		check.call(definition.is_melee == bool(row.melee), kind + " source attack mode")
		check.call(definition.skill_range_px == float(row.skill_range), kind + " skill reach")
		check.call(definition.skill_cooldown_max == int(row.cooldowns.q), kind + " Q cooldown")
		check.call(definition.w_cooldown_max == int(row.cooldowns.w), kind + " W cooldown")
		check.call(definition.e_cooldown_max == int(row.cooldowns.e), kind + " E cooldown")
		check.call(definition.r_cooldown_max == int(row.cooldowns.r), kind + " R cooldown")
		for key in ["q", "w", "e", "r"]:
			check.call(
				int(Skills.VISUAL[kind][key]) == int(row.visual[key]),
				kind + " " + key + " source visual duration"
			)
			check.call(
				float(Skills.RADIUS[kind][key]) == float(row.radius[key]),
				kind + " " + key + " source recipe radius"
			)
			var names: Dictionary = row.recipe
			check.call(
				String(names[key]) == _recipe(kind, key),
				kind + " " + key + " distinct registry recipe " + str(names[key])
			)
			check.call(
				String(names[key]) != String(fixture.catalog[_other(kind)].recipe[key]),
				kind + " " + key + " recipe is not shared with the other level5 boss"
			)


func _recipe(kind: String, key: String) -> String:
	return RECIPES[kind][key]


func _other(kind: String) -> String:
	return "vhalzun" if kind == "krobellus" else "krobellus"


func _cast(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	if bool(row.get("dead", false)):
		enemies[int(row.target)].alive = false
	if int(row.target) >= 0:
		hero.target_id = enemies[int(row.target)].id
	check.call(helpers._skill(world, hero.id, row.key) == row.ok, row.hero + " cast " + row.key)
	check.call(
		helpers._skill(world, hero.id, row.key) == row.repeat,
		row.hero + " duplicate cast " + row.key
	)
	_compare(hero, enemies, row.state, check, row.hero + " " + row.key)


func _trace(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	hero.hp = 500
	var enemies := _enemies(world, row.positions)
	hero.target_id = enemies[0].id
	enemies[0].cooldown_ticks = 90
	check.call(
		helpers._skill(world, hero.id, row.key), "Level5 timer cast " + row.hero + " " + row.key
	)
	var moment := 0
	for tick in range(1, int(row.get("length", 601)) + 1):
		if tick == 2 and row.mode == "move_upgrade":
			hero.position.x += 100
			enemies[0].position.x += 200
			check.call(hero.upgrade(), "Upgrade during level5 effect")
		if tick == 2 and row.mode == "retarget":
			hero.target_id = enemies[1].id
		if tick == 2 and row.mode == "target_dies":
			enemies[0].alive = false
		world._tick_hero(hero)
		if moment < row.rows.size() and tick == row.rows[moment].tick:
			_compare(
				hero,
				enemies,
				row.rows[moment].state,
				check,
				row.hero + " " + row.key + " " + row.mode + " tick " + str(tick)
			)
			moment += 1
	check.call(
		moment == row.rows.size(), "All level5 trace moments compared " + row.hero + " " + row.key
	)


func _recast(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	hero.hp = 500
	var enemies := _enemies(world, [[550, 340]])
	check.call(
		helpers._skill(world, hero.id, row.key), "Level5 recast priming " + row.hero + " " + row.key
	)
	var moment := 0
	for tick in range(1, int(row.length) + 1):
		world._tick_hero(hero)
		if moment < row.rows.size() and tick == int(row.rows[moment].tick):
			check.call(
				helpers._skill(world, hero.id, row.key) == row.rows[moment].ok,
				row.hero + " " + row.key + " exact recast tick " + str(tick)
			)
			_compare(
				hero,
				enemies,
				row.rows[moment].state,
				check,
				row.hero + " " + row.key + " recast tick " + str(tick)
			)
			moment += 1
	check.call(
		moment == row.rows.size(), "All level5 recast moments compared " + row.hero + " " + row.key
	)


func _heal(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	match String(row.hp_mode):
		"partial":
			hero.hp = 500
		"full":
			hero.hp = hero.max_hp
		"one":
			hero.hp = 1
	var enemy = helpers._dummy(world, Vector2(550, 340))
	var label: String = (
		String(row.hero)
		+ " "
		+ String(row.key)
		+ " "
		+ String(row.hp_mode)
		+ " anti "
		+ str(row.anti_heal)
	)
	var anti := float(row.anti_heal)
	if anti > 0.0:
		check.call(world.apply_anti_heal(hero.id, anti, 600), label + " applied")
	check.call(hero.hp == row.before, label + " precondition")
	check.call(helpers._skill(world, hero.id, row.key), label + " cast")
	check.call(hero.hp == row.hp, label + " source heal cap then anti-heal")
	check.call(enemy.hp == row.enemy_hp, label + " damage still lands")
	check.call(
		(
			hero.anti_heal_amount == row.anti_heal_amount
			and hero.anti_heal_timer == row.anti_heal_timer
		),
		label + " debuff fields untouched by heal"
	)


func _attack(row: Dictionary, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, row.hero)
	var point: Array = row.get("target_position", [560, 340])
	var enemy = helpers._dummy(world, Vector2(point[0], point[1]))
	check.call(world.hero_basic_attack(hero.id, enemy.id), "Level5 ranged attack " + row.hero)
	for moment in row.rows:
		if moment.tick > 0:
			world._tick_hero(hero)
		check.call(enemy.hp == moment.hp, "Level5 projectile impact " + row.hero)
		check.call(hero.attack_timer == moment.attack_timer, "Level5 attack cooldown " + row.hero)
		check.call(
			world.hero_projectiles.size() == moment.positions.size(),
			"Level5 arrow lifecycle " + row.hero
		)
		for index in range(mini(world.hero_projectiles.size(), moment.positions.size())):
			var arrow: Array = moment.positions[index]
			check.call(
				(
					world.hero_projectiles[index].position.distance_to(Vector2(arrow[0], arrow[1]))
					< 0.002
				),
				"Level5 homing trajectory " + row.hero
			)


func _respawn(row: Dictionary, check: Callable) -> void:
	var world := World.new()
	var hero := _hero(world, row.hero)
	var enemies := _enemies(world, [[550, 340]])
	for key in ["q", "w", "e", "r"]:
		check.call(helpers._skill(world, hero.id, key), "Pre-death activation " + row.hero)
	hero.attack_timer = 17
	hero.hp = 0
	hero.alive = false
	hero.respawn_timer = 1
	world._step_hero_respawn(hero)
	_compare(hero, enemies, row.state, check, row.hero + " respawn")


func _lifecycle(kind: String, check: Callable) -> void:
	var world := Battle.new()
	var hero := _hero(world, kind)
	var twin := _hero(world, kind)
	var enemies := _enemies(world, [[550, 340]])
	hero.hp = 1
	world._deliver_hit(enemies[0].id, world.BLUE, hero, 10000, "magic", enemies[0].position)
	check.call(not hero.alive and hero.deaths == 1, kind + " level5 death recorded once")
	for key in ["q", "w", "e", "r"]:
		check.call(not helpers._skill(world, hero.id, key), kind + " dead level5 cast refused")
	check.call(twin.skill_timer == 0 and twin.r_cooldown == 0, kind + " per-instance kit state")
	var match_world := World.new()
	var living := _hero(match_world, kind)
	_enemies(match_world, [[550, 340]])
	match_world.winner = match_world.BLUE
	for key in ["q", "w", "e", "r"]:
		check.call(
			not helpers._skill(match_world, living.id, key), kind + " finished match no cast"
		)


func _roster(check: Callable) -> void:
	var world := World.new()
	world.economy.credit_kill(world.RED, 4000)
	var index := 0
	for kind in BOSSES:
		var definition = BOSSES[kind]
		check.call(
			world._buy_ai_hero(kind, definition.cost, Vector2(1120, 90 + index * 40)),
			"Level5 real kits purchased " + kind
		)
		index += 1
	var gold: int = world.economy.gold[world.RED]
	check.call(
		not world._buy_ai_hero("kunkka", 900, Vector2(1120, 90 + index * 40)),
		"Pending level6 recipe still refused after level5 batch"
	)
	check.call(world.transaction_error == "kit", "Pending refusal reason is a missing kit")
	check.call(world.economy.gold[world.RED] == gold, "Pending refusal never debits gold")
	check.call(world.economy.is_balanced(), "Level5 roster ledger balanced")
	check.call(world.units.size() == BOSSES.size(), "Level5 heroes registered")
	for unit in world.units:
		check.call(BOSSES.has(unit.definition.id), "Distinct level5 identity " + unit.definition.id)


func _compare(hero, enemies: Array, expected: Dictionary, check: Callable, label: String) -> void:
	for key in expected:
		if key == "enemies":
			for idx in range(enemies.size()):
				for field in expected.enemies[idx]:
					check.call(
						enemies[idx].get(field) == expected.enemies[idx][field],
						label + " enemy " + str(idx) + " " + field
					)
		elif (
			key
			in [
				"position",
				"vortex_origin",
				"blink_from",
				"mana_void_origin",
				"alchemy_target",
				"w_dir",
				"r_dir"
			]
		):
			if expected[key] is Array:
				check.call(
					hero.get(key) == Vector2(expected[key][0], expected[key][1]), label + " " + key
				)
			else:
				check.call(hero.get(key) == expected[key], label + " " + key)
		elif key in ["target_id", "flux_target_id"]:
			var target := int(expected[key])
			check.call(
				hero.get(key) == (-1 if target < 0 else enemies[target].id), label + " " + key
			)
		else:
			check.call(hero.get(key) == expected[key], label + " " + key)


func _enemies(world: Battle, positions: Array) -> Array:
	var result := []
	for pos in positions:
		result.append(helpers._dummy(world, Vector2(pos[0], pos[1])))
	return result
