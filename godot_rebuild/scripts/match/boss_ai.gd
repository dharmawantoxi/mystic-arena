# gdlint:disable=max-file-lines,max-public-methods,max-line-length,max-returns,function-arguments-number,unused-argument
extends RefCounted
## Layer 8d: source Boss smart ability dispatch for the first active slice.
## The generic Boss ability path is also retained for boss IDs without a native
## recipe in this active match. Entrance/enrage clocks and presentation stay in
## later layers.

const BossState = preload("res://scripts/match/boss_state.gd")
const Damage = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")


static func tick(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, target_distance: float
) -> void:
	if boss == null or not boss.alive:
		return
	# Boss.update checks the true-boss heal before it looks for a target.
	_heal_ability_if_ready(boss)
	if target == null:
		return
	_tick_smart_clocks(world, boss, target)
	match boss.boss_type:
		"gornak":
			_gornak(world, boss, enemies, target, target_distance)
		"morgath":
			_morgath(world, boss, enemies, target, target_distance)
		"drakar":
			_drakar(world, boss, enemies, target, target_distance)
		"abaddon":
			_abaddon(world, boss, enemies, target, target_distance)
		"alchemist":
			_alchemist(world, boss, enemies, target, target_distance)
		"malzareth":
			_malzareth(world, boss, enemies, target, target_distance)
		"akashari":
			_akashari(world, boss, enemies, target, target_distance)
		"vorenmarr":
			_vorenmarr(world, boss, enemies, target, target_distance)
		"nyxarath":
			_nyxarath(world, boss, enemies, target, target_distance)
		"thalgryn":
			_thalgryn(world, boss, enemies, target, target_distance)
		"syrentha":
			_syrentha(world, boss, enemies, target, target_distance)
		"gravewake":
			_gravewake(world, boss, enemies, target, target_distance)
		"kunkka":
			_kunkka(world, boss, enemies, target, target_distance)
		"razak":
			_razak(world, boss, enemies, target, target_distance)
		"kenshiro":
			_kenshiro(world, boss, enemies, target, target_distance)
		"khazan":
			_khazan(world, boss, enemies, target, target_distance)
		"wiro":
			_wiro(world, boss, enemies, target, target_distance)
		"naraka":
			_naraka(world, boss, enemies, target, target_distance)
		"krognarr":
			_krognarr(world, boss, enemies, target, target_distance)
		"raz":
			_raz(world, boss, enemies, target, target_distance)
		"vraskhan":
			_vraskhan(world, boss, enemies, target, target_distance)
		"aurethzar":
			_aurethzar(world, boss, enemies, target, target_distance)
		"aeralith":
			_aeralith(world, boss, enemies, target, target_distance)
		"aurex":
			_aurex(world, boss, enemies, target, target_distance)
		"nyxareva":
			_nyxareva(world, boss, enemies, target, target_distance)
		"thalakryon":
			_thalakryon(world, boss, enemies, target, target_distance)
		"aurelix":
			_aurelix(world, boss, enemies, target, target_distance)
		"aurelyssa":
			_aurelyssa(world, boss, enemies, target, target_distance)
		"vargrath":
			_vargrath(world, boss, enemies, target, target_distance)
		"nazulmor":
			_nazulmor(world, boss, enemies, target, target_distance)
		"kaeldris":
			_kaeldris(world, boss, enemies, target, target_distance)
		"pyraklos":
			_pyraklos(world, boss, enemies, target, target_distance)
		"velmyrth":
			_velmyrth(world, boss, enemies, target, target_distance)
		"solvarin":
			_solvarin(world, boss, enemies, target, target_distance)
		"azureth":
			_azureth(world, boss, enemies, target, target_distance)
		"luminar":
			_luminar(world, boss, enemies, target, target_distance)
		"solara":
			_solara(world, boss, enemies, target, target_distance)
		"pyraethis":
			_pyraethis(world, boss, enemies, target, target_distance)
		"auroth":
			_auroth(world, boss, enemies, target, target_distance)
		"morvein":
			_morvein(world, boss, enemies, target, target_distance)
		"thorvak":
			_thorvak(world, boss, enemies, target, target_distance)
		"yamako":
			_yamako(world, boss, enemies, target, target_distance)
		"ignirus":
			_ignirus(world, boss, enemies, target, target_distance)
		"leoric":
			_leoric(world, boss, enemies, target, target_distance)
		"shirotaka":
			_shirotaka(world, boss, enemies, target, target_distance)
		"seiryukong":
			_seiryukong(world, boss, enemies, target, target_distance)
		"kaelthorn":
			_kaelthorn(world, boss, enemies, target, target_distance)
		"solvanth":
			_solvanth(world, boss, enemies, target, target_distance)
		"xyrael":
			_xyrael(world, boss, enemies, target, target_distance)
		"nyxareth":
			_nyxareth(world, boss, enemies, target, target_distance)
		"cryssalia":
			_cryssalia(world, boss, enemies, target, target_distance)
		"kaelthar":
			_kaelthar(world, boss, enemies, target, target_distance)
		"morkhaera":
			_morkhaera(world, boss, enemies, target, target_distance)
		"aurelion":
			_aurelion(world, boss, enemies, target, target_distance)
		"akahime":
			_akahime(world, boss, enemies, target, target_distance)
		"nyxthrael":
			_nyxthrael(world, boss, enemies, target, target_distance)
		"sylvantheros":
			_sylvantheros(world, boss, enemies, target, target_distance)
		"vaelindra":
			_vaelindra(world, boss, enemies, target, target_distance)
		"astraelion":
			_astraelion(world, boss, enemies, target, target_distance)
		"morvaenthir":
			_morvaenthir(world, boss, enemies, target, target_distance)
		"thornvaegrim":
			_thornvaegrim(world, boss, enemies, target, target_distance)
		"morthraxis":
			_morthraxis(world, boss, enemies, target, target_distance)
		"ancient_apparition":
			_ancient_apparition(world, boss, enemies, target, target_distance)
		"ignis_drachorn":
			_ignis_drachorn(world, boss, enemies, target, target_distance)
		"vhorethzir":
			_vhorethzir(world, boss, enemies, target, target_distance)
		"vaerith":
			_vaerith(world, boss, enemies, target, target_distance)
		"xirthalis":
			_xirthalis(world, boss, enemies, target, target_distance)
		"vhyssarion":
			_vhyssarion(world, boss, enemies, target, target_distance)
		"khalros":
			_khalros(world, boss, enemies, target, target_distance)
		"gorath":
			_gorath(world, boss, enemies, target, target_distance)
		"varkul":
			_varkul(world, boss, enemies, target, target_distance)
		"xerathis":
			_xerathis(world, boss, enemies, target, target_distance)
		"nyzrak":
			_nyzrak(world, boss, enemies, target, target_distance)
		"zharok":
			_zharok(world, boss, enemies, target, target_distance)
		"pyrenth":
			_pyrenth(world, boss, enemies, target, target_distance)
		"vokrahn":
			_vokrahn(world, boss, enemies, target, target_distance)
		"nyxara":
			_nyxara(world, boss, enemies, target, target_distance)
		"gravefang":
			_gravefang(world, boss, enemies, target, target_distance)
		"vhalzun":
			_vhalzun(world, boss, enemies, target, target_distance)
		_:
			_generic(world, boss, enemies)


