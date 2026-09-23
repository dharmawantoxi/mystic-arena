# MobileTouchParityTest — lapisan sentuh + overlay debug (`mobile/touch.py`,
# `mobile/debug.py`, `mobile/platform_utils.get_safe_area`, `main.py:401-413`).
#
# Replay fixture `godot/tests/fixtures/mobile_touch.json`
# (tools/test_godot_mobile_touch_parity.py) pada KELAS PRODUKSINYA:
#   1. `TouchGestures.gd` — 14 skenario event mentah (klik, tahan, double-tap,
#      seret, roda mouse, tombol kanan, dua jari, cancel) diputar lewat
#      `feed_event/update/cancel/collect`; yang dibandingkan URUTAN AKSI
#      (tap/long_press/double_tap/drag/scroll/fling/release), `value`
#      (held_ms / notch / kecepatan), posisi, delta, flag `consumed`,
#      kecepatan inersia akhir, `active_pos`, dan penghitung diagnostik;
#   2. `TouchGestures.dispatch_button` — pemetaan aksi -> tombol klik 1/3/4/5
#      persis `dispatch_to_game`;
#   3. `DebugOverlay.gd` — siklus mode (`toggle`), `set_mode % 4` termasuk
#      mode negatif, `enabled`, riwayat (maxlen 180 + peak + frame lambat
#      > 33 ms), tangga warna fps, teks mini, SEMUA baris panel (teks + warna)
#      dari `build_lines`, baris `[PERF]` + throttle log, dan GEOMETRI panel
#      yang dibandingkan dengan jejak `pygame.draw.rect/line/lines/circle` +
#      `surface.blit` sungguhan. Lebar teks dikirim lewat measurer palsu
#      dengan rumus `len*size*3//8` — sama seperti yang dipakai oracle — jadi
#      yang dibandingkan aritmetika tata letak, bukan raster font;
#   4. `MobileLayout.safe_area()` — (28, 10, 1280-56, 720-20) di mode sentuh,
#      penuh di luar itu; `vibrate()` -> `Input.vibrate_handheld`;
#   5. `Main.gd` — gerbang klaim press: `tap` yang dipatok UI TIDAK diteruskan
#      ke arena, `long_press` pada tombol jeda MENGALAHKAN gerbang itu (persis
#      `main.py:404-413`, cek sebelum filter `claimed`) + mengiklusi overlay
#      debug, `release` melepas patokan.
#
# Ini tes HEADLESS: tidak ada GPU, jadi yang dibandingkan adalah daftar op
# gambar yang DiHASILKAN overlay (pola `FpsCounter.gd` / `TouchHudParityTest`).
#
# godot --headless --path godot res://tests/MobileTouchParityTest.tscn --quit-after 300
# Require "[MobileTouchParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const MainScene = preload("res://scenes/main.tscn")
const FIXTURE := "res://tests/fixtures/mobile_touch.json"
const EPS := 0.0005

var _fx: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done := false
var _messages: Array[String] = []
var _main = null


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	var text := FileAccess.get_file_as_string(FIXTURE)
	if text.is_empty():
		_fail("fixture belum ada — jalankan "
			+ "tools/test_godot_mobile_touch_parity.py --write-fixture")
		_finish()
		return
	var parsed = JSON.parse_string(text)
	if not (parsed is Dictionary) or not (parsed as Dictionary).has("touch"):
		_fail("fixture rusak / tanpa seksi `touch`")
		_finish()
		return
	_fx = parsed as Dictionary
	_test_scenarios()
	_test_dispatch_button()
	_test_overlay_control()
	_test_overlay_history()
	_test_overlay_colors()
	_test_overlay_lines()
	_test_overlay_geometry()
	_test_safe_area()
	_test_main_chain()
	_finish()


# ══════════════════════════════════════════════════════════
#  1. TOUCHGESTURES — 14 skenario dari oracle
# ══════════════════════════════════════════════════════════

func _mk_event(kind: String, step: Dictionary) -> InputEvent:
	var at := Vector2(float((step["pos"] as Array)[0]),
		float((step["pos"] as Array)[1]))
	if kind == "motion":
		var mm := InputEventMouseMotion.new()
		mm.position = at
		mm.global_position = at
		mm.button_mask = MOUSE_BUTTON_MASK_LEFT
		return mm
	var mb := InputEventMouseButton.new()
	mb.position = at
	mb.global_position = at
	match kind:
		"down":
			mb.button_index = MOUSE_BUTTON_LEFT
			mb.pressed = true
		"up":
			mb.button_index = MOUSE_BUTTON_LEFT
			mb.pressed = false
		"right":
			mb.button_index = MOUSE_BUTTON_RIGHT
			mb.pressed = true
		"wheel_up":
			mb.button_index = MOUSE_BUTTON_WHEEL_UP
			mb.pressed = true
			mb.factor = Vector2(0.0, 1.0)
		"wheel_down":
			mb.button_index = MOUSE_BUTTON_WHEEL_DOWN
			mb.pressed = true
			mb.factor = Vector2(0.0, -1.0)
	return mb


func _at(x: float, y: float) -> Dictionary:
	return {"pos": [x, y]}


## Jam diputar lewat `time_ms_override` — padanan `time.perf_counter` yang
## di-monkeypatch di tool; langkah tanpa "t" TIDAK menggeser jam (sama
## persis seperti oracle).
## `g` sengaja Variant (BUKAN `Node`): akses anggota lintas kelas di atas tipe
## Node yangknown adalah error analyzer GDScript 4, padahal di sini yang
## dipanggil anggota milik TouchGestures.
func _trace_of(g: Variant, steps: Array) -> Array:
	var trace: Array = []
	g.time_ms_override = 0.0
	for entry in steps:
		var step := entry as Dictionary
		if step.has("t"):
			g.time_ms_override = float(step["t"])
		var kind := String(step["kind"])
		if kind == "update":
			g.update()
		elif kind == "cancel":
			g.cancel()
		else:
			var consumed: bool = bool(g.feed_event(_mk_event(kind, step)))
			trace.append({"step": kind, "consumed": consumed})
		for raw in g.collect():
			var a := raw as Dictionary
			var pos: Vector2 = a["pos"]
			var delta: Vector2 = a["delta"]
			trace.append({"action": String(a["kind"]),
				"pos": [pos.x, pos.y], "delta": [delta.x, delta.y],
				"value": float(a["value"]),
				"touch_id": int(a["touch_id"])})
	return trace


