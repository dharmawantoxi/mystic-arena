# ComboBadge.gd — port visual ComboCounter.draw pygame (FASE 13).
#
# Counter kill combo di kanan atas layar arena (cx = screen_w - 100, cy =
# 100): teks "x{count}" besar + label ambang (KILLING SPREE! dst, hanya
# count >= 5) + bar jam pasir 80x4 (hanya count >= 2). Dibangun dari kode
# oleh HUD (pola panel lain yang dibangun runtime).
#
# STATE tidak disimpan di sini: badge membaca GameManager.combo tiap frame
# (mesin state ComboCounter.gd — dikunci MatchScoringParityTest). Animasi
# scale mengikuti display_scale mesin itu.
#
# KOMPOSIT PIKSEL (font persis, shadow 8-arah, gradien) = aproksimasi;
# label/warna/lebar bar/anchor terkunci fixture match_scoring.combo.draw.
extends Control

const SCREEN_W := 1280.0

var _count_label: Label
var _tier_label: Label
var _bar_bg: ColorRect
var _bar_fill: ColorRect


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Area bebas di kanan-atas; semua anak diposisikan relatif pusat combo.
	var center := HudLayout.combo_center(SCREEN_W)
	position = Vector2(center.x - 90.0, center.y - 60.0)
	size = Vector2(180.0, 120.0)

	_count_label = Label.new()
	_count_label.position = Vector2(90.0, 60.0) - Vector2(90.0, 34.0)
	_count_label.size = Vector2(180.0, 68.0)
	_count_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_count_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_count_label.add_theme_font_size_override("font_size", 46)
	_count_label.add_theme_color_override("font_outline_color",
		Color(0, 0, 0, 0.9))
	_count_label.add_theme_constant_override("outline_size", 4)
	add_child(_count_label)

	_tier_label = Label.new()
	# Pusat label ambang = (cx, cy - 30) — offset -30 dari pusat combo.
	_tier_label.position = Vector2(0.0, 30.0) - Vector2(0.0, 11.0)
	_tier_label.size = Vector2(180.0, 22.0)
	_tier_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_tier_label.add_theme_font_size_override("font_size", 19)
	_tier_label.add_theme_color_override("font_outline_color",
		Color(0, 0, 0, 0.9))
	_tier_label.add_theme_constant_override("outline_size", 3)
	add_child(_tier_label)

	var bar_rect := HudLayout.combo_bar_rect(SCREEN_W)
	var local := bar_rect.position - position
	_bar_bg = ColorRect.new()
	_bar_bg.position = local
	_bar_bg.size = bar_rect.size
	_bar_bg.color = Color(40.0 / 255.0, 40.0 / 255.0, 40.0 / 255.0)
	add_child(_bar_bg)
	_bar_fill = ColorRect.new()
	_bar_fill.position = local
	_bar_fill.size = Vector2(0, bar_rect.size.y)
	add_child(_bar_fill)

	visible = false


func _process(_delta: float) -> void:
	var combo = GameManager.combo
	if combo == null:
		return
	visible = ComboCounter.is_drawn(combo.count, combo.display_scale)
	# Gate draw pygame: teks hitungan digambar selama gate visible lolos DAN
	# ukurannya masih terbaca (int(48*scale) >= 8) — termasuk "x1" dan sisa
	# animasi "x0" saat decay; BAR hanya count >= 2, label hanya count >= 5.
	var count_size := int(48.0 * combo.display_scale)
	_count_label.visible = count_size >= 8
	_bar_bg.visible = combo.count >= 2
	_bar_fill.visible = combo.count >= 2
	if combo.count >= 2:
		_bar_fill.size.x = ComboCounter.bar_fill_width(combo.timer)
		_bar_fill.color = ComboCounter.display_color(combo.count, 0)
	_tier_label.visible = combo.count >= 5
	if _tier_label.visible:
		_tier_label.text = ComboCounter.tier_label(combo.count)
		_tier_label.add_theme_color_override("font_color",
			ComboCounter.display_color(combo.count, combo.color_flash))
	# Teks hitungan + pulsa scale + warna flash.
	if _count_label.visible:
		var text := ComboCounter.count_text(combo.count)
		if text != _count_label.text:
			_count_label.text = text
		_count_label.add_theme_color_override("font_color",
			ComboCounter.display_color(combo.count, combo.color_flash))
		# Animasi scale mengikuti mesin pygame (display_scale -> ukuran).
		var s: float = clampf(combo.display_scale, 0.0, 1.3)
		_count_label.scale = Vector2(maxf(0.2, s), maxf(0.2, s))