static func _tick_smart_clocks(world, boss: BossState, target: UnitState) -> void:
	if boss.q_timer > 0:
		boss.q_timer -= 1
	if boss.w_timer > 0:
		boss.w_timer -= 1
	if boss.e_timer > 0:
		boss.e_timer -= 1
	if boss.r_timer > 0:
		boss.r_timer -= 1
	if boss.active_skill_timer > 0:
		boss.active_skill_timer -= 1
		if boss.active_skill_timer <= 0:
			boss.active_skill = ""
	if boss.rage_active:
		boss.rage_timer -= 1
		if boss.rage_timer <= 0:
			boss.rage_active = false
			boss.damage = _source_damage(boss)
	if boss.defense_timer > 0:
		boss.defense_timer -= 1
		if boss.defense_timer <= 0:
			boss.defense_boost = false
	if boss.dragon_form_active:
		boss.dragon_form_timer -= 1
		if boss.dragon_form_timer <= 0:
			boss.dragon_form_active = false
			boss.damage = _source_damage(boss)
	if boss.dragon_blood_active:
		boss.dragon_blood_timer -= 1
		if boss.dragon_blood_timer <= 0:
			boss.dragon_blood_active = false
	if boss.corrosive_active:
		boss.corrosive_timer -= 1
		if boss.corrosive_timer <= 0:
			boss.corrosive_active = false
	if boss.shukuchi_active:
		boss.shukuchi_timer -= 1
		if boss.shukuchi_timer <= 0:
			boss.shukuchi_active = false
	if boss.shield_active:
		boss.shield_timer -= 1
		if boss.shield_timer <= 0:
			boss.shield_active = false
	if boss.arcane_buff_active:
		boss.arcane_buff_timer -= 1
		if boss.arcane_buff_timer <= 0:
			boss.arcane_buff_active = false
			boss.damage = boss.base_damage
	if boss.vortex_active_timer > 0:
		boss.vortex_active_timer -= 1
	# xirthalis timelapse mark every 300 ticks
	if boss.boss_type == "xirthalis":
		boss.timelapse_mark_timer += 1
		if boss.timelapse_mark_timer >= 300:
			boss.timelapse_mark_timer = 0
			boss.timelapse_hp_mark = boss.hp
	if boss.boss_type == "morgath":
		_tick_morgath_effects(world, boss, target)


static func _tick_morgath_effects(world, boss: BossState, target: UnitState) -> void:
	if boss.flux_active_timer > 0:
		boss.flux_active_timer -= 1
		if boss.flux_active_timer % 30 == 0:
			var flux_target: UnitState = world.get_unit(boss.flux_target_id)
			if flux_target != null and flux_target.alive:
				_hit(world, boss, flux_target, int(_skill_damage(boss, boss.skill_w_damage) / 4.0))
				_slow(flux_target, 0.4, 60)
	if boss.clones_active_timer > 0:
		boss.clones_active_timer -= 1
		if boss.clones_active_timer % 40 == 0 and target != null and target.alive:
			_hit(world, boss, target, int(float(boss.damage) * 0.5))


static func _heal_ability_if_ready(boss: BossState) -> void:
	if (
		boss.boss_class == "true"
		and boss.ability2_cooldown > 0
		and boss.ability2_timer == 0
		and boss.hp < boss.max_hp * 0.3
	):
		boss.ability2_timer = boss.ability2_cooldown
		var heal_amount := int(boss.max_hp * boss.ability2_heal_pct)
		boss.hp = minf(float(boss.max_hp), boss.hp + heal_amount)


static func _generic(world, boss: BossState, enemies: Array[UnitState]) -> void:
	# Exact source _use_ability fallback: one AOE, then the generic cooldown.
	if boss.ability_timer != 0:
		return
	boss.ability_timer = boss.ability_cooldown
	boss.ability_active = true
	boss.ability_active_timer = 60
	for enemy in enemies:
		if boss.position.distance_to(enemy.position) <= boss.ability_range:
			_hit(world, boss, enemy, boss.eff_ability_damage())
			_attack_lock(enemy, 60)


static func _gornak(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 150.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		boss.mana_void_origin = boss.position
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if distance > 120.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 25)
		var delta := target.position - boss.position
		var length := delta.length()
		if length > 0.0:
			boss.blink_from = boss.position
			boss.position += delta / length * maxf(0.0, length - 60.0)
			boss.blink_to = boss.position
		return
	if nearby_count >= 3 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
				_attack_lock(enemy, 60)
		return
	if distance < 200.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _morgath(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var close_count := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.5 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 60)
		boss.clones_active_timer = 480
		boss.clones_positions = [Vector2(-60, 0), Vector2(60, 0)]
		_heal(boss, 0.15)
		return
	if close_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 90.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
				_attack_lock(enemy, 45)
		_heal(boss, 0.08)
		return
	if distance < 300.0 and boss.w_timer == 0 and boss.flux_active_timer <= 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		boss.flux_target_id = target.id
		boss.flux_active_timer = 240
		_hit(world, boss, target, int(_skill_damage(boss, boss.skill_w_damage) / 2.0))
		_slow(target, 0.5, 240)
		return
	if distance < 350.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _drakar(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 120.0)
	var low_hp_target := false
	var target_max := _max_hp(target)
	if target.alive and target.hp / maxf(1.0, target_max) < 0.3:
		low_hp_target = true
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if low_hp_target and distance < 100.0 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 60)
		var damage := _skill_damage(boss, boss.skill_r_damage)
		if target.hp / maxf(1.0, target_max) < 0.3:
			damage *= 2
			boss.r_timer = 120
		_hit(world, boss, target, damage)
		return
	if hp_ratio < 0.4 and not boss.rage_active and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 90)
		boss.rage_active = true
		boss.rage_timer = 300
		boss.damage = int(float(_source_damage(boss)) * 1.5)
		_heal(boss, 0.1)
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return
	if hp_ratio < 0.6 and not boss.defense_boost and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		boss.defense_boost = true
		boss.defense_timer = 180
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 120.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
				_attack_lock(enemy, 30)


static func _abaddon(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 150.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.3 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		_heal(boss, float(boss.skill_w_shield) / maxf(1.0, float(boss.max_hp)))
		return
	if nearby_count >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if distance < 130.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 30)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))
		return
	if distance > 100.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 40)
		var delta := target.position - boss.position
		var length := delta.length()
		if length > 0.0:
			boss.position += delta / length * 80.0
		_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))


