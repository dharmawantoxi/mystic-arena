extends RefCounted
## Pure, source-shaped payload codec for the Google Play Games cloud snapshot.

const PAYLOAD_MAGIC := "MYSTIC_ARENA_BACKUP"
const PAYLOAD_VERSION := 1
const CLOUD_MAGIC := "MYSTIC_ARENA_CLOUD"
const CLOUD_VERSION := 1
const SOURCE_SLOT_COUNT := 3


static func canonical_json(value: Variant) -> String:
	match typeof(value):
		TYPE_NIL:
			return "null"
		TYPE_BOOL:
			return "true" if value else "false"
		TYPE_INT:
			return str(value)
		TYPE_FLOAT:
			return _python_float(float(value))
		TYPE_STRING:
			return JSON.stringify(String(value))
		TYPE_ARRAY, TYPE_PACKED_STRING_ARRAY, TYPE_PACKED_INT32_ARRAY, TYPE_PACKED_INT64_ARRAY:
			var parts: PackedStringArray = []
			for entry in value:
				parts.append(canonical_json(entry))
			return "[" + ",".join(parts) + "]"
		TYPE_DICTIONARY:
			var keys: Array = value.keys()
			keys.sort_custom(
				func(left: Variant, right: Variant) -> bool: return String(left) < String(right)
			)
			var parts: PackedStringArray = []
			for key in keys:
				parts.append(JSON.stringify(String(key)) + ":" + canonical_json(value[key]))
			return "{" + ",".join(parts) + "}"
		_:
			return "null"


static func _python_float(value: float) -> String:
	# Both Python repr() and Godot's Grisu2 formatter use shortest round-trip
	# binary64 decimals; normalize the exponent and fixed/scientific threshold.
	var shortest := String.num_scientific(value)
	var negative := shortest.begins_with("-")
	if negative:
		shortest = shortest.substr(1)
	if value == 0.0:
		return "-0.0" if negative else "0.0"
	var exponent := 0
	var mantissa := shortest
	var exponent_at := shortest.find("e")
	if exponent_at >= 0:
		mantissa = shortest.substr(0, exponent_at)
		exponent = int(shortest.substr(exponent_at + 1))
	var point := mantissa.find(".")
	var decimal_position := mantissa.length() if point < 0 else point
	var digits := mantissa.replace(".", "")
	while digits.length() > 1 and digits.begins_with("0"):
		digits = digits.substr(1)
		exponent -= 1
	while digits.length() > 1 and digits.ends_with("0"):
		digits = digits.substr(0, digits.length() - 1)
	exponent += decimal_position - 1
	var rendered := ""
	if exponent >= -4 and exponent < 16:
		var decimal_at := exponent + 1
		if decimal_at <= 0:
			rendered = "0." + "0".repeat(-decimal_at) + digits
		elif decimal_at >= digits.length():
			rendered = digits + "0".repeat(decimal_at - digits.length()) + ".0"
		else:
			rendered = digits.substr(0, decimal_at) + "." + digits.substr(decimal_at)
	else:
		rendered = digits.substr(0, 1)
		if digits.length() > 1:
			rendered += "." + digits.substr(1)
		var sign := "+" if exponent >= 0 else "-"
		var exponent_digits := str(absi(exponent)).pad_zeros(2)
		rendered += "e" + sign + exponent_digits
	return "-" + rendered if negative else rendered


static func compute_checksum(payload: Dictionary) -> String:
	var body := payload.duplicate(true)
	body.erase("checksum")
	var context := HashingContext.new()
	if context.start(HashingContext.HASH_SHA256) != OK:
		return ""
	context.update(canonical_json(body).to_utf8_buffer())
	return context.finish().hex_encode()


static func parse_payload(text: String) -> Dictionary:
	var parser := JSON.new()
	if parser.parse(text) != OK:
		return {"payload": null, "error": "File corrupt (not valid JSON)"}
	var parsed: Variant = parser.data
	if not parsed is Dictionary:
		return {"payload": null, "error": "File corrupt (unexpected structure)"}
	var payload: Dictionary = parsed
	if payload.get("magic") != PAYLOAD_MAGIC:
		return {"payload": null, "error": "Not a Mystic Arena save file"}
	var version_value: Variant = payload.get("version", 0)
	var version: Variant = _source_int(version_value)
	if version == null:
		return {"payload": null, "error": "File corrupt (bad version)"}
	if int(version) < 1 or int(version) > PAYLOAD_VERSION:
		return {"payload": null, "error": "Save version %s not supported" % int(version)}
	var slots: Variant = payload.get("slots")
	if not slots is Dictionary or (slots as Dictionary).is_empty():
		return {"payload": null, "error": "Save contains no data"}
	if payload.get("checksum") != compute_checksum(payload):
		return {"payload": null, "error": "File corrupt (checksum mismatch)"}
	return {"payload": payload, "error": ""}


