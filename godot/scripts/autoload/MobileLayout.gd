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
# Popup tower/castle memakai jalur panel kanan (rail_popup_rect), popup
# HERO (panel upgrade) memakai slot tetap pygame (hero_popup_rect =
# platform_utils.ZONA_POPUP_Y), sedangkan HERO SHOP / ITEM FORGE memakai
# modal besar di tengah (modal_rect) — persis pembagian di screenshot pygame.
#
# ATURAN TERTINGGI (koreksi 2026-09-10): SEMUA UI panel hidup di x >= 1280.
# Arena (peta) 1280x720 tidak boleh ditutupi panel; kalau layar tidak
# menyisakan rail (16:9 atau lebih sempit), UI itu TIDAK DIGAMBAR — persis
# pygame yang tidak punya side panel di 16:9.
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
## ARENA = peta permainan (koordinat game 1280x720 rata kiri di 0,0 —
## paritas platform_utils: area main rata kiri sehingga koordinat game dan
## koordinat layar penuh sama). Tidak ada UI panel yang boleh menyentuh
## rect ini; itulah invariant "panel tidak menghalangi map".
const ARENA := Rect2(0.0, 0.0, 1280.0, 720.0)
## Jalur popup panel kanan pygame — `platform_utils.ZONA_POPUP_Y = 430`
## (di bawah daftar HEROES, di atas TACTICAL COMMANDS).
const POPUP_ZONE_TOP := 430.0
## Zona bawah panel yang tidak boleh ditimpa popup — paritas
## `platform_utils.ZONA_BAWAH_H = 120`. Popup yang tidak muat di atas zona
## ini DIDORONG KE ATAS (bukan dibiarkan menutupi dasar panel): untuk panel
## 720 px dan popup hero 276 px, y jadi 720-120-276 = 324, bukan 430.
const POPUP_BOTTOM_RESERVED := 120.0
## Ukuran panel hero pygame (ui_components HeroPanel: panel_w 280,
## panel_h 276) — popup upgrade hero.
const HERO_POPUP_SIZE := Vector2(280.0, 276.0)

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

## Rect PETA (arena 1280x720). Satu sumber untuk invariant "UI panel tidak
## boleh menutupi peta": pemanggil (TacticalBar, SidePanel, popup hero)
## memakai `rect.intersects(MobileLayout.arena_rect())` untuk menolak
## penempatan yang menimpa permainan.
func arena_rect() -> Rect2:
	return ARENA

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

## Popup HERO (panel upgrade hero) DI DALAM panel kanan — port
## `platform_utils.panel_pos_bawah(280, 276)`: x di tengah rail, y di slot
## tetap `ZONA_POPUP_Y` (430). pygame mengembalikan None bila panel tak ada
## ATAU terlalu sempit (`w > p.width - 8`); padanannya di sini Rect2()
## kosong, dan pemanggil (SkillBar) jatuh ke posisi lama kiri-bawah layar.
## Popup ini SENGAJA menimpa sebagian kotak TACTICAL COMMANDS (pygame
## mencatat hal yang sama): hit-test Godot memberi prioritas ke popup
## karena SkillBar ditambahkan SETELAH TacticalBar di HUD, dan
## TacticalBar._popup_blocks() menolak hold baru selama hero terpilih.
func hero_popup_rect() -> Rect2:
	var rail := side_panel_rect()
	if rail.size.x <= 0.0:
		return Rect2()
	if HERO_POPUP_SIZE.x > rail.size.x - 8.0:
		return Rect2()
	# pygame: x = p.x + (p.width - w) // 2
	var x := rail.position.x + floorf((rail.size.x - HERO_POPUP_SIZE.x) * 0.5)
	# pygame: y = p.y + ZONA_POPUP_Y, LALU didorong ke atas kalau popup
	# menabrak zona bawah panel (ZONA_BAWAH_H = 120):
	#   if y + h > p.bottom - 120: y = max(p.y + 8, p.bottom - 120 - h)
	# Untuk rail 720 px + popup hero 276 px clamp ini AKTIF: 430+276=706 >
	# 600, jadi y = 720-120-276 = 324. (Angka 430 hanya berlaku untuk popup
	# pendek 165 px seperti popup upgrade tower.)
	var y := rail.position.y + POPUP_ZONE_TOP
	var bottom := rail.position.y + rail.size.y
	if y + HERO_POPUP_SIZE.y > bottom - POPUP_BOTTOM_RESERVED:
		y = maxf(rail.position.y + 8.0,
			bottom - POPUP_BOTTOM_RESERVED - HERO_POPUP_SIZE.y)
	return Rect2(x, y, HERO_POPUP_SIZE.x, HERO_POPUP_SIZE.y)

## Modal besar di tengah layar (HERO SHOP / ITEM FORGE). Selalu masuk frame:
## lebar/tinggi dibatasi ukuran viewport dikurangi margin.
func modal_rect() -> Rect2:
	var margin := 24.0
	var avail_w := maxf(320.0, viewport_size.x - margin * 2.0)
	var avail_h := maxf(240.0, viewport_size.y - margin * 2.0)
	var w := minf(900.0, avail_w)
	var h := minf(560.0, avail_h)
	return Rect2((viewport_size.x - w) * 0.5, (viewport_size.y - h) * 0.5, w, h)