func _test_scenarios() -> void:
	var scenarios: Array = (_fx["touch"] as Dictionary)["scenarios"] as Array
	_expect(scenarios.size() >= 12, "fixture punya >= 12 skenario gesture")
	for sc_entry in scenarios:
		var sc := sc_entry as Dictionary
		var name := String(sc["name"])
		var g := TouchGestures.new()
		add_child(g)
		var got: Array = _trace_of(g, sc["steps"] as Array)
		var want: Array = sc["trace"] as Array
		_expect(got.size() == want.size(),
			"%s: %d langkah == oracle %d" % [name, got.size(), want.size()])
		for i in mini(got.size(), want.size()):
			var a := got[i] as Dictionary
			var b := want[i] as Dictionary
			if a.has("step"):
				_expect(String(a["step"]) == String(b["step"])
					and bool(a["consumed"]) == bool(b["consumed"]),
					"%s[%d] event %s consumed=%s (oracle %s)"
					% [name, i, String(a["step"]), str(bool(a["consumed"])),
						str(bool(b["consumed"]))])
				continue
			_expect(String(a["action"]) == String(b["action"]),
				"%s[%d] aksi %s (oracle %s)" % [name, i,
					String(a["action"]), String(b["action"])])
			_nums(a["pos"] as Array, b["pos"] as Array,
				"%s[%d] pos" % [name, i])
			_nums(a["delta"] as Array, b["delta"] as Array,
				"%s[%d] delta" % [name, i])
			_near(float(a["value"]), float(b["value"]),
				"%s[%d] value" % [name, i])
			_expect(int(a["touch_id"]) == int(b["touch_id"]),
				"%s[%d] touch_id" % [name, i])
		_near(float(g.fling_velocity), float(sc["fling_velocity"]),
			"%s: kecepatan inersia akhir" % name)
		_expect((g.points as Dictionary).size() == int(sc["open_points"]),
			"%s: %d jari menempel (oracle %d)" % [name,
				(g.points as Dictionary).size(), int(sc["open_points"])])
		var gc: Dictionary = g.counts
		var wc: Dictionary = sc["counts"] as Dictionary
		for key in wc:
			_expect(int(gc.get(key, -1)) == int(wc[key]),
				"%s: penghitung diagnostik %s" % [name, String(key)])
		var want_pos = sc["active_pos"]
		if want_pos == null:
			_expect(g.active_pos == null, "%s: active_pos bersih" % name)
		else:
			_expect(g.active_pos != null
				and absf(float((g.active_pos as Vector2).x)
					- float((want_pos as Array)[0])) <= EPS
				and absf(float((g.active_pos as Vector2).y)
					- float((want_pos as Array)[1])) <= EPS,
				"%s: active_pos = sentuhan terakhir" % name)
		remove_child(g)
		g.free()
	# konstanta mesin (fixture = nilai modul touch.py, bukan salinan tool)
	var cons: Dictionary = (_fx["touch"] as Dictionary)["constants"] as Dictionary
	var mine: Dictionary = TouchGestures.touch_constants()
	for key in cons:
		_near(float(mine.get(key, -999.0)), float(cons[key]),
			"konstanta %s" % String(key))
	# cancel() = touch.py:265-268: points + inersia + antrean dibuang,
	# `active_pos` TIDAK disentuh.
	var g2 := TouchGestures.new()
	add_child(g2)
	g2.time_ms_override = 0.0
	g2.feed_event(_mk_event("down", _at(700, 500)))
	_expect(g2.active_pos != null, "down menandai active_pos")
	g2.cancel()
	_expect((g2.points as Dictionary).is_empty()
		and absf(float(g2.fling_velocity)) <= EPS
		and (g2.collect() as Array).is_empty(),
		"cancel membuang points + inersia + antrean")
	_expect(g2.active_pos != null,
		"cancel TIDAK menghapus active_pos (paritas touch.py)")
	# enabled=false -> tidak ada satu pun aksi (padanan `if not self.enabled`)
	g2.enabled = false
	_expect(not bool(g2.feed_event(_mk_event("down", _at(10, 10))))
		and (g2.collect() as Array).is_empty(),
		"enabled=false -> mesin mati total, persis process_event()")
	remove_child(g2)
	g2.free()
	# dua jari: state titik yang dilihat `_draw_touch` pygame
	var oracle_pts: Dictionary = (_fx["debug"] as Dictionary)\
		["touch_manager_points"] as Dictionary
	var g3 := TouchGestures.new()
	add_child(g3)
	g3.time_ms_override = 0.0
	g3.feed_event(_mk_event("down", _at(200, 300)))
	g3.time_ms_override = 40.0
	g3.feed_event(_mk_event("down", _at(900, 300)))
	g3.time_ms_override = 460.0
	g3.update()
	_expect((g3.points as Dictionary).size() == int(oracle_pts["n"]),
		"oracle: %d jari aktif" % int(oracle_pts["n"]))
	for row in (oracle_pts["items"] as Array):
		var item := row as Array
		var tid := int(item[0])
		var tp: Dictionary = (g3.points as Dictionary).get(tid, {})
		_expect(not tp.is_empty(), "jari %d tercatat" % tid)
		if tp.is_empty():
			continue
		var p: Vector2 = tp["pos"]
		_nums([p.x, p.y], item[1] as Array, "jari %d posisi" % tid)
		_expect(bool(tp["moved"]) == (int(item[2]) != 0),
			"jari %d moved" % tid)
		_expect(bool(tp["long_fired"]) == (int(item[3]) != 0),
			"jari %d long_fired (450 ms, hanya yang belum digeser)" % tid)
		_near(float(tp["velocity"]), float(item[4]), "jari %d kecepatan" % tid)
		_near(float(tp["scroll_accum"]), float(item[5]),
			"jari %d akumulator scroll" % tid)
	remove_child(g3)
	g3.free()


