# CombatSystem.gd — Autoload. Port pipeline damage _entity.py + hero_items.py.
#
# Urutan penyelesaian damage (paritas Hero.take_damage pygame 4550-4712):
#   1. buff penghindar  : Windrun (Sylara W) 75% meleset fisik,
#                         Wind Wall (Kaizen W) memblokir tipe "projectile",
#                         Shadow Realm (Zephyr W) tidak bisa ditarget
#   2. evasion / blind  : item evasion (cap 50%) + aura blind (Solar Brand)
#   3. block            : Scarlet Bulwark (chance 55%, 25 melee / 14 ranged)
#   4. armor shred      : Corroder (-6 armor) lalu mitigasi armor/magic resist
#   5. dmg_amp          : debuff yang menaikkan damage diterima
#   6. Bristleback      : Thorne W menahan 30% fisik / 15% sihir
#   7. hp berkurang     : + damage number
#   8. reflect 25%      : Bristleback memantulkan ke penyerang (source diputus)
#   9. lifesteal/cleave : Demon Maw / Cleave Axe milik penyerang
extends Node

const DAMAGE_NUMBER_SCENE := preload("res://scenes/fx/DamageNumber.tscn")

## Group yang dianggap "unit" saat mencari musuh (nexus = base yang bisa dihancurkan)
const UNIT_GROUPS: Array = ["heroes", "bosses", "minions", "towers", "nexus"]


# ══════════════════════════════════════════════════════════
#  QUERY UNIT
# ══════════════════════════════════════════════════════════

## Semua unit hidup milik satu tim (dipakai skill AOE, aura, AI)
func units_of(team: String) -> Array:
	var out: Array = []
	for group in UNIT_GROUPS:
		for n in get_tree().get_nodes_in_group(group):
			if not is_instance_valid(n) or not (n is Node2D):
				continue
			if str(n.get("team")) != team:
				continue
			if bool(n.get("is_dead")):
				continue
			out.append(n)
	return out


## Semua musuh hidup dari sudut pandang `team`
func enemies_of(team: String) -> Array:
	var out: Array = []
	for group in UNIT_GROUPS:
		for n in get_tree().get_nodes_in_group(group):
			if not is_instance_valid(n) or not (n is Node2D):
				continue
			if str(n.get("team")) == team:
				continue
			if bool(n.get("is_dead")):
				continue
			if not _targetable(n):
				continue
			out.append(n)
	return out


## Musuh dalam radius dari sebuah titik
func enemies_in_radius(team: String, center: Vector2, radius: float) -> Array:
	var out: Array = []
	for e in enemies_of(team):
		if (e as Node2D).global_position.distance_to(center) <= radius:
			out.append(e)
	return out


static func _targetable(unit) -> bool:
	var st = unit.get("status")
	if st != null and st.has_method("can_be_targeted"):
		return st.can_be_targeted()
	return true


## Unit terdekat yang bisa diserang (paritas _find_hunt_target: murni jarak)
func nearest_enemy(unit, max_distance: float) -> Node2D:
	var best: Node2D = null
	var best_d := max_distance
	var from: Vector2 = unit.global_position
	for e in enemies_of(str(unit.get("team"))):
		var d: float = from.distance_to((e as Node2D).global_position)
		if d < best_d:
			best_d = d
			best = e as Node2D
	return best


# ══════════════════════════════════════════════════════════
#  DAMAGE PENYERANG (sebelum mitigasi)
# ══════════════════════════════════════════════════════════

## Damage basic attack: bonus item + buff skill + crit (Dead Edge / Critical Strike)
func calc_damage(attacker: Node, _defender: Node, base: float, _school: String) -> float:
	var dmg := base
	# Buff skill: Warpath (Thorne R) menaikkan damage ×1.5
	var st = attacker.get("status")
	if st != null:
		dmg *= st.damage_mult()
	# Critical Strike (Grimjaw E): basic attack ×2 selama buff
	if st != null and st.has_buff("crit"):
		return dmg * st.buff_val("crit", "mult", 2.0)
	# Item: bonus damage flat + crit Dead Edge
	var inv = attacker.get("items")
	if inv != null:
		dmg += inv.get_bonus_damage()
		var roll: Array = inv.roll_crit()
		if roll[0]:
			dmg *= float(roll[1])
	return dmg


## Damage skill: skill_damage hero × amplifier item × skill_down (Mage Tower)
func calc_skill_damage(attacker: Node, multiplier: float) -> float:
	var base := float(attacker.get("skill_damage"))
	var out := base * multiplier
	var inv = attacker.get("items")
	if inv != null:
		out *= 1.0 + inv.get_skill_amp()
	var st = attacker.get("status")
	if st != null:
		out *= st.skill_damage_mult()
	return maxf(0.0, out)


