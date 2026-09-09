# SkillButton.gd — satu tombol skill (Q/W/E/R) + overlay cooldown.
#
# pygame menggambar bar skill manual tiap frame (_core.Game._draw_skill_bar):
# kotak huruf, nama skill, dan busur cooldown. Di Godot ini Button biasa dengan
# ColorRect anak yang "menyusut" dari atas ke bawah sesuai sisa cooldown, jadi
# tidak ada satu baris pun _draw() dan tetap bisa diklik mouse.
extends Button

## Dipancarkan saat tombol ditekan mouse (SkillBar yang mengeksekusi cast-nya,
# supaya jalur mouse dan keyboard identik)
signal skill_requested(key: String)

var skill_key: String = "q"

var _overlay: ColorRect = null
var _key_label: Label = null
var _name_label: Label = null
var _cd_label: Label = null


func _init(p_key: String = "q") -> void:
	skill_key = p_key
	custom_minimum_size = Vector2(70, 70)
	text = ""
	clip_contents = true
	focus_mode = Control.FOCUS_NONE
	mouse_filter = Control.MOUSE_FILTER_STOP
	_style()
	_build_children()
	pressed.connect(_on_pressed)


func _style() -> void:
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color8(26, 31, 54)
	normal.border_color = UiTheme.EDGE_GOLD
	normal.set_border_width_all(2)
	normal.set_corner_radius_all(10)
	var hover := normal.duplicate() as StyleBoxFlat
	hover.bg_color = Color8(38, 45, 76)
	hover.border_color = UiTheme.GOLD
	var pressed := normal.duplicate() as StyleBoxFlat
	pressed.bg_color = Color8(18, 22, 40)
	pressed.border_color = UiTheme.GOLD_DEEP
	var disabled := normal.duplicate() as StyleBoxFlat
	disabled.bg_color = Color8(20, 21, 30)
	disabled.border_color = Color8(70, 74, 96)
	add_theme_stylebox_override("normal", normal)
	add_theme_stylebox_override("hover", hover)
	add_theme_stylebox_override("pressed", pressed)
	add_theme_stylebox_override("disabled", disabled)
	add_theme_stylebox_override("focus", StyleBoxEmpty.new())


func _build_children() -> void:
	# sisa cooldown: menutup bagian bawah tombol sebanyak `ratio`
	_overlay = ColorRect.new()
	_overlay.name = "CooldownOverlay"
	_overlay.color = Color(0.02, 0.02, 0.05, 0.68)
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

	_key_label = Label.new()
	_key_label.name = "KeyLabel"
	_key_label.text = skill_key.to_upper()
	_key_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_label(_key_label, 20, "body_bold", UiTheme.GOLD_TEXT,
		true)
	_key_label.add_theme_color_override("font_outline_color",
		Color(0.04, 0.03, 0.08, 0.9))
	_key_label.add_theme_constant_override("outline_size", 4)
	_key_label.position = Vector2(7, 3)
	add_child(_key_label)

	_cd_label = Label.new()
	_cd_label.name = "CooldownLabel"
	_cd_label.text = ""
	_cd_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cd_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_cd_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	UiTheme.style_label(_cd_label, 22, "body_bold",
		Color(1, 1, 1, 0.95))
	_cd_label.add_theme_color_override("font_outline_color",
		Color(0.02, 0.02, 0.05, 0.9))
	_cd_label.add_theme_constant_override("outline_size", 5)
	_cd_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_cd_label)

	_name_label = Label.new()
	_name_label.name = "SkillName"
	_name_label.text = ""
	_name_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.clip_text = true
	UiTheme.style_label(_name_label, 9, "body_semibold",
		Color(0.82, 0.87, 1.0, 0.9))
	_name_label.anchor_left = 0.0
	_name_label.anchor_right = 1.0
	_name_label.anchor_top = 1.0
	_name_label.anchor_bottom = 1.0
	_name_label.offset_left = 2.0
	_name_label.offset_right = -2.0
	_name_label.offset_top = -14.0
	_name_label.offset_bottom = -2.0
	add_child(_name_label)


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
		return
	disabled = false
	var ratio: float = skills.cooldown_ratio(skill_key)
	_overlay.anchor_top = clampf(ratio, 0.0, 1.0)
	var ready: bool = skills.is_ready(skill_key)
	var charging: bool = skills.is_charging(skill_key)
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
		"ready" if ready else "cooldown %.1fs" % skills.cooldown_remaining(skill_key)]