# ══════════════════════════════════════════════════════════
#  2. JEMBATAN AKSI -> TOMBOL KLIK (dispatch_to_game)
# ══════════════════════════════════════════════════════════

func _test_dispatch_button() -> void:
	_expect(TouchGestures.dispatch_button("tap") == 1,
		"dispatch_button: tap -> klik kiri (1)")
	_expect(TouchGestures.dispatch_button("long_press") == 3,
		"dispatch_button: long_press -> klik kanan (3)")
	_expect(TouchGestures.dispatch_button("scroll", -1) == 4
		and TouchGestures.dispatch_button("scroll", 1) == 5,
		"dispatch_button: scroll -1/+1 -> tombol 4/5")
	_expect(TouchGestures.dispatch_button("scroll", 0) == 5,
		"dispatch_button: value 0 ikut cabang else (5)")
	for dead in ["drag", "fling", "release", "down", "double_tap", "?"]:
		_expect(TouchGestures.dispatch_button(String(dead)) == 0,
			"dispatch_button: %s tidak dipetakan (0)" % String(dead))
	_expect(TouchGestures.is_mapped({"kind": "tap", "value": 0.0}),
		"is_mapped: tap punya pemetaan")
	_expect(not TouchGestures.is_mapped({"kind": "double_tap",
		"value": 0.0}), "is_mapped: double_tap TIDAK dipetakan pygame")


# ══════════════════════════════════════════════════════════
#  3. OVERLAY — kontrol mode
# ══════════════════════════════════════════════════════════

func _test_overlay_control() -> void:
	var dbg: Dictionary = _fx["debug"] as Dictionary
	var ov := DebugOverlay.new()
	add_child(ov)
	ov.log_to_console = false
	var names: Array = DebugOverlay.mode_names()
	_expect(names.size() == 4 and String(names[0]) == "off"
		and String(names[1]) == "mini" and String(names[2]) == "full"
		and String(names[3]) == "graph",
		"_MODE_NAMES = off/mini/full/graph")
	var cyc: Array = dbg["toggle_cycle"] as Array
	for i in cyc.size():
		var entry := cyc[i] as Dictionary
		var m := int(ov.toggle())
		_expect(m == int(entry["mode"]),
			"toggle #%d -> mode %d (oracle %d)" % [i, m, int(entry["mode"])])
		_expect(String(names[m]) == String(entry["name"]),
			"toggle #%d -> nama %s" % [i, String(names[m])])
	var wrap: Array = dbg["set_mode_wrap"] as Array
	for entry in wrap:
		var want := entry as Dictionary
		ov.set_mode(int(want["in"]))
		_expect(int(ov.mode) == int(want["mode"]),
			"set_mode(%d) -> %d (oracle %d)" % [int(want["in"]),
				int(ov.mode), int(want["mode"])])
		_expect(bool(ov.enabled()) == bool(want["enabled"]),
			"set_mode(%d): enabled = %s" % [int(want["in"]),
				str(bool(want["enabled"]))])
	_expect(DebugOverlay.next_mode(3) == 0, "next_mode: graph -> off")
	_expect(DebugOverlay.wrap_mode(-1) == 3,
		"wrap_mode(-1) = 3 (posmod = `%` Python)")
	_expect(int(DebugOverlay.HISTORY_MAX) == int(dbg["history_max"]),
		"maxlen riwayat 180")
	_near(float(DebugOverlay.JEDA_SEGAR_MS), float(dbg["throttle_ms"]),
		"seegar teks panel = 250 ms")
	_near(float(DebugOverlay.LOG_INTERVAL_SEC), float(dbg["log_interval"]),
		"jeda baris [PERF] = 5 dtk")
	remove_child(ov)
	ov.free()


# ══════════════════════════════════════════════════════════
#  4. OVERLAY — riwayat, peak, frame lambat, throttle log
# ══════════════════════════════════════════════════════════

func _test_overlay_history() -> void:
	var dbg: Dictionary = _fx["debug"] as Dictionary
	var rep: Dictionary = dbg["replay"] as Dictionary
	var hist: Dictionary = dbg["history"] as Dictionary
	var ov := DebugOverlay.new()
	add_child(ov)
	ov.log_to_console = false
	for row in (rep["feed"] as Array):
		var f := row as Array
		for _i in int(f[2]):
			ov.update(float(f[0]), float(f[1]))
	_expect(ov.fps_history.size() == int(hist["fps_len"]),
		"riwayat fps = %d sebelum pemangkasan" % int(hist["fps_len"]))
	_expect(ov.frame_ms_history.size() == int(hist["ms_len"]),
		"riwayat frame-ms = %d" % int(hist["ms_len"]))
	_expect(int(ov._frames) == int(hist["frames"]),
		"penghitung frame = %d" % int(hist["frames"]))
	var after: Dictionary = dbg["history_after_slow"] as Dictionary
	var slow: Array = rep["slow_feed"] as Array
	for _i in 3:
		ov.update(float(slow[0]), float(slow[1]))
	_near(float(ov._peak_ms), float(after["peak"]),
		"peak mengikuti frame lebih lambat")
	_expect(int(ov._slow_frames) == int(after["slow"]),
		"frame > 33 ms dihitung: %d" % int(after["slow"]))
	_expect(ov.frame_ms_history.size() == int(after["ms_len"]),
		"riwayat dipangkas ke maxlen 180 (%d update masuk)"
		% int(after["frames"]))
	_expect(int(ov._frames) == int(after["frames"]),
		"`frames` terus bertambah walau riwayat dipangkas")
	_near(DebugOverlay.avg(ov.frame_ms_history), float(after["ms_avg"]),
		"rata-rata frame-ms atas riwayat yang dipangkas")
	_near(DebugOverlay.avg(ov.fps_history), float(after["fps_avg"]),
		"rata-rata fps")
	_expect(DebugOverlay.avg([]) == 0.0, "rata-rata kosong = 0,0 (`or 0`)")
	# ambang lambat: `frame_ms > 33` strict, bukan `>=`
	_expect(DebugOverlay.slow_frame(33.0001)
		and not DebugOverlay.slow_frame(33.0),
		"ambang frame lambat = > 33, BUKAN >= 33")
	# throttle log: interval 0 -> stamp log di-update tiap panggilan;
	# interval raksasa -> tidak pernah (satu-satunya cara melihat throttle
	# tanpa menyadap stdout di headless).
	ov.log_to_console = true
	ov.log_interval = 0.0
	ov._last_log_ms = 0.0
	ov.update(float(slow[0]), float(slow[1]))
	var stamp := float(ov._last_log_ms)
	_expect(stamp > 0.0, "log_interval 0 -> stamp log di-update")
	ov.log_interval = 1000000000.0
	ov.update(float(slow[0]), float(slow[1]))
	_expect(float(ov._last_log_ms) == stamp,
		"log_interval raksasa -> tidak ada log baru (oracle sama)")
	ov.log_to_console = false
	remove_child(ov)
	ov.free()


