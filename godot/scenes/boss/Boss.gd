# Boss.gd — Port dari bosses/base_boss.py
# Visual baseline: UnitSilhouette pygame (lebih besar + tanduk). Upgrade
# satu-satu lewat RendererRegistry.BOSS[boss_type].
extends CharacterBody2D

@export var boss_type: String = "abaddon"
@export var team: String = "red"

# Stats (diisi dari BossDB)
var display_name: String = "Boss"
var max_hp: float = 30000.0
var hp: float = 30000.0
var damage: float = 120.0
var move_speed: float = 60.0
var attack_range: float = 50.0  # = range pygame (px, tanpa kompensasi)
var attack_cooldown: float = 0.7
var dmg_school: String = "physical"

var target: Node2D = null
var attack_timer: float = 0.0
var is_dead: bool = false
## Padanan alive/defeated/_killed_by pygame untuk klaster reward.
var defeated: bool = false
var killed_by = null
var reward_processed: bool = false
var anim_phase: float = 0.0
var facing: int = -1  # paritas Boss.__init__ pygame (base_boss.py:419)
# Kunci arah hadap selama ayunan serangan dasar (base_boss.py:594-598,
# 746-752): _attack_facing 0 = sentinel None pygame.
var _attack_lock_timer := 0.0 # detik (frame pygame ÷ 60)
var _attack_facing := 0
var radius: float = 22.0
var role: String = ""
var fill_color: Color = Color("#8c64dc")
var fill_dark: Color = Color("#4a3278")
var boss_class: String = "mini"
## Fase 5d: warna entrance + gold reward dibaca BossDeathFX / BossIntroBanner
## (paritas boss.entrance_color & boss.gold_reward bosses/base_boss.py:394)
var entrance_color: Color = Color("#8c64dc")
var gold_reward: int = 0

const UnitSilhouetteScript = preload("res://scripts/render/UnitSilhouette.gd")
const HurtFlashScript = preload("res://scripts/render/HurtFlash.gd")
const RendererRegistry = preload("res://scripts/render/RendererRegistry.gd")
const StatusEffectsScript = preload("res://scripts/systems/StatusEffects.gd")
const TowerBulletScript = preload("res://scenes/tower/TowerBullet.gd")
## Kit smart-AI Q/W/E/R 79 boss — transpile 1:1 dari bosses/base_boss.py
## (lihat header BossKit.gd; state kit hidup di `kit`).
const BossKit = preload("res://scenes/boss/BossKit.gd")
var silhouette = null
var custom_visual = null
## Flash putih hurt_flash_timer pygame (bosses/base_boss.py:6039, dibaca
## _draw_generic_body :6307) — lihat scripts/render/HurtFlash.gd
var hurt_flash = null
## Fase denyut aura true boss (paritas self.pulse base_boss.py:482/580)
var _pulse: float = 0.0
## StatusEffects: boss kena slow/burn/stun menara (paritas TowerDebuffMixin di
## bosses/base_boss.py). Stun boss dipotong 55% supaya tidak di-stunlock.
var status = null
var armor: float = 0.0
var magic_resist: float = 0.0
var combat_timer: float = 0.0
var combat_reset: float = 5.0

# ══════════════════════════════════════════════════════════
#  INTI BOSS — paritas Boss.__init__ bosses/base_boss.py:375-475
#  (Fase 6). Semua field ini dibaca dari BossDB/bosses.json yang
#  diekspor converter dari bosses/boss_data.py + hero_archetypes.
# ══════════════════════════════════════════════════════════
## Inherent damage reduction (True Boss 30%, Mini Boss 20%) — base_boss.py:443
var damage_reduction: float = 0.20
## Tenacity: slow magnitude & duration dikurangi 50% (base_boss.py:444)
var tenacity: float = 0.50
## Anti-burst: cap damage per hit (True 8% max HP, Mini 12%) — :445
var max_damage_per_hit: float = 0.0
## Ability generik (fallback boss tanpa smart-AI) — base_boss.py:388-390
var ability_cooldown_max: int = 0
var ability_damage: int = 0
var ability_range: float = 0.0
var ability_timer: float = 0.0
var ability_active: bool = false
var ability_active_timer: float = 0.0
## Ability kedua true boss (heal saat HP < 30%) — base_boss.py:391-393
var ability2_cooldown_max: int = 0
var ability2_heal_pct: float = 0.0
var ability2_timer: float = 0.0
## Enrage / Frenzy — base_boss.py:467-469
var is_enraged: bool = false
var enrage_triggered: bool = false
var enrage_pulse: float = 0.0
## Entrance freeze (True 180 frame = 3 s, Mini 120 frame = 2 s) — :478
var entrance_timer: float = 0.0
## Cleave splash serangan dasar — base_boss.py:471-472
var cleave_radius: float = 80.0
var cleave_ratio: float = 0.40
## Jarak kiting ranged (histeresis) — dipakai kalau boss masuk daftar
## RANGED_KITE (base_boss.py update :778-797; stat di _get_boss_stats :5921)
var min_distance: float = 200.0
var prefer_distance: float = 280.0
var kite_mode: String = "hold"
## Penghitung frame animasi (enrage mempercepat recovery cooldown 1.5x —
## base_boss.py:652-657: timer/ability_timer turun ekstra tiap 2 frame)
var _anim_frame: int = 0
var _enrage_extra_timer: float = 0.0
## True saat boss_type punya smart-AI spesifik di Pygame
## (bosses/base_boss.py update: rantai elif per boss_type). Boss yang TIDAK
## punya smart-AI memakai ability generik _use_ability (:1071-1106).
var has_smart_ai: bool = false
## Defense boost (hero Drakar W): menaikkan damage_reduction ke 45% selama
## aktif (base_boss.py take_damage :6026-6028).
var defense_boost: bool = false
## Timer frame defense boost (Drakar W, 180 frame) — di-tick kit smart-AI
## (paritas self.defense_timer base_boss.py:2838-2867).
var defense_timer: float = 0.0
## Damage dasar sebelum buff kit (arcane/rum/dragon blood mengalikan ini).
## Paritas self.base_damage base_boss.py:389 (diperbarui apply_scaling :522;
## enrage TIDAK mengubahnya).
var base_damage: float = 0.0
## Pengali damage skill kesulitan Hard (paritas self.dmg_scaling_mult
## base_boss.py:477/516 — dipakai _get_boss_stats untuk SEMUA key *damage*).
var dmg_scaling_mult: float = 1.0
## State kit smart-AI (timer Q/W/E/R frame, buff, target bertanda, dsb.)
## — diisi salinan BossKit.DEFAULT_KIT di _ready; struktur kuncinya
## dibangkitkan tools/gen_boss_smart_ai.py dari AST base_boss.py.
var kit: Dictionary = {}


