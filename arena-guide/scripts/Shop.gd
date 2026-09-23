@warning_ignore("inferred_declaration")
extends Node2D
class_name ShopUI
## ITEM FORGE (biru 340,540) + HERO SHRINE (merah 940,180). H = item, klik gedung = sesuai warna.
## L34 8 item inti + L35 SELL + L36 HERO SHOP

const MAX_SLOTS := 6
const ITEMS_PER_PAGE := 12
const COLS_ITEM := 4
const ITEM_COST := 100

const ITEM_CATALOG := {
	"dead_edge": {"name":"Dead Edge","cost":100,"color":Color8(220,60,60),"glow":Color8(255,90,90),"desc":"+52 Damage. 25% peluang Critical Strike (200","dmg":52,"crit":0.25},
	"holy_rapier": {"name":"Holy Rapier","cost":100,"color":Color8(255,220,80),"glow":Color8(255,245,150),"desc":"+120 Damage. HILANG saat hero mati (tidak di","dmg":120},
	"demon_maw": {"name":"Demon Maw","cost":100,"color":Color8(180,30,30),"glow":Color8(255,70,70),"desc":"+20 Damage, +4 Armor, 20% Lifesteal. Saat HP","dmg":20,"armor":4,"ls":0.2},
	"leviathan_heart": {"name":"Leviathan Heart","cost":100,"color":Color8(80,220,120),"glow":Color8(130,255,160),"desc":"+35% Max HP, +6 HP/reg. Di luar pertempuran ","hp_pct":0.35},
	"cleave_axe": {"name":"Cleave Axe","cost":100,"color":Color8(200,220,240),"glow":Color8(150,210,255),"desc":"+34 Damage, +3 HP/reg. Serangan melee membel","dmg":34},
	"steel_aegis": {"name":"Steel Aegis","cost":100,"color":Color8(180,200,230),"glow":Color8(120,170,255),"desc":"+4 Armor, +30 Attack Speed. Aura: sekutu di ","armor":6,"as":30},
	"moon_shard": {"name":"Moon Shard","cost":100,"color":Color8(130,220,255),"glow":Color8(180,240,255),"desc":"+75 Attack Speed. Serangan secepat cahaya bu","as":75},
	"octarine_core": {"name":"Octarine Core","cost":100,"color":Color8(180,80,230),"glow":Color8(220,130,255),"desc":"+300 HP, +2 HP/reg, 15% Cooldown Reduction, ","hp":300},
	"scarlet_bulwark": {"name":"Scarlet Bulwark","cost":111,"color":Color8(200,60,60),"glow":Color8(255,110,110),"desc":"+250 HP, +8 HP/reg, +6 Armor. Blok pasif 55%","armor":6,"hp":250},
	"monarch_wings": {"name":"Monarch Wings","cost":111,"color":Color8(230,140,220),"glow":Color8(255,190,250),"desc":"+38 Damage, +30 Attack Speed, 28% Evasion (p","dmg":38,"as":30,"evasion":0.28},
	"corroder": {"name":"Corroder","cost":100,"color":Color8(140,220,90),"glow":Color8(190,255,140),"desc":"+65 Damage. Serangan mengikis 6 Armor target","dmg":65},
	"tempest_vane": {"name":"Tempest Vane","cost":122,"color":Color8(120,210,230),"glow":Color8(180,240,255),"desc":"+250 HP, +4 HP/reg, +12% Move Speed. Saat HP","hp":250,"ms":0.12},
	"fenrir_chain": {"name":"Fenrir Chain","cost":116,"color":Color8(240,190,90),"glow":Color8(255,230,150),"desc":"+30 Damage, +30 AS, +250 HP. 20% serangan me","dmg":30,"as":30,"hp":250},
	"sanguine_thorn": {"name":"Sanguine Thorn","cost":133,"color":Color8(230,60,110),"glow":Color8(255,120,160),"desc":"+25 Damage, +60 AS, +5 HP/reg. Soul Rend (au","dmg":25,"as":60},
	"abyss_breaker": {"name":"Abyss Breaker","cost":122,"color":Color8(90,130,220),"glow":Color8(140,180,255),"desc":"+35 Damage, +300 HP, +16% heal diterima, +30","dmg":35,"hp":300},
	"thunder_coil": {"name":"Thunder Coil","cost":116,"color":Color8(250,220,90),"glow":Color8(255,245,160),"desc":"+25 Damage, +65 AS. 22% serangan menyambar 3","dmg":25,"as":65},
	"razor_carapace": {"name":"Razor Carapace","cost":111,"color":Color8(180,180,200),"glow":Color8(230,230,255),"desc":"+18 Damage, +8 Armor, 10% CDR. Saat HP < 55%","dmg":18,"armor":8},
	"everfrost_guard": {"name":"Everfrost Guard","cost":122,"color":Color8(120,190,230),"glow":Color8(180,230,255),"desc":"+10 Armor, +5 HP/reg, 10% CDR. Aura: musuh d","armor":10},
	"sundering_cudgel": {"name":"Sundering Cudgel","cost":111,"color":Color8(230,180,70),"glow":Color8(255,220,130),"desc":"+45 Damage, +25 AS. Serangan TIDAK PERNAH me","dmg":48,"as":25},
	"frostbound_eye": {"name":"Frostbound Eye","cost":116,"color":Color8(120,200,220),"glow":Color8(180,240,255),"desc":"+20 Damage, +250 HP, +4 HP/reg. Tiap seranga","dmg":20,"hp":250},
	"gale_pike": {"name":"Gale Pike","cost":116,"color":Color8(150,230,200),"glow":Color8(200,255,230),"desc":"+18 Damage, +25 AS, +200 HP, +3 HP/reg, +90 ","dmg":18,"as":25,"hp":200},
	"basilisk_breath": {"name":"Basilisk Breath","cost":127,"color":Color8(140,210,90),"glow":Color8(190,255,130),"desc":"+26 Damage, +30 AS, +260 HP, +3 HP/reg. Sera","dmg":26,"as":30,"hp":260},
	"solar_brand": {"name":"Solar Brand","cost":122,"color":Color8(255,190,60),"glow":Color8(255,230,140),"desc":"+30 Damage, +280 HP, +5 HP/reg. Aura: musuh ","dmg":30,"hp":280},
	"runic_gavel": {"name":"Runic Gavel","cost":116,"color":Color8(200,130,240),"glow":Color8(235,180,255),"desc":"+28 Damage, +250 HP, +4 HP/reg, 15% CDR. Set","dmg":28,"hp":250},
	"searbrand": {"name":"Searbrand","cost":127,"color":Color8(235,95,60),"glow":Color8(255,150,110),"desc":"+12 Damage, +320 HP, +6 HP/reg, 15% CDR. AUR","dmg":20,"hp":320},
	"astral_codex": {"name":"Astral Codex","cost":133,"color":Color8(155,90,235),"glow":Color8(210,155,255),"desc":"+280 HP, +4 HP/reg, 18% CDR, 12% Spell Lifes","hp":280},
	"sage_scepter": {"name":"Sage Scepter","cost":111,"color":Color8(120,190,255),"glow":Color8(170,220,255),"desc":"+200 HP, +3 HP/reg, 15% SKILL AMP, 8% Spell ","hp":200},
	"fulgur_scepter": {"name":"Fulgur Scepter","cost":133,"color":Color8(255,180,60),"glow":Color8(255,220,120),"desc":"+15 Damage, +200 HP, 10% SKILL AMP, 8% Spell","dmg":15,"hp":200},
	"hex_idol": {"name":"Hex Idol","cost":127,"color":Color8(170,220,90),"glow":Color8(210,255,140),"desc":"+250 HP, +4 HP/reg, 6% Spell Lifesteal, 10% ","hp":250},
	"rift_veil": {"name":"Rift Veil","cost":122,"color":Color8(130,120,240),"glow":Color8(180,170,255),"desc":"+260 HP, +4 HP/reg, 6% Spell Lifesteal. Saat","hp":260},
	"vital_stone": {"name":"Vital Stone","cost":116,"color":Color8(230,80,110),"glow":Color8(255,140,170),"desc":"+320 HP, +6 HP/reg, 20% Spell Lifesteal. Saa","hp":320},
	"vine_rod": {"name":"Vine Rod","cost":111,"color":Color8(90,200,120),"glow":Color8(150,240,170),"desc":"+15 Damage, +240 HP, +3 HP/reg, 5% Spell Lif","dmg":15,"hp":240},
	"spectral_charm": {"name":"Spectral Charm","cost":122,"color":Color8(190,220,255),"glow":Color8(225,240,255),"desc":"+230 HP, +3 HP/reg, +10% Move Speed, 6% Spel","hp":230,"ms":0.1},
}
# Alias biar kompatibel
const CATALOG := ITEM_CATALOG


