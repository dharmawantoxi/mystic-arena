# HeroShopCard.gd — kartu HERO di toko in-match, DIGAMBAR seperti pygame.
#
# Port `HeroShop._draw_compact_card` (ui_components/_bundle.py:1958-2130)
# 1:1 pada geometri dan warnanya: kartu 340x120, potret 60 px berbingkai di
# kiri, info (nama 22 / judul 16 / chip ROLE 14 / baris HP·DMG·RNG) di tengah,
# dan pill 90x30 di kanan yang isinya HARGA — bukan baris `Button` berlabel
# panjang seperti sebelumnya. Sama seperti ItemForgeCard, kartu ini hanya
# mengubah CARA menampilkan; kontrak kontrol (ui_key, ui_data, tooltip,
# callback beli) tetap ada pada Button anak yang transparan.
#
# Angka literal `_draw_compact_card`:
#   kartu    340x120, radius 8, bg (25,40,30) bila dimiliki else (25,30,50)
#   shadow   rect alpha 100 di belakang kartu (satu ritme dengan PygamePanel)
#   hover    HANYA kalau belum dimiliki dan roster belum penuh: glow
#            warna hero alpha 60 seluas kartu +12, border jadi putih, lebar 3
#   border   (100,220,100) owned / (255,255,255) hover / warna hero, lebar 2
#   potret   kotak 60 px di (10, tengah); bg (15,20,30) radius 4 + border
#            warna hero 1 px; isinya HeroPortraits.draw(..., owned=False) ->
#            di Godot: frame render unit lewat UnitPortrait.portrait_texture
#   info_x   10 + 60 + 12 = 82; nama di cy+10, judul +24, chip role +44
#   nama     body_bold 22 putih, lebar `cw - 110 - (info_x - cx)` + elipsis
#   judul    body_medium 16 (180,190,210)
#   role     body_bold 14 uppercase warna hero, pill hitam radius 8 border
#            warna hero 1 px,lebar = teks + 14, tinggi 18
#   stats    3 sel @56 px mulai cy+78: label 10 px berwarna + angka
#            body_bold 18 putih (HP merah, DMG kuning, RNG biru)
#   tombol   90x30 di kanan (cw - 90 - 12), tengah vertikal:
#              dimiliki  -> bg (40,80,40)   border (100,180,100) "ACTIVE"
#                           teks (150,255,150)
#              roster    -> bg (60,40,40)   border (180,80,80)   "MAX"
#                           teks (255,150,150)
#              tak cukup -> bg (50,50,50)   border (130,130,130) "<cost>G"
#                           teks (200,150,150)
#              siap      -> bg (35,140,45) / hover (40,170,50), border
#                           (100,220,100) / (130,255,130), "<cost>G" putih
#            font body_semibold 24, radius 5, border 2 px
#
# Label "ACTIVE"/"MAX"/harga sengaja TIDAK lewat tabel teks: persis seperti
# pygame, ketiganya literal Inggris di kedua bahasa (badge, bukan kalimat).
# Nama/judul/role/hp/damage/range datang dari heroes.json (sudah Inggris).
#
# Twin Pygame: ui_components/_bundle.py (HeroShop._draw_compact_card).
extends Control
class_name HeroShopCard

const CARD_W := 340.0
const CARD_H := 120.0
const RADIUS := 8.0
const PORTRAIT := 60.0
const PORTRAIT_X := 10.0
const INFO_X := 82.0
const NAME_Y := 10.0
const TITLE_DY := 24.0
const ROLE_DY := 44.0
const ROLE_H := 18.0
const ROLE_PAD_X := 7.0
const STATS_DY := 68.0
const STATS_STEP := 56.0
const BTN_W := 90.0
const BTN_H := 30.0
const BTN_RIGHT := 12.0
const NAME_RESERVE := 110.0
## Ukuran art di dalam bingkai 60 px (bingkai 1 px + margin 4 px dalam).
const PORTRAIT_ART_W := 50
const PORTRAIT_ART_H := 54

