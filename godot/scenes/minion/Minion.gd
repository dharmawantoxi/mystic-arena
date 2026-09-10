# Minion.gd — Port dari minions/ + _entity.Minion (goblin/orc/troll/undead/dark_rider)
# Visual baseline: UnitSilhouette pygame (telinga goblin, taring orc, ...).
# Upgrade satu-satu lewat RendererRegistry.MINION[minion_type].
#
# Update sesi ini: stat dibaca GameManager.minion_type_data() (data/economy.json),
# kena StatusEffects (slow/burn/stun dari menara), memakai CombatSystem untuk
# damage, dan ikut menyerang nexus musuh (sebelumnya berhenti di base lawan).
extends CharacterBody2D

const UnitSilhouetteScript = preload("res://scripts/render/UnitSilhouette.gd")
const RendererRegistry = preload("res://scripts/render/RendererRegistry.gd")
const BakedPropDB = preload("res://scripts/render/BakedPropDB.gd")
const StatusEffectsScript = preload("res://scripts/systems/StatusEffects.gd")
const TowerBulletScript = preload("res://scenes/tower/TowerBullet.gd")
const HurtFlashScript = preload("res://scripts/render/HurtFlash.gd")
const FPS := 60.0

@export var minion_type: String = "goblin"
@export var team: String = "blue"
## Jalur asal wave, dipakai AIPlayer untuk menghitung ancaman per lane.
@export var lane: String = "mid"
## Skala dari nexus tim sendiri, bukan wave atau nexus tim lawan.
@export var stat_scale: float = 1.0
var ai_level: int = 1
var lane_path: PackedVector2Array = PackedVector2Array()
var waypoint_index: int = 0
var regen_per_second: float = 0.0

var display_name: String = "Goblin"
var max_hp: float = 45.0
var hp: float = 45.0
var damage: float = 5.0
var move_speed: float = 90.0
var attack_range: float = 25.0
var attack_cooldown: float = 0.75
var gold_reward: int = 8
var radius: float = 9.0
var armor: float = 0.0
var magic_resist: float = 0.0
var dmg_school: String = "physical"

var target: Node2D = null
var attack_timer: float = 0.0
var is_dead: bool = false
## Kunci anti pembayaran ganda (padanan `_rewarded` pygame _core.py:2198):
## minion yang sama hanya membayar gold/skor/popup/sekali, walau die() atau
## callback reward dipanggil ulang (mayat tetap di daftar pygame selama
## death_anim; guard `_rewarded` mencegah bayar ulang tiap Game.update).
var reward_processed: bool = false
var facing: int = 1
var anim_phase: float = 0.0
var status = null

@onready var visual: Node2D = $Visual
@onready var body: Polygon2D = $Visual/Body
@onready var hp_fill: Polygon2D = $UI/HPFill

const WAYPOINT_REACH := 15.0


func _ready():
	apply_minion_data()
	waypoint_index = 0 if team == "blue" else lane_path.size() - 1
	status = StatusEffectsScript.new(self)
	build_visual()
	# Target flash: sprite bake Fase 7 kalau ada, kalau tidak badan
	# Polygon2D lama (jalur siluet). Pola HurtFlash: silhouette ->
	# custom_visual -> _extra.
	hurt_flash = HurtFlashScript.new(
		self, baked_sprite if baked_sprite != null else body)
	update_ui()
	# Teriakan spawn khusus goblin (paritas Minion.__init__ _entity.py:5495-5496,
	# volume_mult 0.7, throttle 200 ms). Jenis minion lain lahir tanpa suara —
	# suara serangan mereka baru berbunyi saat memukul (lihat try_attack).
	if minion_type == "goblin":
		AudioManager.play_sfx("goblin_spawn", 0.7)
	# Paritas Hero: layer per tim (blue=2, red=4) supaya barisan saling dorong
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2


func apply_minion_data():
	var s: Dictionary = GameManager.minion_type_data(minion_type)
	if s.is_empty():
		push_warning("[Minion] tipe tidak dikenal: %s" % minion_type)
		return
	display_name = s.get("name", minion_type)
	max_hp = float(int(float(s.get("hp", 45)) * stat_scale))
	hp = max_hp
	damage = float(int(float(s.get("damage", 5)) * stat_scale))
	move_speed = float(s.get("speed", 1.5)) * (1.0 + (stat_scale - 1.0) * 0.3) * FPS
	attack_range = float(s.get("range", 25))
	attack_cooldown = maxi(10, int(float(s.get("attack_cooldown", 45))
		/ (1.0 + (stat_scale - 1.0) * 0.2))) / FPS
	gold_reward = int(float(s.get("gold_reward", 8)) * stat_scale)
	regen_per_second = float(s.get("regen", 0.0)) * stat_scale * FPS
	radius = float(s.get("radius", 9))
	armor = float(s.get("armor", 0))
	magic_resist = float(s.get("magic_resist", 0))
	dmg_school = "physical"


