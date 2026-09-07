# Hero.gd — Port dari _entity.py Hero class
# Visual default: strip bake renderer Pygame, termasuk Kaizen.
# UnitSilhouette adalah fallback; rig RendererRegistry.HERO bersifat opt-in.
#
# Yang ditambahkan di sesi port ini (sebelumnya hanya stats + AI hunt):
#   • ItemInventory (6 slot, 33 item) — damage/HP/armor/crit/lifesteal/cleave/
#     attack speed/CDR/spell vamp/skill amp/evasion, semua cap sama dengan pygame.
#   • SkillBook QWER — 6 hero starter port 1:1 dari hero_skills/, sisanya generik.
#   • StatusEffects — slow/atk_slow/burn/skill_down/anti_heal/stun dari menara,
#     plus buff skill (Warpath, Focus Fire, Windrun, Bristleback, Shadow Realm).
#   • Level hero 1..15 (HERO_LEVELS: hp/dmg/skill multiplier + upgrade_cost).
#   • Regen: 180 HP/s di dekat base sendiri, 9 HP/s di luar (paritas 3.0 & 0.15/frame).
#   • Retreat: HP < 20% mundur ke base sampai 60% (paritas is_retreating sederhana).
#   • Serangan ranged = proyektil (bukan damage instan) supaya Wind Wall berguna.
extends CharacterBody2D

const UnitSilhouetteScript = preload("res://scripts/render/UnitSilhouette.gd")
const RendererRegistry = preload("res://scripts/render/RendererRegistry.gd")
const StatusEffectsScript = preload("res://scripts/systems/StatusEffects.gd")
const ItemInventoryScript = preload("res://scripts/items/ItemInventory.gd")
const SkillBookScript = preload("res://scripts/skills/SkillBook.gd")
const TowerBulletScript = preload("res://scenes/tower/TowerBullet.gd")
const SkillProjectileScript = preload("res://scenes/fx/SkillProjectile.gd")
const HurtFlashScript = preload("res://scripts/render/HurtFlash.gd")

const FPS := 60.0
## paritas _entity.Hero 3467-3472
const HUNT_RANGE := 900.0
const AGGRO_RANGE := 250.0
const BASE_HEAL_PER_SEC := 3.0 * FPS      # base_heal_rate 3.0/frame
const PASSIVE_HEAL_PER_SEC := 0.15 * FPS  # passive_heal_rate 0.15/frame
const BASE_HEAL_RADIUS := 100.0
## Retreat: masuk saat HP < 20%, keluar saat HP >= 80% — paritas
## retreat_hp_ratio / heal_target_ratio _entity.py:3469-3473. Godot lama
## keluar di 60% (RETREAT_UNTIL 0.60) sehingga hero kembali bertarung 170 HP
## lebih cepat dari pygame; sekarang disamakan 1:1.
const RETREAT_BELOW := 0.20
const RETREAT_UNTIL := 0.80

@export var hero_type: String = "kaizen"
@export var team: String = "blue"

# ── Stat dasar (dari HeroDB, sebelum level & item) ──
var base_hp: float = 850.0
var base_damage: float = 72.0
var base_speed: float = 180.0        # px/s (pygame speed × 60)
var base_attack_cd: float = 0.52     # detik (frame / 60)
var base_range: float = 70.0
var skill_damage_base: float = 80.0

# ── Stat efektif ──
var max_hp: float = 850.0
var hp: float = 850.0
var damage: float = 72.0
var move_speed: float = 180.0
var attack_range: float = 70.0
var attack_cooldown: float = 0.52
var skill_damage: float = 80.0
var skill_range: float = 100.0
var skill_cooldown_frames: float = 300.0
var skill_name: String = ""
var dmg_school: String = "physical"
var armor: float = 0.0
var magic_resist: float = 0.0
var radius: float = 16.0
var role: String = ""
var level: int = 1
var is_melee_hero: bool = true
var fill_color: Color = Color("#c8c8c8")
var fill_dark: Color = Color("#646464")

