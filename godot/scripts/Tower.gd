extends Node2D
class_name TowerUnit
## TowerUnit — Menara Pertahanan MOBA (Paritas 1:1 Pygame _entity.Tower & TowerDB)
## Mendukung 4 Jalur Menara (Archer, Cannon, Ice, Mage), 6 Level,
## Mekanik Tower Aggro / Tower Dive Protection, Armor Mitigasi, dan Shield.

signal destroyed(tower: TowerUnit)

# ═══ IDENTITAS & STAT ═══
var tower_id: String = "archer"
var tower_type: String = "archer"
var tower_name: String = "Archer Tower"
var team: String = "blue"
var level: int = 1
var slot_index: int = -1
var tower_kind: String = "outer" # "outer" (100G) atau "inner" (150G)

var max_hp: float = 2000.0
var hp: float = 2000.0
var shield_max: float = 800.0
var shield: float = 800.0
var damage: float = 20.0
var attack_range: float = 180.0
var attack_cooldown: float = 0.58
var armor: float = 3.0
var magic_resist: float = 0.0
var gold_reward: int = 100

# ═══ EFEK KHUSUS & TOWER DEBUFF ═══
var splash: float = 0.0
var burn_dps: float = 0.0
var burn_duration: float = 0.0
var slow: float = 0.0
var slow_duration: float = 0.0
var slow_aoe: float = 0.0
var atk_slow: float = 0.0
var chain: int = 1
var double_shot: bool = false
var skill_down: float = 0.0
var anti_heal: float = 0.0
var debuff_duration: float = 0.0

# ═══ STATE & TARGETING ═══
var target = null
var aggro_target = null          # Target prioritas akibat Tower Dive (musuh memukul hero kawan)
var _cooldown: float = 0.0
var _no_damage_timer: float = 0.0 # Timer untuk HP/Shield out-of-combat regen (5 detik)
var _shot_to: Vector2 = Vector2.ZERO
var _shot_t: float = 0.0
var _flash: float = 0.0
var _chain_targets: Array = []   # Array Vector2 untuk proyektil rantai petir Mage

# ═══ FLOATING TEXT ═══
var _float_texts: Array = []


func _ready() -> void:
	add_to_group("towers")


func setup(data: Dictionary, team_name: String, start_pos: Vector2, p_slot: int = -1) -> void:
	team = team_name
	position = start_pos
	slot_index = p_slot
	tower_type = str(data.get("tower_type", data.get("id", "archer")))
	level = int(data.get("level", 1))
	tower_kind = str(data.get("tower_kind", "outer"))
	gold_reward = 150 if tower_kind == "inner" else 100

	_apply_stats()
	queue_redraw()


func _apply_stats() -> void:
	# Formula stat paritas TowerDB / _core.py
	match tower_type:
		"archer":
			tower_name = "Archer Tower"
			match level:
				1: _set_stats(2000, 20, 180, 0.58, 3, false)
				2: _set_stats(2625, 33, 190, 0.53, 4, false)
				3: _set_stats(3375, 50, 200, 0.50, 5, false)
				4: _set_stats(4375, 72, 210, 0.45, 6, false)
				5: _set_stats(5500, 98, 220, 0.40, 7, false)
				_: _set_stats(7000, 130, 230, 0.37, 8, true) # Double shot Lv6
		"cannon":
			tower_name = "Cannon Tower"
			match level:
				2: _set_cannon(3000, 42, 165, 0.73, 4, 45, 8.0, 2.0)
				3: _set_cannon(3750, 60, 175, 0.67, 5, 55, 12.0, 2.5)
				4: _set_cannon(4750, 84, 185, 0.60, 6, 65, 16.0, 2.5)
				5: _set_cannon(6000, 116, 195, 0.53, 7, 80, 22.0, 3.0)
				_: _set_cannon(7500, 155, 210, 0.47, 8, 100, 30.0, 3.0)
		"ice":
			tower_name = "Ice Tower"
			match level:
				2: _set_ice(2375, 20, 170, 0.43, 4, 0.25, 0.15, 1.5, 0.0)
				3: _set_ice(3125, 32, 180, 0.37, 5, 0.35, 0.20, 1.6, 0.0)
				4: _set_ice(4000, 45, 190, 0.30, 6, 0.45, 0.25, 1.8, 0.0)
				5: _set_ice(5125, 60, 200, 0.27, 7, 0.55, 0.30, 2.0, 0.0)
				_: _set_ice(6500, 78, 220, 0.23, 8, 0.65, 0.40, 2.5, 80.0)
		"mage":
			tower_name = "Mage Tower"
			match level:
				2: _set_mage(2125, 17, 180, 0.33, 4, 2, 0.20, 0.40, 2.0)
				3: _set_mage(2750, 26, 190, 0.30, 5, 2, 0.25, 0.50, 2.1)
				4: _set_mage(3625, 39, 200, 0.27, 6, 3, 0.30, 0.60, 2.3)
				5: _set_mage(4625, 55, 210, 0.23, 7, 3, 0.40, 0.75, 2.5)
				_: _set_mage(5875, 70, 230, 0.20, 8, 4, 0.50, 1.00, 3.0)

	hp = max_hp
	shield_max = max_hp * 0.40
	shield = shield_max


