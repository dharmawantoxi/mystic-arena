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
const HeroSkillKit = preload("res://scenes/hero/HeroSkillKit.gd")
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
## Nama gameplay (pygame Hero.name), tidak terkena suffix unik Node.name
## ketika dua tim memiliki tipe hero yang sama. Dipakai popup SLAYER.
var display_name: String = "Hero"

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
var skill_name: String = ""

# ══════════════════════════════════════════════════════════
#  STATE HERO-SKILL KIT (paritas field Hero pygame, frame-based)
#
#  skill_timer/w/e/r cooldown, active_skill(+timer), dan dict `kit` adalah
#  milik HERO di pygame juga (hero_skills/_bundle.py menulis h.<field>);
#  HeroSkillKit.gd (generated) mengaksesnya lewat nama yang sama. Satuan
#  SELALU frame, diturunkan dalam urutan Hero.update — lihat
#  _step_skill_frames().
# ══════════════════════════════════════════════════════════
var skill_data: Dictionary = {}      # salinan katalog mentah (h.skill_data)
var kit: Dictionary = {}             # state handler kustom (h.<nama>)
var skill_timer: int = 0             # Q cooldown
var skill_cooldown_max: int = 300
var w_cooldown: int = 0
var w_cooldown_max: int = 240        # _entity.py:3445-3449 (universal)
var e_cooldown: int = 0
var e_cooldown_max: int = 420
var r_cooldown: int = 0
var r_cooldown_max: int = 900
var active_skill = null              # "q".."r" / null — renderer & HUD
var active_skill_timer: int = 0      # frame
var auto_cast_enabled: bool = true   # _entity.py:3440 — pygame SELALU True;
                                     # field dipertahankan untuk parity, hanya
                                     # test harness yang boleh mematikannya
var auto_cast_frame: int = 0         # _entity.py:3803 (check tiap 20f)
var kit_no_projectiles: bool = false # harness replay: visual projectile off

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
## Kunci anti pembayaran ganda (padanan `_rewarded` pygame _core.py:2230):
## hero hanya membayar +150 sekali per kematian; flag DIBUKA LAGI saat
## respawn (paritas _core.py:2263-2265) supaya kematian berikutnya bayar.
var reward_processed: bool = false
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
## Perintah taktis follow & attack (paritas follow_target _entity.py:3405).
## Dipasang TacticalCommands (attack_boss/dealer, gather push) & klik musuh;
## divalidasi tiap frame (mati/kawan -> null) dan dieksekusi SETELAH
## destination, SEBELUM serang-biasa (paritas _entity.py:4074-4090).
var follow_target: Node2D = null
## Kill hero-vs-hero (paritas _core.py:2506-2515 _process_hero_kill) — dipakai
## AIPlayer sebagai prioritas upgrade & beli item (sort by kills pygame).
var kills: int = 0
## _entity.py:3425 — akumulasi damage milik hero (dipakai command taktis
#  AI "ATTACK DAMAGE DEALER" di pygame). Kredit HANYA lewat
#  CombatSystem._credit_hero_damage (`int(dealt)` setelah HP, bukan
#  shield) — kit_hit TIDAK menambah lagi (kalau tidak skill terhitung dua kali).
var damage_dealt: float = 0.0

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
	# State handler (kaizen._q_stack dst) — persis Hero.skills.init_state()
	# pygame yang dipanggil SETELAH handler dibuat (_entity.py:3455).
	HeroSkillKit.init_state(self)
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
	skill_cooldown_max = int(s.get("skill_cooldown", 300))
	# _entity.py:3373: skill_cooldown_max = stats["skill_cooldown"] MENTAH
	# (frame). Katalog heroes.json sudah menyimpan frame.
	skill_data = HeroDB.get_hero(hero_type)
	# ═══ CATCH-UP STAT DASAR (hero_balance.starter_catchup_stats) ═══
	# Di pygame panggilan ini MENIMPA hasil normalisasi melee untuk
	# SEMUA hero (non-starter => x1.0 dari katalog mentah). Lihat
	# HeroDB.starter_catchup_mults untuk audit lengkapnya.
	var base := HeroDB.catchup_base(hero_type, _catchup_unlocks(), level)
	base_hp = float(base.x)
	base_damage = float(base.y)
	skill_name = str(s.get("skill_name", ""))
	dmg_school = str(s.get("dmg_school", "physical"))
	role = str(s.get("role", ""))
	display_name = str(s.get("name", hero_type))
	name = display_name
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
	# Item aktif auto-trigger (paritas inv.update(1, enemies) _entity.py:3801).
	# 17 item "aktif" pygame tidak punya tombol — semuanya terpicu sendiri
	# dari HP/jumlah musuh/target, jadi cukup dipanggil di sini.
	if items != null:
		items.tick(delta)
	# AUTO-CAST dulu, BARU cooldown diturunkan — urutan persis
	# Hero.update pygame (_entity.py:3803-3810): cast di frame F membakar
	# cooldown yang pada frame yang sama masih di-decrement sekali.
	_auto_cast_frames()
	# ══ FRAME SKILL (Q--, attack_timer--, active--, WER--, kit timers) ══
	_step_skill_frames()
	combat_timer = maxf(0.0, combat_timer - delta)
	_hit_fx_cd = maxf(0.0, _hit_fx_cd - delta)
	if hurt_flash != null:
		hurt_flash.tick(self, delta)
	anim_phase += delta * 6.0  # phase untuk Skeleton2D (breath + stride)

	_regen(delta)

	# ─── Validasi follow_target (paritas _entity.py:3973-3977) ───
	# Target taktis yang mati / ternyata kawan langsung dibuang.
	if follow_target != null:
		if not is_instance_valid(follow_target) \
				or bool(follow_target.get("is_dead")) \
				or str(follow_target.get("team")) == team:
			follow_target = null

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
	# ── 3. PLAYER COMMAND: follow & attack target (paritas _entity.py:4074-4090) ──
	# Perintah taktis (attack_boss/dealer, gather push): kunci target, dekati
	# sampai masuk attack range lalu serang. Prioritas di bawah destination
	# (hero attack_boss yang masih punya titik spread menaati titiknya dulu).
	elif follow_target != null:
		target = follow_target
		var fpos := (follow_target as Node2D).global_position
		var fdist := global_position.distance_to(fpos)
		facing = 1 if fpos.x > global_position.x else -1
		visual_root.scale.x = facing # flip sprite / skeleton
		if fdist <= attack_range:
			velocity = Vector2.ZERO
			try_attack()
		else:
			is_moving = _move_to(fpos, eff_speed)
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