## Port blok enemy scaling _core.py:1792-1796 (hanya minion merah, Hard mode):
## max_hp & damage dikali lalu dipotong int persis pygame, speed dikali
## pengali speed (base_speed pygame = move_speed kita, sudah tanpa status).
## Dipanggil GameManager._spawn_wave_minion SETELAH add_child (stat nexus via stat_scale
## sudah diterapkan _ready -> apply_minion_data).
func apply_enemy_scaling(hp_mult: float, dmg_mult: float, speed_mult: float) -> void:
	max_hp = float(int(max_hp * hp_mult))
	hp = max_hp
	damage = float(int(damage * dmg_mult))
	move_speed = move_speed * speed_mult
	update_ui()


# Bangun siluet minion dari radius + warna palette (0 file PNG dibutuhkan)
func build_visual():
	var r := radius
	if body:
		body.visible = false
	var shadow := get_node_or_null(^"Shadow")
	if shadow:
		shadow.visible = false
	hp_fill.color = Color(0.42, 0.9, 0.42, 1) if team == "blue" else Color(0.95, 0.35, 0.3, 1)
	var col := get_node_or_null(^"CollisionShape2D") as CollisionShape2D
	if col != null and col.shape is CircleShape2D:
		# PackedScene shares resources; changing one troll must not enlarge
		# every goblin collider already on the field.
		col.shape = col.shape.duplicate()
		(col.shape as CircleShape2D).radius = maxf(6.0, r)
	z_as_relative = false
	var packed: PackedScene = RendererRegistry.minion_scene(minion_type)
	if packed != null:
		custom_visual = packed.instantiate()
		custom_visual.name = "CustomVisual"
		visual.add_child(custom_visual)
		return
	# ── Fase 7: sprite minion dari bake renderer pygame (seni asli) ──
	# Sebelumnya Godot menggambar minion sebagai lingkaran/elips
	# (UnitSilhouette) padahal pygame punya 5 rig lengkap ~9.500 baris.
	# Kalau manifest tidak ada (bake belum dijalankan), jatuh ke siluet.
	var baked := BakedPropDB.minion_entry(minion_type, team)
	if not baked.is_empty():
		_build_baked(baked)
		if baked_sprite != null:
			return
	var d: Dictionary = GameManager.minion_type_data(minion_type)
	var fill := _parse_color(d.get("color", "#c8c8c8"), Color("#c8c8c8"))
	silhouette = UnitSilhouetteScript.new()
	silhouette.name = "Silhouette"
	visual.add_child(silhouette)
	var ranged := attack_range >= 80.0
	silhouette.configure(
		UnitSilhouetteScript.Kind.MINION, minion_type, team, fill, fill.darkened(0.35),
		r, display_name, dmg_school, ranged)


## Bangun Sprite2D dari strip bake minion. Satu sprite + region_rect sudah
## cukup: pose idle/walk di-loop, pose serang dipaksa dari progress seperti
## BakedSprite.gd (bukan playback).
func _build_baked(e: Dictionary) -> void:
	_baked = e
	_baked_tex = BakedPropDB.texture(str(e.get("png", "")))
	if _baked_tex == null:
		return
	var sp := Sprite2D.new()
	sp.name = "BakedMinion"
	sp.texture = _baked_tex
	sp.centered = false
	# Titik jangkar (telapak kaki) harus jatuh di origin $Visual, sama
	# dengan kontrak UnitSilhouette.gd.
	sp.offset = -BakedPropDB.anchor(e)
	sp.region_enabled = true
	visual.add_child(sp)
	baked_sprite = sp
	_set_baked_frame(_first_frame("idle"))


func _anim_frames(act: String) -> Array:
	var anims = _baked.get("anims", {})
	var spec = anims.get(act, []) if anims is Dictionary else []
	return spec if spec is Array else []


func _first_frame(act: String) -> int:
	var fr := _anim_frames(act)
	return int(fr[0]) if not fr.is_empty() else 0


func _set_baked_frame(index: int) -> void:
	if baked_sprite == null or _baked_tex == null:
		return
	var region := BakedPropDB.frame_region(_baked, index)
	if region.size.x <= 0.0:
		return
	baked_sprite.region_rect = region


## act = "idle" | "walk" | "attack"; ap = 0..1 progress serang.
func _drive_baked(act: String, ap: float, delta: float) -> void:
	if baked_sprite == null:
		return
	var frames := _anim_frames(act)
	if frames.is_empty():
		return
	if act == "attack":
		# Pose serang di-drive countdown pygame (attack_anim_timer turun
		# dari 24), bukan playback — index dipaksa dari progress.
		var i := clampi(int(ap * float(frames.size())), 0, frames.size() - 1)
		_set_baked_frame(int(frames[i]))
		return
	var fps_table = _baked.get("fps", {})
	var fps := float((fps_table as Dictionary).get(act, 8.0)) if fps_table is Dictionary else 8.0
	_baked_t += delta * fps
	var j := int(_baked_t) % frames.size()
	_set_baked_frame(int(frames[j]))


