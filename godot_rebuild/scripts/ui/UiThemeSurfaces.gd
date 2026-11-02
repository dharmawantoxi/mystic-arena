class_name UiThemeSurfaces
extends RefCounted

## Pure surface formulas from ui_theme.py plus bounded native caches.
static var _grad_cache: Dictionary = {}
static var _glow_cache: Dictionary = {}
static var _shadow_cache: Dictionary = {}
static var _grad_text_cache: Dictionary = {}


static func clear_caches() -> void:
	_grad_cache.clear()
	_glow_cache.clear()
	_shadow_cache.clear()
	_grad_text_cache.clear()


static func cache_sizes() -> Dictionary:
	return {
		"gradient": _grad_cache.size(),
		"glow": _glow_cache.size(),
		"shadow": _shadow_cache.size(),
		"gradient_text": _grad_text_cache.size(),
	}


static func gradient_rows(w: int, h: int, top: Array, bottom: Array) -> Array:
	w = maxi(2, w)
	h = maxi(2, h)
	var rows: Array = []
	for y in range(h):
		var t := float(y) / float(maxi(1, h - 1))
		(
			rows
			. append(
				[
					y,
					int(float(top[0]) + (float(bottom[0]) - float(top[0])) * t),
					int(float(top[1]) + (float(bottom[1]) - float(top[1])) * t),
					int(float(top[2]) + (float(bottom[2]) - float(top[2])) * t),
				]
			)
		)
	return rows


static func gradient_data(w: int, h: int, top: Array, bottom: Array, radius := 0) -> Dictionary:
	w = maxi(2, w)
	h = maxi(2, h)
	var key := "%d:%d:%s:%s:%d" % [w, h, str(top), str(bottom), radius]
	if _grad_cache.has(key):
		return _grad_cache[key]
	var data := {"size": [w, h], "rows": gradient_rows(w, h, top, bottom), "radius": radius}
	_grad_cache[key] = data
	return data


static func radial_data(w: int, h: int, color: Array, alpha: int) -> Dictionary:
	w = maxi(8, w)
	h = maxi(8, h)
	var a := maxi(4, mini(120, floori(alpha / 8.0) * 8))
	var key := "%d:%d:%s:%d" % [w, h, str(color), a]
	if _glow_cache.has(key):
		return _glow_cache[key]
	var blocks: Array = []
	var cx := w / 2.0
	var cy := h / 2.0
	var maxd := sqrt(cx * cx + cy * cy)
	for y in range(0, h, 2):
		for x in range(0, w, 2):
			var dx := x - cx
			var dy := y - cy
			var d := sqrt(dx * dx + dy * dy) / maxd
			if d < 1.0:
				var aa := int(a * (1.0 - d) * (1.0 - d))
				if aa > 0:
					(
						blocks
						. append(
							{
								"op": "rect",
								"color": [color[0], color[1], color[2], aa],
								"rect": [x, y, 2, 2],
								"width": 0,
								"radius": 0,
							}
						)
					)
	var data := {"size": [w, h], "blocks": blocks}
	_glow_cache[key] = data
	return data


static func shadow_data(w: int, h: int, radius := 12, alpha := 110, spread := 4) -> Dictionary:
	w = maxi(2, w + spread * 2)
	h = maxi(2, h + spread * 2)
	var key := "%d:%d:%d:%d" % [w, h, radius, alpha]
	if _shadow_cache.has(key):
		return _shadow_cache[key]
	var sw := maxi(4, floori(w / 8.0))
	var sh := maxi(4, floori(h / 8.0))
	var data := {
		"size": [w, h],
		"small_ops":
		[
			{
				"op": "rect",
				"color": [0, 0, 0, alpha],
				"rect": [0, 0, sw, sh],
				"width": 0,
				"radius": maxi(1, floori(radius / 8.0)),
			}
		],
	}
	_shadow_cache[key] = data
	return data


static func gradient_text_data(
	font_key: String, text: String, top: Array, bottom: Array, height: int
) -> Dictionary:
	var key := "%s:%s:%s:%s" % [font_key, text, str(top), str(bottom)]
	if _grad_text_cache.has(key):
		return _grad_text_cache[key]
	if _grad_text_cache.size() > UiTheme.integer("surface.gradient_text_cache_limit"):
		_grad_text_cache.clear()
	var data := {"rows": gradient_rows(2, maxi(1, height), top, bottom)}
	_grad_text_cache[key] = data
	return data
