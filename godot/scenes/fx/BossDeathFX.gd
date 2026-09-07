# BossDeathFX.gd — port BossDeathAnimation (effects_intro? bukan — kelas
# BossDeathAnimation ada di _render.py:1622, dipakai _core.py:2124-2125).
#
# Urutan kematian boss (paritas frame demi frame):
#   1. FASE KEMATIAN — gameplay PAUSE (paritas _core.py:1995-1997 return):
#      true boss 90 frame / mini boss 60 frame (:1650-1655).
#        • white flash layar penuh 15 frame (alpha 200 -> 0, :1834-1838),
#        • 2-3 gelombang cincin ledakan (:1841-1878),
#        • dissolve badan boss paruh pertama (:1881-1905),
#        • 15/25 pecahan shatter (:1702-1726, fisika per frame),
#        • 15/30 partikel "roh" naik bergelombang (:1728-1742).
#      SFX ledakan/victory SUDAH dimainkan Boss.die() (paritas
#      BossDeathAnimation.update :1757-1766 dibunyikan sekali di awal —
#      frame yang sama), jadi tidak dibunyikan ulang di sini.
#   2. FASE PERAYAAN (true boss saja, 120 frame) — gameplay JALAN LAGI
#      ("Update celebration tapi tidak pause gameplay" _core.py:2000-2001):
#      overlay gelap + tint emas, "BOSS DEFEATED!" melompat masuk, nama +
#      gelar boss, "+ X GOLD", "HERO UNLOCKED!", 6 bintang berputar,
#      hint skip. Fanfare victory 1.0 diputar saat perayaan mulai
#      (paritas :1789-1796). Skip: SPACE / ESC / klik (:1812-1818).
#
# Node dipakai dari Boss.die(): host.add_child(fx); fx.global_position = pos.
extends Node2D

const DEATH_DURATION_TRUE := 90.0
const DEATH_DURATION_MINI := 60.0
const CELEBRATION_FRAMES := 120.0
const FLASH_FRAMES := 15.0
const WAVE_FRAMES := 40.0

var active: bool = true
var death_active: bool = true
var celebration_active: bool = false
var show_celebration: bool = false
var boss_class: String = "mini"
var boss_name: String = "Boss"
var boss_title: String = ""
var boss_color: Color = Color(0.6, 0.4, 0.85)
var boss_color_dark: Color = Color(0.3, 0.2, 0.45)
var entrance_color: Color = Color(0.6, 0.4, 0.85)
var gold_reward: int = 0
var boss_radius: float = 22.0

var _duration: float = DEATH_DURATION_MINI
var _frame: float = 0.0
var _celebration_frame: float = 0.0
var _time: float = 0.0
var _fragments: Array = []
var _rising: Array = []
## Gelombang ledakan: [frame_mulai, radius_maks, warna] (paritas :1659-1670)
var _waves: Array = []
var _owns_pause: bool = false

var _layer: CanvasLayer = null
var _flash: ColorRect = null
var _overlay: ColorRect = null
var _tint: ColorRect = null
var _celebration: Control = null
var _label_defeated: Label = null
var _label_name: Label = null
var _label_title: Label = null
## Posisi Y dasar label perayaan (sudah dipusatkan saat dibangun) — animasi
## bounce hanya menambah offset, tidak menulis ulang posisi absolut.
var _base_y_defeated: float = 0.0
var _base_y_name: float = 0.0
var _base_y_title: float = 0.0
var _label_reward: Label = null
var _label_unlock: Label = null
var _label_hint: Label = null
var _sparkles: Control = null
var _coin: Control = null


