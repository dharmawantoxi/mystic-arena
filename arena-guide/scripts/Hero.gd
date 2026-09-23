extends Node2D
class_name HeroUnit
## Hero Unit — Paritas Penuh Pygame (_entity.py & hero_items.py)
## Fitur: Mitigasi Armor MOBA, Evasion, Critical Strike, Cleave Splash, Lifesteal,
## Out-of-Combat Regen, Holy Rapier Drop on Death, dan Skill QWER 6 Hero Starter.

var hero_id: String = "kaizen"
var hero_name: String = "Kaizen"
var team: String = "blue"
var max_hp: float = 550.0
var hp: float = 550.0
var damage: float = 35.0
var attack_range: float = 90.0
var move_speed: float = 120.0
var body_color: Color = Color8(100, 200, 255)
var selected: bool = false
var attack_interval: float = 1.0

# ── SKILL KIT (QWER) ──
var skill_names: Array = ["Wind Slash", "Swift Dash", "Blade Ward", "Storm Gale"]
var skill_short: Array = ["Slash", "Dash", "Ward", "Gale"]
var skill_cds_max: Array = [4.0, 8.0, 7.0, 15.0]
var skill_cds: Array = [0.0, 0.0, 0.0, 0.0]

# ── ITEM & STATS BONUS (hero_items.py) ──
var inventory: Array = []       # Maks 6 item
var bonus_armor: float = 0.0    # Dari perisai/item armor
var bonus_as: float = 0.0       # Attack speed bonus (%)
var lifesteal: float = 0.0      # Demon Maw (20%)
var crit_chance: float = 0.0    # Dead Edge (25%)
var evasion: float = 0.0        # Monarch Wings (28%)
var hp_reg: float = 0.0         # Regenerasi pasif HP per detik

# ── BUFF & TIMER SEMENTARA ──
var buff_r_t: float = 0.0       # Durasi buff Ultimate
var buff_as_t: float = 0.0      # Durasi buff Attack Speed
var buff_ward_t: float = 0.0    # Durasi perisai defensif
var buff_evasion_t: float = 0.0 # Durasi kebal evasion (Wind Run / Shadow Realm)
var spin_t: float = 0.0         # Durasi putaran Blade Fury (Grimjaw)
var spin_tick_t: float = 0.0
var _out_of_combat_t: float = 0.0 # Timer di luar pertempuran (Leviathan Heart)

var respawn_time: float = 5.0
var _enemy = null
var _cooldown: float = 0.0
var _target: Vector2 = Vector2.ZERO
var _moving: bool = false
var _spawn_pos: Vector2 = Vector2(250, 580)
var _dead: float = 0.0
var _flash: float = 0.0
var _flash_col: Color = Color(1.0, 0.4, 0.4)

# ── FLOATING COMBAT TEXT ──
var _float_texts: Array = [] # [{"text": str, "col": Color, "t": float, "off_y": float}]


func _ready() -> void:
	add_to_group("heroes")


func is_alive() -> bool:
	return _dead <= 0.0 and hp > 0.0


## Mitigasi Damage Gaya MOBA 1:1 Pygame (_entity.py:176224)
func take_damage(amount: float, damage_type: String = "physical") -> void:
	if _dead > 0.0 or hp <= 0.0:
		return

	# 1. Kebal Skill (Shadow Realm Zephyr / Wind Run Sylara)
	if buff_evasion_t > 0.0:
		_add_float_text("WIND/IMMUNE", Color8(100, 240, 255))
		return

	# 2. Evasion Pasif (Monarch Wings = 28% peluang meleset)
	if damage_type == "physical" and evasion > 0.0:
		if randf() < evasion:
			_add_float_text("MISS", Color8(120, 220, 255))
			return

	# 3. Mitigasi Armor MOBA: reduction = armor * 0.06 / (1.0 + armor * 0.06)
	var effective_damage := amount
	if damage_type == "physical":
		var total_armor := bonus_armor + (12.0 if buff_ward_t > 0.0 else 0.0)
		if total_armor > 0.0:
			var reduction: float = (total_armor * 0.06) / (1.0 + total_armor * 0.06)
			effective_damage = maxf(1.0, amount * (1.0 - reduction))
		elif total_armor < 0.0:
			var increase: float = absf(total_armor) * 0.06
			effective_damage = amount * (1.0 + minf(1.0, increase))

	# 4. Pantulan Razor Carapace / Bristleback
	if buff_ward_t > 0.0 and damage_type == "physical":
		var reflect := effective_damage * 0.35
		var foes := _foes_in(140.0)
		for f in foes:
			f.take_damage(reflect)

	hp -= effective_damage
	_out_of_combat_t = 0.0 # Reset timer Leviathan Heart
	_flash = 0.1
	_flash_col = Color(1.0, 0.4, 0.4)
	queue_redraw()

	if hp <= 0.0:
		_die()


