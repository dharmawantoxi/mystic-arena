extends Node
## Layer 9au: HTTP transport for the top-up server (`server/app.py`), the
## counterpart of `Menu._topup_http`. One request at a time, 6 s timeout,
## JSON bodies for POST; the raw response bytes are handed back to the flow
## (`on_http_result`) so it can parse JSON or the QR PNG itself.
##
## The base URL comes from `MYSTIC_TOPUP_URL` (same env var as the source);
## an empty URL keeps the dialog in simulation mode.

const TopupFlow = preload("res://scripts/match/topup_flow.gd")

var base_url := ""
var flow: TopupFlow
var _request: HTTPRequest
var _busy := false


func _ready() -> void:
	_request = HTTPRequest.new()
	_request.name = "HTTPRequest"
	_request.timeout = TopupFlow.HTTP_TIMEOUT
	_request.request_completed.connect(_on_completed)
	add_child(_request)


## `url` null = read `MYSTIC_TOPUP_URL`; empty string = simulation only.
func configure(flow_value: TopupFlow, url: Variant = null) -> void:
	flow = flow_value
	var resolved := TopupFlow.default_server_url() if url == null else String(url)
	base_url = resolved.strip_edges()
	flow.server_url = base_url
	flow.transport = self if not base_url.is_empty() else null


func is_busy() -> bool:
	return _busy


## Transport entry point used by the flow.
func send(method: String, path: String, payload: Variant) -> void:
	if _busy or _request == null:
		_deliver(false, 0, "busy".to_utf8_buffer())
		return
	var url := base_url.rstrip("/") + path
	var headers := PackedStringArray()
	var body := ""
	if payload != null:
		headers.append("Content-Type: application/json")
		body = JSON.stringify(payload)
	var http_method := HTTPClient.METHOD_POST if method == "POST" else HTTPClient.METHOD_GET
	_busy = true
	var error := _request.request(url, headers, http_method, body)
	if error != OK:
		_busy = false
		_deliver(false, 0, ("request error %d" % error).to_utf8_buffer())


func _on_completed(
	result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray
) -> void:
	_busy = false
	var ok := result == HTTPRequest.RESULT_SUCCESS and response_code < 400
	_deliver(ok, response_code, body)


func _deliver(ok: bool, status: int, body: PackedByteArray) -> void:
	if flow != null:
		flow.on_http_result(ok, status, body)
