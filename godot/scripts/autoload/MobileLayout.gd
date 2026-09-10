# MobileLayout.gd — responsive landscape metrics shared by HUD and shops.
#
# Sumber SATU angka untuk tata letak landscape ala pygame
# (mobile/sidepanel.py + mobile/platform_utils.py):
#
#   * arena 1280x720 rata kiri di (0, 0) — koordinat game = koordinat layar,
#   * panel kanan (command rail dinding batu) menempel di tepi arena (x=1280)
#     HANYA saat layar lebih lebar dari 16:9 (sisa >= 120 px), persis pygame,
#   * jalur isi panel kanan TETAP supaya tidak pernah saling menimpa:
#
#        0 ..  76   tombol JEDA
#       84 .. 180   STATUS (gold, LV, wave, shield, difficulty)
#      188 .. 388   daftar HEROES
#      396 .. 474   pintu masuk toko (TOWER/CASTLE/HERO/FORGE)
#      H-236 .. H   TACTICAL COMMANDS (5 tombol)
#
# Popup tower/castle memakai jalur panel kanan (rail_popup_rect), sedangkan
# HERO SHOP / ITEM FORGE memakai modal besar di tengah (modal_rect) —
# persis pembagian di screenshot pygame.
extends Node

signal layout_changed

const DESIGN_SIZE := Vector2(1280.0, 720.0)
## Sisa minimum supaya panel kanan ada — paritas `sisa >= 120`
## platform_utils.create_display (di bawah ini "terlalu sempit, tidak berguna").
## Dengan stretch expand, viewport dinormalisasi ke tinggi 720, jadi ambang
## ini setara rasio layar >= 1400/720 (~17,5:9): 16:9 persis TIDAK punya panel
## (arena penuh, paritas "di layar 16:9 panelnya tidak ada"), HP 18:9 ke atas
## punya panel selebar sisa layarnya (344 px pada 2436x1080).
const SIDE_PANEL_MIN_LEFTOVER := 120.0
## Lebar panel maksimum — paritas batas total pygame `min(2200, usul)`
## (2200 - 1280 = 920). Panel selalu menempel di tepi arena (x = 1280),
## bukan di tepi viewport, persis `Rect(LOGICAL_WIDTH, 0, sisa, H)` pygame.
const SIDE_PANEL_MAX_WIDTH := 920.0
const RAIL_PAD := 14.0
## Tinggi kotak TACTICAL COMMANDS: judul 26 + 5 x (32 + 6) - 6.
const TACTICAL_HEIGHT := 210.0
const TACTICAL_MARGIN := 14.0
const STATUS_TOP := 84.0
const STATUS_HEIGHT := 96.0
const HEROES_TOP := 188.0
const HEROES_HEIGHT := 200.0
const SHOP_TOP := 396.0
const SHOP_HEIGHT := 78.0
## ── PANEL HERO TERPILIH (popup upgrade) ──
## Ukuran HeroPanel pygame (ui_components/_bundle.py 280x276) + jalur popup
## panel kanan pygame (platform_utils.ZONA_POPUP_Y = 430). Di rail Godot
## jalur itu jatuh PAS di dasar kotak TACTICAL (720 - 276 - 14 = 430), jadi
## popup hero menutupi kotak command persis seperti pygame — dan TIDAK
## menutupi tombol toko rail di atasnya (zona 396..474).
const HERO_PANEL_W := 280.0
const HERO_PANEL_H := 276.0
const ZONA_POPUP_Y := 430.0

var viewport_size := DESIGN_SIZE

func _ready() -> void:
	get_tree().root.size_changed.connect(_on_viewport_changed)
	_on_viewport_changed()

func _on_viewport_changed() -> void:
	viewport_size = get_viewport().get_visible_rect().size
	layout_changed.emit()

func has_side_panel() -> bool:
	if viewport_size.x <= viewport_size.y:
		return false
	return (viewport_size.x - DESIGN_SIZE.x) >= SIDE_PANEL_MIN_LEFTOVER

