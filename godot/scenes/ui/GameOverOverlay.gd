# GameOverOverlay.gd — layar VICTORY / DEFEAT (port Overlay.draw 1:1).
#
# Backdrop gelap + 12 ray berputar + glow pusat + judul Cinzel 88 berdenyut
# + sparkle (victory) + panel stat 500px (5 baris + badge NEW BEST) + popup
# unlock 340x220 (delay 90 frame, slide ease-out-cubic) + hint keycap +
# hitungan achievement + tombol aksi mouse/touch.
#
# Teks audit test (MatchScoringParityTest/UiHudParityTest) dipertahankan
# PERSIS di label tersembunyi title_label/stats_label/body_label; HUD
# mengalasinya sebagai _over_title/_over_stats/_over_body.
extends Control
class_name GameOverOverlay

signal menu_requested

const STATS_W := 500.0
const ROW_H := 38.0
const POPUP_W := 340.0
const POPUP_H := 220.0
const POPUP_DELAY_FRAMES := 90
const POPUP_SLIDE_FRAMES := 30

var victory: bool = false
var accent: Color = UiTheme.GOLD

var title_label: Label = null   # audit (tersembunyi)
var stats_label: Label = null   # audit (tersembunyi)
var body_label: Label = null    # audit (tersembunyi)
var stats_panel: PygamePanel = null
var next_button: PygameButton = null

var _fx: _BackFx = null
var _title_fx: _TitleFx = null
var _stats_box: VBoxContainer = null
var _popup: PygamePanel = null
var _popup_body: Control = null
var _popup_frame: int = 0
var _popup_shown: bool = false
var _popup_tween: Tween = null
var _hint_row: HBoxContainer = null
var _ach_row: HBoxContainer = null
var _intro_tween: Tween = null
var _badge_tweens: Array = []


func _ready() -> void:
	name = "GameOverOverlay"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	_build()


func _build() -> void:
	var dim := ColorRect.new()
	dim.color = Color(10.0 / 255.0, 10.0 / 255.0, 20.0 / 255.0,
		180.0 / 255.0)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)

	_fx = _BackFx.new()
	_fx.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fx.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_fx)

	_title_fx = _TitleFx.new()
	_title_fx.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_title_fx.anchor_left = 0.5
	_title_fx.anchor_right = 0.5
	_title_fx.anchor_top = 0.5
	_title_fx.anchor_bottom = 0.5
	_title_fx.offset_left = -500.0
	_title_fx.offset_right = 500.0
	_title_fx.offset_top = -180.0 - 70.0
	_title_fx.offset_bottom = -180.0 + 70.0
	add_child(_title_fx)

	# Label audit tersembunyi (teks PERSIS format lama).
	title_label = Label.new()
	title_label.visible = false
	add_child(title_label)
	stats_label = Label.new()
	stats_label.visible = false
	add_child(stats_label)
	body_label = Label.new()
	body_label.visible = false
	add_child(body_label)


func hide_overlay() -> void:
	visible = false
	_popup_frame = 0
	_popup_shown = false
	if _popup_tween != null and _popup_tween.is_valid():
		_popup_tween.kill()
	if _intro_tween != null and _intro_tween.is_valid():
		_intro_tween.kill()
	if _fx != null:
		_fx.set_process(false)
	if _title_fx != null:
		_title_fx.set_process(false)
	set_process(false)