# ══════════════════════════════════════════════════════════
#  MITIGASI
# ══════════════════════════════════════════════════════════

func mitigate_damage(defender: Node, amount: float, school: String) -> float:
	var armor := float(defender.get("armor")) if "armor" in defender else 0.0
	var mr := float(defender.get("magic_resist")) if "magic_resist" in defender else 0.0
	# Debuff armor shred (Corroder) — armor bisa jadi negatif (damage bonus)
	var st = defender.get("status")
	if st != null:
		armor += st.armor_delta()
	return DamageSchool.mitigate(amount, armor, mr, school)


# ══════════════════════════════════════════════════════════
#  PIPELINE UTAMA
# ══════════════════════════════════════════════════════════

## Terapkan damage ke `target`. Return damage yang benar-benar mengurangi HP.
## `target.hp` diubah di sini supaya urutan mitigasi/reflect identik dengan pygame.
func apply_damage(target, amount: float, from_team: String = "",
		dmg_type: String = "normal", source = null, school: String = "") -> float:
	if target == null or not is_instance_valid(target):
		return 0.0
	if bool(target.get("is_dead")):
		return 0.0
	if amount <= 0.0:
		return 0.0

	# Tidak ada friendly fire di pygame: damage selalu datang dari tim lawan.
	# Guard ini juga membuat `from_team` benar-benar dipakai (bukan hiasan).
	if from_team != "" and str(target.get("team")) == from_team:
		return 0.0

	var st = target.get("status")
	# Sekolah damage = milik PENYERANG, bukan target (paritas
	# resolve_damage_school di _entity.py 106-131: school eksplisit ->
	# dmg_type dot yang netral -> source.dmg_school). Versi sebelumnya salah
	# mengambil dmg_school TARGET, sehingga serangan fisik ke hero berschool
	# magic ikut dianggap magic dan menembus armor.
	var eff_school := DamageSchool.resolve(school, dmg_type, source)
	var is_physical := DamageSchool.is_physical_hit(dmg_type, eff_school)

	# ── 0. Tempest Veil: KEBAL total selama aktif ──
	# Item aktif auto-trigger saat HP < 40% (hero_items.py:2188-2194). pygame
	# memotong damage paling awal dan menampilkan "IMMUNE" alih-alih angka
	# (_entity.py:4589-4600), jadi dicek sebelum mitigasi apa pun.
	var tv = target.get("items")
	if tv != null and tv.has_method("is_veiled") and tv.is_veiled():
		_float_text(target, "IMMUNE", false)
		return 0.0

	# ── 1. buff penghindar ──
	if st != null:
		# Wind Wall (Kaizen W): projectile fisik dipantulkan mentah-mentah
		if st.has_buff("wind_wall") and dmg_type == "projectile" and eff_school != "magic":
			_float_text(target, "WALL", false)
			return 0.0
		# Windrun (Sylara W): 75% serangan fisik meleset
		if st.has_buff("windrun") and is_physical and randf() < 0.75:
			_float_text(target, "WIND", false)
			return 0.0
		# evasion item + blind aura
		var miss: float = st.miss_chance(is_physical)
		if miss > 0.0 and randf() < miss:
			_float_text(target, "MISS", false)
			return 0.0

	# ── 2. block (Scarlet Bulwark) ──
	var inv = target.get("items")
	if inv != null and is_physical:
		var blk: Array = inv.get_block(dmg_type == "normal")
		if float(blk[0]) > 0.0 and randf() < float(blk[0]):
			amount = maxf(1.0, amount - float(blk[1]))
			_float_text(target, "BLOCK", false)

	# ── 3. mitigasi armor / magic resist (+ shred) ──
	var dmg := mitigate_damage(target, amount, eff_school)

	# ── 4. debuff yang menaikkan damage diterima ──
	if st != null:
		dmg *= st.incoming_mult()

	# ── 5. Bristleback (Thorne W): duri menahan 30% fisik / 15% sihir ──
	if st != null and st.has_buff("bristleback"):
		var keep := 0.70 if eff_school != "magic" else 0.85
		dmg = maxf(1.0, round(dmg * keep))

	# ── 5b. BOSS resilience + anti-burst (base_boss.py take_damage 6025-6037):
	# damage_reduction (true 30% / mini 20%) lalu cap per hit (8% / 12% max
	# HP). Boss adalah satu-satunya unit yang punya metode ini.
	if target != null and is_instance_valid(target) \
			and target.has_method("apply_boss_inherent_mitigation"):
		dmg = target.apply_boss_inherent_mitigation(dmg)

	dmg = maxf(0.0, dmg)
	if dmg <= 0.0:
		return 0.0

	# ── 6. kurangi HP (shield tower/nexus menyerap lebih dulu) ──
	var shield_pass: Array = _shield_pass(target, dmg)
	var absorbed := float(shield_pass[0])
	dmg = float(shield_pass[1])
	if dmg > 0.0:
		target.hp = float(target.get("hp")) - dmg
	var dealt := dmg
	var shown := dealt + absorbed
	_spawn_damage_number(target, shown, shown > float(target.get("max_hp")) * 0.12)

	# ── 7. reset timer regen (tower/nexus: no_damage_timer, hero: combat_timer) ──
	if "combat_timer" in target:
		target.combat_timer = float(target.get("combat_reset"))

	# ── 8. reflect Bristleback 25% (source diputus: tidak bisa loop) ──
	if st != null and st.has_buff("bristleback") and dealt > 0.0 \
			and source != null and is_instance_valid(source) and source != target \
			and str(source.get("team")) != str(target.get("team")):
		apply_damage(source, maxf(1.0, floor(dealt * 0.25)), str(target.get("team")),
			"normal", null, "")

	# ── 8b. Thornmail (razor_carapace) — pantulkan reflect_pct damage ──
	# Item aktif auto-trigger saat HP < 55% (hero_items.py:2266-2273). Sama
	# seperti Bristleback di atas, `source` diputus (pakai "" bukan source)
	# supaya pantulan tidak memantul balik jadi loop tak berujung.
	var tinv = target.get("items")
	if tinv != null and dealt > 0.0 and source != null and is_instance_valid(source) \
			and source != target and str(source.get("team")) != str(target.get("team")) \
			and tinv.has_method("get_active_reflect_pct"):
		var rpct := float(tinv.get_active_reflect_pct())
		if rpct > 0.0:
			apply_damage(source, maxf(1.0, floor(dealt * rpct)),
				str(target.get("team")), "normal", null, "")

	# ── 9. lifesteal + cleave penyerang ──
	if source != null and is_instance_valid(source) and dealt > 0.0:
		_on_attacker_hit(source, target, dealt, is_physical)

	return dealt