func _die() -> void:
	_dead = respawn_time
	_moving = false
	_enemy = null
	buff_r_t = 0.0
	buff_as_t = 0.0
	buff_ward_t = 0.0
	buff_evasion_t = 0.0
	spin_t = 0.0
	visible = false

	# Holy Rapier Hilang Saat Hero Gugur (Paritas Mutlak Pygame)
	var rapier_idx: int = inventory.find("holy_rapier")
	if rapier_idx >= 0:
		inventory.remove_at(rapier_idx)
		damage = maxf(1.0, damage - 120.0)
		_add_float_text("RAPIER LOST!", Color8(255, 60, 60))
		print("[Combat] %s gugur! Holy Rapier HILANG!" % hero_name)

	print("[Combat] %s gugur! Respawn dalam %d detik." % [hero_name, int(respawn_time)])


func _respawn() -> void:
	hp = max_hp
	position = _spawn_pos
	_target = _spawn_pos
	visible = true
	_out_of_combat_t = 0.0
	queue_redraw()
	Sound.play("hero_spawn")
	print("[Combat] %s hidup kembali!" % hero_name)


func setup(data: Dictionary, team_name: String, start_pos: Vector2) -> void:
	hero_id = str(data.get("id", "kaizen"))
	hero_name = str(data.get("name", "Kaizen"))
	max_hp = float(data.get("hp", 550))
	hp = max_hp
	damage = float(data.get("damage", 35))
	attack_range = float(data.get("range", 90))
	move_speed = float(data.get("speed", 120.0))
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
	# Flash saat terkena serangan
	if _flash > 0.0:
		_flash -= delta
		modulate = _flash_col if _flash > 0.0 else Color.WHITE

	# Update Cooldown Skill
	for i in skill_cds.size():
		if float(skill_cds[i]) > 0.0:
			skill_cds[i] = maxf(0.0, float(skill_cds[i]) - delta)

	# Update Buff Timers
	if buff_r_t > 0.0: buff_r_t -= delta
	if buff_as_t > 0.0: buff_as_t -= delta
	if buff_ward_t > 0.0: buff_ward_t -= delta
	if buff_evasion_t > 0.0: buff_evasion_t -= delta

	# Grimjaw Spin (Blade Fury)
	if spin_t > 0.0:
		spin_t -= delta
		spin_tick_t -= delta
		if spin_tick_t <= 0.0:
			spin_tick_t = 0.3
			var foes := _foes_in(130.0)
			for f in foes:
				f.take_damage(26.0)
			Sound.play("hit")

	# Floating Combat Text Tick
	var alive_floats: Array = []
	for ft in _float_texts:
		ft["t"] -= delta
		ft["off_y"] -= delta * 30.0
		if ft["t"] > 0.0:
			alive_floats.append(ft)
	_float_texts = alive_floats

	# Respawn Counter
	if _dead > 0.0:
		_dead -= delta
		if _dead <= 0.0:
			_respawn()
		return

	# Out-of-Combat Regen (Leviathan Heart: 4% Max HP/s saat tenang 4 detik)
	_out_of_combat_t += delta
	var total_reg: float = hp_reg
	if inventory.has("leviathan_heart") and _out_of_combat_t >= 4.0:
		total_reg += max_hp * 0.04
	if total_reg > 0.0 and hp < max_hp and is_alive():
		hp = minf(max_hp, hp + total_reg * delta)

	# Pergerakan Hero
	if _moving:
		var to: Vector2 = _target - position
		var spd: float = move_speed * (1.35 if buff_r_t > 0.0 else (1.5 if buff_evasion_t > 0.0 else 1.0))
		var step: float = spd * delta
		if to.length() <= maxf(step, 4.0):
			position = _target
			_moving = false
		else:
			position += to.normalized() * step
		queue_redraw()

	_combat(delta)