func setup(info: Dictionary) -> void:
	boss_class = str(info.get("boss_class", "mini"))
	boss_name = str(info.get("name", "Boss"))
	boss_title = str(info.get("title", ""))
	boss_color = _col(info.get("color"), Color(0.6, 0.4, 0.85))
	boss_color_dark = _col(info.get("color_dark"), boss_color.darkened(0.4))
	entrance_color = _col(info.get("entrance_color"), boss_color)
	gold_reward = int(info.get("gold_reward", 0))
	boss_radius = float(info.get("radius", 22.0))
	show_celebration = boss_class == "true"
	_duration = DEATH_DURATION_TRUE if show_celebration else DEATH_DURATION_MINI
	if show_celebration:
		_waves = [
			[0.0, 60.0, entrance_color],
			[15.0, 120.0, Color(1.0, 0.784, 0.392)],
			[30.0, 200.0, Color(1.0, 1.0, 0.784)],
		]
	else:
		_waves = [
			[0.0, 50.0, entrance_color],
			[15.0, 100.0, Color(1.0, 0.863, 0.588)],
		]
	_init_fragments()
	_init_rising()


static func _col(v, fallback: Color) -> Color:
	if v is Color:
		return v
	if typeof(v) == TYPE_STRING and String(v).begins_with("#"):
		return Color(String(v))
	return fallback


func _ready():
	add_to_group("cinematic")
	add_to_group("boss_death_fx")
	# Animasi + overlay harus jalan walau SceneTree di-pause (fase kematian
	# memang membekukan gameplay, paritas _core.py:1995-1997).
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_physics_process(false)
	_build_overlay()
	# FASE KEMATIAN = pause gameplay (di pygame Game.update return selama
	# is_death_active()). Main/AI/unit sudah PAUSABLE; gold & wave ditahan
	# GameManager.is_paused.
	get_tree().paused = true
	GameManager.set_paused(true)
	_owns_pause = true


func _build_overlay() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 40
	_layer.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(_layer)

	_flash = ColorRect.new()
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.color = Color(1, 1, 1, 0)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(_flash)

	_overlay = ColorRect.new()
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.color = Color(0, 0, 0, 0)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.visible = false
	_layer.add_child(_overlay)

	_tint = ColorRect.new()
	_tint.set_anchors_preset(Control.PRESET_FULL_RECT)
	_tint.color = Color(80.0 / 255.0, 60.0 / 255.0, 20.0 / 255.0, 0)
	_tint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tint.visible = false
	_layer.add_child(_tint)

	_sparkles = Control.new()
	_sparkles.set_anchors_preset(Control.PRESET_FULL_RECT)
	_sparkles.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sparkles.draw.connect(_draw_sparkles)
	_sparkles.visible = false
	_layer.add_child(_sparkles)

	_celebration = Control.new()
	_celebration.set_anchors_preset(Control.PRESET_FULL_RECT)
	_celebration.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_celebration.visible = false
	_layer.add_child(_celebration)
	_build_celebration_labels()


func _build_celebration_labels() -> void:
	var font_title: Font = load("res://assets/fonts/Cinzel.ttf")
	var font_semibold: Font = load("res://assets/fonts/Barlow-SemiBold.ttf")
	var font_medium: Font = load("res://assets/fonts/Barlow-Medium.ttf")
	var cx := 640.0
	var cy := 310.0 # screen_h/2 - 50 (paritas :2008-2009)

	_label_defeated = _mk_label("BOSS DEFEATED!", font_title, 66,
		Color(1.0, 0.863, 0.392), Vector2(cx, cy - 40), true)
	_label_name = _mk_label(boss_name, font_title, 46, entrance_color,
		Vector2(cx, cy + 30), true)
	_label_title = _mk_label("\"%s\"" % boss_title, font_semibold, 32,
		Color(0.784, 0.784, 0.863), Vector2(cx, cy + 75), true)
	# Koin kecil di kiri teks reward digambar _coin
	_label_reward = _mk_label("+ %d GOLD" % gold_reward, font_semibold, 32,
		Color(1.0, 0.863, 0.392), Vector2(cx, cy + 130), false)
	_label_unlock = _mk_label(_letter("HERO UNLOCKED!"), font_medium, 24,
		Color(1.0, 0.706, 0.863), Vector2(cx, cy + 170), false)
	_label_hint = _mk_label("[SPACE] to continue", font_medium, 24,
		Color(0.784, 0.784, 0.784), Vector2(cx, 680), false)
	_base_y_defeated = _label_defeated.position.y
	_base_y_name = _label_name.position.y
	_base_y_title = _label_title.position.y

	_coin = Control.new()
	_coin.size = Vector2(20, 20)
	_coin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_coin.draw.connect(_draw_coin)
	_celebration.add_child(_coin)
	# kiri teks reward (paritas reward_rect.left - 30 :2096)
	var rw := _label_reward.get_combined_minimum_size()
	_coin.position = Vector2(cx - rw.x / 2.0 - 30.0 - 10.0, cy + 130.0 - 10.0)


