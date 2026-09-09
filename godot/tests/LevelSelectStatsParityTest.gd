# FASE 20 — BEST SCORE/BEST TIME per level di kartu LEVEL SELECT vs oracle
# jalur DRAW pygame ASLI (seksi fixture `level_select_stats`).
# python tools/test_godot_match_parity.py   (freshness)
# godot --headless --path godot res://tests/LevelSelectStatsParityTest.tscn --quit-after 300
#
# Oracle pygame: Menu._draw_level_card (kartu 280x290, level 3) headless
# dengan font proxy perekam + SaveManager ASLI (get_level_stats/format_time).
# Yang direplay di sini lewat JALUR PRODUKSI Godot (MainMenu._level_card +
# SaveManager — TIDAK ADA duplikasi rumus di harness):
#
#   * KARTU   : tiap kasus fixture diputar ulang dengan membangun ulang
#               level select produksi (menu._show(LEVEL_SELECT)) lalu
#               membaca meta `parity` pada label nilai kartu level 3 —
#               string skor/waktu/attempt/win-rate + warna RGB slot.
#               Kartu TERKUNCI tidak boleh punya blok stat; kartu tanpa
#               attempt menampilkan baris kosong (beda bahasa terkunci).
#   * FORMAT  : baterai format_time (SaveManager produksi), baterai format
#               skor (raw "9,999"/"12.3K") + aturan truncasi [:8] pada
#               LEBAR PIKSEL PYGAME dari fixture (fungsi murni), dan
#               baterai win-rate int() + band warna.
#
# Beda disengaja yang dikunci eksplisit: label stat Godot berbahasa
# Indonesia (SKOR TERBAIK/…), "No stats yet" -> "Belum ada statistik",
# ukuran/posisi piksel kartu (Godot kartu 380px, pygame 280px) — nilai
# data string/warna/band wajib identik. Batas tepat truncasi tergantung
# metrik font (ambang 120px pygame di-pin sebagai konstanta produksi).
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainMenuScript = preload("res://scenes/ui/MainMenu.gd")

var _fx: Dictionary = {}
var _failures := 0
var _checks := 0
var _save_before: Dictionary = {}
var _save_file_existed := false
var _save_file_before := ""
var _menu = null


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _expect(cond: bool, tag: String) -> void:
	_checks += 1
	if not cond:
		_failures += 1
		printerr("[LevelSelectStatsParityTest] FAIL: ", tag)


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	_save_file_existed = FileAccess.file_exists(SaveManager.SAVE_PATH)
	if _save_file_existed:
		_save_file_before = FileAccess.get_file_as_string(
			SaveManager.SAVE_PATH)
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("level_select_stats"):
		_expect(false, "fixture level_select_stats belum ada — jalankan "
			+ "tools/test_godot_match_parity.py --write-fixture")
		_finish()
		return
	_fx = fixture["level_select_stats"]

	# MainMenu produksi tanpa match (script yang sama yang dipakai
	# Main.tscn) — cukup untuk membangun level select.
	_menu = MainMenuScript.new()
	add_child(_menu)

	# ── 1. baterai format_time — fungsi produksi SaveManager ──
	for row in _fx["format_time_battery"]:
		var secs := int(row[0])
		_compare(SaveManager.format_time(secs), str(row[1]),
			"format_time(%d)" % secs)

	# ── 2. baterai format skor — string mentah + aturan truncasi murni ──
	var limit := float(_fx["limit_px"])
	for row in _fx["score_format_battery"]:
		var score := int(row[0])
		_compare(_menu._format_level_score(score), str(row[1]),
			"format_skor(%d)" % score)
		# Aturan murni [:8] dengan LEBAR PIKSEL PYGAME dari fixture —
		# fungsi truncasi harus keputusan yang sama pada input sama.
		var pygame_w := float(row[2])
		var expected_final := str(row[4])
		var raw := str(row[1])
		var got_final := raw.substr(0, 8) if pygame_w > limit else raw
		_compare(got_final, expected_final,
			"truncasi[%s w=%d]" % [raw, int(pygame_w)])

	# ── 3. baterai win-rate — int() truncation + band ──
	for row in _fx["win_rate_battery"]:
		var wins := int(row[0])
		var att := int(row[1])
		var wr: Vector2i = _menu._level_win_rate(wins, att)
		_compare(wr.x, int(row[2]), "win_rate(%d/%d)" % [wins, att])
		_compare(wr.y, int(row[3]), "band(%d/%d)" % [wins, att])

	# ── 4. kartu produksi per kasus fixture ──
	for case in _fx["cases"]:
		_test_card_case(case)

	_finish()


