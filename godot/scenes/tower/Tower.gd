# Tower.gd — port _entity.Tower (menara pemain & AI).
#
# pygame: 4 jalur upgrade (archer/cannon/ice/mage) × 6 level, HP ×2.5,
# shield 40% max HP, armor 2+level, targeting unit terdekat dalam range,
# peluru BULLET_SPEED 8 px/frame, regen HP setelah 5 detik tidak kena damage.
# Semua tabel dibaca dari TowerDB (godot/data/towers.json) — tidak ada angka
# yang ditulis ulang di sini.
#
# Sengaja extends Node2D (BUKAN StaticBody2D): di pygame menara tidak menahan
# gerakan unit, jadi tidak boleh punya collision shape — unit jalan melewatinya
# sambil menyerangnya.
extends Node2D

const TowerBulletScript = preload("res://scenes/tower/TowerBullet.gd")
const FPS := 60.0

@export var team: String = "blue"
@export var tower_kind: String = "outer"   # outer | inner (menentukan gold reward)
@export var lane: String = "mid"
@export var tower_type: String = "archer"
@export var level: int = 1

# ── stat (diisi _apply_level_stats) ──
var max_hp: float = 2000.0
var hp: float = 2000.0
var shield: float = 0.0
var shield_max: float = 0.0
var shield_active: bool = true
var damage: float = 20.0
var attack_range: float = 180.0
var attack_cooldown: float = 35.0 / FPS
var armor: float = 3.0
var magic_resist: float = 0.0
var radius: float = 18.0
var dmg_school: String = "physical"

# ── kemampuan khusus per jalur ──
var splash: float = 0.0
var slow: float = 0.0
var slow_duration: float = 0.0
var slow_aoe: float = 0.0
var atk_slow: float = 0.0
var chain: int = 1
var double_shot: bool = false
var skill_down: float = 0.0
var anti_heal: float = 0.0
var debuff_duration: float = 0.0
var burn_dps: float = 0.0
var burn_duration: float = 0.0

# ── state ──
var is_dead: bool = false
var target: Node2D = null
var attack_timer: float = 0.0
var angle: float = 0.0
var no_damage_timer: float = 0.0
var kills: int = 0
var gold_reward: int = 100
var is_player_built: bool = true
var regen_shield_active: bool = false
var selected: bool = false
var upgrade_flash: float = 0.0
var shoot_flash: float = 0.0
var display_name: String = "Archer"
var color: Color = Color("#64dc78")
var color_dark: Color = Color("#328c46")

var _redraw_acc: float = 0.0


func _ready() -> void:
	add_to_group("towers")
	is_player_built = (team == "blue")
	gold_reward = 150 if tower_kind == "inner" else 100
	z_as_relative = false
	_apply_level_stats()


## CombatSystem itu autoload singleton -> boleh dirujuk langsung sebagai
## identifier global (gaya yang sama dengan Hero.gd/Minion.gd). Helper ini
## dipertahankan supaya call site tetap `var cs = _combat()` dan mudah
## di-mock kalau suatu saat combat dipisah per-scene.
func _combat():
	return CombatSystem


# ══════════════════════════════════════════════════════════
#  STAT
# ══════════════════════════════════════════════════════════

func _apply_level_stats() -> void:
	var s: Dictionary = TowerDB.level_stats(tower_type, level)
	max_hp = float(s["hp"])
	hp = max_hp                      # paritas pygame: HP segar saat level up
	shield_max = float(s["shield"])
	shield = shield_max
	shield_active = shield_max > 0.0
	damage = float(s["damage"])
	attack_range = float(s["range"])
	attack_cooldown = float(s["cooldown"])
	armor = float(s["armor"])
	magic_resist = float(s["magic_resist"])
	splash = float(s["splash"])
	slow = float(s["slow"])
	slow_duration = float(s["slow_duration"])
	slow_aoe = float(s["slow_aoe"])
	atk_slow = float(s["atk_slow"])
	chain = int(s["chain"])
	double_shot = bool(s["double_shot"])
	skill_down = float(s["skill_down"])
	anti_heal = float(s["anti_heal"])
	debuff_duration = float(s["debuff_duration"])
	burn_dps = float(s["burn_dps"])
	burn_duration = float(s["burn_duration"])
	color = TowerDB.type_color(tower_type)
	color_dark = TowerDB.type_color_dark(tower_type)
	display_name = "%s Lv%d" % [str(TowerDB.type_info(tower_type).get("name",
		tower_type.capitalize())), level]
	radius = 16.0 + float(level)
	queue_redraw()


func can_upgrade() -> bool:
	return level < TowerDB.max_level()


