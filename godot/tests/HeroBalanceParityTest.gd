# HeroBalanceParityTest — paritas port hero_balance.py →
# godot/scripts/core/HeroBalance.gd.
#
# Yang dikunci di sini (oracle = fixture match_parity.json["hero_balance"],
# dibuat tools/test_godot_match_parity.py FASE 28 dari kode pygame ASLI):
#   1. pristine_boss_stats: 216 baseline mentah dari boss_tables (termasuk
#      cabang lewati entri tanpa hero_unlock) — bit-eksak.
#   2. metrics: DPS/EHP/budget 222 hero mentah (eps 1e-9).
#   3. apply_to_catalog penuh (0 unlock, lv 1): stat final boss (== int),
#      starter TAK tertulis, __bal/table, dan HeroBalance.last (parity,
#      pool_means, pool_anchor, fix) — mult eps 1e-9.
#   4. Hitung-ulang == bake: stat final == res://data/heroes.json
#      (hp/damage/skill_damage + cost; unlock_cost SENGAJA beda: bake =
#      harga wrapper luar 4500/0, hitung-ulang = harga inner 1200/2200).
#   5. resolve_catalog varian unlock (5, 216): baris starter vs oracle,
#      baris boss == tabel utama (unlock tak bocor), threading level.
#   6. calibrate_boss_resistances: 216 baris -> tabel + report (mods eps).
#   7. Jalur pristine kosong (baseline = katalog itu sendiri) vs oracle
#      komposisi fungsi py asli.
#   8. _final_fixpoint jalur sel (cell_band terisi, 40 pass) vs oracle.
#   9. Helper numerik: _py_round/_py_round_n (termasuk killer double
#      rounding 1.46475/1.32975), _median/_fmean, school_mod,
#      tower_phys_factor, starter_level_factor, _final_power, _eff_dps.
#  10. Grid catch-up starter (512 mult + 37 stat + 8 hitung unlock).
#  11. Wiring runtime: HeroDB/GameManager mendelegasikan ke HeroBalance
#      (starter_catchup_mults/catchup_base/boss_unlocks_for_purchases).
#
# godot --headless --path godot res://tests/HeroBalanceParityTest.tscn --quit-after 240
# Require "[HeroBalanceParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const HEROES_JSON := "res://data/heroes.json"

var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua pesan kegagalan dikumpulkan di sini supaya tercetak ke STDOUT pada
## akhir run (tail log CI langsung memuat alasannya).
var _error_messages: Array[String] = []

var _hb: Dictionary = {}
var _raw: Dictionary = {}
var _tables: Dictionary = {}
var _pris: Dictionary = {}
var _table_exp: Dictionary = {}
var _final_exp: Dictionary = {}
var _metrics_exp: Dictionary = {}
## Katalog hasil apply penuh (dipakai ulang fix_band agar tak hitung 2x).
var _applied: Dictionary = {}


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	GameManager.in_menu = true
	GameManager.state = "idle"
	_load_section()
	if _failures == 0:
		_test_pristine()
		_test_metrics()
		_test_apply_full()
		_test_bake()
		_test_resolve_variants()
		_test_calibrate()
		_test_fallback()
		_test_fix_band()
		_test_helpers()
		_test_catchup_grid()
		_test_wiring()
	_finish()


func _load_section() -> void:
	var fixture: Variant = JSON.parse_string(
		FileAccess.get_file_as_string(FIXTURE))
	_expect(fixture is Dictionary and (fixture as Dictionary).has(
		"hero_balance"), "fixture hero_balance ada")
	if not (fixture is Dictionary
			and (fixture as Dictionary).has("hero_balance")):
		return
	_hb = (fixture as Dictionary)["hero_balance"]
	for key in ["raw_catalog", "boss_tables", "pristine", "table",
			"final_stats", "metrics"]:
		_expect(_hb.has(key) and _hb[key] is String,
			"blob kompak %s ada" % key)
	_raw = _blob("raw_catalog")
	_tables = _blob("boss_tables")
	_pris = _blob("pristine")
	_table_exp = _blob("table")
	_final_exp = _blob("final_stats")
	_metrics_exp = _blob("metrics")
	_expect(_raw.size() == 222, "raw_catalog 222 (dapat %d)" % _raw.size())
	_expect(_pris.size() == 216, "pristine 216 (dapat %d)" % _pris.size())


