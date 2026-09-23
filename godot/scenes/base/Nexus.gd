# Nexus.gd — port _entity.Castle (base yang harus dihancurkan).
#
# Inilah kondisi menang/kalah yang sebelumnya tidak ada di versi Godot:
#   red nexus hancur  -> GameManager.state = "victory"
#   blue nexus hancur -> GameManager.state = "defeat"
# (paritas _core.Game.update 2281-2292)
#
# Statistik per level castle dibaca dari TowerDB (godot/data/nexus.json =
# NEXUS_LEVELS pygame): L1 4000 HP / 35 dmg / 150 range / 45f cd ... L5 15000 HP.
# Castle Shield: gratis sampai wave 10, sesudah itu harus dibeli (850 gold),
# menyerap 1:1 lalu memotong sisa damage 88%.
#
# ATURAN TAMPIL DI PETA: tidak ada satu pun angka HP yang digambar di atas
# kastil. pygame hanya menggantung crest armor + bar SHIELD 60x6 di atas
# badannya (`_draw_castle_shield` + `_draw_hp_bar`), dan itu yang diport di
# `_draw_overlays`. Bar HP kastil (84x7) + pip level yang pernah ditambah port
# menutupi peta dan DIHAPUS (permintaan user 2026-09-13) — HP dibaca lewat
# tab NEXUS ShopPanel, sama seperti pygame membaca `castle.hp` lewat popup.
extends Node2D

const TowerBulletScript = preload("res://scenes/tower/TowerBullet.gd")
const BakedPropDB = preload("res://scripts/render/BakedPropDB.gd")
const ArmorCrestScript = preload("res://scripts/render/ArmorCrest.gd")
const FPS := 60.0

@export var team: String = "blue"

var level: int = 1
var max_hp: float = 4000.0
var hp: float = 4000.0
var damage: float = 35.0
var attack_range: float = 150.0
var attack_cooldown: float = 45.0 / FPS
var minion_scale: float = 1.0
var radius: float = 45.0
var armor: float = 0.0
var magic_resist: float = 0.0
var dmg_school: String = "physical"
var color_accent: Color = Color(1, 1, 1)

# ── shield (Castle Shield) ──
var shield: float = 0.0
var shield_max: float = 0.0
var shield_active: bool = true
var shield_damage_reduction: float = 0.88
var free_shield_active: bool = true
var castle_shield_purchased: bool = false
var no_damage_timer: float = 0.0
## Flash crest saat shield regen (`_entity.py:1725`, 4 frame).
var shield_regen_flash: float = 0.0

# ── state ──
var is_dead: bool = false
var target: Node2D = null
var attack_timer: float = 0.0
var angle: float = 0.0
var selected: bool = false
var pulse: float = 0.0
var display_name: String = "Nexus"
## Cache entri manifest bake kastil (Fase 7).
var _baked: Dictionary = {}

func _ready() -> void:
	add_to_group("nexus")
	z_as_relative = false
	z_index = 40
	radius = TowerDB.base_radius()
	_apply_level_stats()
	var cfg: Dictionary = TowerDB.shield_cfg()
	shield_damage_reduction = float(cfg.get("damage_reduction", 0.88))
	set_wave(0)
	display_name = "Radiant Nexus" if team == "blue" else "Dire Nexus"
	GameManager.register_nexus(self)

func _exit_tree() -> void:
	GameManager.unregister_nexus(self)

## CombatSystem itu autoload singleton -> boleh dirujuk langsung sebagai
## identifier global (gaya yang sama dengan Hero.gd/Minion.gd). Helper ini
## dipertahankan supaya call site tetap `var cs = _combat()` dan mudah
## di-mock kalau suatu saat combat dipisah per-scene.
func _combat():
	return CombatSystem

# ══════════════════════════════════════════════════════════
#  STAT & SHIELD
# ══════════════════════════════════════════════════════════

