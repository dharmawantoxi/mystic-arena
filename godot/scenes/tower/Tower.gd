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
const BakedPropDB = preload("res://scripts/render/BakedPropDB.gd")
const ArmorCrestScript = preload("res://scripts/render/ArmorCrest.gd")
const FPS := 60.0
const SHIELD_BLUE := Color(100.0 / 255.0, 180.0 / 255.0, 1.0)
const SHIELD_RED := Color(1.0, 100.0 / 255.0, 100.0 / 255.0)

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
## Kunci anti pembayaran ganda (padanan `_rewarded` pygame
## _core.py:2219-2220): menara yang sama hanya membayar reward + skor
## + counter true boss SEKALI, walau die()/callback dipanggil ulang.
var reward_processed: bool = false
var regen_shield_active: bool = false
var selected: bool = false
var upgrade_flash: float = 0.0
var shoot_flash: float = 0.0
## Frame flash saat shield regen (`_entity.py:860`, 3 frame) / aktifkan (6).
var shield_regen_flash: float = 0.0
var display_name: String = "Archer"
var color: Color = Color("#64dc78")
var color_dark: Color = Color("#328c46")

var _redraw_acc: float = 0.0
## Fase nyala obor menara bake (4 fase) — cuma dipakai jalur bake.
var _flame_t: float = 0.0
## Cache entri manifest bake supaya tidak parse JSON tiap frame.
var _baked: Dictionary = {}

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
	shield_regen_flash = 6.0 / FPS
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
	if shield_regen_flash > 0.0:
		shield_regen_flash = maxf(0.0, shield_regen_flash - delta)
	_update_regen(delta)

	var cs = _combat()
	if cs != null:
		# last_wins_ties=true — paritas Tower._find_target pygame yang
		# memakai `dist <= best_dist` (_entity.py:864-869): pada jarak
		# sama persis kandidat TERAKHIR yang menang.
		target = cs.nearest_enemy(self, attack_range, true)
	if target != null:
		angle = (target.global_position - global_position).angle()
		if attack_timer <= 0.0:
			_shoot(cs)
			attack_timer = attack_cooldown

	# redraw 20 Hz (flash + sudut laras + bar HP), bukan tiap frame
	_redraw_acc += delta
	_flame_t += delta
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
			# pygame set flash=3 SETIAP tick regen (`_entity.py:860`)
			# supaya crest tetap "bright" selama shield mengisi.
			shield = minf(shield_max,
				shield + float(scfg.get("rate_per_frame", 1.8)) * FPS * delta)
			shield_active = true
			shield_regen_flash = 3.0 / FPS

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
			# Archer `_shoot_archer` `_entity.py:904-937`: L5=2 / L6=3
			# panah (pad target yang sama); `double_shot` HANYA L<5.
			if tower_type == "archer" and level >= 5:
				_shoot_archer_volley(cs, speed)
			else:
				_spawn_bullet(target, damage, "normal", {}, speed, Color("#ffe9a8"))
				if double_shot:
					var second = null
					for e in cs.enemies_in_radius(team, global_position, attack_range):
						if e == target:
							continue
						second = e
						break
					if second != null:
						_spawn_bullet(second, damage, "normal", {}, speed,
							Color("#ffe9a8"))

## Port `_shoot_archer` L5/L6: 2/3 peluru, offset × SCALE 0.7 lalu `int()`,
## target ekstra dalam range, sisanya di-pad target utama.
func _shoot_archer_volley(cs, speed: float) -> void:
	var num_shots := 2 if level == 5 else 3
	var offsets: Array = []
	if num_shots == 2:
		offsets = [Vector2(-8, 0), Vector2(8, 0)]
	else:
		offsets = [Vector2(-11, 3), Vector2(0, -2), Vector2(11, 3)]
	var targets: Array = [target]
	for e in cs.enemies_in_radius(team, global_position, attack_range):
		if targets.size() >= num_shots:
			break
		if e == target:
			continue
		targets.append(e)
	while targets.size() < num_shots:
		targets.append(target)
	var scale := 0.7
	for i in num_shots:
		var off: Vector2 = offsets[i]
		_spawn_bullet(targets[i], damage, "normal", {}, speed, Color("#ffe9a8"),
			Vector2(float(int(off.x * scale)), float(int(off.y * scale))))