static func _source_int(value: Variant) -> Variant:
	match typeof(value):
		TYPE_BOOL:
			return 1 if value else 0
		TYPE_INT:
			return value
		TYPE_FLOAT:
			if is_nan(float(value)) or is_inf(float(value)):
				return null
			return int(value)
		TYPE_STRING:
			var text := String(value).strip_edges()
			if text.is_valid_int():
				return int(text)
	return null


static func get_payload_summary(payload: Dictionary) -> Dictionary:
	var highest_level := 0
	var best_gold := 0
	var newest_played := 0.0
	var slots: Variant = payload.get("slots", {})
	if slots is Dictionary:
		for slot_value in (slots as Dictionary).values():
			if not slot_value is Dictionary:
				continue
			var data: Dictionary = slot_value
			var completed: Variant = data.get("completed_levels", [])
			if completed is Array:
				for level in completed:
					var parsed_level: Variant = _source_int(level)
					if parsed_level != null:
						highest_level = maxi(highest_level, int(parsed_level))
			var gold: Variant = _source_int(data.get("meta_gold", 0))
			if gold != null:
				best_gold = maxi(best_gold, int(gold))
			var last_played: Variant = data.get("slot_last_played", 0.0)
			if last_played is int or last_played is float:
				if not is_nan(float(last_played)) and not is_inf(float(last_played)):
					newest_played = maxf(newest_played, float(last_played))
	var exported_at: Variant = payload.get("exported_at", 0.0)
	var timestamp := float(exported_at) if exported_at is int or exported_at is float else 0.0
	return {
		"highest_level": highest_level,
		"meta_gold": best_gold,
		"slot_count": (slots as Dictionary).size() if slots is Dictionary else 0,
		"exported_at": timestamp,
		"exported_at_str": _format_exported_at(timestamp),
		"newest_played": newest_played,
	}


static func _format_exported_at(timestamp: float) -> String:
	var date := Time.get_datetime_dict_from_unix_time(int(timestamp))
	var months := [
		"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
	]
	var month_index := int(date.get("month", 1)) - 1
	if month_index < 0 or month_index >= months.size():
		return "?"
	return (
		"%02d %s %04d %02d:%02d"
		% [
			int(date.get("day", 1)),
			months[month_index],
			int(date.get("year", 1970)),
			int(date.get("hour", 0)),
			int(date.get("minute", 0)),
		]
	)


static func build_payload(
	slots: Dictionary, settings: Dictionary, exported_at: float
) -> Dictionary:
	var payload := {
		"magic": PAYLOAD_MAGIC,
		"version": PAYLOAD_VERSION,
		"exported_at": exported_at,
		"slots": slots.duplicate(true),
		"settings": settings.duplicate(true),
	}
	payload["checksum"] = compute_checksum(payload)
	return payload


static func validate_envelope(value: Variant) -> Dictionary:
	if not value is Dictionary:
		return {"payload": null, "error": "Bukan file cloud Mystic Arena"}
	var envelope: Dictionary = value
	if envelope.get("magic") != CLOUD_MAGIC:
		return {"payload": null, "error": "Bukan file cloud Mystic Arena"}
	var version: Variant = _source_int(envelope.get("version", 0))
	if version == null or int(version) < 1:
		return {"payload": null, "error": "Payload cloud rusak"}
	if int(version) > CLOUD_VERSION:
		return {"payload": null, "error": "Versi cloud lebih baru dari game"}
	var raw_payload: Variant = envelope.get("payload")
	if not raw_payload is Dictionary:
		return {"payload": null, "error": "Payload cloud rusak"}
	var parsed := parse_payload(JSON.stringify(raw_payload, "", true, true))
	if parsed.payload == null:
		return {
			"payload": null,
			"error": parsed.error if not String(parsed.error).is_empty() else "Validasi cloud gagal"
		}
	return {"payload": parsed.payload, "error": ""}
