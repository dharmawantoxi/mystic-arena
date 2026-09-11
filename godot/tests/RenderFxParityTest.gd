# RenderFxParityTest — blok `effects.py` di `_render.py` (FASE 26).
#
# Replay fixture `godot/tests/fixtures/render_fx.json` (ditulis
# `tools/test_render_parity.py`, yang menjalankan `HitParticle`,
# `DeathExplosion`, `EffectManager`, dan `PathPreview` pygame SUNGGUHAN lalu
# merekam jejak `pygame.draw.circle/polygon` + `transform.scale` +
# `Surface.blit` + `set_alpha`) pada KELAS PRODUKSINYA:
#   1. `HitSpark.gd`   — gerak 60 Hz + aturan alpha/ukuran + dua lingkaran
#      (pusat = posisi blit + pusat sprite × faktor skala, bisa setengah piksel);
#   2. `DeathBurst.gd` — palet tim, preset 8/15/25 partikel, kilat 8 frame,
#      dan URUTAN konsumsi RNG (angle → speed → warna → spark → lifetime);
#   3. `SparkField.gd` — jumlah per `count`, palet, batas 500/80 (buang tertua);
#   4. `PathPreview.gd` — 130 frame state machine + jejak polygon pada jalur
#      lane ASLI PathGenerator (fade in 20 / fade out 40, offset, pulse).
#
# RNG: `random` pygame dan RNG Godot beda algoritma, jadi fixture merekam
# NILAI yang dikonsumsi pygame dan `ScriptedRng` di bawah memutar ulangnya
# sambil memeriksa nama fungsi + rentang argumennya. Roll yang hilang /
# bertambah / tertukar urutan = gagal.
#
# Bukan tes piksel: yang dibandingkan daftar perintah gambar (circle/polygon:
# pusat, radius/titik, warna+alpha). Headless Godot tidak punya GPU.
#
# godot --headless --path godot res://tests/RenderFxParityTest.tscn --quit-after 300
# Require "[RenderFxParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const HitSparkScript = preload("res://scripts/render/HitSpark.gd")
const DeathBurstScript = preload("res://scripts/render/DeathBurst.gd")
const SparkFieldScript = preload("res://scripts/render/SparkField.gd")
const PathPreviewScript = preload("res://scenes/fx/PathPreview.gd")
const FIXTURE := "res://tests/fixtures/render_fx.json"
## Toleransi perbandingan: fixture menyimpan angka pygame dibulatkan 6 desimal
## (tools/test_render_parity.py `_round3`), jadi selisih < 2e-6 = identik.
const EPS := 0.000002

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done := false
var _error_messages: Array[String] = []


