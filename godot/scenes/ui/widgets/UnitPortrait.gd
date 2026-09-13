# UnitPortrait.gd — potret hero/boss yang DIRENDER dari unit sungguhan.
#
# Port ui_components/hero_portraits.py::HeroPortraits 1:1 (dipakai
# `_draw_meta_hero_card` _core.py:5119 dan `HeroShop._draw_compact_card`
# ui_components/_bundle.py:2043). pygame menyebut modulnya "100%
# auto-generate portraits dari existing renderers": tidak ada satu pun
# berkas gambar portrait — potret kartu HERO SHOP adalah hasil render
# renderer unit itu sendiri (boss renderer dulu, lalu hero renderer, lalu
# alias `_true`), di-crop ke bbox-nya, diperkecil ke kotak 60x70, dan
# digrayscale kalau kartunya tidak bisa dibeli.
#
# Di Godot "renderer unit" adalah strip PNG hasil bake renderer pygame
# (assets/units/<type>.png + manifest data/baked_units.json — Fase 5 Opsi
# A, dibaca BakedUnitDB). Rantainya doncok, jadi jalur potret mengikuti:
#
#   ada strip  -> frame idle[0] di-crop bbox lalu di-scale ke kotak target
#                 (persis HeroPortraits._crop_and_scale: scan 2px, alpha>10,
#                 pad 4, scale = min(sx, sy, 1.0) TANPA pernah memperbesar,
#                 INTERPOLATE_LANCZOS = padanan smoothscale pygame)
#   tanpa strip-> fallback `_draw_generic` (mahkota + wajah), yang sudah
#                 diport di HeroPortrait.gd — kelas ini memperluas kelas itu,
#                 jadi geometri fallback-nya TIDAK ditulis dua kali.
#
# Kenapa frame IDLE pertama, bukan seluruh strip? pygame juga merender satu
# pose (fase idle saat pulse=0) ke kanvas 160/200 px, lalu memotongnya.
#
# `dimmed` = padanan argumen `owned` pygame: kartu yang belum terbuka
# (boss-nya belum dikalahkan) digambar GRAYSCALE dari stripnya dan
# DIREDUPKAN (main_c * 0.45) pada fallback, sama seperti pygame.
#
# Twin Pygame: ui_components/hero_portraits.py (HeroPortraits).
extends HeroPortrait
class_name UnitPortrait

const BakedUnitDB = preload("res://scripts/render/BakedUnitDB.gd")

## Kotak target potret = pw/ph pygame (HeroPortraits._try_auto_render).
const TARGET_W := 60
const TARGET_H := 70
## Bbox portrait pygame: scan per 2 piksel, ambang alpha 10, padding 4
## (_crop_and_scale).
const SCAN_STEP := 2
const ALPHA_MIN := 10
const BBOX_PAD := 4
## Bobot luminansi `_apply_grayscale`.
const LUMA_R := 0.299
const LUMA_G := 0.587
const LUMA_B := 0.114

## "unit@WxHxdim" -> Texture2D (padanan HeroPortraits._cache, yang juga
## menyimpan per (hero_type, owned) seumur proses).
static var _cache: Dictionary = {}


## Potret siap-pakai untuk satu unit pada kotak target tertentu. Null kalau
## unit tidak punya strip bake (caller menggambar fallback generik).
static func portrait_texture(unit_type: String, target_w: int = TARGET_W,
		target_h: int = TARGET_H, dimmed: bool = false) -> Texture2D:
	if unit_type.is_empty():
		return null
	var key := "%s@%dx%d@%d" % [unit_type, target_w, target_h, 1 if dimmed else 0]
	if _cache.has(key):
		return _cache[key] as Texture2D
	var tex := _render_portrait(unit_type, target_w, target_h, dimmed)
	_cache[key] = tex
	return tex


static func _render_portrait(unit_type: String, target_w: int,
		target_h: int, dimmed: bool) -> Texture2D:
	var entry: Dictionary = BakedUnitDB.entry(unit_type)
	var strip: Texture2D = BakedUnitDB.texture(unit_type)
	if entry.is_empty() or strip == null:
		return null
	var frame_w := int(entry.get("frame_w", 0))
	var frame_h := int(entry.get("frame_h", 0))
	if frame_w <= 0 or frame_h <= 0:
		return null
	# Frame PERTAMA animasi "idle" (anims = [frame_pertama, jumlah]) — irisan
	# grid yang sama dipakai BakedSprite.gd saat memotong strip.
	var idle: Array = (entry.get("anims", {}) as Dictionary).get("idle", [0, 0])
	var first := int(idle[0]) if idle.size() >= 1 else 0
	var fpr := maxi(1, int(entry.get("frames_per_row", 1)))
	var region := Rect2i(Vector2i((first % fpr) * frame_w,
		floori(float(first) / float(fpr)) * frame_h),
		Vector2i(frame_w, frame_h))

	var base := strip.get_image()
	if base == null:
		return null
	if base.is_compressed() and (base.decompress() != OK
			or base.is_compressed()):
		# VRAM-compressed (ETC2/ASTC) tidak bisa diurai CPU di 4.3 — sama
		# seperti ItemIcons: mundur ke tekstur sumber utuh, tanpa crop/scale.
		return strip
	if region.end.x > base.get_width() or region.end.y > base.get_height():
		return null
	var frame := base.get_region(region)
	var box := _content_bbox(frame)
	if box.size.x <= 0.0 or box.size.y <= 0.0:
		return null
	var cropped := frame.get_region(box)
	if dimmed:
		_grayscale(cropped)
	# `scale = min(sx, sy, 1.0)` — pygame TIDAK pernah memperbesar potret.
	var scale := minf(float(target_w) / float(cropped.get_width()),
		minf(float(target_h) / float(cropped.get_height()), 1.0))
	var nw := maxi(1, int(float(cropped.get_width()) * scale))
	var nh := maxi(1, int(float(cropped.get_height()) * scale))
	cropped.resize(nw, nh, Image.INTERPOLATE_LANCZOS)
	return ImageTexture.create_from_image(cropped)