func _apply_level_stats() -> void:
	var s: Dictionary = TowerDB.nexus_stats(level)
	var old_max := max_hp
	var old_hp := hp
	var old_shield_max := shield_max
	var old_shield := shield
	max_hp = float(s["hp"])
	if old_max > 0.0 and old_hp > 0.0:
		# paritas Castle._apply_level_stats: pertahankan rasio + bonus 500
		var ratio := old_hp / old_max
		hp = minf(max_hp, max_hp * ratio + 500.0)
	else:
		hp = max_hp
	damage = float(s["damage"])
	attack_range = float(s["range"])
	attack_cooldown = float(s["cooldown"])
	minion_scale = float(s["minion_scale"])
	color_accent = s["color_accent"]
	var cfg: Dictionary = TowerDB.shield_cfg()
	shield_max = max_hp * float(cfg.get("hp_ratio", 1.0))
	# Upgrade castle mempertahankan persentase shield yang tersisa
	if old_shield_max > 0.0:
		shield = shield_max * clampf(old_shield / old_shield_max, 0.0, 1.0)
	else:
		shield = shield_max if shield_active else 0.0
	queue_redraw()

func set_wave(wave_number: int) -> void:
	# paritas Castle.set_wave: perlindungan gratis sampai wave 10
	var cfg: Dictionary = TowerDB.shield_cfg()
	if not bool(cfg.get("enabled", true)):
		shield_active = false
		return
	free_shield_active = wave_number <= int(cfg.get("free_waves", 10))
	if free_shield_active:
		shield_active = true
		if shield <= 0.0:
			shield = shield_max
	elif not castle_shield_purchased:
		shield_active = false
		shield = 0.0
	else:
		shield_active = true
	queue_redraw()

func can_buy_shield() -> bool:
	return not free_shield_active and not castle_shield_purchased and not is_dead

func shield_cost() -> int:
	return int(TowerDB.shield_cfg().get("cost", 850))

func activate_castle_shield() -> bool:
	if not can_buy_shield():
		return false
	castle_shield_purchased = true
	free_shield_active = false
	shield_active = true
	shield_max = max_hp * float(TowerDB.shield_cfg().get("hp_ratio", 1.0))
	shield = shield_max
	no_damage_timer = 0.0
	queue_redraw()
	return true

func can_upgrade() -> bool:
	return level < TowerDB.nexus_max_level() and not is_dead

func upgrade_cost() -> int:
	if not can_upgrade():
		return 0
	return int(TowerDB.nexus_stats(level).get("upgrade_cost", 0))

func upgrade() -> bool:
	if not can_upgrade():
		return false
	level += 1
	_apply_level_stats()
	GameManager.nexus_upgraded.emit(team, level)
	return true

func _update_shield_regen(delta: float) -> void:
	if not shield_active:
		return
	no_damage_timer += delta
	var cfg: Dictionary = TowerDB.shield_cfg()
	var delay := float(cfg.get("regen_delay_frames", 120)) / FPS
	var rate := float(cfg.get("regen_rate_per_frame", 3.5)) * FPS
	if no_damage_timer >= delay and shield < shield_max:
		shield = minf(shield_max, shield + rate * delta)

# ══════════════════════════════════════════════════════════
#  LOOP
# ══════════════════════════════════════════════════════════

func _physics_process(delta: float) -> void:
	if is_dead or GameManager.state != "playing":
		return
	pulse += delta * 3.0
	attack_timer = maxf(0.0, attack_timer - delta)
	if shield_regen_flash > 0.0:
		shield_regen_flash = maxf(0.0, shield_regen_flash - delta)
	_update_shield_regen(delta)

	var cs = _combat()
	if cs != null:
		# last_wins_ties=true — paritas Castle._find_target pygame
		# (_entity.py:1744-1749, `dist <= best_dist`).
		target = cs.nearest_enemy(self, attack_range, true)
	if target != null:
		angle = (target.global_position - global_position).angle()
		if attack_timer <= 0.0:
			_shoot()
			attack_timer = attack_cooldown
	queue_redraw()

func _shoot() -> void:
	if target == null:
		return
	var b = TowerBulletScript.new()
	# Pygame Castle._shoot (_entity.py:1752-1755) membuat Bullet TANPA
	# source dan Bullet._on_hit menerapkan take_damage(damage, team,
	# 'projectile') tanpa source — nexus tidak pernah memberi kill credit
	# maupun reflect (paritas Bristleback/Thornmail/blind).
	b.setup(target, damage, team, "normal", {}, TowerDB.bullet_speed() * 0.85,
		color_accent, null)
	b.global_position = global_position + Vector2(cos(angle), sin(angle)) * 26.0
	GameManager.attach_fx(b)

