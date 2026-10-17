extends RefCounted
## Layer 9au: the top-up dialog state machine of `_core.py` (`Menu.topup_*`,
## `Menu._redeem_*`, `Menu._topup_server_tick`).
##
## Phases: `select` (package + payment method) -> `processing` (simulation,
## 1.6 s bar, no server URL) or `paying` (server: create invoice -> QR -> poll
## status every 60/120 frames -> auto grant) -> `success`; `redeem` is the
## manual voucher keypad. Gold, `redeemed_codes` and `topup_history` live in
## the profile dictionary and are persisted through the `save` callable.
##
## The flow is headless: HTTP goes through a transport object exposing
## `send(method: String, path: String, payload: Variant)` and reporting back
## with `on_http_result(ok, status, body)`. Sounds are emitted as a signal.

signal changed
signal sound_requested(key: String)

const TopupCurrency = preload("res://scripts/match/topup_currency.gd")
const TopupVoucher = preload("res://scripts/match/topup_voucher.gd")

const PACKAGES: Array[Dictionary] = [
	{"label": "PAKET 50K", "gold": 50000, "bonus": 0, "price": 10000},
]
const PAYMENT_METHODS: Array[Dictionary] = [
	{"id": "gopay", "label": "GOPAY"},
	{"id": "ovo", "label": "OVO"},
	{"id": "dana", "label": "DANA"},
	{"id": "shopeepay", "label": "SHOPEEPAY"},
	{"id": "bank", "label": "BANK TRANSFER"},
]
const PROCESSING_SECONDS := 1.6
const HISTORY_CAP := 50
const REDEEMED_CAP := 50
const POLL_DELAY_FIRST := 60
const POLL_DELAY_REPEAT := 120
const HTTP_TIMEOUT := 6.0
const ENV_SERVER_URL := "MYSTIC_TOPUP_URL"
const CREATE_PATH := "/api/topup/create"
const STATUS_PATH := "/api/topup/status/"
const QR_PATH := "/api/topup/qr/"
const MSG_UNREACHABLE := "Top up server tidak terjangkau.\nPeriksa koneksi lalu coba lagi."
const MSG_NOT_SETTLED := "Pembayaran tidak selesai.\nSilakan coba lagi."
const MSG_INVALID := "Invalid code. Format: MA-123456"
const MSG_ALREADY := "Code already redeemed."
const MSG_UNKNOWN := "Unknown code. Contact admin."
const MSG_COLOR := Color(255 / 255.0, 120 / 255.0, 120 / 255.0)

var is_open := false
var phase := "select"
var pkg_idx := 0
var method_idx := 0
var progress := 0.0
var tx_id := ""
var last_total := 0
var currency := "IDR"
var redeem_input := ""
var redeem_msg := ""
var redeem_code := ""
var last_method := ""
var server_url := ""
var pay_state := "idle"
var pay_msg := ""
var invoice := {}
var qr_bytes := PackedByteArray()
var poll_next := 0
var frame := 0
var profile := {"meta_gold": 0}
## Transport with `send(method, path, payload)`; null = simulation only.
var transport: Object
## `Callable(profile: Dictionary) -> bool`; persists the profile after a grant.
var save_callable := Callable()
## `Callable() -> Variant` returning the allowlist dictionary or null (demo).
var allowlist_callable := Callable()
## `Callable() -> int` milliseconds since the Unix epoch (tx ids + history ts).
var clock_callable := Callable()
var http_busy := false
var http_purpose := ""
var _http_result: Array = []
var _http_done := false


## PNG signature prefix (0x89 "PNG"), what the source checks on the QR body.
static func png_magic() -> PackedByteArray:
	return PackedByteArray([0x89, 0x50, 0x4E, 0x47])


static func default_server_url() -> String:
	return OS.get_environment(ENV_SERVER_URL).strip_edges()


## Current package / payment method dictionaries.
func package() -> Dictionary:
	return PACKAGES[clampi(pkg_idx, 0, PACKAGES.size() - 1)]


