# HeroArchetypesParityTest — paritas port hero_archetypes.py →
# godot/scripts/core/HeroArchetypes.gd.
#
# Yang dikunci di sini:
#   1. Konstanta & ukuran tabel (ARMOR_FACTOR/ARMOR_MAX/MR_MAX/base/mods/
#      scale/target, 222 archetype + 216 boss resistance).
#   2. Semantik get_archetype: entri dikenal (salinan — tabel const tidak
#      bisa dikotori pemanggil), override stats["dmg_type"] (valid → menang,
#      invalid → DEFAULT, hero tak dikenal → entri minimal tanpa tier/power),
#      dan entri default ber-`derived` untuk hero tanpa entri.
#   3. school_of lowercase + physical_mitigation terhadap konstanta oracle
#      yang dihitung dari hero_archetypes.py asli.
#   4. _resist_from_profile: baseline kelas, pembulatan banker (12.5→12,
#      13.5→14 — persis round() Python), clamp armor/MR, armor_off.
#   5. get_boss_resistances untuk SELURUH 216 boss dibandingkan dengan
#      oracle Pygame (fixture match_parity.json["boss_core"], dibuat
#      tools/test_godot_match_parity.py dari Boss.__init__ pygame asli)
#      dan dengan export bosses.json yang dibaca BossDB.
#   6. Sinkron data: const ARCHETYPES == godot/data/hero_archetypes.json
#      (yang dibaca HeroDB).
#   7. Wiring runtime: HeroDB.get_balanced_stats mengambil dmg_school dari
#      modul; Boss.gd memakai get_boss_resistances sebagai default +
#      clamp 0..ARMOR_MAX / 0..MR_MAX (base_boss.py:447-457) — diuji dengan
#      entry BossDB tiruan (boss tanpa kunci armor/MR dan override liar).
#
# godot --headless --path godot res://tests/HeroArchetypesParityTest.tscn --quit-after 120
# Require "[HeroArchetypesParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const BossScene = preload("res://scenes/boss/Boss.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"
const ARCH_JSON := "res://data/hero_archetypes.json"
const BOSSES_JSON := "res://data/bosses.json"

var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua pesan kegagalan dikumpulkan di sini supaya tercetak ke STDOUT pada
## akhir run (tail log CI langsung memuat alasannya).
var _error_messages: Array[String] = []


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	GameManager.in_menu = true
	GameManager.state = "idle"
	_test_constants()
	_test_get_archetype_semantics()
	_test_school_of()
	_test_physical_mitigation()
	_test_resist_from_profile()
	_test_archetypes_match_json()
	_test_boss_resistances_vs_fixture()
	_test_boss_resistances_vs_export()
	_test_herodb_wiring()
	await _test_boss_node_wiring()
	_finish()