func _set_stats(p_hp: float, p_dmg: float, p_rng: float, p_cd: float, p_arm: float, p_double: bool) -> void:
	max_hp = p_hp
	damage = p_dmg
	attack_range = p_rng
	attack_cooldown = p_cd
	armor = p_arm
	double_shot = p_double


func _set_cannon(p_hp: float, p_dmg: float, p_rng: float, p_cd: float, p_arm: float, p_spl: float, p_bdps: float, p_bdur: float) -> void:
	_set_stats(p_hp, p_dmg, p_rng, p_cd, p_arm, false)
	splash = p_spl
	burn_dps = p_bdps
	burn_duration = p_bdur


func _set_ice(p_hp: float, p_dmg: float, p_rng: float, p_cd: float, p_arm: float, p_slow: float, p_aslow: float, p_sdur: float, p_aoe: float) -> void:
	_set_stats(p_hp, p_dmg, p_rng, p_cd, p_arm, false)
	slow = p_slow
	atk_slow = p_aslow
	slow_duration = p_sdur
	slow_aoe = p_aoe


func _set_mage(p_hp: float, p_dmg: float, p_rng: float, p_cd: float, p_arm: float, p_chn: int, p_skd: float, p_aheal: float, p_dur: float) -> void:
	_set_stats(p_hp, p_dmg, p_rng, p_cd, p_arm, false)
	chain = p_chn
	skill_down = p_skd
	anti_heal = p_aheal
	debuff_duration = p_dur


func is_alive() -> bool:
	return hp > 0.0


## Notifikasi Tower Aggro (Tower Dive Punishment 1:1 Pygame & MOBA)
## Jika hero kawan diserang oleh unit musuh dalam jangkauan menara,
## menara segera mengalihkan tembakan ke musuh penyerang tersebut!
func notify_hero_attacked(allied_hero: Node2D, enemy_attacker: Node2D) -> void:
	if allied_hero == null or enemy_attacker == null:
		return
	if hp <= 0.0:
		return
	if allied_hero.get("team") == team and enemy_attacker.get("team") != team:
		var d: float = position.distance_to(enemy_attacker.position)
		if d <= attack_range:
			aggro_target = enemy_attacker
			target = enemy_attacker


## Mitigasi Damage & Shield Menara
func take_damage(amount: float, damage_type: String = "physical", _attacker = null) -> void:
	if hp <= 0.0:
		return

	_no_damage_timer = 0.0
	var eff_dmg := amount

	# Mitigasi Armor Fisik MOBA: reduction = armor * 0.06 / (1.0 + armor * 0.06)
	if damage_type == "physical":
		var red: float = (armor * 0.06) / (1.0 + armor * 0.06)
		eff_dmg = maxf(1.0, eff_dmg * (1.0 - red))

	# Penyerapan Shield Dulu
	if shield > 0.0:
		if shield >= eff_dmg:
			shield -= eff_dmg
			eff_dmg = 0.0
			_add_float_text("SHIELD!", Color8(100, 200, 255))
		else:
			eff_dmg -= shield
			shield = 0.0
			_add_float_text("SHIELD BREAK!", Color8(255, 180, 50))

	# Sisa Damage masuk ke HP
	if eff_dmg > 0.0:
		hp -= eff_dmg
		_flash = 0.1
		_add_float_text("-%d" % int(eff_dmg), Color8(255, 230, 100))

	queue_redraw()
	if hp <= 0.0:
		hp = 0.0
		_die()


func _die() -> void:
	Sound.play("destroy")
	print("[Combat] Menara %s (%s) hancur. Bounty %dG diberikan." % [tower_name, team, gold_reward])
	destroyed.emit(self)
	queue_free()


func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash -= delta
		modulate = Color(1.0, 0.4, 0.4) if _flash > 0.0 else Color.WHITE

	if _shot_t > 0.0:
		_shot_t -= delta
		queue_redraw()

	# Floating Text Tick
	var alive_floats: Array = []
	for ft in _float_texts:
		ft["t"] -= delta
		ft["off_y"] -= delta * 24.0
		if ft["t"] > 0.0:
			alive_floats.append(ft)
	_float_texts = alive_floats

	if hp <= 0.0:
		return

	# Out-of-Combat Regen (setelah 5 detik tidak diserang)
	_no_damage_timer += delta
	if _no_damage_timer >= 5.0:
		if shield < shield_max:
			shield = minf(shield_max, shield + shield_max * 0.05 * delta)
		if hp < max_hp:
			hp = minf(max_hp, hp + max_hp * 0.02 * delta)

	if _cooldown > 0.0:
		_cooldown -= delta

	# Prioritas Target Menara
	_update_target()

	# Eksekusi Tembakan
	if target != null and _cooldown <= 0.0:
		_shoot_target()
		_cooldown = attack_cooldown
		_shot_to = target.position - position
		_shot_t = 0.18
		queue_redraw()