## RNG ter-script dari jejak `random` pygame (lihat kepala berkas).
class ScriptedRng:
	extends RefCounted
	var calls: Array = []
	var pos := 0
	var problems: Array = []

	func uniform(lo: float, hi: float) -> float:
		var c = _take("uniform")
		if c.is_empty():
			return 0.0
		_args(c, [lo, hi])
		return float(c["value"])

	func randint(lo: int, hi: int) -> int:
		var c = _take("randint")
		if c.is_empty():
			return lo
		_args(c, [float(lo), float(hi)])
		return int(c["value"])

	func choice(options: Array) -> Array:
		var c = _take("choice")
		if c.is_empty():
			return options[0]
		var want: Array = c["args"][0]
		if want.size() != options.size():
			problems.append("choice: %d opsi, pygame %d"
				% [options.size(), want.size()])
		else:
			for i in range(want.size()):
				if not _same_color(options[i], want[i]):
					problems.append("choice: opsi[%d] %s != pygame %s"
						% [i, options[i], want[i]])
		var idx := int(c["value"])
		if idx < 0 or idx >= options.size():
			problems.append("choice: indeks %d di luar %d opsi"
				% [idx, options.size()])
			return options[0]
		return options[idx]

	func remaining() -> int:
		return calls.size() - pos

	func _take(fn: String) -> Dictionary:
		if pos >= calls.size():
			problems.append("roll %s ke-%d TIDAK ADA di jejak pygame"
				% [fn, pos + 1])
			return {}
		var c: Dictionary = calls[pos]
		pos += 1
		if str(c["fn"]) != fn:
			problems.append("roll ke-%d: pygame %s, Godot %s"
				% [pos, c["fn"], fn])
			return {}
		return c

	func _args(c: Dictionary, got: Array) -> void:
		var want: Array = c["args"]
		if want.size() != got.size():
			problems.append("argumen %s: %s != pygame %s"
				% [c["fn"], got, want])
			return
		for i in range(want.size()):
			if absf(float(want[i]) - float(got[i])) > EPS:
				problems.append("argumen %s[%d]: %s != pygame %s"
					% [c["fn"], i, got[i], want[i]])

	static func _same_color(a, b) -> bool:
		var aa: Array = a
		var bb: Array = b
		if aa.size() != bb.size():
			return false
		for i in range(aa.size()):
			if int(aa[i]) != int(bb[i]):
				return false
		return true


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	var text := FileAccess.get_file_as_string(FIXTURE)
	if text.is_empty():
		_fail("fixture belum ada — jalankan tools/test_render_parity.py "
			+ "--write-fixture")
		_finish()
		return
	_fixture = JSON.parse_string(text)
	if not (_fixture is Dictionary) or not _fixture.has("spark"):
		_fail("fixture rusak / tanpa seksi `spark`")
		_finish()
		return
	_test_sparks()
	_test_bursts()
	_test_hits()
	_test_caps()
	_test_path_preview()
	_test_wiring()
	_finish()


# ══════════════════════════════════════════════════════════
#  1. HitSpark — velocity/lifetime/size eksplisit (tanpa RNG)
# ══════════════════════════════════════════════════════════

func _test_sparks() -> void:
	for case in _fixture["spark"]:
		var init: Dictionary = case["init"]
		var spark = HitSparkScript.new(float(init["x"]), float(init["y"]),
			init["color"], init["velocity"], int(init["lifetime"]),
			int(init["size"]), null)
		_expect(absf(spark.gravity - 0.15) < EPS,
			"%s: gravity harus 0.15" % case["name"])
		for frame in case["frames"]:
			_expect(int(spark.lifetime) == int(frame["lifetime"]),
				"%s frame %d: lifetime %d != pygame %d"
				% [case["name"], frame["step"], spark.lifetime,
					frame["lifetime"]])
			_expect(spark.alive == bool(frame["alive"]),
				"%s frame %d: alive != pygame" % [case["name"], frame["step"]])
			_same_ops(spark.build_ops(), frame["ops"],
				"%s frame %d" % [case["name"], frame["step"]])
			spark.update()
		var fin: Dictionary = case["final"]
		_near(spark.x, float(fin["x"]), "%s: x akhir" % case["name"])
		_near(spark.y, float(fin["y"]), "%s: y akhir" % case["name"])
		_near(spark.vx, float(fin["vx"]), "%s: vx akhir (gesekan)"
			% case["name"])
		_near(spark.vy, float(fin["vy"]), "%s: vy akhir (gravitasi)"
			% case["name"])
		_expect(spark.alive == bool(fin["alive"]),
			"%s: status akhir != pygame" % case["name"])


# ══════════════════════════════════════════════════════════
#  2. DeathBurst — RNG direplay dari jejak pygame
# ══════════════════════════════════════════════════════════