## Shield menyerap damage 1:1 lebih dulu (paritas Tower.take_damage 476-487 dan
## Castle.take_damage 201-225). Castle punya lapisan kedua: sisa damage tetap
## dipotong CASTLE_SHIELD_DAMAGE_REDUCTION (88%) selama shield_active.
## Return [diserap_shield, damage_yang_masuk_hp].
func _shield_pass(target, dmg: float) -> Array:
	if not ("shield" in target):
		return [0.0, dmg]
	if "no_damage_timer" in target:
		target.no_damage_timer = 0.0
	if "shield_active" in target and not bool(target.get("shield_active")):
		return [0.0, dmg]
	var shield := float(target.get("shield"))
	var remaining := dmg
	var absorbed := 0.0
	if shield > 0.0:
		absorbed = minf(shield, remaining)
		target.shield = shield - absorbed
		remaining -= absorbed
	if remaining > 0.0 and "shield_damage_reduction" in target:
		remaining *= 1.0 - float(target.get("shield_damage_reduction"))
	return [absorbed, remaining]


func _on_attacker_hit(attacker, target, dealt: float, is_physical: bool) -> void:
	var inv = attacker.get("items")
	if inv == null:
		return
	# Lifesteal (Demon Maw / Vampiric)
	var ls := float(inv.get_lifesteal_pct())
	if ls > 0.0:
		heal_unit(attacker, dealt * ls)
	# Cleave (Cleave Axe, melee only): 50% damage ke musuh lain radius 110
	var cleave: Array = inv.get_cleave()
	if cleave.size() == 2 and is_physical:
		var splash := int(dealt * float(cleave[0]))
		if splash > 0:
			var center: Vector2 = (target as Node2D).global_position
			for e in enemies_in_radius(str(attacker.get("team")), center, float(cleave[1])):
				if e == target:
					continue
				apply_damage(e, float(splash), str(attacker.get("team")),
					"normal", null, "physical")
	# Corroder: kikis armor target
	var shred := float(inv.get_armor_shred())
	if shred > 0.0:
		var tst = target.get("status")
		if tst != null:
			tst.apply_armor_shred(shred, 360.0 / 60.0)


## Heal yang melewati anti-heal / heal_amp (paritas property `hp` setter pygame)
func heal_unit(unit, amount: float) -> float:
	if amount <= 0.0 or unit == null or not is_instance_valid(unit):
		return 0.0
	if bool(unit.get("is_dead")):
		return 0.0
	var st = unit.get("status")
	var healed := amount
	if st != null:
		healed = st.heal_amount(amount)
	if healed <= 0.0:
		return 0.0
	var max_hp := float(unit.get("max_hp"))
	var before := float(unit.get("hp"))
	unit.hp = minf(max_hp, before + healed)
	return float(unit.get("hp")) - before


# ══════════════════════════════════════════════════════════
#  AURA ITEM (Steel Aegis / Everfrost Guard / Solar Brand / Searbrand)
# ══════════════════════════════════════════════════════════

