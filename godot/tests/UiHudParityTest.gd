# FASE 12 — UI/HUD in-match vs oracle draw pygame (seksi ui_hud).
# python tools/test_godot_match_parity.py   (fixture freshness)
# godot --headless --path godot res://tests/UiHudParityTest.tscn --quit-after 400
extends Node

const MainScene = preload("res://scenes/main.tscn")
const LevelIntroScript = preload("res://scenes/ui/LevelIntro.gd")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

var _main = null
var _hud: Control = null
var _shop: Control = null
var _bar: Control = null
var _menu: Control = null
var _fx: Dictionary = {}
var _save_before: Dictionary = {}
var _save_file_before = null # String bytes / null
var _universe: Array = [] # semesta ui_key tertutup (dibangun sekali)
var _failures: int = 0
var _checks: int = 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	if FileAccess.file_exists(SaveManager.SAVE_PATH):
		_save_file_before = FileAccess.get_file_as_string(SaveManager.SAVE_PATH)
	_fx = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))["ui_hud"]
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
	_shop = _hud.find_child("ShopPanel", true, false)
	_bar = _hud.find_child("SkillBar", true, false)
	_menu = _main.find_child("MainMenu", true, false)

	_test_formats()
	_test_touch()
	_test_magic_melee()
	_test_item_catalog()
	_test_wave_pure()
	_test_intro_skip()
	_test_touchhud_data()
	_test_structure()

	SaveManager.data["unlocked_heroes"] = ["kaizen"]
	SaveManager.data["completed_levels"] = []
	GameManager.start_level(1)
	await get_tree().process_frame
	await get_tree().process_frame
	_test_hud_labels()
	_main._on_key(_key(KEY_SPACE)) # skip intro (tree jalan untuk tween/pause)
	await get_tree().process_frame
	await _test_wave_live()
	await _test_pause_geometry()
	_test_skillbar_panel()
	_test_shop_heroes()
	await _test_shop_tower()
	_test_shop_nexus()
	_test_shop_item()
	_test_clicks()
	_test_hotkeys_playing()
	await _test_gameover()
	_finish()


# ══════════════════════════════════════════════════════════
#  FORMAT TEKS (murni)
# ══════════════════════════════════════════════════════════

func _test_formats() -> void:
	var formats: Dictionary = _fx["formats"]
	for gval in formats["gold"]:
		_expect(HudLayout.format_thousands(int(gval)) == formats["gold"][gval],
			"format_thousands %s" % gval)
	for rval in formats["income"]:
		var want: String = formats["income"][rval]
		var rate := float(rval)
		_expect(HudLayout.format_gold_rate(rate) == want.trim_prefix("+").trim_suffix("/s"),
			"format_gold_rate %s" % rval)
		_expect(GameManager.format_gold_rate(rate) == want.trim_prefix("+").trim_suffix("/s"),
			"GameManager delegates %s" % rval)
		_expect(_hud._format_gold_rate(rate) == want.trim_prefix("+").trim_suffix("/s"),
			"HUD delegates %s" % rval)
		_expect("+" + HudLayout.format_gold_rate(rate) + "/s" == want,
			"income row %s" % rval)
	for dval in formats["mode"]:
		_expect(HudLayout.mode_label(str(dval)) == formats["mode"][dval],
			"mode_label %s" % dval)
	_near_color(HudLayout.mode_color("easy"), Color(100, 210, 255), "mode easy")
	_near_color(HudLayout.mode_color("hard"), Color(255, 120, 120), "mode hard")
	_near_color(HudLayout.mode_color("normal"), Color(120, 230, 150), "mode normal")
	_near_color(HudLayout.mode_color("nightmare"), Color(120, 230, 150), "mode fallback")
	for fval in formats["cooldown"]:
		var want = formats["cooldown"][fval]
		var got := HudLayout.cooldown_seconds(int(fval))
		if want == null:
			_expect(got == 0, "cooldown 0 shows nothing")
		else:
			_expect(got == int(want), "cooldown %s -> %s" % [fval, want])
	for sval in formats["match_time"]:
		_expect(HudLayout.format_match_time(int(sval)) == formats["match_time"][sval],
			"match_time %s" % sval)


func _near_color(actual: Color, rgb: Color, message: String) -> void:
	# rgb = komponen 0..255 (format sumber pygame); actual = Color 0..1.
	_expect(absf(actual.r - rgb.r / 255.0) < 0.002
		and absf(actual.g - rgb.g / 255.0) < 0.002
		and absf(actual.b - rgb.b / 255.0) < 0.002,
		"%s (got %s)" % [message, actual])


# ══════════════════════════════════════════════════════════
#  TOUCH RECT (murni)
# ══════════════════════════════════════════════════════════

func _test_touch() -> void:
	for entry in _fx["rules"]["touch_rects"]:
		var r: Array = entry["rect"]
		var want: Array = entry["expanded"]
		var got := HudLayout.touch_hit_rect(Rect2(r[0], r[1], r[2], r[3]))
		_expect(int(got.position.x) == int(want[0]) and int(got.position.y) == int(want[1])
			and int(got.size.x) == int(want[2]) and int(got.size.y) == int(want[3]),
			"touch_rect %s -> %s (got %s)" % [r, want, got])
	var base := Rect2(10, 10, 20, 20)
	for entry in _fx["rules"]["touch_hits"]:
		var p: Array = entry["point"]
		_expect(HudLayout.touch_hit(base, Vector2(p[0], p[1])) == bool(entry["hit"]),
			"touch_hit %s" % [p])


# ══════════════════════════════════════════════════════════
#  PREDIKAT MELEE/MAGIC 222 HERO + KATALOG ITEM
# ══════════════════════════════════════════════════════════