static func _alchemist(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 180.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby_count >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		var kills_count := 0
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				var was_alive := enemy.alive
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				if was_alive and not enemy.alive:
					kills_count += 1
		if kills_count > 0:
			boss.hp = minf(float(boss.max_hp), boss.hp + kills_count * 100.0)
		return
	if hp_ratio < 0.6 and not boss.rage_active and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		boss.rage_active = true
		boss.rage_timer = 360
		boss.damage = int(float(boss.damage) * 1.5)
		_heal(boss, 0.15)
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 60)
		var target_position := target.position if target != null and target.alive else boss.position
		for enemy in enemies:
			if enemy.position.distance_to(target_position) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				_slow(enemy, 0.5, 180)
		return
	if distance < 200.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _malzareth(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby_count >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 90)
		_heal(boss, 0.12)
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_w_damage))
			for enemy in enemies:
				if enemy != target and target.position.distance_to(enemy.position) <= 60.0:
					_hit(
						world,
						boss,
						enemy,
						_skill_damage(boss, int(float(boss.skill_w_damage) / 2.0))
					)
		return
	if distance < 260.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 45)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))
		_slow(target, 0.5, 180)
		return
	if distance < 280.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 60)
		if target != null and target.alive:
			for enemy in enemies:
				if target.position.distance_to(enemy.position) <= 100.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))


static func _akashari(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby_count >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_slow(enemy, 0.5, 240)
		_heal(boss, 0.1)
		return
	if nearby_count >= 3 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 150.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if hp_ratio < 0.6 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		if target != null and target.alive:
			var delta := target.position - boss.position
			var length := delta.length()
			if length > 0.0:
				var step := minf(length, 150.0)
				boss.position += delta / length * step
				boss.direction = 1 if delta.x > 0.0 else -1
			for enemy in enemies:
				if boss.position.distance_to(enemy.position) <= 80.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		_heal(boss, 0.08)
		return
	if distance < 280.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))
		_slow(target, 0.4, 120)


static func _vorenmarr(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby_count := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby_count >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 100)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 90)
		_heal(boss, 0.12)
		return
	if hp_ratio < 0.6 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 70)
		_heal(boss, 0.14)
		return
	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 80)
		if target != null and target.alive:
			for enemy in enemies:
				if target.position.distance_to(enemy.position) <= 120.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
					_attack_lock(enemy, 60)
		return
	if distance < 280.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 70)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _nyxarath(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	if boss.necro_buff_active:
		boss.necro_buff_timer -= 1
		if boss.necro_buff_timer <= 0:
			boss.necro_buff_active = false
			boss.damage = boss.base_damage
	if boss.presence_active:
		boss.presence_timer -= 1
		if boss.presence_timer <= 0:
			boss.presence_active = false
	var nearby_count := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby_count >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 110)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 120)
				_slow(enemy, 0.6, 240)
				if enemy is HeroState:
					var delta := enemy.position - boss.position
					var length := delta.length()
					if length > 0.0:
						enemy.position += delta / length * 20.0
		_heal(boss, 0.13)
		return
	if hp_ratio < 0.6 and not boss.presence_active and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 80)
		boss.presence_active = true
		boss.presence_timer = 360
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_attack_lock(enemy, 90)
				_slow(enemy, 0.5, 240)
		_heal(boss, 0.1)
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 70)
		var kills_count := 0
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				if not enemy.alive:
					kills_count += 1
		boss.necro_buff_active = true
		boss.necro_buff_timer = 480
		boss.damage = int(float(boss.base_damage) * 1.4)
		var heal_amount := int(float(boss.max_hp) * 0.06) + kills_count * 30
		boss.hp = minf(float(boss.max_hp), boss.hp + heal_amount)
		return
	if distance < 280.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest: UnitState = null
		var closest_distance := INF
		for enemy in enemies:
			var enemy_distance := boss.position.distance_to(enemy.position)
			if enemy_distance < closest_distance:
				closest_distance = enemy_distance
				closest = enemy
		if closest == null or closest_distance > 300.0:
			return
		var direction := (closest.position - boss.position).normalized()
		for enemy in enemies:
			var relative := enemy.position - boss.position
			var projection := relative.dot(direction)
			var perpendicular := absf(relative.x * -direction.y + relative.y * direction.x)
			if projection > 0.0 and projection < 280.0 and perpendicular < 50.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))
				_attack_lock(enemy, 45)


static func _thalgryn(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	if boss.morph_buff_active:
		boss.morph_buff_timer -= 1
		if boss.morph_buff_timer <= 0:
			boss.morph_buff_active = false
			boss.damage = boss.base_damage
	var nearby_count := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby_count >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_slow(enemy, 0.4, 180)
		_heal(boss, 0.1)
		return
	if hp_ratio < 0.55 and not boss.morph_buff_active and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		boss.morph_buff_active = true
		boss.morph_buff_timer = 300
		boss.damage = int(float(boss.base_damage) * 1.35)
		_heal(boss, 0.14)
		return
	if distance > 150.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 60)
		if target != null and target.alive:
			var delta := target.position - boss.position
			var length := delta.length()
			if length > 0.0:
				var direction := delta / length
				for enemy in enemies:
					var relative := enemy.position - boss.position
					var projection := relative.dot(direction)
					var perpendicular := absf(relative.x * -direction.y + relative.y * direction.x)
					if projection > 0.0 and projection < 250.0 and perpendicular < 50.0:
						_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))
				boss.position += direction * minf(length, 200.0)
		return
	if distance < 280.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_w_damage))
			_attack_lock(target, 60)
			for enemy in enemies:
				if enemy != target and target.position.distance_to(enemy.position) <= 60.0:
					_hit(
						world,
						boss,
						enemy,
						_skill_damage(boss, int(float(boss.skill_w_damage) / 3.0))
					)


static func _syrentha(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	# Source _smart_ai_syrentha: Mirror Image buff clock, then R/E/W/Q priority.
	if boss.mirror_buff_active:
		boss.mirror_buff_timer -= 1
		if boss.mirror_buff_timer <= 0:
			boss.mirror_buff_active = false
			boss.damage = boss.base_damage
	var nearby_count := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.45 and nearby_count >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 150)
				_slow(enemy, 0.8, 300)
		_heal(boss, 0.1)
		return
	if hp_ratio < 0.6 and not boss.mirror_buff_active and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 70)
		boss.mirror_buff_active = true
		boss.mirror_buff_timer = 360
		boss.damage = int(float(boss.base_damage) * 1.4)
		_heal(boss, 0.12)
		return
	if nearby_count >= 3 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 150.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				_attack_lock(enemy, 120)
				_slow(enemy, 0.7, 240)
		return
	if distance < 260.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		if target == null or not target.alive:
			return
		var delta := target.position - boss.position
		var length := delta.length()
		if length <= 0.0:
			return
		var direction := delta / length
		for enemy in enemies:
			var relative := enemy.position - boss.position
			var projection := relative.dot(direction)
			var perpendicular := absf(relative.x * -direction.y + relative.y * direction.x)
			if projection > 0.0 and projection < 250.0 and perpendicular < 70.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))
				_slow(enemy, 0.5, 180)


