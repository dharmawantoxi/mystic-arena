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

## Baca ulang ukuran viewport dari engine SEKARANG (bukan menunggu sinyal
## `size_changed`). Dipakai kontrol yang harus menata diri seketika — mis.
## dialog TOP UP yang menerima NOTIFICATION_RESIZED sebelum sinyalnya sampai.
func sync_viewport() -> Vector2:
	var vp := get_viewport()
	if vp != null:
		viewport_size = vp.get_visible_rect().size
	return viewport_size

func _on_viewport_changed() -> void:
	sync_viewport()
	layout_changed.emit()


# ══════════════════════════════════════════════════════════
#  FRAME ARENA 1280x720 DI LAYAR
# ══════════════════════════════════════════════════════════
#
# Kamera arena dipasang Main._frame_camera(): posisi (640, 360) + limit
# 0..1280 / 0..720 + position smoothing. Camera2D MENGUNCI rect layar ke
# limit itu (scene/2d/camera_2d.cpp:172-186 + :225-241), dan zoom-nya
# SELALU 1 — jadi arena TIDAK melebar mengikuti jendela:
#
#   * jendela 16:9 persis  -> frame = (0, 0, 1280, 720) = seluruh viewport,
#   * jendela lebih besar/lebih lebar (16:10, ultrawide, maximize dengan
#     taskbar) -> sudut kiri-atas viewport = world (0, 0), dan sisa kanan /
#     bawah viewport ada DI LUAR peta,
#   * jendela lebih kecil dari 1280x720 -> kamera terpotong rata tengah:
#     frame melewati tepi layar di kedua sisi.
#
# Akibat yang mudah terlewat: Control ber-`anchor = 0.5` terpusat di
# VIEWPORT, bukan di frame arena. Di jendela 16:10 titik itu jatuh di luar
# peta — itulah kenapa layar VICTORY/DEFEAT dan dialog TOP UP tampak keluar
# frame di Godot desktop padahal di pygame (yang menggambar ke surface
# 1280x720) keduanya selalu di tengah arena. Semua UI modal wajib memakai
# `arena_center()` / `place_in_arena()` di bawah, BUKAN pusat viewport.

## Geseran sudut kiri-atas frame arena dari (0,0) viewport, px. Sama dengan
## penguncian Camera2D: nol saat viewport >= frame di kedua sumbu (arena
## menempel di kiri-atas), positif saat viewport lebih kecil (arena tergeser
## keluar layar, kamera terpotong rata tengah).
func arena_frame_offset() -> Vector2:
	return Vector2(
		clampf(DESIGN_SIZE.x * 0.5 - viewport_size.x * 0.5, 0.0,
			maxf(0.0, DESIGN_SIZE.x - viewport_size.x)),
		clampf(DESIGN_SIZE.y * 0.5 - viewport_size.y * 0.5, 0.0,
			maxf(0.0, DESIGN_SIZE.y - viewport_size.y)))

## Rect frame arena di koordinat layar (boleh melewati tepi viewport).
func arena_frame_rect() -> Rect2:
	return Rect2(-arena_frame_offset(), DESIGN_SIZE)

## Bagian frame arena yang benar-benar terlihat (perpotongan dengan viewport).
## Dasar semua pembatasan ukuran supaya isi frame tidak pernah terpotong.
func arena_visible_rect() -> Rect2:
	return Rect2(Vector2.ZERO, viewport_size).intersection(arena_frame_rect())

## Titik tengah frame arena di koordinat layar. Di 16:9 dan di jendela yang
## lebih kecil dari frame nilainya = pusat viewport; di jendela lebih
## besar/lebar ia menjauh ke kiri-atas (mengikuti kamera yang terkunci).
func arena_center() -> Vector2:
	return arena_frame_rect().get_center()

## Offset untuk Control ber-anchor 0.5 agar terpusat di frame arena:
## offset = pusat frame arena - pusat viewport (nol di 16:9).
func arena_center_offset() -> Vector2:
	return arena_center() - viewport_size * 0.5

## Skala seragam (<=1) supaya `size` muat di frame arena yang terlihat
## dikurangi `margin` px. Pemakai (dialog TOP UP) membulatkan ke bawah
## dengan batas keterbacaan sendiri.
func arena_fit_scale(size: Vector2, margin: float = 0.0) -> float:
	if size.x <= 0.0 or size.y <= 0.0:
		return 1.0
	var avail := arena_visible_rect().size
	return minf(1.0, minf((avail.x - margin) / size.x,
		(avail.y - margin) / size.y))

## Tempatkan Control ber-anchor 0.5 supaya terpusat di frame arena:
## `arena_offset` = jarak pusat kontrol dari pusat FRAME ARENA (px),
## `size` = ukuran kontrol (px). Padanan "gambar di surface 1280x720"
## pygame: titik acuannya pusat peta, bukan pusat jendela.
func place_in_arena(c: Control, arena_offset: Vector2, size: Vector2) -> void:
	if c == null:
		return
	var o := arena_center_offset() + arena_offset
	c.anchor_left = 0.5
	c.anchor_top = 0.5
	c.anchor_right = 0.5
	c.anchor_bottom = 0.5
	c.offset_left = o.x - size.x * 0.5
	c.offset_top = o.y - size.y * 0.5
	c.offset_right = o.x + size.x * 0.5
	c.offset_bottom = o.y + size.y * 0.5