## Tampilkan hasil match. Teks + logika visibilitas = 1:1 HUD._on_game_over
## lama (dikunci MatchScoringParityTest + UiHudParityTest).
func show_result(p_victory: bool) -> void:
	victory = p_victory
	accent = Color(1.0, 0.9, 0.45) if victory else Color(1.0, 0.45, 0.45)
	_fx.accent = accent
	_fx.victory = victory
	_fx.set_process(true)
	_title_fx.set_process(true)
	_popup_frame = 0
	_popup_shown = false
	for t in _badge_tweens:
		if is_instance_valid(t):
			(t as Tween).kill()
	_badge_tweens.clear()

	# ── judul audit + visual ──
	title_label.text = "%s LV.%d" % [
		"VICTORY!" if victory else "DEFEAT", GameManager.level_number]
	_title_fx.title_text = title_label.text
	_title_fx.victory = victory

	# ── stat audit (5 baris PERSIS) ──
	var rows: Array = [
		["Final Score", HudLayout.format_thousands(GameManager.score),
			GameManager.new_best_score],
		["Match Time", HudLayout.format_match_time(
			GameManager.match_time_seconds()), GameManager.new_best_time],
		["Waves Survived", str(GameManager.wave_number), false],
		["Total Kills", str(GameManager.total_kills), false],
		["Max Combo", "x%d" % GameManager.max_combo, false],
	]
	var stat_lines: PackedStringArray = PackedStringArray()
	for row in rows:
		var line := "%s: %s" % [row[0], row[1]]
		if row[2]:
			line += "  NEW BEST!"
		stat_lines.append(line)
	stats_label.text = "\n".join(stat_lines)

	# ── body audit (reward + unlock + hero PERSIS) ──
	var reward: int = GameManager.meta_reward_earned
	var replay_txt := ""
	if victory:
		if reward >= 3000:
			replay_txt = "menang pertama"
		elif reward >= 1500:
			replay_txt = "replay pertama"
		else:
			replay_txt = "replay berulang"
	var lines: Array = []
	if victory:
		lines.append("Meta reward: +%d gold (%s) tersimpan ke save." % [reward, replay_txt])
	else:
		lines.append("Nexus Radiant hancur — kalah tidak dibayar.")
	var nxt := GameManager.next_level_number()
	if victory and nxt > 0 and not SaveManager.is_level_completed(nxt):
		lines.append("NEW LEVEL UNLOCKED!")
	var new_heroes: Array = GameManager.heroes_unlocked_this_match
	if victory and not new_heroes.is_empty():
		var names: Array = []
		for bt in new_heroes:
			names.append(str(HeroDB.get_hero(str(bt)).get("name", str(bt))))
		lines.append("NEW HERO: %s" % ", ".join(names))
	body_label.text = "\n".join(lines)

	# ── bangun ulang visual dinamis ──
	_build_stats_panel(rows)
	_build_popup(nxt)
	_build_hint(nxt)
	_build_achievements()
	_build_actions(nxt)

	visible = true
	set_process(victory and _popup != null)
	# Intro: fade + scale BACK OUT pada panel stat (rasa lama dipertahankan).
	if stats_panel != null:
		stats_panel.pivot_offset = stats_panel.size / 2.0
		stats_panel.scale = Vector2(0.85, 0.85)
		stats_panel.modulate.a = 0.0
		if _intro_tween != null and _intro_tween.is_valid():
			_intro_tween.kill()
		_intro_tween = create_tween()
		_intro_tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		_intro_tween.set_parallel(true)
		_intro_tween.tween_property(stats_panel, "modulate:a", 1.0, 0.3)
		_intro_tween.tween_property(stats_panel, "scale", Vector2.ONE, 0.35)


func _process(_delta: float) -> void:
	# Delay popup 90 frame lalu slide-in (paritas unlock_popup_timer).
	if _popup_shown or _popup == null:
		set_process(false)
		return
	_popup_frame += 1
	if _popup_frame >= POPUP_DELAY_FRAMES:
		_popup_shown = true
		set_process(false)
		_popup.visible = true
		var base_x := _popup.position.x
		_popup.position.x = base_x + 400.0
		_popup.modulate.a = 0.0
		if _popup_tween != null and _popup_tween.is_valid():
			_popup_tween.kill()
		_popup_tween = create_tween()
		_popup_tween.set_parallel(true)
		_popup_tween.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		_popup_tween.tween_property(_popup, "position:x", base_x, 0.5)
		_popup_tween.tween_property(_popup, "modulate:a", 1.0, 0.25)


# ── PANEL STAT ──