var silhouette = null
var custom_visual = null
## Sprite bake Fase 7 (null = tidak ada bake, pakai siluet).
var baked_sprite: Sprite2D = null
var _baked: Dictionary = {}
var _baked_tex: Texture2D = null
var _baked_t: float = 0.0
## Flash putih hurt_flash_timer pygame (_entity.py:5545-5551) — lihat HurtFlash.gd
var hurt_flash = null


func _physics_process(delta):
	if is_dead or GameManager.state != "playing":
		return
	if hurt_flash != null:
		hurt_flash.tick(self, delta)
	if status != null:
		status.tick(delta)
	if is_dead:
		return
	if regen_per_second > 0.0:
		CombatSystem.heal_unit(self, regen_per_second * delta)
	attack_timer = maxf(0.0, attack_timer - delta)
	anim_phase += delta * 8.0
	# Pilih ulang tiap tick supaya tidak mengejar target keluar dari lane.
	target = _find_target_smart()

	var is_moving := false
	var eff_speed := _eff_speed()
	if target != null:
		var dist := global_position.distance_to(target.global_position)
		facing = 1 if target.global_position.x >= global_position.x else -1
		visual.scale.x = facing
		if dist <= attack_range:
			velocity = Vector2.ZERO
			try_attack()
		else:
			is_moving = _move_to(target.global_position, eff_speed)
	else:
		is_moving = _follow_lane(eff_speed)
	z_index = int(global_position.y)
	_drive_visual(is_moving, delta)


## _entity.Minion._move_forward: blue mengikuti path dari awal, red dari akhir.
## Setelah ujung lane, lanjut ke nexus lawan. Bukan shortcut diagonal semua lane.
func _follow_lane(speed: float) -> bool:
	var dest := enemy_base()
	if waypoint_index >= 0 and waypoint_index < lane_path.size():
		dest = lane_path[waypoint_index]
	if global_position.distance_to(dest) < WAYPOINT_REACH:
		waypoint_index += 1 if team == "blue" else -1
		velocity = Vector2.ZERO
		return false
	return _move_to(dest, speed)


## Radius aggro = range + 30; prioritas naik bersama level nexus.
func _find_target_smart() -> Node2D:
	var nearby: Array = CombatSystem.enemies_in_radius(team, global_position, attack_range + 30.0)
	if nearby.is_empty():
		return null
	var in_range: Array = []
	for enemy in nearby:
		if global_position.distance_to(enemy.global_position) <= attack_range:
			in_range.append(enemy)
	if in_range.is_empty():
		return _nearest(nearby)
	match ai_level:
		1:
			return _nearest(in_range)
		2:
			for enemy in in_range:
				if enemy.is_in_group("minions") and enemy.lane == lane:
					return enemy
		3:
			return _lowest_hp(in_range)
		4, 5:
			if ai_level == 5:
				for enemy in in_range:
					if enemy.max_hp >= 1500:
						return enemy
				var towers := in_range.filter(func(e): return e.is_in_group("towers"))
				if not towers.is_empty():
					return _lowest_hp(towers)
			var minions := in_range.filter(func(e): return e.is_in_group("minions"))
			if not minions.is_empty():
				return _lowest_hp(minions)
			if ai_level == 4:
				return _nearest(in_range)
	return in_range[0]


func _nearest(units: Array) -> Node2D:
	units.sort_custom(func(a, b): return global_position.distance_squared_to(a.global_position) \
		< global_position.distance_squared_to(b.global_position))
	return units[0]


func _lowest_hp(units: Array) -> Node2D:
	units.sort_custom(func(a, b): return a.hp < b.hp)
	return units[0]


func _move_to(dest: Vector2, speed: float) -> bool:
	if speed <= 1.0:
		velocity = Vector2.ZERO
		return false
	var to := dest - global_position
	if to.length() <= 6.0:
		velocity = Vector2.ZERO
		return false
	velocity = to.normalized() * speed
	facing = 1 if velocity.x >= 0.0 else -1
	visual.scale.x = facing
	move_and_slide()
	return true


func _eff_speed() -> float:
	return move_speed * (status.move_speed_mult() if status != null else 1.0)


func _eff_attack_cd() -> float:
	return status.attack_cd(attack_cooldown) if status != null else attack_cooldown