@onready var visual: Node2D = $Visual
@onready var sprite: AnimatedSprite2D = $Visual/AnimatedSprite2D
@onready var shadow: Polygon2D = $Shadow
@onready var aura: CPUParticles2D = $FX/Aura # CPU: aman di Android/GLES
@onready var hp_bar: ProgressBar = $UI/HPBar
@onready var name_label: Label = $UI/NameLabel

const FPS := 60.0
const AGGRO_MARGIN := 100.0
## Boss ranged yang kiting dengan histeresis (base_boss.py:778-781)
const RANGED_KITE: Array = ["ancient_apparition", "morgath", "razak", "varkul",
	"xerathis", "nyzrak", "syrentha", "thalgryn", "nyxarath", "malzareth",
	"akashari", "vorenmarr"]

func _ready():
	var s: Dictionary = BossDB.get_boss(boss_type)
	if not s.is_empty():
		display_name = s.get("name", boss_type)
		max_hp = float(s.get("hp", 30000))
		hp = max_hp
		damage = float(s.get("damage", 120))
		move_speed = float(s.get("speed", 0.85)) * 60.0
		attack_range = float(s.get("range", 50))
		attack_cooldown = float(s.get("attack_cooldown", 43)) / 60.0
		dmg_school = "physical" # serangan dasar boss SELALU fisik (base_boss.py:707)
		armor = float(s.get("armor", 0))
		magic_resist = float(s.get("magic_resist", 0.0))
	# Paritas Boss.__init__ base_boss.py:389: base_damage = damage mentah
	# (sebelum enrage/buff kit; hanya apply_scaling yang memperbaruinya).
	base_damage = damage
	# State kit smart-AI fresh per instans (timers 0, buff mati).
	kit = BossKit.DEFAULT_KIT.duplicate(true)
	status = StatusEffectsScript.new(self)
	add_to_group("bosses")
	role = str(s.get("title", s.get("role", "")))
	boss_class = str(s.get("boss_class", "mini"))
	fill_color = _parse_color(s.get("color", "#8c64dc"), Color("#8c64dc"))
	fill_dark = fill_color.darkened(0.4)
	entrance_color = _parse_color(s.get("entrance_color", ""), fill_color)
	gold_reward = int(s.get("gold_reward", 0))
	radius = float(s.get("radius", 42.0 if boss_class == "true" else 30.0))
	# ── INTI BOSS (paritas Boss.__init__ base_boss.py:375-475) ──
	damage_reduction = 0.30 if boss_class == "true" else 0.20
	max_damage_per_hit = max_hp * (0.08 if boss_class == "true" else 0.12)
	ability_cooldown_max = int(s.get("ability_cooldown", 0))
	ability_damage = int(s.get("ability_damage", 0))
	ability_range = float(s.get("ability_range", 0))
	ability2_cooldown_max = int(s.get("ability2_cooldown", 0))
	ability2_heal_pct = float(s.get("ability2_heal_pct", 0))
	min_distance = float(s.get("min_distance", 200.0))
	prefer_distance = float(s.get("prefer_distance", 280.0))
	# Boss yang punya rantai smart-AI spesifik di Boss.update pygame memakai
	# per-skill AI Q/W/E/R (port-nya masih terbuka — lihat "Smart-AI boss
	# musuh" di docs/GODOT_PARITY.md); yang TIDAK punya memakai ability
	# generik _use_ability. Bendera dibaca dari bosses.json (diekspor
	# converter dari AST Boss.update — jangan disalin manual ke daftar
	# konstan, supaya daftar smart-AI tidak pernah tidak sinkron).
	has_smart_ai = bool(s.get("uses_smart_ai", false))
	# Entrance freeze: mini 120 frame (2 s), true 180 frame (3 s) — :478.
	# Satu-satunya efek yang TIDAK ikut membeku adalah entrance (banner 100
	# frame digambar di atasnya; Pygame menjalankan boss.update selama banner,
	# dan entrance_timer membuat boss diam sampai timer habis).
	entrance_timer = (180.0 if boss_class == "true" else 120.0) / FPS
	if shadow != null:
		shadow.visible = false
	setup_visual(s)
	# Dibuat SETELAH setup_visual: HurtFlash memilih target tint dari
	# silhouette / custom_visual yang baru saja dipasang.
	hurt_flash = HurtFlashScript.new(self, sprite)
	update_ui()
	collision_layer = 2 if team == "blue" else 4
	collision_mask = 4 if team == "blue" else 2

func setup_visual(_s: Dictionary) -> void:
	if sprite:
		sprite.visible = false
	if aura != null:
		aura.emitting = false # partikel = upgrade, bukan baseline pygame
	visual.scale = Vector2.ONE # tscn lama 1.4x untuk kotak placeholder
	z_as_relative = false
	var packed: PackedScene = RendererRegistry.boss_scene(boss_type)
	if packed != null:
		custom_visual = packed.instantiate()
		custom_visual.name = "CustomVisual"
		visual.add_child(custom_visual)
		if custom_visual.has_method("configure_baked"):
			# Strip bake Fase 5 (skala native 1.0, paritas jalur boss
			# heroes/__init__.py:2873-2878) — boss tanpa offset ekstra.
			custom_visual.configure_baked(boss_type, "boss", team)
		return
	silhouette = UnitSilhouetteScript.new()
	silhouette.name = "Silhouette"
	visual.add_child(silhouette)
	var ranged := attack_range >= 100.0 # AMBANG_RANGED combat_audio.py
	silhouette.configure(
		UnitSilhouetteScript.Kind.BOSS, boss_type, team, fill_color, fill_dark,
		radius, role, dmg_school, ranged, boss_class)

