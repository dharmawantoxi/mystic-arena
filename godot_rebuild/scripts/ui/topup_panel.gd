extends Control
## Layer 9au: the TOP UP HERO GOLD dialog (`Menu._draw_topup_*`). A modal over
## the hero shop with the select / processing / paying / success / redeem
## phases of `TopupFlow`. Buttons forward their source ids to `flow.click()`;
## the panel only renders the flow state.

const TopupFlow = preload("res://scripts/match/topup_flow.gd")
const TopupVoucher = preload("res://scripts/match/topup_voucher.gd")
const TopupCurrency = preload("res://scripts/match/topup_currency.gd")
const DIALOG_SIZE := Vector2(920, 580)
const TITLE := "TOP UP HERO GOLD"
const SUBTITLES := {
	"redeem": "REDEEM CODE - enter the code you received from admin after paying",
	"processing": "Please wait - do not close the dialog",
	"success": "Transaction complete",
}
const SUBTITLE_DEFAULT := "Top up gold untuk membuka hero di HERO SHOP"
const KEYPAD: Array[Array] = [
	["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["del", "0", "redeem"]
]
const GOLD := Color(255 / 255.0, 200 / 255.0, 50 / 255.0)
const MUTED := Color(170 / 255.0, 180 / 255.0, 200 / 255.0)

var flow: TopupFlow
var _title: Label
var _subtitle: Label
var _pages: Dictionary = {}
var _package_buttons: Array[Button] = []
var _method_buttons: Array[Button] = []
var _total: Label
var _note: Label
var _pay: Button
var _processing: ProgressBar
var _processing_sub: Label
var _pay_status: Label
var _pay_msg: Label
var _qr: TextureRect
var _invoice: Label
var _paid: Button
var _retry: Button
var _cancel_pay: Button
var _success_title: Label
var _success_total: Label
var _success_tx: Label
var _redeem_display: Label
var _redeem_msg: Label
var _qr_signature := 0


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false


func _ready() -> void:
	_build()
	if flow != null:
		refresh()


func bind(flow_value: TopupFlow) -> void:
	if flow != null and flow.changed.is_connected(refresh):
		flow.changed.disconnect(refresh)
	flow = flow_value
	flow.changed.connect(refresh)
	if is_inside_tree():
		refresh()


func _process(_delta: float) -> void:
	if flow != null and flow.is_open:
		flow.tick()


func refresh() -> void:
	if flow == null or _title == null:
		return
	visible = flow.is_open
	if not visible:
		return
	_subtitle.text = String(SUBTITLES.get(flow.phase, SUBTITLE_DEFAULT))
	for key in _pages:
		(_pages[key] as Control).visible = key == flow.phase
	match flow.phase:
		"select":
			_refresh_select()
		"processing":
			_processing.value = flow.progress
			_processing_sub.text = (
				"via %s  •  %s" % [String(flow.payment_method().label), flow.price_text()]
			)
		"paying":
			_refresh_paying()
		"success":
			_refresh_success()
		"redeem":
			_redeem_display.text = flow.redeem_input if not flow.redeem_input.is_empty() else "MA-"
			_redeem_display.modulate = Color.WHITE if not flow.redeem_input.is_empty() else MUTED
			_redeem_msg.text = flow.redeem_msg
			_redeem_msg.visible = not flow.redeem_msg.is_empty()


func _refresh_select() -> void:
	for index in range(_package_buttons.size()):
		var pkg: Dictionary = TopupFlow.PACKAGES[index]
		var total := int(pkg.gold) + int(pkg.get("bonus", 0))
		var text := "%s\n+%s GOLD" % [String(pkg.label), _group(total)]
		if int(pkg.get("bonus", 0)) > 0:
			text += "\nincl. +%s BONUS" % _group(int(pkg.bonus))
		_package_buttons[index].text = text
		_package_buttons[index].button_pressed = index == flow.pkg_idx
	for index in range(_method_buttons.size()):
		_method_buttons[index].button_pressed = index == flow.method_idx
	var package := flow.package()
	_total.text = "TOTAL GOLD: +%s" % _group(int(package.gold) + int(package.get("bonus", 0)))
	if flow.server_url.is_empty():
		_note.text = "Simulated payment - no real charge."
	else:
		_note.text = "Payment via QRIS / e-wallet / VA bank."
	_pay.text = "PAY NOW  •  %s" % flow.price_text()


func _refresh_paying() -> void:
	var state := flow.pay_state
	_pay_msg.visible = state == "error"
	_retry.visible = state == "error"
	_paid.visible = state == "awaiting"
	_qr.visible = state == "awaiting"
	_invoice.visible = state == "awaiting"
	_cancel_pay.visible = state != "creating"
	_cancel_pay.text = "BACK" if state == "error" else "CANCEL"
	match state:
		"creating":
			_pay_status.text = "PREPARING PAYMENT..."
		"error":
			_pay_status.text = "PAYMENT FAILED"
			_pay_msg.text = flow.pay_msg if not flow.pay_msg.is_empty() else "Payment failed."
		_:
			_pay_status.text = "AWAITING PAYMENT..."
			var pkg := flow.package()
			var lines := [
				"INVOICE  %s  (+%s GOLD)" % [String(pkg.label), _group(int(pkg.gold))],
				"ID: %s" % String(flow.invoice.get("id", "-")),
				"SCAN WITH ANY QRIS APP",
			]
			if bool(flow.invoice.get("mock", false)):
				lines.append("MOCK MODE - simulated payment")
			_invoice.text = "\n".join(lines)
			_update_qr()


func _update_qr() -> void:
	var signature := flow.qr_bytes.size()
	if signature == _qr_signature:
		return
	_qr_signature = signature
	if flow.qr_bytes.is_empty():
		_qr.texture = null
		return
	var image := Image.new()
	if image.load_png_from_buffer(flow.qr_bytes) == OK:
		_qr.texture = ImageTexture.create_from_image(image)


func _refresh_success() -> void:
	var is_redeem := flow.last_method == "redeem"
	_success_title.text = "CODE REDEEMED!" if is_redeem else "TOP UP SUCCESSFUL!"
	_success_total.text = "+%s HERO GOLD ADDED" % _group(flow.last_total)
	if is_redeem:
		_success_tx.text = "TX ID: %s   •   CODE %s" % [flow.tx_id, flow.redeem_code]
	else:
		_success_tx.text = (
			"TX ID: %s   •   %s   •   %s"
			% [flow.tx_id, String(flow.payment_method().label), flow.price_text()]
		)


func _build() -> void:
	var dim := ColorRect.new()
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.0, 0.0, 0.0, 0.8)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(center)
	var card := PanelContainer.new()
	card.custom_minimum_size = DIALOG_SIZE
	center.add_child(card)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 8)
	card.add_child(column)
	_title = _label(column, TITLE, 30, Color8(255, 200, 80))
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_subtitle = _label(column, SUBTITLE_DEFAULT, 14, Color8(160, 170, 190))
	_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(HSeparator.new())
	_pages["select"] = _build_select(column)
	_pages["processing"] = _build_processing(column)
	_pages["paying"] = _build_paying(column)
	_pages["success"] = _build_success(column)
	_pages["redeem"] = _build_redeem(column)


