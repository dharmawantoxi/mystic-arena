# ================================
# HeroItems.gd — Port 1:1 hero_items.py (Pygame -> Godot)
#
# Twin statik dari hero_items.py untuk LOGIKA MURNI yang belum punya pembaca
# di sisi Godot. Bagian hero_items.py yang lain SUDAH hidup di file lain:
#   - ITEM_CATALOG          -> godot/data/items.json (via convert_to_godot.py)
#   - HeroItemInventory     -> godot/scripts/items/ItemInventory.gd
#   - is_magic_hero         -> godot/scripts/core/ItemDB.gd
#   - suggest_item_for_hero -> godot/scripts/core/ItemDB.gd
#   - update_auras          -> godot/scripts/systems/CombatSystem.gd
#   - HeroItemRenderer/ItemShopUI/handle_item_shop_click -> ShopPanel.gd
#
# Yang di-port DI SINI (semua static, data mentah disuntik — tidak membaca
# autoload — supaya fungsinya murni dan bisa diuji headless):
#   1. get_item_class + ITEM_CLASS_INFO/_ITEM_CLASS_OVERRIDES/
#      _MAP_CATEGORY_TO_CLASS (hero_items.py:1370-1417): kelas PHYSICAL/
#      MAGIC/TANK tiap item (badge kartu + tab ITEM FORGE).
#   2. build_shop_pages + CLASS_ITEM_ORDER/ITEMS_PER_PAGE/ITEM_SHOP_ORDER
#      (hero_items.py:1419-1466): 6 halaman toko SELARAS batas kelas.
#   3. fmt_mech_value + build_item_mechanics + _FIELD_LABELS/_GROUP_LABELS/
#      _MECH_GROUPS/_PCT_KEYS/_FRAME_KEYS (hero_items.py:1508-1653):
#      daftar (kind, text) popup detail item.
#   4. pending_forge_items + deliver_pending_forge_items
#      (hero_items.py:3143-3167): antrian beli saat hero mati, dikirim
#      setelah respawn.
#   5. _resolve_shop_target (hero_items.py:3169-3190): penerima pembelian
#      (termasuk hero mati -> pesanan tertunda).
#   6. _hero_level_mult (hero_items.py:2748-2755): pengali HP per level
#      (HERO_LEVELS).
#
# Adaptasi GDScript (perilaku identik, dikunci paritas):
#   - tuple Python -> Array (urutan indeks sama),
#   - f"{x:g}" (format general 6 angka penting, buang nol belakang) ->
#     _py_g: eksponen lewat loop (tanpa log, bebas float-error di batas
#     pangkat 10) + String.num(desimal) + potong nol/titik,
#   - str(float) Python yang SELALU mempertahankan ".0" untuk bilangan
#     bulat float (3.0 -> "3.0") -> _py_str (Godot str() membuang ".0"),
#   - getattr(obj, "x", None) -> obj.get("x") (Dictionary maupun Node),
#   - hero.alive -> dibaca dulu; kalau absen, fallback NOT is_dead
#     (Godot Hero.gd memakai is_dead, pygame memakai alive) — dikunci
#     kasus eksplisit di HeroItemsParityTest.
#
# Twin Pygame: hero_items.py. Dikunci: godot/tests/HeroItemsParityTest.gd
# (+ fixture match_parity.json["hero_items"]).
# ================================
extends RefCounted
class_name HeroItems


# ─── KELAS ITEM (hero_items.py:1370-1387) ─────────────────────────────
const CLASS_PHYSICAL := "physical"
const CLASS_MAGIC := "magic"
const CLASS_TANK := "tank"

const ITEM_CLASS_INFO := {
	CLASS_PHYSICAL: ["PHYSICAL", [255, 150, 80]],
	CLASS_MAGIC: ["MAGIC", [200, 145, 255]],
	CLASS_TANK: ["TANK", [115, 225, 145]],
}

# Override eksplisit: kategori item-item ini dipakai lintas kelas,
# jadi kelasnya diputuskan satu per satu.
const _ITEM_CLASS_OVERRIDES := {
	"tempest_vane": CLASS_TANK,    # UTILITY - defensif (HP, kebal)
	"abyss_breaker": CLASS_TANK,   # CONTROL - bruiser tank (heal amp,
	                               # slow resist, HP besar)
}

