@warning_ignore("inferred_declaration", "untyped_declaration")
extends Node2D
class_name ShopUI
## ITEM FORGE (biru 340,540) + HERO SHRINE (merah 940,180). H = item, klik gedung = sesuai warna.
## VISUAL 1:1 PYGAME: Panel 1100x720, kartu 250x200, ikon 56px, grid 4x2, 6 tab kelas, inv 6 slot (jual 70%).

const MAX_SLOTS := 6
const ITEMS_PER_PAGE := 8
const COLS_ITEM := 4
const ITEM_COST := 100

## 6 Halaman Toko Selaras Batas Kelas (Paritas 1:1 hero_items.py SHOP_PAGES)
const SHOP_PAGES: Array = [
	["dead_edge", "holy_rapier", "demon_maw", "cleave_axe", "moon_shard", "monarch_wings", "corroder", "fenrir_chain"],
	["sanguine_thorn", "thunder_coil", "sundering_cudgel", "frostbound_eye", "gale_pike", "basilisk_breath"],
	["octarine_core", "runic_gavel", "astral_codex", "sage_scepter", "fulgur_scepter", "hex_idol", "rift_veil", "vital_stone"],
	["vine_rod", "spectral_charm"],
	["leviathan_heart", "steel_aegis", "scarlet_bulwark", "tempest_vane", "abyss_breaker", "razor_carapace", "everfrost_guard", "solar_brand"],
	["searbrand"]
]

const PAGE_LABELS: Array = [
	"PHYSICAL 1/2", "PHYSICAL 2/2",
	"MAGIC 1/2", "MAGIC 2/2",
	"TANK 1/2", "TANK 2/2"
]

const PAGE_COLORS: Array = [
	Color8(255, 150, 80), Color8(255, 150, 80),
	Color8(200, 145, 255), Color8(200, 145, 255),
	Color8(115, 225, 145), Color8(115, 225, 145)
]

