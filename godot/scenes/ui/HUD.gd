# HUD.gd — Port _core.py Game._draw_gold_hud + _render.WaveAnnouncer + bar HP
# Castle (_draw_castle_bars) + banner menang/kalah.
# Di Pygame: chip emas, bar nexus, dan banner digambar manual tiap frame.
# Di Godot: Control statis untuk angka yang jarang berubah; bagian yang baru
# (bar nexus, difficulty, banner victory/defeat, SkillBar, ShopPanel) dibangun
# dari kode supaya HUD.tscn tidak perlu dirombak.
extends Control

const SkillBarScript = preload("res://scenes/ui/SkillBar.gd")
const ShopPanelScript = preload("res://scenes/ui/ShopPanel.gd")
const ComboBadgeScript = preload("res://scenes/ui/ComboBadge.gd")
const AchievementPopupScript = preload("res://scenes/ui/AchievementPopup.gd")
const TacticalBarScript = preload("res://scenes/ui/TacticalBar.gd")
## Seberapa sering bar nexus/disability disegarkan (5 Hz cukup, hemat draw call)
const BAR_REFRESH := 0.2

var _banner_tween: Tween
var _wave_sub: Label = null
var _field_timer: float = 0.0
var _bar_timer: float = 0.0
var _nexus_bars: Dictionary = {}   # team -> {hp: ProgressBar, shield: ProgressBar, label: Label}
var _difficulty_label: Label = null
var _over_panel: PanelContainer = null
var _over_title: Label = null
var _over_stats: Label = null
var _over_body: Label = null
var _next_button: Button = null
var _combo_badge: Control = null
var _achievement_popup: Control = null

@onready var gold_label: Label = $TopLeft/GoldChip/GoldRow/GoldValue
@onready var income_label: Label = $TopLeft/GoldChip/GoldRow/IncomeValue
@onready var level_label: Label = $TopLeft/LevelBadge/LevelRow/LevelValue
@onready var wave_label: Label = $TopLeft/LevelBadge/LevelRow/WaveValue
@onready var wave_banner: Label = $WaveBanner
@onready var field_label: Label = $TopLeft/FieldStatus

func _ready():
	wave_banner.modulate.a = 0.0
	wave_banner.set_meta("base_l", wave_banner.offset_left)
	wave_banner.set_meta("base_r", wave_banner.offset_right)
	_build_wave_sub()
	GameManager.gold_changed.connect(_on_gold_changed)
	GameManager.wave_started.connect(_on_wave_started)
	GameManager.level_started.connect(_on_level_started)
	GameManager.hero_died.connect(_on_field_changed)
	GameManager.minion_died.connect(_on_minion_died)
	GameManager.boss_spawned.connect(_on_boss_spawned)
	GameManager.game_over.connect(_on_game_over)
	GameManager.difficulty_changed.connect(_on_difficulty_changed)
	GameManager.nexus_destroyed.connect(_on_nexus_destroyed)
	_build_nexus_bars()
	_build_difficulty_label()
	_build_game_over_panel()
	# SkillBar + ShopPanel dibangun dari kode (lihat file masing-masing)
	add_child(SkillBarScript.new())
	add_child(ShopPanelScript.new())
	# FASE 18 — panel TACTICAL COMMANDS (HOLD): pemicu UI perintah taktis
	# (port sidepanel _gambar_tactical + apply_hud_action; tekan/lepas =
	# hold_start/hold_end di TacticalCommands.gd).
	var tactical_bar = TacticalBarScript.new()
	tactical_bar.name = "TacticalBar"
	add_child(tactical_bar)
	# FASE 13 — klaster skor: badge combo kanan-atas (port ComboCounter.draw)
	# + popup achievement di layar arena (port AchievementPopup; trigger
	# GameManager.unlock_achievement, mis. NEW HERO UNLOCKED! saat menang).
	_combo_badge = ComboBadgeScript.new()
	_combo_badge.name = "ComboBadge"
	add_child(_combo_badge)
	_achievement_popup = AchievementPopupScript.new()
	_achievement_popup.name = "AchievementPopup"
	add_child(_achievement_popup)
	GameManager.achievement_unlocked.connect(
		_achievement_popup.unlock)
	GameManager.boss_reward_effects_tick.connect(_achievement_popup.tick)
	refresh()
	_refresh_field()
	_refresh_bars()

