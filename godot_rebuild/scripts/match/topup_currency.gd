extends RefCounted
## Layer 9au: port of `topup_currency.py`.
##
## Locale -> currency detection, IDR conversion and price formatting for the
## top-up dialog. Static tables mirror the source module one-to-one; the
## formatting reproduces Python's `f"{int(round(val)):,}"` (banker's rounding)
## and `f"{val:,.2f}"` paths, `topup_source_oracle.py` pins every output.

const IDR_PER_UNIT := {
	"IDR": 1.0,
	"USD": 16200.0,
	"EUR": 17800.0,
	"GBP": 20900.0,
	"SGD": 12200.0,
	"MYR": 3950.0,
	"THB": 480.0,
	"VND": 0.62,
	"PHP": 270.0,
	"JPY": 108.0,
	"KRW": 11.5,
	"CNY": 2240.0,
	"AUD": 10400.0,
	"CAD": 11900.0,
	"BRL": 3050.0,
	"INR": 190.0,
	"MXN": 830.0,
	"ZAR": 900.0,
	"AED": 4400.0,
	"SAR": 4300.0,
}
const CURRENCY_SYMBOLS := {
	"IDR": "Rp ",
	"USD": "$",
	"EUR": "€",
	"GBP": "£",
	"SGD": "S$",
	"MYR": "RM ",
	"THB": "฿",
	"VND": "₫",
	"PHP": "₱",
	"JPY": "¥",
	"KRW": "₩",
	"CNY": "C$",
	"AUD": "A$",
	"CAD": "C$",
	"BRL": "R$",
	"INR": "₹",
	"MXN": "MX$",
	"ZAR": "R ",
	"AED": "AED ",
	"SAR": "SAR ",
}
const NO_DECIMAL: Array[String] = ["IDR", "JPY", "KRW", "VND"]
const REGION_CURRENCY := {
	"ID": "IDR",
	"US": "USD",
	"CA": "CAD",
	"GB": "GBP",
	"DE": "EUR",
	"FR": "EUR",
	"NL": "EUR",
	"BE": "EUR",
	"IE": "EUR",
	"ES": "EUR",
	"IT": "EUR",
	"PT": "EUR",
	"AT": "EUR",
	"FI": "EUR",
	"SG": "SGD",
	"MY": "MYR",
	"TH": "THB",
	"VN": "VND",
	"PH": "PHP",
	"JP": "JPY",
	"KR": "KRW",
	"CN": "CNY",
	"AU": "AUD",
	"BR": "BRL",
	"IN": "INR",
	"MX": "MXN",
	"ZA": "ZAR",
	"AE": "AED",
	"SA": "SAR",
}
const LANG_CURRENCY := {
	"ja": "JPY",
	"ko": "KRW",
	"zh": "CNY",
	"th": "THB",
	"vi": "VND",
	"id": "IDR",
	"ms": "MYR",
	"hi": "INR",
}
const DEFAULT_CURRENCY := "USD"


## `'id_ID.UTF-8' / 'en-US' / 'ind_ID.1252' -> ['id', 'ID']`; `C*` locales and
## empty names are "not detected" (`[null, null]`), like the source.
static func parse_locale_name(lang_code: String) -> Array:
	if lang_code.is_empty() or lang_code.begins_with("C"):
		return [null, null]
	var first := lang_code.split(".")[0].replace("-", "_")
	var parts := first.split("_")
	var language: Variant = parts[0].to_lower()
	if String(language).is_empty():
		language = null
	var region: Variant = null
	if parts.size() > 1 and parts[1].length() == 2 and _is_alpha(parts[1]):
		region = parts[1].to_upper()
	return [language, region]


## Currency for a detected (language, region) pair: region first, then
## language, then `DEFAULT_CURRENCY`. Either value may be null.
static func currency_for(lang: Variant, region: Variant) -> String:
	if region != null and not String(region).is_empty():
		var by_region: Variant = REGION_CURRENCY.get(String(region).to_upper())
		if by_region != null:
			return String(by_region)
	if lang != null and not String(lang).is_empty():
		var by_lang: Variant = LANG_CURRENCY.get(String(lang).to_lower())
		if by_lang != null:
			return String(by_lang)
	return DEFAULT_CURRENCY


## Device currency. Never fails; mirrors `detect_currency()` reading the OS
## locale (`OS.get_locale()` is `language_Script_REGION`, the same shapes the
## source parser accepts). The LANG/LC_* fallback is kept for headless runs.
static func detect_currency() -> String:
	var candidates: Array[String] = [OS.get_locale()]
	for variable in ["LC_ALL", "LC_CTYPE", "LANG"]:
		candidates.append(OS.get_environment(variable).strip_edges())
	for name in candidates:
		if name.is_empty() or name.begins_with("C"):
			continue
		var parsed := parse_locale_name(name)
		if parsed[0] == null and parsed[1] == null:
			continue
		return currency_for(parsed[0], parsed[1])
	return DEFAULT_CURRENCY


## IDR -> currency. Unknown currencies fall back to `DEFAULT_CURRENCY`.
## Returns `{"value": float, "currency": String}`.
static func convert_idr(amount_idr: float, currency: String) -> Dictionary:
	var rate: Variant = IDR_PER_UNIT.get(currency)
	var final := currency
	if rate == null or float(rate) == 0.0:
		final = DEFAULT_CURRENCY
		rate = IDR_PER_UNIT[DEFAULT_CURRENCY]
	return {"value": amount_idr / float(rate), "currency": final}


## `10000 IDR -> 'Rp 10.000' (ID), '$0.62' (US), '¥93' (JP), 'S$0.82' (SG)`.
static func format_price(amount_idr: float, currency: String) -> String:
	var converted := convert_idr(amount_idr, currency)
	var cur := String(converted.currency)
	var value := float(converted.value)
	var number := ""
	if cur in NO_DECIMAL:
		number = group_thousands(str(round_half_even(value)))
		if cur == "IDR":
			number = number.replace(",", ".")
	else:
		var fixed := "%.2f" % value
		var dot := fixed.find(".")
		number = group_thousands(fixed.substr(0, dot)) + fixed.substr(dot)
	return String(CURRENCY_SYMBOLS.get(cur, cur + " ")) + number


## `fmt_idr`: `120000 -> 'Rp 120.000'`.
static func fmt_idr(amount: float) -> String:
	return "Rp " + group_thousands(str(int(amount))).replace(",", ".")


## Python's `round()` on a float: ties go to the even neighbour.
static func round_half_even(value: float) -> int:
	var lower := floorf(value)
	var diff := value - lower
	if diff > 0.5:
		return int(lower) + 1
	if diff < 0.5:
		return int(lower)
	return int(lower) if int(lower) % 2 == 0 else int(lower) + 1


## Python's `{:,}` grouping for an integer string (sign aware).
static func group_thousands(digits: String) -> String:
	var sign := ""
	if digits.begins_with("-"):
		sign = "-"
		digits = digits.substr(1)
	var out := ""
	var count := 0
	for index in range(digits.length() - 1, -1, -1):
		out = digits[index] + out
		count += 1
		if count % 3 == 0 and index > 0:
			out = "," + out
	return sign + out


static func _is_alpha(text: String) -> bool:
	if text.is_empty():
		return false
	for character in text:
		var code := character.unicode_at(0)
		var upper := code >= 65 and code <= 90
		var lower := code >= 97 and code <= 122
		if not (upper or lower):
			return false
	return true
