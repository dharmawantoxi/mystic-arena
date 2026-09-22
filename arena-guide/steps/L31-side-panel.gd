# L31 — panel kanan bata ala pygame + STATUS/HERO/SKILL/TACTICAL — SNIPPET
# ============================================================
# Ringkasan (ikuti urutan A → E):
#   A) project.godot (atau Project Settings): window 1624×720
#   B) Main.tscn Camera2D limit_right = 1624 (jika ada)
#   C) Main.gd: const PANEL + gambar latar bata + blokir klik panel
#   D) Buat scripts/SidePanel.gd (file baru) — tempel utuh di bawah
#   E) Main.gd _ready: spawn SidePanel; Hud.gd: pindah GOLD/WAVE ke panel
#
# Geometri pygame (mobile/sidepanel.py + platform_utils):
#   arena 1280×720 di kiri; panel x=1280..1624 (lebar 344) di kanan.
#   Latar = bata stone sama border wall map.
#   Zona: pause | STATUS | HEROES | SKILLS | TACTICAL COMMANDS
#
# Catatan: perintah tactical di L31 = STUB visual + print().
# Logika penuh (gather/protect/attack) = langkah terpisah nanti.

# ═══════════════════════════════════════════
# A — Project Settings → Display → Window
#     Viewport Width = 1624
#     Viewport Height = 720
#     (atau edit project.godot: window/size/viewport_width=1624)
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
# C — tambah di Main.gd (const + member + potongan)
# ═══════════════════════════════════════════
const PANEL_X := 1280.0
const PANEL_W := 344.0
const VIEW_W := 1624.0

var side_panel = null   # SidePanel

# di _ready(), SETELAH hud.setup(self):
#	$Camera2D.limit_right = int(VIEW_W)
#	side_panel = load("res://scripts/SidePanel.gd").new()
#	add_child(side_panel)
#	side_panel.setup(self)

# di _draw(), SEBELUM overlay match_over (setelah fog):
#	if side_panel != null:
#		side_panel.draw_on(self)

# di _on_left_click / _unhandled_input mouse:
#	if point.x >= PANEL_X:
#		if side_panel != null:
#			side_panel.handle_click(point)
#		return

# ═══════════════════════════════════════════
# D — FILE BARU: res://scripts/SidePanel.gd
# ═══════════════════════════════════════════
extends Node2D
class_name SidePanelManual
## Panel kanan bata (paritas mobile/sidepanel.py) untuk port manual.

const PX := 1280.0
const PW := 344.0
const PH := 720.0
const PAD := 14.0

const FG := Color8(228, 230, 242)
const DIM := Color8(146, 150, 172)
const EMAS := Color8(255, 205, 90)
const OK := Color8(120, 235, 140)
const BAHAYA := Color8(255, 110, 110)
const BIRU := Color8(120, 200, 255)
const UNGU := Color8(190, 165, 255)

var _main = null
var _btns: Array = []          # [{action, rect:Rect2, label, color, enabled}]
var _feedback := ""
var _feedback_t := 0.0

func setup(main_ref) -> void:
	_main = main_ref
	z_index = 50
	_rebuild_buttons()

func _rebuild_buttons() -> void:
	_btns.clear()
	# posisi y dihitung di draw; simpan action saja dulu
	var defs: Array = [
		["gather", "GATHER [G]", BIRU],
		["protect_tower", "PROTECT TOWER [T]", OK],
		["protect_castle", "PROTECT CASTLE [C]", EMAS],
		["attack_boss", "ATTACK BOSS [B]", BAHAYA],
		["attack_dd", "ATTACK DMG DEALER [D]", UNGU],
	]
	for d in defs:
		_btns.append({"action": d[0], "label": d[1], "color": d[2], "rect": Rect2(), "enabled": true})

func _process(delta: float) -> void:
	if _feedback_t > 0.0:
		_feedback_t = maxf(0.0, _feedback_t - delta)