const _MAP_CATEGORY_TO_CLASS := {
	# Caster / sihir
	"caster": CLASS_MAGIC,
	"arcane": CLASS_MAGIC,
	"mystic": CLASS_MAGIC,
	# Defensif
	"tank": CLASS_TANK,
	"guard": CLASS_TANK,
	"thorn": CLASS_TANK,
	"frost": CLASS_TANK,
	"inferno": CLASS_TANK,
	"as_armor": CLASS_TANK,
	"mortal": CLASS_TANK,
}


## Kelas item: CLASS_PHYSICAL / CLASS_MAGIC / CLASS_TANK (badge kartu +
## tab kategori ITEM FORGE). `items` = katalog item (disuntik, contoh
## res://data/items.json) supaya fungsi ini murni seperti HeroBalance.
static func get_item_class(items: Dictionary, item_id: String) -> String:
	var data: Variant = items.get(item_id)
	if not (data is Dictionary):
		return CLASS_PHYSICAL
	var d: Dictionary = data
	if _ITEM_CLASS_OVERRIDES.has(item_id):
		return str(_ITEM_CLASS_OVERRIDES[item_id])
	if d.get("magic_only", false) == true:
		return CLASS_MAGIC
	return str(_MAP_CATEGORY_TO_CLASS.get(str(d.get("category")),
		CLASS_PHYSICAL))


# ─── HALAMAN TOKO (hero_items.py:1419-1466) ───────────────────────────
## Jumlah item per halaman toko (grid 4x2)
const ITEMS_PER_PAGE := 8

# Urutan item DI DALAM tiap kelas (urutan tampil antar halaman).
const CLASS_ITEM_ORDER := {
	CLASS_PHYSICAL: [
		# Physical 1: carry dasar + utility serang
		"dead_edge", "holy_rapier", "demon_maw", "cleave_axe",
		"moon_shard", "monarch_wings", "corroder", "fenrir_chain",
		# Physical 2: late-game carry
		"sanguine_thorn", "thunder_coil", "sundering_cudgel",
		"frostbound_eye", "gale_pike", "basilisk_breath",
	],
	CLASS_MAGIC: [
		# Magic 1: inti caster
		"octarine_core", "runic_gavel", "astral_codex",
		"sage_scepter", "fulgur_scepter", "hex_idol", "rift_veil",
		"vital_stone",
		# Magic 2: sisa paket MAGIC ONLY
		"vine_rod", "spectral_charm",
	],
	CLASS_TANK: [
		"leviathan_heart", "steel_aegis", "scarlet_bulwark",
		"tempest_vane", "abyss_breaker", "razor_carapace",
		"everfrost_guard", "solar_brand", "searbrand",
	],
}

static var _cached_pages: Dictionary = {}


## Pecah item menjadi halaman toko SELARAS batas kelas (tiap kelas
## menempati halaman genap, tidak tercampur kelas lain di halaman yang
## sama). Return {pages: Array[Array], meta: Array[[cls, page, total]],
## order: Array} — persis SHOP_PAGES/SHOP_PAGE_META/ITEM_SHOP_ORDER.
static func build_shop_pages() -> Dictionary:
	if not _cached_pages.is_empty():
		return _cached_pages
	var pages: Array = []
	var meta: Array = []
	for cls in [CLASS_PHYSICAL, CLASS_MAGIC, CLASS_TANK]:
		var ids: Array = CLASS_ITEM_ORDER[cls]
		var n := maxi(1, int(ceil(float(ids.size()) / float(ITEMS_PER_PAGE))))
		for p in range(n):
			pages.append(ids.slice(p * ITEMS_PER_PAGE,
				mini((p + 1) * ITEMS_PER_PAGE, ids.size())))
			meta.append([cls, p + 1, n])
	var order: Array = []
	for page in pages:
		for sid in page:
			order.append(sid)
	_cached_pages = {"pages": pages, "meta": meta, "order": order}
	return _cached_pages