# ── State ──
var target: Node2D = null
var attack_timer: float = 0.0
var is_dead: bool = false
var facing: int = 1
var selected: bool = false
var is_retreating: bool = false
var combat_timer: float = 0.0        # di-reset CombatSystem saat kena damage
var combat_reset: float = 5.0
var auto_cast_timer: float = 0.0
## Hero milik pemain yang sedang dipilih -> skill tidak di-auto-cast
var player_controlled: bool = false
## Destination AI (paritas destination / destination_auto _entity.py:4045-4085).
## `destination_auto` = perintah dari AIPlayer (bukan ketukan pemain): dibatalkan
## segera setelah ada musuh dalam aggro_range supaya hero menyergap target di
## perjalanan, bukan berbaris lurus ke titik jalur (fix _entity.py:4038-4048).
var destination: Vector2 = Vector2.INF
var destination_auto: bool = false
## Kill hero-vs-hero (paritas _core.py:2506-2515 _process_hero_kill) — dipakai
## AIPlayer sebagai prioritas upgrade & beli item (sort by kills pygame).
var kills: int = 0

# ── Sistem ──
var status = null      # StatusEffects
var items = null       # ItemInventory
var skills = null      # SkillBook

# ── Visual nodes (di-assign di _ready) ──
@onready var sprite: AnimatedSprite2D = $Visual/AnimatedSprite2D
@onready var visual_root: Node2D = $Visual
@onready var shadow: Node2D = $Shadow # Polygon2D ellipse (0 asset)
@onready var hp_bar: ProgressBar = $UI/HPBar
@onready var name_label: Label = $UI/NameLabel
# CPUParticles2D (bukan GPU) — lihat catatan di Hero.tscn: aman di
# Compatibility renderer Android/GLES dan tidak butuh shader partikel.
@onready var hit_particles: CPUParticles2D = $FX/HitParticles
@onready var skill_particles: CPUParticles2D = $FX/SkillParticles
@onready var anim_player: AnimationPlayer = $AnimationPlayer

## Jeda minimum antar burst HitParticles (detik) — lihat play_hit_fx()
const HIT_FX_COOLDOWN := 0.08
var _hit_fx_cd: float = 0.0

var silhouette = null
var custom_visual = null
var anim_phase: float = 0.0
var hit_flash_mat: ShaderMaterial
## Flash putih bersama Minion/Boss (scripts/render/HurtFlash.gd). watch_hp =
## false: hero HANYA berkedip lewat trigger() — lihat play_hit_fx().
var hurt_flash = null

# ── FX ring skill (digambar di _draw, tanpa butuh asset partikel) ──
var _ring_radius: float = 0.0
var _ring_alpha: float = 0.0
var _ring_color: Color = Color(1, 0.9, 0.5)


func _ready():
	apply_hero_data()
	items = ItemInventoryScript.new(self)
	status = StatusEffectsScript.new(self)
	skills = SkillBookScript.new()
	skills.setup(self)
	_recalc_derived(true)
	setup_visual()
	# Setelah setup_visual supaya silhouette/custom_visual/hit_flash_mat
	# yang dipilih renderer sudah ada saat HurtFlash memilih target tint.
	hurt_flash = HurtFlashScript.new(self, hit_flash_mat, false)
	update_ui()
	# Godot physics: collision layer beda per team (blue=2, red=4)
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2


func apply_hero_data():
	var s = HeroDB.get_balanced_stats(hero_type)
	if s.is_empty():
		push_warning("Unknown hero: %s" % hero_type)
		return
	base_hp = float(s["hp"])
	base_damage = float(s["damage"])
	base_speed = float(s["speed"]) * FPS   # pygame speed 1.6 -> Godot 96 px/s
	base_attack_cd = float(s["attack_cooldown"]) / FPS
	base_range = float(s["range"])
	skill_damage_base = float(s.get("skill_damage", 80))
	skill_range = float(s.get("skill_range", 100))
	skill_cooldown_frames = float(s.get("skill_cooldown", 300))
	skill_name = str(s.get("skill_name", ""))
	dmg_school = str(s.get("dmg_school", "physical"))
	role = str(s.get("role", ""))
	name = s.get("name", hero_type)
	fill_color = _parse_color(s.get("color", "#c8c8c8"), Color("#c8c8c8"))
	fill_dark = _parse_color(s.get("color_dark", ""), fill_color.darkened(0.35))
	radius = 16.0
	if skills != null:
		skills.setup(self)


