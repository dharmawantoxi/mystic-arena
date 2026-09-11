# ItemIcons.gd — ikon item ITEM FORGE (port hero_items.get_icon 1:1).
#
# pygame memuat `assets/items/<icon>` — nama berkasnya field "icon" di
# ITEM_CATALOG (hero_items.py:248 dst., dibaca get_icon hero_items.py:1676) —
# lalu `pygame.transform.smoothscale(raw, (size, size))` ke ukuran yang
# diminta call site (:1678). Kalau PNG-nya TIDAK ADA, get_icon() menggambar
# ikon prosedural supaya game tetap jalan (hero_items.py:1685-1697): kotak
# warna katalog radius 6 + border glow 2 px.
#
# Port ini mempertahankan DUA cabang itu:
#   * PNG ada      -> ImageTexture hasil scale CPU ke ukuran tampilan, dari
#                     res://assets/items/ (salinan assets/items/ pygame hasil
#                     `tools/convert_to_godot.py --assets`; di-gitignore)
#   * PNG tidak ada -> ImageTexture prosedural (badge warna + border glow),
#                      digambar sendiri di sini — tanpa berkas gambar
# Jadi toko item dan panel hero tetap punya ikon walau aset belum disalin,
# persis janji assets/README.md ("Game tetap jalan tanpa berkas ini").
#
# KENAPA scale di CPU, bukan serahkan tekstur 256 px ke engine?
#   33 ikon × 256² RGBA = ±8,6 MB VRAM hanya untuk ikon toko, padahal yang
#   benar-benar tampil 20-26 px (chip slot SkillBar 30 px, baris ShopPanel
#   30 px). pygame juga men-scale di CPU lalu men-cache hasilnya
#   (_ICON_CACHE hero_items.py:1659), jadi ini sekaligus paritas, dan LANCZOS
#   turun 10:1 jauh lebih bersih daripada minifikasi bilinear engine tanpa
#   mipmap (import 2D bawaan tidak membuat mipmap). Strip unit menyelesaikan
#   masalah sejenis lewat cache FIFO (BakedUnitDB); ikon item cukup kecil
#   untuk di-cache permanen per (item, ukuran). Kalau sumbernya ternyata
#   VRAM-compressed mobile (ETC2/ASTC — tidak bisa diurai CPU di 4.3),
#   scaled_art() mundur teratur: tekstur sumber dipakai dan GPU yang scale.
#
# SATU deviasi sadar dari pygame: badge fallback-nya tanpa label 5 huruf nama
# item (`f.render(data["name"][:5], ...)` hero_items.py:1692). Konsumen port
# ini Button.icon (chip slot item SkillBar + baris toko ShopPanel) yang hanya
# menerima Texture2D, sedangkan Godot tidak punya API raster font -> Image
# (draw_string butuh CanvasItem). Badge warna + glow tetap membawa identitas
# item, dan cabang ini memang hanya hidup saat aset belum disalin.
#
# Twin Pygame: hero_items.py (get_icon + _ICON_CACHE).
# Dikunci: godot/tests/HeroItemsParityTest.gd (_test_icons) +
#          tools/test_godot_asset_pipeline.py (rantai asetnya, tanpa engine).
extends RefCounted
class_name ItemIcons

## Folder ikon di dalam project Godot. Sengaja ditulis sebagai DIREKTORI
## (bukan literal per berkas): 33 nama berkasnya datang dari items.json, jadi
## path-nya disusun runtime — pola yang sama dengan AudioManager.SOUNDS_DIR.
const ITEMS_DIR := "res://assets/items/"

## Ukuran default pygame `get_icon(item_id, size=48)` (hero_items.py:1661).
const DEFAULT_SIZE := 48
## Ukuran ikon slot item di panel hero: SLOT_SIZE 30 - inset 2x2 = 26 px
## (hero_items.py:3010/3080). Call site pygame lain (kartu toko 56 px
## hero_items.py:3808, popup detail 64 px :3530) belum diport — UI Godot
## memakai angka di ShopPanel.gd (ITEM_ROW_ICON) dan SkillBar.gd.
const SLOT_ICON_SIZE := 26