const ITEM_CATALOG := {
	"dead_edge": {"name":"Dead Edge","cost":100,"class":"PHYSICAL","color":Color8(220,60,60),"glow":Color8(255,90,90),"desc":"+52 Damage. 25% peluang Critical Strike (200% damage). Inti penyerang fisik.","dmg":52,"crit":0.25},
	"holy_rapier": {"name":"Holy Rapier","cost":100,"class":"PHYSICAL","color":Color8(255,220,80),"glow":Color8(255,245,150),"desc":"+120 Damage. HILANG saat hero mati (tidak bisa dipulihkan). Risiko tinggi, damage mutlak.","dmg":120},
	"demon_maw": {"name":"Demon Maw","cost":100,"class":"PHYSICAL","color":Color8(180,30,30),"glow":Color8(255,70,70),"desc":"+20 Damage, +4 Armor, 20% Lifesteal. Saat HP kritis: Blood Frenzy lifesteal lonjak.","dmg":20,"armor":4,"ls":0.2},
	"leviathan_heart": {"name":"Leviathan Heart","cost":100,"class":"TANK","color":Color8(80,220,120),"glow":Color8(130,255,160),"desc":"+35% Max HP, +6 HP/reg. Di luar pertempuran memulihkan 4% Max HP per detik.","hp_pct":0.35},
	"cleave_axe": {"name":"Cleave Axe","cost":100,"class":"PHYSICAL","color":Color8(200,220,240),"glow":Color8(150,210,255),"desc":"+34 Damage, +3 HP/reg. Serangan melee membelah 45% damage ke area sekitar (splash 180px).","dmg":34},
	"steel_aegis": {"name":"Steel Aegis","cost":100,"class":"TANK","color":Color8(180,200,230),"glow":Color8(120,170,255),"desc":"+4 Armor, +30 Attack Speed. Aura: sekutu dekat mendapat +4 Armor dan +20 AS.","armor":6,"as":30},
	"moon_shard": {"name":"Moon Shard","cost":100,"class":"PHYSICAL","color":Color8(130,220,255),"glow":Color8(180,240,255),"desc":"+75 Attack Speed. Serangan secepat kilat untuk trigger efek on-hit dan pasif bertubi-tubi.","as":75},
	"octarine_core": {"name":"Octarine Core","cost":100,"class":"MAGIC","color":Color8(180,80,230),"glow":Color8(220,130,255),"desc":"+300 HP, +2 HP/reg, 15% Cooldown Reduction, 8% Spell Vamp. Inti caster tangguh.","hp":300},
	"scarlet_bulwark": {"name":"Scarlet Bulwark","cost":111,"class":"TANK","color":Color8(200,60,60),"glow":Color8(255,110,110),"desc":"+250 HP, +8 HP/reg, +6 Armor. Blok pasif 55% damage serangan. Mengurangi burst musuh.","armor":6,"hp":250},
	"monarch_wings": {"name":"Monarch Wings","cost":111,"class":"PHYSICAL","color":Color8(230,140,220),"glow":Color8(255,190,250),"desc":"+38 Damage, +30 Attack Speed, 28% Evasion (peluang meleset musuh). Kelincahan absolut.","dmg":38,"as":30,"evasion":0.28},
	"corroder": {"name":"Corroder","cost":100,"class":"PHYSICAL","color":Color8(140,220,90),"glow":Color8(190,255,140),"desc":"+65 Damage. Serangan mengikis 6 Armor target selama 4 detik. Melemahkan tank lawan.","dmg":65},
	"tempest_vane": {"name":"Tempest Vane","cost":122,"class":"TANK","color":Color8(120,210,230),"glow":Color8(180,240,255),"desc":"+250 HP, +4 HP/reg, +12% Move Speed. Saat HP kritis: Tempest Veil kebal damage 2.5s.","hp":250,"ms":0.12},
	"fenrir_chain": {"name":"Fenrir Chain","cost":116,"class":"PHYSICAL","color":Color8(240,190,90),"glow":Color8(255,230,150),"desc":"+30 Damage, +30 AS, +250 HP. 20% serangan melepaskan Arc Chain ke 3 target (120 magic).","dmg":30,"as":30,"hp":250},
	"sanguine_thorn": {"name":"Sanguine Thorn","cost":133,"class":"PHYSICAL","color":Color8(230,60,110),"glow":Color8(255,120,160),"desc":"+25 Damage, +60 AS, +5 HP/reg. Soul Rend: tanda target, serangan berikutnya pasti crit 1.5x.","dmg":25,"as":60},
	"abyss_breaker": {"name":"Abyss Breaker","cost":122,"class":"TANK","color":Color8(90,130,220),"glow":Color8(140,180,255),"desc":"+35 Damage, +300 HP, +16% heal diterima, +30% tahan slow. 22% bash stun 1.1s.","dmg":35,"hp":300},
	"thunder_coil": {"name":"Thunder Coil","cost":116,"class":"PHYSICAL","color":Color8(250,220,90),"glow":Color8(255,245,160),"desc":"+25 Damage, +65 AS. 22% serangan menyambar 3 musuh rantai listrik petir.","dmg":25,"as":65},
	"razor_carapace": {"name":"Razor Carapace","cost":111,"class":"TANK","color":Color8(180,180,200),"glow":Color8(230,230,255),"desc":"+18 Damage, +8 Armor, 10% CDR. Saat HP < 55%: pantulkan 40% damage balik ke musuh.","dmg":18,"armor":8},
	"everfrost_guard": {"name":"Everfrost Guard","cost":122,"class":"TANK","color":Color8(120,190,230),"glow":Color8(180,230,255),"desc":"+10 Armor, +5 HP/reg, 10% CDR. Aura: musuh dekat diperlambat AS 25% dan anti-heal 30%.","armor":10},
	"sundering_cudgel": {"name":"Sundering Cudgel","cost":111,"class":"PHYSICAL","color":Color8(230,180,70),"glow":Color8(255,220,130),"desc":"+45 Damage, +25 AS. Serangan TIDAK BISA meleset. 28% peluang pierce bash stun 1.0s.","dmg":48,"as":25},
	"frostbound_eye": {"name":"Frostbound Eye","cost":116,"class":"PHYSICAL","color":Color8(120,200,220),"glow":Color8(180,240,255),"desc":"+20 Damage, +250 HP, +4 HP/reg. Tiap serangan memperlambat gerak dan serang musuh 20%.","dmg":20,"hp":250},
	"gale_pike": {"name":"Gale Pike","cost":116,"class":"PHYSICAL","color":Color8(150,230,200),"glow":Color8(200,255,230),"desc":"+18 Damage, +25 AS, +200 HP, +3 HP/reg, +90 Attack Range untuk serangan jarak jauh.","dmg":18,"as":25,"hp":200},
	"basilisk_breath": {"name":"Basilisk Breath","cost":127,"class":"PHYSICAL","color":Color8(140,210,90),"glow":Color8(190,255,130),"desc":"+26 Damage, +30 AS, +260 HP, +3 HP/reg. Serangan menyembur racun Miasma & multishot 30%.","dmg":26,"as":30,"hp":260},
	"solar_brand": {"name":"Solar Brand","cost":122,"class":"TANK","color":Color8(255,190,60),"glow":Color8(255,230,140),"desc":"+30 Damage, +280 HP, +5 HP/reg. Aura: musuh dekat terbakar 38 dps dan miss 16%.","dmg":30,"hp":280},
	"runic_gavel": {"name":"Runic Gavel","cost":116,"class":"MAGIC","color":Color8(200,130,240),"glow":Color8(235,180,255),"desc":"+28 Damage, +250 HP, +4 HP/reg, 15% CDR. Setiap 9 detik: pukulan ekstra 130 magic damage.","dmg":28,"hp":250},
	"searbrand": {"name":"Searbrand","cost":127,"class":"TANK","color":Color8(235,95,60),"glow":Color8(255,150,110),"desc":"+12 Damage, +320 HP, +6 HP/reg, 15% CDR. AURA: bakar 50 dps dan 45% anti-heal ke sekitar.","dmg":20,"hp":320},
	"astral_codex": {"name":"Astral Codex","cost":133,"class":"MAGIC","color":Color8(155,90,235),"glow":Color8(210,155,255),"desc":"+280 HP, +4 HP/reg, 18% CDR, 12% Spell Vamp. Magic Only: ledakan supernova area luas.","hp":280},
	"sage_scepter": {"name":"Sage Scepter","cost":111,"class":"MAGIC","color":Color8(120,190,255),"glow":Color8(170,220,255),"desc":"+200 HP, +3 HP/reg, 15% SKILL AMP, 8% Spell Vamp. Memperkuat daya rusak skill.","hp":200},
	"fulgur_scepter": {"name":"Fulgur Scepter","cost":133,"class":"MAGIC","color":Color8(255,180,60),"glow":Color8(255,220,120),"desc":"+15 Damage, +200 HP, 10% SKILL AMP, 8% Spell Vamp. Petir menggelegar ke target.","dmg":15,"hp":200},
	"hex_idol": {"name":"Hex Idol","cost":127,"class":"MAGIC","color":Color8(170,220,90),"glow":Color8(210,255,140),"desc":"+250 HP, +4 HP/reg, 6% Spell Vamp, 10% CDR. Mengutuk musuh nearby melambat dan lemah.","hp":250},
	"rift_veil": {"name":"Rift Veil","cost":122,"class":"MAGIC","color":Color8(130,120,240),"glow":Color8(180,170,255),"desc":"+260 HP, +4 HP/reg, 6% Spell Vamp. Saat terancam membuka portal kabur singkat.","hp":260},
	"vital_stone": {"name":"Vital Stone","cost":116,"class":"MAGIC","color":Color8(230,80,110),"glow":Color8(255,140,170),"desc":"+320 HP, +6 HP/reg, 20% Spell Vamp. Mengubah daya magis menjadi daya tahan tubuh.","hp":320},
	"vine_rod": {"name":"Vine Rod","cost":111,"class":"MAGIC","color":Color8(90,200,120),"glow":Color8(150,240,170),"desc":"+15 Damage, +240 HP, +3 HP/reg, 5% Spell Vamp. 25% serangan menjerat root musuh 1.5s.","dmg":15,"hp":240},
	"spectral_charm": {"name":"Spectral Charm","cost":122,"class":"MAGIC","color":Color8(190,220,255),"glow":Color8(225,240,255),"desc":"+230 HP, +3 HP/reg, +10% Move Speed, 6% Spell Vamp. Efek tembus unit saat berlari.","hp":230,"ms":0.1},
}
const CATALOG := ITEM_CATALOG

