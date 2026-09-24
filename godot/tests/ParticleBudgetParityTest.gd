# ParticleBudgetParityTest — replay fixture anggaran partikel (Fase 34).
#
# Fixture ditulis oleh tools/test_godot_particle_budget_parity.py yang
# menghitung angkanya dengan `mobile/perf.py` pygame ASLI (di-exec dengan
# stub pygame: set_fx_load/fx_load/claim/refund/allow + _Quality.apply) dan
# dengan `_fx_busy`/`count_busy_fx_heroes` yang disadur AST dari
# heroes/__init__.py. Berkas ini hanya memutar ulang hasil itu pada produksi
# Godot:
#   1. PRESET — AppShell.PARTICLE_RATIO (0.20/0.40/0.70),
#      AppShell.particles_enabled, target FPS, max_damage_numbers, dan rasio
#      efektif penuh AppShell.particle_ratio() pada load 1.0;
#   2. GOVERNOR — kurva fx_load + lantai token setiap langkah
#      set_fx_load(n) (termasuk input jahat `null` -> 0, paritas try/except);
#   3. CLAIM — token nonaktif = gratis; cap penuh 140/18/10 pada load 1.0;
#      lantai 56/10/5 di bawah beban berat; refund mengembalikan 1 token;
#   4. BUSY — _fx_busy per unit (pecahan timer membulat KEBAWAH, unit mati
#      dilewati, proyektil hidup dihitung, hero_type kosong jatuh ke
#      boss_type, tipe non-live-FX tidak masuk hitungan) + jumlah total;
#   5. HIT SPARK — SparkField.add_hit_particles memusatkan jumlah spawn ke
#      `max(0, _py_round(count * ratio))`, 0 kalau particles_enabled false;
#   6. SHADOW KUALITAS — AppShell._apply_quality menulis bayangan
#      settings.quality (sumber max_damage_numbers GameManager);
#   7. INTEGRASI VFX — VFXManager.wall dipotong lantai skill 5 saat beban,
#      pulih saat set_fx_load(0); pin file (klaim/gate 2x di Hero.gd).
#
# godot --headless --path godot res://tests/ParticleBudgetParityTest.tscn
# Require "[ParticleBudgetParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const FIXTURE := "res://tests/fixtures/particle_budget.json"
## Toleransi pembanding double: fixture membawa repr penuh CPython, parser
## JSON Godot membaca double yang sama — sisanya nol; EPS hanya penampung
## noise parser, bukan kelonggaran rumus.
const EPS := 1e-12

var _fx: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _prev_quality: String = ""


## Stuber unit untuk kasus busy: atribut yang "ada" di pygame (getattr)
## dipetakan 1:1 — yang null setara absen (Godot `get()` -> null).
class BusyStub:
	extends Node
	var hero_type = null
	var boss_type = null
	var is_dead := false
	var active_skill = null
	var attack_timer := 0.0
	var timer := 0.0
	var projectiles: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_prev_quality = AppShell.quality_level
	var text := FileAccess.get_file_as_string(FIXTURE)
	if text.is_empty():
		_fail("fixture belum ada — jalankan tools/test_godot_particle_budget_parity.py --write-fixture")
		_finish()
		return
	var parsed = JSON.parse_string(text)
	if parsed == null or not parsed is Dictionary:
		_fail("fixture rusak / bukan JSON objek")
		_finish()
		return
	_fx = parsed
	_test_presets()
	_test_governor_sequence()
	_test_claims()
	_test_busy()
	_test_hit_spark_scaling()
	_test_quality_shadow()
	_test_vfx_integration()
	_test_source_pins()
	AppShell.quality_level = _prev_quality
	AppShell._sync_quality_setting()
	FXLoadGovernor.reset_fx_load()
	_finish()


func _fail(msg: String) -> void:
	_failures += 1
	_checks += 1
	push_error("[ParticleBudgetParityTest] FAIL: " + msg)
	print("[ParticleBudgetParityTest] FAIL: " + msg)


func _ok() -> void:
	_checks += 1


func _expect(cond: bool, msg: String) -> void:
	if cond:
		_ok()
	else:
		_fail(msg)


