# CloudSaveCodec.gd — canonical JSON compatible with Python json.dumps.
#
# The Pygame cloud-save oracle hashes sorted, compact UTF-8 JSON. Keep this
# byte-level wire format separate from the Android provider and UI logic.
extends RefCounted

static func canonical_json(value: Variant) -> String:
	if value is Dictionary:
		var keys: Array = value.keys()
		keys.sort()
		var parts := PackedStringArray()
		for key in keys:
			parts.append(_python_json_string(str(key)) + ":" +
				canonical_json(value[key]))
		return "{" + ",".join(parts) + "}"
	if value is Array:
		var parts := PackedStringArray()
		for item in value:
			parts.append(canonical_json(item))
		return "[" + ",".join(parts) + "]"
	if value is String:
		return _python_json_string(value)
	if value is float:
		return _python_float_json(value)
	return JSON.stringify(value, "", false, true)


static func _python_json_string(value: String) -> String:
	var result := "\""
	for i in value.length():
		var code := value.unicode_at(i)
		match code:
			8:
				result += "\\b"
			9:
				result += "\\t"
			10:
				result += "\\n"
			12:
				result += "\\f"
			13:
				result += "\\r"
			34:
				result += "\\\""
			92:
				result += "\\\\"
			_:
				if code < 32:
					result += "\\u" + String.num_int64(code, 16).pad_zeros(4)
				else:
				result += value.substr(i, 1)
	return result + "\""


## Python json.dumps uses the shortest decimal that round-trips to the same
## binary64 value, keeps `.0` on integral floats, and switches to exponent
## notation outside [-4, 15]. Godot JSON.stringify(full_precision=true) emits
## 17 fixed decimal places (for example 0.35 -> 0.34999999999999998), so it
## cannot be used directly for the Pygame checksum oracle.
static func _python_float_json(value: float) -> String:
	if not is_finite(value):
		return "null"
	if value == 0.0:
		return "-0.0" if String.num(value, 1).begins_with("-") else "0.0"

	var exponent := _decimal_exponent(absf(value))
	for significant_digits in range(1, 18):
		var decimals := significant_digits - 1 - exponent
		var candidate := ""
		if exponent < -4 and decimals <= 32:
			candidate = _fixed_to_scientific(String.num(value, decimals))
		elif exponent < -4:
			candidate = _scaled_scientific(value, exponent, significant_digits)
		elif exponent >= 16:
			candidate = _large_fixed_scientific(value, exponent, significant_digits)
		elif decimals >= 0:
			candidate = String.num(value, decimals)
			if candidate.find(".") < 0:
				candidate += ".0"
		else:
			var places := -decimals
			var scale := pow(10.0, places)
			var rounded := String.num(value / scale, 0)
			candidate = rounded + "0".repeat(places)
			if candidate.find(".") < 0:
				candidate += ".0"
		if not candidate.is_empty() and candidate.to_float() == value:
			return candidate

	# Save fields use ordinary finite game-domain values. This fallback retains
	# every digit Godot can print if a future payload reaches an exotic exponent.
	return JSON.stringify(value, "", false, true)


static func _decimal_exponent(value: float) -> int:
	var exponent := int(floor(log(value) / log(10.0)))
	var decade := pow(10.0, exponent)
	if decade == 0.0 or not is_finite(decade):
		return exponent
	while value < decade:
		exponent -= 1
		decade /= 10.0
	while exponent < 308 and value >= decade * 10.0:
		exponent += 1
		decade *= 10.0
	return exponent


static func _fixed_to_scientific(fixed: String) -> String:
	var sign := ""
	var unsigned := fixed
	if unsigned.begins_with("-"):
		sign = "-"
		unsigned = unsigned.substr(1)
	var decimal_at := unsigned.find(".")
	var integer_digits := unsigned if decimal_at < 0 else unsigned.substr(0, decimal_at)
	var digits := integer_digits
	if decimal_at >= 0:
		digits += unsigned.substr(decimal_at + 1)
	var first_nonzero := -1
	for i in digits.length():
		if digits.substr(i, 1) != "0":
			first_nonzero = i
			break
	if first_nonzero < 0:
		return sign + "0.0"
	var exponent := integer_digits.length() - first_nonzero - 1
	digits = digits.substr(first_nonzero)
	while digits.length() > 1 and digits.ends_with("0"):
		digits = digits.substr(0, digits.length() - 1)
	return _scientific_from_digits(digits, exponent, sign)


static func _large_fixed_scientific(value: float, exponent: int,
		significant_digits: int) -> String:
	var sign := "-" if value < 0.0 else ""
	var all_digits := String.num(absf(value), 0)
	var kept_count := mini(significant_digits, all_digits.length())
	var digits := all_digits.substr(0, kept_count)
	if all_digits.length() > kept_count:
		var next_digit := int(all_digits.substr(kept_count, 1))
		var remaining := all_digits.substr(kept_count + 1)
		var round_up := next_digit > 5
		if next_digit == 5:
			round_up = not remaining.replace("0", "").is_empty() \
				or int(digits.substr(kept_count - 1, 1)) % 2 == 1
		if round_up:
			digits = str(digits.to_int() + 1)
			if digits.length() > kept_count:
				exponent += 1
				digits = digits.substr(0, kept_count)
	while digits.length() > 1 and digits.ends_with("0"):
		digits = digits.substr(0, digits.length() - 1)
	return _scientific_from_digits(digits, exponent, sign)


static func _scaled_scientific(value: float, exponent: int,
		significant_digits: int) -> String:
	var decade := pow(10.0, exponent)
	if decade == 0.0 or not is_finite(decade):
		return ""
	var normalized := absf(value) / decade
	if exponent < 0:
		normalized = absf(value) * pow(10.0, -exponent)
	while normalized < 1.0:
		exponent -= 1
		normalized *= 10.0
	while normalized >= 10.0:
		exponent += 1
		normalized /= 10.0
	var mantissa := String.num(normalized, significant_digits - 1)
	if mantissa.begins_with("10"):
		exponent += 1
		mantissa = "1"
	var digits := mantissa.replace(".", "")
	while digits.length() > 1 and digits.ends_with("0"):
		digits = digits.substr(0, digits.length() - 1)
	return _scientific_from_digits(digits, exponent,
		"-" if value < 0.0 else "")


static func _scientific_from_digits(digits: String, exponent: int,
		sign: String) -> String:
	var mantissa := digits.substr(0, 1)
	if digits.length() > 1:
		mantissa += "." + digits.substr(1)
	var exponent_digits := str(absi(exponent))
	if exponent_digits.length() < 2:
		exponent_digits = "0" + exponent_digits
	var exponent_sign := "+" if exponent >= 0 else "-"
	return sign + mantissa + "e" + exponent_sign + exponent_digits