## Sistem Prioritas Target Menara 1:1 MOBA
## 1. Aggro Target (Penyerang Hero Sekutu di dalam range menara)
## 2. Target yang sedang terkunci (selama masih hidup & dalam range)
## 3. Minion musuh terdekat
## 4. Hero musuh terdekat
func _update_target() -> void:
	# Cek apakah aggro target masih sah & dalam jarak
	if is_instance_valid(aggro_target) and _is_unit_alive(aggro_target):
		if position.distance_to(aggro_target.position) <= attack_range:
			target = aggro_target
			return
		else:
			aggro_target = null

	# Pertahankan target terkunci jika masih valid & dalam range
	if is_instance_valid(target) and _is_unit_alive(target):
		if position.distance_to(target.position) <= attack_range:
			return

	# Cari musuh baru berdasarkan prioritas: Minion > Hero
	target = _find_best_target()


func _find_best_target():
	var best_minion = null
	var best_minion_d: float = attack_range

	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m == null or m.team == team or not m.is_alive():
			continue
		var d: float = position.distance_to(m.position)
		if d <= best_minion_d:
			best_minion = m
			best_minion_d = d

	if best_minion != null:
		return best_minion

	# Jika tidak ada minion, serang Hero musuh
	var best_hero = null
	var best_hero_d: float = attack_range
	for n in get_tree().get_nodes_in_group("heroes"):
		var h := n as HeroUnit
		if h == null or h.team == team or not h.is_alive():
			continue
		var d2: float = position.distance_to(h.position)
		if d2 <= best_hero_d:
			best_hero = h
			best_hero_d = d2

	return best_hero


func _is_unit_alive(u) -> bool:
	if u == null or not is_instance_valid(u):
		return false
	if u.has_method("is_alive"):
		return u.is_alive()
	return u.get("hp") != null and u.hp > 0.0


## Eksekusi Tembakan Spesifik Per Tipe Menara
func _shoot_target() -> void:
	if target == null:
		return

	_chain_targets.clear()

	match tower_type:
		"archer":
			_shoot_archer()
		"cannon":
			_shoot_cannon()
		"ice":
			_shoot_ice()
		"mage":
			_shoot_mage()


func _shoot_archer() -> void:
	Sound.play("shoot")
	_apply_damage_to(target, damage, "physical")

	if double_shot:
		# Double-shot Lv6: cari target ke-2 atau tembak ulang target utama
		var extra = _find_secondary_target(target)
		if extra != null:
			_apply_damage_to(extra, damage * 0.85, "physical")
			_chain_targets.append(extra.position - position)
		else:
			_apply_damage_to(target, damage * 0.65, "physical")


func _shoot_cannon() -> void:
	Sound.play("hit")
	_apply_damage_to(target, damage, "physical")

	# Splash AOE Damage & Burn DOT ke semua musuh sekitar
	if splash > 0.0:
		var center: Vector2 = target.position
		for n in get_tree().get_nodes_in_group("minions"):
			var m := n as MinionUnit
			if m != null and m.team != team and m.is_alive() and m != target:
				if center.distance_to(m.position) <= splash:
					_apply_damage_to(m, damage * 0.60, "fire")
					_apply_burn(m)

	_apply_burn(target)


func _shoot_ice() -> void:
	Sound.play("shoot")
	_apply_damage_to(target, damage, "ice")
	_apply_ice_debuff(target)

	if slow_aoe > 0.0:
		var center: Vector2 = target.position
		for n in get_tree().get_nodes_in_group("minions"):
			var m := n as MinionUnit
			if m != null and m.team != team and m.is_alive() and m != target:
				if center.distance_to(m.position) <= slow_aoe:
					_apply_damage_to(m, damage * 0.5, "ice")
					_apply_ice_debuff(m)


