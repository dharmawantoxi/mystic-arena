class_name VoucherService
extends RefCounted

## Voucher allowlist + one-time redemption. Demo mode is explicit and debug-only.
const CODE_PATTERN := "^MA-[0-9]{4,8}$"
var allowlist: Dictionary = {}
var allowlist_loaded := false
var demo_mode := false
var default_gold := 50000


func load_allowlist(paths: Array[String]) -> bool:
	allowlist = {}
	allowlist_loaded = false
	for path: String in paths:
		if not FileAccess.file_exists(path):
			continue
		var file := FileAccess.open(path, FileAccess.READ)
		if file == null:
			continue
		while not file.eof_reached():
			var line := file.get_line().strip_edges()
			if line.is_empty() or line.begins_with("#"):
				continue
			if "=" in line:
				var parts := line.split("=", true, 1)
				var amount := int(parts[1])
				if amount > 0:
					allowlist[parts[0].strip_edges().to_upper()] = amount
			else:
				allowlist[line.to_upper()] = default_gold
		allowlist_loaded = true
		return true
	return false


func valid_format(code: String) -> bool:
	var regex := RegEx.new()
	regex.compile(CODE_PATTERN)
	return regex.search(code.strip_edges().to_upper()) != null


func redeem(repo: SaveRepository, code: String, now_ms: int) -> Dictionary:
	var normalized := code.strip_edges().to_upper()
	if not valid_format(normalized):
		return {"ok": false, "reason": "invalid_format", "gold": 0}
	var amount := 0
	if allowlist_loaded:
		if not allowlist.has(normalized):
			return {"ok": false, "reason": "unknown_code", "gold": 0}
		amount = int(allowlist[normalized])
	elif demo_mode and OS.is_debug_build():
		amount = default_gold
	else:
		return {"ok": false, "reason": "allowlist_missing", "gold": 0}
	var data := repo.load_slot()
	var result := SaveRepository.grant_voucher(data, normalized, amount, now_ms)
	if bool(result.ok) and not repo.save_slot(data, -1, now_ms / 1000.0):
		return {"ok": false, "reason": "save_failed", "gold": 0}
	return result
