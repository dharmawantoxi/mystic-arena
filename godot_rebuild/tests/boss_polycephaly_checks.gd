extends RefCounted
## 9a: exact near-distance ordering, actual inventory -> bus -> hit replay.

const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const FIXTURE := "res://tests/fixtures/boss_polycephaly_source.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "9a four Polycephaly cases for 216 bosses")
	var helper := Prior.new()
	var world := Prior.CleaveChainWorld.new()
	for row: Dictionary in cases:
		helper._reset_world(world, false)
		var offsets: Array = row.offsets
		var spawned: Array = (
			helper
			. _spawn_case_units(
				world,
				String(row.boss_type),
				{
					"boss_offset": float(offsets[2]),
					"minion_offsets": [[11, float(offsets[0])], [12, float(offsets[1])]],
				}
			)
		)
		check.call(spawned.size() == 4, "9a boss world setup")
		if spawned.size() != 4:
			continue
		var hero: Prior.HeroState = spawned[1]
		var target: Prior.UnitState = spawned[2]
		var minions: Array = spawned[3]
		world.roles[int(minions[0].id)] = "unit_a"
		world.roles[int(minions[1].id)] = "unit_b"
		hero.items.hero_melee_flag = 0
		hero.items.hero_range = 200.0
		check.call(hero.items.add("basilisk_breath"), "9a equip Basilisk")
		var rng := RandomNumberGenerator.new()
		rng.seed = helper._seed_below(0.30)
		var enemies: Array = world._hero_enemy_list()
		var before: Array = hero.items._nearby_enemies_sorted_from(
			enemies, target.position, 200.0, target.id
		)
		var contrast: Array = row.expected_without_exact_sort
		for i in range(2):
			check.call(
				String(world.roles.get(int(before[i]), "")) == String(contrast[i][0]),
				"9a pre-fix epsilon ordering contrast"
			)
		var bus: Prior.BattleItemEffects = world._battle_item_effects(hero)
		hero.items.on_ranged_attack_hit(target.id, 50, enemies, rng, bus)
		var expected: Array = row.expected
		check.call(world.hit_order.size() == expected.size(), "9a two deliveries")
		for i in range(mini(world.hit_order.size(), expected.size())):
			var tid: int = int(world.hit_order[i])
			var hit: Array = world.deliveries[tid][0]
			# The fixture's third element is the source's third positional
			# argument (`u.take_damage(dmg, h.team, "magic")` => `damage_type`
			# "magic", `school=None`). The native recording stores the delivered
			# school, and layer 9g keeps the boss arm sourceless: no school
			# reaches `resolve_damage_school`, so the boss row is recorded as
			# "neutral" while regular units keep the declared magic school.
			var school: String = (
				"neutral" if String(expected[i][0]) == "boss" else String(expected[i][2])
			)
			check.call(
				int(hit[0]) == int(expected[i][1]) and String(hit[1]) == school,
				"9a 35 magic damage from source"
			)
		helper._reset_world(world, false)
	helper._reset_world(world, false)