# ─── DETAIL POPUP ITEM (hero_items.py:1508-1653) ──────────────────────
# Label field mekanik per bahasa: key -> [label Indonesia, label English]
const _FIELD_LABELS := {
	"damage": ["Damage", "Damage"],
	"hp": ["Max HP", "Max HP"],
	"hp_pct": ["Max HP", "Max HP"],
	"hp_regen": ["HP Regen", "HP Regen"],
	"armor": ["Armor", "Armor"],
	"attack_speed": ["Attack Speed", "Attack Speed"],
	"crit_chance": ["Peluang Crit", "Crit Chance"],
	"crit_mult": ["Pengali Crit", "Crit Multiplier"],
	"lifesteal": ["Lifesteal", "Lifesteal"],
	"lifesteal_bonus": ["Bonus Lifesteal", "Lifesteal Bonus"],
	"cooldown_reduction": ["Cooldown Reduction", "Cooldown Reduction"],
	"spell_vamp": ["Spell Lifesteal", "Spell Lifesteal"],
	"skill_amp": ["Skill Amp", "Skill Amp"],
	"evasion": ["Evasion", "Evasion"],
	"move_speed_pct": ["Move Speed", "Move Speed"],
	"heal_amp": ["Heal Diterima", "Incoming Heal"],
	"slow_resist": ["Tahan Slow", "Slow Resist"],
	"range_bonus": ["Bonus Jangkauan", "Attack Range Bonus"],
	"hp_threshold": ["Ambang HP", "HP Threshold"],
	"duration": ["Durasi", "Duration"],
	"cooldown": ["Cooldown", "Cooldown"],
	"ally_radius": ["Radius Sekutu", "Ally Radius"],
	"ally_armor": ["Armor Sekutu", "Ally Armor"],
	"ally_attack_speed": ["AS Sekutu", "Ally Attack Speed"],
	"base_block": ["Block Dasar", "Base Block"],
	"max_hp_block_pct": ["Block (% Max HP)", "Block (% Max HP)"],
	"stun": ["Stun", "Stun"],
	"silence": ["Silence", "Silence"],
	"silence_duration": ["Durasi Silence", "Silence Duration"],
	"trigger_enemies": ["Pemicu Musuh Dekat", "Trigger Enemies"],
	"trigger_radius": ["Radius Pemicu", "Trigger Radius"],
	"root_radius": ["Radius Root", "Root Radius"],
	"root_duration": ["Durasi Root", "Root Duration"],
	"proc_chance": ["Peluang Aktif", "Proc Chance"],
	"tick": ["Interval Tick", "Tick Interval"],
	"targets": ["Jumlah Target", "Targets"],
	"radius": ["Radius", "Radius"],
	"slow": ["Slow Gerak", "Move Slow"],
	"atk_slow": ["Slow Serang", "Attack Slow"],
	"slow_duration": ["Durasi Slow", "Slow Duration"],
	"burn_dps": ["Bakar (dmg/dtk)", "Burn (dmg/s)"],
	"burn_duration": ["Durasi Bakar", "Burn Duration"],
	"dash_distance": ["Jarak Dorong", "Dash Distance"],
	"as_bonus": ["Bonus Attack Speed", "Attack Speed Bonus"],
	"heal_pct": ["Heal (% Max HP)", "Heal (% Max HP)"],
	"reflect_pct": ["Pantulan Damage", "Damage Reflect"],
	"damage_amp": ["Amplifikasi Damage", "Damage Amp"],
	"chance": ["Peluang", "Chance"],
	"cleave_pct": ["Splash Damage", "Cleave Damage"],
	"cleave_radius": ["Radius Splash", "Cleave Radius"],
	"out_of_combat_regen_pct": ["Regen Luar Tempur", "Out-of-Combat Regen"],
	"combat_timeout": ["Timeout Tempur", "Combat Timeout"],
	"armor_shred": ["Kikis Armor", "Armor Shred"],
	"charge_time": ["Waktu Isi Muatan", "Charge Time"],
	"enemy_radius": ["Radius Musuh", "Enemy Radius"],
	"enemy_armor_reduction": ["Kurangi Armor Musuh", "Enemy Armor Reduction"],
	"enemy_atk_slow": ["AS Musuh Berkurang", "Enemy AS Reduction"],
	"enemy_anti_heal": ["Anti-Heal Musuh", "Enemy Anti-Heal"],
	"blind": ["Musuh Melenceng", "Enemy Miss Chance"],
	"melee_block": ["Block (Melee)", "Block (Melee)"],
	"ranged_block": ["Block (Ranged)", "Block (Ranged)"],
	"anti_heal": ["Anti-Heal", "Anti-Heal"],
	"max_hp_pct_per_tick": ["Racun (% Max HP/tick)", "Poison (% Max HP/tick)"],
	"cap_damage": ["Batas Damage", "Damage Cap"],
	"damage_pct": ["Damage Tembakan Ekstra", "Extra Shot Damage"],
}