## Geometri fallback pygame (hero_items.py:1686-1690):
##   rect(color,  (2, 2, size-4, size-4), border_radius=6)
##   rect(glow,   (2, 2, size-4, size-4), width=2, border_radius=6)
const FALLBACK_INSET := 2
const FALLBACK_RADIUS := 6.0
const FALLBACK_BORDER := 2.0
## Batas bawah ukuran badge: di bawah ini border 2 px menutup seluruh kotak.
const FALLBACK_MIN_SIZE := 12

## Cache "item_id@ukuran" -> Texture2D (paritas _ICON_CACHE hero_items.py:1659
## yang menyimpan Surface hasil smoothscale per (item_id, size)).
static var _icons: Dictionary = {}
## Cache badge prosedural, kunci sama — dipisah supaya `fallback()` tetap bisa
## dipanggil langsung (tes mengunci geometri/warnanya).
static var _badges: Dictionary = {}
## Peringatan "aset belum disalin" cukup sekali per sesi (pola AudioManager).
static var _warned := false
## Himpunan item yang PNG aslinya berhasil dipakai (laporan/tes, bukan jumlah
## berkas di disk). Dictionary sebagai set: satu item bisa diminta di dua
## ukuran (chip 26 px + baris toko 20 px) tanpa ikut terhitung dua kali.
static var _loaded_ids: Dictionary = {}


# ══════════════════════════════════════════════════════════
#  PATH
# ══════════════════════════════════════════════════════════

## Path res:// ikon item; "" kalau item tak dikenal / tidak punya field icon.
static func path_for(item_id: String) -> String:
	var fname := ItemDB.item_icon(item_id)
	return "" if fname.is_empty() else ITEMS_DIR + fname


## True kalau PNG ikonnya ADA di project (sudah disalin converter).
##
## Pakai ResourceLoader.exists(), BUKAN FileAccess.file_exists(): di build
## hasil export PNG impor hanya ada sebagai .ctex + .remap, jadi FileAccess
## akan menjawab false untuk ikon yang sebenarnya bisa dimuat.
static func has_art(item_id: String) -> bool:
	var path := path_for(item_id)
	return not path.is_empty() and ResourceLoader.exists(path)


## Berapa item yang ikon PNG aslinya terpakai (bukan jumlah berkas di disk).
static func loaded_count() -> int:
	return _loaded_ids.size()


# ══════════════════════════════════════════════════════════
#  TEKSTUR
# ══════════════════════════════════════════════════════════

## Ikon siap pakai untuk Button.icon / TextureRect, sudah seukuran tampilan:
## PNG asli kalau ada, badge prosedural kalau tidak. TIDAK PERNAH null —
## padanan `get_icon()` yang selalu mengembalikan Surface untuk id dikenal.
static func texture(item_id: String, size: int = DEFAULT_SIZE) -> Texture2D:
	# Lantai ukuran = FALLBACK_MIN_SIZE supaya kunci cache selalu sama dengan
	# ukuran tekstur yang keluar (badge di bawah 12 px tertutup border 2 px).
	var s := maxi(FALLBACK_MIN_SIZE, size)
	var key := "%s@%d" % [item_id, s]
	if _icons.has(key):
		return _icons[key] as Texture2D
	var tex := scaled_art(item_id, s)
	if tex == null:
		tex = fallback(item_id, s)
	_icons[key] = tex
	return tex