const COL_OWNED_BG := Color(25.0 / 255.0, 40.0 / 255.0, 30.0 / 255.0)
const COL_BG := Color(25.0 / 255.0, 30.0 / 255.0, 50.0 / 255.0)
const COL_OWNED_BORDER := Color(100.0 / 255.0, 220.0 / 255.0, 100.0 / 255.0)
const COL_PORTRAIT_BG := Color(15.0 / 255.0, 20.0 / 255.0, 30.0 / 255.0)
const COL_TITLE := Color(180.0 / 255.0, 190.0 / 255.0, 210.0 / 255.0)
const COL_STAT_HP := Color(1.0, 100.0 / 255.0, 100.0 / 255.0)
const COL_STAT_DMG := Color(1.0, 200.0 / 255.0, 100.0 / 255.0)
const COL_STAT_RNG := Color(100.0 / 255.0, 200.0 / 255.0, 1.0)
const COL_BTN_OWNED_BG := Color(40.0 / 255.0, 80.0 / 255.0, 40.0 / 255.0)
const COL_BTN_OWNED_BD := Color(100.0 / 255.0, 180.0 / 255.0, 100.0 / 255.0)
const COL_BTN_OWNED_TX := Color(150.0 / 255.0, 255.0 / 255.0, 150.0 / 255.0)
const COL_BTN_MAX_BG := Color(60.0 / 255.0, 40.0 / 255.0, 40.0 / 255.0)
const COL_BTN_MAX_BD := Color(180.0 / 255.0, 80.0 / 255.0, 80.0 / 255.0)
const COL_BTN_MAX_TX := Color(1.0, 150.0 / 255.0, 150.0 / 255.0)
const COL_BTN_POOR_BG := Color(50.0 / 255.0, 50.0 / 255.0, 50.0 / 255.0)
const COL_BTN_POOR_BD := Color(130.0 / 255.0, 130.0 / 255.0, 130.0 / 255.0)
const COL_BTN_POOR_TX := Color(200.0 / 255.0, 150.0 / 255.0, 150.0 / 255.0)
const COL_BTN_OK_BG := Color(35.0 / 255.0, 140.0 / 255.0, 45.0 / 255.0)
const COL_BTN_OK_HOVER := Color(40.0 / 255.0, 170.0 / 255.0, 50.0 / 255.0)
const COL_BTN_OK_BD := Color(100.0 / 255.0, 220.0 / 255.0, 100.0 / 255.0)
const COL_BTN_OK_BD_HOVER := Color(130.0 / 255.0, 255.0 / 255.0, 130.0 / 255.0)

## "BUY" | "ACTIVE" | "MAX" | "POOR" | "LOCKED" — percabangan
## _draw_compact_card pygame, dihitung ShopPanel dari state permainan.
var state: String = "BUY"
## Alasan disabled untuk `ui_data.blocked` ("", OWNED, FULL, POOR, LOCKED) —
## kosakata baris toko pygame, BUKAN nama state kartu (lihat configure()).
var reason: String = ""
var hero_type: String = ""
var cost: int = 0
var stats: Dictionary = {}
## Button transparan pemegang ui_key/ui_data + klik (dibangun `configure()`).
var action_button: Button = null
## Potret kartu = `UnitPortrait.portrait_texture` (frame render unit aslinya,
## 50x54 di dalam bingkai 60 px). Null kalau strip bake unitnya belum ada —
## kartunya tetap tampil dengan bingkai kosong (pygame mengganti unit tanpa
## renderer dengan `_draw_generic`; di Godot fallback itu hidup di
## `UnitPortrait`/`HeroPortrait` yang dipakai kartu HERO SHOP menu — bingkai
## 60 px di baris toko terlalu kecil untuk wajah cadangan bergaya itu).
var portrait: Texture2D = null
var _hover := false


func _init() -> void:
	custom_minimum_size = Vector2(CARD_W, CARD_H)
	mouse_filter = Control.MOUSE_FILTER_STOP
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_SHRINK_CENTER
	mouse_entered.connect(_set_hover.bind(true))
	mouse_exited.connect(_set_hover.bind(false))