const HERO_CATALOG := {
	"kaizen": {"name":"Kaizen","cost":100,"color":Color8(79,195,247),"glow":Color8(120,220,255),"desc":"550 HP 22 DMG Seimbang","hp":550,"dmg":22,"range":90,"move_speed":120.0,"color_hex":"#4FC3F7"},
	"krobellus": {"name":"Krobellus","cost":120,"color":Color8(200,80,80),"glow":Color8(255,120,120),"desc":"600 HP 20 DMG Tank","hp":600,"dmg":20,"range":95,"move_speed":115.0,"color_hex":"#C94A4A"},
	"grimjaw": {"name":"Grimjaw","cost":120,"color":Color8(126,217,87),"glow":Color8(170,240,130),"desc":"480 HP 26 DMG Assassin","hp":480,"dmg":26,"range":85,"move_speed":135.0,"color_hex":"#7ED957"},
	"vex": {"name":"Vex","cost":150,"color":Color8(160,120,255),"glow":Color8(190,160,255),"desc":"520 HP 24 DMG Mage","hp":520,"dmg":24,"range":110,"move_speed":120.0,"color_hex":"#A078FF"},
}

var _main = null
var open = false
var mode = "item" # item | hero
var _close_rect = Rect2()
var _page: int = 0
var _page_prev_rect = Rect2()
var _page_next_rect = Rect2()
var _buy_rects: Dictionary = {} # item_id -> Rect2 (item mode)
var _hero_buy_rects: Dictionary = {} # hero_id -> Rect2 (hero mode)
var _inv_rects: Dictionary = {} # slot_index -> Rect2 L35 SELL

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
	else:
		mode = requested_mode
		if mode == "item":
			_page = 0
		open = true
		visible = true
	if _main != null:
		_main.queue_redraw()
	var label = "ITEM FORGE" if mode=="item" else "HERO SHRINE"
	print("[Shop] %s %s" % [label, ("BUKA" if open else "TUTUP")])

