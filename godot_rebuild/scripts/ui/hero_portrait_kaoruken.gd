extends RefCounted
## Native canvas portrait: Kaoruken — Boss/Chakra Prodigy.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "neutral",
		"variant": 5,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(69, 78, 89),
		"accent": Color8(142, 154, 158),
		"light": Color8(227, 231, 212),
		"skin": Color8(153, 109, 92),
		"top": Color8(59, 67, 77),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
