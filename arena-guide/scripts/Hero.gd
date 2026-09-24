extends Node2D
class_name HeroUnit
## Hero - pilih, jalan, combat, skill QWER, gugur/respawn.

var hero_id: String = "kaizen"
var hero_name: String = "Kaizen"
var team: String = "blue"
var max_hp: float = 550.0
var hp: float = 550.0
var damage: float = 22.0
var attack_range: float = 90.0
var move_speed: float = 120.0
var body_color: Color = Color("#4FC3F7")
var selected: bool = false
var attack_interval: float = 1.0
var skill_names: Array = ["Tebas Baja", "Semangat", "Rantai", "Amuk"]
var skill_short: Array = ["Tebas", "Sembuh", "Rantai", "Amuk"]
var skill_cds_max: Array = [4.0, 8.0, 7.0, 15.0]
var skill_cds: Array = [0.0, 0.0, 0.0, 0.0]
var buff_r_t: float = 0.0
var respawn_time: float = 5.0
var _enemy = null
var _cooldown: float = 0.0
var _target: Vector2 = Vector2.ZERO
var _moving: bool = false
var _spawn_pos: Vector2 = Vector2(220, 360)
var _dead: float = 0.0
var _flash: float = 0.0
var _flash_col: Color = Color(1.0, 0.4, 0.4)
var inventory: Array = [] # L34 item ids (max 6)
var lifesteal: float = 0.0 # dari Demon Maw
var bonus_armor: float = 0.0
var bonus_as: float = 0.0
# L37 — armor dasar hero. Pygame _entity.py:4650: armor hero MURNI dari item
# (inv.get_armor()), base = 0 → total = BASE_ARMOR + bonus_armor (dari toko).
const BASE_ARMOR: float = 0.0


func _ready() -> void:
	add_to_group("heroes")


func is_alive() -> bool:
	return _dead <= 0.0 and hp > 0.0


func total_armor() -> float:
	return BASE_ARMOR + bonus_armor


func take_damage(amount: float, school: String = "") -> void:
	if _dead > 0.0 or hp <= 0.0:
		return
	# L37: target HERO — SEMUA damage non-'fire' dikurangi armor
	# (pygame _entity.py:4650 gate damage_type != 'fire', BUKAN gate school).
	if school != "fire":
		amount = CombatCalc.mitigate(amount, total_armor())
	hp -= amount
	_flash = 0.1
	_flash_col = Color(1.0, 0.4, 0.4)
	queue_redraw()
	if hp <= 0.0:
		_dead = respawn_time
		_moving = false
		_enemy = null
		buff_r_t = 0.0
		visible = false
		print("[Combat] %s gugur! Hidup lagi %d detik." % [hero_name, int(respawn_time)])


func _respawn() -> void:
	hp = max_hp
	position = _spawn_pos
	_target = _spawn_pos
	visible = true
	queue_redraw()
	print("[Combat] %s hidup lagi!" % hero_name)


func setup(data: Dictionary, team_name: String, start_pos: Vector2) -> void:
	hero_id = str(data.get("id", "kaizen"))
	hero_name = str(data.get("name", "Kaizen"))
	max_hp = float(data.get("hp", 550))
	hp = max_hp
	damage = float(data.get("damage", 22))
	attack_range = float(data.get("range", 90))
	move_speed = float(data.get("move_speed", 120.0))
	body_color = Color(str(data.get("color", "#4FC3F7")))
	team = team_name
	position = start_pos
	_target = start_pos
	_spawn_pos = start_pos
	queue_redraw()


func set_selected(value: bool) -> void:
	selected = value
	queue_redraw()


func move_to(point: Vector2) -> void:
	_target = Vector2(clampf(point.x, 40.0, 1240.0), clampf(point.y, 40.0, 680.0))
	_moving = true


func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash -= delta
		modulate = _flash_col if _flash > 0.0 else Color.WHITE
	for i in skill_cds.size():
		if float(skill_cds[i]) > 0.0:
			skill_cds[i] = maxf(0.0, float(skill_cds[i]) - delta)
	if buff_r_t > 0.0:
		buff_r_t -= delta
		queue_redraw()
	if _dead > 0.0:
		_dead -= delta
		if _dead <= 0.0:
			_respawn()
		return
	if _moving:
		var to: Vector2 = _target - position
		var spd: float = move_speed * (1.4 if buff_r_t > 0.0 else 1.0)
		var step: float = spd * delta
		if to.length() <= maxf(step, 4.0):
			position = _target
			_moving = false
		else:
			position += to.normalized() * step
		queue_redraw()
	_combat(delta)


func _combat(delta: float) -> void:
	if _cooldown > 0.0:
		_cooldown -= delta
	if not is_instance_valid(_enemy) or not _enemy.is_alive():
		_enemy = _find_enemy()
	if _enemy != null and _cooldown <= 0.0:
		var dmg := _atk_damage()
		# L37: serangan dasar hero = school PHYSICAL (pygame dmg_school Kaizen)
		_enemy.take_damage(dmg, "physical")
		# lifesteal (Demon Maw)
		if lifesteal > 0.0 and dmg > 0.0:
			hp = minf(max_hp, hp + dmg * lifesteal)
			queue_redraw()
		Sound.play("hit")
		_cooldown = attack_interval


