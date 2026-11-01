class_name CloudSaveCodec
extends RefCounted

## Native equivalent of mobile/cloud_save.py payload build/parse/apply.
## Checksum uses canonical JSON (sorted keys, compact, UTF-8). Godot JSON
## numbers are floats after parse; canonicalization normalizes integral floats
## to integers so Python-generated payloads validate. Non-integral floats keep
## Godot's shortest representation; cross-runtime fixtures cover the contract.
const MAGIC := "MYSTIC_ARENA_BACKUP"
const VERSION := 1
const NUM_SLOTS := 3
const FLOAT_KEYS := [
	"master_volume",
	"sfx_volume",
	"bgm_volume",
	"ambient_volume",
	"voice_volume",
	"game_speed",
	"exported_at",
	"slot_created",
	"slot_last_played",
]


static func canonical_json(value: Variant) -> String:
	if value == null:
		return "null"
	if value is bool:
		return "true" if value else "false"
	if value is int:
		return str(value)
	if value is float:
		if is_finite(value) and value == floorf(value) and absf(value) < 9.0e15:
			return str(int(value)) + ".0"
		return JSON.stringify(value)
	if value is String:
		return JSON.stringify(value)
	if value is Array:
		var parts: Array[String] = []
		for item: Variant in value:
			parts.append(canonical_json(item))
		return "[" + ",".join(parts) + "]"
	if value is Dictionary:
		var keys: Array = value.keys()
		keys.sort()
		var parts: Array[String] = []
		for key: Variant in keys:
			parts.append(JSON.stringify(str(key)) + ":" + canonical_json(value[key]))
		return "{" + ",".join(parts) + "}"
	return JSON.stringify(value)


static func compute_checksum(payload: Dictionary) -> String:
	var body: Dictionary = normalize_numbers(payload.duplicate(true), "")
	body.erase("checksum")
	return canonical_json(body).sha256_text()


static func normalize_numbers(value: Variant, key: String) -> Variant:
	if value is Dictionary:
		var result: Dictionary = {}
		for child_key: Variant in value:
			result[child_key] = normalize_numbers(value[child_key], str(child_key))
		return result
	if value is Array:
		var result: Array = []
		for item: Variant in value:
			result.append(normalize_numbers(item, key))
		return result
	if value is float and is_finite(value) and value == floorf(value) and absf(value) < 9.0e15:
		if key in FLOAT_KEYS:
			return value
		return int(value)
	return value


static func build_payload(repo: SaveRepository, settings: Dictionary, now := 0.0) -> Dictionary:
	var slots: Dictionary = {}
	for slot in range(1, NUM_SLOTS + 1):
		if repo.exists(slot):
			var data := repo.load_slot(slot)
			if repo.last_error.is_empty():
				slots[str(slot)] = data
	if slots.is_empty():
		return {}
	var payload := {
		"magic": MAGIC,
		"version": VERSION,
		"exported_at": now,
		"slots": slots,
		"settings": settings,
	}
	payload = normalize_numbers(payload, "") as Dictionary
	payload["checksum"] = compute_checksum(payload)
	return payload


static func parse_payload(text: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(text)
	if not parsed is Dictionary:
		return {"ok": false, "error": "File corrupt (not valid JSON)"}
	var payload: Dictionary = parsed
	if str(payload.get("magic", "")) != MAGIC:
		return {"ok": false, "error": "Not a Mystic Arena save file"}
	var version := int(payload.get("version", 0))
	if version < 1 or version > VERSION:
		return {"ok": false, "error": "Save version %d not supported" % version}
	if not payload.get("slots") is Dictionary or payload.slots.is_empty():
		return {"ok": false, "error": "Save contains no data"}
	var checksum := str(payload.get("checksum", ""))
	if (
		checksum != compute_checksum(payload)
		and checksum != _compute_checksum_int_normal(payload)
		and checksum != _compute_checksum_float_normal(payload)
	):
		return {"ok": false, "error": "File corrupt (checksum mismatch)"}
	return {"ok": true, "payload": payload}


static func _compute_checksum_int_normal(payload: Dictionary) -> String:
	var body: Dictionary = payload.duplicate(true)
	body.erase("checksum")
	return _canonical_int_normal(body).sha256_text()


static func _compute_checksum_float_normal(payload: Dictionary) -> String:
	var body: Dictionary = payload.duplicate(true)
	body.erase("checksum")
	return _canonical_float_normal(body).sha256_text()


static func _canonical_float_normal(value: Variant) -> String:
	if value is float and is_finite(value) and value == floorf(value) and absf(value) < 9.0e15:
		return str(int(value)) + ".0"
	if value is int:
		return str(value) + ".0"
	if value is Array:
		var parts: Array[String] = []
		for item: Variant in value:
			parts.append(_canonical_float_normal(item))
		return "[" + ",".join(parts) + "]"
	if value is Dictionary:
		var keys: Array = value.keys()
		keys.sort()
		var parts: Array[String] = []
		for key: Variant in keys:
			parts.append(JSON.stringify(str(key)) + ":" + _canonical_float_normal(value[key]))
		return "{" + ",".join(parts) + "}"
	return canonical_json(value)


static func _canonical_int_normal(value: Variant) -> String:
	if value is float and is_finite(value) and value == floorf(value) and absf(value) < 9.0e15:
		return str(int(value))
	if value is Array:
		var parts: Array[String] = []
		for item: Variant in value:
			parts.append(_canonical_int_normal(item))
		return "[" + ",".join(parts) + "]"
	if value is Dictionary:
		var keys: Array = value.keys()
		keys.sort()
		var parts: Array[String] = []
		for key: Variant in keys:
			parts.append(JSON.stringify(str(key)) + ":" + _canonical_int_normal(value[key]))
		return "{" + ",".join(parts) + "}"
	return canonical_json(value)


static func summarize(payload: Dictionary) -> Dictionary:
	var highest := 0
	var best_gold := 0
	for slot_data: Dictionary in payload.get("slots", {}).values():
		for level: Variant in slot_data.get("completed_levels", []):
			highest = maxi(highest, int(level))
		best_gold = maxi(best_gold, int(slot_data.get("meta_gold", 0)))
	return {
		"highest_level": highest,
		"meta_gold": best_gold,
		"slot_count": payload.get("slots", {}).size(),
		"exported_at": float(payload.get("exported_at", 0)),
	}


static func apply_payload(
	repo: SaveRepository, payload: Dictionary, settings: GameSettings
) -> bool:
	for slot in range(1, NUM_SLOTS + 1):
		var key := str(slot)
		if payload.get("slots", {}).has(key):
			if not repo.save_slot(payload.slots[key], slot):
				return false
		else:
			repo.delete_slot(slot)
	var restored: Dictionary = payload.get("settings", {})
	for setting_key: String in GameSettings.DEFAULTS:
		if restored.has(setting_key):
			settings.set_value(setting_key, restored[setting_key])
	return true
