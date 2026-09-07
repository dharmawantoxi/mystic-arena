# TowerBullet.gd — port _entity.Bullet (peluru menara & nexus).
#
# pygame: Bullet(x, y, target, damage, team, bullet_type, special_data) bergerak
# BULLET_SPEED=8 px/frame lurus ke target lalu _on_hit() menerapkan:
#   cannon -> burn di target + splash 60% damage radius `splash`
#   ice    -> slow + atk_slow di target, dan slow_aoe (L6) ke musuh sekitar
#   mage   -> skill_down + anti_heal (chain = beberapa peluru sekaligus)
# Di Godot: Node2D homing (tanpa physics body) yang menggambar dirinya sendiri,
# supaya tidak ada masalah collision-layer dan tetap murah untuk ratusan peluru.
extends Node2D

const FPS := 60.0
## Splash cannon: 60% damage ke musuh lain dalam radius (paritas Bullet._on_hit)
const SPLASH_RATIO := 0.6

var target: Node2D = null
var damage: float = 0.0
var team: String = "blue"
var bullet_type: String = "normal"   # normal | cannon | ice | mage
var special: Dictionary = {}
var source = null                    # Tower/Nexus pemilik (untuk kredit kill)
var school: String = "physical"      # sekolah damage penembak (magic = tembus armor)
var speed: float = 480.0             # 8 px/frame × 60
var radius: float = 4.0
var color: Color = Color("#ffe9a8")
var lifetime: float = 4.0

var _cs = null
var _trail: PackedVector2Array = PackedVector2Array()


func _ready() -> void:
	# Group "bullets": Main._clear_field() membersihkan peluru yang masih terbang
	# saat restart, supaya tidak ada proyektil yatim mengejar node yang sudah bebas.
	add_to_group("bullets")


func setup(p_target: Node2D, p_damage: float, p_team: String, p_type: String,
		p_special: Dictionary, p_speed: float, p_color: Color, p_source = null,
		p_school: String = "physical") -> void:
	target = p_target
	damage = p_damage
	team = p_team
	bullet_type = p_type
	special = p_special.duplicate() if not p_special.is_empty() else {}
	source = p_source
	school = p_school
	speed = p_speed
	color = p_color
	z_index = 400
	z_as_relative = false


func _combat():
	if _cs != null and is_instance_valid(_cs):
		return _cs
	var ml := Engine.get_main_loop()
	if ml is SceneTree:
		_cs = (ml as SceneTree).root.get_node_or_null("CombatSystem")
	return _cs


func _physics_process(delta: float) -> void:
	lifetime -= delta
	if lifetime <= 0.0:
		queue_free()
		return
	# pygame: peluru mati kalau targetnya mati (active = False)
	if target == null or not is_instance_valid(target) or bool(target.get("is_dead")):
		queue_free()
		return
	var to: Vector2 = target.global_position - global_position
	var dist := to.length()
	var step := speed * delta
	if dist <= maxf(step, radius + float(_target_radius())):
		_on_hit()
		return
	global_position += to / dist * step
	# jejak pendek (3 titik) — murah, memberi rasa "proyektil"
	_trail.append(global_position)
	if _trail.size() > 3:
		_trail.remove_at(0)
	queue_redraw()


func _target_radius() -> float:
	if target != null and "radius" in target:
		return float(target.get("radius"))
	return 14.0


func _draw() -> void:
	# jejak
	for i in range(_trail.size()):
		var a: float = 0.18 + 0.22 * float(i)
		draw_circle(to_local(_trail[i]), radius * (0.5 + 0.16 * float(i)),
			Color(color.r, color.g, color.b, a))
	match bullet_type:
		"cannon":
			draw_circle(Vector2.ZERO, radius * 1.5, Color(0.12, 0.1, 0.09, 1))
			draw_circle(Vector2.ZERO, radius * 1.1, color)
			draw_circle(Vector2(-1.2, -1.2), radius * 0.45, Color(1, 0.85, 0.5, 0.9))
		"ice":
			draw_circle(Vector2.ZERO, radius * 1.25, Color(color.r, color.g, color.b, 0.55))
			draw_circle(Vector2.ZERO, radius * 0.75, Color(0.92, 0.98, 1, 0.95))
		"mage":
			draw_circle(Vector2.ZERO, radius * 1.2, Color(color.r, color.g, color.b, 0.5))
			draw_circle(Vector2.ZERO, radius * 0.7, color)
		_:
			# panah archer: garis pendek searah gerak
			var dir := Vector2.RIGHT
			if target != null and is_instance_valid(target):
				var d: Vector2 = target.global_position - global_position
				if d.length_squared() > 0.01:
					dir = d.normalized()
			draw_line(-dir * 7.0, dir * 7.0, color, 2.0)
			draw_circle(dir * 7.0, 1.8, Color(1, 1, 1, 0.9))


