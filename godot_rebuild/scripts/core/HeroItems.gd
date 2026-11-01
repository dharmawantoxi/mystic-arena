class_name HeroItems
extends RefCounted

## Native port of hero_items.py catalog/shop helpers. Python remains the oracle;
## tools/prepare_godot_items.py bakes the catalog, class pages and UI labels.
const DEFAULT_PATH := "res://data/hero_items.json"

var load_error := ""
var catalog: Dictionary = {}
var max_item_slots := 6
var item_flat_cost := 4500
var magic_role_keywords: Array = []
var class_info: Dictionary = {}
var class_overrides: Dictionary = {}
var category_to_class: Dictionary = {}
var class_item_order: Dictionary = {}
var items_per_page := 8
var shop_pages: Array = []
var shop_page_meta: Array = []
var item_shop_order: Array = []
var category_info: Dictionary = {}
var field_labels: Dictionary = {}
var group_labels: Dictionary = {}
var mech_groups: Array = []
var mech_field_order: Dictionary = {}
var mech_value_types: Dictionary = {}
var pct_keys: Array = []
var frame_keys: Array = []


func _init(path := DEFAULT_PATH) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary or int(parsed.get("schema", 0)) != 1:
		load_error = "Invalid hero items JSON: %s" % path
		return
	for key: String in [
		"catalog",
		"magic_role_keywords",
		"class_info",
		"class_overrides",
		"category_to_class",
		"class_item_order",
		"shop_pages",
		"shop_page_meta",
		"item_shop_order",
		"category_info",
		"field_labels",
		"group_labels",
		"mech_groups",
		"mech_field_order",
		"mech_value_types",
		"pct_keys",
		"frame_keys"
	]:
		if not parsed.has(key):
			load_error = "Missing hero items field: %s" % key
			return
	catalog = parsed.catalog
	max_item_slots = int(parsed.get("max_item_slots", 6))
	item_flat_cost = int(parsed.get("item_flat_cost", 4500))
	magic_role_keywords = parsed.magic_role_keywords
	class_info = parsed.class_info
	class_overrides = parsed.class_overrides
	category_to_class = parsed.category_to_class
	class_item_order = parsed.class_item_order
	items_per_page = int(parsed.get("items_per_page", 8))
	shop_pages = parsed.shop_pages
	shop_page_meta = parsed.shop_page_meta
	item_shop_order = parsed.item_shop_order
	category_info = parsed.category_info
	field_labels = parsed.field_labels
	group_labels = parsed.group_labels
	mech_groups = parsed.mech_groups
	mech_field_order = parsed.mech_field_order
	mech_value_types = parsed.mech_value_types
	pct_keys = parsed.pct_keys
	frame_keys = parsed.frame_keys
	if catalog.is_empty() or shop_pages.is_empty() or item_shop_order.size() != catalog.size():
		load_error = "Hero items contract requires a catalog and complete shop pages"


func valid() -> bool:
	return load_error.is_empty() and not catalog.is_empty()


func item(item_id: String) -> Dictionary:
	return catalog.get(item_id, {})


func item_class(item_id: String) -> String:
	var data := item(item_id)
	if data.is_empty():
		return "physical"
	if class_overrides.has(item_id):
		return str(class_overrides[item_id])
	if bool(data.get("magic_only", false)):
		return "magic"
	return str(category_to_class.get(str(data.get("category", "")), "physical"))


func is_magic_role(role: String) -> bool:
	var lower := role.to_lower()
	if lower.is_empty() or "anti-mage" in lower:
		return false
	for keyword: String in magic_role_keywords:
		if keyword in lower:
			return true
	return false


func class_label(item_class_id: String) -> String:
	return str(class_info.get(item_class_id, ["PHYSICAL", [255, 150, 80]])[0])


func class_color(item_class_id: String) -> Color:
	var rgb: Array = class_info.get(item_class_id, ["PHYSICAL", [255, 150, 80]])[1]
	return Color(float(rgb[0]) / 255.0, float(rgb[1]) / 255.0, float(rgb[2]) / 255.0)


