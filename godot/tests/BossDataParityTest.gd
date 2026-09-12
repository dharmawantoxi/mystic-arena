# BossDataParityTest — FASE 32 (B): pipeline data bosses/boss_data.py.
#
# `boss_data.py` menjalankan lima fungsi pada saat import dan MENIMPA tabelnya
# sendiri (rebalance piecewise -> smoothing monoton -> curve override ->
# normalisasi stat hero_unlock -> normalisasi range). `BossData.gd` mem-port
# kelimanya; `BossDB.rebuild_from_pristine()` memakainya sebagai jalur
# pemulihan katalog.
#
# Fixture `tests/fixtures/boss_data.json` direkam oleh
# tools/test_boss_data_parity.py dari modul boss_data ASLI (bukan salinan
# rumus Godot): 216 boss x 7 field angka + 7 field hero_unlock, jadwal level,
# probe helper statis (round banker's, slot wave, least-squares), dan fit
# trend NYATA atas data 216 boss.
#
# Yang diuji di sini:
#   1. `BossData.build(pristine, schedule)` == fixture, field demi field;
#   2. `BossData.schedule_from_levels(levels.json)` == jadwal fixture;
#   3. probe helper statis (termasuk gotcha GDScript: pow(d,2), banker's
#      round, pembagian float, sort stabil);
#   4. build() TIDAK memutasi pristine dan deterministik (dijalankan 2x);
#   5. katalog runtime BossDB (bosses.json hasil baker) == hasil hitung ulang;
#   6. jalur pemulihan BossDB.rebuild_from_pristine() menghasilkan 216 baris
#      dengan angka yang sama.
#
# godot --headless --path godot res://tests/BossDataParityTest.tscn --quit-after 120
# Require "[BossDataParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/boss_data.json"
const PRISTINE := "res://data/boss_pristine.json"

## Toleransi untuk nilai float hasil least-squares (harus cukup ketat untuk
## menangkap pow(d,2) vs d*d dan pembagian integer, cukup longgar untuk selisih
## ulp antar platform libm).
const FLOAT_TOL := 1e-9

var _fixture: Dictionary = {}
var _pristine: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua kegagalan dikumpulkan supaya tercetak di tail log CI.
var _error_messages: Array[String] = []


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if _fixture == null or not _fixture.has("final"):
		_fail("fixture boss_data.json belum ada / rusak — jalankan "
			+ "tools/test_boss_data_parity.py --write-fixture")
		_finish()
		return
	_pristine = BossData.load_pristine(PRISTINE)
	if _pristine.is_empty():
		_fail("boss_pristine.json tidak bisa dimuat dari res://data/")
		_finish()
		return
	GameManager.in_menu = true
	GameManager.state = "idle"

	var schedule: Array = _test_schedule()
	var built: Dictionary = BossData.build(_pristine, schedule)
	_test_counts(built)
	_test_final_tables(built)
	_test_probes()
	_test_purity(schedule)
	_test_catalog_agreement(built)
	_test_recovery_path()
	_finish()


# ─────────────────────────────────────────────────────────────────────
# 1) Jadwal level (levels.json -> schedule_from_levels)
# ─────────────────────────────────────────────────────────────────────
func _test_schedule() -> Array:
	var schedule: Array = BossData.schedule_from_levels(BossDB.levels)
	var want: Array = _fixture["schedule"]
	_expect(schedule.size() == want.size(),
		"jadwal %d level (fixture %d)" % [schedule.size(), want.size()])
	var bad := 0
	for i in range(mini(schedule.size(), want.size())):
		var got: Dictionary = schedule[i]
		var exp: Dictionary = want[i]
		var gmb: Dictionary = got.get("mini_bosses", {})
		var emb: Dictionary = exp.get("mini_bosses", {})
		if gmb.size() != emb.size():
			bad += 1
			continue
		for wave in gmb:
			# Kunci Godot int (hasil normalisasi), kunci fixture String (JSON).
			if not emb.has(str(wave)) or str(emb[str(wave)]) != str(gmb[wave]):
				bad += 1
				break
		if str(got.get("true_boss")) != str(exp.get("true_boss")):
			bad += 1
	_expect(bad == 0, "isi jadwal per level sama (%d level berbeda)" % bad)
	return schedule