# ── 1) Konstanta & ukuran tabel ─────────────────────────────────────────
func _test_constants() -> void:
	_expect(HeroArchetypes.ARMOR_FACTOR == 0.06, "ARMOR_FACTOR 0.06")
	_expect(HeroArchetypes.ARMOR_MAX == 40, "ARMOR_MAX 40")
	_expect(HeroArchetypes.MR_MAX == 0.45, "MR_MAX 0.45")
	_expect(HeroArchetypes.DEFAULT_DMG_TYPE == "PHYSICAL", "DEFAULT_DMG_TYPE PHYSICAL")
	_expect(HeroArchetypes.ARCHETYPES.size() == 222,
		"ARCHETYPES 222 entri (dapat %d)" % HeroArchetypes.ARCHETYPES.size())
	_expect(HeroArchetypes.BOSS_RESISTANCES.size() == 216,
		"BOSS_RESISTANCES 216 entri (dapat %d)" % HeroArchetypes.BOSS_RESISTANCES.size())
	# Baseline kelas boss (mini 12/0.10, true 18/0.20).
	var bm: Array = HeroArchetypes.BOSS_RESIST_BASE.get("mini", [])
	var bt: Array = HeroArchetypes.BOSS_RESIST_BASE.get("true", [])
	_expect(bm == [12, 0.10], "BOSS_RESIST_BASE mini [12, 0.10]")
	_expect(bt == [18, 0.20], "BOSS_RESIST_BASE true [18, 0.20]")
	# Modifier profil desain (niat manual, bukan auto-generated).
	var mods: Dictionary = HeroArchetypes.BOSS_RESIST_PROFILE_MODS
	_expect(mods.get("armored") == [10.0, -0.040], "mods armored")
	_expect(mods.get("brute") == [3.0, 0.020], "mods brute")
	_expect(mods.get("balanced") == [0.0, 0.0], "mods balanced")
	_expect(mods.get("soft") == [-2.0, -0.020], "mods soft")
	_expect(mods.get("magic") == [-4.0, 0.060], "mods magic")
	_near(float(HeroArchetypes.BOSS_RESIST_SCALE["mini"]["armor"]), 1.32,
		"scale mini armor", 1e-6)
	_near(float(HeroArchetypes.BOSS_RESIST_SCALE["mini"]["mr"]), 1.8,
		"scale mini mr", 1e-6)
	_near(float(HeroArchetypes.BOSS_RESIST_SCALE["true"]["armor"]), 1.272,
		"scale true armor", 1e-6)
	_near(float(HeroArchetypes.BOSS_RESIST_SCALE["true"]["mr"]), 1.8,
		"scale true mr", 1e-6)
	_expect(HeroArchetypes.BOSS_RESIST_TARGET_RATIO == 1.00,
		"BOSS_RESIST_TARGET_RATIO 1.00")
	# Integritas isi tabel boss: profil & kelas hanya nilai yang dikenal.
	var ok := true
	for btx in HeroArchetypes.BOSS_RESISTANCES:
		var e: Dictionary = HeroArchetypes.BOSS_RESISTANCES[btx]
		if str(e.get("profile", "")) not in mods:
			ok = false
		if str(e.get("boss_class", "")) not in ["mini", "true"]:
			ok = false
	_expect(ok, "seluruh BOSS_RESISTANCES: profile ∈ 5 tema, boss_class ∈ mini/true")


# ── 2) Semantik get_archetype ───────────────────────────────────────────
func _test_get_archetype_semantics() -> void:
	var a: Dictionary = HeroArchetypes.get_archetype("aelyrion")
	_expect(str(a.get("dmg_type", "")) == "PHYSICAL"
		and str(a.get("playstyle", "")) == "FIGHTER"
		and str(a.get("tier", "")) == "B"
		and int(a.get("power", -1)) == 56,
		"aelyrion = entri tabel")
	_expect(not a.has("derived"), "entri dikenal tidak ber-`derived`")
	# Salinan: mengutak-atik hasil tidak boleh mengotori tabel const.
	a["dmg_type"] = "RUSAK"
	a["power"] = -99
	var a2: Dictionary = HeroArchetypes.get_archetype("aelyrion")
	_expect(str(a2.get("dmg_type", "")) == "PHYSICAL"
		and int(a2.get("power", -1)) == 56,
		"hasil get_archetype adalah salinan (const utuh)")
	# stats = {} harus setara tanpa stats (truthiness Python).
	var b1: Dictionary = HeroArchetypes.get_archetype("vex")
	var b2: Dictionary = HeroArchetypes.get_archetype("vex", {})
	_expect(b1 == b2, "stats kosong == tanpa stats")
	# Override valid (lowercase ikut diterima — py: str.upper()).
	var c: Dictionary = HeroArchetypes.get_archetype("kaizen", {"dmg_type": "magic"})
	_expect(str(c.get("dmg_type", "")) == "MAGIC"
		and str(c.get("tier", "")) == "A"
		and int(c.get("power", -1)) == 9,
		"override magic valid: sisa entri kaizen dipertahankan")
	# Override invalid -> DEFAULT_DMG_TYPE, sisa entri dipertahankan.
	var d: Dictionary = HeroArchetypes.get_archetype("kaizen", {"dmg_type": "fire"})
	_expect(str(d.get("dmg_type", "")) == "PHYSICAL"
		and str(d.get("tier", "")) == "A"
		and int(d.get("power", -1)) == 9,
		"override invalid -> PHYSICAL (py oracle)")
	# Override pada hero TANPA entri: entri minimal — tanpa tier/power/derived
	# (persis `dict(ARCHETYPES.get(hero_type, {}))` + setdefault di py).
	var e: Dictionary = HeroArchetypes.get_archetype("hero_baru", {"dmg_type": "MAGIC"})
	_expect(str(e.get("dmg_type", "")) == "MAGIC"
		and str(e.get("playstyle", "")) == "FIGHTER"
		and not e.has("tier") and not e.has("power") and not e.has("derived"),
		"override hero tak dikenal -> entri minimal (py oracle)")
	# Hero tak dikenal tanpa override -> default derived.
	var f: Dictionary = HeroArchetypes.get_archetype("boss_belum_dianalisis")
	_expect(str(f.get("dmg_type", "")) == "PHYSICAL"
		and str(f.get("playstyle", "")) == "FIGHTER"
		and str(f.get("tier", "x")) == ""
		and int(f.get("power", -1)) == 0
		and bool(f.get("derived", false)),
		"hero tak dikenal -> default derived (py oracle)")