static func _gravewake(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	# Source _smart_ai_gravewake: Kraken Shell clock, then R/E/W/Q priority with
	# the 180px "nearby" radius the source uses for this boss.
	if boss.shell_active:
		boss.shell_timer -= 1
		if boss.shell_timer <= 0:
			boss.shell_active = false
	var nearby_count := _count_near(boss, enemies, 180.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby_count >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 90)
				_slow(enemy, 0.5, 180)
				# Source pushes every unit that owns `.speed`; natively that is a hero.
				if enemy is HeroState:
					var delta := enemy.position - boss.position
					var length := delta.length()
					if length > 0.0:
						enemy.position += delta / length * 18.0
		_heal(boss, 0.1)
		return
	if hp_ratio < 0.6 and not boss.shell_active and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 70)
		boss.shell_active = true
		boss.shell_timer = 300
		_heal(boss, 0.12)
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 80)
		var center := boss.position
		if target != null and target.alive:
			center = target.position
		for enemy in enemies:
			if center.distance_to(enemy.position) <= 120.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				_attack_lock(enemy, 60)
		return
	if distance < 220.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		if target == null or not target.alive:
			return
		var delta := target.position - boss.position
		var length := delta.length()
		if length <= 0.0:
			return
		var direction := delta / length
		for enemy in enemies:
			var relative := enemy.position - boss.position
			var projection := relative.dot(direction)
			var perpendicular := absf(relative.x * -direction.y + relative.y * direction.x)
			if projection > 0.0 and projection < 200.0 and perpendicular < 60.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))
				_slow(enemy, 0.5, 180)


static func _kunkka(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	# Source _smart_ai_kunkka: rum buff clock, X Marks the Spot delayed burst,
	# then R/E/W/Q priority over the 180px nearby radius. The Q/W/E/R cooldowns
	# are the literals this boss hardcodes, not the stats table values.
	if boss.rum_buff_active:
		boss.rum_buff_timer -= 1
		if boss.rum_buff_timer <= 0:
			boss.rum_buff_active = false
			boss.damage = boss.base_damage
	if boss.x_mark_timer > 0:
		boss.x_mark_timer -= 1
		if boss.x_mark_timer <= 0 and boss.x_mark_target_id != -1:
			var marked: UnitState = world.get_unit(boss.x_mark_target_id)
			if marked != null and marked.alive:
				for enemy in enemies:
					if marked.position.distance_to(enemy.position) <= 120.0:
						_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
						_attack_lock(enemy, 60)
			boss.x_mark_target_id = -1
	var nearby_count := _count_near(boss, enemies, 180.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby_count >= 2 and boss.r_timer == 0:
		boss.r_timer = 720
		_set_skill(boss, "r", 100)
		var torrent_center := boss.position
		if target != null and target.alive:
			torrent_center = target.position
		for enemy in enemies:
			if torrent_center.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 120)
				# Source pushes every unit that owns `.speed`; natively that is a hero.
				if enemy is HeroState:
					var push := enemy.position - torrent_center
					var push_length := push.length()
					if push_length > 0.0:
						enemy.position += push / push_length * 20.0
		_heal(boss, 0.2)
		return
	if hp_ratio < 0.6 and not boss.rum_buff_active and boss.e_timer == 0:
		boss.e_timer = 480
		_set_skill(boss, "e", 90)
		if target == null or not target.alive:
			return
		var ship_delta := target.position - boss.position
		var ship_length := ship_delta.length()
		if ship_length <= 0.0:
			return
		var ship_direction := ship_delta / ship_length
		for enemy in enemies:
			var ship_relative := enemy.position - boss.position
			var ship_projection := ship_relative.dot(ship_direction)
			var ship_perpendicular := absf(
				ship_relative.x * -ship_direction.y + ship_relative.y * ship_direction.x
			)
			if ship_projection > 0.0 and ship_projection < 300.0 and ship_perpendicular < 80.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
				_attack_lock(enemy, 90)
		boss.rum_buff_active = true
		boss.rum_buff_timer = 480
		boss.damage = int(float(boss.base_damage) * 1.3)
		_heal(boss, 0.15)
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = 300
		_set_skill(boss, "w", 80)
		if target != null and target.alive:
			boss.x_mark_target_id = target.id
			boss.x_mark_timer = 120
		return
	if distance < 220.0 and boss.q_timer == 0:
		boss.q_timer = 240
		_set_skill(boss, "q", 45)
		if target == null or not target.alive:
			return
		var tide_delta := target.position - boss.position
		var tide_length := tide_delta.length()
		if tide_length <= 0.0:
			return
		var tide_direction := tide_delta / tide_length
		for enemy in enemies:
			var tide_relative := enemy.position - boss.position
			var tide_projection := tide_relative.dot(tide_direction)
			var tide_perpendicular := absf(
				tide_relative.x * -tide_direction.y + tide_relative.y * tide_direction.x
			)
			if tide_projection > 0.0 and tide_projection < 250.0 and tide_perpendicular < 70.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))


static func _razak(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	# Source _smart_ai_razak: Firestorm when crowded, then the distance gates
	# E (120 < dist < 260), W (dist <= 220) and Q (dist <= 260).
	var nearby_count := _count_near(boss, enemies, 180.0)
	if nearby_count >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if distance > 120.0 and distance < 260.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 35)
		if target != null and target.alive:
			var delta := target.position - boss.position
			var length := delta.length()
			if length > 0.0:
				var jump := minf(110.0, maxf(40.0, length - 50.0))
				boss.position += delta / length * jump
				boss.direction = 1 if delta.x > 0.0 else -1
			for enemy in enemies:
				if boss.position.distance_to(enemy.position) <= 80.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if distance <= 220.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 50)
		if target != null and target.alive:
			for enemy in enemies:
				if target.position.distance_to(enemy.position) <= 95.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
					_attack_lock(enemy, 45)
		return
	if distance <= 260.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		if target != null and target.alive:
			for enemy in enemies:
				if target.position.distance_to(enemy.position) <= 75.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))
					_slow(enemy, 0.35, 120)