func _test_magic_melee() -> void:
	var rules: Dictionary = _fx["rules"]
	_expect(HudLayout.MELEE_RANGE_MAX == int(rules["melee_max_range"]), "melee gate 80")
	var bad_range: Array = []
	var bad_magic: Array = []
	for ht in rules["hero_range"]:
		var d: Dictionary = HeroDB.get_hero(str(ht))
		if int(d.get("range", -1)) != int(rules["hero_range"][ht]):
			bad_range.append(ht)
		if ItemDB.is_magic_hero(d) != bool(rules["hero_magic"][ht]):
			bad_magic.append(ht)
		_expect(HudLayout.is_melee_range(float(d.get("range", 100)))
			== (float(d.get("range", 100)) <= 80.0), "melee predikat %s" % ht)
	_expect(bad_range.is_empty(), "range 222 hero sama (%s)" % [bad_range])
	_expect(bad_magic.is_empty(), "is_magic_hero 222 hero sama (%s)" % [bad_magic])


func _test_item_catalog() -> void:
	var items: Dictionary = _fx["rules"]["items"]
	_expect(ItemDB.items.keys().size() == items.size(), "33 item")
	for sid in items:
		var want: Dictionary = items[sid]
		var got: Dictionary = ItemDB.get_item(str(sid))
		_expect(int(got.get("cost", -1)) == int(want["cost"]), "cost %s" % sid)
		_expect(bool(got.get("melee_only", false)) == bool(want["melee_only"]),
			"melee_only %s" % sid)
		_expect(bool(got.get("magic_only", false)) == bool(want["magic_only"]),
			"magic_only %s" % sid)
	# Godot tak punya halaman (scroll tunggal) — himpunan id-nya yang direplay.
	var union: Array = []
	for page in _fx["rules"]["shop_pages"].values():
		union.append_array(page)
	_expect(union.size() == 33 and ItemDB.items.keys().all(
		func(sid): return union.has(sid)), "union halaman = 33 id item")


# ══════════════════════════════════════════════════════════
#  WAVE (murni: 121 titik + judul + subtitle)
# ══════════════════════════════════════════════════════════

func _test_wave_pure() -> void:
	var wave: Dictionary = _fx["wave"]
	_expect(HudLayout.WAVE_BANNER_FRAMES == int(wave["duration"]), "durasi 120f")
	for ckey in wave["cases"]:
		var c: Dictionary = wave["cases"][ckey]
		_expect(HudLayout.wave_title(int(ckey)) == c["title"], "wave title %s" % ckey)
		_expect(HudLayout.wave_subtitle() == c["sub"], "wave subtitle")
		_expect(int(HudLayout.WAVE_BANNER_SIZE.x) == int(c["banner"]["w"])
			and int(HudLayout.WAVE_BANNER_SIZE.y) == int(c["banner"]["h"])
			and int(HudLayout.WAVE_BANNER_POS.y) == int(c["banner"]["y"]),
			"banner 400x80 y=200")
	var slides: Dictionary = wave["slide_x"]
	_expect(slides.size() == 121, "121 titik slide")
	var bad := 0
	for t in 121:
		var want: Array = slides[str(t)]
		var got := int(HudLayout.wave_banner_rect(t).position.x)
		if got != int(want[0]):
			bad += 1
			if bad <= 3:
				push_error("[UiHudParityTest] slide t=%d: got %d want %d" % [t, got, want[0]])
		_checks += 1
		if got != int(want[0]):
			_failures += 1
	_expect(bad == 0, "kurva slide 121/121 sama")


# ══════════════════════════════════════════════════════════
#  INTRO SKIP + TOUCH DATA + STRUKTUR
# ══════════════════════════════════════════════════════════

func _test_intro_skip() -> void:
	var skips: Dictionary = _fx["intro_skip"]
	_expect(_fresh_intro().skip_key(_key(KEY_SPACE)) == bool(skips["space"]), "skip SPACE")
	_expect(_fresh_intro().skip_key(_key(KEY_ENTER)) == bool(skips["return"]), "skip ENTER")
	_expect(_fresh_intro().skip_key(_key(KEY_ESCAPE)) == bool(skips["escape"]), "ESC tak skip")
	_expect(_fresh_intro().skip_click() == bool(skips["click"]), "skip klik")


func _fresh_intro():
	var intro = LevelIntroScript.new()
	add_child(intro)
	return intro


func _test_touchhud_data() -> void:
	var touch: Dictionary = _fx["touchhud"]
	for bid in touch["buttons"]:
		var want: Dictionary = touch["buttons"][bid]
		var got: Dictionary = HudLayout.TOUCH_BUTTONS.get(str(bid), {})
		_expect(not got.is_empty(), "touch button %s" % bid)
		if got.is_empty():
			continue
		_expect(got["label"] == want["label"], "touch label %s" % bid)
		# Array == Array GDScript STRICT terhadap tipe elemen (int lawan
		# float JSON selalu false) — bandingkan per elemen via int().
		var gr: Array = got["rect"]
		var wr: Array = want["rect"]
		_expect(gr.size() == 4 and wr.size() == 4
			and int(gr[0]) == int(wr[0]) and int(gr[1]) == int(wr[1])
			and int(gr[2]) == int(wr[2]) and int(gr[3]) == int(wr[3]),
			"touch rect %s (got %s want %s)" % [bid, gr, wr])
	for state_key in touch["visibility"]:
		_expect(HudLayout.touch_visibility(str(state_key)) == touch["visibility"][state_key],
			"touch visibility %s" % state_key)


func _test_structure() -> void:
	# Godot tak punya urutan draw manual (scene tree) — analognya: kehadiran
	# node HUD. (draw_order pygame tercatat di fixture sebagai dokumentasi.)
	for path in ["TopLeft", "GoldChip", "LevelBadge",
			"WaveBanner", "HintLabel", "SkillBar", "ShopPanel"]:
		_expect(_hud.find_child(path, true, false) != null, "HUD has %s" % path)
	_expect(_shop.find_child("Panel", true, false) != null, "ShopPanel has Panel")
	_expect(_shop.find_child("Panel", true, false).mouse_filter == Control.MOUSE_FILTER_STOP,
		"panel menelan klik (itemshop_empty_swallow)")


