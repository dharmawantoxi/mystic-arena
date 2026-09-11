# SystemPerfParityTest — blok `performance.py` + `fps_counter.py` `_system.py`.
#
# Replay fixture `godot/tests/fixtures/system_perf.json` (tools/
# test_system_perf_parity.py) pada KELAS PRODUKSINYA:
#   1. `SpatialGrid.gd` — keanggotaan + URUTAN bucket tiap kueri (9 skenario,
#      termasuk koordinat negatif, batas radius inklusif, `.alive` yang dibaca
#      saat kueri, dan cabang `team=None` yang sama sekali tanpa filter);
#   2. `FrustumCuller.gd` — tabel batas layar (margin 80 + radius);
#   3. `FpsCounter.gd` — aturan riwayat (trim 120, jendela tampil 30, refresh
#      tiap 10 frame) + daftar perintah gambar yang DiHASILKAN `build_ops`,
#      dibandingkan jejak `pygame.draw.rect/line` + `font.render` sungguhan;
#   4. `CombatSystem` — grid dibangun, query targeting lewat grid (urutan bucket,
#      tower/nexus appended di belakang), dan fallback scan langsung saat grid
#      tidak berlaku; himpunan kedua jalur wajib sama.
#
# Bukan tes piksel: `build_ops` mengembalikan op (rect/line/text) — headless
# Godot tidak punya GPU, jadi yang bisa dikunci adalah daftar perintah gambar
# yang dihasilkan, bukan raster-nya. Lebar teks dikirim lewat measurer dari
# fixture supaya posisi yang bergantung lebar (label "FPS", status, "[F8]
# toggle") dibandingkan dengan angka pygame, bukan metrik font Godot.
#
# godot --headless --path godot res://tests/SystemPerfParityTest.tscn --quit-after 300
# Require "[SystemPerfParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const SpatialGridScript = preload("res://scripts/systems/SpatialGrid.gd")
const FpsCounterScript = preload("res://scenes/ui/FpsCounter.gd")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const HeroScene = preload("res://scenes/hero/Hero.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const FIXTURE := "res://tests/fixtures/system_perf.json"

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done := false
var _error_messages: Array[String] = []
var _prev_dispatch: bool = true
var _spawned: Array = []


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	var text := FileAccess.get_file_as_string(FIXTURE)
	if text.is_empty():
		_fail("fixture belum ada — jalankan tools/test_system_perf_parity.py "
			+ "--write-fixture")
		_finish()
		return
	_fixture = JSON.parse_string(text)
	if not (_fixture is Dictionary) or not _fixture.has("grid"):
		_fail("fixture rusak / tanpa seksi `grid`")
		_finish()
		return
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)
	_prev_dispatch = CombatSystem.death_dispatch_enabled
	CombatSystem.death_dispatch_enabled = false
	_test_grid()
	_test_culler()
	_test_fps_history()
	_test_fps_ops()
	_test_combat_wiring()
	_cleanup()
	_finish()


# ══════════════════════════════════════════════════════════
#  1. SpatialGrid — unit Dictionary (x/y/team/is_dead), tanpa node
# ══════════════════════════════════════════════════════════

func _fake_units(rows: Array) -> Array:
	var out: Array = []
	for row in rows:
		out.append({
			"id": str(row["id"]),
			"x": float(row["x"]),
			"y": float(row["y"]),
			"team": str(row["team"]),
			"is_dead": not bool(row["alive"]),
		})
	return out


func _ids(units: Array) -> Array:
	var out: Array = []
	for u in units:
		out.append(str(u["id"]))
	return out


