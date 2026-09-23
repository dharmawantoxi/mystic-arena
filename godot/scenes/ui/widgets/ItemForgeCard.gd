# ItemForgeCard.gd — kartu ITEM FORGE yang DIGAMBAR, bukan daftar tombol.
#
# Port `ItemShopUI._draw_item_card` (hero_items.py:3790-3892) 1:1 pada
# geometri dan warnanya. Sebelumnya tab ITEM ShopPanel hanya menampilkan
# baris `Button` bertekstur 20 px — secara DATA paritas, tapi visualnya
# bukan kartu Item Forge pygame sama sekali. Kelas ini menggambar kartu yang
# sama: gradasi vertikal, border warna kelas, sudut emas, ikon 56 px,
# badge PHYSICAL/MAGIC/TANK, nama + kategori + harga + jumlah, deskripsi
# ter-wrap, lalu pill BUY di bawah.
#
# KONTRAK YANG TIDAK BERUBAH (dipakai tes paritas + keyboard/controller):
#   * SATU Button dengan `ui_key` "item_buy_<item_id>" dan `ui_data`
#     {cost, blocked} — ShopPanel._make_button memakai bentuk yang sama,
#     jadi HudLayout.shop_ui_keys() + UiHudParityTest tetap mengenali
#     kartunya;
#   * klik = `GameManager.try_buy_item()` lewat callback pemberi kartu;
#   * teks lewat MysticLocalization (bahasa aktif berlaku di dalam kartu).
#
# Perbandingan baris-per-baris dengan pygame (semua angka px = literal
# `_draw_item_card`, BUKAN hasil ukur Godot):
#
#   kartu 250x200 (PANEL_W 1100, grid 4 kolom, gap 12/14)
#   bg      _vgrad (34,40,68)->(17,20,38) bila bisa dibeli,
#           (26,26,38)->(16,16,26) bila tidak; tanpa cheap_alpha: solid
#           (28,33,54) / (24,22,30); radius 8
#   border  warna katalog item kalau bisa dibeli, else (70,70,80), lebar 2
#   ticks   ui_theme.corner_ticks(GOLD, length=9) HANYA saat bisa dibeli
#   ikon    get_icon(sid, 56) di (10, 10)
#   badge   ITEM_CLASS_INFO[kelas] kanan-atas, font 14, h 20, pad x 6,
#           bg (18,22,36) radius 6, border warna kelas 1 px
#   nama    font 24 body_bold warna `glow`, di (74, 12), lebar
#           w - 74 - 12 - badge_w - 8, fit elipsis
#   kategori font 17 body_bold warna kategori di (74, 38)
#   harga   font 21 body_bold (255,220,100) / (200,80,80) di (74, 56)
#   dimiliki font 17 body_bold (150,255,170) di (w-90, 58)
#   deskripsi font 17 body_medium TEXT_BODY, wrap ke w-20, maks 4 baris
#           (baris terakhir dipotong + "…"), mulai y+84, langkah 19
#   tombol  pill (10, h-34, w-20, 26): "BUY" hijau, atau alasannya
#           ("MELEE ONLY"/"MAGIC ONLY"/"NOT AFFORDABLE"/"SELECT HERO")
#
# Deviasi sadar:
#   * "Owned: %d" memakai tabel teks (pygame hard-code Inggris) supaya bahasa
#     Indonesia ikut terbaca; pola yang sama sudah dipakai `shop_buy_for`.
#   * Harga memakai angka + "G" apa adanya, persis f"{cost}G" pygame.
#   * Grid Godot = per KATEGORI katalog (bukan halaman kelas pygame); hanya
#     kartu per item yang diparitaskan di sini.
#
# Twin Pygame: hero_items.py (ItemShopUI._draw_item_card/_wrap_text).
extends Control
class_name ItemForgeCard