func upgrade_cost(target_type: String = "") -> int:
	if not can_upgrade():
		return 0
	# Level 1 -> 2 = memilih jalur (archer/cannon/ice/mage)
	var path := tower_type
	if level <= 1 and target_type != "":
		path = target_type
	return TowerDB.upgrade_cost(path, level)


## Upgrade. Level 1 WAJIB memilih jalur (paritas Tower.upgrade).
func upgrade(target_type: String = "") -> bool:
	if not can_upgrade():
		return false
	if level <= 1:
		if target_type == "":
			return false
		if not TowerDB.tower_types().has(target_type):
			return false
		tower_type = target_type
	level += 1
	_apply_level_stats()
	upgrade_flash = 0.5
	return true


func sell_value() -> int:
	if not is_player_built:
		return 0
	return TowerDB.sell_value(tower_type, level, regen_shield_active)


# ══════════════════════════════════════════════════════════
#  REGEN SHIELD (fitur berbayar — paritas Tower.activate_regen_shield)
# ══════════════════════════════════════════════════════════

## Boleh dibeli kalau menara sudah level >= TOWER_REGEN_SHIELD_MIN_LEVEL (4)
## dan belum aktif (paritas Tower.can_activate_regen_shield)
func can_activate_regen_shield() -> bool:
	var cfg: Dictionary = TowerDB.regen_shield_cfg()
	# Paritas pygame: Regen Shield tersedia untuk SEMUA tim (_entity.py:6232
	# AIPlayer._try_activate_regen_shield memakai tower merah). `is_player_built`
	# hanya menandai tower yang dibeli pemain untuk bisa dijual, bukan gerbang
	# fitur — jadi tower Dire (AI) juga boleh membelinya.
	var owned: bool = is_player_built or str(team) == "red"
	return bool(cfg.get("enabled", true)) \
			and level >= TowerDB.regen_shield_min_level() \
			and not regen_shield_active and not is_dead \
			and owned


func regen_shield_cost() -> int:
	return TowerDB.regen_shield_cost()


## Langsung mengisi shield penuh saat dibeli, lalu shield regen sendiri
func activate_regen_shield() -> bool:
	if not can_activate_regen_shield():
		return false
	regen_shield_active = true
	shield = shield_max
	shield_active = shield_max > 0.0
	upgrade_flash = 0.5
	print("[Tower] %s %s membeli Regen Shield" % [team, display_name])
	return true


# ══════════════════════════════════════════════════════════
#  LOOP
# ══════════════════════════════════════════════════════════

func _physics_process(delta: float) -> void:
	if is_dead:
		return
	attack_timer = maxf(0.0, attack_timer - delta)
	no_damage_timer += delta
	if upgrade_flash > 0.0:
		upgrade_flash = maxf(0.0, upgrade_flash - delta)
	if shoot_flash > 0.0:
		shoot_flash = maxf(0.0, shoot_flash - delta)
	_update_regen(delta)

	var cs = _combat()
	if cs != null:
		target = cs.nearest_enemy(self, attack_range)
	if target != null:
		angle = (target.global_position - global_position).angle()
		if attack_timer <= 0.0:
			_shoot(cs)
			attack_timer = attack_cooldown

	# redraw 20 Hz (flash + sudut laras + bar HP), bukan tiap frame
	_redraw_acc += delta
	if _redraw_acc >= 0.05:
		_redraw_acc = 0.0
		z_index = 60 + int(global_position.y) / 4
		queue_redraw()


## Regen HP setelah 5 detik tidak kena damage (paritas Tower._update_regen)
func _update_regen(delta: float) -> void:
	var cfg: Dictionary = TowerDB.hp_regen_cfg()
	if not bool(cfg.get("enabled", true)):
		return
	var delay := float(cfg.get("delay_frames", 300)) / FPS
	if no_damage_timer < delay:
		return
	var max_regen := max_hp * float(cfg.get("max_ratio", 1.0))
	if hp < max_regen:
		hp = minf(max_regen, hp + float(cfg.get("rate_per_frame", 0.3)) * FPS * delta)
	# Shield regen HANYA kalau Regen Shield sudah dibayar (paritas _entity 855-862)
	if regen_shield_active and shield_max > 0.0 and shield < shield_max:
		var scfg: Dictionary = TowerDB.regen_shield_cfg()
		var sdelay := float(scfg.get("delay_frames", 180)) / FPS
		if no_damage_timer >= sdelay:
			shield = minf(shield_max,
				shield + float(scfg.get("rate_per_frame", 1.8)) * FPS * delta)
			shield_active = true


# ══════════════════════════════════════════════════════════
#  TEMBAK
# ══════════════════════════════════════════════════════════