# ══════════════════════════════════════════════════════════
#  DAMAGE
# ══════════════════════════════════════════════════════════

func take_damage(amount: float, from_team: String = "", dmg_type: String = "normal",
		source = null, school: String = "") -> void:
	if is_dead:
		return
	no_damage_timer = 0.0
	# HP SEBELUM damage: pygame membandingkan blue_base.hp dengan nilai frame
	# sebelumnya (_core.py:2275-2276), jadi castle shield yang menyerap semua
	# damage tidak memicu suara. Hanya castle pemain (biru) yang berbunyi.
	var hp_before := hp
	var cs = _combat()
	if cs != null:
		cs.apply_damage(self, amount, from_team, dmg_type, source, school)
	else:
		hp -= amount
	if team == "blue" and hp < hp_before:
		# throttle 300 ms ada di AudioManager.THROTTLE_MS (paritas _system.py:512)
		AudioManager.play_sfx("nexus_hit", 0.7)
	queue_redraw()
	if hp <= 0.0:
		die(from_team)

func heal(amount: float) -> void:
	if is_dead:
		return
	hp = minf(max_hp, hp + amount)

func die(killer_team: String = "") -> void:
	if is_dead:
		return
	is_dead = true
	hp = 0.0
	shield = 0.0
	shield_active = false
	target = null
	print("[Nexus] %s hancur oleh %s" % [display_name, killer_team])
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(self, "modulate:a", 0.25, 0.9)
	tw.tween_property(self, "scale", Vector2(1.15, 0.7), 0.9)
	GameManager.nexus_destroyed.emit(team, killer_team)

# ══════════════════════════════════════════════════════════
#  GAMBAR
# ══════════════════════════════════════════════════════════

func _draw() -> void:
	var team_col := Color(0.30, 0.55, 1.0) if team == "blue" else Color(0.92, 0.30, 0.28)
	var cfg: Dictionary = TowerDB.shield_cfg()
	# BAYANGAN LEMBUT di kaki kastil — pengganti "halaman batu" lama
	# (piringan batu pekat radius*1.55 + cincin warna tim) yang menutupi
	# peta di sekeliling kastil. Pygame sendiri tidak menggambar tanah di
	# kastil (_entity._draw_castle_ground = no-op), jadi kastil cukup
	# "mendarat" di peta lewat bayangan pipih halus ini.
	draw_set_transform(Vector2(0.0, 13.0), 0.0, Vector2(1.0, 0.36))
	draw_circle(Vector2.ZERO, 46.0, Color(0, 0, 0, 0.22))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# ── Fase 7: badan kastil dari bake renderer pygame (seni asli) ──
	# pygame menggambar kastil lewat _render_castle_full (5 level, ~1.600
	# baris: tembok, gerbang, menara, obor, aura). Turret/gerigi/kristal
	# geometris di bawah HANYA dipakai kalau bake tidak tersedia.
	if _baked.is_empty():
		_baked = BakedPropDB.nexus_entry(team)
	if not _baked.is_empty() and _draw_baked_castle(team_col):
		_draw_overlays(team_col, cfg)
		return
	_draw_geometric_castle(team_col)
	_draw_overlays(team_col, cfg)

## Gambar badan kastil dari strip bake. False = tekstur/frame tidak ada.
func _draw_baked_castle(_team_col: Color) -> bool:
	var tex: Texture2D = BakedPropDB.texture(str(_baked.get("png", "")))
	if tex == null:
		return false
	var region := BakedPropDB.frame_region(
		_baked, BakedPropDB.nexus_frame(_baked, level))
	if region.size.x <= 0.0:
		return false
	var a := BakedPropDB.anchor(_baked)
	draw_texture_rect_region(tex, Rect2(-a, region.size), region)
	return true