# Hitungan unit di medan — di-update ~3x/detik (bukan tiap frame) biar murah.
func _process(delta: float) -> void:
	_field_timer += delta
	if _field_timer >= 0.33:
		_field_timer = 0.0
		_refresh_field()
	_bar_timer += delta
	if _bar_timer >= BAR_REFRESH:
		_bar_timer = 0.0
		_refresh_bars()

# Sinkronkan seluruh HUD dari state GameManager (dipakai saat _ready + level_started)
func refresh():
	_on_gold_changed(GameManager.gold)
	level_label.text = "LEVEL %d" % GameManager.level_number
	wave_label.text = "WAVE %d" % GameManager.wave_number

func _on_gold_changed(new_gold: int):
	gold_label.text = _format_thousands(new_gold)
	income_label.text = "+%s/s" % _format_gold_rate(GameManager.gold_per_second)

func _on_level_started(_level_num: int):
	if _achievement_popup != null:
		_achievement_popup.reset()
	# Level baru (PLAY/ENTER-next/R) -> sembunyikan panel menang/kalah lama.
	if _over_panel != null:
		_over_panel.visible = false
	refresh()
	_refresh_field()

func _on_field_changed(_hero: Node) -> void:
	_refresh_field()

func _on_minion_died(_minion: Node, _killer_team: String) -> void:
	_refresh_field()

func _on_boss_spawned(_boss_type: String) -> void:
	_refresh_field()

func _refresh_field() -> void:
	if field_label == null:
		return
	var tree := get_tree()
	var heroes := 0
	for h in tree.get_nodes_in_group("heroes"):
		if is_instance_valid(h) and not bool(h.get("is_dead")):
			heroes += 1
	var minions := 0
	for m in tree.get_nodes_in_group("minions"):
		if is_instance_valid(m) and not bool(m.get("is_dead")):
			minions += 1
	var bosses := 0
	for b in tree.get_nodes_in_group("bosses"):
		if is_instance_valid(b) and not bool(b.get("is_dead")):
			bosses += 1
	field_label.text = "medan: %d hero · %d minion · %d boss · %d fps" % [
		heroes, minions, bosses, int(Engine.get_frames_per_second())]

func _on_wave_started(wave_num: int):
	wave_label.text = "WAVE %d" % wave_num
	announce_wave(wave_num)

# Subtitle banner ("E N E M I E S   I N C O M I N G") — posisi di bawah judul.
func _build_wave_sub() -> void:
	_wave_sub = Label.new()
	_wave_sub.name = "WaveSub"
	_wave_sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_wave_sub.anchor_left = 0.5
	_wave_sub.anchor_top = 0.5
	_wave_sub.anchor_right = 0.5
	_wave_sub.anchor_bottom = 0.5
	_wave_sub.offset_left = -300.0
	_wave_sub.offset_top = -66.0
	_wave_sub.offset_right = 300.0
	_wave_sub.offset_bottom = -36.0
	_wave_sub.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_wave_sub.grow_vertical = Control.GROW_DIRECTION_BOTH
	_wave_sub.add_theme_font_size_override("font_size", 22)
	_wave_sub.add_theme_color_override("font_color", Color(0.78, 0.78, 0.86))
	_wave_sub.add_theme_color_override("font_outline_color", Color(0.03, 0.03, 0.05, 1))
	_wave_sub.add_theme_constant_override("outline_size", 4)
	_wave_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_wave_sub.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_wave_sub.modulate.a = 0.0
	_wave_sub.set_meta("base_l", _wave_sub.offset_left)
	_wave_sub.set_meta("base_r", _wave_sub.offset_right)
	add_child(_wave_sub)


