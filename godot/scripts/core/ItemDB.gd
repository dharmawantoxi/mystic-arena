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


## Nama BERKAS ikon item — field "icon" ITEM_CATALOG yang ikut ter-ekspor ke
## items.json (hero_items.py:248 dst.). Hanya nama berkas ("dead_edge.png");
## yang menyusun path res:// + memuat teksturnya ItemIcons.gd (port
## hero_items.get_icon, hero_items.py:1661-1699).
func item_icon(item_id: String) -> String:
	return str(get_item(item_id).get("icon", ""))


func is_melee_only(item_id: String) -> bool:
	return bool(get_item(item_id).get("melee_only", false))


func is_magic_only(item_id: String) -> bool:
	return bool(get_item(item_id).get("magic_only", false))


## Kata kunci role yang dianggap beratribut MAGIC — paritas
## hero_items.MAGIC_ROLE_KEYWORDS (hero_items.py:151-163). "Anti-Mage"
## sengaja dikecualikan di is_magic_hero(): dia pemburu penyihir, bukan
## penyihir.
const MAGIC_ROLE_KEYWORDS: Array = [
	"mage", "magic", "sorcer", "caster", "warlock", "witch",
	"sage", "prophet", "priestess", "pyro", "necro", "shaman",
	"summoner", "chorister", "farseer", "starweaver", "hex",
	"eldritch",
]


## True kalau `hero` beratribut Magic — paritas hero_items.is_magic_hero
## (hero_items.py:166-187). Dipakai saran item AI & validasi magic_only,
## jadi harus dicek dari ROLE (bukan dmg_school) supaya angka AI = pygame.
func is_magic_hero(hero) -> bool:
	if hero == null:
		return false
	# hero adalah Node: Object.get() hanya 1 argumen (bukan Dictionary.get).
	var role := _hero_role(hero)
	if role.is_empty():
		return false
	if "anti-mage" in role:
		return false
	for kw in MAGIC_ROLE_KEYWORDS:
		if kw in role:
			return true
	return false


## Role hero lowercase; aman untuk Node maupun Dictionary.
func _hero_role(hero) -> String:
	if hero is Dictionary:
		return str(hero.get("role", "")).to_lower()
	var v = hero.get("role") if hero != null else null
	return str(v).to_lower() if v != null else ""


## Base attack range hero (tanpa bonus item). Node Hero memakai base_range;
## Dictionary/fallback memakai "range" atau 100.
func _hero_base_range(hero) -> float:
	if hero is Dictionary:
		if hero.has("base_range"):
			return float(hero["base_range"])
		return float(hero.get("range", 100))
	if hero != null and "base_range" in hero and hero.get("base_range") != null:
		return float(hero.get("base_range"))
	if hero != null and "range" in hero and hero.get("range") != null:
		return float(hero.get("range"))
	return 100.0