## Badan kastil geometris (jalur lama, kalau bake tidak tersedia).
func _draw_geometric_castle(team_col: Color) -> void:
	# 4 turret penjuru (paritas ArenaMap._draw_base)
	for i in range(4):
		var a := TAU * float(i) / 4.0 + PI * 0.25
		var p := Vector2(cos(a), sin(a)) * radius * 1.18
		draw_circle(p, 11.0, Color(0.45, 0.43, 0.4, 1))
		draw_arc(p, 11.0, 0.0, TAU, 16, team_col, 2.0)
	# badan castle
	draw_colored_polygon(PackedVector2Array([
		Vector2(-28, 18), Vector2(28, 18), Vector2(24, -22), Vector2(-24, -22)]),
		Color(0.36, 0.34, 0.33, 1))
	# gerigi atas
	for i in range(5):
		var x := -24.0 + float(i) * 12.0
		draw_rect(Rect2(Vector2(x, -32), Vector2(8, 10)), Color(0.44, 0.42, 0.4, 1), true)
	# nexus kristal (denyut)
	var glow := 0.65 + 0.35 * sin(pulse)
	draw_circle(Vector2(0, -4), 15.0, Color(team_col.r, team_col.g, team_col.b, 0.35 * glow))
	draw_colored_polygon(PackedVector2Array([
		Vector2(0, -20), Vector2(11, -4), Vector2(0, 12), Vector2(-11, -4)]),
		color_accent.darkened(0.15))
	draw_colored_polygon(PackedVector2Array([
		Vector2(0, -16), Vector2(6, -4), Vector2(0, 8), Vector2(-6, -4)]),
		Color(color_accent.r, color_accent.g, color_accent.b, glow))

## Lapisan di atas badan kastil: crest armor + bar SHIELD + ring seleksi +
## overlay mati. pygame menggambar semua ini di luar `_render_castle_full()`,
## jadi tidak ikut bake di kedua jalur.
##
## TIDAK ADA BAR HP di atas kastil — dan itu bukan kekurangan port:
## `Castle.draw` `_entity.py:1855-1889` memanggil `_draw_castle_shield` +
## `_draw_hp_bar`, dan `_draw_hp_bar` `_entity.py:1918-1946` satu-satunya
## menggambar bar SHIELD 60x6 di `y-80` + label "SHIELD n%" di atasnya.
## HP kastil pygame tidak pernah ditumpangkan ke peta (angka aslinya hidup di
## popup/panel nexus — tab NEXUS ShopPanel — dan di overlay debug).
## Bar HP 84x7 + pip level yang dulu digambar port Godot DIHAPUS
## (permintaan user 2026-09-13: "castle HP menghalangi map").
func _draw_overlays(_team_col: Color, cfg: Dictionary) -> void:
	var sc: Color = cfg.get("color_blue", Color("#64c8ff")) if team == "blue" \
		else cfg.get("color_red", Color("#ff7878"))
	# Obor gerbang L4+ + aura L6 — `_render_dynamic_effects` `:3063-3080`
	if level >= 4:
		_draw_gate_torch(Vector2(-16.0, 8.0), 0.0)
		_draw_gate_torch(Vector2(16.0, 8.0), 5.0)
	if level >= 6:
		_draw_magic_aura()
	# ── ARMOR CREST — `_draw_castle_shield` `_entity.py:1892-1916` ──
	# pygame memusatkan crest di (castle.x, canvas_atas-10); dengan kanvas
	# 180x160 diskala 0.85 itu y = -111 dari origin node (anchor bake sama
	# dengan (castle.x, castle.y), lihat tools/convert_to_godot.py
	# _bake_nexus_frames). Hanya terlihat kalau shield masih ada.
	if shield_active and shield > 0.0 and shield_max > 0.0:
		var ratio := clampf(shield / shield_max, 0.0, 1.0)
		var bob := sin(pulse * 1.2) * 2.0
		ArmorCrestScript.draw(self, Vector2(0.0, -111.0 + bob), 18.0,
			sc, ratio, shield_regen_flash > 0.0)
	# ── bar SHIELD — `_draw_hp_bar` `_entity.py:1918-1946` ──
	# rect (x-30, y-80, 60, 6), latar (30,30,50), isi seukuran rasio warna
	# shield, outline hitam 1 px (pygame border_radius=3; Godot kotak), dan
	# label "SHIELD n%" 10 px Barlow-Bold di (x-30, y-92) warna (200,220,255).
	# `blit` pygame menaruh UJUNG ATAS teks; draw_string Godot memakai
	# BASELINE, jadi tinggi ascent font ditambahkan.
	if shield_active and shield_max > 0.0:
		var bar_w := 60.0
		var bar_h := 6.0
		var top := Vector2(-bar_w * 0.5, -80.0)
		var sh_ratio := clampf(shield / maxf(1.0, shield_max), 0.0, 1.0)
		var bar := Rect2(top, Vector2(bar_w, bar_h))
		draw_rect(bar, Color(30.0 / 255.0, 30.0 / 255.0, 50.0 / 255.0), true)
		var fill := bar_w * sh_ratio
		if fill > 0.0:
			draw_rect(Rect2(top, Vector2(fill, bar_h)), sc, true)
		draw_rect(bar, Color(0, 0, 0, 1), false, 1.0)
		# pygame memakai get_font(10, 'body_bold') = Barlow-Bold 10 px —
		# bukan font fallback engine yang kasar.
		var font: Font = UiTheme.body_bold()
		if font != null:
			var pct := int(round(sh_ratio * 100.0))
			var label_top := top.y - 12.0
			draw_string(font, Vector2(top.x, label_top + font.get_ascent(10)),
				"SHIELD %d%%" % pct, HORIZONTAL_ALIGNMENT_LEFT, bar_w, 10,
				Color(200.0 / 255.0, 220.0 / 255.0, 255.0 / 255.0))
	if selected:
		draw_arc(Vector2.ZERO, radius * 1.7, 0.0, TAU, 40, Color(1, 0.92, 0.5, 0.85), 2.0)
	if is_dead:
		draw_rect(Rect2(Vector2(-40, -40), Vector2(80, 80)), Color(0, 0, 0, 0.45), true)