# ══════════════════════════════════════════════════════════
#  LABEL HUD LIVE
# ══════════════════════════════════════════════════════════

func _test_hud_labels() -> void:
	var topleft: Control = _hud.find_child("TopLeft", true, false)
	_expect(int(topleft.offset_left) == 18 and int(topleft.offset_top) == 22,
		"TopLeft di (18,22)")
	GameManager.gold = 1234567
	GameManager.gold_per_second = 7.125
	GameManager.level_number = 1
	GameManager.wave_number = 13
	GameManager.difficulty = "normal"
	_hud.refresh()
	_expect(_hud.gold_label.text == "1,234,567", "gold ribuan (got %s)" % _hud.gold_label.text)
	_expect(_hud.income_label.text == "+7.1/s", "income (got %s)" % _hud.income_label.text)
	_expect(_hud.level_label.text == "LEVEL 1", "level label")
	_expect(_hud.wave_label.text == "WAVE 13", "wave label")
	GameManager.gold = 0
	GameManager.gold_per_second = 3.0
	GameManager.wave_number = 0


func _test_wave_live() -> void:
	_hud.announce_wave(1)
	_expect(_hud.wave_banner.text == "WAVE 1", "banner title live")
	_expect(_hud._wave_sub.text == "E N E M I E S   I N C O M I N G", "banner subtitle live")
	_expect(_hud._banner_tween != null and _hud._banner_tween.is_valid(), "banner tween jalan")
	_expect(HudLayout.WAVE_TWEEN_IN == 0.4 and HudLayout.WAVE_TWEEN_HOLD == 1.0
		and HudLayout.WAVE_TWEEN_OUT == 0.6, "retime 0.4/1.0/0.6")
	# Fast-forward tween (2.0s) lalu kunci status akhirnya.
	Engine.time_scale = 8.0
	await get_tree().create_timer(2.3).timeout
	Engine.time_scale = 1.0
	_expect(absf(_hud.wave_banner.modulate.a) < 0.01, "banner alpha akhir 0")
	_expect(absf(_hud.wave_banner.offset_left - (-300.0 + 1280.0)) < 1.0,
		"banner x akhir +1280 (got %s)" % _hud.wave_banner.offset_left)


func _test_pause_geometry() -> void:
	_menu.open_pause()
	await get_tree().process_frame
	await get_tree().process_frame
	var panel: Control = _find_node_by_name(_menu, "PausePanel") as Control
	_expect(panel != null, "PausePanel ada")
	if panel == null:
		return
	var rect: Rect2 = panel.get_global_rect()
	_expect(absf(rect.position.x - 440.0) < 2.0 and absf(rect.position.y - 160.0) < 2.0
		and absf(rect.size.x - 400.0) < 2.0 and absf(rect.size.y - 400.0) < 2.0,
		"panel 400x400 @(440,160) (got %s)" % rect)
	var names := ["PauseResume", "PauseSettings", "PauseMenu", "PauseQuit"]
	var order: Array = HudLayout.PAUSE_BUTTON_ORDER
	for i in 4:
		var b: Button = panel.find_child(names[i], true, false)
		_expect(b != null, "tombol pause %s" % order[i])
		if b == null:
			continue
		_expect(absf(b.size.x - 300.0) < 2.0 and absf(b.size.y - 48.0) < 2.0,
			"tombol %s 300x48 (got %s)" % [order[i], b.size])
	# Urutan vertikal = urutan pause pygame.
	var ys: Array = names.map(
		func(n): return panel.find_child(n, true, false).position.y)
	_expect(ys[0] < ys[1] and ys[1] < ys[2] and ys[2] < ys[3], "urutan tombol pause")
	var mode: Label = panel.find_child("PauseMode", true, false)
	_expect(mode != null and "MODE: NORMAL" in mode.text, "mode line pause")
	# Toggle pause bulat: tree beku + menu terlihat, lalu pulih.
	_menu.close()
	_main._toggle_pause()
	_expect(get_tree().paused and _menu.is_open(), "pause bulat")
	_main._toggle_pause()
	_expect(not get_tree().paused and not _menu.is_open(), "resume bulat")


func _find_node_by_name(node: Node, want: String) -> Node:
	if node.name == want:
		return node
	for c in node.get_children():
		var found := _find_node_by_name(c, want)
		if found != null:
			return found
	return null


# ══════════════════════════════════════════════════════════
#  PANEL HERO (SkillBar)
# ══════════════════════════════════════════════════════════

func _test_skillbar_panel() -> void:
	GameManager.gold = 1000000
	_expect(GameManager.try_buy_hero("kaizen"), "beli kaizen")
	var hero = GameManager.owned_heroes()[0]
	GameManager.select_hero(hero)
	_expect(_bar._name_label.text == "Kaizen", "nama panel (got %s)" % _bar._name_label.text)
	_expect(_bar._level_label.text == "Lv.1", "level panel")
	_bar._refresh()
	_expect(_bar._hp_label.text == "%d/%d" % [int(hero.hp), int(hero.max_hp)],
		"HP panel (got %s)" % _bar._hp_label.text)
	_expect(_bar._forge_btn.text == "ITEM FORGE  (0/6)", "forge 0/6")
	_expect(_bar._autocast_btn.text == "AUTO-CAST ON", "autocast ON")
	_bar._autocast_btn.pressed.emit()
	_expect(_bar._autocast_btn.text == "AUTO-CAST ON", "autocast toggle no-op")
	_expect(_bar._upgrade_btn.text == "UPGRADE HERO (300G)",
		"upgrade panel (got %s)" % _bar._upgrade_btn.text)
	# panel_upgrade: tekan -> Lv2, gold -300.
	_bar._upgrade_btn.pressed.emit()
	_expect(int(hero.level) == 2 and GameManager.gold == 1000000 - 400 - 300,
		"upgrade Lv2 -300G (lv=%s gold=%d)" % [hero.level, GameManager.gold])
	_expect(_bar._level_label.text == "Lv.2", "level panel Lv.2")
	# panel_slot0_empty + panel_open_items: chip & tombol forge -> tab item.
	_bar._item_chips[0].pressed.emit()
	_expect(GameManager.shop_open and _shop._tab == "item", "chip -> forge")
	GameManager.close_shop()
	_bar._forge_btn.pressed.emit()
	_expect(GameManager.shop_open and _shop._tab == "item", "ITEM FORGE -> tab item")
	_audit_keys("forge")
	_expect(GameManager.requested_shop_tab == "", "requested dikonsumsi")
	# Angka cooldown per tombol (baterai fixture, via SkillBook sungguhan).
	var cds: Dictionary = _fx["formats"]["cooldown"]
	for fval in cds:
		hero.skill_timer = int(fval)
		hero.w_cooldown = int(fval)
		hero.e_cooldown = int(fval)
		hero.r_cooldown = int(fval)
		var want = "" if cds[fval] == null else str(int(cds[fval]))
		for k in ["q", "w", "e", "r"]:
			_bar._buttons[k].update_state(hero)
			_expect(_bar._buttons[k]._cd_label.text == want,
				"cd %s=%s -> '%s'" % [k, fval, want])
	hero.skill_timer = 0
	hero.w_cooldown = 0
	hero.e_cooldown = 0
	hero.r_cooldown = 0
	# panel_close: X -> deselect, toko tak disentuh.
	_bar._close_btn.pressed.emit()
	_expect(GameManager.selected_hero == null, "X deselect")
	GameManager.select_hero(hero)


