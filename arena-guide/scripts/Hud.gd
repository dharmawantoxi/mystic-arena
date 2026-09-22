extends CanvasLayer
class_name Hud
## Langkah 10: HUD dari kode - gold, wave, hero, skill QWER.

var _gold_l: Label
var _wave_l: Label
var _hero_l: Label
var _hint_l: Label
var _btns: Array = []
var _main = null


func setup(main_ref) -> void:
	_main = main_ref
	_gold_l = _make_label(16, 12, 300, 36, 28)
	_wave_l = _make_label(0, 12, 1280, 36, 28)
	_wave_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hero_l = _make_label(16, 648, 340, 56, 20)
	_hint_l = _make_label(764, 616, 500, 32, 15)
	_hint_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_hint_l.text = "Klik hero = pilih | Klik map = jalan | Klik slot biru = bangun (100g)"
	var keys: Array = ["Q", "W", "E", "R"]
	for i in 4:
		var b := Button.new()
		b.position = Vector2(384.0 + float(i) * 128.0, 660.0)
		b.size = Vector2(120, 48)
		b.focus_mode = Control.FOCUS_NONE
		b.text = str(keys[i])
		add_child(b)
		b.pressed.connect(_on_skill_btn.bind(i))
		_btns.append(b)


func _make_label(x: float, y: float, w: float, h: float, fsize: int) -> Label:
	var l := Label.new()
	l.position = Vector2(x, y)
	l.size = Vector2(w, h)
	l.add_theme_font_size_override("font_size", fsize)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	l.add_theme_constant_override("shadow_offset_x", 2)
	l.add_theme_constant_override("shadow_offset_y", 2)
	add_child(l)
	return l


func _on_skill_btn(i: int) -> void:
	if _main != null and is_instance_valid(_main):
		_main.cast_hero_skill(i)


func _process(_delta: float) -> void:
	if _main == null or not is_instance_valid(_main):
		return
	_gold_l.text = "GOLD %d" % int(_main.gold)
	var wc: int = int(_main.wave_count)
	_wave_l.text = "WAVE %d" % wc if wc > 0 else "SIAPKAN PERTAHANAN"
	var h = _main.hero
	if h != null and is_instance_valid(h):
		_hero_l.text = "%s  HP %d/%d%s" % [str(h.hero_name), maxi(0, int(h.hp)), int(h.max_hp), "  [PILIH]" if h.selected else ""]
	else:
		_hero_l.text = ""
	var keys: Array = ["Q", "W", "E", "R"]
	for i in _btns.size():
		var b: Button = _btns[i]
		var cd: float = 0.0
		var short_nm: String = str(keys[i])
		if h != null and is_instance_valid(h):
			cd = float(h.skill_cds[i])
			short_nm = str(h.skill_short[i])
		if cd > 0.0:
			b.text = "%s: %s\n%.1f" % [str(keys[i]), short_nm, cd]
			b.disabled = true
		else:
			b.text = "%s: %s\nSIAP" % [str(keys[i]), short_nm]
			b.disabled = false
