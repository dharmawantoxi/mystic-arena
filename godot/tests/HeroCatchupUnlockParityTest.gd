# HeroCatchupUnlockParityTest — paritas SUMBER unlock catch-up hero
# (FASE 11, progresi lintas-save) vs oracle pygame.
#
# Rumus catch-up sendiri (HeroDB.catchup_base ↔
# hero_balance.starter_catchup_stats) sudah ada sebelumnya, TAPI angka
# masukannya — jumlah hero non-starter yang dimiliki pemain — selalu 0 di
# Godot karena tidak ada yang membaca daftar unlock lintas-save. Efeknya
# setiap save berperilaku seperti save BARU pygame (bonus starter penuh
# ×1.40 HP / ×1.272 damage) walau roster pemain sudah penuh.
#
# Rantai sumber di pygame (yang diport):
#   save 'purchased_heroes'  (_system.SaveManager.load / get_empty_save)
#     -> Game.reset          (_core.py:1593-1604, + AUTO-GRANT 'kaizen')
#     -> __main__.game_instance.purchased_heroes
#     -> Hero.__init__       (_entity.py:3355-3363)
#          hero_balance.boss_unlocks_for_purchases(...) — len() hero yang
#          BUKAN starter; di luar match (game_instance None) = 0.
#
# Di Godot: SaveManager.data["unlocked_heroes"] (kunci lama Godot =
# padanan purchased_heroes) -> GameManager.purchased_heroes (diikat
# GameManager.start_level, dilepas return_to_menu) ->
# GameManager.catchup_unlocks() -> Hero._catchup_unlocks().
#
# Fixture: match_parity.json["hero_catchup_unlocks"] (objek biasa) berisi
#   rules         : kunci save + starter grant hasil AST Game.reset,
#                   STARTER_HEROES, konstanta kurva catch-up,
#   save_backfill : SaveManager.load() pygame atas berkas slot lama,
#   unlock_counts : boss_unlocks_for_purchases() per isi save,
#   mults         : starter_catchup() per hero × unlocks × level,
#   hero_stats    : Hero pygame SUNGGUHAN (base_hp/base_damage/max_hp/
#                   damage, termasuk setelah upgrade()).
#
# Tes ini TIDAK PERNAH menulis berkas save: state SaveManager.data
# di-snapshot di awal, diubah di memori saja (bind persist=false), dan
# dikembalikan di akhir.
#
# godot --headless --path godot res://tests/HeroCatchupUnlockParityTest.tscn --quit-after 120
# Require "[HeroCatchupUnlockParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const HeroScene = preload("res://scenes/hero/Hero.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

var _failures: int = 0
var _checks: int = 0
var _done := false
var _error_messages: Array[String] = []
var _save_backup: Dictionary = {}


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("hero_catchup_unlocks"):
		push_error("[HeroCatchupUnlockParityTest] fixture hero_catchup_unlocks "
			+ "belum ada — jalankan tools/test_godot_match_parity.py --write-fixture")
		_failures += 1
		_finish()
		return
	var cu: Dictionary = fixture["hero_catchup_unlocks"]

	# Harness = di luar match; state save disimpan lalu dipulihkan.
	_save_backup = SaveManager.data.duplicate(true)
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)

	_test_rules(cu["rules"])
	_test_save_backfill(cu["rules"], cu["save_backfill"])
	_test_unlock_counts(cu["unlock_counts"])
	_test_mults(cu["mults"])
	_test_hero_stats(cu["unlock_counts"], cu["hero_stats"])
	_test_menu_release()

	# Pulihkan save apa adanya (tanpa menulis berkas).
	SaveManager.data = _save_backup
	GameManager.purchased_heroes = []
	_finish()


# ══════════════════════════════════════════════════════════
#  1. ATURAN SUMBER (kunci save, starter, konstanta kurva)
# ══════════════════════════════════════════════════════════