# ══════════════════════════════════════════════════════════
#  TOKO HERO
# ══════════════════════════════════════════════════════════

func _test_shop_heroes() -> void:
	GameManager.gold = 100000
	_shop.open_tab("hero")
	_audit_keys("hero")
	_expect(_shop.collect_ui_keys().has("to_hero"), "tab heroes")
	_expect(_shop.collect_ui_keys().has("shop_close"), "tombol tutup")
	_expect(_shop.collect_ui_keys().has("buy_hero_kaizen"), "buy_hero_kaizen")
	_expect(_shop.collect_ui_keys().has("upgrade_hero"), "upgrade_hero (hero dipilih)")
	_expect("1,000,000" not in _shop._gold_label.text, "gold label refresh")
	GameManager.gold = 100000
	_expect("100,000" in _shop._gold_label.text,
		"gold label ribuan (got %s)" % _shop._gold_label.text)
	var kb := _button_by_key("buy_hero_kaizen")
	_expect(kb != null and kb.disabled and kb.text.ends_with("· DIMILIKI"),
		"kaizen DIMILIKI (got %s)" % (kb.text if kb else "?"))
	_expect(str(kb.get_meta("ui_data").get("blocked")) == "OWNED", "OWNED reason")
	SaveManager.data["unlocked_heroes"] = ["kaizen", "grimjaw", "sylara",
		"thorne", "vex", "zephyr"]
	GameManager.bind_purchased_heroes()
	_shop.open_tab("hero")
	# shop_poor: gold 50 -> disabled + POOR (roster belum penuh).
	GameManager.gold = 50
	var gb := _button_by_key("buy_hero_grimjaw")
	_expect(gb != null and gb.disabled
		and str(gb.get_meta("ui_data").get("blocked")) == "POOR", "grimjaw POOR")
	# Beli menutup toko (shop_buy still_open=false).
	GameManager.gold = 1000000
	var before := GameManager.owned_heroes().size()
	var vcost := int(HeroDB.get_hero("vex").get("cost", 400))
	_shop.open_tab("hero")
	_press("buy_hero_grimjaw")
	_press("buy_hero_sylara")
	_press("buy_hero_thorne")
	_shop.open_tab("hero")
	_press("buy_hero_vex")
	_expect(GameManager.owned_heroes().size() == before + 4, "roster +4")
	_expect(not GameManager.shop_open, "shop tutup seusai beli hero")
	_expect(GameManager.gold == 1000000 - 450 - int(HeroDB.get_hero("sylara").get("cost", 400))
		- 500 - vcost, "gold -cost 4 hero")
	# shop_max_case: roster 5/5 -> hero ke-6 MAX + FULL.
	_shop.open_tab("hero")
	var zb := _button_by_key("buy_hero_zephyr")
	_expect(zb != null and zb.disabled and zb.text.ends_with("· MAX"),
		"zephyr MAX (got %s)" % (zb.text if zb else "?"))
	_expect(str(zb.get_meta("ui_data").get("blocked")) == "FULL", "FULL reason")
	# shop_tab analog: tombol tab memindahkan _tab.
	_press("to_item")
	_expect(_shop._tab == "item", "tab -> item")
	_press("to_tower")
	_expect(_shop._tab == "tower", "tab -> tower")
	_press("to_nexus")
	_expect(_shop._tab == "nexus", "tab -> nexus")
	_press("to_hero")
	_expect(_shop._tab == "hero", "tab -> hero")
	GameManager.select_hero(GameManager.owned_heroes()[0])


# ══════════════════════════════════════════════════════════
#  TOKO MENARA (+ TABEL BIAYA)
# ══════════════════════════════════════════════════════════

func _free_blue_slot() -> int:
	for i in GameManager.build_slots.size():
		var s: Dictionary = GameManager.build_slots[i]
		if str(s["team"]) == "blue" and not bool(s["taken"]):
			return i
	return -1


