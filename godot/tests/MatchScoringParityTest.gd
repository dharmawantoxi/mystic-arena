# MatchScoringParityTest — FASE 13, klaster skor match vs oracle pygame.
#
# python tools/test_godot_match_parity.py              (fixture freshness)
# godot --headless --path godot res://tests/MatchScoringParityTest.tscn --quit-after 300
#
# Yang direplay dari seksi fixture "match_scoring" (objek biasa, bukan
# string kompak — diff-able saat review):
#
#   combo        : state machine ComboCounter murni per frame (count/timer/
#                  last_combo/color_flash/display_scale/target_scale) —
#                  5 kasus termasuk quirk max_combo-read-before-add,
#                  expiry 120 frame, dan re-kill menjelang expiry; data
#                  draw (label ambang, warna + pulsa flash, anchor
#                  (W-100,100), bar 80x4 @(cx-40,cy+40)) dari draw pygame
#                  asli via ComboCounter.gd + HudLayout.
#   kills        : 9 skenario loop reward Game.update pygame SUNGGUHAN
#                  (unit betulan mati via take_damage): gold/score/ai_gold/
#                  total_kills/max_combo/combo per frame + atribusi
#                  killer.kills — +150 hero (tim korban), combo hanya kill
#                  minion red, kill netral/tower/minion/self tanpa
#                  atribusi, respawn 600 frame tidak membayar dobel.
#                  Godot: node Minion/Hero/Tower ASLI + GameManager
#                  (_tick_combo/_update_hero_respawns di-step 1/60).
#   level_stats  : SaveManager.get_level_stats/update_level_stats vs 9
#                  kasus pygame (flag NEW BEST, best hanya saat menang,
#                  max_combo all-time, time 0 diabaikan) + default.
#   achievement  : state machine AchievementPopup (antrean, 180 frame,
#                  popup berikutnya menggantikan di frame yang sama) +
#                  kurva slide 181 titik + teks panel; trigger NEW HERO
#                  UNLOCKED! (5 kasus) dari _auto_unlock_defeated_boss_
#                  heroes ASLI lewat signal achievement_unlocked.
#   end_match    : integrasi penuh — start_level(1) + end_match menulis
#                  level_stats save, menyalakan flag NEW BEST, baris panel
#                  game-over (Max Combo + NEW BEST! + NEW HERO), dan
#                  memancarkan popup; defeat menulis statistik tanpa best.
#
# Harness TIDAK menyentuh save pengguna: SaveManager.data + berkas
# user://mystic_save.json di-snapshot di awal lalu dipulihkan di akhir
# (pola UiHudParityTest).
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainScene = preload("res://scenes/main.tscn")
const HeroScene = preload("res://scenes/hero/Hero.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const ComboCounterScript = preload("res://scripts/utils/ComboCounter.gd")
const AchievementPopupScript = preload("res://scenes/ui/AchievementPopup.gd")

const FRAME := 1.0 / 60.0

var _fx: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _save_before: Dictionary = {}
var _save_file_before = null
var _popup_records: Array = []
var _main = null
var _hud: Control = null


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	if FileAccess.file_exists(SaveManager.SAVE_PATH):
		_save_file_before = FileAccess.get_file_as_string(SaveManager.SAVE_PATH)
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("match_scoring"):
		push_error("[MatchScoringParityTest] fixture match_scoring belum ada —"
			+ " jalankan tools/test_godot_match_parity.py --write-fixture")
		_failures += 1
		_finish()
		return
	_fx = fixture["match_scoring"]

	_test_combo_machine()
	_test_combo_draw()
	_test_level_stats()
	_test_achievement_machine()
	_test_new_hero_trigger()
	await _test_kills()
	await _test_end_match()

	_finish()


# ══════════════════════════════════════════════════════════
#  1. MESIN COMBO (murni — state per frame)
# ══════════════════════════════════════════════════════════

func _test_combo_machine() -> void:
	for case in _fx["combo"]["cases"]:
		var cc = ComboCounterScript.new()
		for step in case["steps"]:
			for i in range(int(step["n"])):
				if str(step["op"]) == "kill":
					cc.add_kill()
				else:
					cc.update()
			var st: Dictionary = step["state"]
			var tag := "%s/%s x%d" % [case["name"], step["op"], int(step["n"])]
			_expect(cc.count == int(st["count"]), "%s count" % tag)
			_expect(cc.timer == int(st["timer"]), "%s timer" % tag)
			_expect(cc.last_combo == int(st["last_combo"]), "%s last_combo" % tag)
			_expect(cc.color_flash == int(st["color_flash"]), "%s color_flash" % tag)
			_near(cc.display_scale, float(st["display_scale"]),
				"%s display_scale" % tag, 0.0000011)
			_near(cc.target_scale, float(st["target_scale"]),
				"%s target_scale" % tag, 0.0000011)


# ══════════════════════════════════════════════════════════
#  2. DATA DRAW COMBO (label/warna/bar/anchor — dari draw pygame)
# ══════════════════════════════════════════════════════════

func _test_combo_draw() -> void:
	var draw: Dictionary = _fx["combo"]["draw"]
	for cnt in draw["counts"]:
		var entry: Dictionary = draw["counts"][cnt]
		var c := int(cnt)
		var tag := "combo draw x%d" % c
		# Teks hitungan + warna dasar (render pertama = teks utama).
		var main: Dictionary = entry["texts"][0]
		_expect(ComboCounter.count_text(c) == str(main["text"]),
			"%s teks" % tag)
		var color := ComboCounter.tier_color_rgb(c)
		_expect(color.x == int(main["color"][0])
			and color.y == int(main["color"][1])
			and color.z == int(main["color"][2]), "%s warna" % tag)
		# Label ambang hanya untuk count >= 5 (render ke-3).
		if c >= 5:
			var label: Dictionary = entry["texts"][2]
			_expect(ComboCounter.tier_label(c) == str(label["text"]),
				"%s label" % tag)
			var lcolor := ComboCounter.tier_color_rgb(c)
			_expect(lcolor.x == int(label["color"][0])
				and lcolor.y == int(label["color"][1])
				and lcolor.z == int(label["color"][2]), "%s warna label" % tag)
			var lc: Array = entry["label_center"]
			var want_lc := HudLayout.combo_center() + HudLayout.COMBO_LABEL_OFFSET
			_expect(absf(want_lc.x - float(lc[0])) <= 2.0
				and absf(want_lc.y - float(lc[1])) <= 2.0,
				"%s anchor label %s vs %s" % [tag, want_lc, lc])
		else:
			_expect(entry["texts"].size() == 2,
				"%s tanpa label (gate >= 5)" % tag)
		# Anchor pusat + bar 80x4 di (cx-40, cy+40).
		var cc2: Array = entry["count_center"]
		var want_c := HudLayout.combo_center()
		_expect(absf(want_c.x - float(cc2[0])) <= 2.0
			and absf(want_c.y - float(cc2[1])) <= 2.0,
			"%s anchor %s vs %s" % [tag, want_c, cc2])
		if c >= 2:
			var bar := HudLayout.combo_bar_rect()
			var want_bar: Array = entry["bar_rects"][0]
			_expect(int(bar.position.x) == int(want_bar[0])
				and int(bar.position.y) == int(want_bar[1])
				and int(bar.size.x) == int(want_bar[2])
				and int(bar.size.y) == int(want_bar[3]),
				"%s rect bar %s vs %s" % [tag, bar, want_bar])
		else:
			_expect(entry["bar_rects"].is_empty(),
				"%s tanpa bar (gate >= 2)" % tag)
	# Lebar isi bar per sisa timer.
	for t in draw["bar"]:
		var rects: Array = draw["bar"][t]
		var fill_w := ComboCounter.bar_fill_width(int(t))
		_expect(int(rects[1][2]) == fill_w,
			"bar fill timer %s: %d != %d" % [t, fill_w, int(rects[1][2])])
	# Kasus tersembunyi: count 0 + scale 0 tidak menggambar apa pun.
	var hidden: Dictionary = draw["hidden"]
	_expect(hidden["texts"].is_empty() and hidden["bar_rects"].is_empty(),
		"combo hidden")
	_expect(not ComboCounter.is_drawn(0, 0.0), "gate visible 0/0")
	_expect(ComboCounter.is_drawn(1, 1.0), "gate visible 1/scale")
	_expect(ComboCounter.is_drawn(0, 0.5), "gate visible decay")
	# Pulsa flash: warna tercampur putih selama 20 frame.
	var flash: Dictionary = draw["flash"]
	var fmain: Dictionary = flash["texts"][0]
	var fcolor := ComboCounter.display_color_rgb(5, int(flash["color_flash"]))
	_expect(fcolor.x == int(fmain["color"][0])
		and fcolor.y == int(fmain["color"][1])
		and fcolor.z == int(fmain["color"][2]), "warna flash combo")


# ══════════════════════════════════════════════════════════
#  3. LEVEL STATS (best per level + flag NEW BEST)
# ══════════════════════════════════════════════════════════

func _test_level_stats() -> void:
	for case in _fx["level_stats"]["cases"]:
		var data := {}
		if case["prior"] != null:
			data["level_stats"] = {"3": (case["prior"] as Dictionary).duplicate(true)}
		var result: Dictionary = SaveManager.update_level_stats(
			data, 3, (case["match"] as Dictionary).duplicate(true))
		var tag := str(case["name"])
		_expect(bool(result["is_new_best_score"])
			== bool(case["flags"]["is_new_best_score"]), "%s flag score" % tag)
		_expect(bool(result["is_new_best_time"])
			== bool(case["flags"]["is_new_best_time"]), "%s flag time" % tag)
		_expect(_dict_eq(result["new_stats"], case["new_stats"]),
			"%s new_stats %s vs %s" % [tag, result["new_stats"], case["new_stats"]])
		_expect(_dict_eq(data["level_stats"]["3"], case["new_stats"]),
			"%s written-back" % tag)
	_expect(_dict_eq(SaveManager.get_level_stats({}, 3),
		_fx["level_stats"]["defaults"]), "default level stats")


# ══════════════════════════════════════════════════════════
#  4. POPUP ACHIEVEMENT (state machine + slide + teks)
# ══════════════════════════════════════════════════════════

func _test_achievement_machine() -> void:
	for case in _fx["achievement"]["cases"]:
		var popup = AchievementPopupScript.new()
		add_child(popup)
		popup.set_process(false)
		for u in case["unlocks"]:
			popup.unlock(str(u[0]), str(u[1]), str(u[2]))
		var tag := str(case["name"])
		for step in case["steps"]:
			for i in range(int(step["frames"])):
				popup.tick()
			var want = step["current"]
			if want == null:
				_expect(popup.current == null, "%s current null" % tag)
			else:
				_expect(popup.current != null, "%s current ada" % tag)
				if popup.current != null:
					_expect(str(popup.current["title"]) == str(want["title"]),
						"%s judul" % tag)
					_expect(str(popup.current["description"])
						== str(want["description"]), "%s deskripsi" % tag)
					_expect(str(popup.current["icon"]) == str(want["icon_type"]),
						"%s ikon" % tag)
			_expect(popup.timer == int(step["timer"]), "%s timer" % tag)
			_expect(popup.queue.size() == int(step["queue"]), "%s antrean" % tag)
		popup.free()
	# Kurva slide 181 titik (posisi panel per sisa timer).
	for t in _fx["achievement"]["slide_x"]:
		var want: Array = _fx["achievement"]["slide_x"][t]
		var rect := HudLayout.achievement_panel_rect(int(t))
		_expect(int(rect.position.x) == int(want[0])
			and int(rect.position.y) == int(want[1]),
			"slide x timer %s: (%d,%d) != (%d,%d)" % [t, rect.position.x,
				rect.position.y, int(want[0]), int(want[1])])
	# Teks panel (header letterspaced + judul + deskripsi pendek).
	var texts: Array = _fx["achievement"]["panel_texts"]
	_expect(HudLayout.letter("ACHIEVEMENT") == str(texts[0]["text"]),
		"header popup")
	_expect(_rgb255(HudLayout.ACHIEVEMENT_HEADER_COLOR)
		== Vector3i(int(texts[0]["color"][0]), int(texts[0]["color"][1]),
			int(texts[0]["color"][2])), "warna header popup")
	_expect(str(texts[1]["text"]) == "NEW HERO!", "judul pendek fixture")
	_expect(_rgb255(HudLayout.ACHIEVEMENT_TITLE_COLOR).x
		== int(texts[1]["color"][0]), "warna judul popup")
	_expect(_rgb255(HudLayout.ACHIEVEMENT_DESC_COLOR)
		== Vector3i(int(texts[2]["color"][0]), int(texts[2]["color"][1]),
			int(texts[2]["color"][2])), "warna deskripsi popup")


# ══════════════════════════════════════════════════════════
#  5. TRIGGER NEW HERO UNLOCKED! (dari _auto_unlock asli)
# ══════════════════════════════════════════════════════════

func _test_new_hero_trigger() -> void:
	var recorder := func(title: String, description: String, icon: String):
		_popup_records.append([title, description, icon])
	GameManager.achievement_unlocked.connect(recorder)
	for case in _fx["achievement"]["new_hero"]:
		SaveManager.data["unlocked_heroes"] = (case["purchased"] as Array).duplicate()
		SaveManager.data["unlocked_bosses"] = (case["save_bosses"] as Array).duplicate()
		GameManager.bosses_defeated_this_match = (case["bosses"] as Array).duplicate()
		GameManager.heroes_unlocked_this_match = []
		_popup_records.clear()
		GameManager._auto_unlock_defeated_boss_heroes()
		var tag := str(case["name"])
		_expect(GameManager.heroes_unlocked_this_match == case["newly"],
			"%s newly %s vs %s" % [tag, GameManager.heroes_unlocked_this_match,
				case["newly"]])
		_expect(_popup_records.size() == case["queue"].size(),
			"%s jumlah popup %d != %d" % [tag, _popup_records.size(),
				case["queue"].size()])
		for i in range(int(case["queue"].size())):
			var want: Dictionary = case["queue"][i]
			var got: Array = _popup_records[i]
			_expect(str(got[0]) == str(want["title"]), "%s judul popup" % tag)
			_expect(str(got[1]) == str(want["description"]),
				"%s deskripsi popup (got %s)" % [tag, got[1]])
			_expect(str(got[2]) == str(want["icon"]), "%s ikon popup" % tag)
		_expect(SaveManager.data["unlocked_heroes"] == case["purchased_after"],
			"%s purchased_after" % tag)
		_expect(SaveManager.data["unlocked_bosses"] == case["save_bosses_after"],
			"%s save_bosses_after" % tag)
	GameManager.achievement_unlocked.disconnect(recorder)


# ══════════════════════════════════════════════════════════
#  6. LOOP REWARD KILL (node asli vs Game.update pygame)
# ══════════════════════════════════════════════════════════

func _test_kills() -> void:
	GameManager.set_process(false)
	GameManager.state = "playing"
	GameManager.in_menu = false
	GameManager.set_paused(false)
	GameManager.waves_enabled = false
	for spec in _fx["kills"]:
		_run_kill_scenario(spec)
		await get_tree().process_frame
	GameManager.waves_enabled = true
	GameManager.state = "idle"
	GameManager.in_menu = true


func _run_kill_scenario(spec: Dictionary) -> void:
	# Reset state match — paritas reset_game oracle (gold 1000, income 0).
	GameManager.gold = 1000
	GameManager.score = 0
	GameManager.ai_gold = 0
	GameManager.total_kills = 0
	GameManager.max_combo = 0
	GameManager.combo.reset()
	GameManager._hero_respawn_timers.clear()
	GameManager.gold_per_second = 0.0
	GameManager.wave_number = 0

	var units := {}
	var i := 0
	for uspec in spec["units"]:
		var node = null
		match str(uspec["kind"]):
			"minion":
				node = MinionScene.instantiate()
				node.minion_type = str(uspec["type"])
				node.team = str(uspec["team"])
			"hero":
				node = HeroScene.instantiate()
				node.hero_type = str(uspec["type"])
				node.team = str(uspec["team"])
			"tower":
				# Hanya sebagai SUMBER damage (bukan unit arena) — paritas
				# oracle yang tidak memasukkan tower ke game.towers.
				node = TowerScene.instantiate()
				node.team = str(uspec["team"])
		node.position = Vector2(220.0 + i * 240.0, 300.0 + (i % 2) * 240.0)
		add_child(node)
		node.set_physics_process(false)
		units[str(uspec["id"])] = node
		i += 1

	var tag := str(spec["name"])
	for step in spec["steps"]:
		for kill in step["kills"]:
			var victim = units[str(kill["unit"])]
			var by = null
			if kill.has("by") and kill["by"] != null:
				by = units[str(kill["by"])]
			var from_team := ""
			if kill.has("team"):
				from_team = str(kill["team"])
			elif by != null:
				from_team = str(by.get("team"))
			victim.take_damage(1000000000.0, from_team, "normal", by)
		for f in range(int(step["frames"])):
			# Satu frame oracle = Game.update: combo tick (EffectManager)
			# + countdown respawn hero.
			GameManager._tick_combo(FRAME)
			GameManager._update_hero_respawns(FRAME)
		var snap: Dictionary = step["snap"]
		_expect(GameManager.gold == int(snap["gold"]), "%s gold" % tag)
		_expect(GameManager.score == int(snap["score"]), "%s score" % tag)
		_expect(GameManager.ai_gold == int(snap["ai_gold"]), "%s ai_gold" % tag)
		_expect(GameManager.total_kills == int(snap["total_kills"]),
			"%s total_kills" % tag)
		_expect(GameManager.max_combo == int(snap["max_combo"]),
			"%s max_combo" % tag)
		_expect(GameManager.combo.count == int(snap["combo"]["count"]),
			"%s combo count" % tag)
		_expect(GameManager.combo.timer == int(snap["combo"]["timer"]),
			"%s combo timer" % tag)
		_expect(GameManager.combo.last_combo == int(snap["combo"]["last_combo"]),
			"%s combo last" % tag)
		for uid in snap["kills"]:
			_expect(int(units[str(uid)].get("kills")) == int(snap["kills"][uid]),
				"%s kills %s" % [tag, uid])

	for node in units.values():
		node.free()


# ══════════════════════════════════════════════════════════
#  7. INTEGRASI END_MATCH (level_stats + NEW BEST + baris panel)
# ══════════════════════════════════════════════════════════

func _test_end_match() -> void:
	# Main + HUD sungguhan (pola UiHudParityTest).
	GameManager.set_process(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	_main = MainScene.instantiate()
	add_child(_main)
	_main.set_process(false)
	_main._ai.set_process(false)
	var containers: Node = GameManager.hero_container.get_parent()
	containers.process_mode = Node.PROCESS_MODE_DISABLED
	await get_tree().process_frame
	await get_tree().process_frame
	_hud = _main.find_child("HUD", true, false)

	var recorder := func(_t: String, _d: String, _i: String):
		_popup_records.append([_t, _d, _i])
	GameManager.achievement_unlocked.connect(recorder)

	# ── VICTORY level 1: save segar -> NEW BEST skor+waktu + Max Combo ──
	SaveManager.data["unlocked_heroes"] = ["kaizen"]
	SaveManager.data["completed_levels"] = []
	SaveManager.data["level_stats"] = {}
	SaveManager.data["meta_gold"] = 0
	SaveManager.data["replay_reward_counts"] = {}
	GameManager.start_level(1)
	await get_tree().process_frame
	await get_tree().process_frame
	_main._on_key(_key(KEY_SPACE))  # lewati intro level
	await get_tree().process_frame
	GameManager.score = 7777
	GameManager.total_kills = 4242
	GameManager.max_combo = 17
	GameManager.wave_number = 13
	GameManager.match_start_msec = Time.get_ticks_msec() - 3723 * 1000
	GameManager.bosses_defeated_this_match = ["abaddon"]
	_popup_records.clear()
	GameManager.end_match(true)

	_expect(GameManager.new_best_score and GameManager.new_best_time,
		"victory L1: kedua flag NEW BEST")
	var want_stats: Dictionary = _level_case("first_win")["new_stats"]
	_expect(_dict_eq(SaveManager.data["level_stats"]["1"], want_stats),
		"victory L1: level_stats %s vs %s" % [
			SaveManager.data["level_stats"]["1"], want_stats])
	_expect("Final Score: 7,777  NEW BEST!" in _hud._over_stats.text,
		"baris skor NEW BEST (got %s)" % _hud._over_stats.text)
	_expect("Match Time: 62:03  NEW BEST!" in _hud._over_stats.text,
		"baris waktu NEW BEST (got %s)" % _hud._over_stats.text)
	_expect("Waves Survived: 13" in _hud._over_stats.text, "baris wave")
	_expect("Total Kills: 4242" in _hud._over_stats.text, "baris kill")
	_expect("Max Combo: x17" in _hud._over_stats.text, "baris Max Combo")
	_expect(_hud._over_stats.text.count("NEW BEST!") == 2,
		"tepat 2 penanda NEW BEST")
	# Popup achievement NEW HERO UNLOCKED! + baris panel game-over (Fase 12).
	_expect(_popup_records.size() == 1 and _popup_records[0][0]
		== "NEW HERO UNLOCKED!", "popup NEW HERO terpancar")
	var one_boss := _new_hero_case("one_boss")
	_expect(_popup_records[0][1] == str(one_boss["queue"][0]["description"]),
		"deskripsi popup NEW HERO (got %s)" % _popup_records[0][1])
	var popup_node = _hud.find_child("AchievementPopup", true, false)
	_expect(popup_node != null and popup_node.queue.size() == 1,
		"popup HUD mengantre NEW HERO")
	# Panel game-over pygame (fixture ui_hud): label baris + jumlah NEW BEST.
	var overlay: Dictionary = _fx_ui_hud()["scenarios"]["overlay_victory_best"]
	var labels: Array = ["Final Score", "Match Time", "Waves Survived",
		"Total Kills", "Max Combo"]
	for label in labels:
		_expect(str(label) in overlay["texts"], "label oracle %s" % label)
		_expect(str(label) in _hud._over_stats.text, "baris Godot %s" % label)
	_expect(int(overlay["texts"].count("NEW BEST!")) == 2, "oracle 2 NEW BEST")

	# ── DEFEAT level 1: statistik tetap ditulis, tanpa best/wins ──
	SaveManager.data["level_stats"] = {}
	GameManager.state = "playing"
	GameManager._meta_reward_granted = false
	GameManager.bosses_defeated_this_match = []
	GameManager.score = 7777
	GameManager.total_kills = 4242
	GameManager.max_combo = 17
	GameManager.wave_number = 13
	GameManager.match_start_msec = Time.get_ticks_msec() - 3723 * 1000
	_popup_records.clear()
	GameManager.end_match(false)
	_expect(not GameManager.new_best_score and not GameManager.new_best_time,
		"defeat: tanpa flag NEW BEST")
	var want_defeat: Dictionary = _level_case("first_defeat_big")["new_stats"]
	_expect(_dict_eq(SaveManager.data["level_stats"]["1"], want_defeat),
		"defeat: level_stats %s vs %s" % [
			SaveManager.data["level_stats"]["1"], want_defeat])
	_expect(not ("NEW BEST!" in _hud._over_stats.text), "defeat tanpa penanda")
	_expect("Max Combo: x17" in _hud._over_stats.text, "defeat baris Max Combo")
	_expect(_popup_records.is_empty(), "defeat tanpa popup NEW HERO")

	GameManager.achievement_unlocked.disconnect(recorder)
	# Bersih-bersih (pola UiHudParityTest._finish).
	get_tree().paused = false
	Engine.time_scale = 1.0
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager._hero_respawn_timers.clear()
	GameManager._reset_wave_state()
	GameManager.bosses_defeated_this_match = []
	GameManager.heroes_unlocked_this_match = []
	_main.free()
	_main = null
	_hud = null


func _level_case(name: String) -> Dictionary:
	for case in _fx["level_stats"]["cases"]:
		if str(case["name"]) == name:
			return case
	_expect(false, "kasus level_stats %s hilang dari fixture" % name)
	return {}


func _new_hero_case(name: String) -> Dictionary:
	for case in _fx["achievement"]["new_hero"]:
		if str(case["name"]) == name:
			return case
	_expect(false, "kasus new_hero %s hilang dari fixture" % name)
	return {}


func _fx_ui_hud() -> Dictionary:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	return fixture["ui_hud"]


# ══════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════

## Bandingkan dua Dictionary dari fixture: JSON Godot mem-parse SEMUA angka
## sebagai float, sedangkan nilai Godot kita int — Dictionary == tidak
## memaksa konversi lintas tipe itu, jadi bandingkan per-kunci secara
## numerik (bool/string harus tetap sejenis).
func _dict_eq(a: Dictionary, b: Dictionary) -> bool:
	if a.size() != b.size():
		return false
	for key in a:
		if not b.has(key):
			return false
		var x = a[key]
		var y = b[key]
		if typeof(x) != typeof(y):
			if (x is int or x is float) and (y is int or y is float):
				if float(x) != float(y):
					return false
			else:
				return false
		elif x is Dictionary:
			if not _dict_eq(x, y):
				return false
		elif x != y:
			return false
	return true


## Komponen 0..255 sebuah Color — roundi menghindari perbedaan implementasi
## Color.r8 (truncate vs round) saat membandingkan warna fixture.
func _rgb255(c: Color) -> Vector3i:
	return Vector3i(roundi(c.r * 255.0), roundi(c.g * 255.0),
		roundi(c.b * 255.0))


func _key(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = true
	return event


func _near(actual: float, want: float, message: String,
		eps: float = 0.000001) -> void:
	_expect(absf(actual - want) <= eps,
		"%s (got %s want %s)" % [message, actual, want])


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		# print() ke stdout: gate CI menangkap pola FAIL.
		print("[MatchScoringParityTest] FAIL: " + message)
		push_error("[MatchScoringParityTest] " + message)


func _finish() -> void:
	SaveManager.data = _save_before
	if _save_file_before == null:
		if FileAccess.file_exists(SaveManager.SAVE_PATH):
			DirAccess.remove_absolute(SaveManager.SAVE_PATH)
	else:
		var f := FileAccess.open(SaveManager.SAVE_PATH, FileAccess.WRITE)
		f.store_string(_save_file_before)
	GameManager.set_process(true)
	GameManager.waves_enabled = true
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print("[MatchScoringParityTest] PASS: %d checks klaster skor vs oracle pygame"
			% _checks)
	else:
		print("[MatchScoringParityTest] FAIL: %d/%d checks gagal"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
