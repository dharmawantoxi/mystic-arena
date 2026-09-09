# MysticOptionRow.gd — baris opsi settings generik: label kiri +
# kontrol kanan (slider/toggle/segment) + garis bawah. Dipakai panel
# Settings agar ritme 56px konsisten dengan pygame.
extends HBoxContainer
class_name MysticOptionRow

var label_node: Label
var right_box: HBoxContainer


func _init(p_label: String = "", right: Control = null) -> void:
	custom_minimum_size = Vector2(280, 56)
	alignment = BoxContainer.ALIGNMENT_CENTER
	add_theme_constant_override("separation", 12)
	label_node = Label.new()
	label_node.text = UiTheme.letter(p_label)
	label_node.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UiTheme.style_label(label_node, 15, "body_semibold",
		UiTheme.TEXT_WHITE, true)
	add_child(label_node)
	right_box = HBoxContainer.new()
	right_box.alignment = BoxContainer.ALIGNMENT_END
	right_box.add_theme_constant_override("separation", 8)
	add_child(right_box)
	if right != null:
		right_box.add_child(right)
