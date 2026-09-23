extends Node2D
class_name MinionUnit
## MinionUnit — Pasukan Minion Lane (Paritas 1:1 Pygame MINION_TYPES & _entity.Minion)
## Mendukung 5 Tipe Minion (Goblin, Orc, Troll, Undead, Dark Rider),
## Status Debuff Menara (Slow, Atk Slow, Burn DOT, Anti-Heal), Mitigasi Armor,
## Jalur Waypoint Diagonal, dan Sistem Hadiah Last-Hit (Gold & XP).

signal died(minion: MinionUnit, killer)

# ═══ IDENTITAS & STAT ═══
var minion_type: String = "goblin"
var minion_name: String = "Goblin"
var team: String = "blue"
var max_hp: float = 45.0
var hp: float = 45.0
var damage: float = 5.0
var speed: float = 90.0
var base_speed: float = 90.0
var attack_range: float = 25.0
var attack_interval: float = 0.75
var gold_reward: int = 8
var radius: float = 9.0
var armor: float = 0.0
var magic_resist: float = 0.0
var hp_regen: float = 0.0
var is_ranged: bool = false
var arrived: bool = false

# ═══ WAYPOINT & MOVEMENT ═══
var path := PackedVector2Array()
var _path_i: int = 1
var _lateral: float = 0.0

# ═══ COMBAT & TARGETING ═══
var _enemy = null
var _cooldown: float = 0.0
var _flash: float = 0.0
var _shot_to: Vector2 = Vector2.ZERO
var _shot_t: float = 0.0

# ═══ STATUS DEBUFF MENARA ═══
var _slow_t: float = 0.0
var _slow_pct: float = 0.0
var _atk_slow_t: float = 0.0
var _atk_slow_pct: float = 0.0
var _burn_t: float = 0.0
var _burn_dps: float = 0.0
var _burn_tick: float = 0.0
var _skill_down_t: float = 0.0
var _anti_heal_t: float = 0.0

# ═══ FLOATING COMBAT TEXT ═══
var _float_texts: Array = []


func _ready() -> void:
	add_to_group("minions")


func setup(team_name: String, lane_path: PackedVector2Array, forward: bool, lateral: float, p_type: String = "goblin") -> void:
	team = team_name
	minion_type = p_type
	_apply_minion_type_stats(p_type)

	if forward:
		path = lane_path
	else:
		path = PackedVector2Array()
		for i in range(lane_path.size() - 1, -1, -1):
			path.append(lane_path[i])

	if path.size() > 0:
		position = path[0]
	_path_i = 1
	_lateral = lateral

	# Offset acak kecil agar minion tidak saling bertumpuk persis
	position += Vector2(randf_range(-6.0, 6.0), randf_range(-6.0, 6.0))
	queue_redraw()


func _apply_minion_type_stats(mtype: String) -> void:
	match mtype:
		"goblin":
			minion_name = "Goblin"
			max_hp = 45.0
			damage = 5.0
			speed = 90.0
			attack_range = 28.0
			attack_interval = 0.75
			gold_reward = 8
			radius = 9.0
			armor = 0.0
			magic_resist = 0.0
			hp_regen = 0.0
			is_ranged = false
		"orc":
			minion_name = "Orc"
			max_hp = 110.0
			damage = 13.0
			speed = 57.0
			attack_range = 32.0
			attack_interval = 1.0
			gold_reward = 18
			radius = 12.0
			armor = 0.0
			magic_resist = 0.0
			hp_regen = 0.0
			is_ranged = false
		"troll":
			minion_name = "Troll"
			max_hp = 320.0
			damage = 18.0
			speed = 39.0
			attack_range = 30.0
			attack_interval = 1.25
			gold_reward = 45
			radius = 14.0
			armor = 2.0
			magic_resist = 0.05
			hp_regen = 0.6
			is_ranged = false
		"undead":
			minion_name = "Undead"
			max_hp = 65.0
			damage = 11.0
			speed = 51.0
			attack_range = 110.0 # Ranged
			attack_interval = 1.0
			gold_reward = 16
			radius = 10.0
			armor = 0.0
			magic_resist = 0.15
			hp_regen = 0.0
			is_ranged = true
		"dark_rider":
			minion_name = "Dark Rider"
			max_hp = 280.0
			damage = 32.0
			speed = 120.0
			attack_range = 36.0
			attack_interval = 0.83
			gold_reward = 65
			radius = 13.0
			armor = 1.0
			magic_resist = 0.05
			hp_regen = 0.0
			is_ranged = false

	hp = max_hp
	base_speed = speed