## Banner "WAVE N" — port gerak WaveAnnouncer: slide-in 0.4s (BACK OUT =
## ease_out_back, c1 1.70158 sama) -> tahan 1.0s -> slide-out 0.6s (BACK IN).
## Kurva frame-per-frame dikunci di HudLayout.wave_slide_x (120 titik fixture).
func announce_wave(wave_num: int):
	wave_banner.text = HudLayout.wave_title(wave_num)
	_wave_sub.text = HudLayout.wave_subtitle()
	if _banner_tween and _banner_tween.is_valid():
		_banner_tween.kill()
	wave_banner.scale = Vector2.ONE
	_banner_tween = create_tween()
	_banner_tween.set_parallel(true)
	_banner_tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	for lab in [wave_banner, _wave_sub]:
		var base_l := float(lab.get_meta("base_l"))
		var base_r := float(lab.get_meta("base_r"))
		lab.offset_left = base_l - 1280.0
		lab.offset_right = base_r - 1280.0
		lab.modulate.a = 0.0
		_banner_tween.tween_property(lab, "offset_left", base_l, HudLayout.WAVE_TWEEN_IN)
		_banner_tween.tween_property(lab, "offset_right", base_r, HudLayout.WAVE_TWEEN_IN)
		_banner_tween.tween_property(lab, "modulate:a", 1.0, HudLayout.WAVE_TWEEN_IN)
	_banner_tween.set_parallel(false)
	_banner_tween.tween_interval(HudLayout.WAVE_TWEEN_HOLD)
	_banner_tween.set_parallel(true)
	_banner_tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	for lab in [wave_banner, _wave_sub]:
		var base_l := float(lab.get_meta("base_l"))
		var base_r := float(lab.get_meta("base_r"))
		_banner_tween.tween_property(lab, "offset_left", base_l + 1280.0, HudLayout.WAVE_TWEEN_OUT)
		_banner_tween.tween_property(lab, "offset_right", base_r + 1280.0, HudLayout.WAVE_TWEEN_OUT)
		_banner_tween.tween_property(lab, "modulate:a", 0.0, HudLayout.WAVE_TWEEN_OUT)

# 1234567 -> "1,234,567" — kanon HudLayout, delegasi tipis (dipakai income_label).
static func _format_thousands(n: int) -> String:
	return HudLayout.format_thousands(n)

# 3.0 -> "3", 5.7 -> "5.7", 3.75 -> "3.8" — kanon HudLayout, delegasi tipis.
static func _format_gold_rate(rate: float) -> String:
	return HudLayout.format_gold_rate(rate)


# ══════════════════════════════════════════════════════════
#  BAR NEXUS (port _core.Game._draw_castle_bars)
# ══════════════════════════════════════════════════════════

func _build_nexus_bars() -> void:
	var row := HBoxContainer.new()
	row.name = "NexusBars"
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.anchor_left = 0.5
	row.anchor_right = 0.5
	row.offset_left = -300.0
	row.offset_right = 300.0
	row.offset_top = 14.0
	row.offset_bottom = 74.0
	row.add_theme_constant_override("separation", 24)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	add_child(row)
	for team in ["blue", "red"]:
		row.add_child(_make_nexus_bar(row, str(team)))