func _test_rules(rules: Dictionary) -> void:
	var starters: Array = rules["starter_heroes"]
	_expect(starters.size() == HeroDB.STARTER_HEROES.size(),
		"jumlah STARTER_HEROES %d != oracle %d"
			% [HeroDB.STARTER_HEROES.size(), starters.size()])
	for ht in starters:
		_expect(str(ht) in HeroDB.STARTER_HEROES,
			"starter %s hilang dari HeroDB.STARTER_HEROES" % str(ht))
	# Starter yang di-grant otomatis ke save kosong (pygame: 'kaizen').
	var grant: Array = rules["starter_grant"]
	_expect(grant.size() == 1 and str(grant[0]) == str(HeroDB.STARTER_HEROES[0]),
		"auto-grant starter Godot %s != oracle %s"
			% [str(HeroDB.STARTER_HEROES[0]), str(grant)])
	# Kunci save pygame 'purchased_heroes' = kunci Godot 'unlocked_heroes'
	# (nama lama dipertahankan supaya save Godot yang sudah ada tidak rusak).
	_expect(str(rules["save_key"]) == "purchased_heroes",
		"kunci save pygame berubah: %s — perbarui pemetaan SaveManager"
			% str(rules["save_key"]))
	_expect(SaveManager.data.has("unlocked_heroes"),
		"SaveManager Godot kehilangan kunci unlocked_heroes")
	# Konstanta kurva (mirror HeroDB.starter_catchup_mults).
	_expect(bool(rules["enabled"]), "ENABLE_STARTER_CATCHUP mati di pygame")
	_near(float(rules["catchup_max"]), 1.32, "STARTER_CATCHUP_MAX")
	_near(float(rules["catchup_ref"]), 12.0, "STARTER_CATCHUP_REF")
	_near(float(rules["level_lv0"]), 1.0, "STARTER_CATCHUP_LV0")
	_near(float(rules["level_lv1"]), 8.0, "STARTER_CATCHUP_LV1")
	_near(float(rules["level_decay"]), 0.20, "STARTER_CATCHUP_DECAY")
	_near(float(rules["hp_share"]), 1.25, "bagi bonus HP")
	_near(float(rules["dmg_share"]), 0.85, "bagi bonus damage")


# ══════════════════════════════════════════════════════════
#  2. SAVE LAMA — unlock tidak boleh hilang
# ══════════════════════════════════════════════════════════

## Oracle memuat berkas slot pygame yang formatnya lama; Godot memakai
## berkas save sendiri, jadi yang dibandingkan adalah HASIL yang penting:
##   • setiap hero yang ada di save lama TETAP ter-unlock sesudah backfill,
##   • jumlah unlock catch-up sama dengan pygame.
## Beda yang DISENGAJA (dan tidak memengaruhi angka di atas): Godot
## memberi starter saat backfill/save load, pygame saat match dimulai —
## keduanya menghasilkan 0 unlock untuk save kosong.
func _test_save_backfill(rules: Dictionary, cases: Array) -> void:
	var save_key := str(rules["save_key"])
	for case in cases:
		var name := str(case["name"])
		var stored: Dictionary = case["stored"]
		# Bangun ulang save Godot dari isi berkas lama (kunci pygame
		# purchased_heroes -> unlocked_heroes).
		var data := {"meta_gold": int(stored.get("meta_gold", 0))}
		if stored.has(save_key):
			data["unlocked_heroes"] = (stored[save_key] as Array).duplicate()
		SaveManager.data = data
		SaveManager._backfill()
		for ht in case["loaded_purchased"]:
			_expect(SaveManager.is_unlocked(str(ht)),
				"%s: unlock lama %s HILANG setelah backfill" % [name, str(ht)])
		GameManager.bind_purchased_heroes(false)
		_expect(GameManager.catchup_unlocks() == int(case["unlocks"]),
			"%s: unlocks %d != oracle %d" % [name, GameManager.catchup_unlocks(),
				int(case["unlocks"])])
		# Backfill/bind tidak boleh membuang unlock apa pun dari save.
		var arr: Array = SaveManager.data["unlocked_heroes"]
		_expect(arr.size() >= (case["loaded_purchased"] as Array).size(),
			"%s: daftar unlock menyusut (%d < %d)"
				% [name, arr.size(), (case["loaded_purchased"] as Array).size()])


# ══════════════════════════════════════════════════════════
#  3. JUMLAH UNLOCK PER ISI SAVE
# ══════════════════════════════════════════════════════════

func _test_unlock_counts(cases: Array) -> void:
	for case in cases:
		var name := str(case["name"])
		var purchased = case["purchased"]
		var want := int(case["unlocks"])
		if purchased == null:
			# game_instance None (menu utama): daftar tidak diikat -> 0.
			GameManager.purchased_heroes = []
			_expect(GameManager.catchup_unlocks() == want,
				"%s: di luar match harus 0, dapat %d"
					% [name, GameManager.catchup_unlocks()])
			continue
		_set_save_roster(purchased)
		_expect(GameManager.catchup_unlocks() == want,
			"%s: unlocks %d != oracle %d"
				% [name, GameManager.catchup_unlocks(), want])
		# Fungsi murni juga diuji langsung (dipakai kode lain nanti).
		_expect(GameManager.boss_unlocks_for_purchases(purchased) == want,
			"%s: boss_unlocks_for_purchases %d != oracle %d"
				% [name, GameManager.boss_unlocks_for_purchases(purchased), want])


# ══════════════════════════════════════════════════════════
#  4. MULTIPLIER CATCH-UP (hero × unlocks × level)
# ══════════════════════════════════════════════════════════