func _drive_visual(is_moving: bool, delta: float = 0.0) -> void:
	var ap := 0.0
	if attack_timer > 0.0:
		ap = 1.0 - attack_timer / maxf(0.001, _eff_attack_cd())
	var act := "idle"
	if attack_timer > 0.0:
		act = "attack"
	elif is_moving:
		act = "walk"
	if baked_sprite != null and is_instance_valid(baked_sprite):
		_drive_baked(act, ap, delta)
		return
	if silhouette != null and is_instance_valid(silhouette) and silhouette.has_method("drive"):
		silhouette.drive(anim_phase, act, ap, facing)
	elif custom_visual != null and is_instance_valid(custom_visual) and custom_visual.has_method("drive"):
		custom_visual.drive(anim_phase, act, ap, facing, is_moving, "", 0.016)


static func _parse_color(v, fallback: Color) -> Color:
	if v is Color:
		return v
	var s := str(v).strip_edges()
	if s.is_empty():
		return fallback
	if not s.begins_with("#"):
		s = "#" + s
	var c := Color(s)
	if c.a == 0.0 and s != "#00000000":
		return fallback
	return c


func enemy_base() -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_enemy_base"):
		return am.get_enemy_base(team)
	return Vector2(1180, 100) if team == "blue" else Vector2(100, 620)


func try_attack():
	if attack_timer > 0.0 or target == null:
		return
	attack_timer = _eff_attack_cd()
	# Pukulan SEMUA jenis minion memakai satu suara global (paritas
	# Minion.update _entity.py:5585-5591 — combat_audio.MINION_HIT, volume
	# dasar 0.50, jeda 140 ms). Dulu hanya goblin yang berbunyi.
	AudioManager.play_combat("minion_hit")
	var dmg := CombatSystem.calc_damage(self, target, damage, dmg_school)
	if attack_range >= 80.0:
		# Undead = ranged: proyektil (bisa ditangkis Wind Wall). pygame
		# Minion.update menyerang INSTAN take_damage(damage, team) — NETRAL
		# tanpa source & school (paritas _entity.py:5580-5581) — jadi
		# proyektil ini juga netral; sisa deviasi (projectile vs instant)
		# terbuka di docs/GODOT_PARITY.md. Source TETAP null: minion tidak
		# pernah memberi kill credit / reflect Bristleback-Thornmail /
		# blind (syarat source is not None di pygame).
		var b = TowerBulletScript.new()
		b.setup(target, dmg, team, "normal", {}, 420.0,
			Color(0.85, 0.85, 0.95), null, "")
		b.global_position = global_position + Vector2(0, -6)
		GameManager.attach_fx(b)
	else:
		CombatSystem.apply_damage(target, dmg, team, "normal", null, "")


func take_damage(amount: float, from_team: String = "", dmg_type: String = "normal",
		source = null, school: String = ""):
	if is_dead:
		return
	var before := hp
	CombatSystem.apply_damage(self, amount, from_team, dmg_type, source, school)
	if hp < before:
		_flash()
	update_ui()
	if hp <= 0.0:
		die(from_team)


## Nyalakan flash manual (dipertahankan untuk pemanggil lama seperti
## take_damage). Sebenarnya sudah redundan: HurtFlash.tick() memantau `hp`
## sehingga damage dari jalur MANA PUN — termasuk CombatSystem.apply_damage
## yang dipakai serangan hero/menara — tetap memicu flash.
func _flash() -> void:
	if hurt_flash != null:
		hurt_flash.trigger()


func heal(amount: float) -> void:
	if is_dead:
		return
	CombatSystem.heal_unit(self, amount)
	update_ui()


func die(killer_team: String = ""):
	if is_dead:
		return
	is_dead = true
	hp = 0.0
	set_physics_process(false)
	collision_layer = 0
	collision_mask = 0
	target = null
	# Suara kematian GLOBAL semua jenis minion (paritas Minion.take_damage
	# _entity.py:5854-5856, volume_mult 0.7, throttle 120 ms).
	AudioManager.play_sfx("minion_death", 0.7)
	if status != null:
		status.clear()
	# Loop reward Game.update pygame (_core.py:2196-2216, cabang TIM KORBAN):
	# gold+skor+popup +nG+total_kills+combo untuk minion RED, gold AI untuk
	# minion biru — SEKARANG lewat register_minion_death (dulu award_kill(
	# killer_team), beda untuk sumber damage netral: pygame tetap membayar tim
	# lawan korban). Popup gold +nG + kunci anti dobel ada di GameManager
	# (paritas EffectManager.add_gold_popup). Combo: max_combo dibaca SEBELUM
	# add_kill (quirk pygame).
	GameManager.register_minion_death(self)
	GameManager.minion_died.emit(self, killer_team)
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.3)
	tw.parallel().tween_property(visual, "scale", Vector2(1.3, 0.25), 0.22)
	tw.tween_callback(queue_free)


func update_ui():
	if hp_fill:
		hp_fill.scale.x = clampf(hp / maxf(1.0, max_hp), 0.0, 1.0)