func _build_select(parent: Control) -> Control:
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 10)
	parent.add_child(page)
	_label(page, "1. GOLD PACKAGE", 16, Color8(140, 190, 150))
	var packages := HBoxContainer.new()
	packages.add_theme_constant_override("separation", 12)
	page.add_child(packages)
	for index in range(TopupFlow.PACKAGES.size()):
		var button := _button(packages, "", "topup_pkg_%d" % index, Vector2(220, 96))
		button.toggle_mode = true
		_package_buttons.append(button)
	_label(page, "2. PAYMENT METHOD", 16, Color8(140, 190, 150))
	var methods := HBoxContainer.new()
	methods.add_theme_constant_override("separation", 10)
	page.add_child(methods)
	for index in range(TopupFlow.PAYMENT_METHODS.size()):
		var method: Dictionary = TopupFlow.PAYMENT_METHODS[index]
		var button := _button(
			methods, String(method.label), "topup_method_%d" % index, Vector2(160, 46)
		)
		button.toggle_mode = true
		_method_buttons.append(button)
	var redeem := _button(page, "REDEEM CODE", "topup_redeem", Vector2(220, 44))
	redeem.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_total = _label(page, "", 20, GOLD)
	_note = _label(page, "", 13, MUTED)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 16)
	actions.alignment = BoxContainer.ALIGNMENT_END
	page.add_child(actions)
	_button(actions, "CANCEL", "topup_cancel", Vector2(170, 48))
	_pay = _button(actions, "PAY NOW", "topup_pay", Vector2(320, 48))
	return page