# ══════════════════════════════════════════════════════════
#  5. OVERLAY — tangga warna fps
# ══════════════════════════════════════════════════════════

func _test_overlay_colors() -> void:
	var table: Array = (_fx["debug"] as Dictionary)["color_for_fps"] as Array
	_expect(table.size() == 6, "oracle mengirim 6 titik warna fps")
	for row in table:
		var e := row as Array
		var got: Array = DebugOverlay.color_for_fps(float(e[0]))
		_expect(_ints(got) == _ints(e[1] as Array),
			"warna fps %.1f = %s (oracle %s)" % [float(e[0]), str(got),
				str(e[1])])


# ══════════════════════════════════════════════════════════
#  6. OVERLAY — baris teks panel + baris [PERF]
# ══════════════════════════════════════════════════════════

func _test_overlay_lines() -> void:
	var dbg: Dictionary = _fx["debug"] as Dictionary
	var keep: Array = dbg["godot_lines"] as Array
	var rep: Dictionary = dbg["replay"] as Dictionary
	var state: Dictionary = (rep["lines_state"] as Dictionary).duplicate(true)
	var audio_text := ""
	for entry in keep:
		if String((entry as Dictionary)["tag"]) == "audio":
			audio_text = String((entry as Dictionary)["text"])
	state["audio"] = audio_text
	state["memory"] = "0MB"
	state["build"] = "BUILD ?"
	state["device"] = DebugOverlay.device_info()
	state["extra"] = {}
	var got: Array = DebugOverlay.build_lines(state)
	_expect(got.size() == keep.size(),
		"build_lines menghasilkan %d baris; oracle menyimpan %d baris yang "
		% [got.size(), keep.size()] + "dipunyahi Godot")
	for i in mini(got.size(), keep.size()):
		var line: Array = got[i]
		var want := keep[i] as Dictionary
		var text := String(line[0])
		if bool(want.get("format", false)):
			_check_format(String(want["tag"]), text)
		else:
			_expect(text == String(want["text"]),
				"baris %s identik dengan pygame (got %s)"
				% [String(want["tag"]), _q(text)])
		_expect(_same_color(line[1] as Array, want["color"] as Array),
			"baris %s warna %s (oracle %s)" % [String(want["tag"]),
				str(line[1]), str(want["color"])])
	# baris `extra` (debug.py:358 `"k: v"` + warna (200,190,140))
	var extra: Array = dbg["extra_line"] as Array
	_expect(extra.size() == 1, "oracle mengirim 1 baris extra")
	if extra.size() == 1:
		state["extra"] = {"sim": "4x/frame  mentok 0"}
		var with_extra: Array = DebugOverlay.build_lines(state)
		var last: Array = with_extra[with_extra.size() - 1]
		_expect(String(last[0]) == String((extra[0] as Array)[0]),
			"baris extra = %s (oracle %s)" % [_q(String(last[0])),
				_q(String((extra[0] as Array)[0]))])
		_expect(_ints(last[1] as Array) == _ints((extra[0] as Array)[1]
			as Array), "baris extra warna (200,190,140)")
	# format pembentuk baris, dipanggil langsung (anti salin-tempel)
	_expect(DebugOverlay.entity_counts(3, 1, 2, 4)
		== String(dbg["entity_counts"]),
		"entity_counts = m3/t1/h2/p4 dari angka oracle")
	_expect(DebugOverlay.mini_text(float(rep["fps"]), float(rep["ms_avg"]))
		== String(rep["mini_text"]),
		"teks mini = fps SEKETIKA + rata-rata ms (got %s)"
		% _q(DebugOverlay.mini_text(float(rep["fps"]),
			float(rep["ms_avg"]))))
	var log: Dictionary = dbg["perf_log"] as Dictionary
	var got_log := DebugOverlay.perf_log_line(float(log["fps"]),
		float(log["frame_avg"]), 0.0, 0.0, String(log["quality"]),
		String(log["entities"]), String(log["memory"]))
	_expect(got_log == String(log["text"]),
		"baris [PERF] identik dengan pygame:\n  got  %s\n  want %s"
		% [got_log, String(log["text"])])


func _check_format(tag: String, text: String) -> void:
	match tag:
		"memory":
			_expect(text == "mem n/a" or (text.begins_with("mem ")
				and text.ends_with("MB")),
				"format baris memori: %s" % _q(text))
		"build":
			_expect(text.begins_with("BUILD "),
				"format baris build: %s" % _q(text))
		"device":
			_expect(text.contains(" | Android ") and text.contains(" (API ")
				and text.contains(" | Godot "),
				"format baris perangkat: %s" % _q(text))
		_:
			_fail("tag format tak dikenal: %s" % tag)


# ══════════════════════════════════════════════════════════
#  7. OVERLAY — GEOMETRI vs jejak menggambar pygame
# ══════════════════════════════════════════════════════════