## Logika Pertempuran Utama (Paritas hero_items.py & _entity.py)
func _combat(delta: float) -> void:
	if _cooldown > 0.0:
		_cooldown -= delta
	if not is_instance_valid(_enemy) or not _enemy.is_alive():
		_enemy = _find_enemy()

	if _enemy != null and _cooldown <= 0.0:
		var base_dmg := _atk_damage()
		var _is_crit: bool = false

		# 1. Critical Strike (Dead Edge 25% = 200% damage)
		if crit_chance > 0.0 and randf() < crit_chance:
			base_dmg *= 2.0
			_is_crit = true
			_add_float_text("CRIT!", Color8(255, 60, 60))

		# 2. Berikan Damage ke Musuh Utama
		_enemy.take_damage(base_dmg)

		# 3. Cleave Splash (Cleave Axe: 45% splash ke musuh lain dalam 180px)
		if inventory.has("cleave_axe"):
			var foes := _foes_in(180.0)
			for f in foes:
				if f != _enemy:
					f.take_damage(base_dmg * 0.45)

		# 4. Chain Lightning (Fenrir Chain / Thunder Coil: sambaran listrik 120 damage)
		if inventory.has("thunder_coil") or inventory.has("fenrir_chain"):
			if randf() < 0.22:
				_cast_chain_lightning(3, 120.0)

		# 5. Lifesteal & Blood Frenzy (Demon Maw: 20% + melonjak saat HP < 30%)
		var eff_ls := lifesteal
		if (hp / max_hp) < 0.30 and lifesteal > 0.0:
			eff_ls += 0.25 # Blood Frenzy
		if eff_ls > 0.0 and base_dmg > 0.0:
			var healed := base_dmg * eff_ls
			hp = minf(max_hp, hp + healed)
			queue_redraw()

		Sound.play("hit")
		var eff_interval := attack_interval / (2.5 if buff_as_t > 0.0 else 1.0)
		_cooldown = maxf(0.18, eff_interval)


func _atk_damage() -> float:
	return damage * (1.6 if buff_r_t > 0.0 else 1.0)


func _cast_chain_lightning(targets_count: int, dmg_amount: float) -> void:
	var foes := _foes_in(220.0)
	var hit_count := 0
	for f in foes:
		if hit_count >= targets_count:
			break
		f.take_damage(dmg_amount)
		hit_count += 1
	_add_float_text("CHAIN!", Color8(255, 240, 100))


func _add_float_text(txt: String, col: Color) -> void:
	_float_texts.append({"text": txt, "col": col, "t": 0.8, "off_y": -35.0})
	queue_redraw()


# ══════════════════════════════════════════════════════════
#  SKILL QWER (6 HERO STARTER PYGAME 1:1)
# ══════════════════════════════════════════════════════════

func cast_skill(i: int) -> void:
	if _dead > 0.0:
		print("[Skill] %s gugur, tak bisa menggunakan skill." % hero_name)
		return
	if float(skill_cds[i]) > 0.0:
		print("[Skill] %s cooldown %.1fs." % [str(skill_names[i]), float(skill_cds[i])])
		return

	skill_cds[i] = float(skill_cds_max[i])

	match hero_id:
		"kaizen":
			_cast_kaizen(i)
		"grimjaw":
			_cast_grimjaw(i)
		"sylara":
			_cast_sylara(i)
		"vex":
			_cast_vex(i)
		"thorne":
			_cast_thorne(i)
		"zephyr":
			_cast_zephyr(i)
		_:
			_cast_kaizen(i)