func _make_nexus_bar(_owner: Control, team: String) -> Control:
	var is_blue := team == "blue"
	var accent := Color(0.36, 0.62, 1.0) if is_blue else Color(0.95, 0.35, 0.35)
	var panel := PanelContainer.new()
	panel.name = "NexusBar_%s" % team
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.custom_minimum_size = Vector2(264, 0)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.045, 0.05, 0.085, 0.88)
	sb.border_color = Color(accent.r, accent.g, accent.b, 0.85)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(9)
	sb.content_margin_left = 9.0
	sb.content_margin_right = 9.0
	sb.content_margin_top = 5.0
	sb.content_margin_bottom = 5.0
	panel.add_theme_stylebox_override("panel", sb)

	var vbox := VBoxContainer.new()
	vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_theme_constant_override("separation", 2)
	panel.add_child(vbox)

	var label := Label.new()
	label.text = ("RADIANT NEXUS" if is_blue else "DIRE NEXUS") + "  Lv1"
	label.add_theme_font_size_override("font_size", 11)
	label.add_theme_color_override("font_color", accent.lightened(0.35))
	vbox.add_child(label)

	var hp := ProgressBar.new()
	hp.custom_minimum_size = Vector2(0, 11)
	hp.show_percentage = false
	hp.max_value = 100.0
	hp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var hp_bg := StyleBoxFlat.new()
	hp_bg.bg_color = Color(0.13, 0.05, 0.06, 0.95)
	hp_bg.set_corner_radius_all(3)
	var hp_fill := StyleBoxFlat.new()
	hp_fill.bg_color = Color(0.35, 0.87, 0.45) if is_blue else Color(0.9, 0.4, 0.35)
	hp_fill.set_corner_radius_all(3)
	hp.add_theme_stylebox_override("background", hp_bg)
	hp.add_theme_stylebox_override("fill", hp_fill)
	vbox.add_child(hp)

	var shield := ProgressBar.new()
	shield.custom_minimum_size = Vector2(0, 6)
	shield.show_percentage = false
	shield.max_value = 100.0
	shield.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh_bg := StyleBoxFlat.new()
	sh_bg.bg_color = Color(0.07, 0.09, 0.14, 0.95)
	sh_bg.set_corner_radius_all(3)
	var sh_fill := StyleBoxFlat.new()
	sh_fill.bg_color = Color(0.45, 0.78, 1.0, 0.95)
	sh_fill.set_corner_radius_all(3)
	shield.add_theme_stylebox_override("background", sh_bg)
	shield.add_theme_stylebox_override("fill", sh_fill)
	vbox.add_child(shield)

	_nexus_bars[team] = {"hp": hp, "shield": shield, "label": label}
	return panel


func _refresh_bars() -> void:
	for team in ["blue", "red"]:
		var bars: Dictionary = _nexus_bars.get(str(team), {})
		if bars.is_empty():
			continue
		var data: Array = GameManager.nexus_hp(str(team))
		var hp := float(data[0])
		var max_hp := maxf(1.0, float(data[1]))
		var shield := float(data[2])
		var shield_max := float(data[3])
		var hp_bar: ProgressBar = bars["hp"]
		var sh_bar: ProgressBar = bars["shield"]
		var label: Label = bars["label"]
		hp_bar.value = clampf(100.0 * hp / max_hp, 0.0, 100.0)
		if shield_max > 0.0:
			sh_bar.value = clampf(100.0 * shield / shield_max, 0.0, 100.0)
		else:
			sh_bar.value = 0.0
		sh_bar.visible = shield_max > 0.0
		var nexus = GameManager.blue_nexus if team == "blue" else GameManager.red_nexus
		var lv := int(nexus.get("level")) if nexus != null and is_instance_valid(nexus) else 0
		label.text = "%s  Lv%d  ·  %d/%d HP%s" % [
			"RADIANT NEXUS" if team == "blue" else "DIRE NEXUS", lv,
			int(hp), int(max_hp),
			"" if shield_max <= 0.0 else "  ·  shield %d" % int(shield)]


# ══════════════════════════════════════════════════════════
#  DIFFICULTY + BANNER MENANG/KALAH
# ══════════════════════════════════════════════════════════

func _build_difficulty_label() -> void:
	_difficulty_label = Label.new()
	_difficulty_label.name = "DifficultyLabel"
	_difficulty_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_difficulty_label.offset_left = 18.0
	_difficulty_label.offset_top = 112.0
	_difficulty_label.offset_right = 420.0
	_difficulty_label.offset_bottom = 132.0
	_difficulty_label.add_theme_font_size_override("font_size", 12)
	_difficulty_label.add_theme_color_override("font_color", Color(0.82, 0.86, 0.98, 0.9))
	_difficulty_label.add_theme_color_override("font_outline_color", Color(0.04, 0.03, 0.08, 0.85))
	_difficulty_label.add_theme_constant_override("outline_size", 3)
	add_child(_difficulty_label)
	_on_difficulty_changed(GameManager.difficulty)