## Lebar panel kanan efektif = SELURUH sisa layar (paritas pygame: panel =
## Rect(1280, 0, sisa, 720)), dibatasi 920 px (paritas batas total 2200).
func side_panel_width() -> float:
	if not has_side_panel():
		return 0.0
	return minf(viewport_size.x - DESIGN_SIZE.x, SIDE_PANEL_MAX_WIDTH)

func side_panel_rect() -> Rect2:
	if not has_side_panel():
		return Rect2()
	var w := side_panel_width()
	return Rect2(DESIGN_SIZE.x, 0.0, w, viewport_size.y)

func content_width() -> float:
	return maxf(0.0, viewport_size.x - side_panel_width())

## Kotak TACTICAL COMMANDS di dasar panel kanan (koordinat layar penuh).
func tactical_rect() -> Rect2:
	var rail := side_panel_rect()
	if rail.size.x <= 0.0:
		return Rect2()
	var h := minf(TACTICAL_HEIGHT, rail.size.y - SHOP_TOP - SHOP_HEIGHT - 24.0)
	h = maxf(h, 120.0)
	var y := maxf(SHOP_TOP + SHOP_HEIGHT + 8.0,
		rail.size.y - h - TACTICAL_MARGIN)
	return Rect2(rail.position.x + RAIL_PAD, rail.position.y + y,
		rail.size.x - RAIL_PAD * 2.0, h)

## Rect panel hero terpilih (popup upgrade hero).
##
## Jalur pertama = DI DALAM rail kanan, paritas HeroPanel pygame yang memakai
## platform_utils.panel_pos_bawah (ZONA_POPUP_Y = 430, digeser naik kalau
## panelnya lebih tinggi dari sisa ruang). Ditambah syarat lebar: rail harus
## memuat panel + margin, paritas `panel_popup_pos` pygame yang mengembalikan
## None saat `w > p.width - 8`.
##
## Kalau rail tidak ada (16:9) atau terlalu sempit: fallback pygame
## `px = 20, py = SCREEN_HEIGHT - panel_h - 20` = kiri-bawah arena.
func hero_panel_rect(w: float = HERO_PANEL_W, h: float = HERO_PANEL_H) -> Rect2:
	var rail := side_panel_rect()
	if rail.size.x >= w + 16.0:
		var x := rail.position.x + (rail.size.x - w) * 0.5
		var y := rail.position.y + ZONA_POPUP_Y
		var y_min := rail.position.y + STATUS_TOP
		var y_max := rail.position.y + rail.size.y - h - TACTICAL_MARGIN
		if y_max < y_min:
			y_max = y_min
		return Rect2(x, clampf(y, y_min, y_max), w, h)
	var x2 := 20.0
	if x2 + w > viewport_size.x - 8.0:
		x2 = maxf(8.0, viewport_size.x - w - 8.0)
	var y2 := maxf(8.0, viewport_size.y - h - 20.0)
	return Rect2(x2, y2, w, h)


## Popup toko yang tampil DI DALAM panel kanan (TOWER SHOP / CASTLE SHOP),
## persis popup upgrade pygame (platform_utils.panel_popup_pos).
func rail_popup_rect() -> Rect2:
	var rail := side_panel_rect()
	if rail.size.x <= 0.0:
		return Rect2()
	var top := rail.position.y + STATUS_TOP
	var bottom := tactical_rect().position.y - 8.0
	if bottom - top < 180.0:
		bottom = rail.position.y + rail.size.y - 12.0
	return Rect2(rail.position.x + 8.0, top,
		rail.size.x - 16.0, maxf(180.0, bottom - top))

## Modal besar di tengah layar (HERO SHOP / ITEM FORGE). Selalu masuk frame:
## lebar/tinggi dibatasi ukuran viewport dikurangi margin.
func modal_rect() -> Rect2:
	var margin := 24.0
	var avail_w := maxf(320.0, viewport_size.x - margin * 2.0)
	var avail_h := maxf(240.0, viewport_size.y - margin * 2.0)
	var w := minf(900.0, avail_w)
	var h := minf(560.0, avail_h)
	return Rect2((viewport_size.x - w) * 0.5, (viewport_size.y - h) * 0.5, w, h)