## Geometri kartu pygame — dipin apa adanya (kartu Godot 250x200 juga).
const CARD_W := 250.0
const CARD_H := 200.0
const ICON_SIZE := 56
const ICON_X := 10.0
const ICON_Y := 10.0
const TEXT_X := 74.0
const NAME_Y := 12.0
const CAT_Y := 38.0
const COST_Y := 56.0
const OWNED_Y := 58.0
const DESC_Y := 84.0
const DESC_LINE_H := 19.0
const DESC_MAX_LINES := 4
const BADGE_H := 20.0
const BADGE_PAD_X := 6.0
const BADGE_TOP := 8.0
const BADGE_RIGHT := 8.0
const BTN_H := 26.0
const BTN_BOTTOM := 34.0
const BTN_SIDE := 10.0
const CORNER_RADIUS := 8.0
const TICK_LEN := 9.0

## Warna literal `_draw_item_card`.
const COL_BUY_TOP := Color(34.0 / 255.0, 40.0 / 255.0, 68.0 / 255.0)
const COL_BUY_BOT := Color(17.0 / 255.0, 20.0 / 255.0, 38.0 / 255.0)
const COL_NO_TOP := Color(26.0 / 255.0, 26.0 / 255.0, 38.0 / 255.0)
const COL_NO_BOT := Color(16.0 / 255.0, 16.0 / 255.0, 26.0 / 255.0)
const COL_BUY_SOLID := Color(28.0 / 255.0, 33.0 / 255.0, 54.0 / 255.0)
const COL_NO_SOLID := Color(24.0 / 255.0, 22.0 / 255.0, 30.0 / 255.0)
const COL_DEAD_BORDER := Color(70.0 / 255.0, 70.0 / 255.0, 80.0 / 255.0)
const COL_BADGE_BG := Color(18.0 / 255.0, 22.0 / 255.0, 36.0 / 255.0)
const COL_GOLD_TEXT := Color(255.0 / 255.0, 220.0 / 255.0, 100.0 / 255.0)
const COL_COST_NO := Color(200.0 / 255.0, 80.0 / 255.0, 80.0 / 255.0)
const COL_OWNED := Color(150.0 / 255.0, 255.0 / 255.0, 170.0 / 255.0)

## Data kartu (diisi pemakai lewat `configure()`). `has_hero`/`is_melee`/
## `is_magic` adalah cermin state `_draw_item_card` pygame (hero target ada,
## hero melee/magic) — label pill sudah memakai informasi ini (dihitung
## ShopPanel), ketiganya ikut disimpan supaya popup detail item (belum ada di
## port) tidak perlu mengubah tanda tangan `configure()` lagi.
var item_id: String = ""
var can_buy: bool = false
var owned_count: int = 0
var has_hero: bool = true
var is_melee: bool = false
var is_magic: bool = false
## Alasan tak-bisa-beli: "" | OWNED | FULL | MELEE ONLY | MAGIC ONLY | POOR.
var blocked: String = ""
## Label pill yang tergambar (dictulis di `configure()`): PygameButton
## menggambar `label_text` sendiri dan mengosongkan `Button.text`, jadi teks
## kartu dibaca dari sini — bukan dari `.text` tombolnya (penting untuk tes
## dan untuk pemakai yang mau membaca ulang labelnya).
var pill_label: String = ""
## Ikon kartu = `ItemIcons.get_icon(sid, 56)` pygame (tektur siap-pakai,
## sudah seukuran tampilan; badge prosedural saat PNG aset belum disalin).
var icon_texture: Texture2D = null
## Tombol aksi — Kartu MEMPOSISIKAN-nya sendiri (rect pill pygame).
var buy_button: Button = null


func _init() -> void:
	custom_minimum_size = Vector2(CARD_W, CARD_H)
	mouse_filter = Control.MOUSE_FILTER_STOP
	# Font/ikon tidak boleh memancing layout: kartu menggambar dirinya
	# sendiri, tombol aksi di-anchor di bawah. SHRINK (bukan EXPAND_FILL):
	# di GridContainer kartu harus tetap 250x200 pin supaya kolom grid
	# seragam — EXPAND_FILL membuat kartu melebar berbeda-beda mengikuti
	# sisa lebar panel (baris terlihat berantakan).
	size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	size_flags_vertical = Control.SIZE_SHRINK_CENTER


