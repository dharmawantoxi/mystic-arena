# FASE 20 — TRANSAKSI HERO SHOP META vs oracle _unlock_hero_in_meta_shop
# pygame ASLI (seksi fixture `meta_shop_txn`).
# python tools/test_godot_match_parity.py   (freshness)
# godot --headless --path godot res://tests/MetaShopTxnParityTest.tscn --quit-after 300
#
# Oracle pygame: Menu._unlock_hero_in_meta_shop (_core.py:5298-5328) +
# katalog EFEKTIF get_all_hero_types (def KEDUA _core.py:1255 yang menimpa
# unlock_cost semua hero dengan konstanta flat: starter 0, mini/true 4500)
# + keputusan kartu _draw_meta_hero_card (pill label/kind + status OWNED).
# Yang direplay lewat JALUR PRODUKSI Godot — TIDAK ADA duplikasi rumus:
#
#   * KATALOG  : 222 baris closed-world — kunci hero, unlock_cost,
#                unlock_require_boss, is_boss_hero, boss_class pada
#                HeroDB (heroes.json) wajib persis katalog pygame.
#   * TRANSAKSI: urutan guard katalog -> duplikat -> gate boss -> saldo,
#                pengurangan meta_gold + append purchased (padanan
#                unlocked_heroes), daftar boss tak tersentuh, dan flag
#                diterima; kasus persist membaca file save dari DISK.
#   * KARTU    : matriks 5 state save x 4 hero wakil — meta produksi
#                owned/boss_ready/affordable harus menghasilkan status
#                OWNED / boss-locked / pill yang sama (label FREE hanya
#                untuk cost 0, kind gold hanya saat saldo cukup).
#
# Pemetaan kunci save: pygame purchased_heroes = Godot unlocked_heroes
# (terkunci FASE 13 — catch-up). DEV flags pygame False (fixture); Godot
# tidak punya cabang DEV. SFX tidak diuji (headless).
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainMenuScript = preload("res://scenes/ui/MainMenu.gd")

var _fx: Dictionary = {}
var _failures := 0
var _checks := 0
var _save_before: Dictionary = {}
var _save_file_existed := false
var _save_file_before := ""
var _menu = null


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _expect(cond: bool, tag: String) -> void:
	_checks += 1
	if not cond:
		_failures += 1
		printerr("[MetaShopTxnParityTest] FAIL: ", tag)


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	_save_file_existed = FileAccess.file_exists(SaveManager.SAVE_PATH)
	if _save_file_existed:
		_save_file_before = FileAccess.get_file_as_string(
			SaveManager.SAVE_PATH)
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("meta_shop_txn"):
		_expect(false, "fixture meta_shop_txn belum ada — jalankan "
			+ "tools/test_godot_match_parity.py --write-fixture")
		_finish()
		return
	_fx = fixture["meta_shop_txn"]

	# DEV flags pygame harus off agar cabang DEV tidak menyembunyikan
	# guard saldo (fixture mengunci nilainya; Godot tak punya cabang ini).
	_expect(bool(_fx["dev_flags"]["unlimited_hero_gold"]) == false,
		"DEV_UNLIMITED_HERO_GOLD oracle harus False")
	_expect(bool(_fx["dev_flags"]["topup_enabled"]) == false,
		"DEV_TOPUP_ENABLED oracle harus False")

	_menu = MainMenuScript.new()
	add_child(_menu)

	_test_catalog()
	for case in _fx["txn_cases"]:
		_test_txn(case)
	_test_card_matrix()

	_finish()


# ══════════════════════════════════════════════════════════
#  KATALOG CLOSED-WORLD (222 hero)
# ══════════════════════════════════════════════════════════