## Kaizen — The Wind Blade (Assassin)
func _cast_kaizen(i: int) -> void:
	match i:
		0: # Wind Slash: Dash & Tebasan AOE 70 Damage
			var foes := _foes_in(180.0)
			if not foes.is_empty():
				foes[0].take_damage(70.0)
				position = foes[0].position + Vector2(-25, 0)
			Sound.play("hit")
			_add_float_text("WIND SLASH!", Color8(100, 200, 255))
		1: # Swift Dash: Lari Cepat & Heal 120 HP
			hp = minf(max_hp, hp + 120.0)
			buff_as_t = 3.0
			Sound.play("heal")
			_add_float_text("+120 HP", Color8(100, 255, 120))
		2: # Blade Ward: Perisai Tangguh (+12 Armor 5 detik)
			buff_ward_t = 5.0
			Sound.play("buff")
			_add_float_text("BLADE WARD!", Color8(255, 220, 100))
		3: # Storm Gale (Ultimate): Amuk Badai (Damage x1.6 + Speed 6 detik)
			buff_r_t = 6.0
			Sound.play("buff")
			_add_float_text("STORM GALE!", Color8(255, 230, 80))


## Grimjaw — The Berserker (Fighter)
func _cast_grimjaw(i: int) -> void:
	match i:
		0: # Blade Fury: Putaran Pedang Multi-Hit
			spin_t = 2.5
			spin_tick_t = 0.0
			Sound.play("hit")
			_add_float_text("BLADE FURY!", Color8(255, 120, 60))
		1: # Blood Rage: Lifesteal +30% & Kecepatan Serang
			buff_as_t = 5.0
			lifesteal += 0.30
			Sound.play("buff")
			_add_float_text("BLOOD RAGE!", Color8(255, 80, 80))
		2: # Earth Smash: Hentakan Gempa 85 Damage
			var foes := _foes_in(150.0)
			for f in foes:
				f.take_damage(85.0)
			Sound.play("hit")
			_add_float_text("SMASH!", Color8(255, 160, 60))
		3: # Berserk (Ultimate): Heal 300 HP + Bonus Damage
			hp = minf(max_hp, hp + 300.0)
			buff_r_t = 8.0
			Sound.play("buff")
			_add_float_text("BERSERK!", Color8(255, 60, 60))


## Sylara — The Wind Ranger (Marksman)
func _cast_sylara(i: int) -> void:
	match i:
		0: # Focus Fire: Kecepatan Serang Tembakan Kilat
			buff_as_t = 4.5
			Sound.play("hit")
			_add_float_text("FOCUS FIRE!", Color8(120, 255, 150))
		1: # Wind Run: Kebal Serangan Fisik & Lari Cepat
			buff_evasion_t = 3.5
			Sound.play("buff")
			_add_float_text("WINDRUN!", Color8(100, 240, 255))
		2: # Powershot: Tembakan Panah Menembus 95 Damage
			var foes := _foes_in(280.0)
			for f in foes:
				f.take_damage(95.0)
			Sound.play("hit")
			_add_float_text("POWERSHOT!", Color8(100, 255, 140))
		3: # Gale Arrow (Ultimate): Panah Badai Musuh Terjauh 160 Damage
			var foes := _foes_in(320.0)
			if not foes.is_empty():
				foes[foes.size() - 1].take_damage(160.0)
			Sound.play("hit")
			_add_float_text("GALE ARROW!", Color8(80, 255, 200))