## `p_stats` = entri heroes.json (name/title/role/hp/damage/range/color).
##
## `p_state` (BUY/ACTIVE/MAX/POOR/LOCKED) hanya menentukan VISUAL pill —
## sedangkan `ui_data.blocked` adalah ALASAN dalam kosakata baris toko pygame
## ("", OWNED, FULL, POOR, LOCKED, sama seperti `_make_button(..., {"blocked":
## blocked})`). Dua hal itu berbeda: kartu ACTIVE alasannya OWNED, kartu MAX
## alasannya FULL — dan alasan LOCKED justru string KOSONG di baris toko.
## Karena itu alasannya WAJIB dikirim pemanggil yang menghitungnya dari state
## permainan (`ShopPanel._make_hero_card`), bukan diturunkan dari state kartu:
## sebelum koreksi 2026-09-14 kartu menuliskan STATE ke `blocked` sehingga
## audit kontrak UiHudParityTest gagal ("OWNED reason"/"FULL reason").
func configure(p_hero_type: String, p_stats: Dictionary, p_cost: int,
		p_state: String, p_cb: Callable, p_tip: String,
		p_reason: String) -> HeroShopCard:
	hero_type = p_hero_type
	stats = p_stats
	cost = p_cost
	state = p_state
	reason = p_reason
	portrait = UnitPortrait.portrait_texture(p_hero_type,
		PORTRAIT_ART_W, PORTRAIT_ART_H, false)
	_build_button(p_cb, p_tip)
	queue_redraw()
	return self


## Button AKSI tanpa visual (stylebox dikosongkan) di rect pill pygame —
## kartu yang menggambar pill-nya, tombol hanya memegang ui_key/ui_data +
## klik/keyboard. Persis pemisahan "digambar vs interaktif" di pygame.
func _build_button(cb: Callable, tip: String) -> void:
	if action_button != null and is_instance_valid(action_button):
		action_button.queue_free()
	var b := Button.new()
	b.text = ""
	b.tooltip_text = tip
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	for s in ["normal", "hover", "pressed", "disabled", "focus"]:
		b.add_theme_stylebox_override(s, StyleBoxEmpty.new())
	b.set_meta("ui_key", "buy_hero_" + hero_type)
	b.set_meta("ui_data", {"cost": cost, "blocked": reason,
		"owned": state == "ACTIVE"})
	b.mouse_filter = Control.MOUSE_FILTER_STOP
	# disabled = kartu tidak bisa dibeli (ACTIVE/MAX/POOR/LOCKED) — sama
	# seperti baris lama yang memakai `_make_button(..., can, ...)`.
	b.disabled = state != "BUY"
	if state == "BUY" and cb.is_valid():
		b.pressed.connect(cb)
	add_child(b)
	action_button = b
	_anchor_button()


func _anchor_button() -> void:
	if action_button == null:
		return
	var r := _btn_rect()
	action_button.position = r.position
	action_button.size = r.size


func _set_hover(v: bool) -> void:
	_hover = v
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_anchor_button()
		queue_redraw()


func _btn_rect() -> Rect2:
	return Rect2(Vector2(size.x - BTN_W - BTN_RIGHT, (size.y - BTN_H) * 0.5),
		Vector2(BTN_W, BTN_H))


func _interactive() -> bool:
	# pygame: `not owned and len(g.heroes) < MAX_HEROES_OWNED`
	return state == "BUY"


# ══════════════════════════════════════════════════════════
#  RENDER
# ══════════════════════════════════════════════════════════