static func _kenshiro(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_kenshiro: R when crowded + low HP, W when HP < 0.55,
	# E AOE when 2+, Q to closest when dist < 140.
	# Helpers _init_l9_timers / _tick_l9_timers are handled by _tick_smart_clocks;
	# _l9_stats maps to boss.skill_*_cooldown/damage; _l9_target is closest alive;
	# _l9_aoe is inclusive radial hit.
	var nearby_count := _count_near_alive(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby_count >= 3 and hp_ratio < 0.5 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 70)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if hp_ratio < 0.55 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			var delta := closest.position - boss.position
			var length := delta.length()
			if length > 1.0:
				var step := minf(length, 90.0)
				boss.position += delta / length * step
				boss.direction = 1 if delta.x > 0.0 else -1
				boss.facing = float(boss.direction)
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return
	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 150.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if distance < 140.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest_q := _closest_alive(boss, enemies)
		if closest_q != null and closest_q.alive:
			_hit(world, boss, closest_q, _skill_damage(boss, boss.skill_q_damage))


static func _khazan(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_khazan: R execute when 2+ within 210 + HP < 0.45,
	# E spin when 3+ within 210, W leap when dist > 120, Q chained blade when dist < 150.
	# Helpers _init_l9_timers / _tick_l9_timers handled by _tick_smart_clocks;
	# _l9_stats maps to boss.skill_*_cooldown/damage; _l9_target is closest alive;
	# _l9_aoe is inclusive radial hit.
	var nearby_count := _count_near_alive(boss, enemies, 210.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby_count >= 2 and hp_ratio < 0.45 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 75)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if nearby_count >= 3 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 160.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if distance > 120.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 50)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			var delta := closest.position - boss.position
			var length := delta.length()
			if length > 1.0:
				var step := minf(length, 110.0)
				boss.position += delta / length * step
				boss.direction = 1 if delta.x > 0.0 else -1
				boss.facing = float(boss.direction)
			for enemy in enemies:
				if boss.position.distance_to(enemy.position) <= 90.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return
	if distance < 150.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest_q := _closest_alive(boss, enemies)
		if closest_q != null and closest_q.alive:
			_hit(world, boss, closest_q, _skill_damage(boss, boss.skill_q_damage))


static func _wiro(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_wiro: R typhoon when 3+ within 200, W whirl when 2+,
	# E dash when HP < 0.5, Q wind cut when dist < 140.
	var nearby_count := _count_near_alive(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby_count >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 140.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return
	if hp_ratio < 0.5 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			var delta := closest.position - boss.position
			var length := delta.length()
			if length > 1.0:
				var step := minf(length, 100.0)
				boss.position += delta / length * step
				boss.direction = 1 if delta.x > 0.0 else -1
				boss.facing = float(boss.direction)
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_e_damage))
		return
	if distance < 140.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 30)
		var closest_q := _closest_alive(boss, enemies)
		if closest_q != null and closest_q.alive:
			_hit(world, boss, closest_q, _skill_damage(boss, boss.skill_q_damage))