func _build_stats_panel(rows: Array) -> void:
	if stats_panel != null and is_instance_valid(stats_panel):
		stats_panel.queue_free()
	stats_panel = PygamePanel.new(accent, 2.0, 10.0)
	stats_panel.name = "GameOverPanel"
	stats_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	stats_panel.anchor_left = 0.5
	stats_panel.anchor_right = 0.5
	stats_panel.anchor_top = 0.5
	stats_panel.anchor_bottom = 0.5
	var h := rows.size() * ROW_H + 24.0
	stats_panel.offset_left = -STATS_W * 0.5
	stats_panel.offset_right = STATS_W * 0.5
	stats_panel.offset_top = -100.0
	stats_panel.offset_bottom = -100.0 + h
	stats_panel.configure(Color(30.0 / 255.0, 34.0 / 255.0, 58.0 / 255.0),
		Color(14.0 / 255.0, 16.0 / 255.0, 30.0 / 255.0),
		accent, 2.0, 10.0, true, true)
	stats_panel.ticks_color = UiTheme.GOLD_BRIGHT
	stats_panel.set_margins(20, 15, 20, 9)
	add_child(stats_panel)
	_stats_box = VBoxContainer.new()
	_stats_box.add_theme_constant_override("separation", 6)
	_stats_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stats_panel.add_child(_stats_box)
	for row in rows:
		_stats_box.add_child(_stat_row(str(row[0]), str(row[1]),
			bool(row[2])))


func _stat_row(label: String, value: String, is_new_best: bool) -> Control:
	var row := HBoxContainer.new()
	row.custom_minimum_size = Vector2(0, 32)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lab := Label.new()
	UiTheme.style_label(lab, label, UiTheme.body_semibold(), 22,
		Color(180.0 / 255.0, 180.0 / 255.0, 200.0 / 255.0))
	lab.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(lab)
	if is_new_best:
		row.add_child(_new_best_badge())
	var val := Label.new()
	UiTheme.style_label(val, value, UiTheme.body_semibold(), 26,
		Color(1.0, 220.0 / 255.0, 100.0 / 255.0) if is_new_best else accent,
		HORIZONTAL_ALIGNMENT_RIGHT)
	row.add_child(val)
	return row


func _new_best_badge() -> Control:
	var badge := PanelContainer.new()
	badge.custom_minimum_size = Vector2(118, 22)
	badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(200.0 / 255.0, 150.0 / 255.0, 30.0 / 255.0)
	sb.border_color = Color(1.0, 1.0, 200.0 / 255.0)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 6.0
	sb.content_margin_right = 6.0
	sb.content_margin_top = 1.0
	sb.content_margin_bottom = 1.0
	badge.add_theme_stylebox_override("panel", sb)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 4)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	badge.add_child(row)
	row.add_child(VectorIcon.new("star", Color(80.0 / 255.0, 40.0 / 255.0, 0.0), 0.45))
	var t := Label.new()
	UiTheme.style_label(t, "NEW BEST!", UiTheme.body_semibold(), 15,
		Color(80.0 / 255.0, 40.0 / 255.0, 0.0))
	row.add_child(t)
	# Denyut badge.
	var tw := create_tween().set_loops()
	tw.set_trans(Tween.TRANS_SINE)
	tw.tween_property(badge, "modulate:a", 0.55, 0.4)
	tw.tween_property(badge, "modulate:a", 1.0, 0.4)
	_badge_tweens.append(tw)
	return badge


# ── POPUP UNLOCK ──