func is_open() -> bool:
	return open

func draw_on(host: CanvasItem) -> void:
	if not open:
		return
	host.draw_rect(Rect2(0,0,1280,720), Color(0,0,0,0.65))
	var pw = 900.0
	var ph = 560.0
	var px = (1280.0 - pw) * 0.5
	var py = (720.0 - ph) * 0.5
	host.draw_rect(Rect2(px,py,pw,ph), Color8(22,26,44))
	var edge = Color8(255,205,90) if mode=="item" else Color8(255,120,120)
	host.draw_rect(Rect2(px,py,pw,ph), edge, false, 3.0)
	host.draw_rect(Rect2(px+2,py+2,pw-4,ph-4), Color8(140,110,58), false, 1.0)
	var font: Font = ThemeDB.fallback_font
	var title = "ITEM FORGE — toko biru (H / klik ITEM)" if mode=="item" else "HERO SHRINE — toko merah (klik SHOP)"
	var tcol = Color8(255,220,100) if mode=="item" else Color8(255,160,160)
	host.draw_string(font, Vector2(px+18, py+32), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, tcol)
	var gold_s = "GOLD %d" % int(_main.gold) if _main != null else "GOLD 0"
	host.draw_string(font, Vector2(px+pw-140, py+32), gold_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color8(255,220,100))
	_close_rect = Rect2(px+pw-44, py+8, 36, 36)
	host.draw_rect(_close_rect, Color8(180,60,60))
	host.draw_rect(_close_rect, Color.WHITE, false, 2.0)
	host.draw_string(font, Vector2(_close_rect.position.x+12, _close_rect.position.y+26), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
	if mode == "hero":
		_draw_hero_grid(host, px, py, pw, ph, font)
	else:
		_draw_item_grid(host, px, py, pw, ph, font)

func _draw_item_grid(host: CanvasItem, px: float, py: float, pw: float, ph: float, font: Font) -> void:
	var cols = COLS_ITEM
	var cw = 200.0
	var ch = 108.0
	var gap = 12.0
	var sx = px + (pw - (cols*cw + (cols-1)*gap))*0.5
	var sy = py + 56.0
	_buy_rects.clear()
	_hero_buy_rects.clear()
	_inv_rects.clear()
	var all_ids: Array = ITEM_CATALOG.keys()
	var total: int = all_ids.size()
	var pages: int = int(ceil(float(total)/float(ITEMS_PER_PAGE)))
	if _page >= pages: _page = max(0, pages-1)
	if _page < 0: _page = 0
	var start: int = _page * ITEMS_PER_PAGE
	var end: int = mini(start + ITEMS_PER_PAGE, total)
	var ids: Array = []
	for i in range(start, end):
		ids.append(all_ids[i])
	for i in ids.size():
		var r = int(i / cols)
		var c = int(i % cols)
		var x = sx + float(c)*(cw+gap)
		var y = sy + float(r)*(ch+gap)
		var id: String = ids[i]
		var data: Dictionary = ITEM_CATALOG[id]
		var owned: int = _count_owned(id)
		var can_buy: bool = _can_buy(id)
		var bg = Color8(34,40,68) if can_buy else Color8(30,30,38)
		host.draw_rect(Rect2(x,y,cw,ch), bg)
		var border: Color = data["glow"] if can_buy else Color8(80,80,90)
		host.draw_rect(Rect2(x,y,cw,ch), border, false, 2.0)
		host.draw_rect(Rect2(x+8, y+8, 36, 36), data["color"])
		host.draw_rect(Rect2(x+8, y+8, 36, 36), Color8(255,255,255,0.25), false, 1.0)
		host.draw_string(font, Vector2(x+52, y+22), str(data["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, data["glow"])
		host.draw_string(font, Vector2(x+52, y+38), "%d G" % int(data["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(255,220,100) if can_buy else Color8(200,80,80))
		if owned>0:
			host.draw_string(font, Vector2(x+cw-42, y+38), "x%d" % owned, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color8(150,255,170))
		var desc: String = str(data["desc"])
		var stxt: String = ""
		if data.has("dmg"): stxt += "+%d dmg " % int(data["dmg"])
		if data.has("hp"): stxt += "+%d hp " % int(data["hp"])
		if data.has("hp_pct"): stxt += "+%d%% hp " % int(float(data["hp_pct"])*100)
		if data.has("armor"): stxt += "+%d arm " % int(data["armor"])
		if data.has("as"): stxt += "+%d as" % int(data["as"])
		host.draw_string(font, Vector2(x+8, y+56), stxt.strip_edges(), HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color8(170,255,170) if stxt!="" else Color8(200,210,230))
		host.draw_string(font, Vector2(x+8, y+68), desc.substr(0,24), HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color8(200,210,230))
		var btn = Rect2(x+8, y+ch-22, cw-16, 18)
		_buy_rects[id] = btn
		if can_buy:
			host.draw_rect(btn, Color8(48,100,64))
			host.draw_rect(btn, Color8(120,235,140), false, 1.5)
			var tw = font.get_string_size("BUY", HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
			host.draw_string(font, Vector2(btn.position.x+(btn.size.x-tw)*0.5, btn.position.y+13), "BUY", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color.WHITE)
		else:
			host.draw_rect(btn, Color8(44,44,54))
			host.draw_rect(btn, Color8(90,90,100), false, 1.0)
			var label = "FULL" if _is_full() else ("GOLD -" if _main != null and int(_main.gold) < int(data["cost"]) else "BUY")
			var tw = font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
			host.draw_string(font, Vector2(btn.position.x+(btn.size.x-tw)*0.5, btn.position.y+13), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color8(170,170,180))
	# pagination controls (above inventory)
	var pag_y = py + ph - 78
	_page_prev_rect = Rect2(px+pw*0.5-74, pag_y, 58, 20)
	_page_next_rect = Rect2(px+pw*0.5+16, pag_y, 58, 20)
	var can_prev: bool = _page > 0
	var can_next: bool = _page < pages-1
	host.draw_rect(_page_prev_rect, Color8(40,70,140) if can_prev else Color8(30,30,38))
	host.draw_rect(_page_prev_rect, Color8(90,130,255) if can_prev else Color8(70,70,80), false, 1.0)
	host.draw_rect(_page_next_rect, Color8(40,70,140) if can_next else Color8(30,30,38))
	host.draw_rect(_page_next_rect, Color8(90,130,255) if can_next else Color8(70,70,80), false, 1.0)
	var twp = font.get_string_size("< PREV", HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x
	var twn = font.get_string_size("NEXT >", HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x
	host.draw_string(font, Vector2(_page_prev_rect.position.x+(58-twp)*0.5, pag_y+13), "< PREV", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color.WHITE if can_prev else Color8(130,130,140))
	host.draw_string(font, Vector2(_page_next_rect.position.x+(58-twn)*0.5, pag_y+13), "NEXT >", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color.WHITE if can_next else Color8(130,130,140))
	host.draw_string(font, Vector2(px+pw*0.5-14, pag_y+13), "%d/%d" % [_page+1, pages], HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color8(255,220,100))
	# inventory bawah L35
	_inv_rects.clear()
	if _main != null and _main.hero != null:
		var inv: Array = _main.hero.get("inventory") if "inventory" in _main.hero else []
		var inv_y = py+ph-52
		host.draw_string(font, Vector2(px+18, inv_y), "INVENTORY %d/%d  (klik kanan slot = JUAL 70%%)" % [int(inv.size()), MAX_SLOTS], HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(170,180,205))
		var sx2 = px + pw*0.5 - 180
		for i in 6:
			var r = Rect2(sx2 + float(i)*54, inv_y+8, 48, 32)
			_inv_rects[i] = r
			host.draw_rect(r, Color8(14,17,30))
			var slot_item = null
			if i < inv.size():
				slot_item = inv[i]
			var col = Color8(66,74,104)
			if slot_item != null:
				var d: Dictionary = ITEM_CATALOG.get(str(slot_item), {})
				col = d.get("color", col)
				if d.has("color"):
					host.draw_rect(Rect2(r.position.x+2, r.position.y+2, 44,28), col)
				host.draw_rect(Rect2(r.position.x+34, r.position.y+2, 12, 12), Color8(180,60,60,0.9))
				host.draw_string(font, Vector2(r.position.x+37, r.position.y+11), "x", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color.WHITE)
			host.draw_rect(r, col, false, 1.5 if slot_item != null else 1.0)
		if not inv.is_empty():
			host.draw_string(font, Vector2(px+pw*0.5 - 90, inv_y+46), "klik kanan slot untuk jual", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color8(200,180,160))



func _draw_hero_grid(host: CanvasItem, px: float, py: float, pw: float, ph: float, font: Font) -> void:
	_buy_rects.clear()
	_hero_buy_rects.clear()
	_inv_rects.clear()
	var ids = HERO_CATALOG.keys()
	var cols = 4
	var cw = 200.0
	var ch = 160.0
	var gap = 12.0
	var sx = px + (pw - (cols*cw + (cols-1)*gap))*0.5
	var sy = py + 56.0
	for i in ids.size():
		var r = int(i / cols)
		var c = int(i % cols)
		var x = sx + float(c)*(cw+gap)
		var y = sy + float(r)*(ch+gap)
		var id: String = ids[i]
		var data: Dictionary = HERO_CATALOG[id]
		var can_buy = _can_buy_hero(id)
		var is_current: bool = _main != null and _main.hero != null and str(_main.hero.hero_id) == id
		var bg = Color8(40,30,40) if is_current else (Color8(34,40,68) if can_buy else Color8(30,30,38))
		host.draw_rect(Rect2(x,y,cw,ch), bg)
		var border: Color = Color8(255,220,100) if is_current else (data["glow"] if can_buy else Color8(80,80,90))
		host.draw_rect(Rect2(x,y,cw,ch), border, false, 2.5 if is_current else 2.0)
		# hero circle
		host.draw_circle(Vector2(x+cw*0.5, y+40), 22, Color(0,0,0,0.35))
		host.draw_circle(Vector2(x+cw*0.5, y+38), 20, data["color"])
		host.draw_string(font, Vector2(x+10, y+78), str(data["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, data["glow"] if not is_current else Color8(255,220,100))
		host.draw_string(font, Vector2(x+10, y+96), str(data["desc"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color8(200,210,230))
		host.draw_string(font, Vector2(x+10, y+114), "%d G" % int(data["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(255,220,100) if can_buy else Color8(200,80,80))
		if is_current:
			host.draw_string(font, Vector2(x+cw-70, y+114), "AKTIF", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(150,255,170))
		var btn = Rect2(x+8, y+ch-28, cw-16, 24)
		_hero_buy_rects[id] = btn
		if is_current:
			host.draw_rect(btn, Color8(60,60,70))
			host.draw_rect(btn, Color8(120,120,130), false, 1.0)
			var tw = font.get_string_size("AKTIF", HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
			host.draw_string(font, Vector2(btn.position.x+(btn.size.x-tw)*0.5, btn.position.y+17), "AKTIF", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(170,170,180))
		elif can_buy:
			host.draw_rect(btn, Color8(80,40,40))
			host.draw_rect(btn, Color8(255,120,120), false, 1.5)
			var tw = font.get_string_size("GANTI", HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
			host.draw_string(font, Vector2(btn.position.x+(btn.size.x-tw)*0.5, btn.position.y+17), "GANTI", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
		else:
			host.draw_rect(btn, Color8(44,44,54))
			host.draw_rect(btn, Color8(90,90,100), false, 1.0)
			var tw = font.get_string_size("GOLD -", HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
			host.draw_string(font, Vector2(btn.position.x+(btn.size.x-tw)*0.5, btn.position.y+17), "GOLD -", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(170,170,180))
	# hint
	if _main != null and _main.hero != null:
		host.draw_string(font, Vector2(px+18, py+ph-18), "Ganti hero = heal penuh + reset posisi ke base", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(170,180,205))

func handle_click(point: Vector2) -> bool:
	if not open:
		return false
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
		if _page_prev_rect.has_point(point) and _page>0:
			_page -=1
			_main.queue_redraw()
			Sound.play("click")
			return true
		if _page_next_rect.has_point(point) and _page < int(ceil(float(ITEM_CATALOG.size())/float(ITEMS_PER_PAGE)))-1:
			_page +=1
			_main.queue_redraw()
			Sound.play("click")
			return true
		for id in _buy_rects.keys():
			var r: Rect2 = _buy_rects[id]
			if r.has_point(point):
				_try_buy(str(id))
				return true
	var pw = 900.0
	var ph = 560.0
	var px = (1280.0 - pw)*0.5
	var py = (720.0 - ph)*0.5
	if Rect2(px,py,pw,ph).has_point(point):
		return true
	toggle_mode(mode)
	return true

func handle_right_click(point: Vector2) -> bool:
	if not open:
		return false
	if mode != "item":
		return false
	for idx in _inv_rects.keys():
		var r: Rect2 = _inv_rects[idx]
		if r.has_point(point):
			_try_sell(int(idx))
			return true
	var pw = 900.0
	var ph = 560.0
	var px = (1280.0 - pw)*0.5
	var py = (720.0 - ph)*0.5
	if Rect2(px,py,pw,ph).has_point(point):
		return true
	return false

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
	var cost = int(data.get("cost", 100))
	var refund = int(cost * 0.7)
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
		var sub = float(data["hp"])
		hero.max_hp = maxf(1.0, hero.max_hp - sub)
		hero.hp = minf(hero.hp, hero.max_hp)
		hero.hp = maxf(1.0, hero.hp)
	if data.has("hp_pct"):
		var pct = float(data["hp_pct"])
		var cur = hero.max_hp
		var add = cur * pct / (1.0+pct)
		hero.max_hp = maxf(1.0, cur - add)
		hero.hp = minf(hero.hp, hero.max_hp)
	if data.has("armor"):
		if "bonus_armor" in hero:
			hero.bonus_armor = maxf(0.0, hero.bonus_armor - float(data["armor"]))
	if data.has("as"):
		if "bonus_as" in hero:
			hero.bonus_as = maxf(0.0, hero.bonus_as - float(data["as"]))
		hero.attack_interval = maxf(0.20, 1.0/(1.0+hero.bonus_as/100.0)) if hero.bonus_as>0 else 1.0
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
			c+=1
	return c

func _try_buy(id: String) -> void:
	if not _can_buy(id):
		Sound.play("error")
		return
	var data: Dictionary = ITEM_CATALOG[id]
	_main.gold -= int(data["cost"])
	var hero = _main.hero
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
	var hero = _main.hero
	# simpan inventory — bawa ke hero baru tapi reset bonus stats (item tetap)
	# ganti hero stats
	hero.hero_id = id
	hero.hero_name = str(data["name"])
	hero.max_hp = float(data["hp"])
	hero.hp = hero.max_hp
	hero.damage = float(data["dmg"])
	hero.attack_range = float(data.get("range", 90))
	hero.move_speed = float(data.get("move_speed", 120.0))
	hero.body_color = Color(str(data.get("color_hex", "#4FC3F7")))
	# reset posisi ke base
	hero.position = Vector2(250, 580)
	if "bonus_armor" in hero:
		hero.bonus_armor = 0.0
	if "bonus_as" in hero:
		hero.bonus_as = 0.0
	hero.lifesteal = 0.0
	hero.attack_interval = 1.0
	# terapkan lagi bonus dari inventory yang masih ada
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
		var add = float(data["hp"])
		hero.max_hp += add
		hero.hp += add
		hero.hp = minf(hero.hp, hero.max_hp)
	if data.has("hp_pct"):
		var pct = float(data["hp_pct"])
		var add = hero.max_hp * pct
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
		hero.attack_interval = maxf(0.20, 1.0/(1.0+hero.bonus_as/100.0))
	if data.has("ls"):
		if not "lifesteal" in hero:
			hero.set("lifesteal", 0.0)
		hero.lifesteal += float(data["ls"])
	if data.has("crit"):
		var cur: Variant = hero.get("crit_chance") if hero.has_method("get") else null
		if cur==null:
			hero.set("crit_chance", float(data["crit"]))
		else:
			hero.set("crit_chance", float(cur)+float(data["crit"]))
	if data.has("evasion"):
		var cur2: Variant = hero.get("evasion") if hero.has_method("get") else null
		if cur2==null:
			hero.set("evasion", float(data["evasion"]))
		else:
			hero.set("evasion", float(cur2)+float(data["evasion"]))
	if data.has("ms"):
		hero.move_speed *= (1.0 + float(data["ms"]))
	hero.queue_redraw()