## Rumus ukuran font yang dipakai oracle (`fake_font_metrics` di tool):
## `len(text) * size * 3 // 8`. Font Godot/pygame memang tidak identik —
## yang dikunci di sini ARITMETIKA TATA LETAK-nya.
func _measure(text: String, size: int) -> Vector2:
	return Vector2(floor(float(int(text.length()) * size * 3) / 8.0),
		float(size))


func _ops(state: Dictionary, lines: Array) -> Array:
	return DebugOverlay.build_ops(state, lines, Callable(self, "_measure"))


func _pick(ops: Array, kind: String) -> Array:
	var out: Array = []
	for entry in ops:
		if String((entry as Dictionary)["op"]) == kind:
			out.append(entry)
	return out


func _rect_of(op: Dictionary) -> Array:
	var r: Rect2 = op["rect"]
	return [r.position.x, r.position.y, r.size.x, r.size.y]


func _test_overlay_geometry() -> void:
	var dbg: Dictionary = _fx["debug"] as Dictionary
	var geo: Dictionary = dbg["geometry"] as Dictionary
	var rep: Dictionary = dbg["replay"] as Dictionary
	var safe_arr: Array = rep["safe"] as Array
	var safe := Rect2(Vector2(float(safe_arr[0]), float(safe_arr[1])),
		Vector2(float(safe_arr[2]), float(safe_arr[3])))
	var state: Dictionary = (rep["lines_state"] as Dictionary).duplicate(true)
	state["safe"] = safe
	state["points"] = []
	state["extra"] = {}
	state["audio"] = _line_text(dbg, "audio")
	state["memory"] = "0MB"
	state["build"] = "BUILD ?"
	state["device"] = DebugOverlay.device_info()
	state["frame_ms_history"] = (rep["graph_history"] as Array)
	var lines: Array = DebugOverlay.build_lines(state)

	# ── MINI: panel alpha + satu teks, dibandingkan dengan blit sungguhan ──
	state["mode"] = DebugOverlay.MODE_MINI
	var mini_ops: Array = _ops(state, lines)
	var mini_geo: Dictionary = geo["mini"] as Dictionary
	var panels: Array = _pick(mini_ops, "panel_alpha")
	_expect(panels.size() == 1, "mini: satu panel alpha")
	if panels.size() == 1:
		_nums(_rect_of(panels[0] as Dictionary),
			(mini_geo["panels"] as Array)[0] as Array,
			"mini: rect panel = blit sungguhan pygame")
	var texts: Array = _pick(mini_ops, "text")
	_expect(texts.size() == 1, "mini: satu teks")
	var blits: Array = mini_geo["blits"] as Array
	_expect(blits.size() == 2, "oracle: mini 2 blit (panel + teks)")
	if texts.size() == 1 and blits.size() == 2:
		var t := texts[0] as Dictionary
		_expect(String(t["text"]) == String(rep["mini_text"]),
			"mini: teks \"%s\"" % String(rep["mini_text"]))
		_expect(int(t["size"]) == int((rep["font_sizes"] as Dictionary)
			["mini"]), "mini: font 20")
		var tp: Array = blits[1][0] as Array
		_expect(int(t["x"]) == int(tp[0]) and int(t["y"]) == int(tp[1]),
			"mini: posisi teks = blit pygame (%d,%d) vs (%d,%d)"
			% [int(t["x"]), int(t["y"]), int(tp[0]), int(tp[1])])
		_expect(int(t["w"]) == int(blits[1][1]),
			"mini: lebar permukaan teks = %d" % int(blits[1][1]))

	# ── LENGKAP: buffer opaque + teks 19 px/baris ──
	state["mode"] = DebugOverlay.MODE_FULL
	var full_ops: Array = _ops(state, lines)
	var full_geo: Dictionary = geo["full"] as Dictionary
	var fpanels: Array = _pick(full_ops, "panel_opaque")
	_expect(fpanels.size() == 1, "full: satu panel OPAQUE (bukan alpha)")
	if fpanels.size() == 1:
		_nums(_rect_of(fpanels[0] as Dictionary),
			(full_geo["panels"] as Array)[0] as Array,
			"full: rect panel = blit buffer sungguhan")
		var pr: Rect2 = (fpanels[0] as Dictionary)["rect"]
		_expect(absf(pr.size.x - (float(_widest(lines))
			+ float(DebugOverlay.FULL_PAD_W))) <= EPS
			and absf(pr.size.y - (float(lines.size())
				* float(DebugOverlay.FULL_LINE_PITCH)
				+ float(DebugOverlay.FULL_PAD_H))) <= EPS,
			"full: lebar = teks terlebar + 18, tinggi = baris * 19 + 12")
	var ftexts: Array = _pick(full_ops, "text")
	_expect(ftexts.size() == lines.size(),
		"full: %d baris teks digambar" % ftexts.size())
	if not ftexts.is_empty():
		var want_at: Array = rep["full_text_at"] as Array
		var first := ftexts[0] as Dictionary
		var last := ftexts[ftexts.size() - 1] as Dictionary
		_expect(int(first["x"]) == int(want_at[0])
			and int(first["y"]) == int(want_at[1]),
			"full: teks pertama di (panel+8, panel+6) = (%d,%d)"
			% [int(want_at[0]), int(want_at[1])])
		_expect(int(last["y"]) - int(first["y"])
			== (ftexts.size() - 1) * int(rep["full_line_pitch"]),
			"full: jarak baris 19 px")
		_expect(int(first["size"]) == int((rep["font_sizes"] as Dictionary)
			["full"]), "full: font 16")

	# ── GRAFIK = LENGKAP + grafik (persis `draw()` pygame) ──
	state["mode"] = DebugOverlay.MODE_GRAPH
	var graph_ops: Array = _ops(state, lines)
	var graph_geo: Dictionary = geo["graph"] as Dictionary
	_expect(_pick(graph_ops, "panel_opaque").size() == 1
		and _pick(graph_ops, "panel_alpha").size() == 1,
		"graph = panel teks LENGKAP + panel grafik (bukan mode terpisah)")
	var gpanels: Array = _pick(graph_ops, "panel_alpha")
	_expect(gpanels.size() == 1, "graph: satu panel alpha 240x70")
	if gpanels.size() == 1:
		_nums(_rect_of(gpanels[0] as Dictionary),
			(graph_geo["panels"] as Array)[0] as Array,
			"graph: rect panel = blit sungguhan")
	var guides: Array = _pick(graph_ops, "line")
	var want_guides: Array = graph_geo["guides"] as Array
	_expect(guides.size() == want_guides.size(),
		"graph: %d garis panduan (16,7 + 33,3 ms)" % want_guides.size())
	for i in mini(guides.size(), want_guides.size()):
		var gop := guides[i] as Dictionary
		var wgd := want_guides[i] as Dictionary
		_nums([float(gop["x1"]), float(gop["y1"]), float(gop["x2"]),
			float(gop["y2"])],
			[float((wgd["a"] as Array)[0]), float((wgd["a"] as Array)[1]),
				float((wgd["b"] as Array)[0]), float((wgd["b"] as Array)[1])],
			"graph: garis panduan %d" % i)
		_expect(_ints(gop["color"] as Array) == _ints(wgd["color"] as Array),
			"graph: warna panduan %d = %s" % [i, str(wgd["color"])])
		_near(float(gop.get("width", 1.0)), float(wgd.get("width", 1)),
			"graph: tebal panduan %d" % i)
	var polys: Array = _pick(graph_ops, "poly")
	var poly: Dictionary = graph_geo["poly"] as Dictionary
	_expect(polys.size() == 1, "graph: satu poly-line data")
	if polys.size() == 1:
		var p := polys[0] as Dictionary
		var pts: Array = p["points"] as Array
		_expect(pts.size() == int(poly["count"]),
			"graph: %d titik data (oracle %d)" % [pts.size(),
				int(poly["count"])])
		var head: Array = poly["head"] as Array
		for i in mini(pts.size(), head.size()):
			var pt: Vector2 = pts[i]
			_nums([pt.x, pt.y], head[i] as Array, "graph: titik #%d" % i)
		_expect(_ints(p["color"] as Array) == _ints(poly["color"] as Array),
			"graph: warna poly-line (150,220,255)")
		_near(float(p.get("width", 1.0)), 1.0, "graph: tebal poly-line 1")
	# skala grafik TETAP 50 ms (bukan rata-rata riwayat!) -> titik 26,25 ms
	# jatuh di y = at.y + h - int(26.25/50*h). Ini yang membedakan port yang
	# menyalin `_draw_graph` dari yang mengarang skala sendiri.
	if gpanels.size() == 1:
		var grect: Rect2 = (gpanels[0] as Dictionary)["rect"]
		var first_pt: Vector2 = (polys[0] as Dictionary)["points"][0]
		var want_y := float(DebugOverlay.graph_y(grect.position.y,
			grect.size.y, 26.25))
		_near(first_pt.y, want_y,
			"graph: rumus y titik data = at.y + h - int(min(ms,50)/50*h)")
		_near(float(DebugOverlay.GRAPH_MS_MAX), 50.0,
			"graph: skala tetap 50 ms")

	# ── lingkaran jari ──
	var vpts: Array = []
	for row in (rep["touch_points"] as Array):
		vpts.append(Vector2(float((row as Array)[0]), float((row as Array)[1])))
	state["points"] = vpts
	var dot_ops: Array = _ops(state, lines)
	var dots: Array = _pick(dot_ops, "circle")
	var want_dots: Array = (geo["touch"] as Dictionary)["dots"] as Array
	_expect(dots.size() == want_dots.size(),
		"titik jari: %d lingkaran (cincin + pusat per jari)" % dots.size())
	for i in mini(dots.size(), want_dots.size()):
		var d := dots[i] as Dictionary
		var wd := want_dots[i] as Dictionary
		var cen: Vector2 = d["at"]
		_nums([cen.x, cen.y], wd["center"] as Array, "titik #%d pusat" % i)
		_near(float(d["r"]), float(wd["radius"]), "titik #%d radius" % i)
		_expect(_ints(d["color"] as Array) == _ints(wd["color"] as Array),
			"titik #%d warna %s (oracle %s)" % [i, str(d["color"]),
				str(wd["color"])])
		if int(wd["width"]) > 0:
			_expect(not bool(d["filled"])
				and absf(float(d["width"]) - float(wd["width"])) <= EPS,
				"titik #%d = cincin outline tebal %d" % [i, int(wd["width"])])
		else:
			_expect(bool(d["filled"]), "titik #%d = titik terisi" % i)

	# titik jari dibaca DARI mesin gesture, bukan disuntik (paritas
	# `_draw_touch(surface, touch)` yang membaca touch.points)
	var g := TouchGestures.new()
	add_child(g)
	g.time_ms_override = 0.0
	g.feed_event(_mk_event("down", _at(123, 456)))
	var ov := DebugOverlay.new()
	add_child(ov)
	ov.log_to_console = false
	ov.bind_gestures(g)
	var snap: Dictionary = ov.state_snapshot()
	_expect((snap["points"] as Array).size() == 1,
		"overlay mengambil titik jari aktif dari TouchGestures")
	var live_ops: Array = DebugOverlay.build_ops(snap, [],
		Callable(self, "_measure"))
	_expect(_pick(live_ops, "circle").size() == 2,
		"satu jari aktif -> cincin + titik pusat digambar")
	ov.set_mode(DebugOverlay.MODE_OFF)
	_expect(DebugOverlay.build_ops(ov.state_snapshot(), [],
		Callable(self, "_measure")).is_empty(),
		"mode OFF = NOL op (tidak menggambar apa pun)")
	# 2 jari -> 4 lingkaran, URUTAN sama dengan dict pygame (insertion order)
	g.time_ms_override = 5.0
	g.feed_event(_mk_event("down", _at(888, 111)))
	ov.set_mode(DebugOverlay.MODE_FULL)
	var two_ops: Array = DebugOverlay.build_ops(ov.state_snapshot(), [],
		Callable(self, "_measure"))
	_expect(_pick(two_ops, "circle").size() == 4,
		"dua jari -> 4 lingkaran (cincin+pusat tiap jari)")
	var order: Array = []
	for c in _pick(two_ops, "circle"):
		order.append((c as Dictionary)["at"])
	_expect(absf((order[0] as Vector2).x - 123.0) <= EPS
		and absf((order[2] as Vector2).x - 888.0) <= EPS,
		"urutan titik = urutan jari menekan (paritas dict Python)")
	remove_child(ov)
	ov.free()
	remove_child(g)
	g.free()