func _build_processing(parent: Control) -> Control:
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 14)
	page.alignment = BoxContainer.ALIGNMENT_CENTER
	parent.add_child(page)
	var status := _label(page, "PROCESSING PAYMENT...", 20, Color8(240, 245, 250))
	status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_processing_sub = _label(page, "", 14, MUTED)
	_processing_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_processing = ProgressBar.new()
	_processing.max_value = 1.0
	_processing.step = 0.0
	_processing.show_percentage = false
	_processing.custom_minimum_size = Vector2(520, 18)
	_processing.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	page.add_child(_processing)
	return page


func _build_paying(parent: Control) -> Control:
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 10)
	page.alignment = BoxContainer.ALIGNMENT_CENTER
	parent.add_child(page)
	_pay_status = _label(page, "", 20, Color8(240, 245, 250))
	_pay_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_pay_msg = _label(page, "", 15, Color8(255, 120, 120))
	_pay_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_qr = TextureRect.new()
	_qr.custom_minimum_size = Vector2(220, 220)
	_qr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_qr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_qr.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	page.add_child(_qr)
	_invoice = _label(page, "", 14, MUTED)
	_invoice.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var hint := _label(
		page,
		(
			"Pembayaran via QRIS / GoPay / OVO / DANA / VA bank.\n"
			+ "Gold masuk otomatis setelah pembayaran terverifikasi."
		),
		13,
		MUTED
	)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 16)
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	page.add_child(actions)
	_cancel_pay = _button(actions, "CANCEL", "topup_cancel_pay", Vector2(170, 48))
	_paid = _button(actions, "I'VE PAID", "topup_paid", Vector2(220, 48))
	_retry = _button(actions, "TRY AGAIN", "topup_retry", Vector2(220, 48))
	return page


func _build_success(parent: Control) -> Control:
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 14)
	page.alignment = BoxContainer.ALIGNMENT_CENTER
	parent.add_child(page)
	_success_title = _label(page, "", 24, Color8(255, 220, 100))
	_success_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_success_total = _label(page, "", 22, GOLD)
	_success_total.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_success_tx = _label(page, "", 13, Color8(150, 160, 180))
	_success_tx.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var back := _button(page, "BACK", "topup_back", Vector2(220, 48))
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	return page


func _build_redeem(parent: Control) -> Control:
	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 8)
	parent.add_child(page)
	var back := _button(page, "BACK", "vback", Vector2(120, 36))
	back.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_redeem_display = _label(page, "MA-", 30, Color.WHITE)
	_redeem_display.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var format_hint := _label(
		page,
		"Format: %s123456  (4-%d digits)" % [TopupVoucher.CODE_PREFIX, TopupVoucher.MAX_DIGITS],
		13,
		MUTED
	)
	format_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_redeem_msg = _label(page, "", 15, TopupFlow.MSG_COLOR)
	_redeem_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	page.add_child(grid)
	for row in KEYPAD:
		for key_value in row:
			var key := String(key_value)
			var label := key.to_upper() if key != "redeem" else "REDEEM"
			_button(grid, label, "vpk_" + key, Vector2(120, 52))
	return page


func _label(parent: Control, label_text: String, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = label_text
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	parent.add_child(label)
	return label


func _button(parent: Control, label_text: String, btn_id: String, min_size: Vector2) -> Button:
	var button := Button.new()
	button.text = label_text
	button.name = btn_id
	button.custom_minimum_size = min_size
	button.pressed.connect(func() -> void: _press(btn_id))
	parent.add_child(button)
	return button


func _press(btn_id: String) -> void:
	if flow != null:
		flow.click(btn_id)


## Dialog-local button lookup (tests + external callers).
func find_button(btn_id: String) -> Button:
	return find_child(btn_id, true, false) as Button


func _input(event: InputEvent) -> void:
	if flow == null or not flow.is_open:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_ESCAPE:
			if flow.phase == "redeem":
				flow.click("vback")
			elif flow.phase == "paying":
				flow.click("topup_cancel_pay")
			else:
				flow.click("topup_cancel")
			get_viewport().set_input_as_handled()
		elif flow.key(event.keycode):
			get_viewport().set_input_as_handled()


static func _group(value: int) -> String:
	return TopupCurrency.group_thousands(str(value))