## Port `_draw_gate_torch` `_entity.py:3083-3170` (tanpa draw_ellipse).
func _draw_gate_torch(p: Vector2, off: float) -> void:
	draw_rect(Rect2(p + Vector2(-3, 0), Vector2(6, 8)), Color(0.28, 0.24, 0.22))
	draw_rect(Rect2(p + Vector2(-4, -3), Vector2(8, 3)), Color(0.18, 0.12, 0.08))
	var flicker := int(fmod(pulse * 4.0 + off, 5.0))
	var fire_h := 12.0 + float(flicker)
	draw_colored_polygon(PackedVector2Array([
		p + Vector2(-5, -3), p + Vector2(-2, -fire_h + 2.0),
		p + Vector2(0, -fire_h - 2.0), p + Vector2(2, -fire_h + 2.0),
		p + Vector2(5, -3),
	]), Color(0.75, 0.18, 0.05))
	draw_colored_polygon(PackedVector2Array([
		p + Vector2(-3, -4), p + Vector2(-1, -fire_h + 3.0),
		p + Vector2(0, -fire_h - 1.0), p + Vector2(1, -fire_h + 3.0),
		p + Vector2(3, -4),
	]), Color(1.0, 0.55, 0.12))
	draw_colored_polygon(PackedVector2Array([
		p + Vector2(-2, -5), p + Vector2(0, -fire_h + 4.0), p + Vector2(2, -5),
	]), Color(1.0, 0.9, 0.35))
	draw_circle(p + Vector2(0, -6), 11.0, Color(1.0, 0.45, 0.1, 0.14))

## Port `_draw_castle_magic_aura` `_entity.py:3172-3184` (elips → busur).
func _draw_magic_aura() -> void:
	var pul := sin(pulse * 0.8) * 0.3 + 0.7
	var r := 90
	while r > 30:
		var a := float(90 - r) * 2.0 * pul / 255.0
		if a > 0.0:
			draw_arc(Vector2(0, -20), float(r) * 0.45, 0.0, TAU, 28,
				Color(0.55, 0.75, 1.0, a), 2.0)
		r -= 8
	for i in 8:
		var ang := pulse * 0.9 + float(i) * (PI / 4.0)
		var rad := 28.0 + sin(pulse + float(i)) * 4.0
		var pt := Vector2(cos(ang) * rad, sin(ang) * rad * 0.5 - 20.0)
		draw_circle(pt, 1.4, Color(0.85, 0.95, 1.0, 0.8))