## Hitung ulang stat turunan dari level + item (paritas _apply_level_stats +
## _recalc_item_stats). `full_heal` hanya saat spawn pertama.
func _recalc_derived(full_heal: bool = false) -> void:
	var lvl: Dictionary = HeroDB.level_data(level)
	damage = float(int(base_damage * float(lvl.get("dmg_mult", 1.0))))
	skill_damage = float(int(skill_damage_base * float(lvl.get("skill_mult", 1.0))))
	var base_max := float(int(base_hp * float(lvl.get("hp_mult", 1.0))))
	var old_max := max_hp
	max_hp = float(items.get_max_hp(base_max)) if items != null else base_max
	if full_heal or old_max <= 0.0:
		hp = max_hp
	elif max_hp > old_max:
		hp = minf(max_hp, hp + (max_hp - old_max))
	elif hp > max_hp:
		hp = max_hp
	# Armor hero HANYA dari item/aura (paritas Hero.take_damage pygame 4640-4650)
	armor = float(items.get_armor()) if items != null else 0.0
	attack_range = base_range + (float(items.get_range_bonus()) if items != null else 0.0)
	is_melee_hero = attack_range < 110.0
	move_speed = base_speed
	attack_cooldown = base_attack_cd
	update_ui()


func setup_visual():
	# Sprite kosong legacy dimatikan. Registry memilih bake asli, rig
	# opt-in, atau silhouette bila resource visual belum tersedia.
	if sprite:
		sprite.visible = false
		# Material outline Hero.tscn punya uniform `flash_amount`; disimpan
		# supaya HurtFlash punya jalur ketiga kalau suatu saat sprite HD
		# dipakai (silhouette/custom_visual tetap prioritas). Sebelumnya
		# `hit_flash_mat` dideklarasikan tapi tidak pernah diisi = cabang mati.
		if sprite.material is ShaderMaterial:
			hit_flash_mat = sprite.material
	if shadow:
		shadow.visible = false
	z_as_relative = false
	var packed: PackedScene = RendererRegistry.hero_scene(hero_type)
	if packed != null:
		custom_visual = packed.instantiate()
		custom_visual.name = "CustomVisual"
		visual_root.add_child(custom_visual)
		if custom_visual.has_method("configure_baked"):
			# Strip bake Fase 5: anchor sprite = telapak kaki, sama
			# seperti UnitSilhouette — offset -6 di bawah hanya untuk
			# rig tulang hand-made (Kaizen), jadi dibalikkan ke 0.
			custom_visual.position = Vector2.ZERO
			custom_visual.configure_baked(hero_type, "hero", team)
		else:
			custom_visual.position = Vector2(0, -6)
		return
	silhouette = UnitSilhouetteScript.new()
	silhouette.name = "Silhouette"
	visual_root.add_child(silhouette)
	silhouette.configure(
		UnitSilhouetteScript.Kind.HERO, hero_type, team, fill_color, fill_dark,
		radius, role, dmg_school, not is_melee_hero)


# ══════════════════════════════════════════════════════════
#  LOOP
# ══════════════════════════════════════════════════════════