const _GROUP_LABELS := {
	"stats": ["STAT", "STATS"],
	"passive": ["PASIF", "PASSIVE"],
	"active": ["AKTIF", "ACTIVE"],
	"aura": ["AURA", "AURA"],
	"block": ["BLOCK", "BLOCK"],
	"on_attack": ["EFEK SERANGAN", "ON-ATTACK"],
	"multishot": ["MULTISHOT", "MULTISHOT"],
	"bash": ["BASH", "BASH"],
}

const _MECH_GROUPS := ["stats", "passive", "active", "aura", "block",
	"on_attack", "multishot", "bash"]

# Nilai yang ditampilkan sebagai persen
const _PCT_KEYS := [
	"hp_pct", "hp_threshold", "crit_chance", "lifesteal",
	"lifesteal_bonus", "cooldown_reduction", "spell_vamp",
	"skill_amp", "evasion", "move_speed_pct", "heal_amp",
	"slow_resist", "chance", "proc_chance", "max_hp_block_pct",
	"heal_pct", "reflect_pct", "damage_amp", "cleave_pct",
	"out_of_combat_regen_pct", "enemy_atk_slow", "enemy_anti_heal",
	"blind", "slow", "atk_slow", "anti_heal",
	"max_hp_pct_per_tick", "damage_pct",
]

# Nilai dalam frame (60 fps) yang ditampilkan sebagai detik
const _FRAME_KEYS := [
	"duration", "cooldown", "stun", "silence", "silence_duration",
	"tick", "charge_time", "combat_timeout", "slow_duration",
	"burn_duration", "root_duration",
]

# Nilai mekanik yang di Pygame adalah FLOAT murni (bukan int): str(float)
# Python mempertahankan ".0" untuk bilangan bulat (6.0 -> "6.0"), sedangkan
# int -> "6". JSON.parse_string Godot mengubah SEMUA angka jadi float, jadi
# pemisahan int vs float ini dipulihkan lewat daftar ini (dikunci paritas
# oleh HeroItemsParityTest + fixture mechanics).
const _FLOAT_MECH_FIELDS := {
	"leviathan_heart": {"stats": ["hp_regen"]},
	"cleave_axe": {"stats": ["hp_regen"]},
	"octarine_core": {"stats": ["hp_regen"]},
}


## str(float) Python: bilangan bulat float TETAP diberi ".0" (3.0 -> "3.0"),
## bilangan bulat int TIDAK (3 -> "3"). JSON.parse_string Godot mengubah
## SEMUA angka jadi float, jadi `was_float` (asal nilai: float murni vs int)
## disuntik pemanggil — dari _FLOAT_MECH_FIELDS (mechanics) / flag fixture
## `float` (fmt_battery).
static func _py_str(v: Variant, was_float: bool = false) -> String:
	if was_float and v is float:
		var s := str(v)
		if not (s.contains(".") or s.contains("e") or s.contains("E")):
			return s + ".0"
		return s
	return str(v)


## f"{x:g}" Python: format general 6 angka penting, tanpa notasi ilmiah
## untuk rentang nilai item (0.015 .. 12000), buang nol belakang + titik.
static func _py_g(x: float) -> String:
	if is_nan(x) or is_inf(x):
		return str(x)
	if x == 0.0:
		return "0"
	var neg := x < 0.0
	var m := absf(x)
	var e := 0
	while m >= 10.0:
		m /= 10.0
		e += 1
	while m < 1.0:
		m *= 10.0
		e -= 1
	var decimals := maxi(0, 5 - e)
	var s := String.num(absf(x), decimals)
	if s.contains("."):
		while s.ends_with("0"):
			s = s.substr(0, s.length() - 1)
		if s.ends_with("."):
			s = s.substr(0, s.length() - 1)
	return ("-" if neg else "") + s


## Format nilai mekanik item supaya mudah dibaca manusia.
##   crit_mult -> "x2" / "x1.5"; persen -> "25%"; frame -> "5 dtk"/"5s";
##   sisanya -> str(value) gaya Python (was_float menandai float murni).
static func fmt_mech_value(key: String, value: Variant, en: bool = false,
		was_float: bool = false) -> String:
	if key == "crit_mult":
		return "x" + _py_g(float(value))
	if _PCT_KEYS.has(key):
		return _py_g(float(value) * 100.0) + "%"
	if _FRAME_KEYS.has(key):
		var secs: float = float(value) / 60.0
		return _py_g(secs) + ("s" if en else " dtk")
	return _py_str(value, was_float)