func _physics_process(delta):
	if is_dead:
		return
	if boss_class == "true":
		# pygame: self.pulse += 0.1 tiap frame (base_boss.py:580) -> 6 rad/detik.
		_pulse += delta * PULSE_SPEED
		queue_redraw() # aura true boss menyala terus (lihat _draw)
	if hurt_flash != null:
		hurt_flash.tick(self, delta)
	if status != null:
		status.tick(delta)
	combat_timer = maxf(0.0, combat_timer - delta)
	_anim_frame += 1
	anim_phase += delta * 5.0
	# Kunci arah hadap selama ayunan (base_boss.py:594-598) — di-tick DI ATAS
	# cek stun/entrance supaya kunci tetap melepas walau boss dibekukan.
	if _attack_lock_timer > 0.0:
		_attack_lock_timer = maxf(0.0, _attack_lock_timer - delta)
		if _attack_lock_timer <= 0.0:
			_attack_facing = 0

	# ── STUN: boss membeku total (base_boss.py:604-609). Status sudah di-tick
	# di atas, jadi stun_timer mengecil; entrance/timer/gerak tidak jalan.
	if status != null and status.is_stunned():
		_drive_visual(false)
		return

	# ── ENTRANCE FREEZE (base_boss.py:612-614): diam sampai timer habis.
	if entrance_timer > 0.0:
		entrance_timer -= delta
		_drive_visual(false)
		return

	# ── ENRAGE / FRENZY (base_boss.py:617-650) ──
	_tick_enrage(delta)

	# ── TICK TIMER (base_boss.py:663-668) + extra recovery 1.5x saat enraged
	#    (base_boss.py:651-657: attack_timer & ability_timer turun ekstra tiap
	#    2 frame — ability2/heal dan aura ability TIDAK ikut dipercepat)
	_tick_shared_timers(delta)
	if is_enraged and _anim_frame % 2 == 0:
		attack_timer = maxf(0.0, attack_timer - 1.0 / FPS)
		if ability_timer > 0.0:
			ability_timer = maxf(0.0, ability_timer - 1.0 / FPS)

	# ── TRUE BOSS: ability kedua (heal) saat HP < 30% (base_boss.py:670-673)
	if boss_class == "true" and ability2_cooldown_max > 0 and ability2_timer <= 0.0 \
			and hp < max_hp * 0.30:
		_use_heal_ability()

	# ── Cari target terdekat dalam aggro (base_boss.py:676-697:
	#    best_dist = range + 100; jarak aggro mengikuti jangkauan boss)
	if target == null or not is_instance_valid(target) or bool(target.get("is_dead")):
		target = CombatSystem.nearest_enemy(self, _aggro_radius())
	if target == null:
		# Tidak ada musuh dalam aggro: dorong ke base lawan (nexus bisa dihancurkan)
		var dest := enemy_base()
		if global_position.distance_to(dest) > 40.0:
			var dir := (dest - global_position).normalized()
			velocity = dir * _eff_speed()
			_face(dir.x, dir.y)
			move_and_slide()
			z_index = int(global_position.y)
			_drive_visual(true)
		else:
			velocity = Vector2.ZERO
			z_index = int(global_position.y)
			_drive_visual(false)
		return
	var dist := global_position.distance_to(target.global_position)
	var prev := global_position
	var is_moving := false
	if dist <= attack_range:
		velocity = Vector2.ZERO
		# Hadap sasaran SEBELUM memukul (base_boss.py:733-738). pygame
		# memanggil _face() HANYA di cabang dalam-jangkauan: kiter yang
		# "hold" atau boss yang diam di luar jangkauan TIDAK berbalik —
		# jejak bface oracle smart-AI bergantung pada detail ini.
		_face(target.global_position.x - global_position.x,
			target.global_position.y - global_position.y)
		try_attack()
		_after_attack(dist)
	else:
		_move_toward_target(dist)
		# Pose WALK/IDLE dari perpindahan NYATA (base_boss.py:584-588):
		# kiter ranged yang "hold" diam -> idle, bukan animasi jalan.
		is_moving = global_position.distance_to(prev) > 0.05
	z_index = int(global_position.y)
	_drive_visual(is_moving)


## Jarak aggro boss = jangkauan serang + 100 (base_boss.py:676).
func _aggro_radius() -> float:
	return attack_range + AGGRO_MARGIN


## Timers bersama: attack_timer (serangan dasar), ability_timer (ability
## generik), ability2_timer (heal true boss), ability_active_timer (aura).
func _tick_shared_timers(delta: float) -> void:
	attack_timer = maxf(0.0, attack_timer - delta)
	if ability_timer > 0.0:
		ability_timer = maxf(0.0, ability_timer - delta)
	if ability2_timer > 0.0:
		ability2_timer = maxf(0.0, ability2_timer - delta)
	if ability_active_timer > 0.0:
		ability_active_timer = maxf(0.0, ability_active_timer - delta)
		if ability_active_timer <= 0.0:
			ability_active = false


## ENRAGE / FRENZY — base_boss.py:617-650. True boss 50% HP (speed ×1.25,
## damage ×1.25, cooldown ×0.75 min 18 frame); mini 40% (×1.15 / ×1.20 /
## ×0.80 min 20 frame). Callout ENRAGED!/FRENZY! + shake.
func _tick_enrage(delta: float) -> void:
	if not enrage_triggered and not is_dead:
		if boss_class == "true" and hp <= max_hp * 0.50:
			enrage_triggered = true
			is_enraged = true
			move_speed = move_speed * 1.25
			damage = float(int(damage * 1.25))
			attack_cooldown = _scale_attack_cd(0.75, 18)
			_shake(25.0)
			_callout("ENRAGED!")
			update_ui()
		elif boss_class == "mini" and hp <= max_hp * 0.40:
			enrage_triggered = true
			is_enraged = true
			move_speed = move_speed * 1.15
			damage = float(int(damage * 1.20))
			attack_cooldown = _scale_attack_cd(0.80, 20)
			_shake(15.0)
			_callout("FRENZY!")
			update_ui()
	if is_enraged:
		# +0.08/frame (base_boss.py:649) -> 4,8 rad/s
		enrage_pulse += 0.08 * FPS * delta
		queue_redraw()