func _shoot_mage() -> void:
	Sound.play("zap")
	_apply_damage_to(target, damage, "magic")
	_apply_mage_debuff(target)

	# Chain Lightning ke sejumlah musuh berdekatan
	var chain_count := chain - 1
	var last_pos: Vector2 = target.position
	var hit_foes: Array = [target]

	for _step in chain_count:
		var next_target = null
		var next_d: float = 160.0
		for n in get_tree().get_nodes_in_group("minions"):
			var m := n as MinionUnit
			if m != null and m.team != team and m.is_alive() and not hit_foes.has(m):
				var d: float = last_pos.distance_to(m.position)
				if d <= next_d:
					next_target = m
					next_d = d
		if next_target != null:
			hit_foes.append(next_target)
			_apply_damage_to(next_target, damage * 0.75, "magic")
			_apply_mage_debuff(next_target)
			_chain_targets.append(next_target.position - position)
			last_pos = next_target.position
		else:
			break


func _apply_damage_to(victim, dmg: float, dtype: String) -> void:
	if victim == null or not is_instance_valid(victim):
		return
	if victim.has_method("take_damage"):
		victim.take_damage(dmg, dtype)


func _apply_burn(u) -> void:
	if u != null and is_instance_valid(u) and u.has_method("apply_burn"):
		u.apply_burn(burn_dps, burn_duration)


func _apply_ice_debuff(u) -> void:
	if u != null and is_instance_valid(u) and u.has_method("apply_slow"):
		u.apply_slow(slow, atk_slow, slow_duration)


func _apply_mage_debuff(u) -> void:
	if u != null and is_instance_valid(u) and u.has_method("apply_mage_curse"):
		u.apply_mage_curse(skill_down, anti_heal, debuff_duration)


func _find_secondary_target(exclude_target):
	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m != null and m.team != team and m.is_alive() and m != exclude_target:
			if position.distance_to(m.position) <= attack_range:
				return m
	return null


func _add_float_text(txt: String, col: Color) -> void:
	_float_texts.append({"text": txt, "col": col, "t": 0.9, "off_y": -35.0})


# ═══ RENDERING 1:1 VISUAL PYGAME ═══
func _draw() -> void:
	var banner: Color = Color("#3E7CB1") if team == "blue" else Color("#B13E3E")

	# Bayangan Tanah
	draw_circle(Vector2(3, 14), 22.0, Color(0, 0, 0, 0.35))

	# Pondasi Batu Menara
	draw_rect(Rect2(-18, -16, 36, 38), Color("#565A65"))
	draw_rect(Rect2(-18, -16, 36, 38), Color("#101418"), false, 2.0)
	draw_rect(Rect2(-12, -8, 24, 28), Color("#7B818F"))

	# Aksen Jenis Menara
	var type_accent: Color = Color("#64DC78") # Archer
	match tower_type:
		"cannon": type_accent = Color("#C8643C")
		"ice": type_accent = Color("#78C8FF")
		"mage": type_accent = Color("#B450DC")

	draw_circle(Vector2(0, 0), 6.0, type_accent)
	draw_arc(Vector2(0, 0), 6.0, 0.0, TAU, 16, Color("#101418"), 1.5)

	# Bendera & Atap
	draw_colored_polygon(PackedVector2Array([Vector2(-16, -8), Vector2(16, -8), Vector2(0, -28)]), banner)
	draw_polyline(PackedVector2Array([Vector2(-16, -8), Vector2(16, -8), Vector2(0, -28), Vector2(-16, -8)]), Color("#101418"), 2.0)

	# Laser / Garis Proyektil Tembakan
	if _shot_t > 0.0:
		var beam_col: Color = Color("#FFE28A")
		match tower_type:
			"cannon": beam_col = Color("#FF6A28")
			"ice": beam_col = Color("#7DE2FF")
			"mage": beam_col = Color("#D472FF")

		draw_line(Vector2(0, -12), _shot_to, beam_col, 3.5)

		# Cabang Proyektil Rantai (Mage / Archer Lv6)
		for ct in _chain_targets:
			draw_line(Vector2(0, -12), ct, beam_col.lightened(0.2), 2.0)

	# Bar HP & Shield
	var ratio_hp: float = clampf(hp / max_hp, 0.0, 1.0)
	draw_rect(Rect2(-22, -36, 44, 5), Color("#101418"))
	draw_rect(Rect2(-22, -36, 44.0 * ratio_hp, 5), Color("#5FD35F"))

	if shield_max > 0.0 and shield > 0.0:
		var ratio_sh: float = clampf(shield / shield_max, 0.0, 1.0)
		draw_rect(Rect2(-22, -42, 44, 3), Color("#101418"))
		draw_rect(Rect2(-22, -42, 44.0 * ratio_sh, 3), Color("#5FD3FF"))

	# Floating Texts
	var font: Font = ThemeDB.fallback_font
	for ft in _float_texts:
		var txt: String = str(ft["text"])
		var col: Color = ft["col"]
		var oy: float = float(ft["off_y"])
		var tw := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
		draw_string(font, Vector2(-tw * 0.5 + 1.0, oy + 1.0), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0, 0, 0, 0.8))
		draw_string(font, Vector2(-tw * 0.5, oy), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, col)