func draw_on(host: CanvasItem) -> void:
	# Dipanggil dari Main._draw() supaya 1 pass canvas.
	_draw_brick_bg(host)
	var y := 14.0
	y = _draw_pause(host, y)
	y = _draw_status(host, y)
	y = _draw_heroes(host, y)
	y = _draw_skills(host, y)
	y = _draw_tactical(host, y)
	if _feedback_t > 0.0 and _feedback != "":
		var font: Font = ThemeDB.fallback_font
		host.draw_string(font, Vector2(PX + PAD, PH - 18.0), _feedback,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 14, EMAS)

func _draw_brick_bg(host: CanvasItem) -> void:
	# latar gelap
	host.draw_rect(Rect2(PX, 0.0, PW, PH), Color8(18, 16, 26))
	# bata 16px (paritas border wall / path stone)
	var ps1 := Color8(58, 52, 45)
	var ps2 := Color8(85, 76, 65)
	var ps3 := Color8(115, 105, 90)
	var ps4 := Color8(145, 130, 108)
	var ol := Color8(12, 8, 12)
	for ty in range(0, 720, 16):
		for tx in range(0, 344, 16):
			var gx := PX + float(tx)
			var gy := float(ty)
			var v := (tx * 3 + ty * 7) % 100
			host.draw_rect(Rect2(gx, gy, 16, 16), ol)
			host.draw_rect(Rect2(gx + 1, gy + 1, 14, 14), ps1)
			if v < 40:
				host.draw_rect(Rect2(gx + 2, gy + 2, 12, 12), ps2)
				host.draw_rect(Rect2(gx + 3, gy + 3, 10, 10), ps3)
				host.draw_rect(Rect2(gx + 3, gy + 3, 10, 2), ps4)
			elif v < 70:
				host.draw_rect(Rect2(gx + 2, gy + 2, 12, 6), ps2)
				host.draw_rect(Rect2(gx + 2, gy + 9, 12, 5), ps2)
			else:
				host.draw_rect(Rect2(gx + 2, gy + 2, 5, 5), ps2)
				host.draw_rect(Rect2(gx + 9, gy + 2, 5, 5), ps2)
				host.draw_rect(Rect2(gx + 2, gy + 9, 5, 5), ps2)
				host.draw_rect(Rect2(gx + 9, gy + 9, 5, 5), ps2)
	# bingkai kiri panel (pemisah arena)
	host.draw_rect(Rect2(PX, 0.0, 4.0, PH), Color8(12, 8, 12))
	host.draw_rect(Rect2(PX + 1.0, 0.0, 2.0, PH), Color8(145, 130, 108))

func _kotak(host: CanvasItem, x: float, y: float, w: float, h: float, judul: String) -> void:
	host.draw_rect(Rect2(x, y, w, h), Color8(22, 19, 32))
	host.draw_rect(Rect2(x, y, w, h), Color8(64, 56, 86), false, 1.0)
	var font: Font = ThemeDB.fallback_font
	host.draw_string(font, Vector2(x + 8.0, y + 16.0), judul,
		HORIZONTAL_ALIGNMENT_LEFT, -1, 13, DIM)

func _draw_pause(host: CanvasItem, y: float) -> float:
	var r := Rect2(PX + PAD, y, 58.0, 58.0)
	host.draw_rect(r, Color8(30, 27, 44))
	host.draw_rect(r, EMAS, false, 2.0)
	# ikon pause dua batang
	host.draw_rect(Rect2(r.position.x + 18.0, r.position.y + 16.0, 7.0, 26.0), EMAS)
	host.draw_rect(Rect2(r.position.x + 33.0, r.position.y + 16.0, 7.0, 26.0), EMAS)
	# simpan sebagai tombol khusus
	_pause_rect = r
	return y + 70.0

var _pause_rect := Rect2()