func _mk_label(text: String, font: Font, size: int, color: Color,
		center: Vector2, heavy_shadow: bool) -> Label:
	var l := Label.new()
	l.text = text
	if font != null:
		l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if heavy_shadow:
		l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.31))
		l.add_theme_constant_override("shadow_offset_x", 4)
		l.add_theme_constant_override("shadow_offset_y", 4)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_celebration.add_child(l)
	var sz := l.get_combined_minimum_size()
	l.position = center - sz / 2.0
	return l


static func _letter(text: String) -> String:
	var out := PackedStringArray()
	for ch in text:
		out.append(ch)
	return " ".join(out)


func _init_fragments() -> void:
	# Paritas _init_fragments (:1702-1726) — seed bebas (pygame random.uniform)
	var n := 25 if boss_class == "true" else 15
	for _i in range(n):
		var ang := randf() * TAU
		var spd := randf_range(2.0, 6.0)
		_fragments.append({
			"x": randf_range(-15.0, 15.0), "y": randf_range(-15.0, 15.0),
			"vx": cos(ang) * spd, "vy": sin(ang) * spd - 2.0,
			"size": float(randi_range(3, 8)),
			"color": [boss_color, boss_color_dark, entrance_color][randi() % 3],
			"rotation": randf() * TAU,
			"rot_speed": randf_range(-0.3, 0.3),
			"life": 60.0, "max_life": 60.0,
		})


func _init_rising() -> void:
	# Paritas _init_rising_particles (:1728-1742)
	var n := 30 if boss_class == "true" else 15
	for _i in range(n):
		_rising.append({
			"x": randf_range(-30.0, 30.0), "y": randf_range(-10.0, 10.0),
			"vx": randf_range(-0.5, 0.5), "vy": randf_range(-3.0, -1.0),
			"size": float(randi_range(2, 5)),
			"life": float(randi_range(60, 100)), "max_life": 100.0,
			"phase": randf() * TAU,
		})


func _process(delta: float) -> void:
	if not active:
		return
	_time += delta
	if death_active:
		_frame += delta * 60.0
		_step_particles(delta * 60.0)
		_update_death_visuals()
		if _frame >= _duration:
			death_active = false
			if _owns_pause:
				# Perayaan TIDAK pause gameplay (paritas _core.py:2000-2001)
				get_tree().paused = false
				GameManager.set_paused(false)
				_owns_pause = false
			if show_celebration:
				celebration_active = true
				_celebration_frame = 0.0
				_celebration.visible = true
				_overlay.visible = true
				_tint.visible = true
				_sparkles.visible = true
				AudioManager.play_sfx("victory", 1.0, true)
			else:
				finish()
		queue_redraw()
	elif celebration_active:
		_celebration_frame += delta * 60.0
		_update_celebration_visuals()
		if _celebration_frame >= CELEBRATION_FRAMES:
			finish()


## Fisika pecahan & partikel per-frame (paritas update() :1768-1782 yang
## dijalankan sekali per frame pygame). steps = frame 60fps yang berlalu.
func _step_particles(steps: float) -> void:
	for f in _fragments:
		if f["life"] <= 0.0:
			continue
		f["x"] += f["vx"] * steps
		f["y"] += f["vy"] * steps
		f["vy"] += 0.2 * steps
		f["rotation"] += f["rot_speed"] * steps
		f["life"] -= steps
	for p in _rising:
		if p["life"] <= 0.0:
			continue
		p["x"] += p["vx"] * steps
		p["y"] += p["vy"] * steps
		p["phase"] += 0.1 * steps
		p["x"] += sin(p["phase"]) * 0.5 * steps
		p["life"] -= steps


func _update_death_visuals() -> void:
	# White flash hanya 15 frame pertama (paritas :1834-1838)
	if _frame < FLASH_FRAMES:
		_flash.color.a = 200.0 / 255.0 * (1.0 - _frame / FLASH_FRAMES)
	else:
		_flash.color.a = 0.0