func _test_bursts() -> void:
	for case in _fixture["burst"]:
		var init: Dictionary = case["init"]
		var rng := ScriptedRng.new()
		rng.calls = case["rng_calls"]
		var burst = DeathBurstScript.new(float(init["x"]), float(init["y"]),
			str(init["team"]), str(init["size"]), rng)
		for msg in rng.problems:
			_fail("%s: %s" % [case["name"], msg])
		_expect(rng.remaining() == 0,
			"%s: %d roll pygame tidak dikonsumsi Godot"
			% [case["name"], rng.remaining()])
		var want: Array = case["particles"]
		_expect(burst.particles.size() == want.size(),
			"%s: %d partikel != pygame %d"
			% [case["name"], burst.particles.size(), want.size()])
		for i in range(mini(burst.particles.size(), want.size())):
			var got = burst.particles[i]
			var row: Dictionary = want[i]
			_near(got.vx, float(row["vx"]), "%s[%d] vx" % [case["name"], i])
			_near(got.vy, float(row["vy"]), "%s[%d] vy" % [case["name"], i])
			_expect(int(got.lifetime) == int(row["lifetime"]),
				"%s[%d] lifetime %d != pygame %d"
				% [case["name"], i, got.lifetime, row["lifetime"]])
			_expect(int(got.size) == int(row["size"]),
				"%s[%d] ukuran spark %d != pygame %d"
				% [case["name"], i, got.size, row["size"]])
			_expect(int(got.color[0]) == int((row["color"] as Array)[0])
				and int(got.color[1]) == int((row["color"] as Array)[1])
				and int(got.color[2]) == int((row["color"] as Array)[2]),
				"%s[%d] warna %s != pygame %s"
				% [case["name"], i, got.color, row["color"]])
		var step := 0
		for frame in case["frames"]:
			while step < int(frame["step"]):
				burst.update()
				step += 1
			_expect(int(burst.flash_timer) == int(frame["flash"]),
				"%s frame %d: flash %d != pygame %d"
				% [case["name"], frame["step"], burst.flash_timer,
					frame["flash"]])
			_expect(burst.is_alive() == bool(frame["alive"]),
				"%s frame %d: alive != pygame" % [case["name"], frame["step"]])
			_same_ops(burst.build_ops(), frame["ops"],
				"%s frame %d" % [case["name"], frame["step"]])
		var steps := int(init["steps"])
		while step < steps:
			burst.update()
			step += 1
		_expect(not burst.is_alive(),
			"%s: masih hidup setelah %d frame" % [case["name"], steps])


# ══════════════════════════════════════════════════════════
#  3. SparkField — add_hit_particles + batas
# ══════════════════════════════════════════════════════════

func _test_hits() -> void:
	var pyq: Dictionary = _fixture["py_quality"]
	for case in _fixture["hit"]:
		var init: Dictionary = case["init"]
		var field = SparkFieldScript.new()
		# Rasio kualitas pygame (0.70 di preset HIGH desktop) dipasang supaya
		# yang dibandingkan MESIN-nya. Produksi Godot tetap 1.0 karena
		# adaptive quality belum diport — dikunci di _test_wiring.
		field.particle_ratio = float(pyq["particle_ratio"])
		var rng := ScriptedRng.new()
		rng.calls = case["rng_calls"]
		field.rng = rng
		field.add_hit_particles(float(init["x"]), float(init["y"]),
			str(init["team"]), int(init["count"]))
		for msg in rng.problems:
			_fail("hit %s: %s" % [case["name"], msg])
		_expect(rng.remaining() == 0,
			"hit %s: %d roll pygame tidak dikonsumsi"
			% [case["name"], rng.remaining()])
		var want: Array = case["particles"]
		_expect(field.particles.size() == want.size(),
			"hit %s: %d partikel != pygame %d (count=%d × rasio %s)"
			% [case["name"], field.particles.size(), want.size(),
				init["count"], pyq["particle_ratio"]])
		for i in range(mini(field.particles.size(), want.size())):
			var got = field.particles[i]
			var row: Dictionary = want[i]
			_near(got.vx, float(row["vx"]), "hit %s[%d] vx" % [case["name"], i])
			_near(got.vy, float(row["vy"]), "hit %s[%d] vy" % [case["name"], i])
			_expect(int(got.lifetime) == int(row["lifetime"]),
				"hit %s[%d] lifetime != pygame" % [case["name"], i])
			_expect(int(got.size) == int(row["size"]),
				"hit %s[%d] ukuran != pygame" % [case["name"], i])
		_same_ops(field.build_ops(), case["ops"], "hit %s" % case["name"])