func _test_catalog() -> void:
	var rows: Array = _fx["catalog"]
	var pygame_keys := {}
	for row in rows:
		pygame_keys[str(row["hero"])] = true
	var godot_keys := {}
	for hero_type in HeroDB.heroes:
		godot_keys[str(hero_type)] = true
	_expect(pygame_keys.size() == godot_keys.size()
		and pygame_keys == godot_keys,
		"set katalog 222 hero identik (pygame %d vs godot %d)"
		% [pygame_keys.size(), godot_keys.size()])
	for row in rows:
		var hero := str(row["hero"])
		var d: Dictionary = HeroDB.get_hero(hero)
		if d.is_empty():
			_expect(false, "katalog: %s hilang di HeroDB" % hero)
			continue
		_tag_compare(hero, int(d.get("unlock_cost", 600)),
			int(row["unlock_cost"]), "unlock_cost")
		# JSON null (starter tanpa syarat boss) dinormalkan ke "" di kedua
		# sisi — pygame None = tanpa syarat (str(null) = "<null>" jebakan).
		var req_godot = d.get("unlock_require_boss", "")
		var req_godot_str := "" if req_godot == null else str(req_godot)
		var req_pygame := ""
		if row["unlock_require_boss"] != null:
			req_pygame = str(row["unlock_require_boss"])
		_tag_compare(hero, req_godot_str, req_pygame, "unlock_require_boss")
		_tag_compare(hero, bool(d.get("is_boss_hero", false)),
			bool(row["is_boss_hero"]), "is_boss_hero")
		var cls_pygame := ""
		if row["boss_class"] != null:
			cls_pygame = str(row["boss_class"])
		_tag_compare(hero, str(d.get("boss_class", "")), cls_pygame,
			"boss_class")


# ══════════════════════════════════════════════════════════
#  TRANSAKSI (jalur produksi MainMenu._try_unlock_hero)
# ══════════════════════════════════════════════════════════

func _reset_shop_state(gold: int, purchased: Array, bosses: Array) -> void:
	SaveManager.data["meta_gold"] = gold
	SaveManager.data["unlocked_heroes"] = purchased.duplicate()
	SaveManager.data["unlocked_bosses"] = bosses.duplicate()


func _test_txn(case: Dictionary) -> void:
	var tag := str(case["name"])
	_reset_shop_state(int(case["gold_in"]), case["purchased_in"],
		case["bosses_in"])
	# Jalur produksi penuh (validasi + potong gold + append + save + sfx).
	_menu._try_unlock_hero(str(case["hero"]))
	var accepted := str(case["hero"]) in SaveManager.data["unlocked_heroes"]
	_compare(accepted, bool(case["accepted"]), "%s: diterima" % tag)
	_compare(SaveManager.meta_gold(), int(case["meta_gold"]),
		"%s: meta_gold setelah" % tag)
	_compare(_sorted(SaveManager.data["unlocked_heroes"]),
		_sorted(case["purchased"]), "%s: purchased setelah" % tag)
	_compare(_sorted(SaveManager.data["unlocked_bosses"]),
		_sorted(case["bosses"]), "%s: bosses tak tersentuh" % tag)
	# Kasus persist: baca file save dari DISK (pygame SaveManager.load).
	if case.has("disk_meta_gold"):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(
			SaveManager.SAVE_PATH))
		_expect(parsed is Dictionary, "%s: file save terbaca" % tag)
		if parsed is Dictionary:
			_compare(int(parsed.get("meta_gold", -1)),
				int(case["disk_meta_gold"]), "%s: disk meta_gold" % tag)
			_compare(_sorted(parsed.get("unlocked_heroes", [])),
				_sorted(case["disk_purchased"]), "%s: disk purchased" % tag)


# ══════════════════════════════════════════════════════════
#  MATRIKS KARTU (5 state save x 4 hero wakil)
# ══════════════════════════════════════════════════════════