# ── 3) school_of ────────────────────────────────────────────────────────
func _test_school_of() -> void:
	_expect(HeroArchetypes.school_of("vex") == "magic", "school_of(vex) magic")
	_expect(HeroArchetypes.school_of("kazuren") == "magic", "school_of(kazuren) magic")
	_expect(HeroArchetypes.school_of("kaizen") == "physical", "school_of(kaizen) physical")
	_expect(HeroArchetypes.school_of("tidak_terdaftar") == "physical",
		"school_of fallback physical")
	_expect(HeroArchetypes.school_of("kaizen", {"dmg_type": "magic"}) == "magic",
		"school_of ikut override")


# ── 4) physical_mitigation vs oracle hero_archetypes.py ─────────────────
func _test_physical_mitigation() -> void:
	# Konstanta di bawah = hasil hero_archetypes.physical_mitigation Python.
	_near(HeroArchetypes.physical_mitigation(0.0), 1.0, "mit(0)", 1e-9)
	_near(HeroArchetypes.physical_mitigation(12.0), 0.5813953488372093,
		"mit(12) oracle", 1e-9)
	_near(HeroArchetypes.physical_mitigation(18.0), 0.4807692307692307,
		"mit(18) oracle", 1e-9)
	_near(HeroArchetypes.physical_mitigation(33.0), 0.3355704697986577,
		"mit(33) oracle", 1e-9)
	_near(HeroArchetypes.physical_mitigation(40.0), 0.2941176470588235,
		"mit(40) oracle", 1e-9)
	_near(HeroArchetypes.physical_mitigation(-5.0), 1.0,
		"mit(-5): armor negatif di-clamp 0", 1e-9)


# ── 5) _resist_from_profile + get_boss_resistances fallback ─────────────
func _test_resist_from_profile() -> void:
	# Baseline murni (skala 1.0) — oracle dari hero_archetypes.py.
	var r1: Array = HeroArchetypes._resist_from_profile("armored", "mini")
	_expect(int(r1[0]) == 22, "armored/mini armor 22 (12+10)")
	_near(float(r1[1]), 0.06, "armored/mini mr 0.06", 1e-9)
	var r2: Array = HeroArchetypes._resist_from_profile("magic", "true")
	_expect(int(r2[0]) == 14, "magic/true armor 14 (18-4)")
	_near(float(r2[1]), 0.26, "magic/true mr 0.26", 1e-9)
	var r3: Array = HeroArchetypes._resist_from_profile("soft", "mini")
	_expect(int(r3[0]) == 10, "soft/mini armor 10 (12-2)")
	_near(float(r3[1]), 0.08, "soft/mini mr 0.08", 1e-9)
	# Pembulatan BANKER persis round() Python: 13.5 -> 14, 12.5 -> 12.
	var r4: Array = HeroArchetypes._resist_from_profile("brute", "mini",
		{}, {}, 0.5)
	_expect(int(r4[0]) == 14, "13.5 -> 14 (banker, half-to-even)")
	_near(float(r4[1]), 0.12, "brute mr dengan default scale", 1e-9)
	var r5: Array = HeroArchetypes._resist_from_profile("x", "mini",
		{}, {"x": [1.0, 0.0]}, 0.5)
	_expect(int(r5[0]) == 12, "12.5 -> 12 (banker, half-to-even)")
	# armor_off ikut sebelum pembulatan (12 + 0.5 = 12.5 -> 12).
	var r6: Array = HeroArchetypes._resist_from_profile("balanced", "mini",
		{}, {}, 1.0, 1.0, 0.5)
	_expect(int(r6[0]) == 12, "armor_off 0.5: 12.5 -> 12")
	# Clamp: armor > ARMOR_MAX -> ARMOR_MAX; mr > MR_MAX -> MR_MAX.
	var r7: Array = HeroArchetypes._resist_from_profile("h", "mini",
		{}, {"h": [99.0, 0.0]})
	_expect(int(r7[0]) == HeroArchetypes.ARMOR_MAX, "armor di-clamp ARMOR_MAX")
	var r8: Array = HeroArchetypes._resist_from_profile("h", "mini",
		{}, {"h": [0.0, 9.0]})
	_near(float(r8[1]), HeroArchetypes.MR_MAX, "mr di-clamp MR_MAX", 1e-9)
	# Boss tak dikenal -> profil balanced dengan skala kelasnya.
	var fb1: Array = HeroArchetypes.get_boss_resistances("boss_baru_belum_bake", "mini")
	_expect(int(fb1[0]) == 12, "fallback mini armor 12 (baseline)")
	_near(float(fb1[1]), 0.10, "fallback mini mr 0.10", 1e-9)
	var fb2: Array = HeroArchetypes.get_boss_resistances("boss_baru_belum_bake", "true")
	_expect(int(fb2[0]) == 18, "fallback true armor 18 (baseline)")
	_near(float(fb2[1]), 0.20, "fallback true mr 0.20", 1e-9)