func _test_caps() -> void:
	var caps: Dictionary = _fixture["caps"]
	var field = SparkFieldScript.new()
	field.particle_ratio = 1.0
	var rng := ScriptedRng.new()
	rng.calls = []
	for i in range(int(caps["added_particles"]) / 10):
		field.add_hit_particles(float(i), 0.0, "red", 10)
	_expect(field.particles.size() == int(caps["particles_after"]),
		"partikel harus terpangkas ke %s, dapat %d"
		% [caps["particles_after"], field.particles.size()])
	_expect(field.particles.size() > 0, "partikel harus tersisa setelah trim")
	if field.particles.size() > 0:
		_near(float(field.particles[0].get("x")),
			float(caps["first_particle_x"]), "partikel tertua terbuang")
	for i in range(int(caps["added_explosions"])):
		field.add_death_explosion(float(i), 0.0, "red", "small")
	_expect(field.explosions.size() == int(caps["explosions_after"]),
		"ledakan harus terpangkas ke %s, dapat %d"
		% [caps["explosions_after"], field.explosions.size()])
	_near(float(field.explosions[0].get("x")),
		float(caps["first_explosion_x"]), "ledakan tertua terbuang")
	# `advance()` = kadens 60 Hz: 1 detik = 60 tick, bukan 1.
	var ticked = SparkFieldScript.new()
	ticked.add_death_explosion(0.0, 0.0, "red", "small")
	for _i in range(60):
		ticked.advance(1.0 / 60.0)
	_expect(ticked.explosions.is_empty(),
		"advance(1/60) × 60 harus menghabiskan kilat 8 frame + partikel")


# ══════════════════════════════════════════════════════════
#  4. PathPreview — state machine + polygon
# ══════════════════════════════════════════════════════════

func _test_path_preview() -> void:
	var data: Dictionary = _fixture["path_preview"]
	var lanes: Array = []
	for lane in data["paths"]:
		var pts := PackedVector2Array()
		for pt in lane:
			pts.append(Vector2(float((pt as Array)[0]), float((pt as Array)[1])))
		lanes.append(pts)
	var preview = PathPreviewScript.new()
	preview.show_paths(lanes)
	_expect(preview.active and preview.timer == 120,
		"show_paths harus mengaktifkan preview dengan timer penuh")
	var by_step := {}
	for frame in data["frames"]:
		by_step[int(frame["step"])] = frame
	var timeline: Array = data["timeline"]
	for row in timeline:
		preview.tick()
		var step := int(row["step"])
		_expect(preview.timer == int(row["timer"]),
			"frame %d: timer %d != pygame %d" % [step, preview.timer,
				row["timer"]])
		_expect(preview.active == bool(row["active"]),
			"frame %d: active != pygame" % step)
		if by_step.has(step):
			var frame: Dictionary = by_step[step]
			var ops := PathPreviewScript.build_ops(lanes, int(frame["anim"]),
				preview.timer)
			_same_ops(ops, frame["ops"], "path frame %d" % step)
	_expect(preview.paths.is_empty(),
		"setelah 120 frame jalur lane harus dibuang (paritas PathPreview.update)")
	# Fade in/out dibaca dari warna op: alpha penuh 200 hanya di tengah.
	var mid: Dictionary = by_step[60]
	var first_alpha := int(((mid["ops"] as Array)[0]["color"] as Array)[3])
	_expect(first_alpha == 200,
		"alpha penuh harus 200 di tengah durasi, dapat %d" % first_alpha)
	preview.free()


# ══════════════════════════════════════════════════════════
#  5. Wiring produksi (deviasi rasio kualitas dikunci di sini)
# ══════════════════════════════════════════════════════════