func _physics_process(delta):
	if is_dead or GameManager.state != "playing":
		return
	if status != null:
		status.tick(delta)
	if is_dead:
		return
	if skills != null:
		skills.tick(delta)
	# Item aktif auto-trigger (paritas inv.update(1, enemies) _entity.py:3801).
	# 17 item "aktif" pygame tidak punya tombol — semuanya terpicu sendiri
	# dari HP/jumlah musuh/target, jadi cukup dipanggil di sini.
	if items != null:
		items.tick(delta)
	attack_timer = maxf(0.0, attack_timer - delta)
	combat_timer = maxf(0.0, combat_timer - delta)
	_hit_fx_cd = maxf(0.0, _hit_fx_cd - delta)
	if hurt_flash != null:
		hurt_flash.tick(self, delta)
	anim_phase += delta * 6.0  # phase untuk Skeleton2D (breath + stride)

	_regen(delta)
	_auto_cast(delta)

	# AI sederhana: cari target terdekat (port dari Hero._find_hunt_target)
	if not target or not is_instance_valid(target) or bool(target.get("is_dead")):
		target = CombatSystem.nearest_enemy(self, HUNT_RANGE)

	# ═══ RETREAT MASUK/KELUAR (paritas _entity.py:3983-3994) ═══
	# Dicek SEBELUM state machine supaya transisi terjadi di frame yang sama:
	# masuk saat hp_ratio < 0.20, keluar saat sudah >= 0.80.
	var hp_ratio := hp / max_hp if max_hp > 0.0 else 0.0
	if hp_ratio < RETREAT_BELOW:
		is_retreating = true
	if is_retreating and hp_ratio >= RETREAT_UNTIL:
		is_retreating = false

	var is_moving := false
	var eff_speed := _eff_speed()

	# ── 1. RETREAT + HEAL (paritas _entity.py:4006-4028) ──
	# Jalan ke base; di dekat base berhenti dan heal 180 HP/s (_regen);
	# sambil jalan ATAU heal, tetap serang musuh yang masuk attack range.
	if is_retreating:
		var base := own_base()
		var foe := CombatSystem.nearest_enemy(self, attack_range)
		if foe != null:
			target = foe
			try_attack()
		else:
			target = null
		if global_position.distance_to(base) > BASE_HEAL_RADIUS:
			is_moving = _move_to(base, eff_speed)

	# ── 2. DESTINATION AI / pemain (paritas _entity.py:4040-4085) ──
	# Destination auto (dari AIPlayer._assign_hero_lane) dibuang begitu ada
	# musuh dalam aggro_range sehingga hero menyergap di perjalanan. Sambil
	# jalan tetap menyerang musuh dalam range.
	elif has_destination():
		var dpos := destination
		if destination_auto and CombatSystem.nearest_enemy(self, AGGRO_RANGE) != null:
			clear_destination()
		else:
			var dist := global_position.distance_to(dpos)
			if dist <= 8.0:
				clear_destination()
			else:
				var dfoe := CombatSystem.nearest_enemy(self, attack_range)
				if dfoe != null:
					target = dfoe
					try_attack()
				is_moving = _move_to(dpos, eff_speed)
	elif target != null:
		var dist = global_position.distance_to(target.global_position)
		facing = 1 if target.global_position.x > global_position.x else -1
		visual_root.scale.x = facing # flip sprite / skeleton
		if dist <= attack_range:
			velocity = Vector2.ZERO
			try_attack()
		else:
			is_moving = _move_to(target.global_position, eff_speed)
	else:
		# Push ke base musuh (mirip pygame PUSH) — titiknya diambil dari ArenaMap
		is_moving = _move_to(enemy_base(), eff_speed * 0.6)

	# Painter's algorithm pygame: unit lebih bawah menutupi yang di atas
	z_index = int(global_position.y)
	_drive_visual(is_moving, delta)
	if _ring_alpha > 0.0 or selected:
		queue_redraw()


func _move_to(dest: Vector2, speed: float) -> bool:
	if speed <= 1.0:
		velocity = Vector2.ZERO
		return false
	var to := dest - global_position
	if to.length() <= 8.0:
		velocity = Vector2.ZERO
		return false
	velocity = to.normalized() * speed
	facing = 1 if velocity.x >= 0.0 else -1
	visual_root.scale.x = facing
	move_and_slide()
	return true


## Posisi tujuan AI/pemain (paritas move_to(x, y, auto) _entity.py:
## destination tuple + destination_auto). `auto=true` = perintah AIPlayer,
## dibatalkan oleh aggro (lihat _physics_process state 2).
func set_destination(dest: Vector2, auto: bool = false) -> void:
	destination = dest
	destination_auto = auto


func clear_destination() -> void:
	destination = Vector2.INF
	destination_auto = false


func has_destination() -> bool:
	return destination != Vector2.INF


## Speed efektif: slow menara, buff Windrun, item move speed, stun (paritas _eff_speed)
func _eff_speed() -> float:
	var mult := 1.0
	if status != null:
		mult = status.move_speed_mult()
	return move_speed * mult


## Attack cooldown efektif: atk_slow menara, attack speed item, buff skill
func _eff_attack_cd() -> float:
	if status != null:
		return status.attack_cd(attack_cooldown)
	return attack_cooldown


## Regen: 180 HP/s di base sendiri, 9 HP/s di luar + hp_regen item (per detik)
func _regen(delta: float) -> void:
	if hp >= max_hp:
		return
	var rate := PASSIVE_HEAL_PER_SEC
	if global_position.distance_to(own_base()) < BASE_HEAL_RADIUS:
		rate = BASE_HEAL_PER_SEC
	if items != null:
		rate += float(items.get_hp_regen())
		# Leviathan Vitality hanya menyembuhkan saat luar tempur
		# (hero_items.py:2428-2437), memakai combat_timer yang sudah ada.
		rate += float(items.get_out_of_combat_regen())
	if rate <= 0.0:
		return
	CombatSystem.heal_unit(self, rate * delta)