func _expect_eq(got, want, msg: String) -> void:
	_expect(got == want, "%s — dapat %r, mau %r" % [msg, got, want])


func _expect_close(got: float, want: float, msg: String) -> void:
	_expect(absf(got - want) <= EPS,
		"%s — dapat %.17g, mau %.17g" % [msg, got, want])


# ── 1. PRESET ───────────────────────────────────────────────
func _test_presets() -> void:
	for p in _fx["presets"]:
		var level: String = str(p["level"])
		var base := float(AppShell.PARTICLE_RATIO.get(level, -1.0))
		_expect_close(base, float(p["base"]),
			"PARTICLE_RATIO[%s]" % level)
		AppShell.quality_level = level
		_expect(AppShell.particles_enabled() == bool(p["particles"]),
			"particles_enabled[%s]" % level)
		_expect_eq(AppShell.target_fps(), int(p["target_fps"]),
			"target_fps[%s]" % level)
		# Rasio efektif penuh pada load 1.0 (reset dulu supaya deterministik).
		FXLoadGovernor.reset_fx_load()
		_expect_close(AppShell.particle_ratio(),
			float(p["effective_at_load_1"]), "particle_ratio[%s]" % level)
	# max_damage_numbers: dihitung GameManager.start_level dari shadow.
	for p in _fx["presets"]:
		var level: String = str(p["level"])
		var expect_mdn := 8 if level == "low" else (16 if level == "medium" else 32)
		_expect_eq(expect_mdn, int(p["max_damage_numbers"]),
			"max_damage_numbers[%s] (formula start_level)" % level)


# ── 2. GOVERNOR ─────────────────────────────────────────────
func _test_governor_sequence() -> void:
	FXLoadGovernor.reset_fx_load()
	var rows: Array = _fx["governor_sequence"]
	for i in rows.size():
		var row: Dictionary = rows[i]
		FXLoadGovernor.set_fx_load(row["n"])
		_expect_close(FXLoadGovernor.fx_load(), float(row["fx_load"]),
			"fx_load langkah %d (n=%r)" % [i, row["n"]])
		_expect_eq(FXLoadGovernor.particle_left(),
			int(row["particle_left"]), "particle_left langkah %d" % i)
		_expect_eq(FXLoadGovernor.projectile_left(),
			int(row["projectile_left"]), "projectile_left langkah %d" % i)
		_expect_eq(FXLoadGovernor.skill_projectile_left(),
			int(row["skill_projectile_left"]),
			"skill_projectile_left langkah %d" % i)


# ── 3. CLAIM / REFUND ───────────────────────────────────────
func _test_claims() -> void:
	for scen in _fx["claims"]:
		match str(scen["name"]):
			"inactive_tokens_are_free":
				_claim_inactive(scen)
			"full_caps_at_load_1":
				_claim_full_caps(scen)
			"floors_under_heavy_load":
				_claim_heavy(scen)
			_:
				_fail("skenario claim tak dikenal: %s" % scen["name"])


func _claim_inactive(scen: Dictionary) -> void:
	FXLoadGovernor.reset_fx_load()
	_expect(not FXLoadGovernor.tokens_active(),
		"%s: token harus nonaktif setelah reset" % scen["name"])
	var step_i := 1
	for step in scen["steps"]:
		match str(step["op"]):
			"claim_particle":
				_expect(FXLoadGovernor.claim_fx_particle() ==
					bool(step["expect"]), "claim_particle #%d" % step_i)
			"allow_skill":
				_expect(FXLoadGovernor.allow_skill_projectile() ==
					bool(step["expect"]), "allow_skill #%d" % step_i)
			"refund_particle_x2":
				FXLoadGovernor.refund_fx_particle()
				FXLoadGovernor.refund_fx_particle()
				_expect_eq(FXLoadGovernor.particle_left(),
					int(step["particle_left"]),
					"refund saat nonaktif tidak mengubah stok")
			"reset":
				pass  # state reset sudah dilakukan di kepala skenario
			_:
				_fail("op tak dikenal di %s: %s" % [scen["name"], step["op"]])
		step_i += 1