## Pasang data + tombol beli. `p_label`/`p_tip` dihitung pemakai karena
## teksnya milik ShopPanel (`_loc` + `_item_reason_tip`).
func configure(p_item_id: String, p_can_buy: bool, p_owned: int,
		p_has_hero: bool, p_is_melee: bool, p_is_magic: bool,
		p_blocked: String, p_label: String, p_tip: String,
		p_cb: Callable) -> ItemForgeCard:
	item_id = p_item_id
	pill_label = p_label
	tooltip_text = p_tip
	icon_texture = ItemIcons.texture(p_item_id, ICON_SIZE)
	can_buy = p_can_buy
	owned_count = p_owned
	has_hero = p_has_hero
	is_melee = p_is_melee
	is_magic = p_is_magic
	blocked = p_blocked
	_build_button(p_label, p_tip, p_cb)
	queue_redraw()
	return self


func _build_button(label: String, tip: String, cb: Callable) -> void:
	if buy_button != null and is_instance_valid(buy_button):
		buy_button.queue_free()
	var kind := "success" if can_buy else "locked"
	var b := PygameButton.pill_button(label, kind, "", 0, int(BTN_H),
		16 if can_buy else 13)
	b.mouse_filter = Control.MOUSE_FILTER_STOP
	b.disabled = not can_buy
	b.tooltip_text = tip
	b.set_meta("ui_key", "item_buy_" + item_id)
	b.set_meta("ui_data", {"cost": ItemDB.item_cost(item_id),
		"blocked": blocked})
	if can_buy and cb.is_valid():
		b.pressed.connect(cb)
	add_child(b)
	buy_button = b
	_anchor_button()


## Rect pill pygame: (10, h-34, w-20, 26). Di Godot lewat anchor supaya
## ikut kalau panel memaksa kartu melebar.
func _anchor_button() -> void:
	if buy_button == null:
		return
	buy_button.anchor_left = 0.0
	buy_button.anchor_top = 1.0
	buy_button.anchor_right = 1.0
	buy_button.anchor_bottom = 1.0
	buy_button.offset_left = BTN_SIDE
	buy_button.offset_right = -BTN_SIDE
	buy_button.offset_top = -BTN_BOTTOM
	buy_button.offset_bottom = -BTN_BOTTOM + BTN_H


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_anchor_button()
		# `_draw()` membaca `size` untuk semua rect (border, badge, wrap
		# deskripsi, posisi pill) — kalau layout baru selesai setelah draw
		# pertama, kartunya kosong. Digambar ulang tiap ukuran berubah.
		queue_redraw()


# ══════════════════════════════════════════════════════════
#  RENDER
# ══════════════════════════════════════════════════════════

