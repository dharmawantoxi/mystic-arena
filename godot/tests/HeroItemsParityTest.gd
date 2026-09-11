# HeroItemsParityTest — paritas port hero_items.py ->
# godot/scripts/core/HeroItems.gd.
#
# Yang dikunci di sini (oracle = fixture match_parity.json["hero_items"],
# dibuat tools/test_godot_match_parity.py FASE 29 dari kode pygame ASLI):
#   1. get_item_class: 33 item -> PHYSICAL/MAGIC/TANK (termasuk override
#      tempest_vane/abyss_breaker -> TANK, magic_only -> MAGIC, item tak
#      dikenal -> PHYSICAL).
#   2. build_shop_pages: 6 halaman SELARAS batas kelas + meta + urutan
#      flatten 33 item (== SHOP_PAGES/SHOP_PAGE_META/ITEM_SHOP_ORDER).
#   3. build_item_mechanics: daftar (kind, text) popup detail untuk
#      SEMUA 33 item, bahasa id DAN en (label + format nilai).
#   4. fmt_mech_value: baterai 58 nilai (persen float "kotor" seperti
#      0.022*100 -> "2.2%", frame /60 -> "dtk"/"s", crit_mult "x…",
#      str(float) yang mempertahankan ".0" untuk 3.0 -> "3.0").
#   5. resolve_shop_target: prioritas tersimpan > terseleksi > hidup
#      pertama > mati pertama (+ kasus kosong + fallback is_dead Godot).
#   6. deliver_pending_forge_items: antrian -> inventory, item yang tak
#      muat/tak dikenal tetap diantrikan.
#   7. hero_level_mult: level 0..20 vs HeroDB.hero_levels_int().
#
# godot --headless --path godot res://tests/HeroItemsParityTest.tscn --quit-after 120
# Require "[HeroItemsParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const ITEMS_JSON := "res://data/items.json"

var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua pesan kegagalan dikumpulkan di sini supaya tercetak ke STDOUT pada
## akhir run (tail log CI langsung memuat alasannya).
var _error_messages: Array[String] = []

var _hi: Dictionary = {}
var _items: Dictionary = {}


## Mock inventory untuk deliver_pending_forge_items: cermin kontrak
## HeroItemInventory.add (id dikenal -> isi slot kosong -> true; penuh/
## tak dikenal -> false). Cek melee/magic-only tak relevan untuk kasus uji
## (dead_edge/moon_shard/steel_aegis), jadi sengaja tidak direplika.
class MockInventory extends RefCounted:
	var slots: Array = []
	var known: Dictionary = {}


	func add_item(item_id: String) -> bool:
		if not known.has(item_id):
			return false
		for i in range(slots.size()):
			if str(slots[i]) == "":
				slots[i] = item_id
				return true
		return false


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	GameManager.in_menu = true
	GameManager.state = "idle"
	_load_section()
	if _failures == 0:
		_test_item_class()
		_test_shop_pages()
		_test_mechanics()
		_test_fmt_battery()
		_test_resolve()
		_test_deliver()
		_test_level_mult()
	_finish()


func _load_section() -> void:
	var fixture: Variant = JSON.parse_string(
		FileAccess.get_file_as_string(FIXTURE))
	_expect(fixture is Dictionary and (fixture as Dictionary).has(
		"hero_items"), "fixture hero_items ada")
	if not (fixture is Dictionary
			and (fixture as Dictionary).has("hero_items")):
		return
	_hi = (fixture as Dictionary)["hero_items"]
	var items: Variant = JSON.parse_string(
		FileAccess.get_file_as_string(ITEMS_JSON))
	_expect(items is Dictionary and (items as Dictionary).size() == 33,
		"items.json 33 item")
	if items is Dictionary:
		_items = items


# ── 1) kelas item ──────────────────────────────────────────────────────
func _test_item_class() -> void:
	var exp: Dictionary = _hi["item_class"]
	_expect(exp.size() == 33, "item_class 33 (dapat %d)" % exp.size())
	for sid in exp:
		_expect(HeroItems.get_item_class(_items, str(sid)) == str(exp[sid]),
			"class %s" % str(sid))
	_expect(HeroItems.get_item_class(_items, "item_tak_ada")
		== HeroItems.CLASS_PHYSICAL, "item tak dikenal -> physical")


# ── 2) halaman toko ────────────────────────────────────────────────────
func _test_shop_pages() -> void:
	var exp: Dictionary = _hi["shop_pages"]
	var got: Dictionary = HeroItems.build_shop_pages()
	_expect_deep(got.get("pages"), exp["pages"], "shop pages")
	_expect_deep(got.get("meta"), exp["meta"], "shop meta")
	_expect_deep(got.get("order"), exp["order"], "shop order")
	_expect((got["order"] as Array).size() == 33, "order 33 item")


# ── 3) mekanik detail (id + en) ────────────────────────────────────────
func _test_mechanics() -> void:
	var exp: Dictionary = _hi["mechanics"]
	var exp_en: Dictionary = _hi["mechanics_en"]
	_expect(exp.size() == 33 and exp_en.size() == 33, "mechanics 33+33")
	for sid in exp:
		var data: Dictionary = _items.get(str(sid), {})
		_expect_deep(HeroItems.build_item_mechanics(data, false, str(sid)),
			exp[sid], "mechanics.%s" % str(sid))
		_expect_deep(HeroItems.build_item_mechanics(data, true, str(sid)),
			exp_en[sid], "mechanics_en.%s" % str(sid))