# ── 6) Sinkron const ARCHETYPES dengan godot/data/hero_archetypes.json ──
func _test_archetypes_match_json() -> void:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(ARCH_JSON))
	_expect(parsed is Dictionary, "hero_archetypes.json ter-parse")
	if not (parsed is Dictionary):
		return
	var table: Dictionary = HeroArchetypes.ARCHETYPES
	_expect(parsed.size() == table.size(),
		"JSON %d entri vs const %d entri" % [parsed.size(), table.size()])
	var mismatches := 0
	for hero_type in table:
		var c: Dictionary = table[hero_type]
		var j = parsed.get(hero_type)
		if not (j is Dictionary):
			mismatches += 1
			continue
		if str(j.get("dmg_type", "")) != str(c["dmg_type"]) \
				or str(j.get("playstyle", "")) != str(c["playstyle"]) \
				or str(j.get("tier", "")) != str(c["tier"]) \
				or int(j.get("power", -1)) != int(c["power"]):
			mismatches += 1
	_expect(mismatches == 0, "seluruh %d entri const == JSON" % table.size())
	for hero_type in parsed:
		if hero_type not in table:
			mismatches += 1
	_expect(mismatches == 0, "tidak ada kunci asing di JSON")


# ── 7) get_boss_resistances vs oracle Pygame (fixture boss_core) ────────
func _test_boss_resistances_vs_fixture() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	_expect(fixture is Dictionary and fixture.has("boss_core"),
		"fixture boss_core ada")
	if not (fixture is Dictionary and fixture.has("boss_core")):
		return
	var rows: Array = fixture["boss_core"]["bosses"]
	var checked := 0
	for row in rows:
		var res: Array = HeroArchetypes.get_boss_resistances(
			str(row["boss_type"]), str(row["boss_class"]))
		_expect(int(res[0]) == int(row["armor"]),
			"%s armor (%d vs oracle %d)" % [row["boss_type"], int(res[0]), int(row["armor"])])
		_near(float(res[1]), float(row["magic_resist"]),
			"%s magic_resist" % row["boss_type"], 1e-9)
		checked += 1
	_expect(checked == 216, "semua 216 boss dibandingkan dengan oracle")


# ── 8) get_boss_resistances vs export bosses.json (yang dibaca BossDB) ──
func _test_boss_resistances_vs_export() -> void:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(BOSSES_JSON))
	_expect(parsed is Dictionary, "bosses.json ter-parse")
	if not (parsed is Dictionary):
		return
	var mismatches := 0
	var detail := ""
	for bt in parsed:
		var s: Dictionary = parsed[bt]
		var res: Array = HeroArchetypes.get_boss_resistances(
			bt, str(s.get("boss_class", "mini")))
		if int(s.get("armor", -1)) != int(res[0]) \
				or absf(float(s.get("magic_resist", -1.0)) - float(res[1])) > 1e-9:
			mismatches += 1
			if detail == "":
				detail = bt
	_expect(mismatches == 0,
		"export bosses.json == get_boss_resistances (%d mismatch, pertama '%s')"
		% [mismatches, detail])


