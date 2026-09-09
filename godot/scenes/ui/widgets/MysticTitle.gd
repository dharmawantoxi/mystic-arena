# MysticTitle.gd — judul gradien Cinzel (port gradient_text/outline_text).
#
# Label dengan shader gradasi vertikal (label_gradient.gdshader) + lapisan
# bayangan SUSUN yang meniru outline_text pygame: 8 offset gelap (opaque)
# + 1 bayangan lembut + badan gradasi. `text` Label tetap = teks asli
# (tes paritas memakai properti teks node bernama *Title*).
extends Control
class_name MysticTitle

var title_label: Label
var _layers: Array[Label] = []

@export var font_size: int = 54:
	set(v):
		font_size = v
		_refresh()
@export var top_color: Color = Color8(255, 232, 158):
	set(v):
		top_color = v
		_refresh()
@export var bottom_color: Color = Color8(196, 138, 42):
	set(v):
		bottom_color = v
		_refresh()
@export var outline_color: Color = Color8(8, 9, 18):
	set(v):
		outline_color = v
		_refresh()
@export var show_outline: bool = true:
	set(v):
		show_outline = v
		_refresh()
@export var title_text: String = "":
	set(v):
		title_text = v
		if title_label != null:
			title_label.text = v
		for l in _layers:
			l.text = v
		_refresh()


func _init(p_text: String = "", p_size: int = 54,
		p_top: Color = Color8(255, 232, 158),
		p_bottom: Color = Color8(196, 138, 42),
		p_outline: bool = true) -> void:
	title_text = p_text
	font_size = p_size
	top_color = p_top
	bottom_color = p_bottom
	show_outline = p_outline
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	for l in _layers:
		l.queue_free()
	_layers.clear()
	# Lapisan 1: 8 outline gelap (offset 3px, opaque) — versi Label.
	var offs := [Vector2(-3, -3), Vector2(0, -3), Vector2(3, -3),
		Vector2(-3, 0), Vector2(3, 0), Vector2(-3, 3), Vector2(0, 3),
		Vector2(3, 3)]
	var pad := 6.0
	for o in offs:
		var ol := _make_label(outline_color, null)
		ol.position = o + Vector2(pad, pad)
		add_child(ol)
		_layers.append(ol)
	# Lapisan 2: bayangan lembut (offset +3,+3).
	var sh := _make_label(Color(0, 0, 0, 0.75), null)
	sh.position = Vector2(3 + pad, 3 + pad)
	add_child(sh)
	_layers.append(sh)
	# Lapisan 3: badan gradasi.
	var mat := ShaderMaterial.new()
	mat.shader = UiTheme.gradient_shader()
	mat.set_shader_parameter("top_color", top_color)
	mat.set_shader_parameter("bottom_color", bottom_color)
	title_label = _make_label(Color.WHITE, mat)
	title_label.position = Vector2(pad, pad)
	title_label.name = "TitleLabel"
	add_child(title_label)
	for l in _layers:
		l.visible = show_outline
	_refresh()


func _make_label(color: Color, mat: Material) -> Label:
	var l := Label.new()
	l.text = title_text
	l.add_theme_font_override("font", UiTheme.font("title"))
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if mat != null:
		l.material = mat
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.set_anchors_preset(Control.PRESET_FULL_RECT)
	return l


func _refresh() -> void:
	if not is_node_ready():
		return
	var f := UiTheme.font("title")
	var sz := f.get_string_size(title_text, HORIZONTAL_ALIGNMENT_LEFT, -1,
		font_size)
	var h := f.get_ascent(font_size) + f.get_descent(font_size)
	custom_minimum_size = Vector2(maxf(60.0, sz.x + 12.0), h + 12.0)
	size = custom_minimum_size
	if title_label != null and title_label.material != null:
		var mat := title_label.material as ShaderMaterial
		mat.set_shader_parameter("top_color", top_color)
		mat.set_shader_parameter("bottom_color", bottom_color)
	for l in _layers:
		l.text = title_text
		l.visible = show_outline


func set_text(t: String) -> void:
	title_text = t