func _test_grid() -> void:
	var grid_fix: Dictionary = _fixture["grid"]
	_checks += 1
	if int(grid_fix["cell_size"]) != 60:
		_fail("fixture cell_size harus 60 (paritas SpatialGrid(cell_size=60))")
	var scenarios: Array = grid_fix["scenarios"]
	var queries := 0
	for sc in scenarios:
		var s: Dictionary = sc
		var minions := _fake_units(s["insert"]["minions"])
		var heroes := _fake_units(s["insert"]["heroes"])
		var prod = SpatialGridScript.new()
		# update_from = padanan badan `update_spatial_grid` (unit mati dilompati)
		prod.update_from(minions, heroes)
		for q in s["queries"]:
			var query: Dictionary = q
			queries += 1
			var got: Array = []
			if query.has("raw"):
				var raw_grid = SpatialGridScript.new()
				for u in _fake_units(query["raw"]):
					raw_grid.insert(u)
				got = _grid_query(raw_grid, query)
			else:
				got = _grid_query(prod, query)
			var want: Array = query["ids"]
			_expect(_ids(got) == want,
				"%s @(%s,%s) r=%s team=%s: grid Godot %s != pygame %s" % [
					s["name"], query["x"], query["y"], query["radius"],
					str(query["team"]), _ids(got), want])
			_expect(got.size() == int(query["count"]),
				"%s: jumlah hasil %d != %d" % [s["name"], got.size(),
					int(query["count"])])
	# Grid harus benar-benar mem-parsel per sel: 400 unit kerumunan tidak boleh
	# masuk satu bucket.
	var crowd: Dictionary = scenarios[scenarios.size() - 1]
	var g = SpatialGridScript.new()
	g.update_from(_fake_units(crowd["insert"]["minions"]),
		_fake_units(crowd["insert"]["heroes"]))
	# kisi 20x20 dengan pitch 17/13 px di cell 60 = puluhan sel, BUKAN 400:
	# bukti grid mem-parsel (kalau semua masuk 1 sel, akseleratornya palsu)
	_expect(g.grid.size() >= 10 and g.grid.size() <= 40,
		"kerumunan 400 unit harus tersebar di puluhan sel (dapat %d)" % g.grid.size())
	print("[SystemPerfParityTest] grid: %d skenario, %d kueri" % [
		scenarios.size(), queries])


func _grid_query(grid, query: Dictionary) -> Array:
	var x := float(query["x"])
	var y := float(query["y"])
	var r := float(query["radius"])
	if query["team"] == null:
		return grid.query_range(x, y, r)
	return grid.query_enemies(x, y, r, str(query["team"]))


# ══════════════════════════════════════════════════════════
#  2. FrustumCuller
# ══════════════════════════════════════════════════════════

func _test_culler() -> void:
	var c: Dictionary = _fixture["culler"]
	var screen := Vector2(float(c["screen"][0]), float(c["screen"][1]))
	_checks += 1
	if int(c["margin"]) != int(FrustumCuller.MARGIN):
		_fail("FrustumCuller.MARGIN %s != pygame %s" % [
			FrustumCuller.MARGIN, c["margin"]])
	for row in c["cases"]:
		var case: Dictionary = row
		var got := FrustumCuller.is_visible(float(case["x"]), float(case["y"]),
			float(case["radius"]), screen)
		_expect(got == bool(case["expect"]),
			"is_visible(%s, %s, r=%s) harus %s, dapat %s" % [case["x"],
				case["y"], case["radius"], case["expect"], got])
	# default radius 30 (pemanggil pygame: `m.radius`, proyektil 10, hero)
	_expect(FrustumCuller.is_visible(0, 0)
			== FrustumCuller.is_visible(0, 0, float(c["default_radius"]), screen),
		"radius default harus 30 seperti pygame")
	# Layar Godot = viewport yang DIKIRIM, bukan konstanta beku. Angka di bawah
	# dipilih dengan margin yang benar: titik (900,400) dengan radius 30 punya
	# batas x = 640 + (80+30) = 750 di layar 640x480 -> ter-cull; di 1280x720
	# batasnya 1390 -> terlihat. Jadi yang berubah hanya ukuran layarnya.
	_expect(not FrustumCuller.is_visible(900, 400, 30.0, Vector2(640, 480)),
		"x=900 harus ter-cull di layar 640 (batas 640 + margin 80 + radius 30)")
	_expect(FrustumCuller.is_visible(900, 400, 30.0, Vector2(1280, 720)),
		"titik yang sama harus TERLIHAT di layar 1280 — ukuran layar dihormati")


# ══════════════════════════════════════════════════════════
#  3. FpsCounter — aturan riwayat
# ══════════════════════════════════════════════════════════

