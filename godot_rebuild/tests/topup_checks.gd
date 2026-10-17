extends RefCounted
## Layer 9au: replays the top-up / voucher source oracle fixture through the
## native port. `topup_source_oracle.py` executes the REAL `topup_currency.py`
## and `topup_voucher.py`, the harvested `Menu.topup_*` / `_redeem_*` /
## `_topup_server_tick` methods of `_core.py` (frozen clock, scripted urllib)
## and `server/app.py` in MOCK mode, so every string, amount, phase and
## request below comes from the source.

const TopupCurrency = preload("res://scripts/match/topup_currency.gd")
const TopupVoucher = preload("res://scripts/match/topup_voucher.gd")
const TopupFlow = preload("res://scripts/match/topup_flow.gd")
const FIXTURE := "res://tests/fixtures/topup_source.json"
const BASE_URL := "http://127.0.0.1:8321/"


## Scripted transport: every `send` records the request and answers at once
## with the next `[ok, status, body]` entry (like the oracle's fake urllib).
class FakeTransport:
	extends RefCounted
	var flow: TopupFlow
	var responses: Array = []
	var requests: Array = []

	func send(method: String, path: String, payload: Variant) -> void:
		requests.append({"method": method, "path": path, "payload": payload})
		if responses.is_empty():
			flow.on_http_result(false, 0, "no script".to_utf8_buffer())
			return
		var entry: Array = responses.pop_front()
		var body: Variant = entry[2]
		var bytes: PackedByteArray = (
			body if body is PackedByteArray else String(body).to_utf8_buffer()
		)
		flow.on_http_result(bool(entry[0]), int(entry[1]), bytes)


var _frozen_ms := 0


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Top-up fixture parses")
	if not (data is Dictionary):
		return
	_frozen_ms = int(data["menu"]["frozen_ms"])
	_currency_checks(data["currency"], check)
	_voucher_checks(data["voucher"], check)
	_menu_checks(data["menu"], check)
	_server_checks(data["menu"]["server"], check)
	_contract_checks(data["server"], check)


# ── topup_currency.py ──────────────────────────────────────────────────────
func _currency_checks(data: Dictionary, check: Callable) -> void:
	var rates: Dictionary = data["idr_per_unit"]
	check.call(rates.keys() == TopupCurrency.IDR_PER_UNIT.keys(), "currency table keys match")
	for code in rates:
		check.call(
			is_equal_approx(
				float(String(rates[code])), float(TopupCurrency.IDR_PER_UNIT.get(code, 0))
			),
			"IDR_PER_UNIT[%s] matches" % code
		)
	check.call(data["symbols"] == TopupCurrency.CURRENCY_SYMBOLS, "currency symbols match")
	check.call(Array(data["no_decimal"]) == Array(TopupCurrency.NO_DECIMAL), "NO_DECIMAL matches")
	check.call(data["region_currency"] == TopupCurrency.REGION_CURRENCY, "REGION_CURRENCY matches")
	check.call(data["lang_currency"] == TopupCurrency.LANG_CURRENCY, "LANG_CURRENCY matches")
	check.call(
		String(data["default_currency"]) == TopupCurrency.DEFAULT_CURRENCY,
		"DEFAULT_CURRENCY matches"
	)
	var amounts: Array = data["amounts"]
	var prices: Dictionary = data["prices"]
	for code in prices:
		var expected: Array = prices[code]
		for index in range(amounts.size()):
			var actual := TopupCurrency.format_price(float(amounts[index]), String(code))
			check.call(
				actual == String(expected[index]),
				(
					"format_price(%s, %s) = %s (got %s)"
					% [amounts[index], code, expected[index], actual]
				)
			)
	var converts: Dictionary = data["convert_10000"]
	for code in converts:
		var converted := TopupCurrency.convert_idr(10000.0, String(code))
		check.call(
			(
				String(converted.currency) == String(converts[code]["currency"])
				and is_equal_approx(float(converted.value), float(String(converts[code]["value"])))
			),
			"convert_idr(10000, %s) matches" % code
		)
	var parsed: Dictionary = data["parse_locale"]
	for name in parsed:
		var expected: Array = parsed[name]
		check.call(
			TopupCurrency.parse_locale_name(String(name)) == expected,
			"parse_locale_name(%s) = %s" % [name, str(expected)]
		)
	for entry in data["detect"]:
		var actual := TopupCurrency.currency_for(entry["lang"], entry["region"])
		check.call(
			actual == String(entry["currency"]),
			"currency_for(%s, %s) = %s" % [entry["lang"], entry["region"], entry["currency"]]
		)
	var detected := TopupCurrency.detect_currency()
	check.call(TopupCurrency.IDR_PER_UNIT.has(detected), "detect_currency returns a supported code")