const HERO_CATALOG := {
	"kaizen": {"name":"Kaizen","cost":100,"color":Color8(79,195,247),"glow":Color8(120,220,255),"desc":"550 HP · 22 DMG · Seimbang (Warrior)","hp":550,"dmg":22,"range":90,"move_speed":120.0,"color_hex":"#4FC3F7"},
	"krobellus": {"name":"Krobellus","cost":120,"color":Color8(200,80,80),"glow":Color8(255,120,120),"desc":"600 HP · 20 DMG · Daya Tahan Kuat (Tank)","hp":600,"dmg":20,"range":95,"move_speed":115.0,"color_hex":"#C94A4A"},
	"grimjaw": {"name":"Grimjaw","cost":120,"color":Color8(126,217,87),"glow":Color8(170,240,130),"desc":"480 HP · 26 DMG · Kecepatan Tinggi (Assassin)","hp":480,"dmg":26,"range":85,"move_speed":135.0,"color_hex":"#7ED957"},
	"vex": {"name":"Vex","cost":150,"color":Color8(160,120,255),"glow":Color8(190,160,255),"desc":"520 HP · 24 DMG · Daya Rusak Magis (Mage)","hp":520,"dmg":24,"range":110,"move_speed":120.0,"color_hex":"#A078FF"},
}

var _main = null
var open = false
var mode = "item" # item | hero
var _close_rect = Rect2()
var _page: int = 0
var _tab_rects: Array = []
var _buy_rects: Dictionary = {}
var _card_rects: Dictionary = {}
var _hero_buy_rects: Dictionary = {}
var _inv_rects: Dictionary = {}
var _inspect_item: String = ""
var _detail_close_rect = Rect2()
var _icon_cache: Dictionary = {}


func setup(main_ref) -> void:
	_main = main_ref
	z_index = 60
	visible = false


func toggle() -> void:
	toggle_mode("item")


func toggle_mode(requested_mode: String) -> void:
	if open and mode == requested_mode:
		open = false
		visible = false
		_inspect_item = ""
	else:
		mode = requested_mode
		if mode == "item":
			_page = 0
		_inspect_item = ""
		open = true
		visible = true
	if _main != null:
		_main.queue_redraw()
	var label = "ITEM FORGE" if mode == "item" else "HERO SHRINE"
	print("[Shop] %s %s" % [label, ("BUKA" if open else "TUTUP")])


func is_open() -> bool:
	return open


func _get_item_texture(id: String) -> Texture2D:
	if _icon_cache.has(id):
		return _icon_cache[id]
	var path := "res://assets/items/%s.png" % id
	if ResourceLoader.exists(path):
		var tex = load(path)
		if tex is Texture2D:
			_icon_cache[id] = tex
			return tex
	_icon_cache[id] = null
	return null


func draw_on(host: CanvasItem) -> void:
	if not open:
		return

	# Overlay Gelap Layar Penuh (Paritas darken 215 pygame)
	host.draw_rect(Rect2(0, 0, 1280, 720), Color(0.0, 0.0, 0.0, 0.84))

	# Geometri Panel 1100 x 720 px (Center pada 1280 x 720: px=90, py=0)
	var pw: float = 1100.0
	var ph: float = 720.0
	var px: float = (1280.0 - pw) * 0.5
	var py: float = (720.0 - ph) * 0.5

	# Shadow Panel
	host.draw_rect(Rect2(px - 10, py - 10, pw + 20, ph + 20), Color(0.0, 0.0, 0.0, 0.63))

	# Panel Background (Paritas gradasi / solid pygame)
	host.draw_rect(Rect2(px, py, pw, ph), Color8(22, 26, 44))

	# Border Emas Luar & Dalam
	var edge: Color = Color8(255, 205, 90) if mode == "item" else Color8(255, 120, 120)
	host.draw_rect(Rect2(px, py, pw, ph), edge, false, 3.0)
	host.draw_rect(Rect2(px + 3, py + 3, pw - 6, ph - 6), Color8(140, 110, 58), false, 1.0)

	# Corner Ticks (Sudut Emas 16 px)
	_draw_corner_ticks(host, Rect2(px, py, pw, ph), Color8(255, 230, 140), 16.0, 2.0, 8.0)

	var font: Font = ThemeDB.fallback_font

	# Header: Judul & Emas
	var title: String = "ITEM FORGE" if mode == "item" else "HERO SHRINE"
	var tcol: Color = Color8(255, 220, 100) if mode == "item" else Color8(255, 160, 160)
	host.draw_string(font, Vector2(px + pw * 0.5 - 75, py + 32), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, tcol)

	var gold_s: String = "GOLD %d" % int(_main.gold) if _main != null else "GOLD 0"
	host.draw_string(font, Vector2(px + 24, py + 32), gold_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color8(255, 220, 100))

	# Hint Detail di kanan sebelum tombol X
	var hint_s := "Ketuk kartu: detail · Klik kanan slot: JUAL 70%" if mode == "item" else "Pilih hero untuk rekrut"
	host.draw_string(font, Vector2(px + pw - 380, py + 32), hint_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color8(170, 180, 205))

	# Tombol Tutup X (Lingkaran Merah 38 px)
	_close_rect = Rect2(px + pw - 48, py + 8, 38, 38)
	host.draw_rect(_close_rect, Color8(180, 60, 60))
	host.draw_rect(_close_rect, Color.WHITE, false, 2.0)
	host.draw_string(font, Vector2(_close_rect.position.x + 12, _close_rect.position.y + 26), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)

	if mode == "hero":
		_draw_hero_grid(host, px, py, pw, ph, font)
	else:
		_draw_hero_info_bar(host, px, py + 48, pw - 40, 42, font)
		_draw_page_tabs(host, px, py + 96, pw, font)
		_draw_item_grid(host, px, py, pw, ph, font)
		_draw_inventory_strip(host, px, py + ph - 74, pw, font)

	# Modal Detail Item Popup (Jika sedang menginspeksi item)
	if _inspect_item != "" and ITEM_CATALOG.has(_inspect_item):
		_draw_detail_modal(host, font)