## Perintah gerak pemain/taktis (paritas Hero.move_to _entity.py:3571-3575):
## pasang destination, buang follow_target, batalkan retreat.
func move_to(x: float, y: float, auto: bool = false) -> void:
	destination = Vector2(x, y)
	destination_auto = bool(auto)
	follow_target = null
	is_retreating = false


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


## Hero AI maupun pemain: auto-cast SDLAM NYA AKTIF seperti pygame v27
## (_entity.py:3432-3440 — "Semua skill sekarang dicor otomatis").
## Godot lama salah urut (R butuh 3+ musuh, Q didahulukan) sehingga
## ultimate & skill defensive nyaris tidak pernah dipakai AI.
## Auto-cast dalam FRAME seperti pygame (_entity.py:3803-3810 + 4149-4212).
## Timer per-frame, cek tiap 20 step simulasi; gate stun/veil; TIDAK melewatkan
## hero yang dikendalikan pemain (pygame tidak membedakan player_controlled).
func _auto_cast_frames() -> void:
	if auto_cast_enabled == false:
		return
	var inv = items
	var disabled := false
	if status != null and status.has_method("is_stunned") and status.is_stunned():
		disabled = true
	if inv != null and inv.is_veiled():
		disabled = true
	if not disabled:
		auto_cast_frame -= 1
		if auto_cast_frame <= 0:
			auto_cast_frame = 20
			_try_auto_cast()
	# CATATAN: decrement Q TIDAK di sini — ia terjadi SETELAH auto-cast di
	# _step_skill_frames() (satu-satunya Q-- per frame), sama seperti urutan
	# Hero.update pygame (_entity.py:3806-3810).


