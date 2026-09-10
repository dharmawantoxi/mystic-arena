# SkillButton.gd — satu tombol skill (Q/W/E/R) + overlay cooldown.
#
# Port _draw_skill_slot pygame: frame gelap 54px, glow siap, overlay
# cooldown dari bawah + angka detik, border hijau-denut saat auto-cast /
# emas saat ultimate siap / warna skill saat siap / abu saat cooldown,
# badge huruf kunci di kanan-bawah. Di Godot ini Button biasa dengan
# ColorRect anak yang "menyusut" dari atas ke bawah sesuai sisa cooldown,
# jadi tidak ada satu barispun _draw() dan tetap bisa diklik mouse.
extends Button

## Dipancarkan saat tombol ditekan mouse (SkillBar yang mengeksekusi cast-nya,
# supaya jalur mouse dan keyboard identik)
signal skill_requested(key: String)

var skill_key: String = "q"

var _overlay: ColorRect = null
var _key_label: Label = null
var _name_label: Label = null
var _cd_label: Label = null
var _frame: StyleBoxFlat = null


func _init(p_key: String = "q") -> void:
	skill_key = p_key
	custom_minimum_size = Vector2(54, 54)
	text = ""
	clip_contents = true
	focus_mode = Control.FOCUS_NONE
	mouse_filter = Control.MOUSE_FILTER_STOP
	_frame = StyleBoxFlat.new()
	_frame.bg_color = Color(24.0 / 255.0, 27.0 / 255.0, 46.0 / 255.0)
	_frame.border_color = Color(110.0 / 255.0, 116.0 / 255.0, 142.0 / 255.0)
	_frame.set_border_width_all(1)
	_frame.set_corner_radius_all(6)
	add_theme_stylebox_override("normal", _frame)
	add_theme_stylebox_override("hover", _frame)
	add_theme_stylebox_override("pressed", _frame)
	add_theme_stylebox_override("disabled", _frame)
	_build_children()
	pressed.connect(_on_pressed)


func _build_children() -> void:
	# sisa cooldown: menutup bagian bawah tombol sebanyak `ratio`
	_overlay = ColorRect.new()
	_overlay.name = "CooldownOverlay"
	_overlay.color = Color(0.0, 0.0, 0.0, 190.0 / 255.0)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.anchor_left = 0.0
	_overlay.anchor_right = 1.0
	_overlay.anchor_top = 0.0
	_overlay.anchor_bottom = 1.0
	_overlay.offset_left = 0.0
	_overlay.offset_right = 0.0
	_overlay.offset_top = 0.0
	_overlay.offset_bottom = 0.0
	add_child(_overlay)

	# Nama skill (bawah, mungil).
	_name_label = Label.new()
	_name_label.name = "SkillName"
	_name_label.text = ""
	_name_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.clip_text = true
	_name_label.add_theme_font_override("font", UiTheme.body_medium())
	_name_label.add_theme_font_size_override("font_size", 8)
	_name_label.add_theme_color_override("font_color",
		Color(0.82, 0.87, 1.0, 0.9))
	_name_label.anchor_left = 0.0
	_name_label.anchor_right = 1.0
	_name_label.anchor_top = 1.0
	_name_label.anchor_bottom = 1.0
	_name_label.offset_left = 2.0
	_name_label.offset_right = -2.0
	_name_label.offset_top = -12.0
	_name_label.offset_bottom = -2.0
	add_child(_name_label)

	# Badge huruf kunci (kanan-bawah, paritas badge pygame).
	_key_label = Label.new()
	_key_label.name = "KeyLabel"
	_key_label.text = skill_key.to_upper()
	_key_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_key_label.add_theme_font_override("font", UiTheme.body_bold())
	_key_label.add_theme_font_size_override("font_size", 11)
	_key_label.add_theme_color_override("font_color",
		Color(220.0 / 255.0, 226.0 / 255.0, 245.0 / 255.0))
	_key_label.add_theme_color_override("font_outline_color",
		Color(10.0 / 255.0, 12.0 / 255.0, 22.0 / 255.0))
	_key_label.add_theme_constant_override("outline_size", 4)
	_key_label.anchor_left = 1.0
	_key_label.anchor_right = 1.0
	_key_label.anchor_top = 1.0
	_key_label.anchor_bottom = 1.0
	_key_label.offset_left = -24.0
	_key_label.offset_right = -3.0
	_key_label.offset_top = -26.0
	_key_label.offset_bottom = -12.0
	_key_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(_key_label)

	_cd_label = Label.new()
	_cd_label.name = "CooldownLabel"
	_cd_label.text = ""
	_cd_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cd_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_cd_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_cd_label.add_theme_font_override("font", UiTheme.body_bold())
	_cd_label.add_theme_font_size_override("font_size", 19)
	_cd_label.add_theme_color_override("font_color", Color(1, 1, 1, 0.95))
	_cd_label.add_theme_color_override("font_outline_color",
		Color(0, 0, 0, 0.9))
	_cd_label.add_theme_constant_override("outline_size", 3)
	_cd_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_cd_label.offset_top = -6.0
	add_child(_cd_label)