# ── topup_voucher.py ───────────────────────────────────────────────────────
func _voucher_checks(data: Dictionary, check: Callable) -> void:
	check.call(String(data["code_prefix"]) == TopupVoucher.CODE_PREFIX, "CODE_PREFIX matches")
	check.call(int(data["max_digits"]) == TopupVoucher.MAX_DIGITS, "MAX_DIGITS matches")
	check.call(String(data["code_re"]) == TopupVoucher.CODE_PATTERN, "CODE_RE matches")
	check.call(String(data["voucher_file"]) == TopupVoucher.VOUCHER_FILE, "VOUCHER_FILE matches")
	for entry in data["formats"]:
		check.call(
			TopupVoucher.is_valid_format(entry["code"]) == bool(entry["valid"]),
			"is_valid_format(%s) = %s" % [str(entry["code"]), entry["valid"]]
		)
	var parsed: Variant = TopupVoucher.parse_allowlist(String(data["allowlist_text"]))
	check.call(parsed is Dictionary, "allowlist text parses to a dictionary")
	if parsed is Dictionary:
		var expected: Dictionary = data["parsed_allowlist"]
		check.call(parsed.keys() == expected.keys(), "allowlist codes match the source parse")
		for code in expected:
			var want: Variant = expected[code]
			var got: Variant = parsed.get(code)
			check.call(
				(
					(want == null and got == null)
					or (want != null and got != null and int(want) == int(got))
				),
				"allowlist amount for %s matches" % code
			)
	check.call(
		TopupVoucher.parse_allowlist("# only comments\n\n") == null, "comment-only allowlist = demo"
	)
	check.call(
		data["empty_allowlist"] == null and data["missing_allowlist"] == null, "source demo = None"
	)
	var absent: Array[String] = ["user://topup_checks_missing_voucher_codes.txt"]
	check.call(TopupVoucher.load_vouchers(absent) == null, "missing allowlist file = demo mode")
	var path := "user://topup_checks_voucher_codes.txt"
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(String(data["allowlist_text"]))
		file.close()
		var present: Array[String] = [path]
		var loaded: Variant = TopupVoucher.load_vouchers(present)
		check.call(
			loaded is Dictionary and loaded.keys() == Dictionary(data["parsed_allowlist"]).keys(),
			"load_vouchers reads the allowlist file"
		)
		DirAccess.remove_absolute(path)


# ── _core.py Menu flow ─────────────────────────────────────────────────────
func _new_flow(currency: String = "IDR", gold: int = 1000, profile: Dictionary = {}) -> TopupFlow:
	var flow := TopupFlow.new()
	flow.profile = profile.duplicate(true)
	flow.profile["meta_gold"] = gold
	flow.currency = currency
	flow.is_open = true
	flow.clock_callable = func() -> int: return _frozen_ms
	flow.allowlist_callable = func() -> Variant: return null
	return flow


func _record_sounds(flow: TopupFlow) -> Array:
	var sounds: Array = []
	flow.sound_requested.connect(func(key_name: String) -> void: sounds.append(key_name))
	return sounds