## Mirror Hero._try_auto_cast: prioritas R -> E(2+ musuh) -> W(hp<40%) -> Q;
## wajib ada musuh hidup dalam skill_range (guard anti-buang); target dipaksa
## ke musuh TERDEKAT dalam range.
func _try_auto_cast() -> void:
	var lists := _kit_lists()
	var enemies: Array = []
	for e in lists[0] + lists[1] + lists[2]:
		if str(e.get("team")) == team or bool(e.get("is_dead")):
			continue
		var d := global_position.distance_to((e as Node2D).global_position)
		if d <= skill_range:
			enemies.append([d, e, enemies.size()])
	if enemies.is_empty():
		return
	enemies.sort_custom(Callable(HeroSkillKit, "__by_pair0"))
	target = enemies[0][1]
	var nearby_count := enemies.size()
	var hp_ratio := hp / maxf(1.0, max_hp)
	if is_skill_ready("r"):
		if try_cast_skill("r"):
			return
	if is_skill_ready("e") and nearby_count >= 2:
		try_cast_skill("e")
		return
	if is_skill_ready("w") and hp_ratio < 0.4:
		try_cast_skill("w")
		return
	if is_skill_ready("q"):
		try_cast_skill("q")


func is_skill_ready(key: String) -> bool:
	match key:
		"q":
			return skill_timer <= 0
		"w":
			return w_cooldown <= 0
		"e":
			return e_cooldown <= 0
		"r":
			return r_cooldown <= 0
	return false


## Hero.cast_skill pygame (_entity.py:3578-3643): delegasi ke handler, lalu
## CDR (Octarine) + spell vamp. INI satu-satunya jalur cast (tombol HUD,
## auto-cast AI, harness replay) supaya efek item ikut persis.
func try_cast_skill(key: String, all_units: Array = [], all_towers: Array = [],
		all_bases: Array = []) -> bool:
	if is_dead:
		return false
	var cd_attr := "skill_timer"
	match key:
		"w":
			cd_attr = "w_cooldown"
		"e":
			cd_attr = "e_cooldown"
		"r":
			cd_attr = "r_cooldown"
	var inv = items
	var cdr := 0.0
	if inv != null:
		cdr = float(inv.get_cooldown_reduction())
	var before := int(get(cd_attr))
	var ok: bool = false
	match key:
		"q":
			ok = HeroSkillKit.cast_q(self, all_units, all_towers, all_bases)
		"w":
			ok = HeroSkillKit.cast_w(self, all_units, all_towers, all_bases)
		"e":
			ok = HeroSkillKit.cast_e(self, all_units, all_towers, all_bases)
		"r":
			ok = HeroSkillKit.cast_r(self, all_units, all_towers, all_bases)
		_:
			return false
	if ok:
		if cdr > 0.0:
			var after := int(get(cd_attr))
			var added := after - before
			if added > 0:
				set(cd_attr, maxi(0, HeroDB._py_round(float(after) - float(added) * cdr)))
		if inv != null:
			var sv := float(inv.get_spell_vamp())
			if sv > 0.0:
				var heal := int(float(kit_skill_damage()) * sv)
				if heal > 0:
					hp = minf(max_hp, hp + float(heal))
	return ok


## Langkah timer skill per-frame — URUTAN PERSIS Hero.update pygame:
## (4) skill_timer, (7) attack_timer, (7b) active_skill_timer, (8) w/e/r,
## (9) skills.update_timers. attack_timer di-tick di sini supaya posisi
## relatifnya sama (proyektil visual tidak memengaruhi kit: damage skill
## instan; lihat docs/GODOT_PARITY.md).
func _step_skill_frames() -> void:
	if skill_timer > 0:
		skill_timer -= 1
	if attack_timer > 0.0:
		attack_timer = maxf(0.0, attack_timer - (1.0 / FPS))
	if active_skill_timer > 0:
		active_skill_timer -= 1
		if active_skill_timer <= 0:
			active_skill = null
	if w_cooldown > 0:
		w_cooldown -= 1
	if e_cooldown > 0:
		e_cooldown -= 1
	if r_cooldown > 0:
		r_cooldown -= 1
	var lists := _kit_lists()
	HeroSkillKit.update_timers(self, lists[0], lists[1], lists[2])


## Semua unit/tower/base lawan untuk handler skill (mirror argumen
## Game.update -> Hero.update di pygame). Grup sama dengan Boss.kit_enemies,
## TANPA potong jarak — penyaringan tim+hidup di kit_enemies().
func _kit_lists() -> Array:
	var units: Array = []
	units.append_array(get_tree().get_nodes_in_group("minions"))
	units.append_array(get_tree().get_nodes_in_group("heroes"))
	units.append_array(get_tree().get_nodes_in_group("bosses"))
	var towers: Array = get_tree().get_nodes_in_group("towers")
	var bases: Array = get_tree().get_nodes_in_group("nexus")
	return [units, towers, bases]