func _test_shop_tower() -> void:
	var rules: Dictionary = _fx["rules"]
	GameManager.gold = 100000
	GameManager.select_slot_index(_free_blue_slot())
	_shop.open_tab("tower")
	_audit_keys("tower-build")
	for tt in TowerDB.tower_types():
		_expect(_shop.collect_ui_keys().has("build_" + str(tt)), "build_%s" % tt)
	# build_archer: +menara, -100G, popup_after null (tutup + clear).
	GameManager.gold = 500
	var n0 := get_tree().get_nodes_in_group("towers").size()
	_press("build_archer")
	_expect(get_tree().get_nodes_in_group("towers").size() == n0 + 1, "menara +1")
	_expect(GameManager.gold == 400, "gold 500-100")
	_expect(not GameManager.shop_open and GameManager.selected_tower == null
		and GameManager.selected_slot == -1, "popup_after null")
	# Lv1: TAK ADA tombol jual; fallback +50 via handler.
	var t1 = GameManager.spawn_tower("blue", Vector2(700, 300), "mid", "outer", "archer", 1)
	GameManager.select_tower(t1)
	_shop.open_tab("tower")
	_audit_keys("tower-L1")
	_expect(not _shop.collect_ui_keys().has("sell_tower"), "Lv1 tanpa tombol jual")
	GameManager.gold = 100
	_press("repath_archer")
	_expect(int(t1.level) == 1 and GameManager.gold == 100,
		"repath gagal saat gold kurang")
	GameManager.gold = 100000
	_expect(GameManager.try_sell_tower(), "jual Lv1 via handler")
	_expect(GameManager.gold == 100000 + 50, "fallback +50G")
	await get_tree().process_frame
	# tower_path: repath archer L1 -> L2 archer -175.
	var t2 = GameManager.spawn_tower("blue", Vector2(700, 300), "mid", "outer", "archer", 1)
	GameManager.select_tower(t2)
	_shop.open_tab("tower")
	_audit_keys("tower-repath")
	_expect(_shop.collect_ui_keys().has("repath_archer"), "repath keys")
	GameManager.gold = 100000 # 100050 seusai jual +50 -> reset sebelum ukur
	_press("repath_archer")
	_expect(str(t2.tower_type) == "archer" and int(t2.level) == 2, "L1->L2 archer")
	_expect(GameManager.gold == 100000 - 175, "repath -175")
	# Tabel upgrade L2..L6 + sell values + regen.
	for lv in [2, 3, 4, 5, 6]:
		_expect(int(t2.upgrade_cost()) == int(rules["tower_upgrade_costs"][str(lv)]),
			"tower cost L%d" % lv)
		_expect(int(t2.sell_value()) == int(rules["tower_sell_values"][str(lv)]),
			"tower sell L%d" % lv)
		var rcost = rules["tower_regen_costs"][str(lv)]
		if rcost == null:
			_expect(not t2.can_activate_regen_shield(), "regen L%d terkunci" % lv)
		else:
			_expect(t2.can_activate_regen_shield(), "regen L%d terbuka" % lv)
			_expect(int(t2.regen_shield_cost()) == int(rcost), "regen 850")
		if int(lv) < 6:
			_expect(GameManager.try_upgrade_tower(""), "upgrade L%d" % lv)
	_shop.open_tab("tower")
	_audit_keys("tower-L6")
	_expect(not _shop.collect_ui_keys().has("upgrade_tower"), "L6 tanpa upgrade")
	_expect(_shop.collect_ui_keys().has("sell_tower"), "L6 ada tombol jual")
	# tower_regen_buy: beli di L6 -> aktif.
	GameManager.gold = 100000
	_press("tower_regen")
	_expect(bool(t2.regen_shield_active), "regen aktif")
	_expect(GameManager.gold == 100000 - 850, "regen -850")
	# tower_sell: jual L6 + regen -> (3200+850)/2 = +2025.
	var g0 := GameManager.gold
	_press("sell_tower")
	_expect(GameManager.gold == g0 + 2025, "jual L6+regen +2025")
	_expect(GameManager.selected_tower == null, "seleksi menara lepas")
	await get_tree().process_frame


# ══════════════════════════════════════════════════════════
#  TOKO NEXUS (+ TABEL BIAYA + NAMA CASTLE)
# ══════════════════════════════════════════════════════════

func _test_shop_nexus() -> void:
	var rules: Dictionary = _fx["rules"]
	for lv in [1, 2, 3, 4, 5]:
		_expect(HudLayout.castle_name(lv) == rules["nexus_names"][str(lv)],
			"castle L%d" % lv)
	_expect(HudLayout.castle_name(6) == "CITADEL", "castle L6+ CITADEL")
	var nx = GameManager.blue_nexus
	_shop.open_tab("nexus")
	_audit_keys("nexus")
	_expect(_shop.collect_ui_keys().has("upgrade_nexus"), "upgrade_nexus")
	# Shield gratis aktif di wave 0 -> tak bisa beli (nexus_L1_free).
	_expect(not nx.can_buy_shield(), "shield gratis wave 0")
	nx.free_shield_active = false
	_shop.open_tab("nexus")
	_expect(_shop.collect_ui_keys().has("nexus_shield"), "nexus_shield buyable")
	GameManager.gold = 100000
	_press("nexus_shield")
	_expect(bool(nx.castle_shield_purchased), "shield purchased")
	_expect(GameManager.gold == 100000 - 850, "shield -850")
	for lv in [1, 2, 3, 4, 5]:
		_expect(int(nx.upgrade_cost()) == int(rules["nexus_upgrade_costs"][str(lv)]),
			"nexus cost L%d" % lv)
		_expect(int(nx.shield_cost()) == int(rules["nexus_shield_costs"][str(lv)]),
			"nexus shield L%d" % lv)
		if int(lv) < 5:
			_expect(GameManager.try_upgrade_nexus(), "nexus upgrade L%d" % lv)
	_shop.open_tab("nexus")
	_expect("ROYAL CASTLE" in _shop._body.get_child(0).text
		or _shop_has_text("ROYAL CASTLE"), "judul castle L5")


func _shop_has_text(fragment: String) -> bool:
	return _find_text_in(_shop._body, fragment)


func _find_text_in(node: Node, fragment: String) -> bool:
	for c in node.get_children():
		if c is Label and fragment in c.text:
			return true
		if _find_text_in(c, fragment):
			return true
	return false


# ══════════════════════════════════════════════════════════
#  TOKO ITEM (gates melee/magic + 33 kunci)
# ══════════════════════════════════════════════════════════

