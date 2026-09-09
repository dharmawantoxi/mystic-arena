# MysticTopup.gd — dialog TOP UP HERO GOLD (port _draw_topup_dialog).
#
# Dialog modal 920x580: fase select (paket + metode + ringkasan + CANCEL/
# PAY NOW) -> processing (spinner 1.6 dtk, simulasi) -> success (gold masuk
# ke meta_gold + riwayat tx "MA-..."). Tanpa server = MODE SIMULASI persis
# pygame (TOPUP_SERVER_URL kosong). Sinyal closed -> pemilik membuang node.
extends Control
class_name MysticTopup

signal closed

const PACKAGES: Array = [
	{"label": "PAKET 50K", "gold": 50000, "bonus": 0, "price": 10000},
]
const METHODS: Array = ["GOPAY", "OVO", "DANA", "SHOPEEPAY",
	"BANK TRANSFER"]
const PROCESSING_SECONDS := 1.6

var _phase := "select"
var _pkg_idx := 0
var _method_idx := 0
var _tx_id := ""
var _last_total := 0
var _progress := 0.0
var _panel: MysticPanel = null
var _body: VBoxContainer = null
var _subtitle: Label = null
var _spin: Control = null
var _bar: MysticBar = null
var _proc_tween: Tween = null
var _redeem_msg: Label = null


static func price_str(amount_idr: int) -> String:
	var s := str(amount_idr)
	var out := ""
	for i in range(s.length()):
		if i > 0 and (s.length() - i) % 3 == 0:
			out += "."
		out += s[i]
	return "Rp " + out


func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	visible = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 205.0 / 255.0)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)
	_panel = MysticPanel.new(Color8(32, 38, 66), Color8(16, 20, 38),
		Color8(255, 200, 80), 16.0, 3.0, true)
	_panel.tick_length = 16.0
	_panel.anchor_left = 0.5
	_panel.anchor_right = 0.5
	_panel.anchor_top = 0.5
	_panel.anchor_bottom = 0.5
	_panel.offset_left = -460.0
	_panel.offset_right = 460.0
	_panel.offset_top = -290.0
	_panel.offset_bottom = 290.0
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 24)
	margin.add_theme_constant_override("margin_right", 24)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_bottom", 14)
	_panel.add_child(margin)
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	margin.add_child(vbox)
	var title := MysticTitle.new("TOP UP HERO GOLD", 34)
	title.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	vbox.add_child(title)
	_subtitle = Label.new()
	_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(_subtitle, 13, "body", Color8(160, 170, 190))
	vbox.add_child(_subtitle)
	var sep := MysticFlourish.new(false)
	vbox.add_child(sep)
	_body = VBoxContainer.new()
	_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_theme_constant_override("separation", 8)
	vbox.add_child(_body)


func open() -> void:
	_phase = "select"
	visible = true
	_rebuild()


func _clear_body() -> void:
	for c in _body.get_children():
		_body.remove_child(c)
		c.queue_free()
	if _proc_tween != null and _proc_tween.is_valid():
		_proc_tween.kill()
	_proc_tween = null


func _rebuild() -> void:
	_clear_body()
	_subtitle.text = {
		"redeem": ("REDEEM CODE - enter the code you received from admin "
			+ "after paying"),
		"processing": "Please wait - do not close the dialog",
		"success": "Transaction complete",
	}.get(_phase, "Top up gold untuk membuka hero di HERO SHOP")
	match _phase:
		"select":
			_build_select()
		"processing":
			_build_processing()
		"success":
			_build_success()
		"redeem":
			_build_redeem()


func _pkg() -> Dictionary:
	return PACKAGES[_pkg_idx]


func _pkg_total() -> int:
	return int(_pkg().get("gold", 0)) + int(_pkg().get("bonus", 0))


# ── FASE SELECT ───────────────────────────────────────────