func _shoot(cs) -> void:
	if target == null or cs == null:
		return
	shoot_flash = 0.12
	# Suara tembak PER JENIS menara (paritas Tower._shoot _entity.py:876-884):
	# archer/cannon/ice/mage punya berkas sendiri, dan tim biru (punya pemain)
	# sedikit lebih keras daripada tim merah (volume_mult 1.0 vs 0.8).
	# Jeda 110 ms per jenis + anggaran 4/frame ada di AudioManager.play_combat.
	AudioManager.play_combat(AudioManager.tower_sfx(tower_type),
		1.0 if team == "blue" else 0.8)
	var speed := TowerDB.bullet_speed()
	match tower_type:
		"cannon":
			_spawn_bullet(target, damage, "cannon", {
				"splash": splash, "burn_dps": burn_dps,
				"burn_duration": burn_duration}, speed, Color("#ffb464"))
		"ice":
			var sp := {"slow": slow, "slow_duration": slow_duration,
				"atk_slow": atk_slow}
			if slow_aoe > 0.0:
				sp["slow_aoe"] = slow_aoe
			_spawn_bullet(target, damage, "ice", sp, speed, Color("#aee6ff"))
		"mage":
			# chain: 1 peluru per target (paritas _shoot_mage)
			var targets: Array = [target]
			for e in cs.enemies_in_radius(team, global_position, attack_range):
				if targets.size() >= chain:
					break
				if targets.has(e):
					continue
				targets.append(e)
			var sp := {}
			if skill_down > 0.0:
				sp["skill_down"] = skill_down
			if anti_heal > 0.0:
				sp["anti_heal"] = anti_heal
			if not sp.is_empty():
				sp["debuff_duration"] = debuff_duration
			for t in targets:
				_spawn_bullet(t, damage, "mage", sp, speed, Color("#dca0ff"))
		_:
			_spawn_bullet(target, damage, "normal", {}, speed, Color("#ffe9a8"))
			if double_shot:
				# Archer L6: tembakan kedua ke musuh lain dalam range
				var second = null
				for e in cs.enemies_in_radius(team, global_position, attack_range):
					if e == target:
						continue
					second = e
					break
				if second != null:
					_spawn_bullet(second, damage, "normal", {}, speed,
						Color("#ffe9a8"))


func _spawn_bullet(t: Node2D, dmg: float, btype: String, sp: Dictionary,
		speed: float, col: Color) -> void:
	var b = TowerBulletScript.new()
	b.setup(t, dmg, team, btype, sp, speed, col, self)
	b.global_position = global_position + Vector2(cos(angle), sin(angle)) * 12.0 \
		+ Vector2(0, -22)
	GameManager.attach_fx(b)


# ══════════════════════════════════════════════════════════
#  DAMAGE
# ══════════════════════════════════════════════════════════

func take_damage(amount: float, from_team: String = "", dmg_type: String = "normal",
		source = null, school: String = "") -> void:
	if is_dead:
		return
	var cs = _combat()
	if cs != null:
		cs.apply_damage(self, amount, from_team, dmg_type, source, school)
	else:
		hp -= amount
	queue_redraw()
	if hp <= 0.0:
		die(from_team, source)


func heal(amount: float) -> void:
	if is_dead:
		return
	hp = minf(max_hp, hp + amount)


func die(killer_team: String = "", _killer = null) -> void:
	if is_dead:
		return
	is_dead = true
	hp = 0.0
	target = null
	# Satu suara global untuk SEMUA jenis menara (paritas Tower.take_damage
	# _entity.py:1095-1101, volume_mult 0.8, throttle 300 ms).
	AudioManager.play_sfx("tower_destroyed", 0.8)
	# Gold reward: hanya tim pembunuh yang menabung (paritas GameManager.award_kill)
	GameManager.award_kill(killer_team, gold_reward)
	GameManager.tower_destroyed.emit(self, killer_team)
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(self, "modulate:a", 0.0, 0.45)
	tw.tween_property(self, "scale", Vector2(1.25, 0.35), 0.45)
	tw.chain().tween_callback(queue_free)
	print("[Tower] %s %s hancur (Lv%d %s) — %d gold ke %s" % [
		team, display_name, level, lane, gold_reward, killer_team])


# ══════════════════════════════════════════════════════════
#  GAMBAR (prosedural, 0 asset — gaya sama dengan UnitSilhouette)
# ══════════════════════════════════════════════════════════