## Susun daftar [kind, text] mekanik item dari katalog.
## kind = "header" (nama grup: [AKTIF] Blood Frenzy) atau "bullet"
## ("• label: nilai"). `en` memilih label bahasa English. `item_id`
## dipakai untuk memulihkan field float murni (_FLOAT_MECH_FIELDS) yang
## hilang akibat JSON.parse_string (semua angka jadi float).
static func build_item_mechanics(data: Dictionary, en: bool = false,
		item_id: String = "") -> Array:
	var float_fields: Dictionary = _FLOAT_MECH_FIELDS.get(item_id, {})
	var items: Array = []
	for gkey in _MECH_GROUPS:
		var g: Variant = data.get(gkey)
		if not (g is Dictionary):
			continue
		var gd: Dictionary = g
		if gd.is_empty():
			continue
		var glabel: Array = _GROUP_LABELS[gkey]
		var gname: String = str(gd.get("name", ""))
		var header: String = "[" + str(glabel[1 if en else 0]) + "]"
		if gname != "":
			header += " " + gname
		items.append(["header", header])
		for key in gd:
			if key == "name":
				continue
			var was_float := false
			if float_fields.has(gkey):
				was_float = (float_fields[gkey] as Array).has(key)
			var label = _FIELD_LABELS.get(key, key)
			var lab: String
			if label is Array:
				lab = str(label[1 if en else 0])
			else:
				lab = str(label)
			items.append(["bullet",
				"• " + lab + ": " + fmt_mech_value(str(key), gd[key], en, was_float)])
	return items


# ─── PESANAN FORGE TERTUNDA (hero_items.py:3143-3167) ─────────────────
## Antrian item yang dibeli saat `hero` mati. Antrian melekat pada hero
## agar item tak pernah tertukar dan baru dipindahkan ke inventory
## setelah respawn. Bekerja pada Dictionary maupun Node (get/set).
static func pending_forge_items(hero) -> Array:
	var pending = hero.get("_pending_forge_items")
	if not (pending is Array):
		pending = []
		if hero is Dictionary:
			hero["_pending_forge_items"] = pending
		else:
			hero.set("_pending_forge_items", pending)
	return pending


## Kirim semua pesanan Forge tertunda ke inventory hero. Dipanggil tepat
## setelah respawn. Return daftar id item yang berhasil dikirim; item yang
## tidak muat tetap diantrikan sebagai pengaman.
static func deliver_pending_forge_items(hero) -> Array:
	var pending: Array = pending_forge_items(hero)
	var delivered: Array = []
	var inv = hero.get("items")
	while not pending.is_empty() and inv != null \
			and inv.has_method("add_item") \
			and inv.add_item(str(pending[0])):
		delivered.append(pending.pop_front())
	return delivered


# ─── TARGET TOKO (hero_items.py:3169-3190) ────────────────────────────
## Tentukan penerima pembelian, termasuk hero yang sedang mati.
## Prioritas target tersimpan -> hero terseleksi -> hero hidup pertama ->
## hero mati pertama.
static func resolve_shop_target(game, heroes: Array):
	if heroes == null or heroes.is_empty():
		return null
	var saved = game.get("itemshop_target_hero")
	if saved != null and heroes.has(saved):
		return saved
	var sel = game.get("selected_hero")
	if sel != null and heroes.has(sel):
		return sel
	for h in heroes:
		var alive = h.get("alive")
		if alive == null:
			# Adaptasi Godot: Hero.gd memakai is_dead (pygame: alive).
			alive = not (h.get("is_dead", false) == true)
		if alive == true:
			return h
	return heroes[0]


# ─── PENGALI LEVEL (hero_items.py:2748-2755) ──────────────────────────
## HERO_LEVELS[lvl]["hp_mult"]; level di luar tabel -> 1.0. `hero_levels`
## disuntik (contoh HeroDB.hero_levels_int()) supaya fungsi ini murni.
static func hero_level_mult(level: int, hero_levels: Dictionary) -> float:
	var row = hero_levels.get(level)
	if row is Dictionary:
		return float(row.get("hp_mult", 1.0))
	return 1.0