func cast_skill(i: int) -> void:
	if _dead > 0.0:
		print("[Skill] %s gugur, tak bisa cast." % hero_name)
		return
	if float(skill_cds[i]) > 0.0:
		print("[Skill] %s cooldown %.1fs." % [str(skill_names[i]), float(skill_cds[i])])
		return
	match i:
		0:
			_cast_q()
		1:
			_cast_w()
		2:
			_cast_e()
		3:
			_cast_r()


func _atk_damage() -> float:
	return damage * (2.0 if buff_r_t > 0.0 else 1.0)


func _foes_in(max_d: float) -> Array:
	var out: Array = []
	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m != null and m.team != team and m.is_alive() and position.distance_to(m.position) <= max_d:
			out.append(m)
	for n in get_tree().get_nodes_in_group("towers"):
		var t := n as TowerUnit
		if t != null and t.team != team and t.is_alive() and position.distance_to(t.position) <= max_d + 24.0:
			out.append(t)
	for n in get_tree().get_nodes_in_group("nexus"):
		var nx := n as NexusUnit
		if nx != null and nx.team != team and nx.is_alive() and position.distance_to(nx.position) <= max_d + 46.0:
			out.append(nx)
	return out


func _cast_q() -> void:
	skill_cds[0] = float(skill_cds_max[0])
	var foes: Array = _foes_in(150.0)
	if foes.is_empty():
		print("[Skill] Tebas Baja tak kena siapa-siapa.")
		return
	foes.sort_custom(func(a, b): return position.distance_to(a.position) < position.distance_to(b.position))
	var target = foes[0]
	# L37: skill = school MAGIC → tembus armor target (paritas school pygame;
	# magic_resist semua target port ini 0, jadi damage tetap penuh).
	target.take_damage(60.0, "magic")
	Sound.play("hit")
	print("[Skill] Tebas Baja: 60 damage.")


func _cast_w() -> void:
	skill_cds[1] = float(skill_cds_max[1])
	hp = minf(max_hp, hp + 120.0)
	_flash = 0.4
	_flash_col = Color(0.4, 1.0, 0.4)
	Sound.play("heal")
	queue_redraw()
	print("[Skill] Semangat: heal 120 (HP kini %d)." % int(hp))


func _cast_e() -> void:
	skill_cds[2] = float(skill_cds_max[2])
	var foes: Array = _foes_in(200.0)
	if foes.is_empty():
		print("[Skill] Rantai tak kena siapa-siapa.")
		return
	foes.sort_custom(func(a, b): return position.distance_to(a.position) < position.distance_to(b.position))
	var n: int = mini(3, foes.size())
	for i in n:
		# L37: skill = school MAGIC → tembus armor (lihat _cast_q).
		foes[i].take_damage(35.0, "magic")
	Sound.play("hit")
	print("[Skill] Rantai: 35 damage ke %d musuh." % n)


func _cast_r() -> void:
	skill_cds[3] = float(skill_cds_max[3])
	buff_r_t = 6.0
	Sound.play("buff")
	queue_redraw()
	print("[Skill] AMUK! Damage x2 + lari cepat 6 detik.")


func _find_enemy():
	var best = null
	var best_d: float = attack_range
	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m == null or m.team == team or not m.is_alive():
			continue
		var d: float = position.distance_to(m.position)
		if d <= best_d:
			best = m
			best_d = d
	for n in get_tree().get_nodes_in_group("towers"):
		var t := n as TowerUnit
		if t == null or t.team == team or not t.is_alive():
			continue
		var dt: float = position.distance_to(t.position)
		if dt <= best_d + 24.0:
			best = t
			best_d = dt
	for n in get_tree().get_nodes_in_group("nexus"):
		var nx := n as NexusUnit
		if nx == null or nx.team == team or not nx.is_alive():
			continue
		var dn: float = position.distance_to(nx.position)
		if dn <= best_d + 46.0:
			best = nx
			best_d = dn
	return best


func _draw() -> void:
	var team_ring: Color = Color("#3E7CB1") if team == "blue" else Color("#B13E3E")
	draw_circle(Vector2(3, 15), 16.0, Color(0, 0, 0, 0.35))
	draw_circle(Vector2.ZERO, 20.0, body_color)
	draw_arc(Vector2.ZERO, 20.0, 0.0, TAU, 32, team_ring, 4.0)
	var dir: Vector2 = _target - position
	if dir.length() > 4.0:
		draw_circle(dir.normalized() * 20.0, 5.0, Color.WHITE)
	if selected:
		draw_arc(Vector2.ZERO, 28.0, 0.0, TAU, 40, Color("#C9A227"), 3.0)
	if buff_r_t > 0.0:
		draw_arc(Vector2.ZERO, 34.0, 0.0, TAU, 40, Color("#FFD54F"), 4.0)
	var ratio: float = clampf(hp / max_hp, 0.0, 1.0)
	draw_rect(Rect2(-22, -38, 44, 6), Color("#101418"))
	draw_rect(Rect2(-22, -38, 44.0 * ratio, 6), Color("#5FD35F"))
