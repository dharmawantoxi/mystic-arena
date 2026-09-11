# HeroArchetypesParityTest — replay oracle hero_archetypes.py terhadap
# HeroArchetypes.gd (port helper + data JSON hasil convert_to_godot.py).
#
# Fixture: res://tests/fixtures/hero_archetypes.json
#   (regenerasi: python3 tools/gen_hero_archetypes_fixture.py)
#
# Yang dikunci:
#   1. konstanta desain (ARMOR_FACTOR/MAX, MR_MAX, base/mods/scale)
#   2. get_archetype + school_of untuk 222 hero x 7 kasus stats
#      (override dmg_type valid/invalid/falsy, hero tak dikenal -> derived)
#   3. get_boss_resistances 216 boss x {mini,true} + boss tak dikenal
#   4. resist_from_profile semua profil x kelas (skala kalibrasi & mentah)
#   5. physical_mitigation
#   6. integrasi: HeroDB.get_balanced_stats.dmg_school & Boss armor/MR
#      dari BossDB cocok dengan helper.
#
# godot --headless --path godot res://tests/HeroArchetypesParityTest.tscn --quit-after 60
# Require "[HeroArchetypesParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/hero_archetypes.json"

var _failures: int = 0
var _checks: int = 0
var _error_messages: Array[String] = []


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var fx := _load_fixture()
	if fx.is_empty():
		_fail("fixture kosong / tidak terbaca: %s" % FIXTURE)
		_finish()
		return
	_test_constants(fx["constants"])
	_test_tables(fx)
	_test_archetypes(fx["archetypes"])
	_test_boss_resistances(fx["boss_resistances"])
	_test_profiles(fx["profiles"])
	_test_mitigation(fx["mitigation"])
	_test_integration()
	_finish()


func _load_fixture() -> Dictionary:
	if not FileAccess.file_exists(FIXTURE):
		return {}
	var f := FileAccess.open(FIXTURE, FileAccess.READ)
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if parsed is Dictionary else {}


func _test_constants(c: Dictionary) -> void:
	_near(HeroArchetypes.ARMOR_FACTOR, float(c["ARMOR_FACTOR"]), "ARMOR_FACTOR", 1e-9)
	_expect(HeroArchetypes.ARMOR_MAX == int(c["ARMOR_MAX"]), "ARMOR_MAX")
	_near(HeroArchetypes.MR_MAX, float(c["MR_MAX"]), "MR_MAX", 1e-9)
	_expect(HeroArchetypes.DEFAULT_DMG_TYPE == str(c["DEFAULT_DMG_TYPE"]), "DEFAULT_DMG_TYPE")
	_near(HeroArchetypes.BOSS_RESIST_TARGET_RATIO, float(c["BOSS_RESIST_TARGET_RATIO"]),
		"BOSS_RESIST_TARGET_RATIO", 1e-9)
	for cls in c["BOSS_RESIST_BASE"]:
		var want: Array = c["BOSS_RESIST_BASE"][cls]
		var got: Array = HeroArchetypes.BOSS_RESIST_BASE.get(cls, [])
		_expect(got.size() == 2, "BOSS_RESIST_BASE[%s] ada" % cls)
		if got.size() == 2:
			_near(float(got[0]), float(want[0]), "BOSS_RESIST_BASE[%s].armor" % cls, 1e-9)
			_near(float(got[1]), float(want[1]), "BOSS_RESIST_BASE[%s].mr" % cls, 1e-9)
	_expect(HeroArchetypes.BOSS_RESIST_BASE.size() == c["BOSS_RESIST_BASE"].size(),
		"BOSS_RESIST_BASE jumlah kelas")
	for p in c["BOSS_RESIST_PROFILE_MODS"]:
		var want: Array = c["BOSS_RESIST_PROFILE_MODS"][p]
		var got: Array = HeroArchetypes.BOSS_RESIST_PROFILE_MODS.get(p, [])
		_expect(got.size() == 2, "BOSS_RESIST_PROFILE_MODS[%s] ada" % p)
		if got.size() == 2:
			_near(float(got[0]), float(want[0]), "PROFILE_MODS[%s].d_armor" % p, 1e-9)
			_near(float(got[1]), float(want[1]), "PROFILE_MODS[%s].d_mr" % p, 1e-9)
	_expect(HeroArchetypes.BOSS_RESIST_PROFILE_MODS.size() == c["BOSS_RESIST_PROFILE_MODS"].size(),
		"BOSS_RESIST_PROFILE_MODS jumlah profil")
	for cls in c["BOSS_RESIST_SCALE"]:
		var want: Dictionary = c["BOSS_RESIST_SCALE"][cls]
		var got: Dictionary = HeroArchetypes.BOSS_RESIST_SCALE.get(cls, {})
		_near(float(got.get("armor", -1)), float(want["armor"]), "SCALE[%s].armor" % cls, 1e-9)
		_near(float(got.get("mr", -1)), float(want["mr"]), "SCALE[%s].mr" % cls, 1e-9)


func _test_tables(fx: Dictionary) -> void:
	_expect(HeroArchetypes.archetypes().size() == int(fx["archetype_count"]),
		"hero_archetypes.json %d entri (fixture %d)" % [
			HeroArchetypes.archetypes().size(), int(fx["archetype_count"])])
	_expect(HeroArchetypes.boss_resistances().size() == int(fx["boss_resist_count"]),
		"boss_resistances.json %d entri (fixture %d)" % [
			HeroArchetypes.boss_resistances().size(), int(fx["boss_resist_count"])])


