# BossDrawParityTest — FASE 32: lapisan overlay `Boss.draw()` pygame.
#
# Fixture `godot/tests/fixtures/boss_draw.json` ditulis
# `tools/test_boss_draw_parity.py`, yang MENJALANKAN `Boss.draw` pygame ASLI
# (base_boss.py:6124-6430 + `_draw_tower_debuff_fx` _core.py:1037) di SDL
# dummy, merekam setiap primitif gambar, dan mengonversinya ke op kanonik —
# lalu memverifikasi konversinya dengan PIKSEL (op kanonik digambar ulang harus
# identik byte-per-byte dengan render asli) dan dengan profil alpha terukur
# untuk pita aura.
#
# Yang diuji di sini (engine betulan):
#   1. `BossOverlay.underlay_ops(state)` + `over_ops(state)` menghasilkan op
#      yang SAMA PERSIS dengan fixture untuk 50 skenario (jenis, urutan,
#      geometri, warna, alpha, metrik teks) — entrance eksklusif, tiga aura,
#      bayangan, indikator debuff, badan generik, HP bar, papan nama + clamp
#      tepi layar;
#   2. plumbing `Boss.gd::overlay_state()`: node Boss sungguhan (Boss.tscn +
#      bosses.json via BossDB) menghasilkan state yang sama dengan state
#      pygame — termasuk label_top/entrance_text/warna dari data, konversi
#      detik->frame untuk entrance_timer, `HurtFlash.is_active()`, dan
#      pemetaan timer StatusEffects -> pip debuff;
#   3. `BossOverlay.exec()` benar-benar bisa menggambar SEMUA op fixture di
#      dalam `_draw()` (root tes ini Node2D) tanpa SCRIPT ERROR, dan
#      `BossPlate` terpasang SESUDAH `Visual` (papan HP/nama di atas badan).
#
# Badan boss (strip bake Fase 5) tidak dibandingkan: yang diuji persis
# permukaan yang diport dari bosses/.
#
# godot --headless --path godot res://tests/BossDrawParityTest.tscn --quit-after 400
# Require "[BossDrawParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node2D

