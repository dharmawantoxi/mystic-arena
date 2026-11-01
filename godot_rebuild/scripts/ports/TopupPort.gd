class_name TopupPort
extends Node

## Native top-up HTTP contract from _core.py. No simulated payment success.
## Server URL comes from MYSTIC_TOPUP_URL; empty means unavailable in production.
signal state_changed(state: Dictionary)
signal settled(transaction: Dictionary)

const PROCESSING_SECONDS := 1.6
var server_url := ""
var busy := false
var last_error := ""
var current_transaction: Dictionary = {}
var _http: HTTPRequest
var _pending_kind := ""
var _pending_id := ""


func _ready() -> void:
	server_url = OS.get_environment("MYSTIC_TOPUP_URL").strip_edges()
	_http = HTTPRequest.new()
	_http.timeout = 15.0
	add_child(_http)
	_http.request_completed.connect(_on_response)


func available() -> bool:
	return not server_url.is_empty()


func packages(rules: Dictionary) -> Array:
	return rules.get("TOPUP_PACKAGES", [])


func methods(rules: Dictionary) -> Array:
	return rules.get("TOPUP_PAYMENT_METHODS", [])


func create(package_index: int, method_id: String, rules: Dictionary) -> Dictionary:
	if busy:
		return {"ok": false, "code": "busy"}
	var packs := packages(rules)
	if package_index < 0 or package_index >= packs.size():
		return {"ok": false, "code": "invalid_package"}
	if not available():
		last_error = "Top-up server not configured"
		state_changed.emit({"state": "unavailable", "message": last_error})
		return {"ok": false, "code": "unavailable", "message": last_error}
	var pack: Dictionary = packs[package_index]
	busy = true
	_pending_kind = "create"
	var body := JSON.stringify({"package": pack, "method": method_id})
	var err := _http.request(
		server_url.path_join("api/topup/create"),
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		body
	)
	if err != OK:
		busy = false
		return {"ok": false, "code": "request_failed"}
	return {"ok": true, "code": "pending"}


func poll_status(transaction_id: String) -> Dictionary:
	if busy or not available() or transaction_id.is_empty():
		return {"ok": false, "code": "unavailable"}
	busy = true
	_pending_kind = "status"
	_pending_id = transaction_id
	var err := _http.request(server_url.path_join("api/topup/status").path_join(transaction_id))
	if err != OK:
		busy = false
		return {"ok": false, "code": "request_failed"}
	return {"ok": true, "code": "pending"}


func qr_url(transaction_id: String) -> String:
	if not available() or transaction_id.is_empty():
		return ""
	return server_url.path_join("api/topup/qr").path_join(transaction_id)


func _on_response(
	result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray
) -> void:
	busy = false
	if result != HTTPRequest.RESULT_SUCCESS or response_code < 200 or response_code >= 300:
		last_error = "Top-up server error (%d/%d)" % [result, response_code]
		state_changed.emit({"state": "error", "message": last_error})
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if not parsed is Dictionary:
		last_error = "Invalid top-up response"
		state_changed.emit({"state": "error", "message": last_error})
		return
	var response: Dictionary = parsed
	if _pending_kind == "create":
		current_transaction = response
		state_changed.emit({"state": "created", "transaction": response})
	elif _pending_kind == "status":
		current_transaction = response
		var status := str(response.get("status", ""))
		state_changed.emit({"state": status, "transaction": response})
		if status == "settled":
			settled.emit(response)