func _test_mults(rows: Array) -> void:
	for row in rows:
		var m := HeroDB.starter_catchup_mults(str(row["hero"]),
			int(row["unlocks"]), int(row["level"]))
		var tag := "%s u%d lv%d" % [str(row["hero"]), int(row["unlocks"]),
			int(row["level"])]
		_near(m.x, float(row["hp"]), tag + " hp_mult", 0.000001)
		_near(m.y, float(row["dmg"]), tag + " dmg_mult", 0.000001)


# ══════════════════════════════════════════════════════════
#  5. STAT HERO SUNGGUHAN (node Hero.gd + save terisi)
# ══════════════════════════════════════════════════════════

func _test_hero_stats(cases: Array, rows: Array) -> void:
	var roster_by_case := {}
	for case in cases:
		roster_by_case[str(case["name"])] = case["purchased"]
	for row in rows:
		var case_name := str(row["case"])
		var purchased = roster_by_case.get(case_name)
		if purchased == null:
			GameManager.purchased_heroes = []
		else:
			_set_save_roster(purchased)
		var tag := "%s/%s%s" % [str(row["hero"]), case_name,
			"" if int(row["level_ups"]) == 0 else "+%d" % int(row["level_ups"])]
		_expect(GameManager.catchup_unlocks() == int(row["unlocks"]),
			"%s: unlocks %d != oracle %d" % [tag, GameManager.catchup_unlocks(),
				int(row["unlocks"])])
		var hero = HeroScene.instantiate()
		hero.hero_type = str(row["hero"])
		hero.team = "blue"
		hero.position = Vector2(300.0, 200.0)
		add_child(hero) # _ready sinkron: apply_hero_data -> catchup_base
		hero.set_physics_process(false)
		for i in range(int(row["level_ups"])):
			_expect(hero.upgrade(), "%s: upgrade() ditolak" % tag)
		_expect(int(hero.level) == int(row["level"]),
			"%s: level %d != oracle %d" % [tag, int(hero.level), int(row["level"])])
		_near(float(hero.base_hp), float(row["base_hp"]), tag + " base_hp", 0.001)
		_near(float(hero.base_damage), float(row["base_damage"]),
			tag + " base_damage", 0.001)
		_near(float(hero.max_hp), float(row["max_hp"]), tag + " max_hp", 0.001)
		_near(float(hero.damage), float(row["damage"]), tag + " damage", 0.001)
		hero.free()


# ══════════════════════════════════════════════════════════
#  6. KELUAR KE MENU MELEPAS IKATAN, BUKAN MENGHAPUS SAVE
# ══════════════════════════════════════════════════════════

func _test_menu_release() -> void:
	_set_save_roster(["kaizen", "abaddon", "gornak"])
	_expect(GameManager.catchup_unlocks() == 2, "pra-menu: 2 unlock")
	GameManager.return_to_menu()
	_expect(GameManager.catchup_unlocks() == 0,
		"di menu utama catch-up memakai 0 unlock (game_instance None)")
	var arr: Array = SaveManager.data["unlocked_heroes"]
	_expect(arr.size() == 3 and "abaddon" in arr and "gornak" in arr,
		"return_to_menu TIDAK BOLEH menghapus unlock di save: %s" % str(arr))
	# Unlock baru di tengah match langsung terbaca (list save dibagi
	# referensi, paritas Game.purchased_heroes pygame).
	GameManager.bind_purchased_heroes(false)
	SaveManager.data["unlocked_heroes"].append("morgath")
	_expect(GameManager.catchup_unlocks() == 3,
		"unlock baru saat match berjalan harus langsung terhitung")
	GameManager.purchased_heroes = []
	GameManager.in_menu = true
	GameManager.state = "idle"


# ══════════════════════════════════════════════════════════
#  UTILITAS
# ══════════════════════════════════════════════════════════

## Pasang isi save (in-memory) lalu ikat seperti awal match — persist=false
## supaya berkas save pemain tidak pernah ditulis harness.
func _set_save_roster(purchased) -> void:
	SaveManager.data["unlocked_heroes"] = (purchased as Array).duplicate()
	GameManager.bind_purchased_heroes(false)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_failures += 1
		var line := "[HeroCatchupUnlockParityTest] %s: %.6f != %.6f" % [message, a, b]
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		var line := "[HeroCatchupUnlockParityTest] " + message
		_error_messages.append(line)
		if _error_messages.size() <= 60:
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
		print("[HeroCatchupUnlockParityTest] PASS: sumber unlock catch-up "
			+ "(save purchased_heroes -> GameManager -> Hero) = oracle pygame")
		print("[HeroCatchupUnlockParityTest] PASS: %d pemeriksaan" % _checks)
		print("[HeroCatchupUnlockParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[HeroCatchupUnlockParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[HeroCatchupUnlockParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