func _test_wiring() -> void:
	var field = SparkFieldScript.new()
	_expect(absf(field.particle_ratio - 1.0) < EPS,
		"produksi Godot memakai rasio partikel 1.0 (adaptive quality belum "
		+ "diport); pygame default HIGH = %s — selisih ini dicatat fixture"
		% _fixture["py_quality"]["particle_ratio"])
	_expect(field.particles_enabled,
		"partikel default nyala (paritas Quality.particles=True di HIGH)")
	field.add_hit_particles(0.0, 0.0, "red", 4)
	_expect(field.particles.size() == 4,
		"count=4 tanpa pemangkasan kualitas harus menghasilkan 4 percikan, "
		+ "dapat %d" % field.particles.size())
	# GameManager memegang satu lapangan global + men-tick-nya.
	_expect(GameManager.spark_fx != null,
		"GameManager harus punya spark_fx (satu EffectManager global)")
	GameManager.spark_fx.reset()
	GameManager.spark_fx.add_death_explosion(10.0, 10.0, "blue", "small")
	_expect(GameManager.spark_fx.explosions.size() == 1,
		"spark_fx.add_death_explosion harus mengisi lapangan global")
	GameManager.spark_fx.tick()
	GameManager.spark_fx.reset()
	_expect(GameManager.spark_fx.explosions.is_empty()
		and GameManager.spark_fx.particles.is_empty(),
		"spark_fx.reset harus mengosongkan partikel + ledakan")


# ══════════════════════════════════════════════════════════
#  helper
# ══════════════════════════════════════════════════════════

func _same_ops(got: Array, want: Array, label: String) -> void:
	_checks += 1
	if got.size() != want.size():
		_fail("%s: %d op != pygame %d op" % [label, got.size(), want.size()])
		return
	for i in range(want.size()):
		var g: Dictionary = got[i]
		var w: Dictionary = want[i]
		if str(g["op"]) != str(w["op"]):
			_fail("%s op[%d]: %s != pygame %s"
				% [label, i, g["op"], w["op"]])
			return
		if not _same_color(g["color"], w["color"]):
			_fail("%s op[%d]: warna %s != pygame %s"
				% [label, i, g["color"], w["color"]])
			return
		if str(w["op"]) == "circle":
			if absf(float(g["x"]) - float(w["x"])) > EPS \
					or absf(float(g["y"]) - float(w["y"])) > EPS \
					or absf(float(g["r"]) - float(w["r"])) > EPS:
				_fail("%s op[%d]: circle (%.4f, %.4f) r %.4f != pygame "
					+ "(%.4f, %.4f) r %.4f"
					% [label, i, g["x"], g["y"], g["r"], w["x"], w["y"],
						w["r"]])
				return
		else:
			var gp: Array = g["points"]
			var wp: Array = w["points"]
			if gp.size() != wp.size():
				_fail("%s op[%d]: %d titik != pygame %d"
					% [label, i, gp.size(), wp.size()])
				return
			for j in range(wp.size()):
				var a: Array = gp[j]
				var b: Array = wp[j]
				if absf(float(a[0]) - float(b[0])) > EPS \
						or absf(float(a[1]) - float(b[1])) > EPS:
					_fail("%s op[%d] titik[%d]: (%.4f, %.4f) != pygame "
						+ "(%.4f, %.4f)"
						% [label, i, j, a[0], a[1], b[0], b[1]])
					return


func _same_color(a, b) -> bool:
	var aa: Array = a
	var bb: Array = b
	if aa.size() != bb.size():
		return false
	for i in range(aa.size()):
		if int(aa[i]) != int(bb[i]):
			return false
	return true


func _fail(message: String) -> void:
	_failures += 1
	var line := "[RenderFxParityTest] %s" % message
	_error_messages.append(line)
	if _error_messages.size() <= 40:
		push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _near(a: float, b: float, message: String, eps: float = EPS) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_fail("%s: %.6f != %.6f" % [message, a, b])


func _finish() -> void:
	if _done:
		return
	_done = true
	if _failures == 0:
		print("[RenderFxParityTest] PASS: %d cek spark/burst/hit/caps/path"
			% _checks)
		print("[RenderFxParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[RenderFxParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[RenderFxParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
