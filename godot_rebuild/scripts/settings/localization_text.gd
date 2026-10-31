extends RefCounted
## Source `tr()` bridge for Controls: resolves the Localization autoload lazily,
## so panels can stay testable without the runtime mounted.


static func runtime(host: Node) -> Object:
	if host == null or not host.is_inside_tree():
		return null
	return host.get_tree().root.get_node_or_null("Localization")


static func translate(host: Node, key: String, fallback: String, values: Dictionary = {}) -> String:
	# Mirrors localization.tr(): missing values keep the raw template, unknown
	# keys fall back to the caller's copy instead of leaking the key to screen.
	var localizer: Object = runtime(host)
	if localizer != null:
		var translated: Variant = localizer.call("translate", key, values)
		if translated != null:
			return String(translated)
	return fallback.format(values) if not values.is_empty() else fallback