## attack_cooldown (detik) × `mult`, minimal `min_frames` frame (pygame
## memakai frame: max(18, int(cd*0.75)) base_boss.py:621/631).
func _scale_attack_cd(mult: float, min_frames: int) -> float:
	var frames := int(attack_cooldown * FPS)
	frames = maxi(min_frames, int(frames * mult))
	return frames / FPS


## True boss heal ability2 (base_boss.py:5956-5975): cooldown ability2, heal
## max_hp × ability2_heal_pct, callout "+N".
func _use_heal_ability() -> void:
	ability2_timer = float(ability2_cooldown_max) / FPS
	var heal_amount := int(max_hp * ability2_heal_pct)
	hp = minf(max_hp, hp + heal_amount)
	_callout("+%d" % heal_amount, false)
	_shake(8.0)
	update_ui()


## Callout damage number di atas boss (ENRAGED! / FRENZY! / +heal).
func _callout(text: String, critical: bool = true) -> void:
	var num = preload("res://scenes/fx/DamageNumber.tscn").instantiate()
	num.setup(text, critical)
	num.global_position = global_position + Vector2(0.0, -radius - 30.0)
	var host := get_tree().current_scene
	if host != null and is_instance_valid(host):
		host.add_child(num)


func _shake(amount: float) -> void:
	# Toggle SETTINGS "Screen Shake" (paritas GameSettings.screen_shake_
	# enabled pygame) — dimatikan = semua guncangan kamera di-skip.
	if not GameManager.screen_shake_enabled:
		return
	var tree := Engine.get_main_loop()
	if tree is SceneTree:
		(tree as SceneTree).call_group("camera", "add_trauma", amount / 60.0)


## Gerak kejar target (base_boss.py:746-756): clamp langkah ke jarak tersisa
## supaya tidak osilasi 1 px; face target. Boss ranged memakai band histeresis
## (base_boss.py:778-822) supaya tidak gemetar di batas min/prefer distance.
func _move_toward_target(dist: float) -> void:
	# CATATAN SATUAN: pygame `step = min(sp, d)` membandingkan kecepatan
	# px/frame dengan jarak px. Di sini sp adalah px/DETIK (move_and_slide
	# mengalikan delta 1/60), jadi jarak px harus dikalikan FPS dulu —
	# tanpa ini clamp "menang" 60x terlalu cepat: begitu d < sp, displacement
	# perdetik jadi d/60 px (meluruh geometris) dan boss tidak pernah
	# menyusul target (ketidaksesuaian jejak BossSmartAIParityTest
	# ignis_drachorn: 605.577 vs 605.625).
	var dx := target.global_position.x - global_position.x
	var dy := target.global_position.y - global_position.y
	var d := maxf(1e-6, dist)
	var sp := _eff_speed()
	if sp <= 0.0:
		velocity = Vector2.ZERO
		return
	if is_ranged_kiter():
		if d < min_distance:
			kite_mode = "back"
		elif d > prefer_distance:
			kite_mode = "in"
		elif kite_mode == "back" and d < min_distance + 12.0:
			pass # terus mundur sampai aman
		elif kite_mode == "in" and d > prefer_distance - 12.0:
			pass # terus maju sampai masuk
		else:
			kite_mode = "hold"
		if kite_mode == "back":
			var step := minf(sp, maxf(0.0, (min_distance + 12.0) - d) * FPS)
			if step > 0.0:
				velocity = Vector2(-dx / d, -dy / d) * step
				_face(-dx, -dy)
				move_and_slide()
				return
			velocity = Vector2.ZERO
			return
		elif kite_mode == "in":
			var step := minf(sp, maxf(0.0, d - (prefer_distance - 12.0)) * FPS)
			if step > 0.0:
				velocity = Vector2(dx / d, dy / d) * step
				_face(dx, dy)
				move_and_slide()
				return
			velocity = Vector2.ZERO
			return
		velocity = Vector2.ZERO # hold: diam di jarak tembak ideal
		return
	var step := minf(sp, d * FPS)
	if step > 0.0:
		velocity = Vector2(dx / d, dy / d) * step
		_face(dx, dy)
		move_and_slide()
	else:
		velocity = Vector2.ZERO


## Daftar boss ranged kiting — paritas set literal update() base_boss.py:778.
func is_ranged_kiter() -> bool:
	return boss_type in RANGED_KITE


func _face(dx: float, dy: float) -> void:
	# Selama kunci ayunan aktif, arah TIDAK diubah (pose swing tidak boleh
	# terbalik di tengah animasi) — paritas _face base_boss.py:1394-1408.
	if _attack_lock_timer > 0.0:
		if _attack_facing != 0:
			facing = _attack_facing
			visual.scale.x = facing
		return
	if absf(dx) < 0.35 * maxf(1e-6, absf(dy)):
		return
	facing = 1 if dx > 0 else -1
	visual.scale.x = facing


func _eff_speed() -> float:
	return move_speed * (status.move_speed_mult() if status != null else 1.0)


func _eff_attack_cd() -> float:
	return status.attack_cd(attack_cooldown) if status != null else attack_cooldown


func enemy_base() -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_enemy_base"):
		return am.get_enemy_base(team)
	return Vector2(1180, 100) if team == "blue" else Vector2(100, 620)