func payment_method() -> Dictionary:
	return PAYMENT_METHODS[clampi(method_idx, 0, PAYMENT_METHODS.size() - 1)]


func price_text(amount_idr: float = -1.0) -> String:
	var amount := amount_idr if amount_idr >= 0.0 else float(package().price)
	return TopupCurrency.format_price(amount, currency if not currency.is_empty() else "IDR")


func meta_gold() -> int:
	return int(profile.get("meta_gold", 0))


## Mirrors the `topup_open` button: reset the dialog to package selection.
func open() -> void:
	is_open = true
	phase = "select"
	progress = 0.0
	redeem_input = ""
	redeem_msg = ""
	pay_state = "idle"
	pay_msg = ""
	invoice = {}
	qr_bytes = PackedByteArray()
	changed.emit()


func close() -> void:
	is_open = false
	changed.emit()


## Button ids follow the source click handler one-to-one.
func click(btn_id: String) -> void:
	match btn_id:
		"topup_open":
			open()
		"topup_cancel":
			if phase != "processing":
				close()
		"topup_back":
			close()
		"topup_pay":
			if phase == "select":
				progress = 0.0
				if not server_url.is_empty() and transport != null:
					phase = "paying"
					pay_state = "creating"
					pay_msg = ""
					invoice = {}
					_send_create()
				else:
					phase = "processing"
		"topup_paid":
			if phase == "paying" and pay_state == "awaiting" and not http_busy:
				http_purpose = "poll"
				_send_poll()
		"topup_cancel_pay":
			if phase == "paying" and pay_state in ["error", "awaiting"]:
				pay_state = "idle"
				invoice = {}
				qr_bytes = PackedByteArray()
				phase = "select"
		"topup_retry":
			if phase == "paying" and pay_state == "error":
				pay_state = "creating"
				pay_msg = ""
				invoice = {}
				_send_create()
		"topup_redeem":
			if phase == "select":
				phase = "redeem"
				redeem_input = ""
				redeem_msg = ""
		"vback":
			phase = "select"
			redeem_input = ""
			redeem_msg = ""
		"vpk_del":
			if phase == "redeem":
				redeem_backspace()
		"vpk_redeem":
			if phase == "redeem":
				redeem_submit()
		_:
			if btn_id.begins_with("topup_pkg_"):
				if phase == "select":
					var index := btn_id.get_slice("_", 2)
					if index.is_valid_int():
						pkg_idx = clampi(int(index), 0, PACKAGES.size() - 1)
			elif btn_id.begins_with("topup_method_"):
				if phase == "select":
					var index := btn_id.get_slice("_", 2)
					if index.is_valid_int():
						method_idx = clampi(int(index), 0, PAYMENT_METHODS.size() - 1)
			elif btn_id.begins_with("vpk_"):
				if phase == "redeem":
					redeem_append(btn_id.substr(4))
	changed.emit()


## Keyboard shortcuts of the redeem phase (`_redeem_handle_key`).
func key(keycode: Key) -> bool:
	if phase != "redeem":
		return false
	if keycode >= KEY_0 and keycode <= KEY_9:
		redeem_append(str(keycode - KEY_0))
	elif keycode >= KEY_KP_0 and keycode <= KEY_KP_9:
		redeem_append(str(keycode - KEY_KP_0))
	elif keycode == KEY_BACKSPACE or keycode == KEY_DELETE:
		redeem_backspace()
	elif keycode == KEY_ENTER or keycode == KEY_KP_ENTER:
		redeem_submit()
	else:
		return false
	changed.emit()
	return true


## One menu frame (the source assumes 60 fps): advances the simulation bar
## and drives the server state machine.
func tick() -> void:
	frame += 1
	if not is_open:
		return
	if phase == "processing":
		progress += 1.0 / maxf(1.0, float(int(60 * PROCESSING_SECONDS)))
		if progress >= 1.0:
			complete_simulation()
		changed.emit()
	elif phase == "paying":
		_server_tick()