# ── 9) Wiring HeroDB.get_balanced_stats -> HeroArchetypes ───────────────
func _test_herodb_wiring() -> void:
	var vex: Dictionary = HeroDB.get_balanced_stats("vex")
	_expect(str(vex.get("dmg_school", "")) == "magic"
		and str(vex.get("dmg_type", "")) == "MAGIC",
		"HeroDB: vex magic dari tabel arketipe")
	var kaizen: Dictionary = HeroDB.get_balanced_stats("kaizen")
	_expect(str(kaizen.get("dmg_school", "")) == "physical",
		"HeroDB: kaizen physical")
	var kazuren: Dictionary = HeroDB.get_balanced_stats("kazuren")
	_expect(str(kazuren.get("dmg_school", "")) == "magic",
		"HeroDB: kazuren (TANK MAGIC) magic")
	var unknown: Dictionary = HeroDB.get_balanced_stats("hero_misterius")
	_expect(unknown.is_empty(), "HeroDB: hero tak dikenal tetap {} (guard awal)")


# ── 10) Wiring node Boss.gd (fallback profil + clamp runtime) ───────────
func _spawn_boss(boss_type: String, pos: Vector2):
	var boss = BossScene.instantiate()
	boss.boss_type = boss_type
	boss.team = "red"
	boss.position = pos
	add_child(boss)
	await get_tree().process_frame
	boss.set_physics_process(false)
	return boss


func _test_boss_node_wiring() -> void:
	# Boss NYATA dari export: nilai armor/MR node tetap sama seperti sebelum
	# port (baked di converter + clamp runtime = no-op).
	var gornak = await _spawn_boss("gornak", Vector2(300, 300))
	_expect(int(gornak.armor) == 8, "gornak armor 8 (baked)")
	_near(gornak.magic_resist, 0.187, "gornak mr 0.187 (baked)", 1e-9)
	gornak.queue_free()

	# Boss tiruan TANPA kunci armor/MR: default = profil kelasnya
	# (base_boss.py:447-449), bukan 0. State BossDB dipulihkan setelahnya.
	BossDB.bosses["_test_nores_true"] = {"name": "Tes", "hp": 5000,
		"boss_class": "true"}
	var fb = await _spawn_boss("_test_nores_true", Vector2(400, 300))
	_expect(int(fb.armor) == 18, "boss tanpa armor key -> fallback true 18")
	_near(fb.magic_resist, 0.20, "boss tanpa mr key -> fallback true 0.20", 1e-9)
	fb.queue_free()

	# Override liar di data di-clamp ke ARMOR_MAX / MR_MAX (base_boss.py:455-457).
	BossDB.bosses["_test_clamp_mini"] = {"name": "Tes2", "hp": 5000,
		"boss_class": "mini", "armor": 99, "magic_resist": 0.9}
	var cl = await _spawn_boss("_test_clamp_mini", Vector2(500, 300))
	_expect(int(cl.armor) == HeroArchetypes.ARMOR_MAX,
		"armor 99 -> clamp ARMOR_MAX")
	_near(cl.magic_resist, HeroArchetypes.MR_MAX, "mr 0.9 -> clamp MR_MAX", 1e-9)
	cl.queue_free()
	BossDB.bosses.erase("_test_nores_true")
	BossDB.bosses.erase("_test_clamp_mini")


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		var line := "[HeroArchetypesParityTest] %s: %.10f != %.10f" % [message, a, b]
		_error_messages.append(line)
		_failures += 1
		push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		var line := "[HeroArchetypesParityTest] " + message
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
		print("[HeroArchetypesParityTest] PASS: hero_archetypes.py ↔ Godot (%d checks)" % _checks)
	else:
		# Cetak SETIAP kegagalan ke stdout (bukan hanya push_error) supaya tail
		# log CI memuat alasan lengkapnya.
		for msg in _error_messages:
			print(msg)
		push_error("[HeroArchetypesParityTest] %d failures dari %d checks" % [_failures, _checks])
		print("[HeroArchetypesParityTest] FAIL: %d failures dari %d checks" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