func _blob(key: String) -> Dictionary:
	var v: Variant = JSON.parse_string(str(_hb.get(key, "")))
	if v is Dictionary:
		return v
	_expect(false, "blob %s bukan objek" % key)
	return {}


# ── 1) pristine_boss_stats ─────────────────────────────────────────────
func _test_pristine() -> void:
	var got: Dictionary = HeroBalance.pristine_boss_stats(_tables)
	_expect(got.size() == 216, "pristine 216 (dapat %d)" % got.size())
	_expect(not got.has("_probe_tanpa_unlock")
		and not got.has("_probe_unlock_none"),
		"entri tanpa hero_unlock dilewati")
	for ht in _pris:
		_deep_near(got.get(ht, null), _pris[ht], "pristine.%s" % ht, 1e-9)


# ── 2) metrics ──────────────────────────────────────────────────────────
func _test_metrics() -> void:
	var n := 0
	for ht in _raw:
		_deep_near(HeroBalance.metrics(_raw[ht]), _metrics_exp[ht],
			"metrics.%s" % ht, 1e-9)
		n += 1
	_expect(n == 222, "metrics 222 hero (dapat %d)" % n)


# ── 3) apply_to_catalog penuh ───────────────────────────────────────────
func _test_apply_full() -> void:
	var catalog: Dictionary = _raw.duplicate(true)
	var pris: Dictionary = _pris.duplicate(true)
	var ret: Dictionary = HeroBalance.apply_to_catalog(catalog, pris, 0, 1)
	_expect(ret == catalog, "apply mengembalikan katalog yang sama")
	_applied = catalog
	var last: Dictionary = HeroBalance.last
	_expect(last.has("table") and (last["table"] as Dictionary).size() == 222,
		"last.table 222")
	for ht in _final_exp:
		var v: Dictionary = catalog.get(ht, {})
		var e: Dictionary = _final_exp[ht]
		_expect(int(v.get("hp", -1)) == int(e["hp"])
			and int(v.get("damage", -1)) == int(e["damage"])
			and int(v.get("skill_damage", -1)) == int(e["skill_damage"]),
			"%s hp/dmg/sk final" % ht)
		for qk in HeroBalance.SKILL_QWER_KEYS:
			_expect(v.get(qk, null) == e[qk],
				"%s %s (%s vs %s)" % [ht, qk, str(v.get(qk, null)),
					str(e[qk])])
		_deep_near(v.get("__bal", null), _table_exp[ht],
			"__bal.%s" % ht, 1e-9)
	# Starter tak tertulis + tak ber-__bal.
	for ht in _raw:
		if bool((_raw[ht] as Dictionary).get("is_boss_hero", false)):
			continue
		_deep_near(catalog.get(ht, null), _raw[ht], "starter.%s" % ht, 0.0)
		_expect(not (catalog[ht] as Dictionary).has("__bal"),
			"starter %s tanpa __bal" % ht)
		var te: Dictionary = _table_exp[ht]
		_expect(float(te["skill"]) == 1.0
			and te["dbg"].get("starter_unlocks", -1) == 0,
			"starter %s tabel catch-up" % ht)
	# last.* (table dibandingkan terpisah per hero di atas).
	var le: Dictionary = _hb["last"]
	_expect((last.get("pool", null) is Dictionary)
		and (last["pool"] as Dictionary).is_empty(),
		"last.pool tetap {} (quirk py)")
	_deep_near(last.get("parity", null), le["parity"], "last.parity", 1e-9)
	_deep_near(last.get("pool_means", null), le["pool_means"],
		"last.pool_means", 1e-9)
	_deep_near(last.get("pool_anchor", null), le["pool_anchor"],
		"last.pool_anchor", 1e-12)
	_deep_near(last.get("fix", null), le["fix"], "last.fix", 1e-9)
	_deep_near(last.get("table", null), _table_exp, "last.table", 1e-9)