func _snapshot_matches(
	flow: TopupFlow, snap: Dictionary, sounds: Array, label: String, check: Callable
) -> void:
	check.call(flow.phase == String(snap["phase"]), "%s: phase %s" % [label, snap["phase"]])
	check.call(
		flow.pay_state == String(snap["pay_state"]), "%s: pay_state %s" % [label, snap["pay_state"]]
	)
	var pay_msg := String(snap["pay_msg"]) if snap["pay_msg"] != null else ""
	check.call(flow.pay_msg == pay_msg, "%s: pay_msg" % label)
	check.call(
		flow.meta_gold() == int(snap["meta_gold"]),
		"%s: meta_gold %d" % [label, int(snap["meta_gold"])]
	)
	var tx := String(snap["tx_id"]) if snap["tx_id"] != null else ""
	check.call(flow.tx_id == tx, "%s: tx_id %s" % [label, tx])
	check.call(flow.last_total == int(snap["last_total"]), "%s: last_total" % label)
	check.call(flow.redeem_input == String(snap["redeem_input"]), "%s: redeem_input" % label)
	var msg := ""
	if snap["redeem_msg"] != null:
		msg = String(snap["redeem_msg"][0])
		var color: Array = snap["redeem_msg"][1]
		check.call(
			TopupFlow.MSG_COLOR == Color8(int(color[0]), int(color[1]), int(color[2])),
			"%s: redeem message colour" % label
		)
	check.call(flow.redeem_msg == msg, "%s: redeem_msg '%s'" % [label, msg])
	var code := String(snap["redeem_code"]) if snap["redeem_code"] != null else ""
	check.call(flow.redeem_code == code, "%s: redeem_code" % label)
	var method := String(snap["last_method"]) if snap["last_method"] != null else ""
	if method == "redeem" or flow.last_method == "redeem":
		check.call(flow.last_method == method, "%s: last_method" % label)
	check.call(int(snap["qr_len"]) == flow.qr_bytes.size(), "%s: qr bytes" % label)
	var save_data: Dictionary = snap["save_data"]
	for key_name in save_data:
		check.call(
			_json_equal(flow.profile.get(key_name), save_data[key_name]),
			(
				"%s: save_data[%s] matches (%s vs %s)"
				% [label, key_name, str(flow.profile.get(key_name)), str(save_data[key_name])]
			)
		)
	var expected_sounds: Array = []
	for entry in snap["sounds"]:
		expected_sounds.append(String(entry[0]))
	check.call(
		sounds == expected_sounds,
		"%s: sounds %s (got %s)" % [label, str(expected_sounds), str(sounds)]
	)


func _json_equal(actual: Variant, expected: Variant) -> bool:
	if expected is Dictionary:
		return _dict_equal(actual, expected)
	if expected is Array:
		return _array_equal(actual, expected)
	if expected is float or expected is int:
		return (
			(actual is float or actual is int) and is_equal_approx(float(actual), float(expected))
		)
	if expected == null:
		return actual == null
	return str(actual) == str(expected)


func _dict_equal(actual: Variant, expected: Dictionary) -> bool:
	if not (actual is Dictionary) or actual.size() != expected.size():
		return false
	for key_name in expected:
		if not actual.has(key_name) or not _json_equal(actual[key_name], expected[key_name]):
			return false
	return true


func _array_equal(actual: Variant, expected: Array) -> bool:
	if not (actual is Array) or actual.size() != expected.size():
		return false
	for index in range(expected.size()):
		if not _json_equal(actual[index], expected[index]):
			return false
	return true