func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	var hover := _hover and _interactive()
	var color_main: Color = _color_main()
	# ── shadow + hover glow + badan kartu ──
	UiTheme.draw_shadow(self, rect, RADIUS)
	if hover:
		UiTheme.draw_glow(self, rect.grow_individual(6.0, 6.0, 6.0, 6.0),
			color_main, 60.0 / 255.0)
	UiTheme.draw_rr(self, rect,
		COL_OWNED_BG if state == "ACTIVE" else COL_BG, RADIUS)
	var border := color_main
	if state == "ACTIVE":
		border = COL_OWNED_BORDER
	elif hover:
		border = Color(1, 1, 1)
	UiTheme.draw_rr_outline(self, rect, border, RADIUS, 3.0 if hover else 2.0)
	# ── potret 60 px berbingkai ──
	var pbox := Rect2(Vector2(PORTRAIT_X, (size.y - PORTRAIT) * 0.5),
		Vector2(PORTRAIT, PORTRAIT))
	UiTheme.draw_rr(self, pbox, COL_PORTRAIT_BG, 4.0)
	UiTheme.draw_rr_outline(self, pbox, color_main, 4.0, 1.0)
	if portrait != null:
		var pw := float(portrait.get_width())
		var ph := float(portrait.get_height())
		# `HeroPortraits.draw(..., cx + size//2, cy + size//2 + 3)` —
		# dipusatkan di kotak potret, digeser 3 px ke bawah.
		draw_texture_rect(portrait, Rect2(pbox.get_center()
			+ Vector2(-pw * 0.5, -ph * 0.5 + 3.0), Vector2(pw, ph)), false)
	# ── info ──
	var info_x := INFO_X
	var nf := UiTheme.body_bold()
	var name_w := maxf(60.0, size.x - NAME_RESERVE - info_x)
	UiTheme.draw_text(self, nf,
		UiTheme.fit_ellipsis(nf, 22, str(stats.get("name", hero_type)),
			name_w), 22, Color(1, 1, 1), Vector2(info_x, NAME_Y), false)
	var tf := UiTheme.body_medium()
	UiTheme.draw_text(self, tf,
		UiTheme.fit_ellipsis(tf, 16, str(stats.get("title", "")), name_w),
		16, COL_TITLE, Vector2(info_x, NAME_Y + TITLE_DY), false)
	# chip ROLE
	var rf := UiTheme.body_bold()
	var role := str(stats.get("role", "-")).to_upper()
	var role_w: float = rf.get_string_size(role, HORIZONTAL_ALIGNMENT_LEFT,
		-1, 14).x + ROLE_PAD_X * 2.0
	var rbox := Rect2(Vector2(info_x, NAME_Y + ROLE_DY),
		Vector2(role_w, ROLE_H))
	UiTheme.draw_rr(self, rbox, Color(0, 0, 0), 8.0)
	UiTheme.draw_rr_outline(self, rbox, color_main, 8.0, 1.0)
	UiTheme.draw_text_centered(self, rf, role, 14, color_main,
		rbox.get_center(), false)
	# baris HP / DMG / RNG
	var sf := UiTheme.body_regular()
	var vf := UiTheme.body_bold()
	var cells := [
		["HP", stats.get("hp", 0), COL_STAT_HP],
		["DMG", stats.get("damage", 0), COL_STAT_DMG],
		["RNG", stats.get("range", 0), COL_STAT_RNG],
	]
	for i in cells.size():
		var sx := info_x + float(i) * STATS_STEP
		UiTheme.draw_text(self, sf, str(cells[i][0]), 10,
			cells[i][2] as Color, Vector2(sx, NAME_Y + STATS_DY), false)
		UiTheme.draw_text(self, vf, str(cells[i][1]), 18, Color(1, 1, 1),
			Vector2(sx, NAME_Y + STATS_DY + 15.0), false)
	# ── pill kanan (digambar kartu, bukan Button) ──
	var br := _btn_rect()
	var label := "%dG" % cost
	var bg := COL_BTN_OK_HOVER if hover else COL_BTN_OK_BG
	var bd := COL_BTN_OK_BD_HOVER if hover else COL_BTN_OK_BD
	var tx := Color(1, 1, 1)
	match state:
		"ACTIVE":
			label = "ACTIVE"
			bg = COL_BTN_OWNED_BG
			bd = COL_BTN_OWNED_BD
			tx = COL_BTN_OWNED_TX
		"MAX":
			label = "MAX"
			bg = COL_BTN_MAX_BG
			bd = COL_BTN_MAX_BD
			tx = COL_BTN_MAX_TX
		"POOR", "LOCKED":
			bg = COL_BTN_POOR_BG
			bd = COL_BTN_POOR_BD
			tx = COL_BTN_POOR_TX
	UiTheme.draw_rr(self, br, bg, 5.0)
	UiTheme.draw_rr_outline(self, br, bd, 5.0, 2.0)
	UiTheme.draw_text_centered(self, UiTheme.body_semibold(), label, 24, tx,
		br.get_center(), false)


## Warna accent hero — sama seperti kartu HERO SHOP menu: warna katalog
## dari HeroDB (heroes.json menyimpannya sebagai "#rrggbb").
func _color_main() -> Color:
	return HeroDB.get_hero_color(hero_type)