func _build_select() -> void:
	var cols := HBoxContainer.new()
	cols.add_theme_constant_override("separation", 16)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(cols)
	# Kiri: paket.
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 8)
	cols.add_child(left)
	var l1 := Label.new()
	l1.text = "1. CHOOSE PACKAGE"
	UiTheme.style_label(l1, 13, "body_bold", Color8(140, 190, 150))
	left.add_child(l1)
	var pad1 := Control.new()
	pad1.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(pad1)
	for i in PACKAGES.size():
		left.add_child(_package_card(i))
	var pad2 := Control.new()
	pad2.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(pad2)
	# Kanan: metode.
	var right := VBoxContainer.new()
	right.custom_minimum_size = Vector2(300, 0)
	right.add_theme_constant_override("separation", 6)
	cols.add_child(right)
	var l2 := Label.new()
	l2.text = "2. PAYMENT METHOD"
	UiTheme.style_label(l2, 13, "body_bold", Color8(140, 190, 150))
	right.add_child(l2)
	for i in METHODS.size():
		right.add_child(_method_row(i))
	var redeem := Button.new()
	redeem.text = "REDEEM CODE"
	redeem.custom_minimum_size = Vector2(0, 38)
	redeem.focus_mode = Control.FOCUS_NONE
	redeem.add_theme_font_override("font", UiTheme.font("body_bold"))
	redeem.add_theme_font_size_override("font_size", 13)
	redeem.add_theme_color_override("font_color", Color8(255, 225, 150))
	_style_box_btn(redeem, Color8(40, 36, 20), Color8(190, 160, 80), 2)
	right.add_child(redeem)
	redeem.pressed.connect(func() -> void:
		_phase = "redeem"
		_rebuild())
	# Ringkasan.
	var sep := MysticFlourish.new(false)
	_body.add_child(sep)
	var sum := HBoxContainer.new()
	_body.add_child(sum)
	var tot_t := Label.new()
	tot_t.text = "TOTAL GOLD: "
	UiTheme.style_label(tot_t, 15, "body", Color8(170, 180, 200))
	sum.add_child(tot_t)
	var tot_v := Label.new()
	tot_v.text = "+%s" % _fmt(_pkg_total())
	UiTheme.style_label(tot_v, 18, "body_bold", UiTheme.GOLD)
	sum.add_child(tot_v)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sum.add_child(spacer)
	var price := Label.new()
	price.text = price_str(int(_pkg().get("price", 0)))
	UiTheme.style_label(price, 18, "body_bold", UiTheme.TEXT_WHITE)
	sum.add_child(price)
	var note := Label.new()
	note.text = "Simulated payment - no real charge."
	UiTheme.style_label(note, 12, "body", Color8(120, 130, 150))
	_body.add_child(note)
	# Tombol bawah.
	var btns := HBoxContainer.new()
	btns.add_theme_constant_override("separation", 12)
	_body.add_child(btns)
	var cancel := MysticPill.new("CANCEL", "neutral", "", 18, false)
	cancel.custom_minimum_size = Vector2(170, 52)
	btns.add_child(cancel)
	cancel.pressed.connect(_on_cancel)
	var sp2 := Control.new()
	sp2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btns.add_child(sp2)
	var pay := MysticPill.new("PAY NOW  •  %s" % price_str(
		int(_pkg().get("price", 0))), "success", "coin", 18, false)
	pay.custom_minimum_size = Vector2(340, 52)
	btns.add_child(pay)
	pay.pressed.connect(_on_pay)


func _package_card(idx: int) -> Button:
	var pkg: Dictionary = PACKAGES[idx]
	var selected := idx == _pkg_idx
	var b := Button.new()
	b.text = ""
	b.custom_minimum_size = Vector2(0, 92)
	b.focus_mode = Control.FOCUS_NONE
	var bg := Color8(22, 66, 44) if selected else Color8(28, 34, 54)
	var edge := Color8(120, 255, 160) if selected else Color8(75, 85, 110)
	_style_box_btn(b, bg, edge, 3 if selected else 1, 10)
	var vbox := VBoxContainer.new()
	vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.set_anchors_preset(Control.PRESET_FULL_RECT)
	vbox.offset_left = 12
	vbox.offset_right = -12
	vbox.offset_top = 9
	vbox.offset_bottom = -9
	vbox.add_theme_constant_override("separation", 2)
	b.add_child(vbox)
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_child(row)
	var lb := Label.new()
	lb.text = str(pkg.get("label", ""))
	lb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_label(lb, 13, "body_bold",
		Color8(255, 220, 130) if selected else Color8(170, 180, 200))
	row.add_child(lb)
	var sp := Control.new()
	sp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(sp)
	var pr := Label.new()
	pr.text = price_str(int(pkg.get("price", 0)))
	pr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_label(pr, 15, "body_semibold",
		UiTheme.TEXT_WHITE if selected else Color8(200, 205, 220))
	row.add_child(pr)
	var grow := HBoxContainer.new()
	grow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	grow.add_theme_constant_override("separation", 6)
	vbox.add_child(grow)
	var icon := MysticIcon.new("coin", UiTheme.GOLD, 1.1)
	grow.add_child(icon)
	var gl := Label.new()
	gl.text = "+%s" % _fmt(_pkg_total())
	gl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_label(gl, 20, "body_bold", Color8(255, 200, 50))
	grow.add_child(gl)
	var gu := Label.new()
	gu.text = "GOLD"
	gu.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_label(gu, 12, "body_bold", Color8(200, 160, 60))
	grow.add_child(gu)
	b.pressed.connect(func() -> void:
		_pkg_idx = idx
		_rebuild())
	return b