## PNG asli yang diperkecil ke `size` px — paritas smoothscale pygame
## (hero_items.py:1678). Null kalau item tak dikenal atau aset belum disalin.
##
## Tipe kembaliannya Texture2D, bukan ImageTexture: satu-satunya kasus ikon
## asli TIDAK bisa di-scale di CPU adalah tekstur VRAM-compressed ETC1/ETC2/
## ASTC (Image.decompress() 4.3 hanya mendukung DXT/RGTC/BPTC) — di situ
## tekstur sumber dikembalikan apa adanya dan engine yang men-scale-nya.
static func scaled_art(item_id: String, size: int) -> Texture2D:
	var path := path_for(item_id)
	if path.is_empty():
		return null
	if not ResourceLoader.exists(path):
		# Jangan load() buta: ke path yang hilang engine mencetak "Error
		# opening file" dan godot/tools/godot_log_gate.py menggagalkan CI.
		if not _warned:
			_warned = true
			push_warning(("[ItemIcons] %s belum terisi — ikon item mundur ke "
				+ "badge prosedural. Jalankan `python3 tools/convert_to_godot.py "
				+ "--assets` agar 33 PNG assets/items/ disalin.") % ITEMS_DIR)
		return null
	var src := load(path) as Texture2D
	if src == null:
		return null
	_loaded_ids[item_id] = true
	var base := src.get_image()
	if base == null:
		return src
	# Salinan milik sendiri: get_image() tekstur hasil import bisa mengembalikan
	# Image yang masih dipegang cache ResourceLoader, sedangkan resize()
	# mengubah in-place — tanpa salinan, permintaan ukuran lain untuk item yang
	# sama memulai dari gambar yang sudah terlanjur diperkecil. Dimensi dan
	# format harus sama persis dengan sumber (copy_from menolak yang beda).
	var img := Image.create(base.get_width(), base.get_height(), false,
		base.get_format())
	img.copy_from(base)
	if img.is_compressed() and (img.decompress() != OK or img.is_compressed()):
		# Kompresi VRAM mobile (ETC1/ETC2/ASTC) tidak bisa diurai di CPU:
		# resize() menolak data terkompres, jadi serahkan ke GPU. Import 2D
		# bawaan project ini Lossless, jadi cabang ini tidak kena di build normal.
		return src
	if img.has_mipmaps():
		img.clear_mipmaps()
	if img.get_width() != size or img.get_height() != size:
		# Signature Godot 4.3: resize(width, height, interpolation). Bentuk
		# resize(dst_size: Vector2i, ...) baru ada di 4.4+ dan di 4.3 langsung
		# Parse Error saat import ("argument 1 should be int but is Vector2i").
		img.resize(size, size, Image.INTERPOLATE_LANCZOS)
	return ImageTexture.create_from_image(img)


## Badge prosedural (cabang fallback get_icon): kotak warna katalog radius 6
## + border glow 2 px, digambar piksel demi piksel (pola UiTheme._knob_texture
## yang juga menggambar tekstur tanpa berkas gambar).
static func fallback(item_id: String, size: int = DEFAULT_SIZE) -> ImageTexture:
	var s := maxi(FALLBACK_MIN_SIZE, size)
	var key := "%s@%d" % [item_id, s]
	if _badges.has(key):
		return _badges[key] as ImageTexture
	var col := ItemDB.item_color(item_id)
	var glow := ItemDB.item_glow(item_id)
	var img := Image.create(s, s, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var side := float(s - FALLBACK_INSET * 2)
	var rect := Rect2(Vector2(FALLBACK_INSET, FALLBACK_INSET), Vector2(side, side))
	for y in range(s):
		for x in range(s):
			# Sampel di tengah piksel (x+0.5) supaya tepi tidak bergeser
			# setengah piksel saat tekstur di-scale engine.
			var d := _rr_distance(Vector2(x + 0.5, y + 0.5), rect, FALLBACK_RADIUS)
			if d > 0.5:
				continue
			# Border 2 px di tepi dalam kotak = pygame width=2 (digambar di
			# atas fill, jadi ring menutupi 2 px terluar bentuk membulat).
			var c := glow if d > -FALLBACK_BORDER else col
			# Anti-aliasing 1 px: pygame draw_rect tepinya keras, tapi badge
			# ini ikut di-scale engine (Button.expand_icon) sehingga tepi
			# keras terlihat bergerigi.
			img.set_pixel(x, y,
				Color(c.r, c.g, c.b, c.a * clampf(0.5 - d, 0.0, 1.0)))
	var tex := ImageTexture.create_from_image(img)
	_badges[key] = tex
	return tex


## Kosongkan cache (dipakai tes; runtime tidak perlu — items.json tidak
## berubah selama proses hidup, sama seperti _ICON_CACHE pygame).
static func clear_cache() -> void:
	_icons.clear()
	_badges.clear()
	_loaded_ids.clear()
	_warned = false


# ══════════════════════════════════════════════════════════
#  GEOMETRI
# ══════════════════════════════════════════════════════════

## Jarak bertanda ke persegi membulat: negatif = di dalam, 0 = tepat di tepi.
static func _rr_distance(p: Vector2, rect: Rect2, radius: float) -> float:
	var r := clampf(radius, 0.0, minf(rect.size.x, rect.size.y) * 0.5)
	var half := rect.size * 0.5 - Vector2(r, r)
	var d := (p - rect.get_center()).abs() - half
	return (Vector2(maxf(d.x, 0.0), maxf(d.y, 0.0)).length()
		+ minf(maxf(d.x, d.y), 0.0) - r)