# ══════════════════════════════════════════════════════════
#  JEMBATAN HeroSkillKit (dipanggil HeroSkillKit.gd — konversi frame<->detik
#  HANYA di sini; semua timer kit sendiri tetap FRAME seperti pygame)
# ══════════════════════════════════════════════════════════

## BaseSkill._get_enemies -> hero._get_all_enemies(all_units, towers, bases).
func kit_enemies(all_units, all_towers, all_bases) -> Array:
	var out: Array = []
	for lst in [all_units, all_towers, all_bases]:
		for n in lst:
			if not is_instance_valid(n) or not (n is Node2D):
				continue
			if str(n.get("team")) == team:
				continue
			if bool(n.get("is_dead")):
				continue
			out.append(n)
	return out


## Mirror property skill_damage _entity.py (int(round) BERANTAI: base lalu
## amp item, lalu skill_down tower) — dibaca 280x oleh kit; JANGAN pakai
## CombatSystem.calc_skill_damage (float, tanpa rantai bulat pygame).
func kit_skill_damage() -> int:
	var base := int(skill_damage)
	var inv = items
	if inv != null:
		var amp := float(inv.get_skill_amp())
		if amp > 0.0:
			base = HeroDB._py_round(float(base) * (1.0 + amp))
	if status != null and status.skill_down_timer > 0.0:
		var f := maxf(0.0, 1.0 - float(status.skill_down_amount))
		return HeroDB._py_round(float(base) * f)
	return base


## settings.get_all_hero_types()[hero_type] — katalog mentah heroes.json.
func kit_catalog_all() -> Dictionary:
	return HeroDB.catalog_all()


## settings.HERO_LEVELS (int-keyed) untuk reset buff damage Thorne R dkk.
func kit_hero_levels() -> Dictionary:
	return HeroDB.hero_levels_int()


## e.take_damage(dmg, team[, source=, school=]) — kwargs DIPERTAHANKAN per
## call-site (attribution damage_dealt hanya bila source ada; sekolah
## menentukan armor-vs-MR). Lifesteal/cleave item TIDAK ikut: di pygame
## damage skill tidak memicu jalur _on_attacker_hit penyerang (jaket
## CombatSystem.apply_damage punya flag trigger_on_hit=false untuk ini).
func kit_hit(e, dmg, from_team, src = null, school = "") -> void:
	if e == null or not is_instance_valid(e):
		return
	# Kredit damage_dealt ada di CombatSystem.apply_damage (int, setelah
	# HP). Jangan dijumlah di sini — pygame `credit_hero_damage` dipanggil
	# sekali dari take_damage, bukan dari handler skill.
	CombatSystem.apply_damage(e, float(dmg), str(from_team),
		"normal", src, str(school) if school != null else "", false)


## e.apply_slow(amount, durasi_FRAME pygame).
func kit_slow(e, amount: float, dur_frames) -> void:
	if e == null or not is_instance_valid(e):
		return
	if not kit_has_slow(e):
		return
	e.status.apply_slow(float(amount), float(dur_frames) / 60.0)


## _apply_stun / e.attack_timer = max(t, F_frame) pygame.
func kit_lock(e, frames) -> void:
	if e == null or not is_instance_valid(e):
		return
	if not ("attack_timer" in e):
		return
	e.attack_timer = maxf(float(e.get("attack_timer")), float(frames) / 60.0)


func kit_atk_timer(e) -> float:
	if e == null or not is_instance_valid(e) or not ("attack_timer" in e):
		return 0.0
	return float(e.get("attack_timer")) * 60.0


func kit_unit_alive(e) -> bool:
	if e == null or not is_instance_valid(e):
		return false
	return not bool(e.get("is_dead"))


## hasattr(e, "apply_slow") — unit dengan status effects (bukan tower/nexus).
func kit_has_slow(e) -> bool:
	if e == null or not is_instance_valid(e):
		return false
	var st = e.get("status")
	return st != null


func kit_has_atk_timer(e) -> bool:
	if e == null or not is_instance_valid(e):
		return false
	return "attack_timer" in e


func kit_has_hp(e) -> bool:
	if e == null or not is_instance_valid(e):
		return false
	return "hp" in e