## Dipanggil GameManager ~4x/detik. pygame: hero_items.update_auras() tiap frame.
func update_auras() -> void:
	var all: Array = units_of("blue") + units_of("red")
	# reset aura yang diterima
	for u in all:
		var inv = u.get("items")
		if inv == null:
			continue
		inv.aura_armor = 0.0
		inv.aura_attack_speed = 0.0
		inv.aura_armor_reduction = 0.0
		inv.aura_atk_slow = 0.0
		inv.aura_anti_heal = 0.0
		inv.aura_burn_dps = 0.0
		inv.aura_blind = 0.0
		inv.aura_guard_block = 0.0
	# ── Bulwark Guard lebih dulu, sebelum aura biasa ──
	# pygame menghitungnya DULUAN dan terpisah dari Steel Aegis
	# (hero_items.py:2774-2795): hero ber-scarlet_bulwark yang guard-nya
	# menyala memberi block ke DIRINYA + sekutu dalam ally_radius.
	# aura_guard_block sudah lama ada di ItemInventory.get_block() tapi tak
	# pernah diisi siapa pun — nilainya selalu 0 sampai sekarang.
	for u in all:
		var ginv = u.get("items")
		if ginv == null or not ginv.has_method("is_guarding") or not ginv.is_guarding():
			continue
		var gdb = ItemDB.get_item("scarlet_bulwark")
		var gact = gdb.get("active")
		if not (gact is Dictionary):
			continue
		var g_radius := float(gact.get("ally_radius", 320.0))
		var g_team := str(u.get("team"))
		var g_pos: Vector2 = u.global_position
		for ally in all:
			if str(ally.get("team")) != g_team:
				continue
			if (ally as Node2D).global_position.distance_to(g_pos) > g_radius:
				continue
			var ainv = ally.get("items")
			if ainv == null:
				continue
			# block = base_block + max_hp_block_pct × Max HP sekutu
			var amt := float(gact.get("base_block", 0.0)) \
				+ float(gact.get("max_hp_block_pct", 0.0)) * float(ally.get("max_hp"))
			ainv.aura_guard_block = maxf(float(ainv.aura_guard_block), amt)
	# pancarkan
	for u in all:
		var inv = u.get("items")
		if inv == null:
			continue
		var auras: Array = inv.get_emitted_auras()
		if auras.is_empty():
			continue
		var pos: Vector2 = u.global_position
		var team := str(u.get("team"))
		for aura in auras:
			_apply_aura(u, aura, pos, team, all)


func _apply_aura(_caster, aura: Dictionary, pos: Vector2, team: String, all: Array) -> void:
	var ally_r := float(aura.get("ally_radius", 0))
	var enemy_r := float(aura.get("enemy_radius", 0))
	for u in all:
		if not is_instance_valid(u):
			continue
		var d: float = pos.distance_to(u.global_position)
		var inv = u.get("items")
		if inv == null:
			continue
		if str(u.get("team")) == team:
			if ally_r > 0.0 and d <= ally_r:
				inv.aura_armor += float(aura.get("ally_armor", 0))
				inv.aura_attack_speed += float(aura.get("ally_attack_speed", 0))
		else:
			if enemy_r > 0.0 and d <= enemy_r:
				inv.aura_armor_reduction += float(aura.get("enemy_armor_reduction", 0))
				var st = u.get("status")
				if st == null:
					continue
				var atk_slow := float(aura.get("enemy_atk_slow", 0))
				if atk_slow > 0.0:
					st.apply_attack_slow(atk_slow, 0.6)
				var anti_heal := float(aura.get("enemy_anti_heal", 0))
				if anti_heal > 0.0:
					st.apply_anti_heal(anti_heal, 0.6)
				var burn := float(aura.get("burn_dps", 0))
				if burn > 0.0:
					st.apply_burn(burn, 0.6, team)
				var blind := float(aura.get("blind", 0))
				if blind > 0.0:
					st.apply_blind(blind, 0.6)


# ══════════════════════════════════════════════════════════
#  FX TEKS
# ══════════════════════════════════════════════════════════

func _spawn_damage_number(target, amount: float, big: bool) -> void:
	if amount < 1.0:
		return
	_float_text(target, str(int(round(amount))), big)


func _float_text(target, text: String, big: bool) -> void:
	var tree := get_tree()
	if tree == null:
		return
	var host: Node = tree.current_scene
	if host == null:
		host = target
	var num = DAMAGE_NUMBER_SCENE.instantiate()
	num.setup(text, big)
	var radius := float(target.get("radius")) if "radius" in target else 16.0
	num.global_position = (target as Node2D).global_position \
		+ Vector2(randf_range(-radius * 0.6, radius * 0.6), -radius - 22.0)
	host.add_child(num)