func _draw() -> void:
	if is_dead:
		return
	var team_col := Color(0.35, 0.6, 1.0) if team == "blue" else Color(0.95, 0.35, 0.3)
	# bayangan
	draw_circle(Vector2(0, 12), radius * 1.05, Color(0, 0, 0, 0.28))
	# pondasi batu
	draw_colored_polygon(PackedVector2Array([
		Vector2(-radius, 12), Vector2(radius, 12),
		Vector2(radius * 0.78, -6), Vector2(-radius * 0.78, -6)]),
		Color(0.33, 0.31, 0.29, 1))
	draw_colored_polygon(PackedVector2Array([
		Vector2(-radius * 0.78, -6), Vector2(radius * 0.78, -6),
		Vector2(radius * 0.62, -26), Vector2(-radius * 0.62, -26)]),
		Color(0.42, 0.4, 0.37, 1))
	# badan menara sesuai jenis
	var body_top := -30.0 - float(level) * 2.0
	draw_colored_polygon(PackedVector2Array([
		Vector2(-radius * 0.62, -26), Vector2(radius * 0.62, -26),
		Vector2(radius * 0.5, body_top), Vector2(-radius * 0.5, body_top)]),
		color_dark)
	# kepala / turret
	draw_circle(Vector2(0, body_top - 4), radius * 0.52, color)
	draw_arc(Vector2(0, body_top - 4), radius * 0.52, 0.0, TAU, 20,
		Color(1, 1, 1, 0.35), 1.5)
	# aksen per jenis
	match tower_type:
		"archer":
			var dir := Vector2(cos(angle), sin(angle))
			draw_line(Vector2(0, body_top - 4), Vector2(0, body_top - 4) + dir * 16.0,
				Color(0.9, 0.85, 0.6, 0.95), 2.5)
		"cannon":
			var dir := Vector2(cos(angle), sin(angle))
			draw_line(Vector2(0, body_top - 4), Vector2(0, body_top - 4) + dir * 18.0,
				Color(0.2, 0.18, 0.17, 1), 6.0)
			if shoot_flash > 0.0:
				draw_circle(Vector2(0, body_top - 4) + dir * 20.0, 7.0,
					Color(1, 0.75, 0.3, shoot_flash * 6.0))
		"ice":
			for i in range(3):
				var a := TAU * float(i) / 3.0 + float(level) * 0.2
				draw_line(Vector2(0, body_top - 4),
					Vector2(0, body_top - 4) + Vector2(cos(a), sin(a)) * 10.0,
					Color(0.85, 0.95, 1, 0.9), 2.0)
		"mage":
			draw_circle(Vector2(0, body_top - 6), 5.0, Color(color.r, color.g, color.b, 0.55))
			draw_circle(Vector2(0, body_top - 6), 2.6, Color(1, 1, 1, 0.9))
	# pip level
	for i in range(level):
		draw_circle(Vector2(-radius * 0.5 + float(i) * 5.0, -12), 1.8,
			Color(1, 0.85, 0.35, 0.9))
	# shield bubble
	if shield > 0.0 and shield_active:
		var ratio := clampf(shield / maxf(1.0, shield_max), 0.0, 1.0)
		draw_arc(Vector2(0, -8), radius * 1.5, 0.0, TAU, 28,
			Color(team_col.r, team_col.g, team_col.b, 0.25 + 0.35 * ratio), 2.0)
	# bar HP + shield
	var w := 34.0
	var hp_ratio := clampf(hp / maxf(1.0, max_hp), 0.0, 1.0)
	draw_rect(Rect2(Vector2(-w * 0.5, body_top - 22), Vector2(w, 4)),
		Color(0, 0, 0, 0.55), true)
	draw_rect(Rect2(Vector2(-w * 0.5, body_top - 22), Vector2(w * hp_ratio, 4)),
		team_col.lightened(0.1), true)
	if shield_max > 0.0:
		var sh_ratio := clampf(shield / shield_max, 0.0, 1.0)
		draw_rect(Rect2(Vector2(-w * 0.5, body_top - 26), Vector2(w * sh_ratio, 2.5)),
			Color(0.6, 0.85, 1, 0.85), true)
	# upgrade flash
	if upgrade_flash > 0.0:
		draw_circle(Vector2(0, -10), radius * (1.6 + (0.5 - upgrade_flash)),
			Color(1, 0.95, 0.6, upgrade_flash * 0.7))
	# ring seleksi
	if selected:
		draw_arc(Vector2(0, 8), radius * 1.35, 0.0, TAU, 26,
			Color(1, 0.92, 0.5, 0.9), 2.0)
		# jangkauan
		draw_arc(Vector2.ZERO, attack_range, 0.0, TAU, 48,
			Color(1, 0.92, 0.5, 0.18), 1.5)