# ─────────────────────────────────────────────────────────────────────
# 2) Hasil pipeline untuk 216 boss
# ─────────────────────────────────────────────────────────────────────
func _test_counts(built: Dictionary) -> void:
	var want: Dictionary = _fixture["counts"]
	_expect((built["mini"] as Dictionary).size() == int(want["mini"]),
		"162 mini boss (dapat %d)" % (built["mini"] as Dictionary).size())
	_expect((built["true"] as Dictionary).size() == int(want["true"]),
		"54 true boss (dapat %d)" % (built["true"] as Dictionary).size())
	_expect((built["all"] as Dictionary).size() == int(want["all"]),
		"get_all_boss_types 216 baris (dapat %d)" % (built["all"] as Dictionary).size())


func _test_final_tables(built: Dictionary) -> void:
	var final: Dictionary = _fixture["final"]
	var boss_fields: Array = _fixture["boss_fields"]
	var hu_fields: Array = _fixture["hu_fields"]
	var all_rows: Dictionary = built["all"]
	_expect(all_rows.size() == final.size(),
		"jumlah boss dibandingkan sama (%d vs %d)" % [all_rows.size(), final.size()])

	var compared := 0
	var diffs: Array[String] = []
	for btype in final:
		var key := str(btype)
		if not all_rows.has(key):
			_fail("%s tidak ada di hasil build()" % key)
			continue
		var got: Dictionary = all_rows[key]
		var exp: Dictionary = final[key]
		_expect(str(got.get("boss_class", "?")) == str(exp["table"]),
			"%s: boss_class %s" % [key, exp["table"]])
		for f in boss_fields:
			var field := str(f)
			if not exp.has(field):
				_expect(not got.has(field), "%s: field %s tidak muncul" % [key, field])
				continue
			compared += 1
			if not _num_eq(got.get(field), exp[field]):
				diffs.append("%s.%s: %s != %s" % [key, field,
					str(got.get(field)), str(exp[field])])
		var ghu = got.get("hero_unlock")
		var ehu = exp.get("hero_unlock")
		_expect((ghu is Dictionary) == (ehu is Dictionary),
			"%s: keberadaan hero_unlock" % key)
		if ghu is Dictionary and ehu is Dictionary:
			for hf in hu_fields:
				var field2 := str(hf)
				if not (ehu as Dictionary).has(field2):
					continue
				compared += 1
				if not _num_eq((ghu as Dictionary).get(field2),
						(ehu as Dictionary)[field2]):
					diffs.append("%s.hero_unlock.%s: %s != %s" % [key, field2,
						str((ghu as Dictionary).get(field2)),
						str((ehu as Dictionary)[field2])])
	_expect(diffs.is_empty(), "pipeline == boss_data asli untuk %d field (%d selisih: %s)"
		% [compared, diffs.size(), ", ".join(diffs.slice(0, 6))])
	print("     %d field angka dibandingkan dengan fixture" % compared)


# ─────────────────────────────────────────────────────────────────────
# 3) Probe helper statis (gotcha GDScript)
# ─────────────────────────────────────────────────────────────────────
func _test_probes() -> void:
	var probes: Dictionary = _fixture["probes"]

	for pair in probes["py_round"]:
		var v: Array = pair
		_expect(BossData._py_round(float(v[0])) == int(v[1]),
			"_py_round(%s) == %s (banker's, dapat %s)"
			% [str(v[0]), str(v[1]), str(BossData._py_round(float(v[0])))])

	for pair2 in probes["py_int"]:
		var v2: Array = pair2
		_expect(BossData._py_int(float(v2[0])) == int(v2[1]),
			"_py_int(%s) == %s" % [str(v2[0]), str(v2[1])])

	for pair3 in probes["slots"]:
		var v3: Array = pair3
		_expect(BossData.slot_of_mini_wave(int(v3[0])) == str(v3[1]),
			"slot_of_mini_wave(%d) == %s" % [int(v3[0]), str(v3[1])])

	for probe in probes["trend"]:
		var pairs: Array = []
		for p in (probe as Dictionary)["in"]:
			pairs.append(p)
		var got: Array = BossData.hero_unlock_trend(pairs)
		var want: Array = (probe as Dictionary)["out"]
		_expect(got.size() == 2 and _close(float(got[0]), float(want[0]))
			and _close(float(got[1]), float(want[1])),
			"hero_unlock_trend(%d titik) == [%s, %s] (dapat [%s, %s])"
			% [pairs.size(), str(want[0]), str(want[1]),
				str(got[0]) if got.size() > 0 else "?",
				str(got[1]) if got.size() > 1 else "?"])

	# Fit NYATA atas 216 boss: mengunci sxx (pow(d,2)), urutan penjumlahan,
	# dan sort stabil per cost — selisih 1 ulp di sini akan menggeser clamp.
	var fits: Dictionary = probes["fits"]
	var pre_norm: Dictionary = _state_before_normalize()
	for table_name in ["mini", "true"]:
		var want_fit: Dictionary = fits[table_name]
		var got_fit: Array = _fits_of_table(pre_norm[str(table_name)])
		for stat in ["hp", "dps", "skill"]:
			var w: Array = want_fit[stat]
			var g: Array = got_fit[int(["hp", "dps", "skill"].find(stat))]
			_expect(_close(float(g[0]), float(w[0])) and _close(float(g[1]), float(w[1])),
				"fit %s/%s == [%s, %s] (dapat [%s, %s])"
				% [table_name, stat, str(w[0]), str(w[1]), str(g[0]), str(g[1])])
		_expect(int(want_fit["heroes"]) > 0,
			"fit %s direkam atas %d hero unlock" % [table_name, int(want_fit["heroes"])])