func _menu_checks(data: Dictionary, check: Callable) -> void:
	check.call(_json_equal(TopupFlow.PACKAGES, data["packages"]), "TOPUP_PACKAGES match")
	check.call(
		_json_equal(TopupFlow.PAYMENT_METHODS, data["payment_methods"]),
		"TOPUP_PAYMENT_METHODS match"
	)
	check.call(
		is_equal_approx(TopupFlow.PROCESSING_SECONDS, float(data["processing_seconds"])),
		"TOPUP_PROCESSING_SECONDS matches"
	)
	var fmt: Dictionary = data["fmt_idr"]
	for amount in fmt:
		check.call(
			TopupCurrency.fmt_idr(float(String(amount))) == String(fmt[amount]),
			"fmt_idr(%s)" % amount
		)
	# simulation progress bar: 96 ticks of 1/96 reach 1.0 exactly like the source
	var flow := _new_flow()
	flow.click("topup_pay")
	check.call(flow.phase == "processing", "PAY NOW without a server enters processing")
	var ticks := 0
	while flow.phase == "processing" and ticks < 200:
		flow.tick()
		ticks += 1
	check.call(
		ticks == int(data["simulation_frames"]),
		"simulation takes %d frames (got %d)" % [int(data["simulation_frames"]), ticks]
	)
	check.call(flow.phase == "success", "simulation ends in success")
	for entry in data["simulation"]:
		flow = _new_flow(String(entry["currency"]), int(entry["gold_before"]))
		flow.method_idx = int(entry["method_idx"])
		flow.phase = "processing"
		var sounds := _record_sounds(flow)
		flow.complete_simulation()
		_snapshot_matches(flow, entry["after"], sounds, "simulation %s" % entry["currency"], check)
	flow = _new_flow()
	for _step in range(52):
		flow.complete_simulation()
	check.call(
		(
			flow.history().size() == int(data["history_cap"]["len"])
			and flow.meta_gold() == int(data["history_cap"]["meta_gold"])
		),
		"topup_history keeps the last 50 purchases"
	)
	# keypad
	flow = _new_flow()
	flow.phase = "redeem"
	var sounds := _record_sounds(flow)
	for entry in data["keypad"]:
		if String(entry["op"]) == "del":
			flow.redeem_backspace()
		else:
			flow.redeem_append(String(entry["op"]))
		check.call(
			flow.redeem_input == String(entry["input"]),
			"keypad '%s' -> '%s' (got '%s')" % [entry["op"], entry["input"], flow.redeem_input]
		)
	check.call(
		sounds.size() == Array(data["keypad_sounds"]).size(),
		"keypad clicks play ui_click per accepted digit"
	)
	flow = _new_flow()
	flow.phase = "select"
	flow.redeem_append("5")
	flow.redeem_backspace()
	check.call(
		flow.redeem_input == String(data["keypad_wrong_phase"]), "keypad ignored outside redeem"
	)
	# button-id keypad path + keyboard path
	flow = _new_flow()
	flow.click("topup_redeem")
	flow.click("vpk_1")
	flow.click("vpk_2")
	flow.key(KEY_3)
	flow.key(KEY_KP_4)
	flow.key(KEY_BACKSPACE)
	check.call(
		flow.phase == "redeem" and flow.redeem_input == "MA-123", "vpk_/key input builds the code"
	)
	flow.click("vback")
	check.call(flow.phase == "select" and flow.redeem_input.is_empty(), "vback returns to select")
	# submit outcomes
	for entry in data["submits"]:
		var profile: Dictionary = {}
		var before: Dictionary = entry["after"]["save_data"]
		if String(entry["label"]) == "already_redeemed":
			profile["redeemed_codes"] = before["redeemed_codes"]
		elif String(entry["label"]) == "demo_mode":
			profile["topup_history"] = [{"tx": "x"}]
		flow = _new_flow("IDR", 500, profile)
		var text: Variant = entry["allowlist"]
		flow.allowlist_callable = func() -> Variant:
			return null if text == null else TopupVoucher.parse_allowlist(String(text))
		flow.phase = "redeem"
		flow.redeem_input = String(entry["input"])
		var submit_sounds := _record_sounds(flow)
		flow.redeem_submit()
		_snapshot_matches(flow, entry["after"], submit_sounds, "submit %s" % entry["label"], check)
	# redeemed_codes cap + duplicate grant
	flow = _new_flow()
	for index in range(53):
		flow.phase = "redeem"
		flow.grant("MA-%06d" % index, 10)
	check.call(
		(
			_json_equal(flow.profile["redeemed_codes"], data["redeem_cap"]["codes"])
			and flow.history().size() == int(data["redeem_cap"]["history_len"])
			and flow.meta_gold() == int(data["redeem_cap"]["meta_gold"])
		),
		"redeemed_codes keep the last 50 codes"
	)
	check.call(
		flow.grant("MA-000052", 10) == bool(data["grant_duplicate"]), "duplicate grant is refused"
	)
	# dialog open / cancel semantics
	flow = _new_flow()
	flow.is_open = false
	flow.click("topup_open")
	check.call(flow.is_open and flow.phase == "select", "topup_open resets to select")
	flow.click("topup_method_3")
	flow.click("topup_pkg_0")
	check.call(flow.method_idx == 3 and flow.pkg_idx == 0, "package / method buttons select")
	flow.click("topup_pay")
	flow.click("topup_cancel")
	check.call(flow.is_open and flow.phase == "processing", "cancel is ignored while processing")
	flow.phase = "select"
	flow.click("topup_cancel")
	check.call(not flow.is_open, "cancel closes the dialog from select")


