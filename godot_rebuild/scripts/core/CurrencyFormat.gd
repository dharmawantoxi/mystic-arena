class_name CurrencyFormat
extends RefCounted

## Static display conversion from topup_currency.py. Not a live FX feed.
var rates: Dictionary = {}
var symbols: Dictionary = {}
var no_decimal: Array = []
var region_currency: Dictionary = {}
var lang_currency: Dictionary = {}
var default_currency := "USD"


func _init(currency_data: Dictionary = {}) -> void:
	rates = currency_data.get("IDR_PER_UNIT", {})
	symbols = currency_data.get("CURRENCY_SYMBOLS", {})
	no_decimal = currency_data.get("NO_DECIMAL", [])
	region_currency = currency_data.get("REGION_CURRENCY", {})
	lang_currency = currency_data.get("LANG_CURRENCY", {})
	default_currency = str(currency_data.get("DEFAULT_CURRENCY", "USD"))


func currency_for(region: String, language: String) -> String:
	if region_currency.has(region.to_upper()):
		return str(region_currency[region.to_upper()])
	if lang_currency.has(language):
		return str(lang_currency[language])
	return default_currency


func format_idr(amount_idr: float, currency: String) -> String:
	var rate := float(rates.get(currency, 0))
	if rate <= 0:
		return "Rp %d" % int(amount_idr)
	var value := amount_idr / rate
	var symbol := str(symbols.get(currency, currency + " "))
	if currency in no_decimal:
		return symbol + str(int(round(value)))
	return symbol + ("%.2f" % value)