func _test_fps_history() -> void:
	var fps: Dictionary = _fixture["fps"]
	var counter = FpsCounterScript.new()
	add_child(counter)
	counter.set_process(false)
	_expect(int(counter.HISTORY_SIZE) == int(fps["history_size"]),
		"HISTORY_SIZE harus %d (pygame `history_size = 120`), dapat %d" % [
			int(fps["history_size"]), counter.HISTORY_SIZE])
	_expect(int(counter.DISPLAY_WINDOW) == int(fps["display_window"]),
		"jendela tampil harus %d" % int(fps["display_window"]))
	_expect(int(counter.DISPLAY_EVERY) == int(fps["display_every"]),
		"refresh angka harus tiap %d frame" % int(fps["display_every"]))
	var prev := [0.0, 0.0, 0.0, 0.0]
	var seen: Array = []
	for i in range((fps["samples"] as Array).size()):
		counter.update(float((fps["samples"] as Array)[i]))
		var cur := [counter.display_fps, counter.display_avg,
			counter.display_min, counter.display_max]
		if cur != prev:
			seen.append({"frame": i + 1, "display_fps": cur[0],
				"display_avg": cur[1], "display_min": cur[2],
				"display_max": cur[3]})
			prev = cur
	var want: Array = fps["trace"]
	_expect(seen.size() == want.size(),
		"jumlah pembaruan panel %d != pygame %d" % [seen.size(), want.size()])
	for k in range(mini(seen.size(), want.size())):
		var got_u: Dictionary = seen[k]
		var want_u: Dictionary = want[k]
		_expect(int(got_u["frame"]) == int(want_u["frame"]),
			"pembaruan #%s pada frame %s != pygame %s" % [k + 1,
				got_u["frame"], want_u["frame"]])
		for key in ["display_fps", "display_avg", "display_min", "display_max"]:
			_near(float(got_u[key]), float(want_u[key]),
				"%s saat frame %s" % [key, want_u["frame"]], 1e-6)
	_expect(counter.fps_history.size() == int(fps["history_size"]),
		"riwayat di-trim ke %d (dapat %d)" % [int(fps["history_size"]),
			counter.fps_history.size()])
	var state: Dictionary = fps["state"]
	# eps 1e-6: rumus statistiknya identik, jadi tidak boleh ada toleransi raster
	for key in ["display_fps", "display_avg", "display_min", "display_max"]:
		_near(float(counter.get(key)), float(state[key]), "%s akhir" % key, 1e-6)
	# toggle: ON/OFF + print `[FPS COUNTER] ...` seperti pygame
	counter.set_enabled(false)
	counter.toggle()
	_expect(counter.enabled and counter.visible, "toggle menyalakan panel")
	counter.toggle()
	_expect(not counter.enabled and not counter.visible,
		"toggle kedua mematikan panel (pygame: draw() no-op saat !enabled)")
	counter.free()


# ══════════════════════════════════════════════════════════
#  4. FpsCounter — daftar perintah gambar vs jejak pygame
# ══════════════════════════════════════════════════════════

func _test_fps_ops() -> void:
	var fps: Dictionary = _fixture["fps"]
	var widths := {}
	for r in fps["render"]:
		widths["%s|%d" % [r["text"], int(r["size"])]] = int(r["w"])
	var measurer := func(text: String, size: int) -> float:
		var key := "%s|%d" % [text, size]
		return float(widths[key]) if widths.has(key) else 0.0
	# `state_short` = angka panel yang sedang berlaku saat jejak render pygame
	# diambil (update ke-20 dari 21 sampel; frame 21 tidak me-refresh).
	var st: Dictionary = fps["state_short"]
	var state := {
		"display_fps": float(st["display_fps"]),
		"display_avg": float(st["display_avg"]),
		"display_min": float(st["display_min"]),
		"display_max": float(st["display_max"]),
		"fps_history": (fps["samples_short"] as Array).duplicate(),
	}
	var got: Array = FpsCounterScript.build_ops(state, measurer)
	var want: Array = fps["ops"]
	_expect(got.size() == want.size(),
		"jumlah op %d != jejak pygame %d" % [got.size(), want.size()])
	for i in range(mini(got.size(), want.size())):
		_deep(want[i], got[i], "op[%d]" % i)
	# tangga warna/status: angka fixtures (ops text) sudah dipinjam dari
	# render pygame; pastikan fungsi statisnya konsisten untuk semua band
	for band in [[60.0, "SMOOTH", [100, 255, 100]], [55.0, "SMOOTH", [100, 255, 100]],
			[54.9, "OK", [255, 255, 100]], [40.0, "OK", [255, 255, 100]],
			[39.9, "SLOW", [255, 150, 50]], [25.0, "SLOW", [255, 150, 50]],
			[24.9, "LAG!", [255, 60, 60]], [0.0, "LAG!", [255, 60, 60]]]:
		var v := float(band[0])
		_expect(FpsCounterScript.status_for(v) == str(band[1]),
			"status_for(%s) harus %s" % [v, band[1]])
		_expect((FpsCounterScript.number_color_for(v) as Array) == (band[2] as Array),
			"number_color_for(%s) harus %s" % [v, band[2]])
	# bar memakai tangga warna KEDUA yang lebih gelap (quirk pygame)
	_expect((FpsCounterScript.bar_color_for(60.0) as Array) == [50, 160, 50],
		"bar 60 fps harus (50,160,50), bukan warna teks")
	_expect(FpsCounterScript.bar_height_for(60.0) == 16,
		"tinggi bar 60 fps = int(22*60/80) = 16")
	_expect(FpsCounterScript.bar_height_for(80.0) == 22,
		"bar di-clamp ke skala 80 -> tinggi penuh 22")


