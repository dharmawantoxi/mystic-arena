extends RefCounted
## Layer 9au: port of `topup_voucher.py`.
##
## Voucher codes are `MA-` + 4..8 digits (the keypad types 6). The optional
## allowlist `voucher_codes.txt` (project root first, then the save dir) holds
## one `CODE` or `CODE=gold` per line; `#` lines are comments. When the file is
## missing (or holds no codes) the game is in demo mode and every well-formed
## code is accepted - `load_vouchers()` then returns `null`, like the source.

const CODE_PREFIX := "MA-"
const MAX_DIGITS := 6
const CODE_PATTERN := "^MA-(\\d{4,8})$"
const VOUCHER_FILE := "voucher_codes.txt"
## Project root first, then the save dir (`user://`), like the source.
const DEFAULT_ROOTS: Array[String] = ["res://", "user://"]

static var _code_re: RegEx


static func is_valid_format(code: Variant) -> bool:
	if code == null:
		return false
	if _code_re == null:
		_code_re = RegEx.create_from_string(CODE_PATTERN)
	return _code_re.search(String(code).strip_edges().to_upper()) != null


## Parse allowlist text -> `{CODE: gold or null}`; `null` when it holds no codes.
static func parse_allowlist(text: String) -> Variant:
	var result := {}
	for raw_line in text.split("\n"):
		var line := raw_line.strip_edges()
		if line.is_empty() or line.begins_with("#"):
			continue
		if "=" in line:
			var split := line.split("=", true, 1)
			var amount := split[1].strip_edges()
			if not amount.is_valid_int():
				continue
			result[split[0].strip_edges().to_upper()] = int(amount)
		else:
			result[line.to_upper()] = null
	return null if result.is_empty() else result


## Read the first existing allowlist file; `null` = demo mode.
static func load_vouchers(paths: Array[String] = []) -> Variant:
	var candidates: Array[String] = paths
	if candidates.is_empty():
		for root in DEFAULT_ROOTS:
			candidates.append(root + VOUCHER_FILE)
	for path in candidates:
		if not FileAccess.file_exists(path):
			continue
		return parse_allowlist(FileAccess.get_file_as_string(path))
	return null