func _widest(lines: Array) -> float:
	var w := 0.0
	for entry in lines:
		var text := String((entry as Array)[0])
		w = maxf(w, _measure(text, int(DebugOverlay.FULL_FONT)).x)
	return w


func _line_text(dbg: Dictionary, tag: String) -> String:
	for entry in (dbg["godot_lines"] as Array):
		var e := entry as Dictionary
		if String(e["tag"]) == tag:
			return String(e.get("text", ""))
	return ""


# ══════════════════════════════════════════════════════════
#  8. SAFE AREA + GETAR
# ══════════════════════════════════════════════════════════

func _test_safe_area() -> void:
	var want: Array = (_fx["debug"] as Dictionary)["safe_area"] as Array
	var margin := float(MobileLayout.SAFE_MARGIN_LOGICAL)
	var built := Rect2(Vector2(margin, float(MobileLayout.SAFE_TOP)),
		Vector2(MobileLayout.DESIGN_SIZE.x - margin * 2.0,
			MobileLayout.DESIGN_SIZE.y - float(MobileLayout.SAFE_TOP)
			- float(MobileLayout.SAFE_BOTTOM)))
	_nums([built.position.x, built.position.y, built.size.x, built.size.y],
		want, "safe area sentuh = rumus pygame (28,10,W-56,H-20)")
	if not AppShell.touch_mode():
		var full := MobileLayout.safe_area()
		_expect(full.position == Vector2.ZERO
			and full.size == MobileLayout.DESIGN_SIZE,
			"di luar mode sentuh: safe area = 1280x720 penuh")
	_expect(not MobileLayout.vibrate(30),
		"vibrate() no-op di luar mode sentuh (paritas `if not IS_ANDROID`)")