func _deep(want, got, path: String) -> void:
	if want is Array:
		var wa: Array = want
		if not (got is Array):
			_expect(false, "%s: bukan array (%s)" % [path, str(got)])
			return
		var ga: Array = got
		_expect(wa.size() == ga.size(),
			"%s: panjang %d != %d" % [path, ga.size(), wa.size()])
		for i in range(mini(wa.size(), ga.size())):
			_deep(wa[i], ga[i], "%s[%d]" % [path, i])
		return
	if want is Dictionary:
		var wd: Dictionary = want
		if not (got is Dictionary):
			_expect(false, "%s: bukan dictionary (%s)" % [path, str(got)])
			return
		var gd: Dictionary = got
		for key in wd:
			if not gd.has(key):
				_expect(false, "%s: field `%s` hilang (godot: %s)" % [path, key, gd])
				continue
			_deep(wd[key], gd[key], "%s.%s" % [path, str(key)])
		for key in gd:
			_expect(wd.has(key), "%s: field asing `%s` = %s" % [path, key, gd[key]])
		return
	if want is float or want is int:
		var wv := float(want)
		var gv := float(got) if (got is float or got is int) else INF
		_checks += 1
		if absf(wv - gv) > 1e-6:
			_fail("%s: %s != %s" % [path, got, want])
		return
	_expect(str(got) == str(want), "%s: '%s' != '%s' (pygame)" % [path, got, want])


# ══════════════════════════════════════════════════════════
#  5. CombatSystem — wiring grid (jalur produksi) + fallback
# ══════════════════════════════════════════════════════════

func _make_minion(pos: Vector2, team: String):
	var m = MinionScene.instantiate()
	m.minion_type = "goblin"
	m.team = team
	m.lane = "mid"
	m.lane_path = PackedVector2Array()
	m.position = pos
	add_child(m)
	_spawned.append(m)
	m.set_physics_process(false)
	m.set_process(false)
	m.max_hp = 9000.0
	m.hp = 9000.0
	return m


func _make_hero(pos: Vector2, team: String):
	var h = HeroScene.instantiate()
	h.hero_type = "kaizen"
	h.team = team
	h.position = pos
	add_child(h)
	_spawned.append(h)
	h.set_physics_process(false)
	h.set_process(false)
	return h


func _make_tower(pos: Vector2, team: String):
	var t = TowerScene.instantiate()
	t.tower_type = "archer"
	t.team = team
	t.level = 1
	t.position = pos
	add_child(t)
	_spawned.append(t)
	t.set_physics_process(false)
	t.set_process(false)
	return t