# ── 4) baterai format nilai ────────────────────────────────────────────
func _test_fmt_battery() -> void:
	for c in (_hi["fmt_battery"] as Array):
		var key := str(c["key"])
		var v: Variant = c["value"]
		var en := (c.get("en", false) == true)
		var was_float := (c.get("float", false) == true)
		var out: String = HeroItems.fmt_mech_value(key, v, en, was_float)
		_expect(out == str(c["out"]),
			"fmt %s %s -> %s (ekspektasi %s)" % [key, str(v), out,
				str(c["out"])])


# ── 5) target toko ─────────────────────────────────────────────────────
func _test_resolve() -> void:
	for c in (_hi["resolve_cases"] as Array):
		var alive: Array = c["alive"]
		var heroes: Array = []
		for i in range(alive.size()):
			heroes.append({"alive": (alive[i] == true), "idx": i})
		var game := {"itemshop_target_hero": null, "selected_hero": null}
		var saved = c["saved"]
		var selected = c["selected"]
		if saved != null:
			game["itemshop_target_hero"] = heroes[int(saved)]
		if selected != null:
			game["selected_hero"] = heroes[int(selected)]
		var chosen = HeroItems.resolve_shop_target(game, heroes)
		if c["expect"] == null:
			_expect(chosen == null, "resolve tanpa hero")
		else:
			_expect(chosen != null and int(chosen.get("idx", -1))
				== int(c["expect"]),
				"resolve saved=%s sel=%s -> %d" % [str(saved),
					str(selected), int(c["expect"])])
	# Adaptasi Godot: hero tanpa `alive` memakai fallback NOT is_dead.
	var heroes2: Array = [{"is_dead": false, "idx": 0},
		{"is_dead": true, "idx": 1}]
	var chosen2 = HeroItems.resolve_shop_target(
		{"itemshop_target_hero": null, "selected_hero": null}, heroes2)
	_expect(chosen2 != null and int(chosen2.get("idx")) == 0,
		"resolve fallback is_dead pilih hero hidup")


# ── 6) kirim pesanan forge tertunda ────────────────────────────────────
func _test_deliver() -> void:
	for c in (_hi["deliver_cases"] as Array):
		var free_slots := int(c["free_slots"])
		var inv := MockInventory.new()
		inv.slots.resize(6)
		for i in range(6):
			inv.slots[i] = ""
		var fill := 6 - free_slots
		for i in range(fill):
			inv.slots[i] = "moon_shard"
		inv.known = {"dead_edge": true, "moon_shard": true,
			"steel_aegis": true}
		var pending: Array = []
		for p in c["pending"]:
			pending.append(str(p))
		var hero := {"_pending_forge_items": pending, "items": inv}
		var delivered: Array = HeroItems.deliver_pending_forge_items(hero)
		_expect_deep(delivered, c["delivered"], "deliver dikirim")
		_expect_deep(hero["_pending_forge_items"], c["remaining"],
			"deliver sisa antrean")


# ── 7) pengali level ───────────────────────────────────────────────────
func _test_level_mult() -> void:
	var levels: Dictionary = HeroDB.hero_levels_int()
	for c in (_hi["hero_level_mult"] as Array):
		_near(HeroItems.hero_level_mult(int(c["level"]), levels),
			float(c["out"]), "level_mult %d" % int(c["level"]), 1e-12)


# ── util ────────────────────────────────────────────────────────────────
func _near(a: float, b: float, message: String, eps: float) -> void:
	_checks += 1
	if absf(a - b) > eps:
		var line := "[HeroItemsParityTest] %s: %.10f != %.10f" % [message, a, b]
		_error_messages.append(line)
		_failures += 1
		push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		var line := "[HeroItemsParityTest] " + message
		_error_messages.append(line)
		_failures += 1
		push_error(line)


## Banding eksak (string/int/bool/null + struktur bersarang).
func _deep_eq(a: Variant, b: Variant) -> bool:
	if a == null and b == null:
		return true
	if a == null or b == null:
		return false
	if a is Array and b is Array:
		if a.size() != b.size():
			return false
		for i in range(a.size()):
			if not _deep_eq(a[i], b[i]):
				return false
		return true
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size():
			return false
		for k in a:
			if not b.has(k) or not _deep_eq(a[k], b[k]):
				return false
		return true
	return a == b


func _expect_deep(a: Variant, b: Variant, message: String) -> void:
	_checks += 1
	if not _deep_eq(a, b):
		var line := "[HeroItemsParityTest] " + message
		_error_messages.append(line)
		_failures += 1
		push_error(line)


func _finish() -> void:
	if _done:
		return
	_done = true
	get_tree().paused = false
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print("[HeroItemsParityTest] PASS: hero_items.py ↔ Godot (%d checks)" % _checks)
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[HeroItemsParityTest] %d failures dari %d checks" % [_failures, _checks])
		print("[HeroItemsParityTest] FAIL: %d failures dari %d checks" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