# ══════════════════════════════════════════════════════════
#  9. MAIN — gerbang klaim press + rantai tahan-jeda
# ══════════════════════════════════════════════════════════

func _test_main_chain() -> void:
	_main = MainScene.instantiate()
	add_child(_main)
	_main.set_process(false)
	GameManager.in_menu = false
	GameManager.state = "playing"
	GameManager.set_paused(false)
	var hud = _main.find_child("HUD", true, false)
	var touch = get_tree().get_first_node_in_group("touch_hud")
	_expect(_main.has_method("toggle_debug_overlay")
		and _main.has_method("debug_mode"),
		"Main punya toggle_debug_overlay()/debug_mode()")
	_expect(int(_main.debug_mode()) == 0, "overlay mulai dari mode OFF")
	var claim: Dictionary = _main._press_claim
	# (a) tap yang DIPUNYAI Control (press tidak pernah lolos ke arena)
	claim[0] = true
	_expect(not bool(_main._dispatch_gesture({"kind": "tap",
		"pos": Vector2(640, 360), "delta": Vector2.ZERO, "value": 100.0,
		"touch_id": 0})), "tap saat press diklaim UI -> tidak dikonsumsi")
	# (b) lepas patokan -> tap yang sama DIPUNYAI arena
	claim.erase(0)
	_expect(bool(_main._dispatch_gesture({"kind": "tap",
		"pos": Vector2(640, 360), "delta": Vector2.ZERO, "value": 100.0,
		"touch_id": 0})), "tap tanpa klaim -> diteruskan ke arena")
	# (c) kind tanpa pemetaan -> selalu false (deviasi scroll/fling dicatat)
	for kind in ["drag", "scroll", "fling", "double_tap", "down"]:
		_expect(not bool(_main._dispatch_gesture({"kind": kind,
			"pos": Vector2(640, 360), "delta": Vector2(0, 42), "value": -1,
			"touch_id": 0})), "%s tidak diteruskan ke arena" % kind)
	# (d) release SELALU melepas patokan, dan mengembalikan false
	claim[3] = true
	_expect(not bool(_main._dispatch_gesture({"kind": "release",
		"pos": Vector2(1, 2), "delta": Vector2.ZERO, "value": 0.0,
		"touch_id": 3})) and not claim.has(3),
		"release melepas patokan klaim touch_id 3")
	# (e) tahan tombol jeda = siklus overlay + getar, MENANG atas gerbang
	#     klaim (main.py:404-413: dicek SEBELUM filter `claimed`)
	var hit := _make_pause_hittable(touch)
	_expect(hit.x > -1.0, "tombol jeda sentuh bisa disiapkan di headless")
	if hit.x > -1.0:
		claim[0] = true
		_expect(bool(_main._dispatch_gesture({"kind": "long_press",
			"pos": hit, "delta": Vector2.ZERO, "value": 0.0,
			"touch_id": 0})), "long_press pada tombol jeda dikonsumsi")
		_expect(int(_main.debug_mode()) == 1,
			"tahan jeda -> mode mini (dapat %d)" % int(_main.debug_mode()))
		_expect(bool(_main._dispatch_gesture({"kind": "long_press",
			"pos": hit, "delta": Vector2.ZERO, "value": 0.0,
			"touch_id": 0})), "tahan jeda kedua dikonsumsi juga")
		_expect(int(_main.debug_mode()) == 2, "tahan jeda kedua -> full")
		# satu-satunya tap yang MATI saat diklaim adalah tap BIASA
		claim[0] = true
		_expect(bool(_main._dispatch_gesture({"kind": "long_press",
			"pos": hit + Vector2(0, 4), "delta": Vector2.ZERO, "value": 0.0,
			"touch_id": 0})) and int(_main.debug_mode()) == 3,
			"tahan di tepi tombol -> graph (ambang 24 px inflate masih kena)")
	# (f) long_press DI LUAR tombol jeda + press diklaim -> dilewati
	claim[0] = true
	_expect(not bool(_main._dispatch_gesture({"kind": "long_press",
		"pos": Vector2(1200, 700), "delta": Vector2.ZERO, "value": 0.0,
		"touch_id": 0})),
		"long_press di area UI yang mengklaim press -> dilewati")
	claim.erase(0)
	# (g) HUD meneruskan siklus ke MESIN YANG SAMA (bukan overlay sendiri)
	if hud != null:
		var before := int(_main.debug_mode())
		var after := int(hud.call("toggle_debug_overlay"))
		_expect(after == (before + 1) % 4,
			"HUD.toggle_debug_overlay() = DebugOverlay.toggle() %4")
		_expect(int(_main.debug_mode()) == after,
			"HUD dan Main memakai SATU mesin overlay")
		_expect(int(hud.call("debug_mode")) == after,
			"HUD.debug_mode() membaca mode dari mesin yang sama")
	# (h) rail SidePanel: titik jauh selalu false; pusat tombol true saat
	#     rail aktif (getar 15 ms + rantai tahan-jeda bergantung pada ini)
	var sp = _main.find_child("SidePanel", true, false)
	if sp != null:
		var btn = sp.get("_pause_button")
		var active := bool(sp.call("rail_active"))
		_expect(active == MobileLayout.has_side_panel(),
			"rail_active() = MobileLayout.has_side_panel()")
		_expect(not bool(sp.call("rail_pause_contains",
			Vector2(-9000, -9000))), "rail: titik jauh = selalu false")
		if btn != null and active and (btn as Control).visible:
			var center: Vector2 = (btn as Control).get_global_rect() \
				.get_center()
			_expect(bool(sp.call("rail_pause_contains", center)),
				"rail: pusat tombol jeda terdeteksi")
			_expect(bool(_main._pause_button_holds(center)),
				"_pause_button_holds membaca rail saat panel aktif")
	# (i) input mentah: press kiri DIPATOK, gerakan/tombol lain tidak
	claim.clear()
	var press := _mk_event("down", _at(10, 10))
	_main._input(press)
	_expect(claim.has(0), "_input mematok klaim pada press tombol kiri")
	var move := InputEventMouseMotion.new()
	move.global_position = Vector2(11, 11)
	_main._input(move)
	_expect(claim.has(0), "gerakan mouse tidak menghapus patokan")
	var right := _mk_event("right", _at(12, 12))
	_main._input(right)
	_expect(claim.has(0), "kanan tidak mengubah patokan kiri")
	_main._unhandled_input(_mk_event("up", _at(10, 10)))
	_expect(not claim.has(0),
		"press yang lolos ke arena -> patokan dilepas (_unhandled_input)")
	# (j) overlay debug benar-benar node hidup di di atas UI
	var ov = _main.find_child("DebugOverlay", true, false)
	_expect(ov != null, "Main membangun DebugOverlay saat _ready")
	if ov != null:
		_expect(int(ov.get("mode")) == int(_main.debug_mode()),
			"debug_mode() = mode node overlay yang sama")
		_expect(int(ov.get("process_mode"))
			== int(Node.PROCESS_MODE_ALWAYS),
			"overlay tetap hidup saat game dijeda (tahan-jeda = menjeda!)")
	var cur := int(_main.debug_mode())
	_expect(int(_main.toggle_debug_overlay()) == (cur + 1) % 4,
		"Main.toggle_debug_overlay() = DebugOverlay.toggle() %4")
	if ov != null:
		_expect(int(ov.get("mode")) == (cur + 1) % 4,
			"mode node ikut bergeser (satu-satunya sumber kebenaran)")
	GameManager.in_menu = true
	GameManager.state = "idle"