## Transport callback: `body` is the raw response (JSON or PNG bytes).
func on_http_result(ok: bool, status: int, body: PackedByteArray) -> void:
	_http_result = [ok, status, body]
	_http_done = true


# ── simulation purchase (`topup_complete`) ─────────────────────────────────
func complete_simulation() -> void:
	var pkg := package()
	var method := payment_method()
	var total := int(pkg.gold) + int(pkg.get("bonus", 0))
	profile["meta_gold"] = meta_gold() + total
	var now_ms := _now_ms()
	var cur := currency if not currency.is_empty() else "IDR"
	var converted := TopupCurrency.convert_idr(float(pkg.price), cur)
	_append_history(
		{
			"tx": _tx_id(now_ms),
			"pkg": String(pkg.label),
			"gold": int(pkg.gold),
			"bonus": int(pkg.get("bonus", 0)),
			"price": int(pkg.price),
			"cur": cur,
			"price_cur": roundf(float(converted.value) * 100.0) / 100.0,
			"method": String(method.id),
			"ts": int(now_ms / 1000),
		}
	)
	_persist()
	phase = "success"
	tx_id = _tx_id(now_ms)
	last_total = total
	last_method = String(method.id)
	sound_requested.emit("ui_buy")
	changed.emit()


# ── redeem keypad (`_redeem_append/_backspace/_submit/_grant`) ─────────────
func redeem_append(character: String) -> void:
	if phase != "redeem":
		return
	var digits := redeem_input.replace(TopupVoucher.CODE_PREFIX, "")
	if digits.length() >= TopupVoucher.MAX_DIGITS:
		return
	if not redeem_input.begins_with(TopupVoucher.CODE_PREFIX):
		redeem_input = TopupVoucher.CODE_PREFIX
	redeem_input += character
	redeem_msg = ""
	sound_requested.emit("ui_click")


func redeem_backspace() -> void:
	if phase != "redeem" or redeem_input.is_empty():
		return
	var prefix := TopupVoucher.CODE_PREFIX
	if redeem_input.begins_with(prefix) and redeem_input.length() == prefix.length():
		redeem_input = ""
	else:
		redeem_input = redeem_input.substr(0, redeem_input.length() - 1)
	redeem_msg = ""


func redeem_submit() -> void:
	var code := redeem_input.strip_edges().to_upper()
	if not TopupVoucher.is_valid_format(code):
		_redeem_fail(MSG_INVALID)
		return
	var used: Array = _list("redeemed_codes")
	if code in used:
		_redeem_fail(MSG_ALREADY)
		return
	var allow: Variant = null
	if allowlist_callable.is_valid():
		allow = allowlist_callable.call()
	else:
		allow = TopupVoucher.load_vouchers()
	if allow != null and not (allow as Dictionary).has(code):
		_redeem_fail(MSG_UNKNOWN)
		return
	var amount: Variant = null
	if allow != null:
		amount = (allow as Dictionary).get(code)
	if amount == null or int(amount) == 0:
		var pkg: Dictionary = PACKAGES[0]
		amount = int(pkg.gold) + int(pkg.get("bonus", 0))
	grant(code, int(amount))


## Shared by the manual redeem and the settled server invoice. Returns false
## when the code was already granted (the caller then drops back to select).
func grant(code: String, amount: int) -> bool:
	var used: Array = _list("redeemed_codes")
	if code in used:
		return false
	profile["meta_gold"] = meta_gold() + amount
	var now_ms := _now_ms()
	var new_tx := _tx_id(now_ms)
	used.append(code)
	if used.size() > REDEEMED_CAP:
		used = used.slice(used.size() - REDEEMED_CAP)
	profile["redeemed_codes"] = used
	_append_history(
		{
			"tx": new_tx,
			"pkg": "REDEEM",
			"gold": amount,
			"bonus": 0,
			"price": 0,
			"cur": "IDR",
			"price_cur": 0,
			"method": "redeem",
			"code": code,
			"ts": int(now_ms / 1000),
		}
	)
	_persist()
	last_method = "redeem"
	redeem_code = code
	phase = "success"
	tx_id = new_tx
	last_total = amount
	sound_requested.emit("ui_buy")
	changed.emit()
	return true