# ── 4) hitung-ulang == bake heroes.json ─────────────────────────────────
func _test_bake() -> void:
	var bake: Variant = JSON.parse_string(
		FileAccess.get_file_as_string(HEROES_JSON))
	_expect(bake is Dictionary and (bake as Dictionary).size() == 222,
		"heroes.json 222")
	if not (bake is Dictionary):
		return
	var n := 0
	for ht in _final_exp:
		var v: Dictionary = _applied.get(ht, {})
		var b: Dictionary = (bake as Dictionary).get(ht, {})
		_expect(int(v.get("hp", -1)) == int(b.get("hp", -2))
			and int(v.get("damage", -1)) == int(b.get("damage", -2))
			and int(v.get("skill_damage", -1))
				== int(b.get("skill_damage", -2)),
			"%s final == bake" % ht)
		_expect(int(v.get("cost", -1)) == int(b.get("cost", -2)),
			"%s cost passthrough" % ht)
		# Bake memakai harga wrapper LUAR (4500/0); hitung-ulang memakai
		# harga inner (1200/2200) — beda ini disengaja & dikunci.
		_expect(int(b.get("unlock_cost", -1)) == 4500,
			"%s bake unlock_cost 4500" % ht)
		n += 1
	_expect(n == 216, "216 boss == bake")
	for ht in _raw:
		if bool((_raw[ht] as Dictionary).get("is_boss_hero", false)):
			continue
		var b2: Dictionary = (bake as Dictionary).get(ht, {})
		_expect(int(b2.get("hp", -1))
				== int((_raw[ht] as Dictionary).get("hp", -2)),
			"starter %s bake = mentah (tanpa catch-up)" % ht)
		_expect(int(b2.get("unlock_cost", -1)) == 0,
			"starter %s bake unlock_cost 0" % ht)


# ── 5) resolve varian unlock ────────────────────────────────────────────
func _test_resolve_variants() -> void:
	# Baseline: resolve SEGAR (unlocks 0) — tabel oracle pasca-apply tak
	# sebanding (mult-nya sudah di-rescale + fix).
	var src0: Dictionary = _raw.duplicate(true)
	for k0 in _pris:
		if src0.has(k0):
			src0[k0] = (_pris[k0] as Dictionary).duplicate(true)
	var base: Dictionary = HeroBalance.resolve_catalog(src0, 0, 1)
	for var_case in (_hb["resolve_variants"] as Array):
		var u := int(var_case["unlocks"])
		var src: Dictionary = _raw.duplicate(true)
		for k in _pris:
			if src.has(k):
				src[k] = (_pris[k] as Dictionary).duplicate(true)
		var vt: Dictionary = HeroBalance.resolve_catalog(src, u, 1)
		_expect(vt.size() == 222, "varian u=%d 222 baris" % u)
		for ht in (var_case["starters"] as Dictionary):
			_deep_near(vt.get(ht, null),
				(var_case["starters"] as Dictionary)[ht],
				"varian u=%d starter %s" % [u, ht], 1e-9)
		for ht in vt:
			if (var_case["starters"] as Dictionary).has(ht):
				continue
			_deep_near(vt[ht], base[ht],
				"varian u=%d boss %s tak berubah" % [u, ht], 0.0)
	# Threading level (py meng-hardcode 1; konsistensi vs rumus langsung).
	var src2: Dictionary = _raw.duplicate(true)
	for k in _pris:
		if src2.has(k):
			src2[k] = (_pris[k] as Dictionary).duplicate(true)
	var vt2: Dictionary = HeroBalance.resolve_catalog(src2, 5, 3)
	for ht in (_hb["catchup"] as Dictionary)["starter_heroes"]:
		var m: Array = HeroBalance.starter_catchup(ht, 5, 3)
		var row: Dictionary = vt2[ht]
		_near(float(row["hp"]), HeroBalance._py_round_n(float(m[0]), 4),
			"thread level %s hp" % ht, 0.0)
		_near(float(row["dmg"]), HeroBalance._py_round_n(float(m[1]), 4),
			"thread level %s dmg" % ht, 0.0)