static func _naraka(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_naraka: R execute when 3+ within 240 or HP < 0.4,
	# E chain hammer AOE when 2+, W shadowstep when HP < 0.6, Q chaos when dist < 170.
	var nearby_count := _count_near_alive(boss, enemies, 240.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 230.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if hp_ratio < 0.6 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 50)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			var delta := closest.position - boss.position
			var length := delta.length()
			if length > 1.0:
				var step := minf(length, 120.0)
				boss.position += delta / length * step
				boss.direction = 1 if delta.x > 0.0 else -1
				boss.facing = float(boss.direction)
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return
	if distance < 170.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest_q := _closest_alive(boss, enemies)
		if closest_q != null and closest_q.alive:
			_hit(world, boss, closest_q, _skill_damage(boss, boss.skill_q_damage))


static func _krognarr(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_krognarr: R eruption when 3+ within 220 + HP < 0.5,
	# E rampart when HP < 0.55, W seismic AOE when 2+, Q stone strike when dist < 200.
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby_count >= 3 and hp_ratio < 0.5 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 85)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if hp_ratio < 0.55 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 120.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return
	if distance < 200.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest_q := _closest_alive(boss, enemies)
		if closest_q != null and closest_q.alive:
			_hit(world, boss, closest_q, _skill_damage(boss, boss.skill_q_damage))


static func _raz(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_raz: R gloom leap when 3+ within 210, W searing dash when HP < 0.55,
	# E surge AOE when 2+, Q overdrive when dist < 170.
	var nearby_count := _count_near_alive(boss, enemies, 210.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby_count >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if hp_ratio < 0.55 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			var delta := closest.position - boss.position
			var length := delta.length()
			if length > 1.0:
				var step := minf(length, 100.0)
				boss.position += delta / length * step
				boss.direction = 1 if delta.x > 0.0 else -1
				boss.facing = float(boss.direction)
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return
	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 160.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if distance < 170.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest_q := _closest_alive(boss, enemies)
		if closest_q != null and closest_q.alive:
			_hit(world, boss, closest_q, _skill_damage(boss, boss.skill_q_damage))


static func _vraskhan(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_vraskhan: R omni arms when 3+ within 220 or HP < 0.4,
	# W shadow leap when dist > 150 (teleport to target), E death slash AOE when 2+,
	# Q thorned when dist < 160 with dash.
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 85)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if distance > 150.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			boss.position = closest.position + Vector2(0.0, -20.0)
			boss.direction = 1 if closest.position.x > boss.position.x else -1
			boss.facing = float(boss.direction)
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return
	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if distance < 160.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest_q := _closest_alive(boss, enemies)
		if closest_q != null and closest_q.alive:
			var delta := closest_q.position - boss.position
			var length := delta.length()
			if length > 1.0:
				var step := minf(length, 90.0)
				boss.position += delta / length * step
				boss.direction = 1 if delta.x > 0.0 else -1
				boss.facing = float(boss.direction)
			_hit(world, boss, closest_q, _skill_damage(boss, boss.skill_q_damage))


static func _aurethzar(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_aurethzar: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 260.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 250.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 160 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_e_damage))
			_slow(closest, 0.5, 90)
		return

	if distance < 320 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _aeralith(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_aeralith: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 240.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 240.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 320 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _aurex(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_aurex: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby_count >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 75)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if hp_ratio < 0.55 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 130.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if distance < 280 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 160 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _nyxareva(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_nyxareva: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.45):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 85)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if hp_ratio < 0.55 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 170 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _thalakryon(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_thalakryon: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 260.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 260.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if hp_ratio < 0.6 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 340 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _aurelix(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_aurelix: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 240.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 85)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 240.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if hp_ratio < 0.55 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 60)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 320 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _aurelyssa(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_aurelyssa: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.45):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 160.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if hp_ratio < 0.55 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 160 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _vargrath(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_vargrath: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 85)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 230.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if distance > 140.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		var closest_w := _closest_alive(boss, enemies)
		if closest_w != null and closest_w.alive:
			var delta_w := closest_w.position - boss.position
			var length_w := delta_w.length()
			if length_w > 1.0:
				var step_w := minf(length_w, 110.0)
				boss.position += delta_w / length_w * step_w
				boss.direction = 1 if delta_w.x > 0.0 else -1
				boss.facing = float(boss.direction)
			for enemy in enemies:
				if boss.position.distance_to(enemy.position) <= 100.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if distance < 160.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _nazulmor(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_nazulmor: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 270.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 270.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if hp_ratio < 0.6 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 350 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _kaeldris(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_kaeldris: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.45):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if distance > 140 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			var delta := closest.position - boss.position
			var length := delta.length()
			if length > 1.0:
				var step := minf(length, 110.0)
				boss.position += delta / length * step
				boss.direction = 1 if delta.x > 0.0 else -1
				boss.facing = float(boss.direction)
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 160 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _pyraklos(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_pyraklos: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby_count >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 85)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 230.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if hp_ratio < 0.5 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 130.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 180 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _velmyrth(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_velmyrth: auto-generated from base_boss.py
	# R: execute saat ada musuh HP rendah ATAU ramai
	var nearby_count := _count_near_alive(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	var low_target := false
	for enemy in enemies:
		if not enemy.alive:
			continue
		if enemy.hp / maxf(1.0, _max_hp(enemy)) < 0.3:
			low_target = true
			break
	if boss.r_timer == 0 and (low_target or nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if distance > 150 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			boss.position = closest.position + Vector2(0.0, -20.0)
			boss.direction = 1 if closest.position.x > boss.position.x else -1
			boss.facing = float(boss.direction)
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 170.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if distance < 160 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 35)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _solvarin(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_solvarin: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 280.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 280.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if hp_ratio < 0.6 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _azureth(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_azureth: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 270.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 85)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 270.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 400 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _luminar(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_luminar: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 280.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 280.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 410 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _solara(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_solara: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 240.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 240.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 185.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if hp_ratio < 0.65 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		_heal(boss, 0.1)
		return

	if distance < 360.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _pyraethis(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_pyraethis: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 300.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 300.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 430 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _auroth(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_auroth: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 240.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 240.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if hp_ratio < 0.6 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 185.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		_heal(boss, 0.1)
		return

	if distance < 350.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _morvein(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_morvein: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 250.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 250.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _thorvak(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_thorvak: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 250.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 250.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if hp_ratio < 0.65 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if distance < 350 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _yamako(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_yamako: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 300.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 300.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 400 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _ignirus(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_ignirus: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 280.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 280.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 410 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _leoric(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_leoric: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 250.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and hp_ratio < 0.45:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 250.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		_heal(boss, 0.2)
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 350.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _shirotaka(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_shirotaka: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 250.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 250.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _seiryukong(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_seiryukong: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 300.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 300.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 400 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _kaelthorn(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_kaelthorn: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 250.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 250.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _solvanth(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_solvanth: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 260.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 260.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _xyrael(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_xyrael: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 250.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 250.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _nyxareth(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_nyxareth: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 300.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "4", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 300.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "3", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "2", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 420 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "1", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _cryssalia(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_cryssalia: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 280.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 280.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 215.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 420 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _kaelthar(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_kaelthar: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 250.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 250.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _morkhaera(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_morkhaera: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 280.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 280.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 215.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 420 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _aurelion(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_aurelion: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 300.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 300.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 225.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 400 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _akahime(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_akahime: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 270.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 270.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 410 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _nyxthrael(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_nyxthrael: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 260.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 260.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _sylvantheros(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_sylvantheros: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 280.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 280.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 215.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 420 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _vaelindra(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_vaelindra: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 310.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 310.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 230.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 215.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 430 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _astraelion(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_astraelion: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 260.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 260.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 195.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _morvaenthir(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_morvaenthir: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 290.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 290.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 205.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 420 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _thornvaegrim(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_thornvaegrim: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 270.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 270.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 215.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 360 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _morthraxis(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	# Source _smart_ai_morthraxis: auto-generated from base_boss.py
	var nearby_count := _count_near_alive(boss, enemies, 310.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if boss.r_timer == 0 and (nearby_count >= 3 or hp_ratio < 0.4):
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 95)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 310.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return

	if nearby_count >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 65)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 225.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return

	if nearby_count >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 55)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 210.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return

	if distance < 430 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and closest.alive:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
		return


static func _ancient_apparition(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var med_range := _count_near(boss, enemies, 300.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and med_range >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		if target != null and target.alive:
			var dir := (target.position - boss.position).normalized()
			for enemy in enemies:
				var rel := enemy.position - boss.position
				var proj := rel.dot(dir)
				if proj > 0.0 and proj < 500.0:
					var perp := (rel - dir * proj).length()
					if perp < 60.0:
						_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
						_slow(enemy, 0.7, 240)
		return
	if med_range >= 3 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 60)
		boss.vortex_origin = (
			target.position if target != null and target.alive else boss.position + Vector2(100, 0)
		)
		boss.vortex_active_timer = 180
		for enemy in enemies:
			if enemy.position.distance_to(boss.vortex_origin) <= 80.0:
				_hit(world, boss, enemy, int(_skill_damage(boss, boss.skill_q_damage) / 2.0))
		return
	if distance > 250.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 50)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))
		_attack_lock(target, 90)
		return
	if distance < 320.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 45)
		if target != null and target.alive:
			var dir := (target.position - boss.position).normalized()
			for enemy in enemies:
				var rel := enemy.position - boss.position
				var proj := rel.dot(dir)
				if proj > 0.0 and proj < 400.0:
					var perp := (rel - dir * proj).length()
					if perp < 30.0:
						_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
						_slow(enemy, 0.6, 180)


static func _ignis_drachorn(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 180.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.5 and nearby >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		boss.dragon_form_active = true
		boss.dragon_form_timer = 600
		boss.damage = int(float(_source_damage(boss)) * 1.8)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 90)
		_heal(boss, 0.25)
		return
	if hp_ratio < 0.65 and not boss.dragon_blood_active and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		boss.dragon_blood_active = true
		boss.dragon_blood_timer = 480
		boss.damage = int(float(_source_damage(boss)) * 1.3)
		_heal(boss, 0.20)
		return
	if nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 130.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				_attack_lock(enemy, 60)
		return
	if distance < 220.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		if target != null and target.alive:
			var dir := (target.position - boss.position).normalized()
			for enemy in enemies:
				var rel := enemy.position - boss.position
				var proj := rel.dot(dir)
				if proj > 0.0 and proj < 250.0:
					var perp := (rel - dir * proj).length()
					var allowed := 60.0 * (0.3 + proj / 250.0 * 0.7)
					if perp < allowed:
						_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))
						_attack_lock(enemy, 45)


static func _vhorethzir(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and nearby >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 100)
		var closest := _closest_alive(boss, enemies)
		var cx := closest.position if closest != null else boss.position
		for enemy in enemies:
			if enemy.position.distance_to(cx) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 120)
				_slow(enemy, 0.65, 300)
		_heal(boss, 0.12)
		return
	if hp_ratio < 0.6 and not boss.corrosive_active and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 80)
		boss.corrosive_active = true
		boss.corrosive_timer = 360
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_attack_lock(enemy, 90)
				_slow(enemy, 0.5, 240)
		_heal(boss, 0.10)
		return
	if nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 90)
		var closest := _closest_alive(boss, enemies)
		if closest != null:
			for enemy in enemies:
				if enemy.position.distance_to(closest.position) <= 110.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
					_attack_lock(enemy, 60)
					_slow(enemy, 0.6, 180)
		return
	if distance < 280.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and boss.position.distance_to(closest.position) <= 300.0:
			for enemy in enemies:
				if enemy.position.distance_to(closest.position) <= 70.0:
					var falloff := 1.0 if enemy == closest else 0.6
					_hit(
						world,
						boss,
						enemy,
						int(float(_skill_damage(boss, boss.skill_q_damage)) * falloff)
					)
					_attack_lock(enemy, 45)


static func _vaerith(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.45 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 100)
				_slow(enemy, 0.6, 240)
		_heal(boss, 0.15)
		return
	if hp_ratio < 0.7 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 55)
		var closest := _closest_alive(boss, enemies)
		if closest != null and boss.position.distance_to(closest.position) <= 220.0:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_e_damage))
			_attack_lock(closest, 60)
			var heal_amount := int(float(_skill_damage(boss, boss.skill_e_damage)) * 0.6)
			boss.hp = minf(float(boss.max_hp), boss.hp + float(heal_amount))
		return
	if nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 70)
		var closest := _closest_alive(boss, enemies)
		var cx := closest.position if closest != null else boss.position
		for enemy in enemies:
			if enemy.position.distance_to(cx) <= 90.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				_attack_lock(enemy, 75)
				_slow(enemy, 0.7, 240)
		return
	if distance < 260.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		var closest := _closest_alive(boss, enemies)
		if closest != null and boss.position.distance_to(closest.position) <= 280.0:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_q_damage))
			_attack_lock(closest, 40)


static func _xirthalis(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 60)
		var mark := boss.timelapse_hp_mark
		if mark <= 0.0:
			mark = float(boss.max_hp) * 0.5
		if mark > boss.hp:
			boss.hp = minf(float(boss.max_hp), mark)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 160.0:
				_attack_lock(enemy, 90)
				_slow(enemy, 0.5, 180)
		return
	if hp_ratio < 0.65 and not boss.shukuchi_active and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 60)
		boss.shukuchi_active = true
		boss.shukuchi_timer = 180
		return
	if nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 70)
		var closest := _closest_alive(boss, enemies)
		var cx := closest.position if closest != null else boss.position
		for enemy in enemies:
			if enemy.position.distance_to(cx) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				_attack_lock(enemy, 60)
				_slow(enemy, 0.6, 200)
		return
	if distance < 250.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 45)
		var closest := _closest_alive(boss, enemies)
		if closest != null and boss.position.distance_to(closest.position) <= 270.0:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_e_damage))
			if closest.alive:
				_hit(
					world, boss, closest, int(float(_skill_damage(boss, boss.skill_e_damage)) * 0.6)
				)
			_attack_lock(closest, 50)


static func _vhyssarion(
	world, boss: BossState, enemies: Array[UnitState], _target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.45 and nearby >= 2 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 110)
				_slow(enemy, 0.6, 260)
		return
	if nearby >= 2 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 90)
		var closest := _closest_alive(boss, enemies)
		var cx := closest.position if closest != null else boss.position
		for enemy in enemies:
			if enemy.position.distance_to(cx) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))
				_attack_lock(enemy, 70)
				_slow(enemy, 0.65, 240)
		return
	if nearby >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 70)
		var closest := _closest_alive(boss, enemies)
		var cx := closest.position if closest != null else boss.position
		for enemy in enemies:
			if enemy.position.distance_to(cx) <= 85.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
				_attack_lock(enemy, 80)
				_slow(enemy, 0.75, 200)
		return
	if distance < 270.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		var closest := _closest_alive(boss, enemies)
		if closest != null and boss.position.distance_to(closest.position) <= 300.0:
			_hit(world, boss, closest, _skill_damage(boss, boss.skill_w_damage))
			_attack_lock(closest, 55)
			_slow(closest, 0.5, 180)


static func _khalros(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 140.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 70)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_attack_lock(enemy, 30)
		return
	if hp_ratio < 0.7 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 120.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				_slow(enemy, 0.5, 90)
		_heal(boss, 0.08)
		return
	if distance > 110.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 45)
		if target != null and target.alive:
			var delta := target.position - boss.position
			var length := delta.length()
			if length > 0.0:
				var charge := minf(90.0, maxf(35.0, length - 45.0))
				boss.position += delta / length * charge
				boss.direction = 1 if delta.x > 0.0 else -1
			for enemy in enemies:
				if boss.position.distance_to(enemy.position) <= 85.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
					_attack_lock(enemy, 40)
		return
	if distance <= 260.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		if target != null and target.alive:
			for enemy in enemies:
				if enemy.position.distance_to(target.position) <= 70.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))


static func _gorath(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 150.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	var low_hp_target := false
	if target != null and target.alive:
		var t_max := _max_hp(target)
		if target.hp / maxf(1.0, t_max) < 0.35:
			low_hp_target = true
	if low_hp_target and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		if target != null and target.alive:
			_hit(world, boss, target, int(_skill_damage(boss, boss.skill_r_damage) / 2.0))
		return
	if not boss.rage_active and hp_ratio < 0.7 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 90)
		boss.rage_active = true
		boss.rage_timer = 300
		boss.damage = int(float(_source_damage(boss)) * 1.4)
		_heal(boss, 0.08)
		return
	if nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 150.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
				_attack_lock(enemy, 50)
		return
	if distance > 90.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 35)
		if target != null and target.alive:
			var delta := target.position - boss.position
			var length := delta.length()
			if length > 0.0:
				var leap := minf(120.0, maxf(45.0, length - 35.0))
				boss.position += delta / length * leap
				boss.direction = 1 if delta.x > 0.0 else -1
			for enemy in enemies:
				if boss.position.distance_to(enemy.position) <= 85.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if hp_ratio < 0.45 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 190.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		if target != null and target.alive:
			_hit(world, boss, target, int(_skill_damage(boss, boss.skill_r_damage) / 2.0))


static func _varkul(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if nearby >= 3 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_slow(enemy, 0.5, 180)
		return
	if hp_ratio < 0.5 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))
		_heal(boss, 0.12)
		return
	if distance <= 250.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 60)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_w_damage))
			_attack_lock(target, 60)
		return
	if distance <= 280.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))
			_slow(target, 0.4, 120)