func _draw_corner_ticks(host: CanvasItem, rect: Rect2, color: Color, length: float, width: float, inset: float) -> void:
	var x1 := rect.position.x + inset
	var y1 := rect.position.y + inset
	var x2 := rect.position.x + rect.size.x - inset
	var y2 := rect.position.y + rect.size.y - inset
	# Top-Left
	host.draw_line(Vector2(x1, y1), Vector2(x1 + length, y1), color, width)
	host.draw_line(Vector2(x1, y1), Vector2(x1, y1 + length), color, width)
	# Top-Right
	host.draw_line(Vector2(x2, y1), Vector2(x2 - length, y1), color, width)
	host.draw_line(Vector2(x2, y1), Vector2(x2, y1 + length), color, width)
	# Bottom-Left
	host.draw_line(Vector2(x1, y2), Vector2(x1 + length, y2), color, width)
	host.draw_line(Vector2(x1, y2), Vector2(x1, y2 - length), color, width)
	# Bottom-Right
	host.draw_line(Vector2(x2, y2), Vector2(x2 - length, y2), color, width)
	host.draw_line(Vector2(x2, y2), Vector2(x2, y2 - length), color, width)


## Baris Ringkasan Hero Aktif (Paritas _draw_hero_info pygame)
func _draw_hero_info_bar(host: CanvasItem, x: float, y: float, w: float, h: float, font: Font) -> void:
	var box := Rect2(x + 20, y, w, h)
	host.draw_rect(box, Color8(30, 36, 58))
	host.draw_rect(box, Color8(79, 195, 247), false, 2.0)
	if _main != null and _main.hero != null:
		var hero = _main.hero
		var hname: String = str(hero.hero_name)
		var hlv: int = int(hero.get("level") if "level" in hero else 1)
		var dmg: int = int(hero.damage)
		var hp: int = int(hero.hp)
		var max_hp: int = int(hero.max_hp)
		var arm: int = int(hero.get("bonus_armor") if "bonus_armor" in hero else 0)
		var as_pct: float = 1.0 / (float(hero.attack_interval) if float(hero.attack_interval) > 0.0 else 1.0)
		var ls: int = int((hero.get("lifesteal") if "lifesteal" in hero else 0.0) * 100.0)
		host.draw_string(font, Vector2(box.position.x + 12, box.position.y + 18),
			"%s  Lv.%d" % [hname, hlv], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color8(79, 195, 247))
		var stat_txt := "HP %d/%d   DMG %d   Armor %d   AS x%.2f   LS %d%%" % [hp, max_hp, dmg, arm, as_pct, ls]
		host.draw_string(font, Vector2(box.position.x + 12, box.position.y + 34),
			stat_txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(200, 210, 230))
	else:
		host.draw_string(font, Vector2(box.position.x + 12, box.position.y + 26),
			"BELUM ADA HERO — Item dapat dilihat dan dibeli untuk disimpan",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color8(255, 190, 190))


## 6 Tab Kelas Paginasi (PHYSICAL 1/2, 2/2, MAGIC 1/2, 2/2, TANK 1/2, 2/2)
func _draw_page_tabs(host: CanvasItem, px: float, py: float, pw: float, font: Font) -> void:
	_tab_rects.clear()
	var tab_count := SHOP_PAGES.size()
	var tab_w := 154.0
	var tab_h := 30.0
	var gap := 8.0
	var total_w := float(tab_count) * tab_w + float(tab_count - 1) * gap
	var sx := px + (pw - total_w) * 0.5

	for i in tab_count:
		var r := Rect2(sx + float(i) * (tab_w + gap), py, tab_w, tab_h)
		_tab_rects.append(r)
		var is_cur := (i == _page)
		var col: Color = PAGE_COLORS[i]
		var bg := Color8(40, 52, 84) if is_cur else Color8(22, 26, 40)
		host.draw_rect(r, bg)
		host.draw_rect(r, col if is_cur else Color8(60, 68, 92), false, 2.0 if is_cur else 1.0)
		var label: String = PAGE_LABELS[i]
		var tw := font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
		host.draw_string(font, Vector2(r.position.x + (tab_w - tw) * 0.5, r.position.y + 19),
			label, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color.WHITE if is_cur else col)