func is_alive() -> bool:
	return hp > 0.0


## Aplikasi Debuff dari Menara (Paritas _entity.py)
func apply_slow(slow_amt: float, atk_slow_amt: float, duration: float) -> void:
	_slow_t = maxf(_slow_t, duration)
	_slow_pct = maxf(_slow_pct, slow_amt)
	_atk_slow_t = maxf(_atk_slow_t, duration)
	_atk_slow_pct = maxf(_atk_slow_pct, atk_slow_amt)
	_add_float_text("SLOW", Color8(100, 220, 255))


func apply_burn(dps: float, duration: float) -> void:
	_burn_t = maxf(_burn_t, duration)
	_burn_dps = maxf(_burn_dps, dps)


func apply_mage_curse(sk_down: float, a_heal: float, duration: float) -> void:
	_skill_down_t = maxf(_skill_down_t, duration)
	_anti_heal_t = maxf(_anti_heal_t, duration)
	_add_float_text("HEX!", Color8(210, 100, 255))


## Penerimaan Damage dengan Mitigasi MOBA
func take_damage(amount: float, damage_type: String = "physical", from_source = null) -> void:
	if hp <= 0.0:
		return

	var eff_dmg := amount

	# Mitigasi Armor MOBA
	if damage_type == "physical" and armor != 0.0:
		var red: float = (armor * 0.06) / (1.0 + absf(armor) * 0.06)
		eff_dmg = maxf(1.0, eff_dmg * (1.0 - red))
	elif damage_type == "magic" and magic_resist > 0.0:
		eff_dmg = maxf(1.0, eff_dmg * (1.0 - magic_resist))

	hp -= eff_dmg
	_flash = 0.1
	queue_redraw()

	if hp <= 0.0:
		hp = 0.0
		_die(from_source)


func _die(killer = null) -> void:
	died.emit(self, killer)

	# Berikan Reward Gold & XP jika minion musuh dikalahkan pemain
	_award_bounty(killer)
	queue_free()


func _award_bounty(killer) -> void:
	var tree := get_tree()
	if tree == null:
		return

	var main_node = tree.current_scene
	if main_node == null:
		return

	# Jika minion yang mati adalah musuh (red), tim pemain (blue) mendapatkan gold
	if team == "red":
		if "gold" in main_node:
			main_node.gold += gold_reward

		# Berikan XP ke Hero kawan di dekatnya
		for n in tree.get_nodes_in_group("heroes"):
			var h := n as HeroUnit
			if h != null and h.team == "blue" and h.is_alive():
				if position.distance_to(h.position) <= 450.0:
					# XP scaling berdasarkan minion type
					var xp_gain: float = 15.0
					match minion_type:
						"orc": xp_gain = 25.0
						"undead": xp_gain = 35.0
						"troll": xp_gain = 55.0
						"dark_rider": xp_gain = 80.0
					if h.has_method("add_xp"):
						h.add_xp(xp_gain)

		# Floating Gold Text di lokasi kematian
		if killer is HeroUnit or (killer != null and killer.get("team") == "blue"):
			Sound.play("coin")
			print("[Combat] Last hit %s! +%dG" % [minion_name, gold_reward])
	elif team == "blue":
		# AI Team gold gain
		if "ai_gold" in main_node:
			main_node.ai_gold += gold_reward


