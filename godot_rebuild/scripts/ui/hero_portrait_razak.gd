extends RefCounted
## Native canvas portrait: Razak — Boss/Fire Rider.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "rider",
		"feature": "fire",
		"variant": 5,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(137, 52, 41),
		"accent": Color8(234, 112, 43),
		"light": Color8(255, 221, 128),
		"skin": Color8(207, 168, 142),
		"top": Color8(105, 53, 46),
		"bottom": Color8(34, 27, 34)
	}
	RENDERER.paint(canvas, box, spec)