## AI memakai skill sendiri; hero yang dipilih pemain menunggu input Q/W/E/R.
## Paritas _try_auto_cast _entity.py:4149-4240 — kombo prioritas:
##   R (kapan pun siap) → E (2+ musuh di skill_range) → W (HP < 40%) → Q.
## Godot lama salah urut (R butuh 3+ musuh, Q didahulukan) sehingga
## ultimate & skill defensive nyaris tidak pernah dipakai AI.
func _auto_cast(delta: float) -> void:
	if player_controlled or skills == null:
		return
	# pygame _disabled = stun atau Tempest Veil (_entity.py:3801-3802):
	# keduanya menonaktifkan pencarian auto-cast sepenuhnya.
	if status != null and status.has_method("is_stunned") and status.is_stunned():
		return
	if items != null and items.is_veiled():
		return
	auto_cast_timer -= delta
	if auto_cast_timer > 0.0:
		return
	auto_cast_timer = 0.4
	# Musuh hidup dalam skill_range; kalau tidak ada, JANGAN cast apa pun
	# (aturan ketat anti buang skill ke area kosong, _entity.py:4161-4164).
	var enemies := CombatSystem.enemies_in_radius(team, global_position, skill_range)
	if enemies.is_empty():
		return
	# Target = musuh TERDEKAT dalam skill_range (bukan target serangan yang
	# bisa berada di luar jangkauan skill) — paritas _entity.py:4173-4177.
	var nearest: Node2D = null
	var nd := 1e18
	for e in enemies:
		var d: float = global_position.distance_to((e as Node2D).global_position)
		if d < nd:
			nd = d
			nearest = e as Node2D
	target = nearest
	# 1. R: ultimate dipakai kapan pun cooldown siap — kondisi 3+ musuh yang
	# hampir tidak pernah terpenuhi membuat R terdengar mati (_entity.py:4179).
	if skills.is_ready("r"):
		if skills.cast("r"):
			return
	# 2. E: hanya kalau 2+ musuh dekat (AI_SKILL_USE_MIN_ENEMIES _core.py:1097).
	if skills.is_ready("e") and enemies.size() >= 2:
		skills.cast("e")
		return
	# 3. W: defensive, hanya saat HP < 40%.
	if skills.is_ready("w") and hp < max_hp * 0.4:
		skills.cast("w")
		return
	# 4. Q: basic, paling sering.
	if skills.is_ready("q"):
		skills.cast("q")


func _drive_visual(is_moving: bool, delta: float) -> void:
	var ap := 0.0
	var cd := _eff_attack_cd()
	if attack_timer > 0.0:
		ap = 1.0 - attack_timer / maxf(0.001, cd)
	var act := "idle"
	if attack_timer > 0.0:
		act = "attack"
	elif is_moving:
		act = "walk"
	var skill_key := ""
	if skills != null:
		skill_key = str(skills.active_skill)
	if silhouette != null and is_instance_valid(silhouette) and silhouette.has_method("drive"):
		silhouette.drive(anim_phase, act, ap, facing)
	elif custom_visual != null and is_instance_valid(custom_visual) and custom_visual.has_method("drive"):
		custom_visual.drive(anim_phase, act, ap, facing, is_moving, skill_key, delta)


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


func own_base() -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_own_base"):
		return am.get_own_base(team)
	return Vector2(100, 620) if team == "blue" else Vector2(1180, 100)


func enemy_base() -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_enemy_base"):
		return am.get_enemy_base(team)
	return Vector2(1180, 100) if team == "blue" else Vector2(100, 620)


# ══════════════════════════════════════════════════════════
#  SERANG
# ══════════════════════════════════════════════════════════