func _build_popup(nxt: int) -> void:
	if _popup != null and is_instance_valid(_popup):
		_popup.queue_free()
	_popup = null
	_popup_body = null
	var show := victory and nxt > 0 \
		and not SaveManager.is_level_completed(nxt)
	if not show:
		return
	var cfg: Dictionary = BossDB.get_level(nxt)
	if cfg.is_empty():
		return
	_popup = PygamePanel.new(Color(1.0, 220.0 / 255.0, 100.0 / 255.0),
		3.0, 12.0)
	_popup.visible = false
	_popup.mouse_filter = Control.MOUSE_FILTER_STOP
	_popup.anchor_left = 0.5
	_popup.anchor_right = 0.5
	_popup.anchor_top = 0.5
	_popup.anchor_bottom = 0.5
	_popup.offset_left = 220.0
	_popup.offset_right = 220.0 + POPUP_W
	_popup.offset_top = -100.0
	_popup.offset_bottom = -100.0 + POPUP_H
	_popup.configure(Color(40.0 / 255.0, 30.0 / 255.0, 10.0 / 255.0),
		Color(60.0 / 255.0, 45.0 / 255.0, 15.0 / 255.0),
		Color(1.0, 220.0 / 255.0, 100.0 / 255.0), 3.0, 12.0, false, true)
	_popup.set_margins(15, 10, 15, 10)
	add_child(_popup)
	_popup_body = Control.new()
	_popup_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_popup.add_child(_popup_body)
	_build_popup_content(nxt, cfg)


func _popup_label(text: String, size: int, color: Color,
		pos: Vector2, bold: bool = false) -> Label:
	var l := Label.new()
	UiTheme.style_label(l, text,
		UiTheme.body_bold() if bold else UiTheme.body_semibold(),
		size, color)
	l.position = pos
	_popup_body.add_child(l)
	return l


func _build_popup_content(nxt: int, cfg: Dictionary) -> void:
	var boss_type := str(cfg.get("true_boss", "abaddon"))
	var bdata: Dictionary = BossDB.get_boss(boss_type)
	var boss_name := str(bdata.get("name", "???"))
	var boss_class := str(bdata.get("boss_class", "true"))
	var boss_col := _parse_color(bdata.get("color",
		Color(150.0 / 255.0, 100.0 / 255.0, 200.0 / 255.0)),
		Color(150.0 / 255.0, 100.0 / 255.0, 200.0 / 255.0))
	var entrance := _parse_color(bdata.get("entrance_color", boss_col),
		boss_col)
	# Gembok terbuka + judul.
	var lock := VectorIcon.new("lock", Color(100.0 / 255.0, 255.0 / 255.0,
		100.0 / 255.0), 1.2)
	lock.position = Vector2(8, 6)
	lock.custom_minimum_size = Vector2(32, 32)
	_popup_body.add_child(lock)
	_popup_label("NEW LEVEL UNLOCKED!", 22,
		Color(1.0, 220.0 / 255.0, 100.0 / 255.0), Vector2(50, 2))
	_popup_label("LEVEL %d" % nxt, 24, Color.WHITE, Vector2(50, 26))
	_popup_label(str(cfg.get("name", "")), 18,
		Color(200.0 / 255.0, 200.0 / 255.0, 220.0 / 255.0), Vector2(50, 52))
	# Separator.
	var sep := HSeparator.new()
	sep.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sep.anchor_left = 0.0
	sep.anchor_right = 1.0
	sep.offset_top = 76.0
	sep.offset_bottom = 78.0
	UiTheme.style_separator(sep, Color(1.0, 220.0 / 255.0, 100.0 / 255.0))
	_popup_body.add_child(sep)
	# Siluet boss.
	var sil := _BossSilhouette.new(entrance, boss_col, boss_class)
	sil.position = Vector2(8, 88)
	sil.size = Vector2(90, 80)
	_popup_body.add_child(sil)
	# Info boss.
	_popup_label("FINAL BOSS", 16, Color(1.0, 100.0 / 255.0,
		100.0 / 255.0), Vector2(100, 90))
	_popup_label(UiTheme.fit_ellipsis(UiTheme.body_semibold(), 24,
		boss_name, 195), 24, entrance, Vector2(100, 108))
	var diff := GameManager.difficulty
	var diff_text := "NORMAL"
	var diff_col := Color(100.0 / 255.0, 220.0 / 255.0, 150.0 / 255.0)
	var diff_level := 1
	if diff == "hard":
		diff_text = "HARD"
		diff_col = Color(1.0, 120.0 / 255.0, 100.0 / 255.0)
		var mult := float(cfg.get("enemy_hp_mult", 1.0))
		diff_level = mini(5, maxi(1, int(mult * 2.5)))
	elif diff == "easy":
		diff_text = "EASY"
		diff_col = Color(100.0 / 255.0, 210.0 / 255.0, 1.0)
	_popup_label(diff_text, 15, diff_col, Vector2(100, 136))
	var pips := DiffPips.new(diff_level, 10, 8, 4)
	pips.position = Vector2(100, 156)
	_popup_body.add_child(pips)
	# Tombol PLAY NEXT LEVEL.
	var play := PygameButton.pill_button("PLAY NEXT LEVEL", "success",
		"play", POPUP_W - 30, 30, 20)
	play.position = Vector2(0, POPUP_H - 50)
	play.pressed.connect(func(): GameManager.next_level())
	_popup_body.add_child(play)