func _drive_visual(is_moving: bool) -> void:
	var ap := 0.0
	if attack_timer > 0.0:
		ap = 1.0 - attack_timer / maxf(0.001, attack_cooldown)
	var act := "idle"
	if attack_timer > 0.0:
		act = "attack"
	elif is_moving:
		act = "walk"
	if silhouette != null and is_instance_valid(silhouette) and silhouette.has_method("drive"):
		silhouette.drive(anim_phase, act, ap, facing)
	elif custom_visual != null and is_instance_valid(custom_visual) and custom_visual.has_method("drive"):
		custom_visual.drive(anim_phase, act, ap, facing, is_moving, "", 0.016)


# ══════════════════════════════════════════════════════════
#  AURA TRUE BOSS (_draw_true_boss_aura bosses/base_boss.py:6351-6375)
# ══════════════════════════════════════════════════════════
# pygame menggambarnya SETIAP frame selama true boss hidup — bukan efek skill,
# melainkan penanda kelas. Mini boss TIDAK punya ini. Resep pygame:
#   pulse  = sin(self.pulse) * 0.3 + 0.7      (self.pulse += 0.1/frame :580)
#   aura_r = radius + 15
#   for r_off in range(aura_r, aura_r - 15, -2):        -> 8 lingkaran
#       alpha = (aura_r - r_off) * 5 * pulse            -> 0,10,20..70 x pulse
#
# JEBAKAN YANG DIVERIFIKASI ULANG: `pygame.draw.circle` TIDAK melakukan alpha
# blending — ia MENIMPA piksel (termasuk kanal alpha) di surface SRCALPHA.
# Jadi 8 lingkaran itu bukan tumpukan yang makin pekat, melainkan gradien
# BERPITA: tiap piksel memakai alpha lingkaran TERKECIL yang menutupinya, dan
# bagian dalam (d <= aura_r - 14) rata di alpha 70 * pulse.
# `draw_circle()` Godot sebaliknya MEM-BLEND; menyalinnya mentah-mentah
# membuat pusat aura ~3x lebih pekat (144/255 vs 49/255 pada pulse 0,7 —
# diukur di tools/test_boss_true_aura_parity.py). Karena itu di sini: satu
# cakram inti + 7 cincin `draw_arc` selebar AURA_STEP yang TIDAK saling
# menimpa, sehingga profil alpha-nya sama dengan pygame.
#
# Aura ability (`ability_active`) dan aura enrage (`is_enraged`) pygame belum
# diport karena mekanik enrage/ability boss memang belum ada di Godot; begitu
# diport, tempatnya di sini juga.
#
# Digambar di node Boss (bukan child) supaya otomatis BERADA DI BAWAH
# Visual/Silhouette: CanvasItem menggambar dirinya dulu, anaknya belakangan.
## rad/detik = 0.1 per frame pygame x 60 fps
const PULSE_SPEED := 6.0
## jumlah lingkaran pygame: range(aura_r, aura_r - 15, -2) -> 8
const AURA_RINGS := 8
const AURA_STEP := 2.0
const AURA_MARGIN := 15.0
## kenaikan alpha per langkah (0..70) sebelum dikali pulse, /255 -> 0..1
const AURA_ALPHA_STEP := 5.0


func _draw() -> void:
	if is_dead:
		return
	var center := Vector2(0.0, -radius * 0.7)
	if boss_class == "true":
		var pulse := sin(_pulse) * 0.3 + 0.7
		var aura_r := radius + AURA_MARGIN
		# pygame memusatkan aura di (x, y) = TENGAH badan; origin unit Godot ada di
		# telapak kaki (UnitSilhouette._draw), jadi digeser naik ke torso.
		# 1) cakram inti: alpha maksimum, rata sampai aura_r - 14
		var inner_r := aura_r - float(AURA_RINGS - 1) * AURA_STEP
		var inner_a: float = float(AURA_RINGS - 1) * AURA_STEP * AURA_ALPHA_STEP * pulse / 255.0
		draw_circle(center, inner_r, Color(fill_color.r, fill_color.g, fill_color.b, inner_a))
		# 2) cincin luar, makin ke luar makin transparan (i = 0 alpha 0 -> dilewati)
		for i in range(1, AURA_RINGS - 1):
			var r_off := aura_r - float(i) * AURA_STEP
			var a := (aura_r - r_off) * AURA_ALPHA_STEP * pulse / 255.0
			if a <= 0.0:
				continue
			# draw_arc menaruh garis DI TENGAH radius -> mid = r_off - step/2
			# menutup pita (r_off - step, r_off], persis satu langkah pygame.
			draw_arc(center, r_off - AURA_STEP * 0.5, 0.0, TAU, 32,
				Color(fill_color.r, fill_color.g, fill_color.b, a), AURA_STEP)
	# ── AURA ENRAGE / FRENZY (base_boss.py:6277-6300) ──
	# Pygame menggambar cincin garis (bukan cakram) radius = radius + 14*pulse,
	# warna merah untuk true boss / oranye untuk mini. Pendekatan draw_arc
	# lebar 2 px menyamai stroke pygame; profil alpha/pixel belum diverifikasi
	# screenshot — dicatat di docs/GODOT_PARITY_CHECKLIST.md (visual stage).
	if is_enraged:
		var epulse := sin(enrage_pulse) * 0.3 + 0.7
		var era := radius + 14.0 * epulse
		var ecol := Color(1.0, 0.196, 0.157) if boss_class == "true" else Color(1.0, 0.55, 0.118)
		draw_arc(center, era, 0.0, TAU, 40, ecol, 2.0)
		draw_arc(center, era - 3.0, 0.0, TAU, 40,
			Color(ecol.r, ecol.g, ecol.b, 0.6), 2.0)


static func _parse_color(v, fallback: Color) -> Color:
	if v is Color:
		return v
	var s := str(v).strip_edges()
	if s.is_empty():
		return fallback
	if not s.begins_with("#"):
		s = "#" + s
	return Color(s)


## Dicari lewat CombatSystem supaya nexus/menara ikut jadi target dan unit
## yang sedang Shadow Realm (invis) dilewati.
func find_nearest_enemy() -> Node2D:
	return CombatSystem.nearest_enemy(self, _aggro_radius())