func _spawn_bullet(t: Node2D, dmg: float, btype: String, sp: Dictionary,
		speed: float, col: Color, spawn_offset: Vector2 = Vector2.ZERO) -> void:
	var b = TowerBulletScript.new()
	# Pygame Bullet._on_hit (_entity.py:246-248) memanggil
	# take_damage(damage, team, damage_type='projectile') TANPA source —
	# peluru menara TIDAK pernah membawa penembak. Source diputus (null)
	# supaya reflect Bristleback/Thornmail/blind/kill credit ikut paritas
	# (semua syarat source is not None di pygame _entity.py:4699-4710 /
	# hero_items.py:2460-2468).
	b.setup(t, dmg, team, btype, sp, speed, col, null)
	b.global_position = global_position + Vector2(cos(angle), sin(angle)) * 12.0 \
		+ Vector2(0, -22) + spawn_offset
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
	# Loop reward Game.update pygame (_core.py:2218-2227, cabang TIM KORBAN,
	# BUKAN tim pembunuh): menara merah → gold+skor pemain, menara biru →
	# saldo AI, termasuk sumber netral/tanpa killer. TANPA popup gold
	# (pygame tidak membuatnya) dan tanpa total_kills (hanya minion).
	# red_towers_destroyed (Main, via signal di bawah) naik sekali per
	# menara merah mati — digerakkan die() yang ter-guard ini.
	GameManager.register_tower_death(self)
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
	var body_top := -30.0 - float(level) * 2.0
	# ── Fase 7: badan menara dari bake renderer pygame (seni asli) ──
	# Kalau manifest tidak punya entri (bake belum dijalankan), jatuh ke
	# gambar geometris lama — perilaku pra-Fase 7 tetap utuh.
	if _baked.is_empty():
		_baked = BakedPropDB.tower_entry(tower_type, team)
	if not _baked.is_empty() and _draw_baked_body():
		_draw_overlays(team_col, body_top)
		return
	_draw_geometric_body(team_col, body_top)
	_draw_overlays(team_col, body_top)

## Gambar badan menara dari strip bake. Return false kalau tekstur/frame
## tidak tersedia (pemanggil lalu memakai gambar geometris).
func _draw_baked_body() -> bool:
	var tex: Texture2D = BakedPropDB.texture(str(_baked.get("png", "")))
	if tex == null:
		return false
	var shoot_frames := BakedPropDB.tower_shoot_frames(_baked, level)
	var idle_frames := BakedPropDB.tower_idle_frames(_baked, level)
	var frames: Array = idle_frames
	var fps := float(_baked.get("fps_flame", 15.0))
	if shoot_flash > 0.0 and not shoot_frames.is_empty():
		# Pygame memilih pose tembak dari shoot_flash_timer (8 -> 4 -> 0).
		# Godot menurunkan shoot_flash dari 1/6 dtk; petakan ke 2 frame.
		frames = shoot_frames
		fps = float(_baked.get("fps_shoot", 12.0))
	if frames.is_empty():
		return false
	var idx := int(_flame_t * fps) % frames.size()
	var region := BakedPropDB.frame_region(_baked, int(frames[idx]))
	if region.size.x <= 0.0:
		return false
	var a := BakedPropDB.anchor(_baked)
	draw_texture_rect_region(tex, Rect2(-a, region.size), region)
	return true

## Badan menara geometris (jalur lama, dipakai kalau bake tidak ada).
func _draw_geometric_body(team_col: Color, body_top: float) -> void:
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

## Lapisan yang digambar Godot di ATAS badan menara (bake maupun geometris):
## pip level, gelembung shield, bar HP, kilau upgrade, ring seleksi.
## pygame menggambar semua ini di luar render_tower(), jadi tidak ikut bake.
func _draw_overlays(team_col: Color, body_top: float) -> void:
	# pip level
	for i in range(level):
		draw_circle(Vector2(-radius * 0.5 + float(i) * 5.0, -12), 1.8,
			Color(1, 0.85, 0.35, 0.9))
	# Armor crest (pengganti gelembung) — `_draw_shield_crest` `:1295-1317`
	if shield > 0.0 and shield_max > 0.0:
		var ratio := clampf(shield / shield_max, 0.0, 1.0)
		var sc: Color = SHIELD_BLUE if team == "blue" else SHIELD_RED
		ArmorCrestScript.draw(self, Vector2(26.0, -28.0 - float(level)), 14.0,
			sc, ratio, shield_regen_flash > 0.0)
	# bar HP + shield
	var w := 34.0
	var hp_ratio := clampf(hp / maxf(1.0, max_hp), 0.0, 1.0)
	draw_rect(Rect2(Vector2(-w * 0.5, body_top - 22), Vector2(w, 4)),
		Color(0, 0, 0, 0.55), true)
	draw_rect(Rect2(Vector2(-w * 0.5, body_top - 22), Vector2(w * hp_ratio, 4)),
		team_col.lightened(0.1), true)
	if shield_max > 0.0:
		var sh_ratio := clampf(shield / shield_max, 0.0, 1.0)
		var shc: Color = SHIELD_BLUE if team == "blue" else SHIELD_RED
		if shield_regen_flash > 0.0:
			shc = Color(minf(1.0, shc.r + 50.0 / 255.0),
				minf(1.0, shc.g + 50.0 / 255.0),
				minf(1.0, shc.b + 50.0 / 255.0))
		draw_rect(Rect2(Vector2(-w * 0.5, body_top - 26), Vector2(w * sh_ratio, 2.5)),
			shc, true)
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