## Tombol jeda HUD hanya tampil di mode sentuh; headless tidak pernah masuk
## sana, jadi visibilitas + rect-nya diset langsung supaya rantai
## `_pause_button_holds` bisa diuji apa adanya.
func _make_pause_hittable(touch: Variant) -> Vector2:
	if touch == null:
		return Vector2(-1, -1)
	touch.set_process(false)
	touch.visible = true
	var dict = touch.get("_buttons")
	if dict == null or not (dict is Dictionary):
		return Vector2(-1, -1)
	var d: Dictionary = dict as Dictionary
	if not d.has("pause"):
		return Vector2(-1, -1)
	var b: Dictionary = d["pause"] as Dictionary
	b["visible"] = true
	b["hit"] = Rect2(64, 64, 58, 58)
	return Vector2(80, 80)


# ══════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════

func _ints(arr: Array) -> Array:
	var out: Array = []
	for v in arr:
		out.append(int(v))
	return out


func _same_color(a: Array, b: Array) -> bool:
	# pygame mengirim 3 komponen untuk teks, Godot selalu 4 (alpha 255)
	if a.size() < b.size():
		return false
	for i in b.size():
		if int(a[i]) != int(b[i]):
			return false
	return true


func _q(s: String) -> String:
	return "\"" + s.replace("\"", "\\\"") + "\""


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _near(a: float, b: float, message: String) -> void:
	_checks += 1
	if absf(a - b) > EPS:
		_fail("%s: %.6f != %.6f" % [message, a, b])


func _nums(a: Array, b: Array, message: String) -> void:
	_checks += 1
	if a.size() != b.size():
		_fail("%s: panjang %d != %d" % [message, a.size(), b.size()])
		return
	for i in a.size():
		if absf(float(a[i]) - float(b[i])) > EPS:
			_fail("%s[%d]: %.4f != %.4f" % [message, i, float(a[i]),
				float(b[i])])
			return


func _fail(message: String) -> void:
	_failures += 1
	_messages.append("  FAIL " + message)


func _finish() -> void:
	if _done:
		return
	_done = true
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _main != null and is_instance_valid(_main):
		remove_child(_main)
		_main.free()
	if _failures == 0:
		print("[MobileTouchParityTest] PASS: %d cek gesture/overlay/safe-area"
			% _checks)
		print("[MobileTouchParityTest] PASS")
	else:
		for msg in _messages:
			print(msg)
		push_error("[MobileTouchParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[MobileTouchParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