## Jalankan langkah 1..3 di atas SALINAN pristine (persis urutan build()),
## berhenti SEBELUM normalisasi — itulah keadaan tempat boss_data.py
## menghitung fit trend-nya.
func _state_before_normalize() -> Dictionary:
	var tables: Array = BossData.clone_tables(_pristine)
	var mini: Dictionary = tables[0]
	var true_table: Dictionary = tables[1]
	BossData.apply_boss_rebalancing(mini, true_table)
	BossData.smooth_boss_progression(mini, true_table,
		BossData.schedule_from_levels(BossDB.levels))
	BossData.apply_boss_curve_overrides(true_table, _pristine.get("curves", {}))
	return {"mini": mini, "true": true_table}


## Tiga fit least-squares (hp / dps / skill) dari satu tabel, memakai urutan
## hero yang sama dengan normalize_hero_unlock_stats: urut cost, sort STABIL
## (indeks asal sebagai tie-break).
func _fits_of_table(rows: Dictionary) -> Array:
	var heroes: Array = []
	var idx := 0
	for bt in rows:
		var bd: Dictionary = rows[bt]
		# pristine menulis hero_unlock null untuk boss tanpa unlock — `(null as
		# Dictionary).size()` akan meledak, jadi cek tipe lebih dulu (paritas
		# truthiness Python: None dan dict kosong sama-sama dilewati).
		var raw = bd.get("hero_unlock")
		if raw is Dictionary and not (raw as Dictionary).is_empty():
			heroes.append([bt, raw, idx])
		idx += 1
	heroes.sort_custom(func(a, b):
		var ca := int((a[1] as Dictionary).get("cost", 0))
		var cb := int((b[1] as Dictionary).get("cost", 0))
		if ca != cb:
			return ca < cb
		return int(a[2]) < int(b[2]))
	var hp_pairs: Array = []
	var dps_pairs: Array = []
	var sk_pairs: Array = []
	for h in heroes:
		var hu: Dictionary = h[1]
		var cost := int(hu.get("cost", 0))
		hp_pairs.append([cost, int(hu.get("hp", 0))])
		dps_pairs.append([cost, float(int(hu.get("damage", 0)))
			/ float(maxi(1, int(hu.get("attack_cooldown", 30)))) * 60.0])
		sk_pairs.append([cost, int(hu.get("skill_damage", 0))])
	return [BossData.hero_unlock_trend(hp_pairs),
		BossData.hero_unlock_trend(dps_pairs),
		BossData.hero_unlock_trend(sk_pairs)]


# ─────────────────────────────────────────────────────────────────────
# 4) Purity + determinisme
# ─────────────────────────────────────────────────────────────────────
func _test_purity(schedule: Array) -> void:
	var before := JSON.stringify(_pristine)
	var first: Dictionary = BossData.build(_pristine, schedule)
	var after := JSON.stringify(_pristine)
	_expect(before == after, "build() tidak memutasi tabel pristine yang dimuat")

	var second: Dictionary = BossData.build(_pristine, schedule)
	_expect(JSON.stringify(first["all"]) == JSON.stringify(second["all"]),
		"build() deterministik (dua panggilan identik)")

	# Hero_unlock hasil build tidak boleh berbagi referensi dengan pristine.
	var any_bt := str((first["mini"] as Dictionary).keys()[0])
	var built_hu = (first["mini"][any_bt] as Dictionary).get("hero_unlock")
	var pris_hu = (_pristine["mini"][any_bt] as Dictionary).get("hero_unlock")
	if built_hu is Dictionary and pris_hu is Dictionary:
		_expect(not is_same(built_hu, pris_hu),
			"hero_unlock hasil build tersalin (bukan referensi pristine)")


