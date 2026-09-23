extends Node2D
class_name ShopUI
## ITEM FORGE godot — toko biru (SHOP_BLUE). Buka: tekan H atau klik gedung ITEM.
## 8 item inti (paritas hero_items.py disederhanakan) — beli pakai GOLD.

const MAX_SLOTS := 6
const ITEM_COST := 100  # diset 100 biar test cepat (pygame 4500, di Godot 100 = 1 tower)

const CATALOG := {
	"dead_edge": {"name":"Dead Edge","cost":100,"color":Color8(220,60,60),"glow":Color8(255,90,90),"desc":"+30 Damage, 25% crit x2","dmg":30,"crit":0.25},
	"holy_rapier": {"name":"Holy Rapier","cost":150,"color":Color8(255,220,80),"glow":Color8(255,245,150),"desc":"+60 Damage (hilang saat mati)","dmg":60},
	"leviathan_heart": {"name":"Leviathan Heart","cost":100,"color":Color8(80,220,120),"glow":Color8(130,255,160),"desc":"+250 HP, +5 regen","hp":250},
	"steel_aegis": {"name":"Steel Aegis","cost":100,"color":Color8(180,200,230),"glow":Color8(120,170,255),"desc":"+6 Armor, +20 AS, aura","armor":6,"as":20},
	"moon_shard": {"name":"Moon Shard","cost":100,"color":Color8(130,220,255),"glow":Color8(180,240,255),"desc":"+60 Attack Speed","as":60},
	"demon_maw": {"name":"Demon Maw","cost":120,"color":Color8(180,30,30),"glow":Color8(255,70,70),"desc":"+20 Damage, 15% lifesteal","dmg":20,"ls":0.15},
	"scarlet_bulwark": {"name":"Scarlet Bulwark","cost":120,"color":Color8(200,60,60),"glow":Color8(255,110,110),"desc":"+250 HP +6 Armor, block 25","hp":250,"armor":6},
	"searbrand": {"name":"Searbrand","cost":120,"color":Color8(235,95,60),"glow":Color8(255,150,110),"desc":"+15 Damage +150 HP, bakar 6/dtk","dmg":15,"hp":150},
}

var _main = null
var open := false
var _close_rect := Rect2()
var _buy_rects: Dictionary = {} # item_id -> Rect2

func setup(main_ref) -> void:
	_main = main_ref
	z_index = 60
	visible = false

func toggle() -> void:
	open = not open
	visible = open
	if _main != null:
		_main.queue_redraw()
	print("[Shop] %s" % ("BUKA" if open else "TUTUP"))

func is_open() -> bool:
	return open