## Paritas Bullet._on_hit: damage projectile + efek khusus per jenis menara
func _on_hit() -> void:
	var cs = _combat()
	queue_free()
	if cs == null or target == null or not is_instance_valid(target):
		return
	if bool(target.get("is_dead")):
		return

	var dealt := cs.apply_damage(target, damage, team, "projectile", source, school)

	# Proyektil hero ranged juga memicu efek on-attack item, paritas
	# on_ranged_attack_hit (hero_items.py:2506-2517). Di pygame fungsi itu
	# HANYA memanggil _on_hit_common — lifesteal & cleave sudah dibayar saat
	# proyektil dilepas, jadi jangan panggil _on_attacker_hit di sini.
	# Penyaring "ini peluru hero": bullet_type "normal" juga dipakai minion,
	# boss, dan nexus, jadi yang dicek adalah adanya inventory item.
	if dealt > 0.0 and source != null and is_instance_valid(source):
		var sinv = source.get("items")
		if sinv != null and sinv.has_method("on_attack_hit"):
			sinv.on_attack_hit(target, dealt)

	var st = target.get("status")
	match bullet_type:
		"cannon":
			var splash_radius := float(special.get("splash", 40))
			var burn_dps := float(special.get("burn_dps", 0))
			var burn_duration := float(special.get("burn_duration", 0))
			# Ledakan impact cannon. pygame memakai 'bullet_hit' di sini
			# (_entity.py:331-332), tapi bullet_hit.wav memang TIDAK ADA di
			# assets/sounds/ — jadi di pygame momen ini sunyi. Port memakai
			# 'explosion' (volume kecil + throttle 120 ms di AudioManager)
			# supaya dentuman meriam terdengar tanpa menutupi suara lain.
			AudioManager.play_sfx("explosion", 0.3)
			if burn_dps > 0.0 and st != null:
				st.apply_debuff("burn", burn_dps, burn_duration, team)
			if splash_radius > 0.0:
				var center: Vector2 = target.global_position
				for u in cs.enemies_in_radius(team, center, splash_radius):
					if u == target:
						continue
					cs.apply_damage(u, floor(damage * SPLASH_RATIO), team,
						"normal", source, school)
					if burn_dps > 0.0:
						var ust = u.get("status")
						if ust != null:
							ust.apply_debuff("burn", burn_dps, burn_duration, team)
		"ice":
			var slow_amount := float(special.get("slow", 0.2))
			var slow_duration := float(special.get("slow_duration", 90.0 / FPS))
			var atk_slow := float(special.get("atk_slow", 0))
			if st != null:
				st.apply_slow(slow_amount, slow_duration)
				if atk_slow > 0.0:
					st.apply_debuff("atk_slow", atk_slow, slow_duration)
			var aoe := float(special.get("slow_aoe", 0))
			if aoe > 0.0:
				var center: Vector2 = target.global_position
				for u in cs.enemies_in_radius(team, center, aoe):
					if u == target:
						continue
					var ust = u.get("status")
					if ust == null:
						continue
					ust.apply_slow(slow_amount, slow_duration)
					if atk_slow > 0.0:
						ust.apply_debuff("atk_slow", atk_slow, slow_duration)
		"mage":
			if st == null:
				return
			var skill_down := float(special.get("skill_down", 0))
			var anti_heal := float(special.get("anti_heal", 0))
			var debuff_duration := float(special.get("debuff_duration", 120.0 / FPS))
			if skill_down > 0.0:
				st.apply_debuff("skill_down", skill_down, debuff_duration)
			if anti_heal > 0.0:
				st.apply_debuff("anti_heal", anti_heal, debuff_duration)