func _on_pressed() -> void:
	skill_requested.emit(skill_key)


## Disinkronkan ~20x/detik oleh SkillBar
func update_state(hero) -> void:
	var skills = hero.get("skills") if hero != null and is_instance_valid(hero) else null
	if skills == null:
		disabled = true
		_overlay.anchor_top = 0.0
		_cd_label.text = ""
		_name_label.text = ""
		modulate = Color(0.6, 0.62, 0.7, 1.0)
		_style_frame(false, false, false, Color(0.5, 0.5, 0.6))
		return
	disabled = false
	var ratio: float = skills.cooldown_ratio(skill_key)
	_overlay.anchor_top = clampf(ratio, 0.0, 1.0)
	var ready: bool = skills.is_ready(skill_key)
	var charging: bool = skills.is_charging(skill_key)
	_style_frame(ready and not charging, skill_key == "r",
		bool(hero.get("auto_cast_enabled")), _skill_color(hero))
	if ready and not charging:
		_cd_label.text = ""
		modulate = Color(1, 1, 1, 1)
	elif charging:
		_cd_label.text = "..."
		modulate = Color(1.0, 0.95, 0.7, 1.0)
	else:
		# Angka detik paritas HeroPanel (frames // 60 + 1 — 60f tampil "2",
		# bukan ceil()=1).
		_cd_label.text = "%d" % HudLayout.cooldown_seconds(
			skills.cooldown_frames(skill_key))
		modulate = Color(0.78, 0.8, 0.88, 1.0)
	_name_label.text = str(skills.skill_label(skill_key))
	tooltip_text = "%s (%s) — %s" % [
		skill_key.to_upper(), str(skills.skill_label(skill_key)),
		"siap" if ready else "cooldown %.1fs" % skills.cooldown_remaining(skill_key)]


## Warna slot per kunci (paritas HeroPanel: Q = warna hero).
func _skill_color(hero) -> Color:
	match skill_key:
		"w":
			return Color(100.0 / 255.0, 200.0 / 255.0, 1.0)
		"e":
			return Color(100.0 / 255.0, 1.0, 100.0 / 255.0)
		"r":
			return Color(1.0, 100.0 / 255.0, 100.0 / 255.0)
		_:
			return HeroDB.get_hero_color(str(hero.get("hero_type")))


## Frame slot (paritas border _draw_skill_slot).
func _style_frame(ready: bool, ultimate: bool, auto: bool, col: Color) -> void:
	if _frame == null:
		return
	if ready:
		_frame.bg_color = Color(30.0 / 255.0, 34.0 / 255.0, 58.0 / 255.0)
	else:
		_frame.bg_color = Color(24.0 / 255.0, 27.0 / 255.0, 46.0 / 255.0)
	if auto:
		_frame.border_color = Color(140.0 / 255.0, 1.0, 140.0 / 255.0)
		_frame.set_border_width_all(2)
	elif ready and ultimate:
		_frame.border_color = UiTheme.GOLD
		_frame.set_border_width_all(2)
	elif ready:
		_frame.border_color = Color(minf(1.0, col.r + 60.0 / 255.0),
			minf(1.0, col.g + 60.0 / 255.0),
			minf(1.0, col.b + 60.0 / 255.0))
		_frame.set_border_width_all(2)
	else:
		_frame.border_color = Color(110.0 / 255.0, 116.0 / 255.0, 142.0 / 255.0)
		_frame.set_border_width_all(1)
	queue_redraw()