func _method_row(idx: int) -> Button:
	var selected := idx == _method_idx
	var b := Button.new()
	b.text = "%s %s" % ["●" if selected else "○", METHODS[idx]]
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.custom_minimum_size = Vector2(0, 36)
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_override("font", UiTheme.font("body_semibold"))
	b.add_theme_font_size_override("font_size", 14)
	b.add_theme_color_override("font_color",
		Color8(235, 255, 240) if selected else Color8(190, 200, 215))
	var bg := Color8(22, 66, 44) if selected else Color8(28, 34, 54)
	var edge := Color8(120, 255, 160) if selected else Color8(75, 85, 110)
	_style_box_btn(b, bg, edge, 2 if selected else 1, 8)
	b.pressed.connect(func() -> void:
		_method_idx = idx
		_rebuild())
	return b


func _style_box_btn(b: Button, bg: Color, edge: Color, bw: int,
		radius: int = 8) -> void:
	var normal := StyleBoxFlat.new()
	normal.bg_color = bg
	normal.border_color = edge
	normal.set_border_width_all(bw)
	normal.set_corner_radius_all(radius)
	normal.content_margin_left = 12.0
	normal.content_margin_right = 12.0
	var hover := normal.duplicate() as StyleBoxFlat
	hover.border_color = Color8(120, 230, 150)
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", normal)
	b.add_theme_stylebox_override("focus", normal)


func _on_cancel() -> void:
	if _phase == "processing":
		return
	visible = false
	closed.emit()


func _on_pay() -> void:
	if _phase != "select":
		return
	_phase = "processing"
	_progress = 0.0
	_rebuild()


# ── FASE PROCESSING ───────────────────────────────────────

func _build_processing() -> void:
	var pkg: Dictionary = _pkg()
	var center := VBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 10)
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(center)
	_spin = _Spinner.new()
	_spin.custom_minimum_size = Vector2(96, 96)
	_spin.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	center.add_child(_spin)
	var t1 := Label.new()
	t1.text = "PROCESSING PAYMENT..."
	t1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(t1, 20, "body_semibold", UiTheme.TEXT_WHITE, true)
	center.add_child(t1)
	var t2 := Label.new()
	t2.text = "via %s  •  %s" % [METHODS[_method_idx],
		price_str(int(pkg.get("price", 0)))]
	t2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(t2, 15, "body", Color8(170, 180, 200))
	center.add_child(t2)
	_bar = MysticBar.new()
	_bar.custom_minimum_size = Vector2(360, 10)
	_bar.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_bar.track_top = Color8(40, 48, 68)
	_bar.track_bottom = Color8(40, 48, 68)
	_bar.fill_top = Color8(120, 255, 160)
	_bar.fill_bottom = Color8(120, 255, 160)
	_bar.edge_color = Color8(90, 100, 130)
	_bar.show_text = false
	_bar.fill_ratio = 0.0
	center.add_child(_bar)
	_proc_tween = create_tween()
	_proc_tween.tween_property(_bar, "fill_ratio", 1.0,
		PROCESSING_SECONDS)
	_proc_tween.tween_callback(_on_processing_done)


func _on_processing_done() -> void:
	var total := _pkg_total()
	_last_total = total
	_tx_id = "MA-%010d" % (int(Time.get_ticks_msec()) % 10000000000)
	SaveManager.add_meta_gold(total)
	if not (SaveManager.data.get("topup_history") is Array):
		SaveManager.data["topup_history"] = []
	(SaveManager.data["topup_history"] as Array).append({
		"tx": _tx_id,
		"pkg": str(_pkg().get("label", "")),
		"gold": int(_pkg().get("gold", 0)),
		"bonus": int(_pkg().get("bonus", 0)),
		"method": METHODS[_method_idx],
	})
	SaveManager.save()
	AudioManager.play_sfx("ui_buy", 1.0)
	_phase = "success"
	_rebuild()


