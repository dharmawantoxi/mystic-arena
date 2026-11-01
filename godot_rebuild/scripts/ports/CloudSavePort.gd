class_name CloudSavePort
extends Node

## Explicit Google Play Games Saved Games contract. No plugin is bundled.
## A real adapter must provide poll(), sign_in(), upload(payload), download().
## Default state is unavailable; local saves never depend on cloud success.
signal status_changed(status: Dictionary)
signal operation_finished(result: Dictionary)

var status := {
	"available": false,
	"signed_in": false,
	"busy": false,
	"message": "Play Games plugin not configured"
}
var adapter: Node


func configure(node: Node) -> void:
	adapter = node
	if adapter == null:
		status = {
			"available": false,
			"signed_in": false,
			"busy": false,
			"message": "Play Games plugin not configured"
		}
	elif (
		not adapter.has_method("poll")
		or not adapter.has_method("upload")
		or not adapter.has_method("download")
	):
		adapter = null
		status = {
			"available": false,
			"signed_in": false,
			"busy": false,
			"message": "Cloud adapter contract incomplete"
		}
	else:
		status.available = true
		status.message = "Cloud adapter configured; sign-in unverified"
	status_changed.emit(status)


func poll() -> void:
	if adapter != null and adapter.has_method("poll"):
		adapter.call("poll")


func sign_in() -> Dictionary:
	if adapter == null or not adapter.has_method("sign_in"):
		return _unavailable("sign_in")
	return adapter.call("sign_in")


func upload(payload: Dictionary) -> Dictionary:
	if payload.is_empty():
		return {
			"ok": false, "kind": "upload", "code": "empty", "message": "No local slots to upload"
		}
	if adapter == null:
		return _unavailable("upload")
	return adapter.call("upload", payload)


func download() -> Dictionary:
	if adapter == null:
		return _unavailable("download")
	return adapter.call("download")


func _unavailable(kind: String) -> Dictionary:
	var result := {"ok": false, "kind": kind, "code": "unavailable", "message": status.message}
	operation_finished.emit(result)
	return result