## _shake_screen / _play_skill_sound / _add_popup — lapisan feedback; di
## harness replay tetap aman (call_group tanpa receiver = no-op).
func kit_shake(amount: float) -> void:
	var tree := Engine.get_main_loop()
	if tree is SceneTree:
		(tree as SceneTree).call_group("camera", "add_trauma", amount / 60.0)


func kit_sound(volume: float) -> void:
	AudioManager.play_sfx("hero_skill", volume)


func kit_popup(text: String, critical: bool = false) -> void:
	var num = preload("res://scenes/fx/DamageNumber.tscn").instantiate()
	num.setup(text, critical)
	num.global_position = global_position + Vector2(0.0, -26.0)
	var host := get_tree().current_scene
	if host != null and is_instance_valid(host):
		host.add_child(num)


## Hero._spawn_skill_projectile: visual homing TANPA damage (damage skill
## instan). Harness replay melewatkan spawn (tidak ada sistem proyektil).
## `speed` adalah parameter warisan pygame — SkillProjectile Godot memakai
## konstanta internal 13 px/frame (paritas), jadi nilai ini sengaja diabaikan.
func kit_skill_proj(target, _speed := 13.0) -> void:
	if kit_no_projectiles or target == null or not is_instance_valid(target):
		return
	var p := SkillProjectileScript.new()
	p.setup(target, hero_type, self)
	var host := get_tree().current_scene
	if host != null:
		host.add_child(p)


## Pengganti blok `try: from heroes/<alias>_fx import ... notify_skill_cast/
## impact` (lapisan visual per-boss). Sama seperti jembatan Boss.gd.
func kit_fx_cast(skill: String) -> void:
	kit_popup(str(skill).to_upper(), false)
	_kit_ring(global_position, radius + 16.0, fill_color.lightened(0.25))


func kit_fx_impact(x: float, y: float, r: float, skill: String) -> void:
	_kit_ring(Vector2(x, y), maxf(10.0, r), fill_color.lightened(0.4))
	if skill == "r":
		_kit_ring(Vector2(x, y), maxf(10.0, r) * 0.6, Color(1.0, 0.85, 0.4))


func _kit_ring(center: Vector2, r: float, col: Color) -> void:
	var host := get_tree().current_scene
	if host == null or not is_instance_valid(host):
		return
	var ring = preload("res://scenes/fx/KitShockRing.gd").new()
	ring.setup(center, r, col)
	host.add_child(ring)


## Input catch-up: jumlah hero NON-starter yang sudah dibuka pemain lintas
## save — paritas `Hero.__init__` pygame (_entity.py:3355-3360):
##
##     _g = getattr(__main__, "game_instance", None)
##     _unlocks = hero_balance.boss_unlocks_for_purchases(
##         getattr(_g, "purchased_heroes", None) if _g else None)
##
## Sumbernya SAVE (`purchased_heroes` pygame = `unlocked_heroes` Godot),
## bukan roster in-match, dan berlaku untuk hero KEDUA tim. Di luar match
## GameManager tidak mengikat daftarnya -> 0 (bonus catch-up penuh, sama
## seperti save baru). Dikunci fixture `hero_catchup_unlocks` +
## HeroCatchupUnlockParityTest.
func _catchup_unlocks() -> int:
	return GameManager.catchup_unlocks()


