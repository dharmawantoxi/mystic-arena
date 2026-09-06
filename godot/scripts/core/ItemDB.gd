# ItemDB.gd — Autoload. Port hero_items.py (ITEM_CATALOG + metadata toko).
#
# Sumber: godot/data/items.json (33 item) + godot/data/items_meta.json
# (MAX_ITEM_SLOTS=6, ITEM_FLAT_COST=4500, ITEM_SHOP_ORDER, CATEGORY_INFO).
# Sebelumnya items.json di-generate tapi TIDAK dibaca satu pun script Godot —
# sekarang ItemInventory.gd (stat per hero) dan ShopPanel.gd (UI toko) memakainya.
extends Node

const ITEMS_PATH := "res://data/items.json"
const META_PATH := "res://data/items_meta.json"

## Fallback — paritas hero_items.py 120-123
const FALLBACK_MAX_SLOTS := 6
const FALLBACK_FLAT_COST := 4500

## Satu item contoh supaya toko tidak kosong kalau items.json belum di-generate
const FALLBACK_ITEMS: Dictionary = {
	"dead_edge": {"name": "Dead Edge", "category": "crit", "cost": 4500,
		"color": [220, 60, 60], "stats": {"damage": 52, "crit_chance": 0.25, "crit_mult": 2.0},
		"melee_only": false, "drops_on_death": false,
		"desc": "+52 Damage. 25% peluang Critical Strike (200% damage)."},
	"steel_aegis": {"name": "Steel Aegis", "category": "as_armor", "cost": 4500,
		"color": [180, 200, 230], "stats": {"armor": 6, "attack_speed": 30},
		"melee_only": false, "drops_on_death": false,
		"desc": "+6 Armor, +30 Attack Speed."},
	"leviathan_heart": {"name": "Leviathan Heart", "category": "tank", "cost": 4500,
		"color": [80, 220, 120], "stats": {"hp_pct": 0.35, "hp_regen": 6.0},
		"melee_only": false, "drops_on_death": false,
		"desc": "+35% Max HP, +6 HP/reg."},
}

var items: Dictionary = {}
var meta: Dictionary = {}


func _ready() -> void:
	load_all()


func load_all() -> void:
	items = _read_json(ITEMS_PATH)
	meta = _read_json(META_PATH)
	if items.is_empty():
		push_warning("[ItemDB] items.json belum ada — pakai fallback 3 item. "
			+ "Jalankan tools/convert_to_godot.py")
		items = FALLBACK_ITEMS.duplicate(true)
	print("[ItemDB] Loaded %d items · %d slot · harga %d" % [
		items.size(), max_slots(), flat_cost()])


static func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if parsed is Dictionary else {}


# ══════════════════════════════════════════════════════════
#  METADATA TOKO
# ══════════════════════════════════════════════════════════

func max_slots() -> int:
	return int(meta.get("max_slots", FALLBACK_MAX_SLOTS))


func flat_cost() -> int:
	return int(meta.get("flat_cost", FALLBACK_FLAT_COST))


## Urutan tampil di toko (paritas ITEM_SHOP_ORDER); fallback = urutan katalog
func shop_order() -> Array:
	var order = meta.get("shop_order")
	if order is Array and not order.is_empty():
		return order
	return items.keys()


func category_label(category: String) -> String:
	var c = meta.get("categories", {}).get(category)
	if c is Dictionary:
		return str(c.get("label", category.to_upper()))
	return category.to_upper()


func category_color(category: String) -> Color:
	var c = meta.get("categories", {}).get(category)
	if c is Dictionary:
		return _color_from(c.get("color", ""), Color("#c8c8c8"))
	return Color("#c8c8c8")


# ══════════════════════════════════════════════════════════
#  ITEM
# ══════════════════════════════════════════════════════════

func has_item(item_id: String) -> bool:
	return items.has(item_id)


func get_item(item_id: String) -> Dictionary:
	var it = items.get(item_id)
	return it if it is Dictionary else {}


func item_name(item_id: String) -> String:
	return str(get_item(item_id).get("name", item_id))


func item_desc(item_id: String) -> String:
	var it := get_item(item_id)
	var d := str(it.get("desc", ""))
	return d if not d.is_empty() else str(it.get("desc_en", ""))


func item_category(item_id: String) -> String:
	return str(get_item(item_id).get("category", "damage"))


## Harga: hero_items memakai ITEM_FLAT_COST seragam; katalog boleh menimpanya.
func item_cost(item_id: String) -> int:
	var it := get_item(item_id)
	if it.has("cost"):
		return int(it["cost"])
	return flat_cost()


func item_color(item_id: String) -> Color:
	return _rgb_array(get_item(item_id).get("color"), Color("#c8c8c8"))


func item_glow(item_id: String) -> Color:
	return _rgb_array(get_item(item_id).get("glow"), item_color(item_id).lightened(0.3))


func is_melee_only(item_id: String) -> bool:
	return bool(get_item(item_id).get("melee_only", false))


func drops_on_death(item_id: String) -> bool:
	return bool(get_item(item_id).get("drops_on_death", false))


func stat(item_id: String, key: String, default: float = 0.0) -> float:
	var s = get_item(item_id).get("stats")
	if s is Dictionary and s.has(key):
		return float(s[key])
	return default


func stats(item_id: String) -> Dictionary:
	var s = get_item(item_id).get("stats")
	return s.duplicate() if s is Dictionary else {}


func passive(item_id: String) -> Dictionary:
	var p = get_item(item_id).get("passive")
	return p.duplicate() if p is Dictionary else {}


func aura(item_id: String) -> Dictionary:
	var a = get_item(item_id).get("aura")
	return a.duplicate() if a is Dictionary else {}


## Item dikelompokkan per kategori untuk UI toko (3 halaman ala SHOP_PAGES)
func grouped() -> Dictionary:
	var out: Dictionary = {}
	for item_id in shop_order():
		if not items.has(item_id):
			continue
		var cat := item_category(item_id)
		if not out.has(cat):
			out[cat] = []
		out[cat].append(item_id)
	return out


# ══════════════════════════════════════════════════════════
static func _color_from(v, fallback: Color) -> Color:
	if v is Color:
		return v
	if v is Array:
		return _rgb_array(v, fallback)
	var s := str(v).strip_edges()
	if s.is_empty():
		return fallback
	if not s.begins_with("#"):
		s = "#" + s
	var c := Color(s)
	if c.a == 0.0 and s != "#00000000":
		return fallback
	return c


static func _rgb_array(v, fallback: Color) -> Color:
	if v is Array and v.size() >= 3:
		return Color8(int(v[0]) & 255, int(v[1]) & 255, int(v[2]) & 255)
	return _color_from(v, fallback)