## Serangan dasar boss (base_boss.py:707-755). Sekolah damage SELALU fisik.
## Cleave splash dieksekusi di sini (hanya saat serangan benar-benar dilepas,
## base_boss.py:719-726) — bukan tiap frame.
func try_attack() -> bool:
	if attack_timer > 0.0 or target == null or is_dead:
		return false
	if status != null and status.is_stunned():
		return false
	attack_timer = _eff_attack_cd()
	# Kunci arah hadap seumur wind-up s/d impact (base_boss.py:746-752:
	# min 6 / max 15 frame = attack_cooldown // 3, digenggam saat swing).
	_attack_facing = facing
	_attack_lock_timer = clampf(attack_cooldown / 3.0, 6.0 / FPS, 15.0 / FPS)
	# Boss memakai DUA suara global yang sama seperti hero (paritas
	# BaseBoss._suara_serangan + update bosses/base_boss.py:552-566/746-752):
	# melee vs ranged dipilih dari jangkauan, ambang 100 (AMBANG_RANGED).
	# is_melee=null -> AudioManager memakai ambang jarak, bukan flag.
	AudioManager.play_combat(AudioManager.basic_attack_sfx(null, attack_range))
	var dmg := CombatSystem.calc_damage(self, target, damage, dmg_school)
	if attack_range >= 100.0: # AMBANG_RANGED (base_boss._suara_serangan)
		# Boss ranged: proyektil (visual Godot; damage diserap target saat
		# impact). Cleave tetap dihitung dari posisi boss saat ayunan — sama
		# seperti pygame yang menghitung splash di momen serangan.
		var b = TowerBulletScript.new()
		# pygame base_boss.py:707: basic boss SELALU instan 'normal' +
		# school 'physical' — proyektil di sini visual saja, damage-nya
		# mendarat dengan damage_type 'normal' (tidak dipantulkan Wind
		# Wall, sama seperti pygame).
		b.setup(target, dmg, team, "normal", {}, 380.0,
			fill_color.lightened(0.3), self, dmg_school, "normal")
		b.global_position = global_position + Vector2(0, -20)
		GameManager.attach_fx(b)
	else:
		CombatSystem.apply_damage(target, dmg, team, "normal", self, dmg_school)
	_do_cleave()
	GameManager.request_hit_stop(0.045) # boss feel: sedikit lebih lama dari hero
	return true


## Setelah ayunan (dipanggil tiap frame saat target dalam jangkauan, sama
## seperti pygame): boss ber-smart-AI menjalankan kit Q/W/E/R; boss tanpa
## smart-AI memakai ability generik (base_boss.py:757-920 → _use_ability).
func _after_attack(dist: float) -> void:
	if has_smart_ai:
		# Daftar musuh TIDAK difilter targetabilitas (paritas update()
		# pygame: all_units + towers + bases hanya disaring tim & hidup —
		# hero Shadow Realm tetap kena skill boss).
		BossKit.dispatch(self, boss_type, kit_enemies(), dist)
	elif ability_timer <= 0.0 and ability_range > 0.0:
		_use_ability()


# ══════════════════════════════════════════════════════════
#  JEMBATAN KIT SMART-AI (dipanggil BossKit.gd — lihat header file itu).
#  Semua konversi frame pygame ↔ detik Godot terjadi DI SINI, satu tempat.
# ══════════════════════════════════════════════════════════

## Musuh dari sudut pandang boss — persis blok `enemies` Boss.update
## pygame (base_boss.py:676-687): semua unit + tower + base tim lawan yang
## hidup, TANPA filter targetabilitas dan tanpa pemotongan jarak.
func kit_enemies() -> Array:
	var out: Array = []
	for group in ["heroes", "bosses", "minions", "towers", "nexus"]:
		for n in get_tree().get_nodes_in_group(group):
			if not is_instance_valid(n) or not (n is Node2D):
				continue
			if str(n.get("team")) == team:
				continue
			if bool(n.get("is_dead")):
				continue
			out.append(n)
	return out


## Port _get_boss_stats base_boss.py:5921-5946: stat mentah boss_data,
## lalu SEMUA key numerik ber-*damage* dikalikan (skill_down Mage Tower,
## dmg_scaling_mult Hard, enrage ×1.25) dengan int(round()) Python
## (round-half-even — round() Godot memotong ke atas, beda!).
func kit_get_stats() -> Dictionary:
	var stats := kit_stats_full()
	var mult := 1.0
	if status != null and status.skill_down_timer > 0.0:
		mult *= maxf(0.0, 1.0 - status.skill_down_amount)
	if dmg_scaling_mult != 1.0: # pygame: != eksak, bukan approx
		mult *= dmg_scaling_mult
	if is_enraged:
		mult *= 1.25
	if mult != 1.0 and not stats.is_empty():
		var scaled := stats.duplicate()
		for k in stats.keys():
			var v = stats[k]
			var t := typeof(v)
			if (t == TYPE_INT or t == TYPE_FLOAT) and String(k).find("damage") != -1:
				scaled[k] = _py_round(float(v) * mult)
		return scaled
	return stats


## round() Python: half-to-EVEN (banker's). round() GDScript: half-away.
## _get_boss_stats pygame memakai int(round(v*mult)) — hasilnya harus sama.
static func _py_round(v: float) -> int:
	var f := floorf(v)
	var diff := v - f
	if diff > 0.5:
		return int(f) + 1
	if diff < 0.5:
		return int(f)
	return int(f) if int(f) % 2 == 0 else int(f) + 1


## Stat mentah boss_data (paritas _l9_stats base_boss.py:6450-6455 — tanpa
## pengali apa pun). Cache statis: file dibaca sekali per proses.
static var _full_stats_cache: Dictionary = {}
static func _load_full_stats() -> Dictionary:
	if _full_stats_cache.is_empty():
		var f := FileAccess.open("res://data/boss_stats_full.json", FileAccess.READ)
		if f != null:
			var parsed = JSON.parse_string(f.get_as_text())
			if parsed is Dictionary:
				_full_stats_cache = parsed
		if _full_stats_cache.is_empty():
			push_error("[Boss] boss_stats_full.json tidak terbaca — regenerasi "
				+ "tools/convert_to_godot.py")
	return _full_stats_cache