## ══ HARNESS PARITAS (HeroSkillParityTest) ══
## Satu langkah frame dengan urutan yang sama persis oracle
## tools/test_godot_match_parity.py::_run_hero_skill_scenario:
##   cast (opsional) -> Q-- -> active-- -> WER-- -> kit.update_timers
##   -> hit harness 'fire' (tiap 37f mulai f30, bila ada musuh) -> floor hp.
## Mengembalikan hasil cast (true/false) untuk dicatat test.
func skill_test_step(frame: int, cast_key: String, force: bool, enemies: Array) -> bool:
	var ok := false
	if cast_key != "":
		if force:
			match cast_key:
				"q":
					skill_timer = 0
				"w":
					w_cooldown = 0
				"e":
					e_cooldown = 0
				"r":
					r_cooldown = 0
		ok = try_cast_skill(cast_key, enemies, [], [])
	if skill_timer > 0:
		skill_timer -= 1
	if active_skill_timer > 0:
		active_skill_timer -= 1
		if active_skill_timer <= 0:
			active_skill = null
	if w_cooldown > 0:
		w_cooldown -= 1
	if e_cooldown > 0:
		e_cooldown -= 1
	if r_cooldown > 0:
		r_cooldown -= 1
	HeroSkillKit.update_timers(self, enemies, [], [])
	if enemies.size() > 0 and frame >= 30 and frame % 37 == 0:
		# Sama seperti oracle: panggil guard+HP situs (CombatSystem.apply_damage
		# = padanan Hero.take_damage pygame) LANGSUNG — tanpa jalur die() milik
		# Godot. Di pygame harness, alive=False tidak pernah dibaca kode yang
		# diuji (cast/timer tidak ceknya), jadi floor 1.0 cukup.
		CombatSystem.apply_damage(self, 40.0, "red", "fire", enemies[0], "")
	if hp < 1.0:
		hp = 1.0
	return ok


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
	if active_skill != null:
		skill_key = str(active_skill)
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
	# pygame Hero._do_attack TIDAK memanggil combat_feel.hit_stop /
	# screenshake (itu milik FX skill / camera lain). Jangan request_hit_stop
	# di sini — harness mengunci GameManager._hit_stop_active tetap false.

	var dmg := CombatSystem.calc_damage(self, target, damage, dmg_school)
	# Suara serangan dasar: tebasan (melee) atau lesatan (ranged). Paritas
	# combat_audio.play_hero_basic dipanggil dari Hero._attack _entity.py:4412-4418:
	# flag is_melee_hero lebih dulu, kalau tidak ada pakai ambang jarak 100.
	# Berlaku untuk hero tim biru MAUPUN merah (pygame tidak membedakan tim).
	AudioManager.play_combat(AudioManager.basic_attack_sfx(is_melee_hero, attack_range))
	# pygame _do_attack 4347: melee ATAU morgath (beam petirnya digambar
	# renderer boss, bukan projectile) → damage INSTAN dengan damage_type
	# 'normal' + school; ranged lain → proyektil ('projectile').
	if is_melee_hero or hero_type == "morgath":
		var t = target
		CombatSystem.apply_damage(t, dmg, team, "normal", self, dmg_school)
		# Efek on-attack item (bash/chain/frostbite/miasma/empower/entangle).
		# Sengaja dipanggil DI SINI, bukan di CombatSystem.apply_damage: pygame
		# hanya memicunya dari on_basic_attack_hit (hero_items.py:2484-2517)
		# dengan damage PRA-mitigasi — jadi damage skill & DoT tidak boleh
		# ikut nge-proc, dan angkanya bukan damage yang mendarat.
		# Lifesteal/cleave/corroder dibayar di CombatSystem._on_attacker_hit
		# (basis dmg, bukan damage mendarat).
		if items != null and items.has_method("on_attack_hit"):
			items.on_attack_hit(t, dmg)
	else:
		# RANGED — urutan pygame _do_attack 4336-4365: proyektil dilepas
		# DULU, lifesteal dibayar SAAT ITU dengan int(damage*ls) (bukan saat
		# mendarat), lalu on_ranged_attack_hit (bash/chain/shred tier II).
		_shoot_projectile(target, dmg)
		if items != null:
			var ls := float(items.get_lifesteal_pct())
			if ls > 0.0:
				CombatSystem.heal_gain_py(self, float(int(dmg * ls)))
			if items.has_method("on_attack_hit"):
				items.on_attack_hit(target, dmg)


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
## hero_skills/_bundle.py), jadi pemanggilnya jembatan kit_hit()/kit_popup()
## di file ini — bukan serangan dasar.
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
	if GameManager._killer_is_hero(killer, self):
		# Object.get() hanya menerima nama properti (bukan default ala Dictionary).
		# Hero selalu punya `kills`; tambah langsung supaya kill AI terhitung.
		killer.kills = int(killer.get("kills")) + 1
	# Reward kematian hero (paritas loop reward _core.py:2227-2235): +150
	# FLAT ke tim lawan KORBAN (hero merah mati -> pemain, hero biru -> AI),
	# tanpa memedulikan siapa pembunuhnya dan TANPA menyalakan combo.
	GameManager.register_hero_death(self)
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
	# VISUAL ONLY: state kit (charge powershot, tickers) TIDAK dibersihkan di
	# sini — paritas _entity.py: Hero yang mati berhenti di-update sehingga
	# timer membeku dan berjalan lagi saat respawn; respawn() hanya menyiapkan
	# ulang Q (skill_timer=0), tidak menyentuh W/E/R maupun charge.
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
	# _entity.py:4765-4767 (respawn): HANYA Q yang direset siap —
	# W/E/R tetap carrying cooldown (membeku selama mati) dan charge kit
	# dibiarkan lanjut. active_skill(+timer) juga TIDAK disentuh pygame.
	skill_timer = 0
	_recalc_derived(true)
	is_dead = false
	# Flag reward dibuka ulang saat hidup kembali (paritas reset
	# `h._rewarded = False` Game.update _core.py:2263-2265): hero yang
	# respawn lalu mati lagi membayar +150 sekali lagi — dikunci FASE 13
	# (hero_respawn_reward_twice) + FASE 15 (rewarded snapshot).
	reward_processed = false
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
		# pygame `_build_name_badge`: nama SAJA; bintang level digambar
		# terpisah di `_draw_level_stars` (bukan teks "LvN").
		name_label.text = display_name
	queue_redraw()