func _test_shop_item() -> void:
	var heroes := {}
	for h in GameManager.owned_heroes():
		heroes[str(h.hero_type)] = h
	var kaizen = heroes["kaizen"]
	var sylara = heroes["sylara"]
	var vex = heroes["vex"]
	GameManager.select_hero(kaizen)
	_shop.open_tab("item")
	_audit_keys("item")
	var keys: Array = _shop.collect_ui_keys()
	var item_keys: Array = keys.filter(func(k): return str(k).begins_with("item_buy_"))
	_expect(item_keys.size() == 33, "33 kunci item (got %d)" % item_keys.size())
	for sid in ItemDB.items.keys():
		_expect(keys.has("item_buy_" + str(sid)), "key %s" % sid)
	# Matriks gates: kaizen melee non-magic, sylara ranged non-magic,
	# vex ranged magic.
	_check_gate(kaizen, "cleave_axe", true, "")
	_check_gate(sylara, "cleave_axe", false, "MELEE ONLY")
	_check_gate(vex, "cleave_axe", false, "MELEE ONLY")
	for sid in ["astral_codex", "fulgur_scepter", "hex_idol", "rift_veil",
			"sage_scepter", "spectral_charm", "vine_rod", "vital_stone"]:
		_check_gate(kaizen, sid, false, "MAGIC ONLY")
		_check_gate(sylara, sid, false, "MAGIC ONLY")
		_check_gate(vex, sid, true, "")
	_check_gate(kaizen, "dead_edge", true, "")
	# Tombol cleave sylara: disabled + tooltip MELEE ONLY.
	GameManager.select_hero(sylara)
	_shop.open_tab("item")
	var cb := _button_by_key("item_buy_cleave_axe")
	_expect(cb != null and cb.disabled and "MELEE ONLY" in cb.tooltip_text,
		"cleave denied sylara")
	# itemshop_buy_click: beli -> -4500, tetap buka.
	GameManager.select_hero(kaizen)
	_shop.open_tab("item")
	GameManager.gold = 100000
	_press("item_buy_dead_edge")
	_expect(GameManager.gold == 100000 - 4500, "item -4500")
	_expect(GameManager.shop_open, "forge tetap buka")
	_expect(kaizen.items.has("dead_edge"), "dead_edge dimiliki")
	var db := _button_by_key("item_buy_dead_edge")
	_expect(db != null and db.disabled and db.text.ends_with("— dimiliki"),
		"owned label (got %s)" % (db.text if db else "?"))
	GameManager.select_hero(kaizen)


func _check_gate(hero, item_id: String, can: bool, reason: String) -> void:
	_expect(hero.items.can_equip(item_id) == can,
		"gate %s x %s" % [hero.hero_type, item_id])
	_expect(hero.items.equip_block_reason(item_id) == reason,
		"reason %s x %s (got %s)" % [hero.hero_type, item_id,
			hero.items.equip_block_reason(item_id)])


# ══════════════════════════════════════════════════════════
#  KLIK DUNIA
# ══════════════════════════════════════════════════════════

func _test_clicks() -> void:
	GameManager.close_shop()
	GameManager.clear_selection()
	var kaizen = null
	for h in GameManager.owned_heroes():
		if str(h.hero_type) == "kaizen":
			kaizen = h
	# world_hero: klik hero biru -> dipilih.
	_main._on_click(kaizen.position)
	_expect(GameManager.selected_hero == kaizen, "world_hero select")
	# world_tower: tanpa seleksi, klik menara biru -> popup (shop tower).
	GameManager.clear_selection()
	var tw = GameManager.spawn_tower("blue", Vector2(750, 250), "mid",
		"outer", "archer", 1)
	_main._on_click(Vector2(750, 250))
	_expect(GameManager.selected_tower == tw, "world_tower select")
	_expect(GameManager.shop_open and _shop._tab == "tower", "world_tower shop")
	# world_build_slot: klik slot kosong -> shop tower.
	GameManager.clear_selection()
	GameManager.close_shop()
	var si := _free_blue_slot()
	var spos: Vector2 = GameManager.build_slots[si]["pos"]
	_main._on_click(spos)
	_expect(GameManager.selected_slot == si, "world_build_slot select")
	_expect(GameManager.shop_open and _shop._tab == "tower", "world_build_slot shop")
	# world_empty_command: hero hidup + tanah kosong -> MOVE, tetap dipilih.
	GameManager.select_hero(kaizen)
	var shop_was_open := GameManager.shop_open
	var empty := _find_empty_point()
	kaizen.set_destination(Vector2.INF, false)
	_main._on_click(empty)
	_expect(GameManager.selected_hero == kaizen, "move tetap dipilih")
	_expect(kaizen.destination == empty, "destination %s" % [empty])
	_expect(GameManager.shop_open == shop_was_open, "toko tak tersentuh move")
	# Menara merah tanpa seleksi -> tak dipilih (paritas step 7: blue-only).
	GameManager.clear_selection()
	var rt = GameManager.spawn_tower("red", _find_empty_point(), "mid",
		"outer", "archer", 1)
	_main._on_click(rt.position)
	_expect(GameManager.selected_tower == null and GameManager.selected_hero == null,
		"menara merah tak dipilih")
	# Click tower biru saat hero dipilih -> pindah ke menara (step 6).
	GameManager.select_hero(kaizen)
	_main._on_click(tw.position)
	_expect(GameManager.selected_tower == tw and GameManager.selected_hero == null,
		"switch hero -> tower")
	# popup_close analog: tanah kosong tanpa hero -> clear + tutup.
	GameManager.clear_selection()
	GameManager.select_tower(tw)
	GameManager.open_shop()
	_main._on_click(_find_empty_point())
	_expect(GameManager.selected_tower == null and not GameManager.shop_open,
		"empty clear+close")
	# world_empty_dead_deselect: hero mati + kosong -> None.
	GameManager.select_hero(kaizen)
	kaizen.die()
	_main._on_click(_find_empty_point())
	_expect(GameManager.selected_hero == null, "dead deselect")
	# world_rightclick: tutup toko + MOVE.
	var sylara = null
	for h in GameManager.owned_heroes():
		if str(h.hero_type) == "sylara":
			sylara = h
	GameManager.select_hero(sylara)
	GameManager.open_shop()
	var rp := _find_empty_point()
	_main._on_right_click(rp)
	_expect(sylara.destination == rp, "rightclick move")
	_expect(not GameManager.shop_open, "rightclick tutup toko")
	GameManager.select_hero(sylara)