func _test_combat_wiring() -> void:
	CombatSystem.reset_spatial_grid()
	# ── sebelum ada build: fallback scan langsung, hasil identik dengan
	#    enemies_in_radius (inilah yang menjaga harness lama tetap hijau) ──
	_expect(not CombatSystem.spatial_grid_fresh(),
		"habis reset_spatial_grid grid tidak boleh dianggap berlaku")
	# Semua unit di bawah MUSUH tim "blue" (hero AI + menara merah + minion
	# merah), supaya urutan grup vs urutan bucket bisa dibandingkan langsung.
	var m0 = _make_minion(Vector2(300, 200), "red")
	var m1 = _make_minion(Vector2(320, 200), "red")
	var h0 = _make_hero(Vector2(330, 200), "red")
	var t0 = _make_tower(Vector2(310, 240), "red")
	var center := Vector2(315, 210)
	var fallback: Array = CombatSystem.query_enemies_in_range("blue", center, 120.0)
	var direct: Array = CombatSystem.enemies_in_radius("blue", center, 120.0)
	_expect(_same_set(fallback, direct),
		"fallback grid = scan langsung (himpunan sama)")
	_expect(fallback.size() >= 3,
		"setup skenario harus ketemu 3+ musuh (dapat %d)" % fallback.size())
	_expect(fallback[0] == h0,
		"tanpa grid urutannya ikut GRUP (heroes -> minions -> towers), dapat %s"
		% _node_ids(fallback))
	# ── grid aktif: urutan = urutan bucket (minion -> hero), tower/nexus di
	#    belakang; himpunan tetap sama dengan scan langsung ──
	CombatSystem.update_spatial_grid_from_tree()
	_expect(CombatSystem.spatial_grid_fresh(), "setelah update grid berlaku")
	var via_grid: Array = CombatSystem.query_enemies_in_range("blue", center, 120.0)
	_expect(_same_set(via_grid, direct),
		"grid vs scan langsung harus mengembalikan himpunan yang sama")
	_expect(via_grid[0] == m0 and via_grid[1] == m1 and via_grid[2] == h0,
		"urutan grid = urutan insert (minion dulu, hero belakangan), bukan urutan "
		+ "grup: %s" % _node_ids(via_grid))
	_expect(via_grid[via_grid.size() - 1] == t0,
		"tower/nexus tidak diindeks grid -> appended paling akhir")
	# ── unit mati tidak masuk grid; jarak dibaca LANGSUNG dari posisi hidup ──
	h0.is_dead = true
	CombatSystem.update_spatial_grid_from_tree()
	var after: Array = CombatSystem.query_enemies_in_range("blue", center, 120.0)
	_expect(not after.has(h0), "hero mati tidak boleh terindeks")
	m1.position = Vector2(9000, 9000)
	var moved: Array = CombatSystem.query_enemies_in_range("blue", center, 120.0)
	_expect(not moved.has(m1),
		"jarak dibandingkan dengan posisi SAAT INI: unit yang kabur keluar radius "
		+ "harus terbuang walau bucket-nya masih lama")
	m1.position = Vector2(320, 200)
	# ── kebalikannya (paritas pygame, BUKAN bug port): unit yang BERGESER MASUK
	#    radius baru terlihat setelah grid dibangun ulang, karena build-nya
	#    terjadwal 2 frame sekali (`animation_time % 2 == 0`, _core.py:2009) ──
	var late = _make_minion(Vector2(4000, 4000), "red")
	CombatSystem.update_spatial_grid_from_tree()
	late.position = center + Vector2(5, 0)
	_expect(not CombatSystem.query_enemies_in_range("blue", center, 120.0)
		.has(late),
		"bucket basi = kandidat belum terlihat (persis perilaku grid pygame)")
	CombatSystem.update_spatial_grid_from_tree()
	_expect(CombatSystem.query_enemies_in_range("blue", center, 120.0).has(late),
		"setelah rebuild, unit yang masuk radius harus terlihat")
	# ── query jauh di luar kerumunan: tetap kosong, tidak crash ──
	_expect(CombatSystem.query_enemies_in_range("blue", Vector2(-5000, -5000), 40.0)
		.is_empty(), "kueri di luar peta = kosong")
	# ── grid basi -> kembali ke scan langsung (jalur menu/pause/harness) ──
	CombatSystem.reset_spatial_grid()
	_expect(_same_set(CombatSystem.query_enemies_in_range("blue", center, 120.0),
		CombatSystem.enemies_in_radius("blue", center, 120.0)),
		"grid basi harus jatuh ke scan langsung, bukan hasil kosong")
	print("[SystemPerfParityTest] wiring grid ok (%d kandidat)" % via_grid.size())


func _node_ids(units: Array) -> String:
	var out: Array = []
	for u in units:
		out.append("%s@(%d,%d)" % [(u as Node).name, int((u as Node2D).position.x),
			int((u as Node2D).position.y)])
	return ", ".join(out)


func _same_set(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for e in a:
		if not b.has(e):
			return false
	return true


func _cleanup() -> void:
	for n in _spawned:
		if is_instance_valid(n):
			n.free()
	_spawned.clear()
	CombatSystem.reset_spatial_grid()


func _fail(message: String) -> void:
	_failures += 1
	var line := "[SystemPerfParityTest] %s" % message
	_error_messages.append(line)
	if _error_messages.size() <= 40:
		push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_fail("%s: %.6f != %.6f" % [message, a, b])


func _finish() -> void:
	if _done:
		return
	_done = true
	CombatSystem.death_dispatch_enabled = _prev_dispatch
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print("[SystemPerfParityTest] PASS: %d cek grid/culler/fps/wiring" % _checks)
		print("[SystemPerfParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[SystemPerfParityTest] %d failures dari %d checks" % [
			_failures, _checks])
		print("[SystemPerfParityTest] FAIL: %d failures dari %d checks" % [
			_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
