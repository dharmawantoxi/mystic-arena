class_name UiThemeText
extends RefCounted

## Text helpers. Measurement/glyph probes are injected so the pygame oracle
## and native Font can share the same truncation/outline semantics.


static func letter(text: String, gap := " ") -> String:
	var parts: PackedStringArray = []
	for index in range(text.length()):
		parts.append(text.substr(index, 1))
	return gap.join(parts)


static func fit_ellipsis(
	text: String, max_w: float, measure: Callable, has_glyph: Callable
) -> String:
	if float(measure.call(text)) <= max_w:
		return text
	var ell := "…" if bool(has_glyph.call("…")) else "..."
	while text.length() > 1:
		var cand := text.substr(0, text.length() - 1)
		if float(measure.call(cand + ell)) <= max_w:
			return cand + ell
		text = cand
	return ell


static func layout(
	size: Vector2, center: Variant, topleft: Variant, shadow: bool, offset: Array
) -> Array:
	var pos := Vector2.ZERO
	if center != null:
		var c := _as_vec(center)
		pos = Vector2(floori(c.x - size.x / 2.0), floori(c.y - size.y / 2.0))
	elif topleft != null:
		pos = _as_vec(topleft)
	var blits: Array = []
	if shadow:
		blits.append({"pos": pos + Vector2(float(offset[0]), float(offset[1])), "shadow": true})
	blits.append({"pos": pos, "shadow": false})
	return blits


static func outline_offsets(width: int, cheap: bool) -> Array:
	var offsets: Array = [[-width, 0], [width, 0], [0, -width], [0, width]]
	if cheap:
		offsets.append_array([[-width, -width], [width, width], [-width, width], [width, -width]])
	return offsets


static func font_measure(font: Font, font_size: int) -> Callable:
	return func(text: String) -> float:
		return font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x


static func font_glyph(font: Font) -> Callable:
	return func(ch: String) -> bool: return font.has_char(ch.unicode_at(0))


static func _as_vec(value: Variant) -> Vector2:
	if value is Vector2:
		return value
	return Vector2(float(value[0]), float(value[1]))