## Bbox isi (piksel alpha > ALPHA_MIN), di-scan per SCAN_STEP lalu dilebarkan
## BBOX_PAD dan dijepit ke gambar — padanan `_crop_and_scale` bagian scan.
##
## Jalur cepat membaca buffer RGBA8 langsung (satu `get_data()`, indeks
## `y*w*4 + x*4 + 3`) — kartu HERO SHOP bisa memuat puluhan unit sekaligus dan
## `Image.get_pixel()` per piksel membuat layar itu terasa macet. Format lain
## (mis. RGB8/E TC yang baru didecompress) jatuh ke jalur per-piksel.
static func _content_bbox(img: Image) -> Rect2i:
	var w := img.get_width()
	var h := img.get_height()
	var min_x := w
	var min_y := h
	var max_x := -1
	var max_y := -1
	if img.get_format() == Image.FORMAT_RGBA8:
		var data := img.get_data()
		var row_len := w * 4
		var sy := 0
		while sy < h:
			var base := sy * row_len
			var sx := 0
			while sx < w:
				if data[base + sx * 4 + 3] > ALPHA_MIN:
					min_x = mini(min_x, sx)
					min_y = mini(min_y, sy)
					max_x = maxi(max_x, sx)
					max_y = maxi(max_y, sy)
				sx += SCAN_STEP
			sy += SCAN_STEP
	else:
		for sy2 in range(0, h, SCAN_STEP):
			for sx2 in range(0, w, SCAN_STEP):
				if img.get_pixel(sx2, sy2).a * 255.0 <= float(ALPHA_MIN):
					continue
				min_x = mini(min_x, sx2)
				min_y = mini(min_y, sy2)
				max_x = maxi(max_x, sx2)
				max_y = maxi(max_y, sy2)
	if max_x < min_x or max_y < min_y:
		return Rect2i()
	var x0 := clampi(min_x - BBOX_PAD, 0, w - 1)
	var y0 := clampi(min_y - BBOX_PAD, 0, h - 1)
	var x1 := clampi(max_x + BBOX_PAD, x0 + 1, w)
	var y1 := clampi(max_y + BBOX_PAD, y0 + 1, h)
	return Rect2i(x0, y0, x1 - x0, y1 - y0)


## Grayscale in-place, alpha utuh (`_apply_grayscale` pygame: 0.299/0.587/
## 0.114). Dijalankan SEBELUM resize supaya hasilnya setahap dengan pygame
## yang men-scale permukaan sudah kelabu.
static func _grayscale(img: Image) -> void:
	if img.get_format() == Image.FORMAT_RGBA8:
		var data := img.get_data()
		var i := 0
		var n := data.size()
		while i + 3 < n:
			var g := int(float(data[i]) * LUMA_R
				+ float(data[i + 1]) * LUMA_G
				+ float(data[i + 2]) * LUMA_B)
			data[i] = g
			data[i + 1] = g
			data[i + 2] = g
			i += 4
		img.set_data(img.get_width(), img.get_height(), false,
			Image.FORMAT_RGBA8, data)
		return
	for y in img.get_height():
		for x in img.get_width():
			var c := img.get_pixel(x, y)
			var g2: float = c.r * LUMA_R + c.g * LUMA_G + c.b * LUMA_B
			img.set_pixel(x, y, Color(g2, g2, g2, c.a))


## Kosongkan cache (dipakai tes; runtime tidak perlu — manifest bake tidak
## berubah selama proses hidup, sama seperti HeroPortraits._cache).
static func clear_cache() -> void:
	_cache.clear()


# ══════════════════════════════════════════════════════════
#  WIDGET (fallback generik diwarisi dari HeroPortrait)
# ══════════════════════════════════════════════════════════

var unit_type: String = ""
var _tex: Texture2D = null


## Pasang unit + warna fallback. `p_dimmed` = kartu terkunci (grayscale pada
## strip, diredupkan pada fallback) — persis argumen `owned` pygame.
func setup_unit(p_unit_type: String, p_main: Color, p_dark: Color,
		p_dimmed: bool = false) -> void:
	unit_type = p_unit_type
	color_main = p_main
	color_dark = p_dark
	dimmed = p_dimmed
	_tex = portrait_texture(p_unit_type, TARGET_W, TARGET_H, p_dimmed)
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		# Potret dipusatkan terhadap `size`; bingkai 78 px baru punya ukuran
		# tetap setelah layout, jadi digambar ulang sekali lagi.
		queue_redraw()


func _draw() -> void:
	if _tex == null:
		# Tidak ada strip bake -> gambar HeroPortrait generik.
		super._draw()
		return
	# Kotak 60x70 pygame di tengah ruang kartu, digeser +3 seperti
	# `portrait_y + portrait_size // 2 + 3` di _draw_meta_hero_card.
	var tw := float(_tex.get_width())
	var th := float(_tex.get_height())
	var pos := Vector2((size.x - tw) * 0.5,
		(size.y - th) * 0.5 + 3.0)
	draw_texture_rect(_tex, Rect2(pos, Vector2(tw, th)), false)