# ── 6) kalibrasi resistansi boss ────────────────────────────────────────
func _test_calibrate() -> void:
	var rows: Array = (_hb["calibrate"] as Dictionary)["rows"]
	_expect(rows.size() == 216, "216 baris kalibrasi")
	var cal: Array = HeroBalance.calibrate_boss_resistances(rows)
	var res: Dictionary = cal[0]
	var rep: Dictionary = cal[1]
	var rese: Dictionary = (_hb["calibrate"] as Dictionary)["res"]
	var repe: Dictionary = (_hb["calibrate"] as Dictionary)["report"]
	_expect(res.size() == 216, "res 216")
	for bt in rese:
		_deep_near(res.get(bt, null), rese[bt], "cal.res.%s" % bt, 1e-9)
	for dc in ["mini", "true"]:
		var r: Dictionary = rep.get(dc, {})
		var e: Dictionary = repe.get(dc, {})
		_near(float(r.get("magic_over_phys", -1.0)),
			float(e["magic_over_phys"]), "cal.%s ratio" % dc, 1e-9)
		_near(float(r.get("avg_armor", -1.0)), float(e["avg_armor"]),
			"cal.%s avg_armor" % dc, 1e-9)
		_near(float(r.get("avg_mr", -1.0)), float(e["avg_mr"]),
			"cal.%s avg_mr" % dc, 1e-9)
		_deep_near(r.get("scale", null), e["scale"],
			"cal.%s scale" % dc, 1e-12)
		_deep_near(r.get("mods", null), e["mods"], "cal.%s mods" % dc,
			1e-12)
	_deep_near(rep.get("_scales", null), repe["_scales"], "cal._scales",
		1e-12)
	_deep_near(rep.get("_mods_mini", null), repe["_mods_mini"],
		"cal._mods_mini", 1e-12)


# ── 7) jalur pristine kosong ────────────────────────────────────────────
func _test_fallback() -> void:
	var catalog: Dictionary = _raw.duplicate(true)
	HeroBalance.apply_to_catalog(catalog, {}, 0, 1)
	var fb: Dictionary = _hb["pristine_fallback"]
	var ffinal: Dictionary = fb["final"]
	var fbal: Dictionary = fb["bal"]
	_expect(ffinal.size() == 216, "fallback 216 final")
	for ht in ffinal:
		var v: Dictionary = catalog.get(ht, {})
		var e: Dictionary = ffinal[ht]
		_expect(int(v.get("hp", -1)) == int(e["hp"])
			and int(v.get("damage", -1)) == int(e["damage"])
			and int(v.get("skill_damage", -1)) == int(e["skill_damage"]),
			"fb %s final" % ht)
		# Oracle fallback minimal (hp/dmg/skill saja, tanpa dbg).
		var fbv: Dictionary = v.get("__bal", {})
		var fbe2: Dictionary = fbal[ht]
		_near(float(fbv.get("hp", -1.0)), float(fbe2["hp"]),
			"fb.bal.%s hp" % ht, 1e-9)
		_near(float(fbv.get("dmg", -1.0)), float(fbe2["dmg"]),
			"fb.bal.%s dmg" % ht, 1e-9)
		_near(float(fbv.get("skill", -1.0)), float(fbe2["skill"]),
			"fb.bal.%s skill" % ht, 1e-9)
	var fl: Dictionary = fb["last"]
	var last: Dictionary = HeroBalance.last
	_deep_near(last.get("parity", null), fl["parity"], "fb.parity", 1e-9)
	_deep_near(last.get("pool_means", null), fl["pool_means"], "fb.means",
		1e-9)
	_deep_near(last.get("pool_anchor", null), fl["pool_anchor"], "fb.anchor",
		1e-12)
	_deep_near(last.get("fix", null), fl["fix"], "fb.fix", 1e-9)


# ── 8) fixpoint jalur sel ───────────────────────────────────────────────
func _test_fix_band() -> void:
	var band: Array = (_hb["fix_band"] as Dictionary)["cell_band"]
	var cat: Dictionary = _applied.duplicate(true)
	var info: Dictionary = HeroBalance._final_fixpoint(
		cat, 1.0, band, 40, 0.85, 0.002)
	var fbe: Dictionary = _hb["fix_band"]
	_deep_near(info, fbe["info"], "fixband.info", 1e-9)
	_expect(int(info.get("passes_run", -1)) == 40
		and int(info.get("n", -1)) == 216,
		"fixband 40 pass 216 hero")
	var dmg: Dictionary = fbe["damage"]
	for ht in dmg:
		var v: Dictionary = cat.get(ht, {})
		var e: Dictionary = dmg[ht]
		_expect(int(v.get("damage", -1)) == int(e["damage"])
			and int(v.get("skill_damage", -1)) == int(e["skill_damage"]),
			"fixband %s damage" % ht)