# ─────────────────────────────────────────────────────────────────────
# 5) Katalog runtime (bosses.json) == hasil hitung ulang
# ─────────────────────────────────────────────────────────────────────
func _test_catalog_agreement(built: Dictionary) -> void:
	var all_rows: Dictionary = built["all"]
	var bad: Array[String] = []
	var compared := 0
	for btype in all_rows:
		var key := str(btype)
		var s: Dictionary = BossDB.get_boss(key)
		if s.is_empty():
			bad.append("%s tidak ada di BossDB" % key)
			continue
		var row: Dictionary = all_rows[key]
		for f in ["hp", "damage", "ability_damage", "skill_q_damage",
				"skill_w_damage", "skill_e_damage", "skill_r_damage"]:
			if not row.has(f) or not s.has(f):
				continue
			compared += 1
			if not _num_eq(row[f], s[f]):
				bad.append("%s.%s: BossData %s vs bosses.json %s"
					% [key, f, str(row[f]), str(s[f])])
	_expect(bad.is_empty(), "katalog runtime == hasil pipeline (%d field; %d selisih: %s)"
		% [compared, bad.size(), ", ".join(bad.slice(0, 4))])
	print("     %d field katalog runtime dibandingkan" % compared)


# ─────────────────────────────────────────────────────────────────────
# 6) Jalur pemulihan BossDB (bosses.json hilang)
# ─────────────────────────────────────────────────────────────────────
func _test_recovery_path() -> void:
	var rebuilt: Dictionary = BossDB.rebuild_from_pristine(PRISTINE)
	var final: Dictionary = _fixture["final"]
	_expect(rebuilt.size() == final.size(),
		"rebuild_from_pristine menghasilkan %d baris (fixture %d)"
		% [rebuilt.size(), final.size()])
	var bad := 0
	var unnamed := 0
	for btype in final:
		var key := str(btype)
		if not rebuilt.has(key):
			bad += 1
			continue
		var row: Dictionary = rebuilt[key]
		if str(row.get("name", "")).strip_edges().is_empty():
			unnamed += 1
		var exp: Dictionary = final[key]
		for f in ["hp", "damage", "ability_damage"]:
			if exp.has(f) and not _num_eq(row.get(f), exp[f]):
				bad += 1
				break
	_expect(bad == 0, "angka jalur pemulihan == fixture (%d boss meleset)" % bad)
	_expect(unnamed == 0, "setiap baris pemulihan punya name (%d kosong)" % unnamed)
	_expect(BossDB.title_from_key("ghost_warrior") == "Ghost Warrior",
		"title_from_key('ghost_warrior') == 'Ghost Warrior' (dapat '%s')"
		% BossDB.title_from_key("ghost_warrior"))
	_expect(BossDB.title_from_key("ancient-apparition") == "Ancient Apparition",
		"title_from_key menangani tanda hubung")
	# BossDB asli (punya bosses.json) tidak boleh berubah karena tes ini.
	_expect(BossDB.bosses.size() == final.size(),
		"BossDB.bosses tetap dari bosses.json (%d baris)" % BossDB.bosses.size())


# ─────────────────────────────────────────────────────────────────────
# Util
# ─────────────────────────────────────────────────────────────────────
## Perbandingan angka lintas tipe: JSON bisa memberi int atau float.
func _num_eq(a, b) -> bool:
	if a == null or b == null:
		return a == b
	if a is bool or b is bool:
		return a == b
	if (a is int or a is float) and (b is int or b is float):
		return absf(float(a) - float(b)) <= FLOAT_TOL
	return a == b


func _close(a: float, b: float) -> bool:
	return absf(a - b) <= FLOAT_TOL * maxf(1.0, absf(b))


func _fail(message: String) -> void:
	_error_messages.append("[BossDataParityTest] " + message)
	_failures += 1
	push_error("[BossDataParityTest] " + message)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _finish() -> void:
	if _done:
		return
	_done = true
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print("[BossDataParityTest] PASS: pipeline data 216 boss (%d checks)" % _checks)
	else:
		for msg in _error_messages:
			print(msg)
		print("[BossDataParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