func _on_difficulty_changed(d: String) -> void:
	if _difficulty_label == null:
		return
	_difficulty_label.text = "difficulty: %s  ·  gold x%.2f" % [
		str(d).to_upper(), GameManager.difficulty_mult(d)]


func _build_game_over_panel() -> void:
	_over_panel = PanelContainer.new()
	_over_panel.name = "GameOverPanel"
	_over_panel.visible = false
	_over_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	_over_panel.anchor_left = 0.5
	_over_panel.anchor_right = 0.5
	_over_panel.anchor_top = 0.5
	_over_panel.anchor_bottom = 0.5
	_over_panel.offset_left = -260.0
	_over_panel.offset_right = 260.0
	_over_panel.offset_top = -186.0
	_over_panel.offset_bottom = 186.0
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.045, 0.08, 0.94)
	sb.border_color = Color(1, 0.85, 0.4, 0.95)
	sb.set_border_width_all(3)
	sb.set_corner_radius_all(14)
	sb.content_margin_left = 22.0
	sb.content_margin_right = 22.0
	sb.content_margin_top = 14.0
	sb.content_margin_bottom = 14.0
	sb.shadow_color = Color(0, 0, 0, 0.6)
	sb.shadow_size = 18
	_over_panel.add_theme_stylebox_override("panel", sb)
	add_child(_over_panel)

	var vbox := VBoxContainer.new()
	vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	vbox.add_theme_constant_override("separation", 8)
	_over_panel.add_child(vbox)

	_over_title = Label.new()
	_over_title.text = "VICTORY"
	_over_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_over_title.add_theme_font_size_override("font_size", 44)
	_over_title.add_theme_color_override("font_color", Color(1, 0.9, 0.45))
	_over_title.add_theme_color_override("font_outline_color", Color(0.12, 0.06, 0, 1))
	_over_title.add_theme_constant_override("outline_size", 6)
	vbox.add_child(_over_title)

	# Baris stat paritas _draw_stats (label + nilai per baris).
	_over_stats = Label.new()
	_over_stats.text = ""
	_over_stats.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_over_stats.add_theme_font_size_override("font_size", 15)
	_over_stats.add_theme_color_override("font_color", Color(0.92, 0.95, 1.0))
	vbox.add_child(_over_stats)

	_over_body = Label.new()
	_over_body.text = ""
	_over_body.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_over_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_over_body.add_theme_font_size_override("font_size", 13)
	_over_body.add_theme_color_override("font_color", Color(0.85, 0.9, 1.0))
	vbox.add_child(_over_body)

	# Tombol alur setelah match (paritas tombol pygame: play_next_level /
	# replay / main menu — _core.py:7734-7743 + 8320-8336). Keyboard tetap
	# jalan (ENTER/R/ESC di Main._on_key), tombol ini untuk mouse/touch.
	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	actions.add_theme_constant_override("separation", 10)
	vbox.add_child(actions)
	_next_button = Button.new()
	_next_button.text = "LANJUT KE LEVEL 2  (ENTER)"
	_next_button.custom_minimum_size = Vector2(210, 34)
	_next_button.pressed.connect(func(): GameManager.next_level())
	actions.add_child(_next_button)
	var replay_btn := Button.new()
	replay_btn.text = "ULANGI  (R)"
	replay_btn.custom_minimum_size = Vector2(130, 34)
	replay_btn.pressed.connect(func(): GameManager.restart_match())
	actions.add_child(replay_btn)
	var menu_btn := Button.new()
	menu_btn.text = "MENU UTAMA  (ESC)"
	menu_btn.custom_minimum_size = Vector2(160, 34)
	menu_btn.pressed.connect(_goto_main_menu)
	actions.add_child(menu_btn)

	var hint := Label.new()
	hint.text = "ENTER/N = lanjut level berikutnya  ·  R = ulangi  ·  ESC = menu utama"
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.add_theme_font_size_override("font_size", 12)
	hint.add_theme_color_override("font_color", Color(0.7, 0.76, 0.9, 0.85))
	vbox.add_child(hint)