# ── 9) helper numerik ───────────────────────────────────────────────────
func _test_helpers() -> void:
	var h: Dictionary = _hb["helpers"]
	for c in (h["py_round"] as Array):
		_expect(HeroBalance._py_round(float(c[0])) == int(c[1]),
			"round(%s)" % str(c[0]))
	for c in (h["py_round_n"] as Array):
		_near(HeroBalance._py_round_n(float(c["in"]), int(c["n"])),
			float(c["out"]), "round(%s,%d)" % [str(c["in"]),
				int(c["n"])], 1e-12)
	for c in (h["median"] as Array):
		_near(HeroBalance._median(c["in"]), float(c["out"]),
			"median n=%d" % (c["in"] as Array).size(), 1e-12)
	for c in (h["fmean"] as Array):
		_near(HeroBalance._fmean(c["in"]), float(c["out"]),
			"fmean n=%d" % (c["in"] as Array).size(), 1e-12)
	for c in (h["school_mod"] as Array):
		_expect(HeroBalance.school_mod(str(c[0])) == float(c[1]),
			"school_mod %s" % str(c[0]))
	_near(HeroBalance.tower_phys_factor(), float(h["tower_phys_factor"]),
		"tower_phys_factor", 1e-15)
	for c in (h["level_factor"] as Array):
		_near(HeroBalance.starter_level_factor(int(c[0])), float(c[1]),
			"level_factor %d" % int(c[0]), 1e-12)
	for c in (h["final_power"] as Array):
		var m := {"dmg": float(c["dmg"]), "skill": float(c["skill"]),
			"cd": float(c["cd"]), "skcd": float(c["skcd"]),
			"ehp": float(c["ehp"])}
		_near(HeroBalance._final_power(m, float(c["y"]), float(c["x_dmg"]),
			float(c["x_sk"]), float(c["med_dps"]), float(c["med_ehp"])),
			float(c["out"]), "power %s" % str(c["hero"]), 1e-9)
	for c in (h["eff_dps"] as Array):
		_near(HeroBalance._eff_dps(str(c["hero"]), c["stats"],
			float(c["dps"])), float(c["out"]),
			"eff_dps %s" % str(c["hero"]), 1e-9)


# ── 10) grid catch-up ───────────────────────────────────────────────────
func _test_catchup_grid() -> void:
	var cu: Dictionary = _hb["catchup"]
	_expect((cu["starter_heroes"] as Array) == HeroBalance.STARTER_HEROES,
		"STARTER_HEROES == oracle")
	for c in (cu["mult_grid"] as Array):
		var m: Array = HeroBalance.starter_catchup(str(c["hero"]),
			int(c["unlocks"]), int(c["level"]))
		_near(float(m[0]), float(c["hp"]),
			"catchup %s u%d lv%d hp" % [str(c["hero"]), int(c["unlocks"]),
				int(c["level"])], 1e-12)
		_near(float(m[1]), float(c["dmg"]),
			"catchup %s u%d lv%d dmg" % [str(c["hero"]), int(c["unlocks"]),
				int(c["level"])], 1e-12)
	for c in (cu["stat_cases"] as Array):
		var stats := {"hp": int(c["base_hp"]),
			"damage": int(c["base_damage"])}
		var got: Vector2i = HeroBalance.starter_catchup_stats(
			str(c["hero"]), stats, int(c["unlocks"]), int(c["level"]))
		_expect(got.x == int(c["hp"]) and got.y == int(c["damage"]),
			"catchup_stats %s u%d lv%d" % [str(c["hero"]),
				int(c["unlocks"]), int(c["level"])])
	for c in (cu["unlock_counts"] as Array):
		_expect(HeroBalance.boss_unlocks_for_purchases(c["purchased"])
			== int(c["unlocks"]), "unlocks %s" % str(c["name"]))