## Grid 4x2 Kartu Item Forge 250px x 200px (Paritas 1:1 ItemShopUI._draw_item_grid)
func _draw_item_grid(host: CanvasItem, px: float, py: float, pw: float, _ph: float, font: Font) -> void:
	var cols: int = COLS_ITEM
	var cw: float = 250.0
	var ch: float = 200.0
	var gap_x: float = 12.0
	var gap_y: float = 14.0
	var grid_w := float(cols) * cw + float(cols - 1) * gap_x
	var sx := px + (pw - grid_w) * 0.5
	var sy := py + 134.0

	_buy_rects.clear()
	_card_rects.clear()

	if _page < 0 or _page >= SHOP_PAGES.size():
		_page = 0
	var page_items: Array = SHOP_PAGES[_page]

	for i in page_items.size():
		var r: int = i / cols
		var c: int = i % cols
		var x: float = sx + float(c) * (cw + gap_x)
		var y: float = sy + float(r) * (ch + gap_y)
		var id: String = page_items[i]
		var data: Dictionary = ITEM_CATALOG[id]
		var owned: int = _count_owned(id)
		var can_buy: bool = _can_buy(id)

		var card_rect := Rect2(x, y, cw, ch)
		_card_rects[id] = card_rect

		# Background kartu gradasi / solid
		var bg := Color8(34, 40, 68) if can_buy else Color8(26, 26, 38)
		host.draw_rect(card_rect, bg)

		# Border kartu
		var border: Color = data["color"] if can_buy else Color8(70, 70, 80)
		host.draw_rect(card_rect, border, false, 2.0)

		# Sudut Emas (Corner Ticks) jika mampu beli
		if can_buy:
			_draw_corner_ticks(host, card_rect, Color8(255, 205, 90), 9.0, 1.5, 2.0)

		# Ikon 56 x 56 px
		var tex := _get_item_texture(id)
		var icon_rect := Rect2(x + 10, y + 10, 56, 56)
		if tex != null:
			host.draw_texture_rect(tex, icon_rect, false)
		else:
			host.draw_rect(icon_rect, data["color"])
			host.draw_rect(icon_rect, data["glow"], false, 2.0)

		# Badge Kelas di Kanan Atas
		var cls_name: String = str(data.get("class", "PHYSICAL"))
		var cls_col: Color = PAGE_COLORS[_page]
		var badge_rect := Rect2(x + cw - 88, y + 8, 80, 20)
		host.draw_rect(badge_rect, Color8(18, 22, 36))
		host.draw_rect(badge_rect, cls_col, false, 1.0)
		var btw := font.get_string_size(cls_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x
		host.draw_string(font, Vector2(badge_rect.position.x + (80 - btw) * 0.5, y + 22),
			cls_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, cls_col)

		# Nama Item (Font 14 Bold Glow)
		host.draw_string(font, Vector2(x + 74, y + 24), str(data["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, data["glow"])

		# Harga Item
		var cost_col: Color = Color8(255, 220, 100) if can_buy else Color8(200, 80, 80)
		host.draw_string(font, Vector2(x + 74, y + 44), "%d G" % int(data["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, cost_col)

		# Jumlah Dimiliki
		if owned > 0:
			host.draw_string(font, Vector2(x + cw - 88, y + 44), "x%d" % owned, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(150, 255, 170))

		# Baris Stat Singkat
		var stxt := ""
		if data.has("dmg"): stxt += "+%d dmg " % int(data["dmg"])
		if data.has("hp"): stxt += "+%d hp " % int(data["hp"])
		if data.has("hp_pct"): stxt += "+%d%% hp " % int(float(data["hp_pct"]) * 100)
		if data.has("armor"): stxt += "+%d arm " % int(data["armor"])
		if data.has("as"): stxt += "+%d as " % int(data["as"])
		if data.has("ls"): stxt += "+%d%% ls " % int(float(data["ls"]) * 100)
		host.draw_string(font, Vector2(x + 74, y + 60), stxt.strip_edges(), HORIZONTAL_ALIGNMENT_LEFT, -1, 10,
			Color8(170, 255, 170) if stxt != "" else Color8(200, 210, 230))

		# Deskripsi Terbungkus (3-4 Baris)
		var desc: String = str(data["desc"])
		var desc_lines := _wrap_text(desc, 34)
		var dy := y + 80
		for dl in desc_lines.slice(0, 4):
			host.draw_string(font, Vector2(x + 10, dy), dl, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color8(200, 210, 230))
			dy += 15

		# Tombol BUY (Pill Bawah Kartu)
		var btn := Rect2(x + 10, y + ch - 32, cw - 20, 24)
		_buy_rects[id] = btn
		if can_buy:
			host.draw_rect(btn, Color8(48, 100, 64))
			host.draw_rect(btn, Color8(120, 235, 140), false, 1.5)
			var tw := font.get_string_size("BUY", HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
			host.draw_string(font, Vector2(btn.position.x + (btn.size.x - tw) * 0.5, btn.position.y + 17),
				"BUY", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
		else:
			host.draw_rect(btn, Color8(44, 44, 54))
			host.draw_rect(btn, Color8(90, 90, 100), false, 1.0)
			var label: String = "FULL" if _is_full() else ("GOLD -" if _main != null and int(_main.gold) < int(data["cost"]) else "BUY")
			var tw := font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
			host.draw_string(font, Vector2(btn.position.x + (btn.size.x - tw) * 0.5, btn.position.y + 16),
				label, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(170, 170, 180))


## Strip 6 Slot Inventory di Bawah (Paritas _draw_owned_slots pygame: 54x54 px)
func _draw_inventory_strip(host: CanvasItem, px: float, inv_y: float, pw: float, font: Font) -> void:
	_inv_rects.clear()
	var inv: Array = _main.hero.get("inventory") if _main != null and _main.hero != null and "inventory" in _main.hero else []

	var label_txt := "INVENTORY %d/%d  ·  (Klik kanan slot untuk JUAL refund 70%%)" % [inv.size(), MAX_SLOTS]
	host.draw_string(font, Vector2(px + 32, inv_y - 8), label_txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(170, 180, 205))

	var slot_size := 54.0
	var gap := 8.0
	var total_w := float(MAX_SLOTS) * slot_size + float(MAX_SLOTS - 1) * gap
	var sx2 := px + (pw - total_w) * 0.5

	for i in MAX_SLOTS:
		var r := Rect2(sx2 + float(i) * (slot_size + gap), inv_y, slot_size, slot_size)
		_inv_rects[i] = r
		host.draw_rect(r, Color8(14, 17, 30))

		var slot_item: Variant = null
		if i < inv.size():
			slot_item = inv[i]

		var col: Color = Color8(66, 74, 104)
		if slot_item != null:
			var d: Dictionary = ITEM_CATALOG.get(str(slot_item), {})
			col = d.get("color", col)
			var tex := _get_item_texture(str(slot_item))
			var icon_box := Rect2(r.position.x + 3, r.position.y + 3, 48, 48)
			if tex != null:
				host.draw_texture_rect(tex, icon_box, false)
			else:
				host.draw_rect(icon_box, col)

			# Badge kecil tanda jual 70% di pojok slot
			host.draw_rect(Rect2(r.position.x + slot_size - 14, r.position.y + 2, 12, 12), Color8(180, 60, 60, 0.9))
			host.draw_string(font, Vector2(r.position.x + slot_size - 11, r.position.y + 11), "x", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color.WHITE)

		host.draw_rect(r, col, false, 2.0 if slot_item != null else 1.0)


## Modal Popup Detail Item (Paritas _draw_detail_popup pygame: 880x520 px)
func _draw_detail_modal(host: CanvasItem, font: Font) -> void:
	var sid := _inspect_item
	if not ITEM_CATALOG.has(sid):
		return
	var data: Dictionary = ITEM_CATALOG[sid]

	# Dimensi Popup
	var dw: float = 880.0
	var dh: float = 520.0
	var dx: float = (1280.0 - dw) * 0.5
	var dy: float = (720.0 - dh) * 0.5
	var drect := Rect2(dx, dy, dw, dh)

	# Shadow & Panel
	host.draw_rect(Rect2(dx - 8, dy - 8, dw + 16, dh + 16), Color(0.0, 0.0, 0.0, 0.7))
	host.draw_rect(drect, Color8(24, 28, 48))
	host.draw_rect(drect, Color8(255, 205, 90), false, 3.0)
	_draw_corner_ticks(host, drect, Color8(255, 230, 140), 16.0, 2.0, 6.0)

	# Ikon 64 x 64 px
	var tex := _get_item_texture(sid)
	var icon_box := Rect2(dx + 24, dy + 20, 64, 64)
	if tex != null:
		host.draw_texture_rect(tex, icon_box, false)
	else:
		host.draw_rect(icon_box, data["color"])
		host.draw_rect(icon_box, data["glow"], false, 2.0)

	# Nama & Kelas
	host.draw_string(font, Vector2(dx + 104, dy + 42), str(data["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 24, data["glow"])
	var cls_str: String = str(data.get("class", "PHYSICAL"))
	host.draw_string(font, Vector2(dx + 104, dy + 68), "KELAS: %s" % cls_str, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color8(255, 150, 80))

	# Harga
	host.draw_string(font, Vector2(dx + dw - 160, dy + 42), "%d GOLD" % int(data["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color8(255, 220, 100))

	# Garis Pemisah
	host.draw_line(Vector2(dx + 24, dy + 100), Vector2(dx + dw - 24, dy + 100), Color8(70, 78, 110), 1.0)

	# Deskripsi Lengkap
	host.draw_string(font, Vector2(dx + 24, dy + 128), "DESKRIPSI & MEKANIK:", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color8(255, 205, 90))
	var desc_lines := _wrap_text(str(data["desc"]), 90)
	var ly := dy + 152
	for line in desc_lines:
		host.draw_string(font, Vector2(dx + 24, ly), line, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(220, 225, 240))
		ly += 18

	# Stat Spesifik
	ly += 10
	host.draw_string(font, Vector2(dx + 24, ly), "ATRIBUT BONUS:", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color8(255, 205, 90))
	ly += 22
	if data.has("dmg"):
		host.draw_string(font, Vector2(dx + 24, ly), "• Bonus Damage: +%d" % int(data["dmg"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(200, 210, 230))
		ly += 18
	if data.has("hp"):
		host.draw_string(font, Vector2(dx + 24, ly), "• Bonus Max HP: +%d" % int(data["hp"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(200, 210, 230))
		ly += 18
	if data.has("hp_pct"):
		host.draw_string(font, Vector2(dx + 24, ly), "• Pengali Max HP: +%d%%" % int(float(data["hp_pct"]) * 100), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(200, 210, 230))
		ly += 18
	if data.has("armor"):
		host.draw_string(font, Vector2(dx + 24, ly), "• Bonus Armor: +%d" % int(data["armor"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(200, 210, 230))
		ly += 18
	if data.has("as"):
		host.draw_string(font, Vector2(dx + 24, ly), "• Attack Speed: +%d" % int(data["as"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(200, 210, 230))
		ly += 18
	if data.has("ls"):
		host.draw_string(font, Vector2(dx + 24, ly), "• Lifesteal: +%d%%" % int(float(data["ls"]) * 100), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(200, 210, 230))
		ly += 18
	if data.has("crit"):
		host.draw_string(font, Vector2(dx + 24, ly), "• Peluang Critical: +%d%% (200%% dmg)" % int(float(data["crit"]) * 100), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(200, 210, 230))
		ly += 18

	# Tombol X Tutup Modal
	_detail_close_rect = Rect2(dx + dw - 44, dy + 16, 32, 32)
	host.draw_rect(_detail_close_rect, Color8(180, 60, 60))
	host.draw_rect(_detail_close_rect, Color.WHITE, false, 2.0)
	host.draw_string(font, Vector2(_detail_close_rect.position.x + 10, _detail_close_rect.position.y + 22), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)

	# Hint Tutup
	host.draw_string(font, Vector2(dx + dw * 0.5 - 100, dy + dh - 16), "Ketuk di mana pun untuk menutup info", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(150, 160, 190))


func _wrap_text(text: String, chars_per_line: int) -> Array:
	var words := text.split(" ")
	var lines: Array = []
	var cur := ""
	for w in words:
		if (cur + " " + w).length() <= chars_per_line:
			cur = (cur + " " + w).strip_edges()
		else:
			if cur != "":
				lines.append(cur)
			cur = w
	if cur != "":
		lines.append(cur)
	return lines


## Grid Hero Shrine
func _draw_hero_grid(host: CanvasItem, px: float, py: float, pw: float, _ph: float, font: Font) -> void:
	_buy_rects.clear()
	_hero_buy_rects.clear()
	_inv_rects.clear()

	var ids = HERO_CATALOG.keys()
	var cols = 4
	var cw: float = 250.0
	var ch = 200.0
	var gap: float = 12.0
	var sx: float = px + (pw - (float(cols) * cw + float(cols - 1) * gap)) * 0.5
	var sy: float = py + 134.0

	for i in ids.size():
		var r: int = i / cols
		var c: int = i % cols
		var x: float = sx + float(c) * (cw + gap)
		var y: float = sy + float(r) * (ch + gap)
		var id: String = ids[i]
		var data: Dictionary = HERO_CATALOG[id]
		var can_buy = _can_buy_hero(id)
		var is_current: bool = _main != null and _main.hero != null and str(_main.hero.hero_id) == id

		var bg = Color8(40, 30, 40) if is_current else (Color8(34, 40, 68) if can_buy else Color8(30, 30, 38))
		host.draw_rect(Rect2(x, y, cw, ch), bg)
		var border: Color = Color8(255, 220, 100) if is_current else (data["glow"] if can_buy else Color8(80, 80, 90))
		host.draw_rect(Rect2(x, y, cw, ch), border, false, 2.5 if is_current else 2.0)

		# Hero Circle Avatar
		host.draw_circle(Vector2(x + cw * 0.5, y + 44), 26, Color(0, 0, 0, 0.35))
		host.draw_circle(Vector2(x + cw * 0.5, y + 42), 24, data["color"])

		host.draw_string(font, Vector2(x + 14, y + 90), str(data["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, data["glow"] if not is_current else Color8(255, 220, 100))
		host.draw_string(font, Vector2(x + 14, y + 110), str(data["desc"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(200, 210, 230))
		host.draw_string(font, Vector2(x + 14, y + 130), "%d GOLD" % int(data["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color8(255, 220, 100) if can_buy else Color8(200, 80, 80))

		if is_current:
			host.draw_string(font, Vector2(x + cw - 70, y + 130), "AKTIF", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(150, 255, 170))

		var btn := Rect2(x + 10, y + ch - 34, cw - 20, 26)
		_hero_buy_rects[id] = btn
		if is_current:
			host.draw_rect(btn, Color8(60, 60, 70))
			host.draw_rect(btn, Color8(120, 120, 130), false, 1.0)
			var tw := font.get_string_size("AKTIF", HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
			host.draw_string(font, Vector2(btn.position.x + (btn.size.x - tw) * 0.5, btn.position.y + 17), "AKTIF", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(170, 170, 180))
		elif can_buy:
			host.draw_rect(btn, Color8(80, 40, 40))
			host.draw_rect(btn, Color8(255, 120, 120), false, 1.5)
			var tw := font.get_string_size("GANTI HERO", HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
			host.draw_string(font, Vector2(btn.position.x + (btn.size.x - tw) * 0.5, btn.position.y + 17), "GANTI HERO", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
		else:
			host.draw_rect(btn, Color8(44, 44, 54))
			host.draw_rect(btn, Color8(90, 90, 100), false, 1.0)
			var tw := font.get_string_size("GOLD -", HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
			host.draw_string(font, Vector2(btn.position.x + (btn.size.x - tw) * 0.5, btn.position.y + 17), "GOLD -", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(170, 170, 180))


func handle_click(point: Vector2) -> bool:
	if not open:
		return false

	# Jika modal detail terbuka, cek klik tutup
	if _inspect_item != "":
		if _detail_close_rect.has_point(point):
			_inspect_item = ""
			Sound.play("click")
			_main.queue_redraw()
			return true
		# Klik di luar / di dalam modal menutup modal
		_inspect_item = ""
		Sound.play("click")
		_main.queue_redraw()
		return true

	# Tombol Tutup Panel
	if _close_rect.has_point(point):
		toggle_mode(mode)
		Sound.play("click")
		return true

	if mode == "hero":
		for id in _hero_buy_rects.keys():
			var r: Rect2 = _hero_buy_rects[id]
			if r.has_point(point):
				_try_buy_hero(str(id))
				return true
	else:
		# Tab Kelas Paginasi
		for i in _tab_rects.size():
			var r: Rect2 = _tab_rects[i]
			if r.has_point(point):
				_page = i
				Sound.play("click")
				_main.queue_redraw()
				return true

		# Tombol BUY kartu
		for id in _buy_rects.keys():
			var r: Rect2 = _buy_rects[id]
			if r.has_point(point):
				_try_buy(str(id))
				return true

		# Klik bodi kartu item = buka popup detail
		for id in _card_rects.keys():
			var r: Rect2 = _card_rects[id]
			if r.has_point(point):
				_inspect_item = str(id)
				Sound.play("click")
				_main.queue_redraw()
				return true

		# Klik kiri slot inventory = buka detail item
		for idx in _inv_rects.keys():
			var r: Rect2 = _inv_rects[idx]
			if r.has_point(point):
				if _main != null and _main.hero != null:
					var inv: Array = _main.hero.get("inventory") if "inventory" in _main.hero else []
					if int(idx) < inv.size():
						_inspect_item = str(inv[int(idx)])
						Sound.play("click")
						_main.queue_redraw()
						return true

	# Klik di dalam panel = tahan
	var pw: float = 1100.0
	var ph: float = 720.0
	var px: float = (1280.0 - pw) * 0.5
	var py: float = (720.0 - ph) * 0.5
	if Rect2(px, py, pw, ph).has_point(point):
		return true

	# Klik di luar panel = tutup
	toggle_mode(mode)
	return true


func handle_right_click(point: Vector2) -> bool:
	if not open:
		return false
	if mode != "item":
		return false

	# Klik kanan slot inventory = JUAL refund 70%
	for idx in _inv_rects.keys():
		var r: Rect2 = _inv_rects[idx]
		if r.has_point(point):
			_try_sell(int(idx))
			return true

	var pw: float = 1100.0
	var ph: float = 720.0
	var px: float = (1280.0 - pw) * 0.5
	var py: float = (720.0 - ph) * 0.5
	if Rect2(px, py, pw, ph).has_point(point):
		return true
	return false


## Jual Item (Refund 70% Harga Beli)
func _try_sell(slot_idx: int) -> void:
	if _main == null or _main.hero == null:
		return
	var inv: Array = _main.hero.get("inventory") if "inventory" in _main.hero else []
	if slot_idx < 0 or slot_idx >= inv.size():
		Sound.play("error")
		return
	var id: String = str(inv[slot_idx])
	var data: Dictionary = ITEM_CATALOG.get(id, {})
	if data.is_empty():
		return
	var cost: int = int(data.get("cost", 100))
	var refund: int = int(cost * 0.7)
	inv.remove_at(slot_idx)
	_revert_stats(_main.hero, data)
	_main.gold += refund
	Sound.play("click")
	print("[Shop] %s jual %s (+%d G) sisa %d" % [_main.hero.hero_name, str(data["name"]), refund, int(_main.gold)])
	_main.queue_redraw()


func _revert_stats(hero, data: Dictionary) -> void:
	if data.has("dmg"):
		hero.damage = maxf(1.0, hero.damage - float(data["dmg"]))
	if data.has("hp"):
		var sub: float = float(data["hp"])
		hero.max_hp = maxf(1.0, hero.max_hp - sub)
		hero.hp = minf(hero.hp, hero.max_hp)
		hero.hp = maxf(1.0, hero.hp)
	if data.has("hp_pct"):
		var pct: float = float(data["hp_pct"])
		var cur: float = float(hero.max_hp)
		var add: float = cur * pct / (1.0 + pct)
		hero.max_hp = maxf(1.0, cur - add)
		hero.hp = minf(hero.hp, hero.max_hp)
	if data.has("armor"):
		if "bonus_armor" in hero:
			hero.bonus_armor = maxf(0.0, hero.bonus_armor - float(data["armor"]))
	if data.has("as"):
		if "bonus_as" in hero:
			hero.bonus_as = maxf(0.0, hero.bonus_as - float(data["as"]))
		hero.attack_interval = maxf(0.20, 1.0 / (1.0 + hero.bonus_as / 100.0)) if hero.bonus_as > 0 else 1.0
	if data.has("ls"):
		if "lifesteal" in hero:
			hero.lifesteal = maxf(0.0, hero.lifesteal - float(data["ls"]))
	if data.has("crit") and hero.get("crit_chance") != null:
		hero.set("crit_chance", maxf(0.0, float(hero.get("crit_chance")) - float(data["crit"])))
	if data.has("evasion") and hero.get("evasion") != null:
		hero.set("evasion", maxf(0.0, float(hero.get("evasion")) - float(data["evasion"])))
	if data.has("ms"):
		hero.move_speed = hero.move_speed / (1.0 + float(data["ms"]))
	hero.queue_redraw()


func _can_buy(id: String) -> bool:
	if _main == null or _main.hero == null:
		return false
	if _is_full():
		return false
	var data: Dictionary = ITEM_CATALOG.get(id, {})
	if data.is_empty():
		return false
	if int(_main.gold) < int(data["cost"]):
		return false
	if not _main.hero.is_alive():
		return false
	return true


func _can_buy_hero(id: String) -> bool:
	if _main == null or _main.hero == null:
		return false
	if str(_main.hero.hero_id) == id:
		return false
	var data: Dictionary = HERO_CATALOG.get(id, {})
	if data.is_empty():
		return false
	if int(_main.gold) < int(data["cost"]):
		return false
	return true


func _is_full() -> bool:
	if _main == null or _main.hero == null:
		return true
	var inv: Array = _main.hero.get("inventory") if "inventory" in _main.hero else []
	return inv.size() >= MAX_SLOTS


func _count_owned(id: String) -> int:
	if _main == null or _main.hero == null:
		return 0
	var inv: Array = _main.hero.get("inventory") if "inventory" in _main.hero else []
	var c = 0
	for v in inv:
		if str(v) == id:
			c += 1
	return c


func _try_buy(id: String) -> void:
	if not _can_buy(id):
		Sound.play("error")
		return
	var data: Dictionary = ITEM_CATALOG[id]
	_main.gold -= int(data["cost"])
	var hero: Variant = _main.hero
	if not "inventory" in hero:
		hero.set("inventory", [])
	hero.inventory.append(id)
	_apply_stats(hero, data)
	Sound.play("buy")
	print("[Shop] %s beli %s (-%d G) sisa %d" % [hero.hero_name, str(data["name"]), int(data["cost"]), int(_main.gold)])
	_main.queue_redraw()


func _try_buy_hero(id: String) -> void:
	if not _can_buy_hero(id):
		Sound.play("error")
		return
	var data: Dictionary = HERO_CATALOG[id]
	_main.gold -= int(data["cost"])
	var hero: Variant = _main.hero
	hero.hero_id = id
	hero.hero_name = str(data["name"])
	hero.max_hp = float(data["hp"])
	hero.hp = hero.max_hp
	hero.damage = float(data["dmg"])
	hero.attack_range = float(data.get("range", 90))
	hero.move_speed = float(data.get("move_speed", 120.0))
	hero.body_color = Color(str(data.get("color_hex", "#4FC3F7")))
	hero.position = Vector2(250, 580)
	if "bonus_armor" in hero:
		hero.bonus_armor = 0.0
	if "bonus_as" in hero:
		hero.bonus_as = 0.0
	hero.lifesteal = 0.0
	hero.attack_interval = 1.0
	for item_id in hero.inventory:
		var idata: Dictionary = ITEM_CATALOG.get(str(item_id), {})
		if not idata.is_empty():
			_apply_stats(hero, idata)
	hero.set_selected(true)
	hero.queue_redraw()
	Sound.play("buy")
	print("[Shop] GANTI HERO -> %s (-%d G) sisa %d" % [hero.hero_name, int(data["cost"]), int(_main.gold)])
	_main.queue_redraw()


func _apply_stats(hero, data: Dictionary) -> void:
	if data.has("dmg"):
		hero.damage += float(data["dmg"])
	if data.has("hp"):
		var add: float = float(data["hp"])
		hero.max_hp += add
		hero.hp += add
		hero.hp = minf(hero.hp, hero.max_hp)
	if data.has("hp_pct"):
		var pct: float = float(data["hp_pct"])
		var add: float = float(hero.max_hp) * pct
		hero.max_hp += add
		hero.hp = minf(hero.hp + add, hero.max_hp)
	if data.has("armor"):
		if not "bonus_armor" in hero:
			hero.set("bonus_armor", 0.0)
		hero.bonus_armor += float(data["armor"])
	if data.has("as"):
		if not "bonus_as" in hero:
			hero.set("bonus_as", 0.0)
		hero.bonus_as += float(data["as"])
		hero.attack_interval = maxf(0.20, 1.0 / (1.0 + hero.bonus_as / 100.0))
	if data.has("ls"):
		if not "lifesteal" in hero:
			hero.set("lifesteal", 0.0)
		hero.lifesteal += float(data["ls"])
	if data.has("crit"):
		var cur: Variant = hero.get("crit_chance") if hero.has_method("get") else null
		if cur == null:
			hero.set("crit_chance", float(data["crit"]))
		else:
			hero.set("crit_chance", float(cur) + float(data["crit"]))
	if data.has("evasion"):
		var cur2: Variant = hero.get("evasion") if hero.has_method("get") else null
		if cur2 == null:
			hero.set("evasion", float(data["evasion"]))
		else:
			hero.set("evasion", float(cur2) + float(data["evasion"]))
	if data.has("ms"):
		hero.move_speed *= (1.0 + float(data["ms"]))
	hero.queue_redraw()