func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash -= delta
		modulate = Color(1.0, 0.4, 0.4) if _flash > 0.0 else Color.WHITE

	if _shot_t > 0.0:
		_shot_t -= delta
		queue_redraw()

	# Tick Floating Text
	var alive_floats: Array = []
	for ft in _float_texts:
		ft["t"] -= delta
		ft["off_y"] -= delta * 20.0
		if ft["t"] > 0.0:
			alive_floats.append(ft)
	_float_texts = alive_floats

	if hp <= 0.0:
		return

	# Tick Status Effects (Slow, Burn)
	_tick_status_effects(delta)

	# HP Regen pasif (Troll)
	if hp_regen > 0.0 and hp < max_hp:
		var reg: float = hp_regen * (0.3 if _anti_heal_t > 0.0 else 1.0)
		hp = minf(max_hp, hp + reg * delta)

	# Cooldown Serangan
	if _cooldown > 0.0:
		_cooldown -= delta

	# Pengecekan Target Pertempuran
	if not is_instance_valid(_enemy) or not _is_enemy_alive(_enemy):
		_enemy = _find_enemy()

	# Eksekusi Serangan Jika Ada Target
	if _enemy != null:
		var d: float = position.distance_to(_enemy.position)
		if d <= attack_range:
			if _cooldown <= 0.0:
				_attack_enemy(_enemy)
			return

	# Pergerakan Waypoint Lane
	if arrived:
		_march_to_nexus(delta)
		return

	if _path_i >= path.size():
		position = path[path.size() - 1]
		arrived = true
		return

	var tp := _path_target()
	var to: Vector2 = tp - position
	var eff_speed := speed * (1.0 - _slow_pct if _slow_t > 0.0 else 1.0)
	var step: float = eff_speed * delta

	if to.length() <= maxf(step, 6.0):
		_path_i += 1
	else:
		position += to.normalized() * step


func _tick_status_effects(delta: float) -> void:
	if _slow_t > 0.0:
		_slow_t -= delta
		if _slow_t <= 0.0:
			_slow_pct = 0.0

	if _atk_slow_t > 0.0:
		_atk_slow_t -= delta
		if _atk_slow_t <= 0.0:
			_atk_slow_pct = 0.0

	if _skill_down_t > 0.0:
		_skill_down_t -= delta
	if _anti_heal_t > 0.0:
		_anti_heal_t -= delta

	if _burn_t > 0.0:
		_burn_t -= delta
		_burn_tick -= delta
		if _burn_tick <= 0.0:
			_burn_tick = 0.25
			hp -= _burn_dps * 0.25
			_flash = 0.08
			if hp <= 0.0:
				hp = 0.0
				_die()


func _attack_enemy(target_unit) -> void:
	if is_ranged:
		# Undead: Serangan panah / proyektil berjarak
		Sound.play("shoot")
		_shot_to = target_unit.position - position
		_shot_t = 0.15
	else:
		Sound.play("hit")

	var eff_dmg := damage
	if target_unit.has_method("take_damage"):
		target_unit.take_damage(eff_dmg, "magic" if is_ranged else "physical", self)

	var eff_cd := attack_interval * (1.0 + _atk_slow_pct if _atk_slow_t > 0.0 else 1.0)
	_cooldown = eff_cd
	queue_redraw()


func _path_target() -> Vector2:
	var p: Vector2 = path[mini(_path_i, path.size() - 1)]
	var j0 := maxi(0, _path_i - 1)
	var j1 := mini(path.size() - 1, _path_i + 1)
	var d: Vector2 = path[j1] - path[j0]
	if d.length() > 1.0:
		p += Vector2(-d.y, d.x).normalized() * _lateral
	return p


func _is_enemy_alive(u) -> bool:
	if u == null or not is_instance_valid(u):
		return false
	if u.has_method("is_alive"):
		return u.is_alive()
	return u.get("hp") != null and u.hp > 0.0


func _find_enemy():
	var best = null
	var best_d: float = attack_range

	# 1. Minion Musuh
	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m == null or m == self or m.team == team or not m.is_alive():
			continue
		var d: float = position.distance_to(m.position)
		if d <= best_d:
			best = m
			best_d = d

	# 2. Menara Musuh
	for n in get_tree().get_nodes_in_group("towers"):
		var t := n as TowerUnit
		if t == null or t.team == team or not t.is_alive():
			continue
		var d2: float = position.distance_to(t.position)
		if d2 <= best_d + 30.0:
			best = t
			best_d = d2

	# 3. Hero Musuh
	for n in get_tree().get_nodes_in_group("heroes"):
		var h := n as HeroUnit
		if h == null or h.team == team or not h.is_alive():
			continue
		var d3: float = position.distance_to(h.position)
		if d3 <= best_d:
			best = h
			best_d = d3

	# 4. Nexus Musuh
	for n in get_tree().get_nodes_in_group("nexus"):
		var nx := n as NexusUnit
		if nx == null or nx.team == team or not nx.is_alive():
			continue
		var d4: float = position.distance_to(nx.position)
		if d4 <= best_d + 46.0:
			best = nx
			best_d = d4

	return best