func try_attack():
	if attack_timer > 0:
		return
	if not target or not is_instance_valid(target) or bool(target.get("is_dead")):
		return
	attack_timer = _eff_attack_cd()
	# Animasi attack (5x lebih smooth dari pygame 6 frame)
	if sprite.sprite_frames and sprite.sprite_frames.has_animation("attack"):
		sprite.play("attack")
		if not sprite.animation_finished.is_connected(func(): sprite.play("idle")):
			sprite.animation_finished.connect(func(): sprite.play("idle"), CONNECT_ONE_SHOT)
	# Hit-stop + screenshake (menggantikan combat_feel.hit_stop pygame)
	GameManager.request_hit_stop(0.03)
	if get_tree() and get_tree().has_group("camera"):
		get_tree().call_group("camera", "add_trauma", 0.15)

	var dmg := CombatSystem.calc_damage(self, target, damage, dmg_school)
	# Suara serangan dasar: tebasan (melee) atau lesatan (ranged). Paritas
	# combat_audio.play_hero_basic dipanggil dari Hero._attack _entity.py:4412-4418:
	# flag is_melee_hero lebih dulu, kalau tidak ada pakai ambang jarak 100.
	# Berlaku untuk hero tim biru MAUPUN merah (pygame tidak membedakan tim).
	AudioManager.play_combat(AudioManager.basic_attack_sfx(is_melee_hero, attack_range))
	if is_melee_hero:
		var t = target
		var dealt := CombatSystem.apply_damage(t, dmg, team, "normal", self, dmg_school)
		# Efek on-attack item (bash/chain/frostbite/miasma/empower/entangle).
		# Sengaja dipanggil DI SINI, bukan di CombatSystem.apply_damage: pygame
		# hanya memicunya dari on_basic_attack_hit / on_ranged_attack_hit
		# (hero_items.py:2484-2517), jadi damage skill & DoT tidak boleh ikut
		# nge-proc bash/chain. Pasangan ranged-nya ada di TowerBullet._hit.
		if dealt > 0.0 and items != null and items.has_method("on_attack_hit"):
			items.on_attack_hit(t, dealt)
	else:
		_shoot_projectile(target, dmg)


## Hero ranged menembak proyektil (paritas Bullet pygame): bisa ditangkis
## Wind Wall Kaizen dan bisa meleset karena evasion.
func _shoot_projectile(t: Node2D, dmg: float) -> void:
	var b = TowerBulletScript.new()
	b.setup(t, dmg, team, "normal", {}, 520.0,
		fill_color.lightened(0.35), self, dmg_school)
	b.global_position = global_position + Vector2(0, -10)
	GameManager.attach_fx(b)


## Proyektil skill visual-only (paritas _spawn_skill_projectile
## _entity.py:4509-4530). Damage otoritatif tetap instan di SkillBook —
## sama seperti pygame; proyektil ini HANYA memberi visual homing terarah.
func spawn_skill_projectile(t: Node2D) -> void:
	if t == null or not is_instance_valid(t) or bool(t.get("is_dead")):
		# Paritas _spawn_projectile _entity.py:4460-4462: target hilang/mati
		# -> tidak ada proyektil sama sekali.
		return
	# Batas 6 proyektil per hero (paritas _HERO_PROJ_MAX _entity.py:3225-3232).
	# pygame saat penuh MEMBUANG proyektil skill paling tua (4474-4482), jadi di
	# sini yang di-drop juga proyektil skill tertua milik hero ini. Deviasi
	# kecil: peluru basic attack (TowerBullet) tidak ikut dihitung — node
	# terpisah dengan batas umur sendiri (4 detik) dan mati saat target mati.
	if get_tree() != null:
		var owned: Array = []
		for p in get_tree().get_nodes_in_group("skill_projectiles"):
			if p.get("source") == self:
				owned.append(p)
		if owned.size() >= 6:
			var oldest = null
			for p in owned:
				if oldest == null or float(p.get("age")) > float(oldest.get("age")):
					oldest = p
			if oldest != null:
				(oldest as Node).queue_free()
	var p = SkillProjectileScript.new()
	p.setup(t, hero_type, self)
	# Spawn sedikit di atas hero (paritas oy = self.y - 5, arah awal langsung
	# ke target _entity.py:4491-4493).
	p.global_position = global_position + Vector2(0, -5)
	GameManager.attach_fx(p)


# ══════════════════════════════════════════════════════════
#  DAMAGE & MATI
# ══════════════════════════════════════════════════════════

func take_damage(amount: float, from_team: String, dmg_type: String = "normal",
		source = null, school: String = ""):
	if is_dead:
		return
	var before := hp
	CombatSystem.apply_damage(self, amount, from_team, dmg_type, source, school)
	if hp < before:
		_flash()
		# Hook item yang bereaksi saat pemilik KENA damage — Static Charge
		# (thunder_coil) proc 20% di sini, bukan saat menyerang
		# (paritas on_damage_taken hero_items.py:2440-2457). Dipanggil dengan
		# damage yang benar-benar mengurangi HP (setelah armor/block/shield).
		if items != null:
			items.on_damage_taken(before - hp)
	if hp <= 0:
		die(source)
	update_ui()