func history() -> Array:
	return _list("topup_history")


# ── server flow (`_topup_server_tick`) ─────────────────────────────────────
func _send_create() -> void:
	http_purpose = "create"
	_send("POST", CREATE_PATH, {"pkg": String(package().label)})


func _send_poll() -> void:
	if not invoice.is_empty():
		_send("GET", STATUS_PATH + String(invoice.id), null)


func _send(method: String, path: String, payload: Variant) -> void:
	_http_done = false
	_http_result = []
	http_busy = true
	if transport != null:
		transport.call("send", method, path, payload)
	else:
		on_http_result(false, 0, "no transport".to_utf8_buffer())


func _server_tick() -> void:
	if http_busy:
		if not _http_done:
			return
		http_busy = false
		_http_done = false
		var ok := bool(_http_result[0]) if _http_result.size() == 3 else false
		var body: PackedByteArray = (
			_http_result[2] if _http_result.size() == 3 else PackedByteArray()
		)
		_http_result = []
		var purpose := http_purpose
		http_purpose = ""
		var data := _json(body)
		match purpose:
			"create":
				if ok and data.has("id") and not String(data.id).is_empty():
					invoice = data
					pay_state = "awaiting"
					pay_msg = ""
					http_purpose = "qr"
					_send("GET", QR_PATH + String(data.id), null)
					poll_next = frame + POLL_DELAY_FIRST
				else:
					_pay_fail(MSG_UNREACHABLE)
			"qr":
				if ok and body.size() >= 4 and body.slice(0, 4) == png_magic():
					qr_bytes = body
			"poll":
				var status := String(data.get("status", ""))
				var code := String(data.get("code", ""))
				if status == "settled" and not code.is_empty():
					pay_state = "idle"
					var gold: Variant = data.get("gold")
					var amount := (
						int(gold) if gold != null and int(gold) != 0 else int(PACKAGES[0].gold)
					)
					if not grant(code, amount):
						phase = "select"
						pay_msg = ""
				elif status in ["expired", "cancel"]:
					_pay_fail(MSG_NOT_SETTLED)
				else:
					poll_next = frame + POLL_DELAY_REPEAT
		changed.emit()
		return
	if pay_state == "awaiting" and frame >= poll_next:
		http_purpose = "poll"
		_send_poll()


func _pay_fail(message: String) -> void:
	pay_state = "error"
	pay_msg = message
	sound_requested.emit("ui_error")


func _redeem_fail(message: String) -> void:
	redeem_msg = message
	sound_requested.emit("ui_error")
	changed.emit()


# ── bookkeeping ────────────────────────────────────────────────────────────
func _list(key_name: String) -> Array:
	var value: Variant = profile.get(key_name)
	if value is Array:
		return value
	var fresh: Array = []
	profile[key_name] = fresh
	return fresh


func _append_history(entry: Dictionary) -> void:
	var entries: Array = _list("topup_history")
	entries.append(entry)
	if entries.size() > HISTORY_CAP:
		entries = entries.slice(entries.size() - HISTORY_CAP)
	profile["topup_history"] = entries


func _persist() -> void:
	if save_callable.is_valid():
		save_callable.call(profile)


func _now_ms() -> int:
	if clock_callable.is_valid():
		return int(clock_callable.call())
	return int(Time.get_unix_time_from_system() * 1000.0)


static func _tx_id(now_ms: int) -> String:
	return "MA-" + ("%010d" % (now_ms % 10_000_000_000))


static func _json(body: PackedByteArray) -> Dictionary:
	if body.is_empty():
		return {}
	var parser := JSON.new()
	if parser.parse(body.get_string_from_utf8()) != OK:
		return {}
	var parsed: Variant = parser.data
	return parsed if parsed is Dictionary else {}