func _march_to_nexus(delta: float) -> void:
	var nx := _find_nexus()
	if nx == null:
		return
	var d: float = position.distance_to(nx.position)
	if d > attack_range + 46.0:
		var eff_spd := speed * (1.0 - _slow_pct if _slow_t > 0.0 else 1.0)
		position += (nx.position - position).normalized() * eff_spd * delta


func _find_nexus() -> NexusUnit:
	for n in get_tree().get_nodes_in_group("nexus"):
		var nx := n as NexusUnit
		if nx != null and nx.team != team and nx.is_alive():
			return nx
	return null


func _add_float_text(txt: String, col: Color) -> void:
	_float_texts.append({"text": txt, "col": col, "t": 0.8, "off_y": -18.0})


# ═══ RENDERING 1:1 VISUAL PYGAME PER TIPE MINION ═══
func _draw() -> void:
	var body: Color = Color("#3E7CB1") if team == "blue" else Color("#B13E3E")

	# Bayangan
	draw_circle(Vector2(2, radius * 0.7), radius * 0.8, Color(0, 0, 0, 0.35))

	# Bentuk Spesifik Berdasarkan Minion Type
	match minion_type:
		"goblin":
			# Goblin: kecil, gesit, telinga runcing
			draw_circle(Vector2.ZERO, radius, body)
			draw_colored_polygon(PackedVector2Array([Vector2(-radius, -2), Vector2(-radius - 4, -7), Vector2(-radius + 2, -5)]), body)
			draw_colored_polygon(PackedVector2Array([Vector2(radius, -2), Vector2(radius + 4, -7), Vector2(radius - 2, -5)]), body)
		"orc":
			# Orc: besar, taring putih
			draw_circle(Vector2.ZERO, radius, body.darkened(0.1))
			draw_rect(Rect2(-3, -2, 6, 5), Color("#FFFFFF"))
		"troll":
			# Troll: batu berduri, tank tebal
			draw_circle(Vector2.ZERO, radius, body.darkened(0.25))
			draw_arc(Vector2.ZERO, radius, 0.0, TAU, 16, Color("#A0A4B8"), 2.5)
		"undead":
			# Undead: berjubah sihir, mata menyala
			draw_circle(Vector2.ZERO, radius, body.lightened(0.15))
			draw_circle(Vector2(2, -2), 2.5, Color("#64FFDA"))
		"dark_rider":
			# Dark Rider: kavaleri berzirah gelap
			draw_circle(Vector2.ZERO, radius, Color("#2C3440") if team == "blue" else Color("#4A1E24"))
			draw_arc(Vector2.ZERO, radius, 0.0, TAU, 16, body, 2.0)

	# Outline Badan
	draw_arc(Vector2.ZERO, radius, 0.0, TAU, 16, Color("#101418"), 1.8)

	# Efek Proyektil Ranged
	if _shot_t > 0.0:
		draw_line(Vector2.ZERO, _shot_to, Color("#90EE90") if minion_type == "undead" else Color("#FFE28A"), 2.0)

	# Status Debuff Aura
	if _slow_t > 0.0:
		draw_arc(Vector2.ZERO, radius + 3.0, 0.0, TAU, 12, Color("#78C8FF"), 1.5)
	if _burn_t > 0.0:
		draw_arc(Vector2.ZERO, radius + 2.0, 0.0, TAU, 12, Color("#FFA040"), 1.5)

	# Bar HP
	var ratio: float = clampf(hp / max_hp, 0.0, 1.0)
	var bar_w := radius * 2.2
	draw_rect(Rect2(-bar_w * 0.5, -radius - 8, bar_w, 3), Color("#101418"))
	draw_rect(Rect2(-bar_w * 0.5, -radius - 8, bar_w * ratio, 3), Color("#5FD35F"))

	# Floating Text
	var font: Font = ThemeDB.fallback_font
	for ft in _float_texts:
		var txt: String = str(ft["text"])
		var col: Color = ft["col"]
		var oy: float = float(ft["off_y"])
		var tw := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x
		draw_string(font, Vector2(-tw * 0.5 + 1.0, oy + 1.0), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0, 0, 0, 0.8))
		draw_string(font, Vector2(-tw * 0.5, oy), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, col)