func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	# ── bg gradasi / solid (cabang cheap_alpha pygame) ──
	if UiTheme.cheap_alpha():
		UiTheme.draw_vgrad(self, rect,
			COL_BUY_TOP if can_buy else COL_NO_TOP,
			COL_BUY_BOT if can_buy else COL_NO_BOT, CORNER_RADIUS)
	else:
		UiTheme.draw_rr(self, rect,
			COL_BUY_SOLID if can_buy else COL_NO_SOLID, CORNER_RADIUS)
	# ── border warna kelas + sudut emas ──
	var badge: Array = ItemDB.item_class_badge(item_id)
	UiTheme.draw_rr_outline(self, rect,
		ItemDB.item_color(item_id) if can_buy else COL_DEAD_BORDER,
		CORNER_RADIUS, 2.0)
	if can_buy:
		UiTheme.draw_corner_ticks(self, rect, UiTheme.GOLD, TICK_LEN, 2.0,
			2.0)
	# ── ikon 56 px ──
	if icon_texture != null:
		draw_texture_rect(icon_texture, Rect2(Vector2(ICON_X, ICON_Y),
			Vector2(ICON_SIZE, ICON_SIZE)), false)
	# ── badge kelas kanan-atas ──
	var bf := UiTheme.body_bold()
	var badge_w: float = bf.get_string_size(str(badge[0]),
		HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x + BADGE_PAD_X * 2.0
	var badge_rect := Rect2(Vector2(size.x - badge_w - BADGE_RIGHT, BADGE_TOP),
		Vector2(badge_w, BADGE_H))
	UiTheme.draw_rr(self, badge_rect, COL_BADGE_BG, 6.0)
	UiTheme.draw_rr_outline(self, badge_rect, badge[1] as Color, 6.0, 1.0)
	UiTheme.draw_text_centered(self, bf, str(badge[0]), 14, badge[1] as Color,
		badge_rect.get_center(), false)
	# ── nama (fit elipsis terhadap ruang yang tersisa) ──
	var nf := UiTheme.body_bold()
	var name_w := maxf(40.0, size.x - TEXT_X - 12.0 - badge_w - 8.0)
	UiTheme.draw_text(self, nf,
		UiTheme.fit_ellipsis(nf, 24, ItemDB.item_name(item_id), name_w), 24,
		ItemDB.item_glow(item_id), Vector2(TEXT_X, NAME_Y), false)
	# ── kategori ──
	var cf := UiTheme.body_bold()
	UiTheme.draw_text(self, cf,
		ItemDB.category_label(ItemDB.item_category(item_id)), 17,
		ItemDB.category_color(ItemDB.item_category(item_id)),
		Vector2(TEXT_X, CAT_Y), false)
	# ── harga ──
	UiTheme.draw_text(self, UiTheme.body_bold(),
		"%dG" % ItemDB.item_cost(item_id), 21,
		COL_GOLD_TEXT if can_buy else COL_COST_NO,
		Vector2(TEXT_X, COST_Y), false)
	# ── jumlah dimiliki ──
	if owned_count > 0:
		UiTheme.draw_text(self, UiTheme.body_bold(),
			MysticLocalization.tr_text("shop_card_owned") % owned_count, 17,
			COL_OWNED, Vector2(size.x - 90.0, OWNED_Y), false)
	# ── deskripsi ter-wrap (bahasa aktif) ──
	var df := UiTheme.body_medium()
	var lines := _wrap_text(ItemDB.item_desc_localized(item_id), df, 17,
		size.x - 20.0)
	if lines.size() > DESC_MAX_LINES:
		lines = lines.slice(0, DESC_MAX_LINES)
		var last: String = lines[DESC_MAX_LINES - 1]
		while last.length() > 1 and df.get_string_size(last + "…",
				HORIZONTAL_ALIGNMENT_LEFT, -1, 17).x > size.x - 20.0:
			last = last.substr(0, last.length() - 1)
		lines[DESC_MAX_LINES - 1] = last + "…"
	var ty := DESC_Y
	for line in lines:
		UiTheme.draw_text(self, df, line, 17, UiTheme.TEXT_BODY,
			Vector2(10.0, ty), false)
		ty += DESC_LINE_H


## Port `ItemShopUI._wrap_text` (hero_items.py:3897-3913): kata per kata,
## ukur dengan font yang sama seperti pygame mengukur.
static func _wrap_text(text: String, font: Font, size_px: int,
		max_w: float) -> Array:
	var lines: Array = []
	var cur := ""
	for word in text.split(" ", false):
		var test := (cur + " " + word).strip_edges()
		if font.get_string_size(test, HORIZONTAL_ALIGNMENT_LEFT, -1,
				size_px).x <= max_w:
			cur = test
		else:
			if cur != "":
				lines.append(cur)
			cur = word
	if cur != "":
		lines.append(cur)
	return lines