## Item berikutnya terbaik untuk hero AI — paritas 1:1
## hero_items.suggest_item_for_hero (hero_items.py:2936-3006).
## `owned` = daftar item yang sudah dimiliki, pool disaring per role,
## lalu cleave_axe ditaruh paling depan untuk hero melee dan
## holy_rapier di belakang untuk semua (persis pygame).
func suggest_item(hero, owned: Array) -> String:
	if hero == null:
		return ""
	var rng := _hero_base_range(hero)
	var is_melee := rng <= 80.0
	# Pygame memakai hero.range (base, tanpa bonus item); Godot padanannya
	# adalah base_range — attack_range sudah termasuk bonus Gale Pike dll.
	var role := _hero_role(hero)
	var pool: Array = []
	if "tank" in role or "bruiser" in role or "fighter" in role:
		pool = ["leviathan_heart", "scarlet_bulwark", "searbrand",
			"razor_carapace", "everfrost_guard", "steel_aegis",
			"abyss_breaker", "solar_brand", "demon_maw",
			"corroder", "fenrir_chain", "octarine_core",
			"moon_shard"]
	elif "marksman" in role or "assassin" in role:
		pool = ["dead_edge", "basilisk_breath", "gale_pike",
			"frostbound_eye", "sundering_cudgel", "searbrand",
			"monarch_wings", "thunder_coil", "sanguine_thorn",
			"moon_shard", "runic_gavel", "corroder", "demon_maw",
			"octarine_core", "steel_aegis"]
	elif "mage" in role or "trickster" in role or is_magic_hero(hero):
		# Catatan paritas: pygame mengecek "mage" in role APA ADANYA, jadi
		# "Boss/Anti-Mage" masuk pool Magic di sini — walau is_magic_hero
		# menolak "anti-mage". Efek akhirnya sama: item magic_only ditolak
		# hero_items.HeroItemInventory.add (_entity path) karena
		# is_magic_hero-nya False.
		pool = ["astral_codex", "fulgur_scepter", "sage_scepter",
			"hex_idol", "rift_veil", "vital_stone",
			"spectral_charm", "vine_rod", "octarine_core",
			"runic_gavel", "searbrand", "solar_brand",
			"frostbound_eye", "everfrost_guard", "tempest_vane",
			"corroder", "moon_shard", "thunder_coil",
			"steel_aegis", "demon_maw", "dead_edge"]
	else:
		pool = ["steel_aegis", "searbrand", "sundering_cudgel",
			"frostbound_eye", "razor_carapace", "moon_shard",
			"demon_maw", "leviathan_heart", "scarlet_bulwark",
			"solar_brand", "thunder_coil", "monarch_wings",
			"octarine_core", "gale_pike", "dead_edge", "corroder",
			"everfrost_guard"]
	if is_melee:
		pool = ["cleave_axe"] + pool + ["holy_rapier"]
	else:
		pool = pool + ["holy_rapier"]
	for sid in pool:
		if owned.has(sid):
			continue
		var data := get_item(sid)
		if data.is_empty():
			continue
		if bool(data.get("melee_only", false)) and not is_melee:
			continue
		if bool(data.get("magic_only", false)) and not is_magic_hero(hero):
			continue
		return sid
	return ""


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
#  KELAS ITEM + HALAMAN TOKO + MEKANIK DETAIL
#  (delegasi HeroItems.gd — twin hero_items.py FASE 29)
# ══════════════════════════════════════════════════════════

## Kelas item PHYSICAL/MAGIC/TANK — delegasi HeroItems.get_item_class
## (paritas hero_items.get_item_class, hero_items.py:1395-1417).
func item_class(item_id: String) -> String:
	return HeroItems.get_item_class(items, item_id)


## Label badge kelas item ("PHYSICAL"/"MAGIC"/"TANK") — ITEM_CLASS_INFO[cls][0].
func item_class_label(item_id: String) -> String:
	var cls := item_class(item_id)
	var info = HeroItems.ITEM_CLASS_INFO.get(cls)
	if info is Array and info.size() >= 1:
		return str(info[0])
	return cls.to_upper()


## Daftar (kind, text) mekanik detail item (popup ITEM FORGE) — delegasi
## HeroItems.build_item_mechanics (paritas hero_items._build_item_mechanics).
func item_mechanics(item_id: String, en: bool = false) -> Array:
	return HeroItems.build_item_mechanics(get_item(item_id), en, item_id)


## Mekanik detail item dalam BAHASA ANTARMUKA AKTIF — paritas
## `en = get_language() == "en"` di hero_items.py:1632 (dan :3894 untuk
## flavor text). Pemakai UI memanggil ini, bukan `item_mechanics`, supaya
## popup detail item ikut bahasa yang dipilih pemain di PENGATURAN.
func item_mechanics_localized(item_id: String) -> Array:
	return item_mechanics(item_id, MysticLocalization.is_english())


## Halaman toko SELARAS batas kelas — delegasi HeroItems.build_shop_pages
## (paritas hero_items.SHOP_PAGES/SHOP_PAGE_META/ITEM_SHOP_ORDER).
func shop_pages() -> Dictionary:
	return HeroItems.build_shop_pages()


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