func _test_card_case(case: Dictionary) -> void:
	var tag := str(case["name"])
	# State save sesuai kasus: level 3 terbuka butuh level 2 selesai
	# (is_level_unlocked pygame — paritas data unlock_after_level).
	SaveManager.data["completed_levels"] = ([1, 2] if bool(case["unlocked"])
		else [1])
	SaveManager.data["level_stats"] = {"3": case["stats_in"]}
	_menu._show(_menu.State.LEVEL_SELECT)
	var card := _find_card(3)
	_expect(card != null, "%s: kartu level 3 ada" % tag)
	if card == null:
		return

	var values := _collect_parity_labels(card)
	if not bool(case["unlocked"]):
		# Kartu terkunci: TANPA blok stat sama sekali (pygame hanya
		# menggambar stat untuk kartu terbuka).
		_expect(values.is_empty(),
			"%s: kartu terkunci tanpa blok stat (dapet %s)" % [tag,
			str(values.keys())])
		return
	if int(case["attempts"]) == 0:
		# attempts == 0: baris kosong, tanpa slot stat (beda bahasa
		# "No stats yet" -> "Belum ada statistik" dikunci eksplisit).
		_expect(values.is_empty(),
			"%s: tanpa attempt tanpa slot stat" % tag)
		var has_empty := false
		for child in card.find_children("*", "Label", true, false):
			if str(child.text) == "Belum ada statistik":
				has_empty = true
		_expect(has_empty, "%s: baris 'Belum ada statistik' ada" % tag)
		return

	var expect: Dictionary = case["expect"]
	_compare(str(values.get("score", "")), str(expect["score"]),
		"%s: string skor" % tag)
	_compare(str(values.get("time", "")), str(expect["time"]),
		"%s: string waktu" % tag)
	_compare(str(values.get("attempts", "")), str(expect["attempts"]),
		"%s: string attempts" % tag)
	_compare(str(values.get("win_rate", "")),
		"%d%%" % int(expect["win_rate"]), "%s: string win-rate" % tag)
	# Warna slot = RGB ui_theme pygame (data fixture colors).
	var colors: Dictionary = _fx["colors"]
	var band := int(expect["win_rate_band"])
	var wr_rgb = colors["win_rate_low"]
	if band >= 2:
		wr_rgb = colors["win_rate_green"]
	elif band == 1:
		wr_rgb = colors["win_rate_gold"]
	_check_rgb(values, "score", colors["score"], "%s: warna skor" % tag)
	_check_rgb(values, "time", colors["time"], "%s: warna waktu" % tag)
	_check_rgb(values, "attempts", colors["attempts"],
		"%s: warna attempts" % tag)
	_check_rgb(values, "win_rate", wr_rgb, "%s: warna win-rate" % tag)


func _find_card(level_num: int) -> Control:
	for node in _menu._root.find_children("*", "PanelContainer", true, false):
		if node.has_meta("level_num") \
				and int(node.get_meta("level_num")) == level_num:
			return node
	return null


func _collect_parity_labels(card: Control) -> Dictionary:
	var out := {}
	for label in card.find_children("*", "Label", true, false):
		if label.has_meta("parity"):
			out[str(label.get_meta("parity"))] = {
				"text": str(label.text),
				"rgb": label.get_meta("parity_rgb"),
			}
	return out


func _check_rgb(values: Dictionary, key: String, rgb, tag: String) -> void:
	if not values.has(key):
		_expect(false, tag + " (slot hilang)")
		return
	var got: Array = values[key]["rgb"]
	_expect(int(got[0]) == int(rgb[0]) and int(got[1]) == int(rgb[1]) \
		and int(got[2]) == int(rgb[2]),
		"%s (dapet %s, mau %s)" % [tag, str(got), str(rgb)])


func _compare(got, want, tag: String) -> void:
	_expect(str(got) == str(want),
		"%s (dapet %s, mau %s)" % [tag, str(got), str(want)])


func _finish() -> void:
	_menu.queue_free()
	# Pulihkan state in-memory + isi file user:// persis sebelum tes —
	# save pengguna tidak boleh tersentuh tes apa pun.
	SaveManager.data = _save_before
	if _save_file_existed:
		var f := FileAccess.open(SaveManager.SAVE_PATH, FileAccess.WRITE)
		f.store_string(_save_file_before)
		f.close()
	else:
		DirAccess.remove_absolute(
			ProjectSettings.globalize_path(SaveManager.SAVE_PATH))
	print("[LevelSelectStatsParityTest] %s: %d cek, %d gagal"
		% ["PASS" if _failures == 0 else "FAIL", _checks, _failures])
	get_tree().quit(0 if _failures == 0 else 1)