## Burst partikel + flash saat hero KENA damage SKILL.
##
## KENAPA tidak dipanggil dari take_damage/CombatSystem.apply_damage:
## kontrak pemilik game (dikunci tools/test_basic_attack_no_impact_fx.py dan
## komentar _entity.py:4376-4384) = SERANGAN DASAR tidak boleh punya impact FX
## sama sekali, karena tumpukan flash+spark tiap pukulan bikin combat ramai
## kedap-kedip. Impact FX eksklusif milik SKILL (paritas notify_skill_impact
## hero_skills/_bundle.py), jadi pemanggilnya SkillBook._damage().
func play_hit_fx(col: Color = Color(1.0, 0.72, 0.55)) -> void:
	if is_dead:
		return
	# Skill AoE + ticker DoT bisa memanggil ini beberapa kali dalam satu
	# frame; restart() beruntun justru MEMBATALKAN burst sebelumnya (dan
	# boros). Satu burst per 0,08 detik sudah terbaca sebagai "kena".
	if _hit_fx_cd > 0.0:
		return
	_hit_fx_cd = HIT_FX_COOLDOWN
	_flash()
	if hit_particles != null:
		hit_particles.color = Color(col.r, col.g, col.b, 0.9)
		hit_particles.restart()
		hit_particles.emitting = true


## Flash putih 8 frame. Dipanggil take_damage() dan play_hit_fx() — TIDAK
## dari deteksi hp seperti minion/boss (lihat watch_hp di HurtFlash.gd).
func _flash() -> void:
	if hurt_flash != null:
		hurt_flash.trigger()


func heal(amount: float) -> void:
	if is_dead:
		return
	CombatSystem.heal_unit(self, amount)
	update_ui()


func die(killer = null):
	if is_dead:
		return
	# Atribusi kill hero-vs-hero (paritas _core.py:2490-2515
	# _process_hero_kill): hanya hero yang mencatat kills (dipakai AIPlayer
	# untuk prioritas upgrade & beli item). Kill oleh tower/minion tidak
	# dihitung — sama seperti pygame.
	if killer != null and is_instance_valid(killer) and killer != self \
			and "hero_type" in killer and "skills" in killer \
			and str(killer.get("team")) != team:
		# Object.get() hanya menerima nama properti (bukan default ala Dictionary).
		# Hero selalu punya `kills`; tambah langsung supaya kill AI terhitung.
		killer.kills = int(killer.get("kills")) + 1
	is_dead = true
	hp = 0.0
	add_to_group("dead")
	# Matikan fisika dulu: mayat tidak boleh menahan langkah unit lain
	set_physics_process(false)
	collision_layer = 0
	collision_mask = 0
	target = null
	velocity = Vector2.ZERO
	_cancel_active_skills()
	if status != null:
		status.clear()
	if items != null:
		items.clear_on_death()
	# Hero mati tidak digambar oleh pygame. Node dipertahankan agar level,
	# item dan kepemilikan tetap utuh; GameManager mengelola timer 10 detik.
	hide()
	GameManager.hero_died.emit(self)


func _cancel_active_skills() -> void:
	if skills != null:
		skills.cancel_active()
	_ring_alpha = 0.0
	if hit_particles != null:
		hit_particles.emitting = false
	if skill_particles != null:
		skill_particles.emitting = false


## _entity.Hero.respawn: instance sama, HP penuh, kembali ke base sendiri.
func respawn() -> void:
	if not is_dead:
		return
	if status != null:
		status.clear()
	_cancel_active_skills()
	_recalc_derived(true)
	is_dead = false
	remove_from_group("dead")
	is_retreating = false
	target = null
	clear_destination()
	velocity = Vector2.ZERO
	combat_timer = 0.0
	global_position = own_base() + (Vector2(60, -30) if team == "blue" else Vector2(-60, 30))
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2
	modulate = Color.WHITE
	show()
	set_physics_process(true)
	update_ui()
	queue_redraw()


func update_ui():
	if hp_bar:
		hp_bar.max_value = max_hp
		hp_bar.value = hp
	if name_label:
		name_label.text = "%s Lv%d" % [name, level]


# ══════════════════════════════════════════════════════════
#  SKILL (dipanggil HUD / tombol Q W E R)
# ══════════════════════════════════════════════════════════

func cast_q(): return _cast_skill("q")
func cast_w(): return _cast_skill("w")
func cast_e(): return _cast_skill("e")
func cast_r(): return _cast_skill("r")


func _cast_skill(key: String) -> bool:
	if is_dead or skills == null:
		return false
	var ok: bool = skills.cast(key)
	if ok:
		play_skill_fx(key)
	else:
		# Cast gagal (cooldown belum siap / tidak ada target / kena stun):
		# umpan balik "tidak bisa" paritas _cast_hero_skill _core.py:8441
		# (ui_error volume_mult 0.3). Suara skill yang berhasil dibunyikan
		# SkillBook._trigger_cooldown.
		AudioManager.play_sfx("ui_error", 0.3)
	return ok