func _parse_color(v, fallback: Color) -> Color:
	if v is Color:
		return v
	if v is String and str(v) != "":
		return Color(str(v))
	if v is Array and (v as Array).size() >= 3:
		var a: Array = v
		return Color(float(a[0]) / 255.0, float(a[1]) / 255.0,
			float(a[2]) / 255.0)
	return fallback


# ── HINT + ACHIEVEMENT + AKSI ──

func _build_hint(nxt: int) -> void:
	if _hint_row != null and is_instance_valid(_hint_row):
		_hint_row.queue_free()
	_hint_row = HBoxContainer.new()
	_hint_row.alignment = BoxContainer.ALIGNMENT_CENTER
	_hint_row.add_theme_constant_override("separation", 16)
	_hint_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hint_row.anchor_left = 0.5
	_hint_row.anchor_right = 0.5
	_hint_row.anchor_top = 0.5
	_hint_row.anchor_bottom = 0.5
	_hint_row.offset_left = -500.0
	_hint_row.offset_right = 500.0
	_hint_row.offset_top = 200.0 - 18.0
	_hint_row.offset_bottom = 200.0 + 18.0
	add_child(_hint_row)
	if victory and nxt > 0:
		_hint_row.add_child(_key_hint("ENTER", "lanjut level"))
	_hint_row.add_child(_key_hint("R", "ulangi"))
	_hint_row.add_child(_key_hint("ESC", "menu utama"))
	if victory and nxt <= 0:
		var plain := Label.new()
		UiTheme.style_label(plain, "(You cleared all levels!)",
			UiTheme.body_semibold(), 20,
			Color(150.0 / 255.0, 156.0 / 255.0, 180.0 / 255.0))
		plain.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		_hint_row.add_child(plain)


func _key_hint(key: String, desc: String) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var cap := PanelContainer.new()
	cap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(48.0 / 255.0, 52.0 / 255.0, 70.0 / 255.0)
	sb.border_color = Color(140.0 / 255.0, 150.0 / 255.0, 175.0 / 255.0)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 9.0
	sb.content_margin_right = 9.0
	sb.content_margin_top = 4.0
	sb.content_margin_bottom = 4.0
	cap.add_theme_stylebox_override("panel", sb)
	row.add_child(cap)
	var k := Label.new()
	UiTheme.style_label(k, key, UiTheme.body_bold(), 22,
		Color(1.0, 235.0 / 255.0, 140.0 / 255.0))
	cap.add_child(k)
	var d := Label.new()
	UiTheme.style_label(d, desc, UiTheme.body_semibold(), 20,
		Color(205.0 / 255.0, 210.0 / 255.0, 225.0 / 255.0))
	d.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(d)
	return row


