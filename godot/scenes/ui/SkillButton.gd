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
	_build_children()
	pressed.connect(_on_pressed)


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
	_key_label.add_theme_font_size_override("font_size", 20)
	_key_label.add_theme_color_override("font_color", Color(1, 0.92, 0.45))
	_key_label.add_theme_color_override("font_outline_color", Color(0.04, 0.03, 0.08, 0.9))
	_key_label.add_theme_constant_override("outline_size", 4)
	_key_label.position = Vector2(6, 2)
	add_child(_key_label)

	_cd_label = Label.new()
	_cd_label.name = "CooldownLabel"
	_cd_label.text = ""
	_cd_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cd_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_cd_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_cd_label.add_theme_font_size_override("font_size", 19)
	_cd_label.add_theme_color_override("font_color", Color(1, 1, 1, 0.95))
	_cd_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_cd_label)

	_name_label = Label.new()
	_name_label.name = "SkillName"
	_name_label.text = ""
	_name_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_label.clip_text = true
	_name_label.add_theme_font_size_override("font_size", 9)
	_name_label.add_theme_color_override("font_color", Color(0.82, 0.87, 1.0, 0.9))
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
		_cd_label.text = "%d" % int(ceil(skills.cooldown_remaining(skill_key)))
		modulate = Color(0.78, 0.8, 0.88, 1.0)
	_name_label.text = str(skills.skill_label(skill_key))
	tooltip_text = "%s (%s) — %s" % [
		skill_key.to_upper(), str(skills.skill_label(skill_key)),
		"siap" if ready else "cooldown %.1fs" % skills.cooldown_remaining(skill_key)]