func kit_stats_full() -> Dictionary:
	return _load_full_stats().get(boss_type, {})


## e.take_damage(dmg, self.team) pygame — netral sekolah, tanpa source
## (blind/reflect tidak berlaku; armor/MR target ikut pipeline umum).
func kit_skill_hit(e, amount) -> void:
	if e == null or not is_instance_valid(e):
		return
	CombatSystem.apply_damage(e, float(amount), team, "normal", null, "")


## e.apply_slow(amount, durasi_frame) pygame — hanya unit yang punya
## apply_slow (hero/minion/boss; tower & nexus pygame tidak punya).
func kit_apply_slow(e, amount: float, dur_frames: float) -> void:
	if e == null or not is_instance_valid(e):
		return
	if not kit_has_slow(e):
		return
	e.status.apply_slow(amount, dur_frames / 60.0)


## e.attack_timer = max(e.attack_timer, F_frame) pygame (kunci serangan).
func kit_lock_attack(e, frames: float) -> void:
	if e == null or not is_instance_valid(e):
		return
	if not ("attack_timer" in e):
		return
	e.attack_timer = maxf(float(e.get("attack_timer")), frames / 60.0)


## Baca attack_timer musuh dalam FRAME (penggunaan: max(...) di kit).
func kit_atk_timer(e) -> float:
	if e == null or not is_instance_valid(e) or not ("attack_timer" in e):
		return 0.0
	return float(e.get("attack_timer")) * 60.0


## e.alive pygame.
func kit_unit_alive(e) -> bool:
	if e == null or not is_instance_valid(e):
		return false
	return not bool(e.get("is_dead"))


## hasattr(e, 'apply_slow') pygame — tower/nexus tidak punya status.
func kit_has_slow(e) -> bool:
	if e == null or not is_instance_valid(e):
		return false
	var st = e.get("status")
	return st != null


## hasattr(e, 'speed') pygame — hanya unit bergerak (bukan tower/nexus).
func kit_can_move(e) -> bool:
	if e == null or not is_instance_valid(e):
		return false
	return "move_speed" in e


## Pengganti lapisan FX heroes/<boss>_fx pygame (notify_skill_cast):
## callout nama skill + denyut ring di posisi boss. Lapisan visual
## aproksimasi — koefisien/timing perilaku dijamin BossSmartAIParityTest,
## bukan audit piksel FX (lihat docs/GODOT_PARITY.md).
func kit_fx_cast(skill: String) -> void:
	_callout(str(skill).to_upper() + "!")
	_kit_ring(global_position, radius + 18.0, fill_color.lightened(0.25))


## Pengganti notify_skill_impact(self, x, y, radius, skill) pygame:
## cincin ekspansi senyala di titik impact (radius sama dengan pygame).
func kit_fx_impact(x: float, y: float, r: float, skill: String) -> void:
	_kit_ring(Vector2(x, y), maxf(10.0, r), fill_color.lightened(0.4))
	if skill == "r":
		_kit_ring(Vector2(x, y), maxf(10.0, r) * 0.6, Color(1.0, 0.85, 0.4))


## Cincin ekspansi sederhana (draw_arc + fade, CPU-only, aman Android).
func _kit_ring(center: Vector2, r: float, col: Color) -> void:
	var host := get_tree().current_scene
	if host == null or not is_instance_valid(host):
		return
	var ring = preload("res://scenes/fx/KitShockRing.gd").new()
	ring.setup(center, r, col)
	host.add_child(ring)


## Cleave: 40% damage ke musuh LAIN dalam cleave_radius (80 px) dari posisi
## boss — target utama tidak kena dua kali (base_boss.py:719-726).
func _do_cleave() -> void:
	var cleave_dmg := int(damage * cleave_ratio)
	if cleave_dmg <= 0:
		return
	var center: Vector2 = global_position
	for e in CombatSystem.enemies_of(team):
		if e == target or not is_instance_valid(e):
			continue
		if (e as Node2D).global_position.distance_to(center) <= cleave_radius:
			# Cleave netral sekolah (base_boss.py:722-725: take_damage tanpa
			# source/school) — dulu "physical" membuat cleave boss salah
			# diredam armor hero.
			CombatSystem.apply_damage(e, float(cleave_dmg), team, "normal", null, "")


## Ability generik fallback boss tanpa smart-AI (base_boss.py:1071-1106):
## damage ability_damage ke semua musuh dalam ability_range + kunci serangan
## 60 frame (attack_timer, bukan stun gerak) + aura ability 60 frame.
func _use_ability() -> void:
	if is_dead:
		return
	ability_timer = float(ability_cooldown_max) / FPS
	ability_active = true
	ability_active_timer = 1.0 # 60 frame
	queue_redraw()
	var hits := 0
	for e in CombatSystem.enemies_of(team):
		if not is_instance_valid(e):
			continue
		var dist := (e as Node2D).global_position.distance_to(global_position)
		if dist > ability_range:
			continue
		# Netral sekolah (base_boss.py _use_ability:1082-1091: take_damage
		# tanpa source/school, jadi armor/MR hero tidak meredam ability).
		CombatSystem.apply_damage(e, float(ability_damage), team, "normal", null, "")
		if "attack_timer" in e:
			e.attack_timer = maxf(float(e.get("attack_timer")), 1.0)
		hits += 1
	if hits > 0:
		_shake(15.0 if boss_class == "true" else 12.0)


## Resilience + anti-burst boss — base_boss.py take_damage 6025-6037, dipanggil
## CombatSystem.apply_damage tepat SETELAH mitigasi armor/MR (dan sebelum HP
## berkurang). Defense boost (skill hero Drakar W) menaikkan ke 45%.
func apply_boss_inherent_mitigation(raw: float) -> float:
	if raw <= 0.0 or is_dead:
		return raw
	var dr := damage_reduction
	if defense_boost:
		dr = maxf(dr, 0.45)
	var eff := int(raw * (1.0 - dr))
	eff = mini(eff, int(max_damage_per_hit))
	return float(maxi(1, eff))