func _update_celebration_visuals() -> void:
	var p := _celebration_frame / CELEBRATION_FRAMES
	# Overlay gelap: naik 15% awal, turun 15% akhir (paritas :1995-2002)
	var ov := 180.0
	if p < 0.15:
		ov = 180.0 * (p / 0.15)
	elif p > 0.85:
		ov = 180.0 * (1.0 - (p - 0.85) / 0.15)
	_overlay.color.a = ov / 255.0
	# Tint emas hanya sebelum 85% (paritas :2005-2009)
	_tint.color.a = (40.0 / 255.0) if p < 0.85 else 0.0
	# Bounce teks: ease-out cubic 30% awal, fade 15% akhir (paritas :2014-2024)
	var text_alpha := 1.0
	var text_off := 0.0
	if p < 0.3:
		var bp := p / 0.3
		var eased := 1.0 - pow(1.0 - bp, 3.0)
		text_alpha = eased
		text_off = (1.0 - eased) * 60.0
	elif p > 0.85:
		text_alpha = 1.0 - (p - 0.85) / 0.15
	_label_defeated.modulate.a = text_alpha
	_label_name.modulate.a = text_alpha
	_label_title.modulate.a = text_alpha
	_label_defeated.position.y = _base_y_defeated + text_off
	_label_name.position.y = _base_y_name + text_off
	_label_title.position.y = _base_y_title + text_off
	# Reward + unlock baru muncul setelah 30% (paritas :2083-2085)
	if p > 0.3:
		var ra := minf(1.0, (p - 0.3) / 0.3)
		_label_reward.modulate.a = ra
		_label_unlock.modulate.a = ra
		_coin.modulate.a = ra
		_coin.visible = true
	else:
		_label_reward.modulate.a = 0.0
		_label_unlock.modulate.a = 0.0
		_coin.visible = false
	_sparkles.queue_redraw()
	# Hint skip berdenyut setelah 50% (paritas :2127-2135)
	if p > 0.5:
		var pulse := sin(_time * 5.0) * 0.3 + 0.7
		_label_hint.modulate.a = 180.0 / 255.0 * pulse
		_label_hint.visible = true
	else:
		_label_hint.visible = false


# ══════════════════════════════════════════════════════════
#  GAMBAR DUNIA (cincin ledakan, dissolve, pecahan, roh) — koordinat
#  lokal Node2D ini (global_position = posisi boss saat mati).
# ══════════════════════════════════════════════════════════