func _find_empty_point() -> Vector2:
	var avoid: Array = []
	for s in GameManager.build_slots:
		avoid.append(s["pos"])
	for n in [GameManager.blue_nexus, GameManager.red_nexus]:
		if n != null and is_instance_valid(n):
			avoid.append(n.position)
	for h in get_tree().get_nodes_in_group("heroes"):
		if is_instance_valid(h):
			avoid.append((h as Node2D).position)
	for t in get_tree().get_nodes_in_group("towers"):
		if is_instance_valid(t):
			avoid.append((t as Node2D).position)
	var y := 120.0
	while y < 680.0:
		var x := 60.0
		while x < 1240.0:
			var p := Vector2(x, y)
			var ok := true
			for a in avoid:
				if p.distance_to(a) < 70.0:
					ok = false
					break
			if ok:
				return p
			x += 40.0
		y += 40.0
	return Vector2(640, 360)


# ══════════════════════════════════════════════════════════
#  HOTKEY (playing) + SKOR/KILL
# ══════════════════════════════════════════════════════════

func _test_hotkeys_playing() -> void:
	GameManager.close_shop()
	_main._on_key(_key(KEY_H))
	_expect(GameManager.shop_open, "H buka toko")
	_main._on_key(_key(KEY_H))
	_expect(not GameManager.shop_open, "H tutup toko (toggle)")
	# FASE 18: B kini paritas pygame (oracle ui_hud.hotkeys.b → hold_start
	# attack_boss, shop tidak tersentuh) — "B = toko" (ekstensi Godot lama)
	# dihapus bersama binding FASE 18.
	_main._on_key(_key(KEY_B))
	_expect(not GameManager.shop_open, "B = perintah taktis (bukan toko)")
	var _tac = _main._tactical
	_expect(_tac.hold_active() and str(_tac.held_command) == "attack_boss",
		"B menahan attack_boss (boss tak ada → hold dipersenjatai)")
	_main._on_key(_keyup(KEY_B))
	_expect(not _tac.hold_active(), "lepas B melepas hold")
	_main._on_key(_key(KEY_N))
	_expect(GameManager.state == "playing", "N saat playing diam")
	_main._on_key(_key(KEY_R))
	_expect(GameManager.state == "playing", "R saat playing = skill (tak replay)")
	# Skor/kill (FASE 15: register_minion_death/register_tower_death —
	# cabang TIM KORBAN _core.py:2196-2227, bukan lagi award_kill killer):
	# minion merah menambah skor+total_kills, menara merah menambah skor
	# TANPA kill, minion biru membayar AI saja (skor pemain diam).
	GameManager.gold = 1000
	GameManager.score = 0
	GameManager.total_kills = 0
	var red_minion = MinionScene.instantiate()
	red_minion.minion_type = "goblin"
	red_minion.team = "red"
	red_minion.position = Vector2(1500, 700)
	add_child(red_minion)
	red_minion.set_physics_process(false)
	var minion_gold := int(red_minion.gold_reward)
	GameManager.register_minion_death(red_minion)
	_expect(GameManager.score == minion_gold and GameManager.total_kills == 1
		and GameManager.gold == 1000 + minion_gold, "reward minion merah")
	var red_tower = TowerScene.instantiate()
	red_tower.team = "red"
	red_tower.position = Vector2(1560, 700)
	add_child(red_tower)
	red_tower.set_physics_process(false)
	var tower_gold := int(red_tower.gold_reward)
	GameManager.register_tower_death(red_tower)
	_expect(GameManager.score == minion_gold + tower_gold
		and GameManager.total_kills == 1, "tower menambah skor tanpa kill")
	var blue_minion = MinionScene.instantiate()
	blue_minion.minion_type = "goblin"
	blue_minion.team = "blue"
	blue_minion.position = Vector2(1620, 700)
	add_child(blue_minion)
	blue_minion.set_physics_process(false)
	var ai_gold_before := GameManager.ai_gold
	GameManager.register_minion_death(blue_minion)
	_expect(GameManager.score == minion_gold + tower_gold
		and GameManager.total_kills == 1
		and GameManager.ai_gold == ai_gold_before
		+ int(blue_minion.gold_reward), "minion biru membayar AI saja")
	red_minion.free()
	red_tower.free()
	blue_minion.free()


# ══════════════════════════════════════════════════════════
#  GAME OVER (victory/defeat/last + N/R/ESC)
# ══════════════════════════════════════════════════════════

func _pin_end_state() -> void:
	GameManager.score = 7777
	GameManager.total_kills = 4242
	GameManager.wave_number = 13
	GameManager.match_start_msec = Time.get_ticks_msec() - 3723 * 1000