static func _xerathis(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 220.0)
	if nearby >= 4 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 100)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 240.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_slow(enemy, 0.55, 240)
		return
	if not boss.arcane_buff_active and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 90)
		boss.arcane_buff_active = true
		boss.arcane_buff_timer = 360
		boss.damage = int(float(boss.base_damage) * 1.3)
		_heal(boss, 0.10)
		return
	if nearby >= 2 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 60)
		if target != null and target.alive:
			for enemy in enemies:
				if enemy.position.distance_to(target.position) <= 90.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))
					_slow(enemy, 0.4, 120)
		return
	if distance <= 280.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_w_damage))
			_attack_lock(target, 75)
			_slow(target, 0.6, 180)


static func _nyzrak(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 180.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.45 and not boss.shield_active and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		boss.shield_active = true
		boss.shield_timer = 240
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 200.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
				_slow(enemy, 0.5, 180)
		_heal(boss, 0.15)
		return
	if distance <= 220.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 70)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))
			_attack_lock(target, 90)
			_slow(target, 0.7, 180)
		return
	if nearby >= 2 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 50)
		if target != null and target.alive:
			for enemy in enemies:
				if enemy.position.distance_to(target.position) <= 80.0:
					_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return
	if distance <= 260.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))
			_slow(target, 0.4, 120)