# ── FASE SUCCESS ──────────────────────────────────────────

func _build_success() -> void:
	var pkg: Dictionary = _pkg()
	var center := VBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 10)
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(center)
	var ring := _CheckRing.new()
	ring.custom_minimum_size = Vector2(96, 96)
	ring.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	center.add_child(ring)
	var t1 := Label.new()
	t1.text = "TOP UP SUCCESSFUL!"
	t1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(t1, 20, "body_bold", UiTheme.GOLD_TEXT, true)
	center.add_child(t1)
	var t2 := Label.new()
	t2.text = "+%s HERO GOLD ADDED" % _fmt(_last_total)
	t2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(t2, 20, "body_semibold", UiTheme.GOLD)
	center.add_child(t2)
	var tx := Label.new()
	tx.text = "TX ID: %s   •   %s   •   %s" % [_tx_id,
		METHODS[_method_idx], price_str(int(pkg.get("price", 0)))]
	tx.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(tx, 13, "body", Color8(150, 160, 180))
	center.add_child(tx)
	var back := MysticPill.new("BACK", "neutral", "", 16, false)
	back.custom_minimum_size = Vector2(220, 48)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	center.add_child(back)
	back.pressed.connect(_on_cancel)


# ── FASE REDEEM ───────────────────────────────────────────

func _build_redeem() -> void:
	var top := HBoxContainer.new()
	top.alignment = BoxContainer.ALIGNMENT_END
	_body.add_child(top)
	var vback := MysticPill.new("BACK", "neutral", "", 12, false)
	vback.custom_minimum_size = Vector2(68, 30)
	top.add_child(vback)
	vback.pressed.connect(func() -> void:
		_phase = "select"
		_rebuild())
	var center := VBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 12)
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(center)
	var prompt := Label.new()
	prompt.text = "ENTER VOUCHER CODE"
	prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(prompt, 16, "body_bold", UiTheme.GOLD_TEXT)
	center.add_child(prompt)
	var edit := LineEdit.new()
	edit.placeholder_text = "MA-XXXX-XXXX"
	edit.custom_minimum_size = Vector2(320, 44)
	edit.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	edit.alignment = HORIZONTAL_ALIGNMENT_CENTER
	edit.add_theme_font_override("font", UiTheme.font("body_bold"))
	edit.add_theme_font_size_override("font_size", 18)
	center.add_child(edit)
	_redeem_msg = Label.new()
	_redeem_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(_redeem_msg, 13, "body", UiTheme.RED)
	center.add_child(_redeem_msg)
	var go := MysticPill.new("REDEEM", "gold", "", 16, false)
	go.custom_minimum_size = Vector2(220, 48)
	go.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	center.add_child(go)
	go.pressed.connect(func() -> void:
		_redeem_msg.text = "Invalid or already-used code.")


static func _fmt(n: int) -> String:
	var s := str(n)
	var out := ""
	for i in range(s.length()):
		if i > 0 and (s.length() - i) % 3 == 0:
			out += ","
		out += s[i]
	return out


## Spinner 3 busur berputar (port _draw_topup_processing).
class _Spinner extends Control:
	var _t := 0.0

	func _process(delta: float) -> void:
		_t += delta
		queue_redraw()

	func _draw() -> void:
		var c := size * 0.5
		for k in 3:
			var start := _t * TAU + TAU * float(k) / 3.0
			draw_arc(c, 44.0, start, start + TAU / 4.0, 24,
				Color8(120, 255, 160), 5.0, true)


## Lingkaran centang sukses.
class _CheckRing extends Control:
	func _draw() -> void:
		var c := size * 0.5
		UiTheme.draw_ring(c, 46.0, Color8(16, 60, 36), 6.0)
		draw_circle(c, 40.0, Color8(30, 120, 66))
		draw_line(c + Vector2(-18, -2), c + Vector2(-4, 14),
			Color8(140, 255, 175), 6.0, true)
		draw_line(c + Vector2(-4, 14), c + Vector2(20, -16),
			Color8(140, 255, 175), 6.0, true)