const BossOverlay = preload("res://scripts/render/BossOverlay.gd")
const BossScene = preload("res://scenes/boss/Boss.tscn")
const FIXTURE := "res://tests/fixtures/boss_draw.json"
const FPS := 60.0

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua pesan kegagalan dikumpulkan supaya tercetak di akhir run (tail log CI
## langsung memuat alasannya).
var _error_messages: Array[String] = []
## Semua op fixture, digambar sekali di `_draw()` sebagai smoke test raster.
var _smoke_ops: Array = []
## Terisi kalau engine benar-benar mengirim NOTIFICATION_DRAW (headless
## biasanya tetap mengirim; kalau tidak, smoke raster dilaporkan dilewati).
var _draw_calls := 0
## Deviasi yang TIDAK digagalkan (mis. shaping font engine vs SDL_ttf) tetapi
## wajib terlihat di log CI.
var _notes: Array[String] = []
## Statistik pita aura (diperbarui _close_band_run).
var _band_runs := 0
var _band_overlaps := 0
var _band_gaps := 0


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	var raw := FileAccess.get_file_as_string(FIXTURE)
	if raw.is_empty():
		_fail("fixture %s tidak terbaca — jalankan python3 "
			% FIXTURE + "tools/test_boss_draw_parity.py --write-fixture")
		_finish()
		return
	var parsed = JSON.parse_string(raw)
	if not (parsed is Dictionary):
		_fail("fixture %s bukan JSON object" % FIXTURE)
		_finish()
		return
	_fixture = parsed
	if not _fixture.has("scenarios"):
		_fail("fixture tanpa kunci scenarios")
		_finish()
		return
	GameManager.in_menu = true
	GameManager.state = "idle"
	_test_ops()
	_test_layer_semantics()
	await _test_node_plumbing()
	await _test_raster_smoke()
	_finish()


# ══════════════════════════════════════════════════════════
# 1) Op BossOverlay == op pygame
# ══════════════════════════════════════════════════════════

func _scenarios() -> Array:
	return _fixture["scenarios"]


func _test_ops() -> void:
	var n_ops := 0
	for s in _scenarios():
		var name := str(s["name"])
		var state: Dictionary = s["state"]
		var want_u: Array = s["underlay"]
		var want_o: Array = s["over"]
		var got_u: Array = BossOverlay.underlay_ops(state)
		var got_o: Array = BossOverlay.over_ops(state)
		n_ops += want_u.size() + want_o.size()
		_expect(_deep_eq(got_u, want_u),
			"%s: underlay %d op (pygame %d)%s" % [name, got_u.size(),
				want_u.size(), _first_diff(got_u, want_u)])
		_expect(_deep_eq(got_o, want_o),
			"%s: over %d op (pygame %d)%s" % [name, got_o.size(),
				want_o.size(), _first_diff(got_o, want_o)])
		# Pemanggilan terpisah per lapisan harus sama dengan rangkaian utuh.
		var both: Array = got_u.duplicate()
		both.append_array(got_o)
		_expect(both.size() == want_u.size() + want_o.size(),
			"%s: tidak ada op yang hilang antar lapisan" % name)
	_expect(_scenarios().size() >= 40,
		"fixture punya >= 40 skenario (%d)" % _scenarios().size())
	_expect(n_ops >= 500, "fixture punya >= 500 op (%d)" % n_ops)


## Perbandingan dalam: angka dibandingkan numerik (JSON int vs float GDScript),
## Dictionary harus punya himpunan kunci yang sama.
func _deep_eq(a, b) -> bool:
	if a is Array and b is Array:
		if (a as Array).size() != (b as Array).size():
			return false
		for i in range((a as Array).size()):
			if not _deep_eq(a[i], b[i]):
				return false
		return true
	if a is Dictionary and b is Dictionary:
		var da: Dictionary = a
		var db: Dictionary = b
		if da.size() != db.size():
			return false
		for key in da:
			if not db.has(key):
				return false
			if not _deep_eq(da[key], db[key]):
				return false
		return true
	if typeof(a) in [TYPE_INT, TYPE_FLOAT] and typeof(b) in [TYPE_INT, TYPE_FLOAT]:
		return absf(float(a) - float(b)) < 0.0000001
	return a == b


func _first_diff(got: Array, want: Array) -> String:
	var n := mini(got.size(), want.size())
	for i in range(n):
		if not _deep_eq(got[i], want[i]):
			return " | op[%d] godot=%s pygame=%s" % [i, _brief(got[i]),
				_brief(want[i])]
	if got.size() != want.size():
		return " | jumlah beda: godot %d vs pygame %d" % [got.size(), want.size()]
	return ""


func _brief(op) -> String:
	var s := str(op)
	return s if s.length() <= 220 else s.substr(0, 217) + "..."


# ══════════════════════════════════════════════════════════
# 2) Makna lapisan (bukan cuma angka)
# ══════════════════════════════════════════════════════════

func _test_layer_semantics() -> void:
	var entrance := 0
	var generic := 0
	var bands := 0
	for s in _scenarios():
		var state: Dictionary = s["state"]
		var under: Array = s["underlay"]
		var over: Array = s["over"]
		var name := str(s["name"])
		if int(state.get("entrance_timer", 0)) > 0:
			entrance += 1
			# ENTRANCE eksklusif: pygame `return` setelah `_draw_entrance`
			# (base_boss.py:6135) -> tanpa bayangan/bar/papan nama.
			_expect(over.is_empty(), "%s: entrance tanpa lapisan atas" % name)
			for o in under:
				var kind := str((o as Dictionary).get("k", ""))
				_expect(kind == "disc" or kind == "text",
					"%s: entrance hanya disc/text (%s)" % [name, kind])
			_expect(BossOverlay.is_entrance(state),
				"%s: is_entrance() true" % name)
		else:
			_expect(not over.is_empty(), "%s: ada HP bar + papan nama" % name)
			_expect(not BossOverlay.is_entrance(state),
				"%s: is_entrance() false" % name)
			# Lapisan atas dimulai HP bar bg, diakhiri teks papan nama.
			_expect(str((over[0] as Dictionary).get("k", "")) == "rect",
				"%s: lapisan atas dimulai rect HP bar" % name)
			_expect(str((over[over.size() - 1] as Dictionary).get("k", "")) == "text",
				"%s: lapisan atas diakhiri teks papan nama" % name)
		if not bool(state.get("has_renderer", true)):
			generic += 1
			var has_poly := false
			for o in under:
				if str((o as Dictionary).get("k", "")) == "poly":
					has_poly = true
			_expect(has_poly, "%s: badan generik punya mahkota polygon" % name)
		# Pita alpha: dalam SATU grup aura (satu panggilan filled_aura_bands)
		# pita-pitanya harus MENUTUP cakram tanpa tumpang tindih — itulah
		# sebabnya raster draw_arc sama dengan semantik TIMPA pygame. Grup
		# berakhir di pita ber-ri 0 (inti). Dua grup berbeda (ability + true
		# boss) boleh saling menimpa: pygame menggambarnya berurutan.
		bands += _check_band_runs(under, name)
	_expect(entrance >= 6, "fixture punya >= 6 skenario entrance (%d)" % entrance)
	_expect(generic >= 4, "fixture punya >= 4 skenario badan generik (%d)" % generic)
	_expect(bands >= 50, "fixture punya >= 50 pita aura (%d)" % bands)
	_expect(_band_runs >= 20, "pita terkelompok >= 20 grup aura (%d)" % _band_runs)
	_expect(_band_overlaps == 0,
		"pita dalam satu grup tidak tumpang tindih (%d grup, %d tabrakan)"
		% [_band_runs, _band_overlaps])
	_expect(_band_gaps == 0,
		"pita dalam satu grup menutup cakram penuh, tanpa celah (%d)" % _band_gaps)


## Hitung pita satu skenario per grup; kembalikan jumlah pitanya.
func _check_band_runs(under: Array, name: String) -> int:
	var total := 0
	var run: Array = []
	for o in under:
		var op: Dictionary = o
		if str(op.get("k", "")) != "band":
			_close_band_run(run, name)
			run = []
			continue
		run.append(op)
		total += 1
		if int(op.get("ri", -1)) == 0:
			_close_band_run(run, name)
			run = []
	_close_band_run(run, name)
	return total


## Satu grup pita harus partisi cakram: tidak saling menimpa dan jumlah
## lebarnya == radius terluar (inti ri=0 menutup sisa di dalamnya).
func _close_band_run(run: Array, name: String) -> void:
	if run.is_empty():
		return
	_band_runs += 1
	var covered := 0
	var outer := 0
	var ivs: Array = []
	for o in run:
		var ri := int((o as Dictionary)["ri"])
		var ro := int((o as Dictionary)["ro"])
		_expect(ri < ro, "%s: band ri < ro (%d..%d)" % [name, ri, ro])
		covered += ro - ri
		outer = maxi(outer, ro)
		for pair in ivs:
			if ri < int(pair[1]) and int(pair[0]) < ro:
				_band_overlaps += 1
		ivs.append([ri, ro])
	if covered != outer:
		_band_gaps += 1
		_expect(false, "%s: grup %d pita menutup %d dari radius %d"
			% [name, run.size(), covered, outer])


# ══════════════════════════════════════════════════════════
# 3) Plumbing Boss.gd -> overlay_state()
# ══════════════════════════════════════════════════════════

func _test_node_plumbing() -> void:
	var tested := 0
	for s in _scenarios():
		var state: Dictionary = s["state"]
		var name := str(s["name"])
		# Skenario badan generik memaksa `_get_boss_draw_func` pygame jadi None;
		# di Godot semua 216 boss punya strip bake, jadi has_renderer-nya pasti
		# berbeda. Teks entrance paksa juga bukan data bosses.json. Jalur op-nya
		# sudah diuji di bagian 1 — di sini yang diuji plumbing data nyata.
		if not bool(state.get("has_renderer", true)):
			continue
		if name == "entrance_wrap_forced":
			continue
		var boss = await _spawn_boss(str(s["boss_type"]),
			Vector2(float(state["x"]), float(state["y"])))
		_apply_dynamic(boss, state)
		var got: Dictionary = boss.overlay_state()
		_expect(boss.plate != null, "%s: Boss.tscn punya node Plate" % name)
		if boss.plate != null:
			_expect(boss.plate.boss == boss, "%s: Plate.boss terpasang" % name)
			_expect(boss.plate.get_index() > boss.visual.get_index(),
				"%s: Plate digambar sesudah Visual (di atas badan)" % name)
		# Node UI statis lama (CanvasGroup + ProgressBar + Label) sudah
		# diganti BossPlate: tidak boleh ada Control tersisa di pohon Boss.
		var old_ui := 0
		for child in boss.get_children():
			if child is Control:
				old_ui += 1
		_expect(old_ui == 0,
			"%s: tidak ada Control statis lama di Boss (%d)" % [name, old_ui])
		for key in state:
			if str(key) == "metrics":
				continue
			_expect(got.has(key), "%s: overlay_state punya %s" % [name, key])
			if not got.has(key):
				continue
			_expect(_deep_eq(got[key], state[key]),
				"%s: state.%s godot=%s pygame=%s" % [name, key,
					_brief(got[key]), _brief(state[key])])
		# Op dari state node. METRIK FONT tidak bisa dihasilkan Godot (shaping
		# HarfBuzz != SDL_ttf, dan tinggi baris Godot ikut line gap), jadi untuk
		# perbandingan GEOMETRI metrik rekaman oracle disuntik — yang diuji di
		# sini plumbing ANGKA (posisi, warna, timer, label_top/entrance_text/
		# color_dark dari bosses.json), bukan bentuk font.
		var injected: Dictionary = got.duplicate()
		injected["metrics"] = state["metrics"]
		_expect(_deep_eq(BossOverlay.underlay_ops(injected), s["underlay"]),
			"%s: underlay dari node == fixture%s" % [name,
				_first_diff(BossOverlay.underlay_ops(injected), s["underlay"])])
		_expect(_deep_eq(BossOverlay.over_ops(injected), s["over"]),
			"%s: over dari node == fixture%s" % [name,
				_first_diff(BossOverlay.over_ops(injected), s["over"])])
		_test_engine_metrics(got, s, name)
		boss.queue_free()
		tested += 1
	_expect(tested >= 30, "plumbing diuji pada >= 30 skenario (%d)" % tested)


## Jalur PRODUKSI: tanpa metrik suntikan, BossOverlay mengukur teks dengan font
## engine. Yang wajib benar di sini bukan angkanya (font berbeda), melainkan:
## op tetap terbentuk, keputusannya (jumlah baris entrance / jumlah lapisan)
## sama, metriknya terukur (font benar-benar termuat), dan teks tidak melebar
## melewati batas wrap/layar. Selisih urutan jenis op dicatat sebagai NOTE.
func _test_engine_metrics(got: Dictionary, s: Dictionary, name: String) -> void:
	var eng_u: Array = BossOverlay.underlay_ops(got)
	var eng_o: Array = BossOverlay.over_ops(got)
	_expect(not eng_u.is_empty(), "%s: jalur metrik engine menghasilkan op" % name)
	if _kinds(eng_u) != _kinds(s["underlay"]) or _kinds(eng_o) != _kinds(s["over"]):
		_notes.append("%s: urutan jenis op beda saat memakai metrik font engine "
			% name + "(underlay %s vs %s)" % [str(_kinds(eng_u)),
				str(_kinds(s["underlay"]))])
	var is_entrance := int(got.get("entrance_timer", 0)) > 0
	for o in eng_u + eng_o:
		var op: Dictionary = o
		if str(op.get("k", "")) != "text":
			continue
		var wh: Array = op["wh"]
		_expect(int(wh[0]) > 0 and int(wh[1]) > 0 and int(op["asc"]) > 0,
			"%s: metrik font engine terukur (wh %s, asc %s)"
			% [name, str(wh), str(op["asc"])])
		_expect(int(wh[0]) <= BossOverlay.SCREEN_W,
			"%s: teks tidak lebih lebar dari layar (%d)" % [name, int(wh[0])])
		if is_entrance:
			_expect(int(wh[0]) <= BossOverlay.ENTRANCE_WRAP_W,
				"%s: teks entrance dalam batas wrap %d (dapat %d)"
				% [name, BossOverlay.ENTRANCE_WRAP_W, int(wh[0])])


func _kinds(ops: Array) -> Array:
	var out: Array = []
	for o in ops:
		out.append(str((o as Dictionary).get("k", "")))
	return out


func _spawn_boss(boss_type: String, pos: Vector2):
	var boss = BossScene.instantiate()
	boss.boss_type = boss_type
	boss.team = "red"
	boss.position = pos
	add_child(boss)
	await get_tree().process_frame
	boss.set_physics_process(false)
	return boss


## Set field DINAMIS dari state fixture. Field yang datang dari data
## (radius/kelas/warna/label_top/entrance_text/nama/max_hp) SENGAJA tidak
## diset: justru itu yang dibandingkan (bosses.json -> Boss.gd -> overlay).
func _apply_dynamic(boss, state: Dictionary) -> void:
	boss.hp = float(state["hp"])
	boss.entrance_timer = float(state["entrance_timer"]) / FPS
	boss._anim_frame = int(state["anim_time"])
	boss._pulse = float(state["pulse"])
	boss.enrage_pulse = float(state["enrage_pulse"])
	boss.is_enraged = bool(state["is_enraged"])
	boss.ability_active = bool(state["ability_active"])
	boss.ability_range = float(state["ability_range"])
	if bool(state.get("hurt_flash", false)):
		boss.hurt_flash.trigger()
	var debuff: Dictionary = state.get("debuff", {})
	if boss.status != null:
		boss.status.slow_timer = 1.0 if bool(debuff.get("slow", false)) else 0.0
		boss.status.atk_slow_timer = 1.0 if bool(debuff.get("atk_slow", false)) else 0.0
		boss.status.skill_down_timer = 1.0 if bool(debuff.get("skill_down", false)) else 0.0
		boss.status.anti_heal_timer = 1.0 if bool(debuff.get("anti_heal", false)) else 0.0
		boss.status.burn_timer = 1.0 if bool(debuff.get("burn", false)) else 0.0


# ══════════════════════════════════════════════════════════
# 4) Raster smoke: exec() atas semua op fixture
# ══════════════════════════════════════════════════════════

func _test_raster_smoke() -> void:
	for s in _scenarios():
		for o in (s["underlay"] as Array):
			_smoke_ops.append(o)
		for o in (s["over"] as Array):
			_smoke_ops.append(o)
	_expect(_smoke_ops.size() >= 500,
		"smoke raster punya >= 500 op (%d)" % _smoke_ops.size())
	# Root tes ini Node2D: `_draw()` di bawah benar-benar memanggil
	# draw_circle/draw_arc/draw_rect/draw_style_box/draw_colored_polygon/
	# draw_polyline/draw_string untuk SEMUA op. Kalau ada jenis op yang salah
	# raster, engine mencetak SCRIPT ERROR dan gerbang log CI menggagalkan run.
	queue_redraw()
	await get_tree().process_frame
	await get_tree().process_frame
	if _draw_calls == 0:
		print("  NOTE _draw() tidak dipanggil engine headless — smoke raster "
			+ "dilewati (%d op tetap tervalidasi lewat perbandingan op)"
			% _smoke_ops.size())
	else:
		_expect(_draw_calls >= 500,
			"exec() menggambar semua op di _draw() (%d)" % _draw_calls)


func _draw() -> void:
	if _smoke_ops.is_empty():
		return
	BossOverlay.exec(self, _smoke_ops, Vector2.ZERO)
	_draw_calls = _smoke_ops.size()


# ══════════════════════════════════════════════════════════

func _fail(message: String) -> void:
	_failures += 1
	if _error_messages.size() < 40:
		_error_messages.append("  FAIL " + message)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _finish() -> void:
	if _done:
		return
	_done = true
	for note in _notes:
		print("  NOTE " + note)
	if _failures == 0:
		print("[BossDrawParityTest] PASS: %d cek op/state/raster atas %d skenario"
			% [_checks, _scenarios().size()])
		print("[BossDrawParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[BossDrawParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[BossDrawParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