static func _zharok(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if nearby >= 2 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 150.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if distance < 200.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		return
	if distance < 250.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _pyrenth(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 180.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.4 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 70)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if nearby >= 3 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if hp_ratio < 0.6 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 40)
		_heal(boss, 0.08)
		return
	if distance < 200.0 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _vokrahn(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 200.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.5 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, 150)
		return
	if nearby >= 3 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 220.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return
	if distance < 200.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))
		return
	if boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 50)
		if target != null and target.alive:
			_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _nyxara(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if target != null and hp_ratio < 0.55 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 90)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_r_damage))
		_heal(boss, 0.135)
		return
	if nearby >= 3 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 100.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_e_damage))
		return
	if target != null and distance <= 280.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 70)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_w_damage))
		_attack_lock(target, 75)
		return
	if target != null and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 60)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_q_damage))


static func _gravefang(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	var nearby := _count_near(boss, enemies, 180.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if (nearby >= 3 or hp_ratio < 0.35) and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 100)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 180.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_r_damage))
		return
	if target != null and distance > 90.0 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 70)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_w_damage))
		return
	if target != null and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 70)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))
		_attack_lock(target, 60)
		return
	if nearby >= 2 and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 120.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))


static func _vhalzun(
	world, boss: BossState, enemies: Array[UnitState], target: UnitState, distance: float
) -> void:
	if boss.active_skill != "":
		return
	var nearby := _count_near(boss, enemies, 220.0)
	var hp_ratio := boss.hp / maxf(1.0, float(boss.max_hp))
	if hp_ratio < 0.40 and boss.r_timer == 0:
		boss.r_timer = boss.skill_r_cooldown
		_set_skill(boss, "r", 100)
		_heal(boss, 0.18)
		return
	if nearby >= 3 and boss.w_timer == 0:
		boss.w_timer = boss.skill_w_cooldown
		_set_skill(boss, "w", 80)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 150.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_w_damage))
		return
	if target != null and distance > 96.0 and boss.e_timer == 0:
		boss.e_timer = boss.skill_e_cooldown
		_set_skill(boss, "e", 60)
		_hit(world, boss, target, _skill_damage(boss, boss.skill_e_damage))
		return
	if target != null and boss.q_timer == 0:
		boss.q_timer = boss.skill_q_cooldown
		_set_skill(boss, "q", 60)
		for enemy in enemies:
			if boss.position.distance_to(enemy.position) <= 130.0:
				_hit(world, boss, enemy, _skill_damage(boss, boss.skill_q_damage))


static func _set_skill(boss: BossState, key: String, duration: int) -> void:
	boss.active_skill = key
	boss.active_skill_timer = duration


static func _count_near(boss: BossState, enemies: Array[UnitState], radius: float) -> int:
	var result := 0
	for enemy in enemies:
		if boss.position.distance_to(enemy.position) <= radius:
			result += 1
	return result


static func _count_near_alive(boss: BossState, enemies: Array[UnitState], radius: float) -> int:
	var result := 0
	for enemy in enemies:
		if not enemy.alive:
			continue
		if boss.position.distance_to(enemy.position) <= radius:
			result += 1
	return result


static func _closest_alive(boss: BossState, enemies: Array[UnitState]) -> UnitState:
	var best: UnitState = null
	var best_distance := INF
	for enemy in enemies:
		if not enemy.alive:
			continue
		var distance := boss.position.distance_to(enemy.position)
		if distance < best_distance:
			best_distance = distance
			best = enemy
	return best


static func _skill_damage(boss: BossState, base: int) -> int:
	var multiplier := 1.0
	if boss.skill_down_timer > 0:
		multiplier *= maxf(0.0, 1.0 - boss.skill_down_amount)
	multiplier *= boss.dmg_scaling_mult
	if boss.is_enraged:
		multiplier *= 1.25
	return Damage.rounded_like_python(float(base) * multiplier)


static func _source_damage(boss: BossState) -> int:
	var multiplier := 1.0
	if boss.skill_down_timer > 0:
		multiplier *= maxf(0.0, 1.0 - boss.skill_down_amount)
	if boss.is_enraged:
		multiplier *= 1.25
	return Damage.rounded_like_python(float(boss.base_damage) * multiplier)


static func _max_hp(target: UnitState) -> float:
	if target is HeroState:
		return (target as HeroState).max_hp
	return target.definition.max_hp


static func _heal(boss: BossState, fraction: float) -> void:
	boss.hp = minf(float(boss.max_hp), boss.hp + int(float(boss.max_hp) * fraction))


static func _hit(world, boss: BossState, target: UnitState, raw_damage: int) -> void:
	if target == null or not target.alive or raw_damage <= 0:
		return
	var school := "physical" if target is HeroState else "neutral"
	world._deliver_hit(boss.id, boss.team, target, raw_damage, school, boss.position)


static func _slow(target: UnitState, amount: float, duration: int) -> void:
	if target == null or not target.alive or target is StructureState:
		return
	if amount > target.slow_amount or target.slow_timer < duration:
		target.slow_amount = amount
		target.slow_timer = duration


static func _attack_lock(target: UnitState, duration: int) -> void:
	if target == null or not target.alive or target is StructureState:
		return
	if target is HeroState:
		var hero := target as HeroState
		hero.attack_timer = maxi(hero.attack_timer, duration)
	else:
		target.cooldown_ticks = maxi(target.cooldown_ticks, duration)