func _test_card_matrix() -> void:
	var states: Dictionary = {
		"gold0_none": [0, [], []],
		"gold4499_none": [4499, [], []],
		"gold4500_none": [4500, [], []],
		"gold4500_allboss": [4500, [], _all_bosses()],
		"owned_all": [0, _all_heroes(), _all_bosses()],
	}
	for st_name in states:
		var cfg: Array = states[st_name]
		_reset_shop_state(int(cfg[0]), cfg[1], cfg[2])
		for row in _fx["card_matrix"]:
			if str(row["state"]) != str(st_name):
				continue
			var hero := str(row["hero"])
			# Grid toko difilter per tab (paritas 4925-4946) — pilih tab
			# yang menampilkan hero ini sebelum membangun ulang.
			var d: Dictionary = HeroDB.get_hero(hero)
			if bool(d.get("is_boss_hero", false)):
				_menu._hero_tab = ("true" if str(
					d.get("boss_class", "mini")) == "true" else "mini")
			else:
				_menu._hero_tab = "starter"
			_menu._show(_menu.State.HERO_SHOP)
			var card := _find_hero_card(hero)
			_expect(card != null, "kartu %s (%s) ada" % [hero, st_name])
			if card == null:
				continue
			var owned := bool(card.get_meta("owned"))
			var boss_ready := bool(card.get_meta("boss_ready"))
			var affordable := bool(card.get_meta("affordable"))
			var cost := int(card.get_meta("unlock_cost"))
			var status := str(row["status"])
			_compare(owned, status == "owned",
				"%s/%s: status owned" % [st_name, hero])
			_compare(boss_ready, status != "boss_locked",
				"%s/%s: status boss_ready" % [st_name, hero])
			_expect((not owned and boss_ready) == (status == "unlock"),
				"%s/%s: status unlock konsisten" % [st_name, hero])
			if status == "unlock":
				_compare(affordable, str(row["kind"]) == "gold",
					"%s/%s: kind gold <-> affordable" % [st_name, hero])
				# label FREE hanya untuk hero gratis (cost 0) — pygame
				# "FREE" if unlock_cost <= 0 else "UNLOCK" (DEV off).
				_compare(cost <= 0, str(row["label"]) == "FREE",
					"%s/%s: label FREE <-> cost 0" % [st_name, hero])


func _find_hero_card(hero_type: String) -> Control:
	for node in _menu._root.find_children("*", "PanelContainer", true, false):
		if node.has_meta("hero_type") \
				and str(node.get_meta("hero_type")) == hero_type:
			return node
	return null


func _all_bosses() -> Array:
	var out := []
	for row in _fx["catalog"]:
		if row["unlock_require_boss"] != null:
			out.append(str(row["unlock_require_boss"]))
	return _sorted(out)


func _all_heroes() -> Array:
	var out := []
	for row in _fx["catalog"]:
		out.append(str(row["hero"]))
	return _sorted(out)


# ══════════════════════════════════════════════════════════
#  UTIL
# ══════════════════════════════════════════════════════════

func _sorted(arr) -> Array:
	var out := []
	for v in arr:
		out.append(str(v))
	out.sort()
	return out


func _tag_compare(hero: String, got, want, field: String) -> void:
	_expect(str(got) == str(want),
		"katalog %s %s (dapet %s, mau %s)" % [hero, field, str(got),
		str(want)])


func _compare(got, want, tag: String) -> void:
	_expect(str(got) == str(want),
		"%s (dapet %s, mau %s)" % [tag, str(got), str(want)])


func _finish() -> void:
	_menu.queue_free()
	SaveManager.data = _save_before
	if _save_file_existed:
		var f := FileAccess.open(SaveManager.SAVE_PATH, FileAccess.WRITE)
		f.store_string(_save_file_before)
		f.close()
	else:
		DirAccess.remove_absolute(
			ProjectSettings.globalize_path(SaveManager.SAVE_PATH))
	print("[MetaShopTxnParityTest] %s: %d cek, %d gagal"
		% ["PASS" if _failures == 0 else "FAIL", _checks, _failures])
	get_tree().quit(0 if _failures == 0 else 1)