func _draw() -> void:
	if not death_active:
		return
	var progress := _frame / _duration
	# ── Gelombang cincin ledakan (paritas :1841-1878) ──
	for w in _waves:
		var wave_elapsed := _frame - float(w[0])
		if wave_elapsed < 0.0 or wave_elapsed >= WAVE_FRAMES:
			continue
		var wp := wave_elapsed / WAVE_FRAMES
		var radius := float(w[1]) * wp
		var alpha := 220.0 * (1.0 - wp) / 255.0
		if alpha <= 0.0 or radius <= 0.0:
			continue
		var wc: Color = w[2]
		var r := radius
		while r > maxf(0.0, radius - 20.0):
			var a := alpha * (r / radius)
			draw_arc(Vector2.ZERO, r, 0.0, TAU, 40,
				Color(wc.r, wc.g, wc.b, a), 3.0)
			r -= 3.0
		# Inti padat memudar
		draw_circle(Vector2.ZERO, maxf(1.0, radius - 15.0),
			Color(wc.r, wc.g, wc.b, alpha / 2.0))
	# ── Dissolve badan (paritas :1881-1905) ──
	if progress < 0.5:
		var da := 1.0 - progress * 2.0
		var dsz := boss_radius * (1.0 - progress * 0.5)
		draw_circle(Vector2.ZERO, dsz, Color(boss_color.r, boss_color.g,
			boss_color.b, da))
		draw_circle(Vector2.ZERO, dsz / 2.0, Color(entrance_color.r,
			entrance_color.g, entrance_color.b, da / 2.0))
	# ── Pecahan shatter (paritas :1908-1946) ──
	# Semua angka dari Dictionary = Variant -> konversi eksplisit; proyek ini
	# menganggap "infer dari Variant" sebagai error (lihat README bagian
	# "Cannot infer the type").
	for f in _fragments:
		var life: float = f["life"]
		if life <= 0.0:
			continue
		var lr: float = life / float(f["max_life"])
		var a: float = lr
		if a * 255.0 < 10.0:
			continue
		var sz: float = f["size"]
		var fx: float = f["x"]
		var fy: float = f["y"]
		var cos_r := cos(float(f["rotation"]))
		var sin_r := sin(float(f["rotation"]))
		var pts := PackedVector2Array()
		for corner in [Vector2(-sz, -sz), Vector2(sz, -sz), Vector2(sz, sz), Vector2(-sz, sz)]:
			pts.append(Vector2(fx + corner.x * cos_r - corner.y * sin_r,
				fy + corner.x * sin_r + corner.y * cos_r))
		var fc: Color = f["color"]
		draw_colored_polygon(pts, Color(fc.r, fc.g, fc.b, a))
		# Tepi terang warna entrance (pygame: polygon outline 1px)
		draw_polyline(pts + PackedVector2Array([pts[0]]),
			Color(entrance_color.r, entrance_color.g, entrance_color.b, a), 1.0)
	# ── Partikel roh naik (paritas :1949-1979) ──
	for p in _rising:
		var life: float = p["life"]
		if life <= 0.0:
			continue
		var lr: float = life / float(p["max_life"])
		var a: float = 200.0 * lr / 255.0
		if a * 255.0 < 10.0:
			continue
		var sz: float = p["size"]
		var pos := Vector2(float(p["x"]), float(p["y"]))
		var gr := sz + 2.0
		while gr > 0.0:
			var ga: float = a * (1.0 - gr / (sz + 2.0))
			if ga > 0.0:
				draw_circle(pos, gr, Color(entrance_color.r, entrance_color.g,
					entrance_color.b, ga))
			gr -= 1.0
		draw_circle(pos, 1.0, Color(1, 1, 1, a))


func _draw_sparkles() -> void:
	# 6 bintang berputar mengelilingi teks (paritas :2112-2125)
	var p := _celebration_frame / CELEBRATION_FRAMES
	if p <= 0.4:
		return
	var cx := 640.0
	var cy := 310.0
	for i in range(6):
		var ang := _time * 1.0 + float(i) * PI / 3.0
		var sx := cx + cos(ang) * 220.0
		var sy := cy + sin(ang) * 60.0
		var pulse := sin(_time * 5.0 + float(i)) * 0.3 + 0.7
		_sparkles.draw_circle(Vector2(sx, sy), 4.0 * pulse, Color(1.0, 0.863, 0.392))
		_sparkles.draw_circle(Vector2(sx, sy), 2.0 * pulse, Color(1, 1, 1))


func _draw_coin() -> void:
	# Koin reward perayaan (paritas :2094-2103)
	var c := Vector2(10, 10)
	_coin.draw_circle(c, 10.0, Color(1.0, 0.784, 0.196))
	_coin.draw_arc(c, 10.0, 0.0, TAU, 24, Color(0.784, 0.588, 0.118), 2.0)


# ══════════════════════════════════════════════════════════
#  SKIP / SELESAI
# ══════════════════════════════════════════════════════════

## Hanya fase perayaan yang bisa di-skip (paritas handle_skip :1812-1818:
## "Skip celebration only (death animation tetap play)").
func cinematic_active() -> bool:
	return celebration_active


func skip_key(event: InputEventKey) -> bool:
	if not celebration_active:
		return false
	if event.keycode == KEY_SPACE or event.keycode == KEY_ESCAPE:
		finish()
		return true
	return false


func skip_click() -> bool:
	if not celebration_active:
		return false
	finish()
	return true


func finish() -> void:
	if not active:
		return
	active = false
	death_active = false
	celebration_active = false
	if _owns_pause:
		get_tree().paused = false
		GameManager.set_paused(false)
		_owns_pause = false
	queue_free()