func draw_on(host: CanvasItem) -> void:
	if not open:
		return
	# overlay gelap
	host.draw_rect(Rect2(0,0,1280,720), Color(0,0,0,0.65))
	# panel tengah
	var pw := 900.0
	var ph := 560.0
	var px := (1280.0 - pw) * 0.5
	var py := (720.0 - ph) * 0.5
	host.draw_rect(Rect2(px,py,pw,ph), Color8(22,26,44))
	host.draw_rect(Rect2(px,py,pw,ph), Color8(255,205,90), false, 3.0)
	host.draw_rect(Rect2(px+2,py+2,pw-4,ph-4), Color8(140,110,58), false, 1.0)
	# judul
	var font: Font = ThemeDB.fallback_font
	host.draw_string(font, Vector2(px+18, py+32), "ITEM FORGE — toko biru (H / klik ITEM)", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color8(255,220,100))
	# gold
	var gold_s := "GOLD %d" % int(_main.gold) if _main != null else "GOLD 0"
	host.draw_string(font, Vector2(px+pw-140, py+32), gold_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color8(255,220,100))
	# close X
	_close_rect = Rect2(px+pw-44, py+8, 36, 36)
	host.draw_rect(_close_rect, Color8(180,60,60))
	host.draw_rect(_close_rect, Color.WHITE, false, 2.0)
	host.draw_string(font, Vector2(_close_rect.position.x+12, _close_rect.position.y+26), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
	# grid 4x2
	var cols := 4
	var cw := 200.0
	var ch := 150.0
	var gap := 12.0
	var sx := px + (pw - (cols*cw + (cols-1)*gap))*0.5
	var sy := py + 56.0
	_buy_rects.clear()
	var ids := CATALOG.keys()
	for i in ids.size():
		var r := int(i / cols)
		var c := int(i % cols)
		var x := sx + float(c)*(cw+gap)
		var y := sy + float(r)*(ch+gap)
		var id: String = ids[i]
		var data: Dictionary = CATALOG[id]
		var owned: int = _count_owned(id)
		var can_buy: bool = _can_buy(id)
		# card bg
		var bg := Color8(34,40,68) if can_buy else Color8(30,30,38)
		host.draw_rect(Rect2(x,y,cw,ch), bg)
		var border: Color = data["glow"] if can_buy else Color8(80,80,90)
		host.draw_rect(Rect2(x,y,cw,ch), border, false, 2.0)
		# icon kotak warna
		host.draw_rect(Rect2(x+8, y+8, 36, 36), data["color"])
		host.draw_rect(Rect2(x+8, y+8, 36, 36), Color8(255,255,255,0.25), false, 1.0)
		# nama
		host.draw_string(font, Vector2(x+52, y+22), str(data["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, data["glow"])
		host.draw_string(font, Vector2(x+52, y+38), "%d G" % int(data["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(255,220,100) if can_buy else Color8(200,80,80))
		if owned>0:
			host.draw_string(font, Vector2(x+cw-60, y+38), "x%d" % owned, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(150,255,170))
		# desc
		var desc: String = str(data["desc"])
		# wrap sederhana 2 baris
		if desc.length() > 22:
			host.draw_string(font, Vector2(x+8, y+62), desc.substr(0,22), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(200,210,230))
			host.draw_string(font, Vector2(x+8, y+78), desc.substr(22,26), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(200,210,230))
		else:
			host.draw_string(font, Vector2(x+8, y+62), desc, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(200,210,230))
		# tombol BUY
		var btn := Rect2(x+8, y+ch-32, cw-16, 24)
		_buy_rects[id] = btn
		if can_buy:
			host.draw_rect(btn, Color8(48,100,64))
			host.draw_rect(btn, Color8(120,235,140), false, 1.5)
			var tw := font.get_string_size("BUY", HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
			host.draw_string(font, Vector2(btn.position.x+(btn.size.x-tw)*0.5, btn.position.y+17), "BUY", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
		else:
			host.draw_rect(btn, Color8(44,44,54))
			host.draw_rect(btn, Color8(90,90,100), false, 1.0)
			var label := "FULL" if _is_full() else ("GOLD -" if _main != null and int(_main.gold) < int(data["cost"]) else "BUY")
			var tw := font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
			host.draw_string(font, Vector2(btn.position.x+(btn.size.x-tw)*0.5, btn.position.y+17), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(170,170,180))
	# inventory bawah
	if _main != null and _main.hero != null:
		var inv: Array = _main.hero.get("inventory") if "inventory" in _main.hero else []
		var inv_y := py+ph-52
		host.draw_string(font, Vector2(px+18, inv_y), "INVENTORY %d/%d  (klik kanan slot di game untuk drop — v1)" % [int(inv.size()), MAX_SLOTS], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color8(170,180,205))
		var sx2 := px + pw*0.5 - 180
		for i in 6:
			var r := Rect2(sx2 + float(i)*54, inv_y+8, 48, 32)
			host.draw_rect(r, Color8(14,17,30))
			var slot_item = null
			if i < inv.size():
				slot_item = inv[i]
			var col := Color8(66,74,104)
			if slot_item != null:
				var d: Dictionary = CATALOG.get(str(slot_item), {})
				col = d.get("color", col)
				if d.has("color"):
					host.draw_rect(Rect2(r.position.x+2, r.position.y+2, 44,28), col)
			host.draw_rect(r, col, false, 1.5 if slot_item != null else 1.0)

func handle_click(point: Vector2) -> bool:
	if not open:
		return false
	if _close_rect.has_point(point):
		toggle()
		Sound.play("click")
		return true
	for id in _buy_rects.keys():
		var r: Rect2 = _buy_rects[id]
		if r.has_point(point):
			_try_buy(str(id))
			return true
	# klik di panel tapi bukan tombol = tahan (jangan tembus ke map)
	var pw := 900.0
	var ph := 560.0
	var px := (1280.0 - pw)*0.5
	var py := (720.0 - ph)*0.5
	if Rect2(px,py,pw,ph).has_point(point):
		return true
	# klik di luar panel = tutup
	toggle()
	return true

func _can_buy(id: String) -> bool:
	if _main == null or _main.hero == null:
		return false
	if _is_full():
		return false
	var data: Dictionary = CATALOG.get(id, {})
	if data.is_empty():
		return false
	if int(_main.gold) < int(data["cost"]):
		return false
	# hero harus hidup
	if not _main.hero.is_alive():
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
	var c := 0
	for v in inv:
		if str(v) == id:
			c+=1
	return c

func _try_buy(id: String) -> void:
	if not _can_buy(id):
		Sound.play("error")
		return
	var data: Dictionary = CATALOG[id]
	_main.gold -= int(data["cost"])
	# simpan ke inventory hero
	var hero = _main.hero
	if not "inventory" in hero:
		hero.set("inventory", [])
	hero.inventory.append(id)
	# terapkan stat langsung
	_apply_stats(hero, data)
	Sound.play("buy")
	print("[Shop] %s beli %s (-%d G) sisa %d" % [hero.hero_name, str(data["name"]), int(data["cost"]), int(_main.gold)])
	_main.queue_redraw()

func _apply_stats(hero, data: Dictionary) -> void:
	if data.has("dmg"):
		hero.damage += float(data["dmg"])
	if data.has("hp"):
		var add := float(data["hp"])
		hero.max_hp += add
		hero.hp += add
		hero.hp = minf(hero.hp, hero.max_hp)
	if data.has("armor"):
		if not "bonus_armor" in hero:
			hero.set("bonus_armor", 0.0)
		hero.bonus_armor += float(data["armor"])
	if data.has("as"):
		if not "bonus_as" in hero:
			hero.set("bonus_as", 0.0)
		hero.bonus_as += float(data["as"])
		# attack_interval lebih kecil = lebih cepat (60 fps base 1.0 -> kurangi 0.01 per 10 AS)
		hero.attack_interval = maxf(0.35, hero.attack_interval - float(data["as"])*0.006)
	# lifesteal simpan
	if data.has("ls"):
		if not "lifesteal" in hero:
			hero.set("lifesteal", 0.0)
		hero.lifesteal += float(data["ls"])
	hero.queue_redraw()