func _claim_full_caps(scen: Dictionary) -> void:
	FXLoadGovernor.reset_fx_load()
	FXLoadGovernor.set_fx_load(0)
	var header: Dictionary = scen["steps"][0]
	_expect_close(FXLoadGovernor.fx_load(), float(header["fx_load"]),
		"%s: fx_load" % scen["name"])
	_expect_eq(FXLoadGovernor.particle_left(), int(header["particle_left"]),
		"%s: particle_left awal" % scen["name"])
	_expect_eq(FXLoadGovernor.projectile_left(),
		int(header["projectile_left"]), "%s: projectile_left awal" % scen["name"])
	_expect_eq(FXLoadGovernor.skill_projectile_left(),
		int(header["skill_projectile_left"]),
		"%s: skill_projectile_left awal" % scen["name"])
	var s_p: Dictionary = scen["steps"][1]
	var ok_p := 0
	for i in 200:
		if FXLoadGovernor.claim_fx_particle():
			ok_p += 1
	_expect_eq(ok_p, int(s_p["accepted"]), "%s: partikel diterima" % scen["name"])
	_expect(FXLoadGovernor.claim_fx_particle() == bool(s_p["next"]),
		"%s: claim partikel kehabisan cap" % scen["name"])
	var s_j: Dictionary = scen["steps"][2]
	var ok_j := 0
	for i in 30:
		if FXLoadGovernor.claim_fx_projectile():
			ok_j += 1
	_expect_eq(ok_j, int(s_j["accepted"]), "%s: proyektil diterima" % scen["name"])
	_expect(FXLoadGovernor.claim_fx_projectile() == bool(s_j["next"]),
		"%s: claim proyektil kehabisan cap" % scen["name"])
	var s_s: Dictionary = scen["steps"][3]
	var ok_s := 0
	for i in 15:
		if FXLoadGovernor.allow_skill_projectile():
			ok_s += 1
	_expect_eq(ok_s, int(s_s["accepted"]), "%s: skill diterima" % scen["name"])
	_expect(FXLoadGovernor.allow_skill_projectile() == bool(s_s["next"]),
		"%s: allow skill kehabisan cap" % scen["name"])


func _claim_heavy(scen: Dictionary) -> void:
	FXLoadGovernor.reset_fx_load()
	for i in 12:
		FXLoadGovernor.set_fx_load(8)
	var header: Dictionary = scen["steps"][0]
	_expect_close(FXLoadGovernor.fx_load(), float(header["fx_load"]),
		"%s: fx_load" % scen["name"])
	_expect_eq(FXLoadGovernor.particle_left(), int(header["particle_left"]),
		"%s: particle_left lantai" % scen["name"])
	var s_p: Dictionary = scen["steps"][1]
	var ok_p := 0
	for i in 80:
		if FXLoadGovernor.claim_fx_particle():
			ok_p += 1
	_expect_eq(ok_p, int(s_p["accepted"]), "%s: partikel diterima sesuai lantai"
		% scen["name"])
	_expect(FXLoadGovernor.claim_fx_particle() == bool(s_p["denied_extra"]),
		"%s: claim di luar lantai ditolak" % scen["name"])
	FXLoadGovernor.refund_fx_particle()
	_expect_eq(FXLoadGovernor.particle_left(), int(s_p["after_refund"]),
		"%s: refund menambah tepat satu" % scen["name"])
	_expect(FXLoadGovernor.claim_fx_particle() ==
		bool(s_p["claim_after_refund"]),
		"%s: token hasil refund bisa dipakai" % scen["name"])