# ── server state machine ───────────────────────────────────────────────────
func _server_flow(responses: Array, gold: int = 10) -> Array:
	var flow := _new_flow("IDR", gold)
	var transport := FakeTransport.new()
	transport.flow = flow
	transport.responses = responses
	flow.transport = transport
	flow.server_url = BASE_URL
	flow.frame = 100
	flow.phase = "select"
	var sounds := _record_sounds(flow)
	flow.click("topup_pay")
	return [flow, transport, sounds]


func _drain(flow: TopupFlow) -> void:
	var guard := 0
	while flow.http_busy and guard < 50:
		flow._server_tick()
		guard += 1


func _poll_due(flow: TopupFlow) -> void:
	flow.frame = flow.poll_next
	flow._server_tick()
	_drain(flow)


func _responses(entries: Array) -> Array:
	var out: Array = []
	for entry in entries:
		var body: Variant = entry[2]
		if body is Dictionary:
			body = JSON.stringify(body)
		out.append([entry[0], entry[1], body])
	return out


func _server_checks(data: Dictionary, check: Callable) -> void:
	check.call(
		int(data["poll_delay_first"]) == TopupFlow.POLL_DELAY_FIRST, "first poll after 60 frames"
	)
	check.call(
		int(data["poll_delay_repeat"]) == TopupFlow.POLL_DELAY_REPEAT,
		"repeat poll after 120 frames"
	)
	check.call(
		is_equal_approx(float(data["http_timeout"]), TopupFlow.HTTP_TIMEOUT), "HTTP timeout 6 s"
	)
	var png := TopupFlow.png_magic()
	png.append_array("\r\n\u001a\nfakepngbody".to_utf8_buffer())
	var create := {
		"id": "mock-abc",
		"pkg": "PAKET 50K",
		"amount": 10000,
		"gold": 50000,
		"status": "pending",
		"qr_url": "/api/topup/qr/mock-abc",
		"mock": true,
	}
	var pending := {"id": "mock-abc", "status": "pending", "gold": 50000, "amount": 10000}
	var settled := {
		"id": "mock-abc", "status": "settled", "gold": 50000, "amount": 10000, "code": "MA-424242"
	}
	# happy path
	var happy: Dictionary = data["happy"]
	var parts := _server_flow(
		_responses(
			[[true, 200, create], [true, 200, png], [true, 200, pending], [true, 200, settled]]
		)
	)
	var flow: TopupFlow = parts[0]
	var transport: FakeTransport = parts[1]
	var sounds: Array = parts[2]
	var steps: Array = happy["steps"]
	check.call(
		flow.phase == "paying" and flow.pay_state == "creating",
		"PAY NOW with a server enters paying/creating"
	)
	_drain(flow)
	_snapshot_matches(flow, steps[0][1], sounds, "server after_create", check)
	check.call(
		flow.poll_next == int(steps[0][1]["poll_next"]),
		"first poll scheduled at frame %d" % int(steps[0][1]["poll_next"])
	)
	_snapshot_matches(flow, steps[1][1], sounds, "server after_qr", check)
	flow.frame = 159
	flow._server_tick()
	check.call(transport.requests.size() == int(steps[2][2]), "no poll before poll_next")
	flow.frame = 160
	flow._server_tick()
	_drain(flow)
	_snapshot_matches(flow, steps[3][1], sounds, "server after_pending_poll", check)
	check.call(flow.poll_next == int(steps[3][1]["poll_next"]), "pending poll reschedules +120")
	_poll_due(flow)
	_snapshot_matches(flow, steps[4][1], sounds, "server after_settled_poll", check)
	var expected_requests: Array = happy["requests"]
	check.call(transport.requests.size() == expected_requests.size(), "happy path sends 4 requests")
	for index in range(mini(transport.requests.size(), expected_requests.size())):
		var want: Dictionary = expected_requests[index]
		var got: Dictionary = transport.requests[index]
		var want_payload: Variant = null
		if want["body"] != null:
			want_payload = JSON.parse_string(String(want["body"]))
		check.call(
			(
				String(got["method"]) == String(want["method"])
				and BASE_URL.rstrip("/") + String(got["path"]) == String(want["url"])
				and _json_equal(got["payload"], want_payload)
			),
			"request %d matches %s %s" % [index, want["method"], want["url"]]
		)
	# manual "I'VE PAID" polls immediately when idle
	parts = _server_flow(_responses([[true, 200, create], [true, 200, png], [true, 200, settled]]))
	flow = parts[0]
	transport = parts[1]
	_drain(flow)
	flow.click("topup_paid")
	_drain(flow)
	check.call(
		flow.phase == "success" and transport.requests.size() == 3, "I'VE PAID polls at once"
	)
	# failures
	parts = _server_flow([[false, 0, "connection refused"]])
	flow = parts[0]
	_drain(flow)
	_snapshot_matches(
		flow, data["create_unreachable"]["after"], parts[2], "server create_unreachable", check
	)
	check.call(
		parts[1].requests.size() == Array(data["create_unreachable"]["requests"]).size(),
		"unreachable: one request"
	)
	flow.click("topup_retry")
	check.call(
		flow.pay_state == "creating" and parts[1].requests.size() == 2, "TRY AGAIN re-sends create"
	)
	parts = _server_flow(_responses([[true, 400, {"error": "unknown_package"}]]))
	flow = parts[0]
	_drain(flow)
	_snapshot_matches(flow, data["create_rejected"], parts[2], "server create_rejected", check)
	flow.click("topup_cancel_pay")
	check.call(
		flow.phase == "select" and flow.pay_state == "idle", "BACK from error returns to select"
	)
	parts = _server_flow(
		_responses(
			[
				[true, 200, create],
				[true, 404, "not found"],
				[true, 200, {"id": "mock-abc", "status": "expired", "gold": 50000, "amount": 10000}]
			]
		)
	)
	flow = parts[0]
	_drain(flow)
	_poll_due(flow)
	_snapshot_matches(flow, data["expired"], parts[2], "server expired", check)
	parts = _server_flow(
		_responses(
			[
				[true, 200, create],
				[true, 200, png],
				[true, 200, {"id": "mock-abc", "status": "cancel"}]
			]
		)
	)
	flow = parts[0]
	_drain(flow)
	_poll_due(flow)
	_snapshot_matches(flow, data["cancel"], parts[2], "server cancel", check)
	parts = _server_flow(
		_responses([[true, 200, create], [true, 200, png], [false, 0, "timed out"]])
	)
	flow = parts[0]
	_drain(flow)
	_poll_due(flow)
	_snapshot_matches(flow, data["poll_error"], parts[2], "server poll_error", check)
	check.call(
		flow.poll_next == int(data["poll_error"]["poll_next"]), "poll error reschedules +120"
	)
	parts = _server_flow(
		_responses(
			[
				[true, 200, create],
				[true, 200, png],
				[true, 200, {"id": "mock-abc", "status": "settled", "code": "MA-111111"}]
			]
		)
	)
	flow = parts[0]
	_drain(flow)
	_poll_due(flow)
	_snapshot_matches(
		flow, data["settled_default_gold"], parts[2], "server settled_default_gold", check
	)
	parts = _server_flow(
		_responses(
			[
				[true, 200, create],
				[true, 200, png],
				[
					true,
					200,
					{"id": "mock-abc", "status": "settled", "gold": 50000, "code": "MA-111111"}
				]
			]
		)
	)
	flow = parts[0]
	flow.profile["redeemed_codes"] = ["MA-111111"]
	_drain(flow)
	_poll_due(flow)
	_snapshot_matches(
		flow, data["settled_duplicate_code"], parts[2], "server settled_duplicate_code", check
	)