func _build_achievements() -> void:
	if _ach_row != null and is_instance_valid(_ach_row):
		_ach_row.queue_free()
	_ach_row = HBoxContainer.new()
	_ach_row.alignment = BoxContainer.ALIGNMENT_CENTER
	_ach_row.add_theme_constant_override("separation", 8)
	_ach_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ach_row.anchor_left = 0.0
	_ach_row.anchor_right = 1.0
	_ach_row.anchor_top = 0.5
	_ach_row.anchor_bottom = 0.5
	_ach_row.offset_top = 250.0 - 14.0
	_ach_row.offset_bottom = 250.0 + 14.0
	add_child(_ach_row)
	var n_ach := 0
	if GameManager.achievements_unlocked is Dictionary:
		n_ach = (GameManager.achievements_unlocked as Dictionary).size()
	if n_ach <= 0:
		_ach_row.visible = false
		return
	_ach_row.add_child(VectorIcon.new("trophy",
		Color(1.0, 220.0 / 255.0, 50.0 / 255.0), 0.7))
	var t := Label.new()
	UiTheme.style_label(t, "%d Achievements Unlocked!" % n_ach,
		UiTheme.body_semibold(), 20, Color(1.0, 220.0 / 255.0, 50.0 / 255.0))
	_ach_row.add_child(t)


func _build_actions(nxt: int) -> void:
	if next_button != null and is_instance_valid(next_button):
		next_button.queue_free()
	next_button = null
	# Bersihkan baris aksi lama (tag via grup).
	for c in get_children():
		if c is HBoxContainer and c.has_meta("actions_row"):
			c.queue_free()
	var row := HBoxContainer.new()
	row.set_meta("actions_row", true)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.anchor_left = 0.0
	row.anchor_right = 1.0
	row.anchor_top = 0.5
	row.anchor_bottom = 0.5
	row.offset_top = 292.0 - 18.0
	row.offset_bottom = 292.0 + 18.0
	add_child(row)
	next_button = PygameButton.pill_button(
		"LANJUT KE LEVEL %d  (ENTER)" % maxi(nxt, 1), "success", "play",
		260, 36, 17)
	next_button.visible = victory and nxt > 0
	next_button.pressed.connect(func(): GameManager.next_level())
	row.add_child(next_button)
	var replay := PygameButton.pill_button("ULANGI  (R)", "gold", "",
		150, 36, 17)
	replay.pressed.connect(func(): GameManager.restart_match())
	row.add_child(replay)
	var menu_btn := PygameButton.pill_button("MENU UTAMA  (ESC)",
		"neutral", "", 190, 36, 17)
	menu_btn.pressed.connect(func(): menu_requested.emit())
	row.add_child(menu_btn)


# ══════════════════════════════════════════════════════════
#  FX KHUSUS (inner class — ray, judul, siluet boss)
# ══════════════════════════════════════════════════════════

## Ray berputar + glow pusat + sparkle victory.
class _BackFx extends Control:
	var accent: Color = UiTheme.GOLD
	var victory: bool = false
	var t: float = 0.0

	func _init() -> void:
		set_process(false)

	func _process(delta: float) -> void:
		t += delta * 20.0 * 0.05
		queue_redraw()

	func _notification(what: int) -> void:
		if what == NOTIFICATION_RESIZED:
			queue_redraw()

	func _draw() -> void:
		var cx := size.x * 0.5
		var cy := size.y * 0.5
		# 12 ray berputar.
		for i in range(12):
			var angle := (float(i) / 12.0) * TAU + t * 0.3
			var ray_len := 400.0 + sin(t + float(i)) * 50.0
			var tip := Vector2(cx, cy) + Vector2(cos(angle),
				sin(angle)) * ray_len
			var perp := angle + PI * 0.5
			var off := Vector2(cos(perp), sin(perp)) * 30.0
			draw_colored_polygon(PackedVector2Array([
				Vector2(cx, cy), tip + off, tip - off]),
				Color(accent.r, accent.g, accent.b, 30.0 / 255.0))
		# Glow pusat (lingkaran konsentris).
		var r := 200.0
		while r > 50.0:
			var a := (200.0 - r) / 200.0 * 60.0 / 255.0
			draw_circle(Vector2(cx, cy), r,
				Color(accent.r, accent.g, accent.b, a))
			r -= 20.0
		# Sparkle victory.
		if victory:
			for i in range(8):
				var sa := t + float(i) * PI / 4.0
				var sd := 100.0 + sin(t + float(i)) * 20.0
				var sp := Vector2(cx + cos(sa) * sd,
					cy - 180.0 + sin(sa) * 30.0)
				draw_circle(sp, 3.0, Color(1.0, 1.0, 200.0 / 255.0))
				draw_circle(sp, 2.0, accent)