# ── 4. BUSY ─────────────────────────────────────────────────
func _test_busy() -> void:
	for case in _fx["busy_cases"]:
		var units: Array = []
		for spec in case["units"]:
			var u := BusyStub.new()
			if bool(spec.get("boss", false)):
				u.boss_type = str(spec.get("boss_type_fallback",
					spec.get("kind", "")))
			else:
				u.hero_type = str(spec.get("kind", ""))
			u.is_dead = not bool(spec.get("alive", true))
			if spec.has("active_skill"):
				u.active_skill = spec["active_skill"]
			u.attack_timer = float(spec.get("attack_timer", 0.0))
			if spec.has("timer"):
				u.timer = float(spec["timer"])
			if spec.has("projectiles"):
				u.projectiles = spec["projectiles"]
			add_child(u)
			units.append(u)
		for i in units.size():
			_expect(FXLoadGovernor.fx_busy(units[i]) ==
				bool(case["busy"][i]),
				"%s busy[%d]" % [case["name"], i])
		_expect_eq(FXLoadGovernor.count_busy_fx_units(units),
			int(case["count"]), "%s count" % case["name"])
		for u in units:
			u.queue_free()


# ── 5. HIT SPARK SCALING ────────────────────────────────────
func _test_hit_spark_scaling() -> void:
	for row in _fx["hit_spark_scaling"]:
		var field := SparkField.new()
		field.particle_ratio = float(row["ratio"])
		field.particles_enabled = bool(row["enabled"])
		field.add_hit_particles(0.0, 0.0, "red", int(row["count"]))
		_expect_eq(field.particles.size(), int(row["spawn"]),
			"hit_spark count=%d ratio=%s enabled=%s" % [int(row["count"]),
				str(row["ratio"]), str(row["enabled"])])


# ── 6. SHADOW KUALITAS ──────────────────────────────────────
func _test_quality_shadow() -> void:
	for level in ["low", "medium", "high"]:
		AppShell._apply_quality(level)
		_expect_eq(SaveManager.get_setting_str("quality", "?"), level,
			"shadow settings.quality == %r" % level)


# ── 7. INTEGRASI VFX + PIN SUMBER ───────────────────────────
func _test_vfx_integration() -> void:
	FXLoadGovernor.reset_fx_load()
	for i in 12:
		FXLoadGovernor.set_fx_load(8)
	# Lantai skill 5 (dari skenario heavy): 5 wall pertama lolos, sisanya null.
	var anchor := Node2D.new()
	add_child(anchor)
	var accepted := 0
	for i in 10:
		if VFXManager.wall(anchor, Vector2.ZERO, 0.5, 20.0, Color.RED) != null:
			accepted += 1
	_expect_eq(accepted, FXLoadGovernor.SKILL_PROJECTILE_FLOOR,
		"VFXManager.wall mematuhi lantai skill saat beban berat")
	FXLoadGovernor.set_fx_load(0)
	_expect(VFXManager.wall(anchor, Vector2.ZERO, 0.5, 20.0, Color.RED) != null,
		"token kembali penuh setelah set_fx_load(0)")
	anchor.queue_free()


func _test_source_pins() -> void:
	# Pin runtime terhadap isi file produksi (drift gate/wrap tidak boleh
	# lolos walau engine tidak punya pygame untuk dibandingkan).
	var hero_src := FileAccess.get_file_as_string("res://scenes/hero/Hero.gd")
	_expect_eq(hero_src.count(
		"if not FXLoadGovernor.allow_skill_projectile():"), 2,
		"gate skill projectile di Hero.gd harus tepat 2")
	var vfx_src := FileAccess.get_file_as_string("res://scripts/vfx/VFXManager.gd")
	_expect_eq(vfx_src.count("FXLoadGovernor.claim_fx_particle()"), 1,
		"klaim partikel di VFXManager harus tepat 1 (sparks)")
	_expect_eq(vfx_src.count("FXLoadGovernor.claim_fx_projectile()"), 6,
		"klaim proyektil di VFXManager harus tepat 6 (6 API bentuk)")
	var gm_src := FileAccess.get_file_as_string(
		"res://scripts/autoload/GameManager.gd")
	_expect(gm_src.find("FXLoadGovernor.set_fx_load(") >= 0 and
		gm_src.find("FXLoadGovernor.set_fx_load(") <
		gm_src.find("spark_fx.advance(delta)"),
		"urutan hook governor harus sebelum spark_fx.advance")


func _finish() -> void:
	if _failures == 0:
		print("[ParticleBudgetParityTest] PASS: %d cek" % _checks)
	else:
		print("[ParticleBudgetParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