func category_label(category: String) -> String:
	return str(category_info.get(category, [category.to_upper(), [255, 255, 255]])[0])


func category_color(category: String) -> Color:
	var rgb: Array = category_info.get(category, [category.to_upper(), [255, 255, 255]])[1]
	return Color(float(rgb[0]) / 255.0, float(rgb[1]) / 255.0, float(rgb[2]) / 255.0)


func page_count() -> int:
	return shop_pages.size()


func page_items(index: int) -> Array:
	if index < 0 or index >= shop_pages.size():
		return []
	return shop_pages[index]


func page_meta(index: int) -> Dictionary:
	if index < 0 or index >= shop_page_meta.size():
		return {}
	var row: Array = shop_page_meta[index]
	return {"class": str(row[0]), "page": int(row[1]), "pages": int(row[2]), "total": int(row[2])}


func mechanics(item_id: String, lang := "id") -> Array:
	var data := item(item_id)
	var out: Array = []
	var en := lang == "en"
	for group_key: String in mech_groups:
		var group: Dictionary = data.get(group_key, {})
		if group.is_empty():
			continue
		var glabel: String = str(
			group_labels.get(group_key, [group_key, group_key])[1 if en else 0]
		)
		var gname := str(group.get("name", ""))
		out.append(
			{
				"kind": "header",
				"text": "[%s]%s" % [glabel, (" " + gname) if not gname.is_empty() else ""]
			}
		)
		var order: Array = mech_field_order.get(item_id, {}).get(group_key, group.keys())
		for key: String in order:
			if key == "name" or not group.has(key):
				continue
			var labels: Array = field_labels.get(key, [key, key])
			var label := str(labels[1 if en else 0])
			var vtype := str(mech_value_types.get(item_id, {}).get(group_key, {}).get(key, ""))
			out.append(
				{
					"kind": "bullet",
					"text": "• %s: %s" % [label, _fmt_mech_value(key, group[key], en, vtype)]
				}
			)
	return out


func _fmt_mech_value(key: String, value: Variant, en: bool, vtype := "") -> String:
	if key == "crit_mult":
		return "x%s" % _fmt_g(float(value))
	if key in pct_keys:
		return "%s%%" % _fmt_g(float(value) * 100.0)
	if key in frame_keys:
		var secs := float(value) / 60.0
		return "%s dtk" % _fmt_g(secs) if not en else "%ss" % _fmt_g(secs)
	return _fmt_plain(value, vtype)


static func _fmt_g(value: float) -> String:
	# Python "%g": 6 significant digits, strip trailing zeros, scientific when
	# exponent < -4 or >= 6. Godot's % operator has no %g specifier.
	if value == 0.0:
		return "0"
	var av := absf(value)
	var exponent := int(floor(log(av) / log(10.0)))
	if exponent < -4 or exponent >= 6:
		var mant := value / pow(10.0, exponent)
		var ms := String.num(mant, 5).rstrip("0").rstrip(".")
		var sign := "+" if exponent >= 0 else "-"
		return "%se%s%02d" % [ms, sign, absi(exponent)]
	var decimals := maxi(0, 5 - exponent)
	var text := String.num(value, decimals)
	if "." in text:
		text = text.rstrip("0").rstrip(".")
	return text


static func _fmt_plain(value: Variant, vtype := "") -> String:
	# JSON numbers lose Python's int/float distinction; the contract exports the
	# source type so plain values keep str(52) == "52" vs str(3.0) == "3.0".
	if vtype == "int":
		return str(int(value))
	if vtype == "bool":
		return "True" if bool(value) else "False"
	if vtype == "float" or value is float:
		var f := float(value)
		if is_equal_approx(f, roundf(f)) and absf(f) < 1e15:
			return String.num(f, 1)
		return str(f)
	return str(value)