## Patok Control supaya benar-benar mengisi seluruh rect parent (atau
## viewport, bila parent-nya bukan Control) — pengganti langsung pemanggilan
## `set_anchors_preset(Control.PRESET_FULL_RECT)`.
##
## Jebakan yang memperbaiki bug 2026-09-14 ("pop up TOP UP & layar
## VICTORY/DEFEAT keluar frame"): `set_anchors_preset` TIDAK mengosongkan
## offset — dengan `keep_offsets` default (false) Godot MENGHITUNG ULANG
## offset supaya rect Control tetap seperti sebelumnya, jadi Control yang
## dibuat lewat kode (rect 0x0) TETAP 0x0 walau anchor-nya sudah 0..1.
## Anak ber-anchor 0.5 pun terpusat di (0,0) = pojok kiri-atas jendela
## (terpotong keluar layar) dan lapisan gelap full-rect tidak terlihat.
## Offset dinolkan eksplisit di sini supaya anchor 0..1 benar-benar berarti.
func fill_parent(c: Control) -> void:
	if c == null:
		return
	c.anchor_left = 0.0
	c.anchor_top = 0.0
	c.anchor_right = 1.0
	c.anchor_bottom = 1.0
	c.offset_left = 0.0
	c.offset_top = 0.0
	c.offset_right = 0.0
	c.offset_bottom = 0.0

## Rekatkan Control ke frame ARENA (bukan viewport) — dipakai lapisan gelap
## full-screen overlay hasil. Di luar frame (rail panel kanan / tepi kosong)
## peta tetap terlihat, persis pygame yang tidak pernah menutupi panel kanan.
func cover_arena(c: Control) -> void:
	if c == null:
		return
	var f := arena_frame_rect()
	c.anchor_left = 0.0
	c.anchor_top = 0.0
	c.anchor_right = 0.0
	c.anchor_bottom = 0.0
	c.offset_left = f.position.x
	c.offset_top = f.position.y
	c.offset_right = f.position.x + f.size.x
	c.offset_bottom = f.position.y + f.size.y

# ══════════════════════════════════════════════════════════
#  SAFE AREA + GETAR (port platform_utils.get_safe_area / .vibrate)
# ══════════════════════════════════════════════════════════

## Paritas `platform_utils._SAFE_MARGIN_LOGICAL = 28`: tepi kiri/kanan aman
## dari poni dan gesture bar saat fullscreen HP. Atas 10 px, bawah 10 px
## (pygame menulis `LOGICAL_HEIGHT - 20` = 10 + 10).
const SAFE_MARGIN_LOGICAL := 28.0
const SAFE_TOP := 10.0
const SAFE_BOTTOM := 10.0


## Padanan `platform_utils.TOUCH_MODE` = `IS_ANDROID or MYSTIC_FORCE_TOUCH=1`.
## Pemilik keputusannya AppShell (port `main.py`), dibaca ulang di sini supaya
## HUD/overlay punya SATU sumber.
func touch_mode() -> bool:
	return AppShell.touch_mode()


## Rect aman dalam koordinat logis 1280x720 — paritas `get_safe_area()`:
## di luar mode sentuh = arena penuh (0,0,1280,720); di HP =
## (28, 10, 1280-56, 720-20).
##
## CATATAN: pygame TIDAK membaca data poni asli (Android API
## `WindowInsets`), hanya margin tetap — jadi "poni/cutout" ditangani lewat
## asumsi 28 px. Godot sengaja TIDAK menambah `DisplayServer.screen_get_*`
## di atasnya: aturan proyek adalah paritas, bukan melampaui pygame. Titik
## penyatuannya ada di satu fungsi ini, jadi kalau nanti mau ditingkatkan,
## hanya sini yang diubah.
func safe_area() -> Rect2:
	if not touch_mode():
		return Rect2(Vector2.ZERO, DESIGN_SIZE)
	return Rect2(SAFE_MARGIN_LOGICAL, SAFE_TOP,
		DESIGN_SIZE.x - SAFE_MARGIN_LOGICAL * 2.0,
		DESIGN_SIZE.y - SAFE_TOP - SAFE_BOTTOM)


## Getar pendek sebagai umpan balik tombol (paritas `platform_utils.vibrate`
## — dipakai main.py: 30 ms untuk TAHAN tombol jeda, 15 ms untuk tombol panel
## kanan). Godot 4: `Input.vibrate_handheld`, hanya nyata di Android/iOS.
## Return false di luar mode sentuh, persis `if not IS_ANDROID: return False`.
## Deviasi mesin: pygame mengembalikan False kalau `getSystemService` tidak
## memberi vibrator; Godot tidak bisa menanya alatnya, jadi True di sini
## berarti "permintaan diteruskan ke engine".
func vibrate(ms: int) -> bool:
	if not touch_mode():
		return false
	Input.vibrate_handheld(ms)
	return true


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

## Modal besar di tengah FRAME ARENA (HERO SHOP / ITEM FORGE). Selalu masuk
## frame: lebar/tinggi dibatasi bagian frame yang terlihat dikurangi margin,
## dan pusatnya = pusat frame arena — pusat VIEWPORT akan jatuh di luar peta
## begitu jendela lebih lebar/tinggi dari 16:9 (lihat catatan di atas).
func modal_rect() -> Rect2:
	var margin := 24.0
	var avail := arena_visible_rect().size
	var w := minf(900.0, maxf(320.0, avail.x - margin * 2.0))
	var h := minf(560.0, maxf(240.0, avail.y - margin * 2.0))
	var c := arena_center()
	return Rect2(c.x - w * 0.5, c.y - h * 0.5, w, h)