func _draw_status(host: CanvasItem, y: float) -> float:
	var x := PX + PAD
	var w := PW - PAD * 2.0
	var h := 96.0
	_kotak(host, x, y, w, h, "STATUS")
	var font: Font = ThemeDB.fallback_font
	var gold_i := 0
	var wave_i := 0
	var lvl_i := 1
	if _main != null:
		gold_i = int(_main.gold)
		wave_i = int(_main.wave_count)
		if _main.level_data is Dictionary:
			lvl_i = int(_main.level_data.get("level", 1))
	host.draw_string(font, Vector2(x + 10.0, y + 44.0), str(gold_i),
		HORIZONTAL_ALIGNMENT_LEFT, -1, 22, EMAS)
	host.draw_string(font, Vector2(x + 10.0, y + 62.0), "GOLD",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 13, DIM)
	host.draw_string(font, Vector2(x + 10.0, y + 82.0), "NORMAL",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 12, OK)
	var right := x + w - 10.0
	var lv_s := "LV %d" % lvl_i
	var lw: float = font.get_string_size(lv_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 16).x
	host.draw_string(font, Vector2(right - lw, y + 40.0), lv_s,
		HORIZONTAL_ALIGNMENT_LEFT, -1, 16, FG)
	var wv_s := "Wave %d" % wave_i if wave_i > 0 else "Wave —"
	var ww: float = font.get_string_size(wv_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x
	host.draw_string(font, Vector2(right - ww, y + 62.0), wv_s,
		HORIZONTAL_ALIGNMENT_LEFT, -1, 13, DIM)
	return y + h + 10.0

func _draw_heroes(host: CanvasItem, y: float) -> float:
	var x := PX + PAD
	var w := PW - PAD * 2.0
	var h := 70.0
	_kotak(host, x, y, w, h, "HEROES")
	var font: Font = ThemeDB.fallback_font
	if _main == null or _main.hero == null:
		host.draw_string(font, Vector2(x + 10.0, y + 40.0), "No heroes",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 14, DIM)
		return y + h + 10.0
	var hro = _main.hero
	var nama := str(hro.hero_name)
	host.draw_string(font, Vector2(x + 10.0, y + 34.0), nama,
		HORIZONTAL_ALIGNMENT_LEFT, -1, 15, FG)
	# HP bar
	var bx := x + 10.0
	var by := y + 44.0
	var bw := w - 20.0
	host.draw_rect(Rect2(bx, by, bw, 8.0), Color8(48, 14, 14))
	var ratio := 0.0
	if float(hro.max_hp) > 0.0:
		ratio = clampf(float(hro.hp) / float(hro.max_hp), 0.0, 1.0)
	var hc := OK if ratio > 0.5 else (EMAS if ratio > 0.25 else BAHAYA)
	host.draw_rect(Rect2(bx, by, bw * ratio, 8.0), hc)
	host.draw_rect(Rect2(bx, by, bw, 8.0), Color8(90, 84, 110), false, 1.0)
	var hp_s := "%d/%d" % [maxi(0, int(hro.hp)), int(hro.max_hp)]
	host.draw_string(font, Vector2(bx, by + 22.0), hp_s,
		HORIZONTAL_ALIGNMENT_LEFT, -1, 12, DIM)
	return y + h + 10.0

func _draw_skills(host: CanvasItem, y: float) -> float:
	var x := PX + PAD
	var w := PW - PAD * 2.0
	var h := 100.0
	_kotak(host, x, y, w, h, "SKILLS")
	var font: Font = ThemeDB.fallback_font
	if _main == null or _main.hero == null:
		return y + h + 10.0
	var hro = _main.hero
	var keys: Array = ["Q", "W", "E", "R"]
	var shorts: Array = ["Tebas", "Sembuh", "Rantai", "Amuk"]
	if "skill_short" in hro:
		shorts = hro.skill_short
	var gap := 6.0
	var bw := (w - 20.0 - gap * 3.0) / 4.0
	var bh := 52.0
	var bx := x + 10.0
	var by := y + 28.0
	for i in 4:
		var r := Rect2(bx + float(i) * (bw + gap), by, bw, bh)
		host.draw_rect(r, Color8(30, 27, 44))
		var cd := 0.0
		if "skill_cds" in hro:
			cd = float(hro.skill_cds[i])
		var col := UNGU if cd <= 0.0 else DIM
		host.draw_rect(r, col, false, 2.0)
		var label := "%s\n%s" % [str(keys[i]), str(shorts[i])]
		if cd > 0.0:
			label = "%s\n%.1f" % [str(keys[i]), cd]
		else:
			label = "%s\nSIAP" % str(keys[i])
		# dua baris
		host.draw_string(font, Vector2(r.position.x + 6.0, r.position.y + 18.0),
			str(keys[i]), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, col)
		var sub := ("%.1f" % cd) if cd > 0.0 else "SIAP"
		if cd <= 0.0:
			sub = str(shorts[i])
		host.draw_string(font, Vector2(r.position.x + 4.0, r.position.y + 38.0),
			sub.substr(0, 7), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, FG)
		# klik area = cast
		_skill_rects[i] = r
	return y + h + 10.0

var _skill_rects: Array = [Rect2(), Rect2(), Rect2(), Rect2()]

func _draw_tactical(host: CanvasItem, y: float) -> float:
	var x := PX + PAD
	var w := PW - PAD * 2.0
	var btn_h := 32.0
	var gap := 6.0
	var n := _btns.size()
	var h := 26.0 + float(n) * (btn_h + gap) - gap
	if y + h > PH - 12.0:
		h = maxf(40.0, PH - 12.0 - y)
	_kotak(host, x, y, w, h, "TACTICAL COMMANDS")
	var font: Font = ThemeDB.fallback_font
	var by := y + 24.0
	for i in n:
		var b: Dictionary = _btns[i]
		var r := Rect2(x + 6.0, by, w - 12.0, btn_h)
		b["rect"] = r
		var col: Color = b["color"]
		var bg := Color(col.r * 0.25, col.g * 0.25, col.b * 0.25, 1.0)
		host.draw_rect(r, bg)
		host.draw_rect(r, col, false, 2.0)
		var lbl: String = str(b["label"])
		var tw: float = font.get_string_size(lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x
		host.draw_string(font, Vector2(r.position.x + (r.size.x - tw) * 0.5, r.position.y + 22.0),
			lbl, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, col)
		by += btn_h + gap
		_btns[i] = b
	return y + h + 10.0

func handle_click(point: Vector2) -> void:
	if _pause_rect.has_point(point):
		if _main != null:
			_main.toggle_pause()
		return
	for i in _skill_rects.size():
		var r: Rect2 = _skill_rects[i]
		if r.has_point(point):
			if _main != null:
				_main.cast_hero_skill(i)
			return
	for b in _btns:
		var r2: Rect2 = b["rect"]
		if r2.has_point(point):
			_issue_tactical(str(b["action"]))
			return

func _issue_tactical(action: String) -> void:
	# STUB: visual feedback saja. Logika penuh = langkah berikut.
	_feedback = "CMD: " + action.to_upper()
	_feedback_t = 2.0
	print("[SidePanel] tactical stub: %s (logika penuh belakangan)" % action)
	if _main != null and _main.hero != null and action == "gather":
		# mini-aksi: kumpulkan hero ke titik dekat nexus biru
		_main.hero.move_to(Vector2(250, 580))

# ═══════════════════════════════════════════
# E — Hud.gd: sembunyikan GOLD/WAVE/hint/skill lama (pindah ke panel)
#     di setup(), setelah label dibuat:
# ═══════════════════════════════════════════
#	_gold_l.visible = false
#	_wave_l.visible = false
#	_hint_l.visible = false
#	for b in _btns:
#		b.visible = false
#	# hero HP boleh tetap kiri-bawah ATAU ikut disembunyikan:
#	_hero_l.visible = false