## Judul Cinzel 88 berdenyut + glow.
class _TitleFx extends Control:
	var title_text: String = ""
	var victory: bool = false
	var t: float = 0.0

	func _init() -> void:
		set_process(false)

	func _process(delta: float) -> void:
		t += delta * 20.0 * 0.05
		queue_redraw()

	func _notification(what: int) -> void:
		if what == NOTIFICATION_RESIZED:
			queue_redraw()

	func _draw() -> void:
		if title_text.is_empty():
			return
		var cx := size.x * 0.5
		var cy := size.y * 0.5
		var pulse := sin(t * 2.0) * 0.04 + 1.0
		var title_size := int(round(88.0 * pulse / 4.0) * 4.0)
		var gc := Color(1.0, 205.0 / 255.0, 90.0 / 255.0) if victory \
			else Color(1.0, 90.0 / 255.0, 70.0 / 255.0)
		UiTheme.draw_glow(self, Rect2(cx - 380, cy - 95, 760, 190),
			gc, 54.0 / 255.0)
		var body := Color(1.0, 242.0 / 255.0, 175.0 / 255.0) if victory \
			else Color(1.0, 175.0 / 255.0, 150.0 / 255.0)
		UiTheme.draw_outline_text(self, UiTheme.title_font(),
			title_text, title_size, Vector2(cx, cy), body,
			Color(8.0 / 255.0, 9.0 / 255.0, 18.0 / 255.0), 3)


## Siluet boss popup unlock: aura + badan + duri mahkota + mata menyala.
class _BossSilhouette extends Control:
	var entrance: Color = Color(0.6, 0.4, 0.8)
	var boss_col: Color = Color(0.6, 0.4, 0.8)
	var boss_class: String = "true"
	var t: float = 0.0

	func _init(p_entrance: Color, p_boss: Color,
			p_class: String) -> void:
		entrance = p_entrance
		boss_col = p_boss
		boss_class = p_class
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		t += delta
		queue_redraw()

	func _draw() -> void:
		var scx := 47.0
		var scy := 47.0
		# Aura denyut.
		var ap := sin(t * 2.5) * 0.3 + 0.7
		var ar := 35.0 * ap
		var r := ar
		while r > 5.0:
			var a := (ar - r) * 3.0 / 255.0
			if a > 0.0:
				draw_circle(Vector2(scx, scy), r,
					Color(entrance.r, entrance.g, entrance.b, a))
			r -= 3.0
		# Badan siluet.
		var pts := PackedVector2Array([
			Vector2(scx - 15, scy - 5), Vector2(scx - 10, scy - 20),
			Vector2(scx, scy - 25), Vector2(scx + 10, scy - 20),
			Vector2(scx + 15, scy - 5), Vector2(scx + 18, scy + 10),
			Vector2(scx + 12, scy + 22), Vector2(scx - 12, scy + 22),
			Vector2(scx - 18, scy + 10)])
		draw_colored_polygon(pts, Color.BLACK)
		draw_polyline(PackedVector2Array(pts + PackedVector2Array([pts[0]])),
			boss_col, 2.0)
		# Duri mahkota.
		var n := 5 if boss_class == "true" else 3
		for i in range(n):
			var sx := scx + float(i - n / 2) * 8.0
			draw_colored_polygon(PackedVector2Array([
				Vector2(sx - 3, scy - 25), Vector2(sx, scy - 33),
				Vector2(sx + 3, scy - 25)]), Color.BLACK)
		# Mata menyala.
		var ep := sin(t * 5.0) * 0.3 + 0.7
		for ex in [-6.0, 6.0]:
			var eye := Vector2(scx + ex, scy - 12)
			draw_circle(eye, 4.0, Color(entrance.r, entrance.g,
				entrance.b, 0.35 * ep))
			draw_circle(eye, 2.0, entrance)
			draw_circle(eye, 1.0, Color.WHITE)