## FX skill: ring memancar + burst CPUParticles2D (warna mengikuti tombol)
func play_skill_fx(key: String) -> void:
	var col := Color(1.0, 0.85, 0.4)
	match key:
		"w": col = Color(0.5, 0.9, 1.0)
		"e": col = Color(0.6, 1.0, 0.6)
		"r": col = Color(1.0, 0.45, 0.8)
	_ring_color = col
	_ring_radius = 12.0
	_ring_alpha = 0.95
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(self, "_ring_radius", skill_range if key == "r" else 90.0, 0.32) \
		.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(self, "_ring_alpha", 0.0, 0.34)
	var particles := skill_particles
	if particles != null:
		# CPUParticles2D: parameter emisi = properti node (tidak ada
		# process_material). Diset ULANG tiap cast, bukan sekali saja,
		# supaya warna partikel ikut warna skill — dulu `if process_material
		# == null` bikin Q/W/E/R semua memakai warna cast pertama.
		particles.direction = Vector2(0, -1)
		particles.spread = 180.0
		particles.initial_velocity_min = 40.0
		particles.initial_velocity_max = 120.0
		particles.gravity = Vector2.ZERO
		particles.scale_amount_min = 1.2
		particles.scale_amount_max = 2.6
		particles.color = col
		particles.amount = 36 if key == "r" else 20
		particles.restart()
		particles.emitting = true
	queue_redraw()


## Dipanggil StatusEffects saat buff habis (Warpath/Focus Fire sudah otomatis
## lewat buff multiplier, jadi tidak ada stat yang perlu dipulihkan manual).
func on_buff_expired(_id: String) -> void:
	queue_redraw()


# ══════════════════════════════════════════════════════════
#  LEVEL & ITEM (dipanggil ShopPanel)
# ══════════════════════════════════════════════════════════

func can_upgrade() -> bool:
	return level < HeroDB.max_hero_level


func upgrade_cost() -> int:
	return HeroDB.upgrade_cost(hero_type, level)


func upgrade() -> bool:
	if not can_upgrade():
		return false
	level += 1
	_recalc_derived()
	print("[Hero] %s naik ke level %d" % [name, level])
	return true


func buy_item(item_id: String) -> bool:
	if items == null or not items.can_equip(item_id):
		return false
	if not items.add_item(item_id):
		return false
	_recalc_derived()
	print("[Hero] %s membeli %s" % [name, ItemDB.item_name(item_id)])
	return true


# ══════════════════════════════════════════════════════════
#  SELEKSI & GAMBAR TAMBAHAN
# ══════════════════════════════════════════════════════════

func set_selected(value: bool) -> void:
	if selected == value:
		return
	selected = value
	player_controlled = value and team == "blue"
	queue_redraw()


func _draw() -> void:
	# ring seleksi di tanah
	if selected:
		draw_arc(Vector2(0, 14), radius * 1.5, 0.0, TAU, 28,
			Color(1, 0.92, 0.5, 0.9), 2.0)
	# ring skill memancar
	if _ring_alpha > 0.01:
		draw_arc(Vector2(0, 6), _ring_radius, 0.0, TAU, 40,
			Color(_ring_color.r, _ring_color.g, _ring_color.b, _ring_alpha), 3.0)
	# indikator buff/debuff aktif (titik kecil di atas kepala)
	if status == null:
		return
	var i := 0
	for id in status.buffs:
		var c := Color(0.55, 1.0, 0.65, 0.9)
		match str(id):
			"wind_wall": c = Color(0.6, 0.9, 1.0, 0.9)
			"bristleback": c = Color(0.8, 1.0, 0.5, 0.9)
			"invis": c = Color(0.7, 0.6, 1.0, 0.9)
			"crit", "damage", "attack_speed": c = Color(1.0, 0.7, 0.35, 0.9)
		draw_circle(Vector2(-14 + float(i) * 7, -46), 2.6, c)
		i += 1
		if i > 4:
			break
	var j := 0
	for icon in status.active_icon_list():
		draw_circle(Vector2(-14 + float(j) * 7, -52), 2.2, Color(1.0, 0.35, 0.35, 0.9))
		j += 1
		if j > 4:
			break