## Tombol MENU UTAMA pada panel game over: jalankan alur yang sama dengan
## Main._on_menu_main_menu (unpause + buang match + tampilkan menu MAIN)
## supaya klik mouse dan keyboard ESC identik.
func _goto_main_menu() -> void:
	if _over_panel != null:
		_over_panel.visible = false
	var main = get_tree().get_first_node_in_group("main")
	if main != null and is_instance_valid(main) and main.has_method("_on_menu_main_menu"):
		main.call("_on_menu_main_menu")
		return
	# fallback kalau scene uji tidak memasang Main.gd
	GameManager.return_to_menu()
	var menu = get_tree().get_first_node_in_group("main_menu")
	if menu != null and is_instance_valid(menu) and menu.has_method("show_main"):
		menu.show_main()


func _on_game_over(victory: bool) -> void:
	if _over_panel == null:
		return
	_over_panel.visible = true
	# Judul paritas overlay ("VICTORY! LV.1" / "DEFEAT LV.3").
	_over_title.text = "%s LV.%d" % [
		"VICTORY!" if victory else "DEFEAT", GameManager.level_number]
	_over_title.add_theme_color_override("font_color",
		Color(1, 0.9, 0.45) if victory else Color(1, 0.45, 0.45))
	# Stat paritas _draw_stats (ui_components/_bundle.py:2976-3060): lima
	# baris — Final Score (ribuan), Match Time (m:ss), Waves Survived,
	# Total Kills, Max Combo (x{n}); baris skor/waktu mendapat penanda
	# NEW BEST! saat flag _grant_meta_reward menyala (badge gradasi+ikon
	# bintang pygame = piksel, tidak diaudit; data baris direplay dari
	# fixture ui_hud overlay + match_scoring).
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
	_over_stats.text = "\n".join(stat_lines)
	# Reward yang BENAR-BENAR diberikan (paritas _grant_meta_reward: menang
	# pertama 3000 / replay 1500 sekali / 200 berikutnya / kalah 0), bukan
	# lagi rumusan 3000 + level*100.
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
	# Paritas _get_newly_unlocked_level: menang + level berikut ADA + belum
	# pernah ditamatkan (end_match sudah complete_level saat ini).
	var nxt := GameManager.next_level_number()
	if victory and nxt > 0 and not SaveManager.is_level_completed(nxt):
		lines.append("NEW LEVEL UNLOCKED!")
	# Baris NEW HERO: pygame MENGHITUNG subtitle ini tapi TIDAK me-render-nya
	# (Overlay.draw mengabaikan param subtitle; satu-satunya jalur tampil =
	# popup achievement). Godot menampilkannya — beda disengaja, data sama.
	var new_heroes: Array = GameManager.heroes_unlocked_this_match
	if victory and not new_heroes.is_empty():
		var names: Array = []
		for bt in new_heroes:
			names.append(str(HeroDB.get_hero(str(bt)).get("name", str(bt))))
		lines.append("NEW HERO: %s" % ", ".join(names))
	_over_body.text = "\n".join(lines)
	if _next_button != null:
		_next_button.visible = victory and nxt > 0
		if nxt > 0:
			_next_button.text = "LANJUT KE LEVEL %d  (ENTER)" % nxt
	_over_panel.pivot_offset = _over_panel.size / 2.0
	_over_panel.scale = Vector2(0.85, 0.85)
	_over_panel.modulate.a = 0.0
	var tw := create_tween()
	tw.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.set_parallel(true)
	tw.tween_property(_over_panel, "modulate:a", 1.0, 0.3)
	tw.tween_property(_over_panel, "scale", Vector2.ONE, 0.35)


func _on_nexus_destroyed(team: String, _killer_team: String) -> void:
	if field_label != null:
		field_label.text = "nexus %s hancur" % ("Radiant" if team == "blue" else "Dire")