# ══════════════════════════════════════════════════════════
#  SKILL (dipanggil HUD / tombol Q W E R)
# ══════════════════════════════════════════════════════════

func cast_q(): return _cast_skill("q")
func cast_w(): return _cast_skill("w")
func cast_e(): return _cast_skill("e")
func cast_r(): return _cast_skill("r")


func _cast_skill(key: String) -> bool:
	if is_dead:
		return false
	var lists := _kit_lists()
	var ok := try_cast_skill(key, lists[0], lists[1], lists[2])
	if ok:
		play_skill_fx(key)
	else:
		# Cast gagal (cooldown belum siap / tidak ada target): umpan balik
		# "tidak bisa" paritas _cast_hero_skill _core.py:8441 (ui_error
		# volume_mult 0.3). Suara/shake yang berhasil dibunyikan handler kit
		# (BaseSkill._trigger_* -> h.kit_sound).
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


## Bintang level di atas papan nama — port `_build_name_badge`
## `_entity.py:4931-4970`. L<=5: satu bintang per level; L>5: 1 bintang + `xN`.
func _draw_level_stars() -> void:
	var y := -72.0
	var col := Color(1.0, 0.85, 0.2, 0.95)
	if level <= 5:
		for i in level:
			var sx := -float(level - 1) * 5.0 + float(i) * 10.0
			_draw_star(Vector2(sx, y), col)
	else:
		_draw_star(Vector2(-10.0, y), col)
		var font: Font = ThemeDB.fallback_font
		if font != null:
			draw_string(font, Vector2(-2.0, y + 4.0), "x%d" % level,
				HORIZONTAL_ALIGNMENT_LEFT, -1, 10, col)


func _draw_star(c: Vector2, col: Color) -> void:
	draw_colored_polygon(PackedVector2Array([
		c + Vector2(0, -3), c + Vector2(2, 0), c + Vector2(4, 0),
		c + Vector2(2, 2), c + Vector2(3, 5), c + Vector2(0, 3),
		c + Vector2(-3, 5), c + Vector2(-2, 2), c + Vector2(-4, 0),
		c + Vector2(-2, 0),
	]), col)


func _draw() -> void:
	_draw_level_stars()
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
	# State skill kit (field h.kit — nama persis seperti _bundle.py). Sejak
	# hero memakai HeroSkillKit, buff ini hidup di kit, bukan status.buffs.
	if i <= 4 and not kit.is_empty():
		var kit_dots: Array = [
			[int(kit.get("_wind_wall_timer", 0)) > 0,
				Color(0.6, 0.9, 1.0, 0.9)],
			[bool(kit.get("_windrun_active", false)),
				Color(0.55, 1.0, 0.65, 0.9)],
			[bool(kit.get("_bristleback_active", false)),
				Color(0.8, 1.0, 0.5, 0.9)],
			[bool(kit.get("_shadow_realm_active", false)),
				Color(0.7, 0.6, 1.0, 0.9)],
		]
		for pair in kit_dots:
			if not bool(pair[0]):
				continue
			draw_circle(Vector2(-14 + float(i) * 7, -46), 2.6, pair[1])
			i += 1
			if i > 4:
				break
	var j := 0
	for icon in status.active_icon_list():
		draw_circle(Vector2(-14 + float(j) * 7, -52), 2.2, Color(1.0, 0.35, 0.35, 0.9))
		j += 1
		if j > 4:
			break
_list():
		draw_circle(Vector2(-14 + float(j) * 7, -52), 2.2, Color(1.0, 0.35, 0.35, 0.9))
		j += 1
		if j > 4:
			break