func _test_gameover() -> void:
	# ── victory L1: judul/stat/unlock/newhero/next ──
	SaveManager.data["completed_levels"] = []
	SaveManager.data["unlocked_heroes"] = ["kaizen", "grimjaw", "sylara",
		"thorne", "vex", "zephyr"]
	GameManager.bosses_defeated_this_match = ["abaddon"]
	_pin_end_state()
	GameManager.end_match(true)
	_expect(GameManager.state == "victory", "state victory")
	_expect(GameManager.heroes_unlocked_this_match == ["abaddon"],
		"unlock data (got %s)" % [GameManager.heroes_unlocked_this_match])
	_expect(_hud._over_title.text == "VICTORY! LV.1",
		"judul victory (got %s)" % _hud._over_title.text)
	_expect("Final Score: 7,777" in _hud._over_stats.text, "stat score")
	_expect("Match Time: 62:03" in _hud._over_stats.text,
		"stat time (got %s)" % _hud._over_stats.text)
	_expect("Waves Survived: 13" in _hud._over_stats.text, "stat wave")
	_expect("Total Kills: 4242" in _hud._over_stats.text, "stat kill")
	_expect("NEW LEVEL UNLOCKED!" in _hud._over_body.text, "unlock line")
	var ab_name := str(HeroDB.get_hero("abaddon").get("name", "abaddon"))
	_expect(("NEW HERO: " + ab_name) in _hud._over_body.text,
		"new hero line (got %s)" % _hud._over_body.text)
	_expect(_hud._next_button.visible, "next visible L1")
	# victory_L1_n: N -> level 2.
	_main._on_key(_key(KEY_N))
	_expect(GameManager.level_number == 2 and GameManager.state == "playing",
		"N -> level 2")
	await get_tree().process_frame
	_main._on_key(_key(KEY_SPACE))
	await get_tree().process_frame
	# ── defeat L2: judul + replay; N diam ──
	_pin_end_state()
	GameManager.end_match(false)
	_expect(_hud._over_title.text == "DEFEAT LV.2", "judul defeat")
	_expect(not _hud._next_button.visible, "next hidden defeat")
	_main._on_key(_key(KEY_N))
	_expect(GameManager.state == "defeat", "N saat defeat diam")
	# defeat r: R -> replay level sama.
	_main._on_key(_key(KEY_R))
	_expect(GameManager.level_number == 2 and GameManager.state == "playing",
		"R replay L2")
	await get_tree().process_frame
	_main._on_key(_key(KEY_SPACE))
	await get_tree().process_frame
	# ── victory L2 -> ESC menu ──
	_pin_end_state()
	GameManager.end_match(true)
	_main._on_key(_key(KEY_ESCAPE))
	_expect(GameManager.in_menu and GameManager.state == "idle", "ESC -> menu")
	# ── victory L54: next hidden; N diam; overlay_next_level via tombol ──
	_menu.close()
	GameManager.start_level(54)
	await get_tree().process_frame
	await get_tree().process_frame
	_main._on_key(_key(KEY_SPACE))
	await get_tree().process_frame
	_pin_end_state()
	GameManager.end_match(true)
	_expect(_hud._over_title.text == "VICTORY! LV.54", "judul last")
	_expect(not _hud._next_button.visible, "next hidden last")
	_expect("NEW LEVEL UNLOCKED!" not in _hud._over_body.text, "last tanpa unlock")
	_main._on_key(_key(KEY_N))
	_expect(GameManager.level_number == 54 and GameManager.state == "victory",
		"N last diam")
	# victory L1 ulang -> tombol LANJUT = overlay_next_level.
	_menu.close()
	GameManager.start_level(1)
	await get_tree().process_frame
	_main._on_key(_key(KEY_SPACE))
	await get_tree().process_frame
	SaveManager.data["completed_levels"] = [1]
	_pin_end_state()
	GameManager.end_match(true)
	_hud._next_button.pressed.emit()
	_expect(GameManager.level_number == 2 and GameManager.state == "playing",
		"tombol LANJUT -> level 2")
	await get_tree().process_frame
	_main._on_key(_key(KEY_SPACE))
	await get_tree().process_frame


# ══════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════

## Audit closed-world: tiap ui_key yang tampil harus ada di semesta
## HudLayout.shop_ui_keys() dan tak boleh ganda di satu layar.
func _audit_keys(context: String) -> void:
	if _universe.is_empty():
		var spec: Dictionary = HudLayout.shop_ui_keys()
		_universe.append_array(spec["tabs"])
		_universe.append_array(spec["hero_selected"])
		_universe.append_array(spec["tower_selected"])
		_universe.append_array(spec["nexus"])
		for group in ["heroes", "tower_build", "tower_repath", "item"]:
			var g: Dictionary = spec[group]
			for entry in g["source"]:
				_universe.append(str(g["prefix"]) + str(entry))
	var keys: Array = _shop.collect_ui_keys()
	var seen := {}
	for k in keys:
		_expect(_universe.has(k), "key dikenal %s (%s)" % [k, context])
		_expect(not seen.has(k), "key unik %s (%s)" % [k, context])
		seen[k] = true


func _button_by_key(ui_key: String) -> Button:
	return _find_button_in(_shop, ui_key)


func _find_button_in(node: Node, ui_key: String) -> Button:
	for c in node.get_children():
		if c is Button and c.has_meta("ui_key") and str(c.get_meta("ui_key")) == ui_key:
			return c
		var found := _find_button_in(c, ui_key)
		if found != null:
			return found
	return null


func _press(ui_key: String) -> void:
	var b := _button_by_key(ui_key)
	_expect(b != null, "tombol %s ada" % ui_key)
	if b != null:
		b.pressed.emit()


func _key(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = true
	return event


func _keyup(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = false
	return event


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		# print() ke stdout: grep FAIL-LINES di CI menangkap "FAIL" (push_error
		# hanya menulis "ERROR:" yang tak cocok pola anotasi).
		print("[UiHudParityTest] FAIL: " + message)
		push_error("[UiHudParityTest] " + message)


func _finish() -> void:
	get_tree().paused = false
	Engine.time_scale = 1.0
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager._hero_respawn_timers.clear()
	GameManager._reset_wave_state()
	_main.free()
	SaveManager.data = _save_before
	if _save_file_before == null:
		if FileAccess.file_exists(SaveManager.SAVE_PATH):
			DirAccess.remove_absolute(SaveManager.SAVE_PATH)
	else:
		var f := FileAccess.open(SaveManager.SAVE_PATH, FileAccess.WRITE)
		f.store_string(_save_file_before)
	GameManager.set_process(true)
	if _failures == 0:
		print("[UiHudParityTest] PASS: %d checks UI/HUD vs oracle pygame" % _checks)
	else:
		print("[UiHudParityTest] FAIL: %d/%d checks gagal" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