# ── server/app.py contract ─────────────────────────────────────────────────
func _contract_checks(data: Dictionary, check: Callable) -> void:
	var routes: Array = data["routes"]
	check.call("POST " + TopupFlow.CREATE_PATH in routes, "server exposes the create route")
	check.call(
		"GET " + TopupFlow.STATUS_PATH + "<invoice_id>" in routes, "server exposes the status route"
	)
	check.call("GET " + TopupFlow.QR_PATH + "<invoice_id>" in routes, "server exposes the QR route")
	var packages: Dictionary = data["packages"]
	var pkg: Dictionary = TopupFlow.PACKAGES[0]
	check.call(
		(
			packages.has(String(pkg.label))
			and int(packages[String(pkg.label)][0]) == int(pkg.price)
			and int(packages[String(pkg.label)][1]) == int(pkg.gold)
		),
		"server package table matches the client package"
	)
	var created: Dictionary = data["create_ok"]["body"]
	for key_name in ["id", "pkg", "amount", "gold", "status", "qr_url"]:
		check.call(created.has(key_name), "create response carries %s" % key_name)
	check.call(
		String(created["qr_url"]) == TopupFlow.QR_PATH + "<id>", "create qr_url matches the QR path"
	)
	check.call(
		bool(data["create_id_ok"]) and bool(data["code_ok"]),
		"server ids and codes have the pinned shapes"
	)
	var settled: Dictionary = data["status_settled"]["body"]
	check.call(
		String(settled["status"]) == "settled" and settled.has("code") and settled.has("gold"),
		"settled status carries code + gold (auto-grant inputs)"
	)
	check.call(
		not Dictionary(data["status_pending"]["body"]).has("code"), "pending status carries no code"
	)
	check.call(
		bool(data["qr_ok"]["png"]) and String(data["qr_ok"]["mimetype"]) == "image/png",
		"QR route serves PNG"
	)
	check.call(int(data["create_unknown"]["status"]) == 400, "unknown package is rejected (400)")
	check.call(int(data["status_missing"]["status"]) == 404, "unknown invoice is 404")
	check.call(
		TopupVoucher.is_valid_format("MA-" + "123456"),
		"server codes (MA-6 digits) pass the client format"
	)
	check.call(
		(
			String(data["redeem_again"]["body"]["error"]) == "already_redeemed"
			and int(data["redeem_again"]["status"]) == 409
		),
		"server rejects a second redeem"
	)