## Vex — The Void Harbinger (Mage)
func _cast_vex(i: int) -> void:
	match i:
		0: # Arcane Orb: Bola Sihir Meledak 95 Damage
			var foes := _foes_in(240.0)
			if not foes.is_empty():
				foes[0].take_damage(95.0)
			Sound.play("hit")
			_add_float_text("ARCANE ORB!", Color8(180, 140, 255))
		1: # Void Rift: Blink Teleport 160px
			var offset := (_target - position).normalized() * 160.0
			position = Vector2(clampf(position.x + offset.x, 50, 1230), clampf(position.y + offset.y, 50, 670))
			Sound.play("buff")
			_add_float_text("VOID RIFT!", Color8(200, 100, 255))
		2: # Null Field: Perisai Sihir 140 HP
			hp = minf(max_hp, hp + 140.0)
			var foes := _foes_in(140.0)
			for f in foes: f.take_damage(45.0)
			Sound.play("heal")
			_add_float_text("NULL FIELD!", Color8(160, 160, 255))
		3: # Supernova (Ultimate): Ledakan Area Besar 220 Damage
			var foes := _foes_in(260.0)
			for f in foes:
				f.take_damage(220.0)
			Sound.play("hit")
			_add_float_text("SUPERNOVA!", Color8(255, 120, 255))


## Thorne — The Quill Sprayer (Tank)
func _cast_thorne(i: int) -> void:
	match i:
		0: # Viscous Nose: Semburan Lendir
			var foes := _foes_in(140.0)
			for f in foes: f.take_damage(50.0)
			Sound.play("hit")
			_add_float_text("GOO SPRAY!", Color8(220, 180, 60))
		1: # Quill Spray: Duri Membalas 70 Damage
			var foes := _foes_in(180.0)
			for f in foes: f.take_damage(70.0)
			Sound.play("hit")
			_add_float_text("QUILL SPRAY!", Color8(255, 200, 80))
		2: # Bristleback: Mengurangi Damage Diterima
			buff_ward_t = 6.0
			Sound.play("buff")
			_add_float_text("BRISTLEBACK!", Color8(240, 160, 40))
		3: # Warpath (Ultimate): Amukan Penuh + Damage
			buff_r_t = 8.0
			hp = minf(max_hp, hp + 200.0)
			Sound.play("buff")
			_add_float_text("WARPATH!", Color8(255, 180, 50))


## Zephyr — Meander of Mischief (Trickster)
func _cast_zephyr(i: int) -> void:
	match i:
		0: # Bramble Maze: Duri Pengikat Musuh
			var foes := _foes_in(200.0)
			for f in foes.slice(0, 4): f.take_damage(60.0)
			Sound.play("hit")
			_add_float_text("BRAMBLE MAZE!", Color8(255, 100, 140))
		1: # Shadow Realm: Masuk Alam Bayangan (Kebal)
			buff_evasion_t = 3.0
			hp = minf(max_hp, hp + 100.0)
			Sound.play("buff")
			_add_float_text("SHADOW REALM!", Color8(255, 120, 180))
		2: # Cursed Crown: Ledakan Kutukan 110 Damage
			var foes := _foes_in(180.0)
			if not foes.is_empty(): foes[0].take_damage(110.0)
			Sound.play("hit")
			_add_float_text("CURSED CROWN!", Color8(220, 80, 120))
		3: # Bedlam (Ultimate): Badai Roh Peri 180 Damage
			var foes := _foes_in(220.0)
			for f in foes: f.take_damage(180.0)
			Sound.play("buff")
			_add_float_text("BEDLAM!", Color8(255, 80, 150))


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
	if buff_ward_t > 0.0:
		draw_arc(Vector2.ZERO, 30.0, 0.0, TAU, 32, Color8(100, 220, 255), 2.5)

	# Health bar di atas kepala
	var ratio: float = clampf(hp / max_hp, 0.0, 1.0)
	draw_rect(Rect2(-22, -38, 44, 6), Color("#101418"))
	draw_rect(Rect2(-22, -38, 44.0 * ratio, 6), Color("#5FD35F"))

	# Floating combat text
	var font: Font = ThemeDB.fallback_font
	for ft in _float_texts:
		var txt: String = str(ft["text"])
		var col: Color = ft["col"]
		var oy: float = float(ft["off_y"])
		var tw := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
		draw_string(font, Vector2(-tw * 0.5, oy), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, col)