func take_damage(amount: float, from_team: String = "", dmg_type: String = "normal",
		source = null, school: String = ""):
	if is_dead:
		return
	var before := hp
	# CombatSystem yang mengurangi HP + memunculkan damage number (urutan mitigasi
	# identik untuk hero/minion/boss/tower/nexus)
	CombatSystem.apply_damage(self, amount, from_team, dmg_type, source, school)
	if hp < before:
		_flash()
	if hp <= 0:
		die(source)
	update_ui()


func heal(amount: float) -> void:
	if is_dead:
		return
	CombatSystem.heal_unit(self, amount)
	update_ui()


## Lihat catatan di Minion._flash(): deteksi utama ada di HurtFlash.tick().
func _flash() -> void:
	if hurt_flash != null:
		hurt_flash.trigger()

func _spawn_damage_number(amount: float) -> void:
	var num = preload("res://scenes/fx/DamageNumber.tscn").instantiate()
	num.setup(str(int(amount)), amount > max_hp * 0.06)
	num.global_position = global_position + Vector2(randf_range(-18, 18), -70)
	var host := get_tree().current_scene
	if host:
		host.add_child(num)
	else:
		add_child(num)

func die(killer = null):
	if is_dead:
		return
	is_dead = true
	defeated = true
	hp = 0.0
	killed_by = killer
	set_physics_process(false)
	collision_layer = 0
	collision_mask = 0
	target = null
	if aura != null:
		aura.emitting = false
	# Seluruh reward/atribusi/tracking di satu pintu, tepat sekali. Hero
	# gratis tetap menunggu kemenangan; unlock_boss tersimpan SEKARANG.
	GameManager.register_boss_death(self)
	# Ledakan kematian boss (paritas BossDeathExplosion.update _render.py:1761-1770):
	# true boss = explosion 1.5 + victory 0.7, mini boss = explosion 1.0.
	# force=true: nama 'explosion' dipakai juga oleh splash cannon (throttle
	# 120 ms), dan kematian boss tidak boleh tertelan dentuman meriam.
	if boss_class == "true":
		AudioManager.play_sfx("explosion", 1.5, true)
		AudioManager.play_sfx("victory", 0.7, true)
	else:
		AudioManager.play_sfx("explosion", 1.0, true)
	# Ledakan kematian besar 25 percikan (paritas `add_death_explosion(...,
	# size='large')` `base_boss.py:6076`, satu blok dengan shake 28/20 yang
	# sudah diport `Boss._shake`).
	GameManager.spark_fx.add_death_explosion(global_position.x,
		global_position.y, team, "large")
	# Cinematic kematian: ledakan + dissolve + pecahan + (true boss) perayaan
	# "BOSS DEFEATED!" — port BossDeathAnimation (_render.py:1622, dipanggil
	# _core.py:2124 saat boss terdeteksi mati). Fase kematian membekukan
	# gameplay persis seperti pygame (_core.py:1995-1997).
	var death_fx = preload("res://scenes/fx/BossDeathFX.gd").new()
	death_fx.setup({
		"boss_class": boss_class,
		"name": display_name,
		"title": role,
		"color": fill_color,
		"color_dark": fill_dark,
		"entrance_color": entrance_color,
		"gold_reward": gold_reward,
		"radius": radius,
	})
	var host := get_tree().current_scene
	if host != null and is_instance_valid(host):
		host.add_child(death_fx)
	else:
		get_parent().add_child(death_fx)
	death_fx.global_position = global_position
	# Death: scale squash + fade (GPU, bukan ellipse manual)
	var tw := create_tween()
	tw.parallel().tween_property(visual, "scale", Vector2(1.9, 0.18), 0.45).set_trans(Tween.TRANS_BACK)
	tw.parallel().tween_property(self, "modulate:a", 0.0, 0.5)
	tw.tween_callback(queue_free)
	print("[Boss] %s mati — tim %s menang wave" % [display_name, "blue" if team == "red" else "red"])


## Port bosses/base_boss.py apply_scaling (513-525): pengali difficulty Hard
## diterapkan ke stat yang SUDAH diisi BossDB (dipanggil Main._boss_tick tepat
## setelah spawn, paritas _core.py:1822 mini boss / 2097 true boss).
## HP dipotong int seperti pygame; speed mengikuti pengali apa adanya.
func apply_scaling(hp_mult: float = 1.0, dmg_mult: float = 1.0, spd_mult: float = 1.0) -> void:
	max_hp = float(int(max_hp * hp_mult))
	hp = max_hp
	damage = float(int(damage * dmg_mult))
	# Paritas apply_scaling base_boss.py:513-526: base_damage ikut nilai baru
	# dan dmg_scaling_mult membuat SEMUA key *damage* stat skill ter-skala
	# lewat _get_boss_stats (sebelumnya skill boss tidak ter-skala di Godot).
	base_damage = damage
	dmg_scaling_mult = dmg_mult
	# Ability generik ikut skala damage (base_boss.py:521 apply_scaling)
	ability_damage = int(ability_damage * dmg_mult)
	move_speed = move_speed * spd_mult
	# Cap anti-burst ikut skala max_hp baru (base_boss.py:524-525)
	max_damage_per_hit = max_hp * (0.08 if boss_class == "true" else 0.12)
	update_ui()

func update_ui():
	if hp_bar:
		hp_bar.max_value = 100.0
		hp_bar.value = clampf(hp / maxf(1.0, max_hp) * 100.0, 0.0, 100.0)
	if name_label:
		var tag := ""
		if is_enraged:
			tag = " [ENRAGED]" if boss_class == "true" else " [FRENZY]"
		name_label.text = "%s%s  %d/%d" % [display_name, tag, int(maxf(0.0, hp)), int(max_hp)]
		# Label memerah saat enrage (base_boss.py:6254 label_color merah)
		name_label.add_theme_color_override("font_color",
			Color(1.0, 0.235, 0.235) if is_enraged else Color(1, 0.86, 0.6))