func _test_archetypes(rows: Array) -> void:
	for r in rows:
		var stats: Dictionary = r["stats"]
		var tag := "%s#%d" % [str(r["hero"]), int(r["case"])]
		var got := HeroArchetypes.get_archetype(str(r["hero"]), stats)
		_expect(str(got.get("dmg_type", "")) == str(r["dmg_type"]),
			"%s dmg_type %s != %s" % [tag, got.get("dmg_type"), r["dmg_type"]])
		_expect(str(got.get("playstyle", "")) == str(r["playstyle"]),
			"%s playstyle %s != %s" % [tag, got.get("playstyle"), r["playstyle"]])
		_expect(str(got.get("tier", "")) == str(r["tier"]),
			"%s tier %s != %s" % [tag, got.get("tier"), r["tier"]])
		_expect(int(got.get("power", 0)) == int(r["power"]),
			"%s power %s != %s" % [tag, got.get("power"), r["power"]])
		_expect(bool(got.get("derived", false)) == bool(r["derived"]),
			"%s derived %s != %s" % [tag, got.get("derived", false), r["derived"]])
		_expect(HeroArchetypes.school_of(str(r["hero"]), stats) == str(r["school"]),
			"%s school_of != %s" % [tag, r["school"]])
	# get_archetype harus mengembalikan salinan (pygame mengembalikan dict
	# tabel langsung, tapi Godot tidak boleh membiarkan pemanggil merusak cache)
	var a := HeroArchetypes.get_archetype("kaizen")
	a["dmg_type"] = "MAGIC"
	_expect(HeroArchetypes.get_archetype("kaizen")["dmg_type"] == "PHYSICAL",
		"get_archetype mengembalikan salinan, cache tidak berubah")


func _test_boss_resistances(rows: Array) -> void:
	for r in rows:
		var got := HeroArchetypes.get_boss_resistances(str(r["boss"]), str(r["boss_class"]))
		var tag := "%s/%s" % [str(r["boss"]), str(r["boss_class"])]
		_expect(int(got[0]) == int(r["armor"]),
			"%s armor %d != %d" % [tag, int(got[0]), int(r["armor"])])
		_near(float(got[1]), float(r["magic_resist"]), "%s magic_resist" % tag, 1e-9)


func _test_profiles(rows: Array) -> void:
	for r in rows:
		var p := str(r["profile"])
		var cls := str(r["boss_class"])
		var sc: Dictionary = HeroArchetypes.BOSS_RESIST_SCALE.get(cls, {})
		var scaled := HeroArchetypes.resist_from_profile(p, cls, {}, {},
			float(sc.get("armor", 1.0)), float(sc.get("mr", 1.0)))
		var raw := HeroArchetypes.resist_from_profile(p, cls)
		var tag := "profil %s/%s" % [p, cls]
		_expect(int(scaled[0]) == int(r["scaled"][0]),
			"%s scaled.armor %d != %d" % [tag, int(scaled[0]), int(r["scaled"][0])])
		_near(float(scaled[1]), float(r["scaled"][1]), "%s scaled.mr" % tag, 1e-9)
		_expect(int(raw[0]) == int(r["raw"][0]),
			"%s raw.armor %d != %d" % [tag, int(raw[0]), int(r["raw"][0])])
		_near(float(raw[1]), float(r["raw"][1]), "%s raw.mr" % tag, 1e-9)


func _test_mitigation(rows: Array) -> void:
	for r in rows:
		_near(HeroArchetypes.physical_mitigation(float(r["armor"])), float(r["mult"]),
			"physical_mitigation(%s)" % str(r["armor"]), 1e-9)


func _test_integration() -> void:
	# HeroDB: dmg_school/playstyle ikut arketipe (bukan heroes.json yang
	# selalu PHYSICAL).
	var n_magic := 0
	for ht in HeroDB.heroes:
		var s: Dictionary = HeroDB.get_balanced_stats(ht)
		var want := HeroArchetypes.school_of(ht)
		if want == "magic":
			n_magic += 1
		_expect(str(s.get("dmg_school", "")) == want,
			"HeroDB %s dmg_school %s != %s" % [ht, s.get("dmg_school"), want])
		_expect(str(s.get("playstyle", "")) == str(HeroArchetypes.get_archetype(ht)["playstyle"]),
			"HeroDB %s playstyle" % ht)
	_expect(n_magic > 0, "ada hero MAGIC di HeroDB (%d)" % n_magic)
	# BossDB (hasil convert) harus sama dengan helper — bosses.json memakai
	# fungsi pygame yang sama saat ekspor.
	var n_boss := 0
	for bt in BossDB.bosses:
		var b: Dictionary = BossDB.bosses[bt]
		if not b.has("armor") or not b.has("magic_resist"):
			continue
		n_boss += 1
		var res := HeroArchetypes.get_boss_resistances(bt, str(b.get("boss_class", "mini")))
		_expect(int(b["armor"]) == int(res[0]),
			"BossDB %s armor %d != helper %d" % [bt, int(b["armor"]), int(res[0])])
		_near(float(b["magic_resist"]), float(res[1]), "BossDB %s magic_resist" % bt, 1e-6)
	_expect(n_boss > 0, "BossDB memuat armor/MR (%d boss)" % n_boss)


func _fail(message: String) -> void:
	_failures += 1
	var line := "[HeroArchetypesParityTest] %s" % message
	_error_messages.append(line)
	if _error_messages.size() <= 40:
		push_error(line)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_fail("%s: %.6f != %.6f" % [message, a, b])


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _finish() -> void:
	if _failures == 0:
		print("[HeroArchetypesParityTest] PASS: %d cek arketipe/resistansi/mitigasi" % _checks)
		print("[HeroArchetypesParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[HeroArchetypesParityTest] %d failures dari %d checks" % [_failures, _checks])
		print("[HeroArchetypesParityTest] FAIL: %d failures dari %d checks" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