# ── 11) wiring runtime ──────────────────────────────────────────────────
func _test_wiring() -> void:
	_expect(HeroDB.STARTER_HEROES == HeroBalance.STARTER_HEROES,
		"HeroDB.STARTER_HEROES == HeroBalance")
	var m: Vector2 = HeroDB.starter_catchup_mults("kaizen", 5, 3)
	var e: Array = HeroBalance.starter_catchup("kaizen", 5, 3)
	# Delegasi + kuantisasi Vector2 single-precision (<= 6e-8).
	_near(m.x, float(e[0]), "HeroDB.starter_catchup_mults hp", 1e-6)
	_near(m.y, float(e[1]), "HeroDB.starter_catchup_mults dmg", 1e-6)
	var cb: Vector2i = HeroDB.catchup_base("kaizen", 5, 3)
	var ce: Vector2i = HeroBalance.starter_catchup_stats("kaizen",
		HeroDB.get_hero("kaizen"), 5, 3)
	_expect(cb == ce, "HeroDB.catchup_base mendelegasikan")
	_expect(HeroDB.catchup_base("hero_misterius", 5, 3) == Vector2i(1, 1),
		"HeroDB.catchup_base hero tak dikenal (1,1)")
	_expect(GameManager.boss_unlocks_for_purchases(
		["kaizen", "gornak", "gornak"]) == 2,
		"GameManager.boss_unlocks_for_purchases mendelegasikan")
	_expect(GameManager.boss_unlocks_for_purchases(
		HeroBalance.STARTER_HEROES) == 0,
		"starter tak dihitung unlock")
	_expect(GameManager.catchup_unlocks() == 0,
		"catchup_unlocks 0 di luar match")


# ── util ────────────────────────────────────────────────────────────────
func _near(a: float, b: float, message: String, eps: float) -> void:
	_checks += 1
	if absf(a - b) > eps:
		var line := "[HeroBalanceParityTest] %s: %.10f != %.10f" % [message,
			a, b]
		_error_messages.append(line)
		_failures += 1
		push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		var line := "[HeroBalanceParityTest] " + message
		_error_messages.append(line)
		_failures += 1
		push_error(line)


## Banding struktur bersarang: float dengan eps, int/String/bool/null eksak.
## Satu check per panggilan; pesan bawa jalur daun pertama yang beda.
func _deep_near(a: Variant, b: Variant, path: String, eps: float) -> void:
	_checks += 1
	var msg := _deep_diff(a, b, path, eps)
	if msg != "":
		_error_messages.append("[HeroBalanceParityTest] " + msg)
		_failures += 1
		push_error("[HeroBalanceParityTest] " + msg)


func _deep_diff(a: Variant, b: Variant, path: String, eps: float) -> String:
	if a == null and b == null:
		return ""
	if a == null or b == null:
		return "%s: %s != %s" % [path, str(a), str(b)]
	var a_num := a is float or a is int
	var b_num := b is float or b is int
	if a_num and b_num:
		if absf(float(a) - float(b)) > eps:
			return "%s: %s != %s" % [path, str(a), str(b)]
		return ""
	if a is bool or b is bool:
		if a != b:
			return "%s: %s != %s" % [path, str(a), str(b)]
		return ""
	if a is String or b is String:
		if str(a) != str(b):
			return "%s: %s != %s" % [path, str(a), str(b)]
		return ""
	if a is Array and b is Array:
		if a.size() != b.size():
			return "%s.size: %d != %d" % [path, a.size(), b.size()]
		for i in range(a.size()):
			var m := _deep_diff(a[i], b[i], "%s[%d]" % [path, i], eps)
			if m != "":
				return m
		return ""
	if a is Dictionary and b is Dictionary:
		for k in a:
			if not b.has(k):
				return "%s: kunci %s hilang di oracle" % [path, str(k)]
		for k in b:
			if not a.has(k):
				return "%s: kunci %s hilang di Godot" % [path, str(k)]
		for k in a:
			var m2 := _deep_diff(a[k], b[k], "%s.%s" % [path, str(k)],
				eps)
			if m2 != "":
				return m2
		return ""
	return "%s: tipe %s != %s" % [path, str(a), str(b)]


func _finish() -> void:
	if _done:
		return
	_done = true
	get_tree().paused = false
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print("[HeroBalanceParityTest] PASS: hero_balance.py ↔ Godot (%d checks)" % _checks)
	else:
		# Cetak SETIAP kegagalan ke stdout (bukan hanya push_error) supaya tail
		# log CI memuat alasan lengkapnya.
		for msg in _error_messages:
			print(msg)
		push_error("[HeroBalanceParityTest] %d failures dari %d checks" % [_failures, _checks])
		print("[HeroBalanceParityTest] FAIL: %d failures dari %d checks" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
