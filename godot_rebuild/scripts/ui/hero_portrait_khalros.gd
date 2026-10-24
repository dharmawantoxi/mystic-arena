extends RefCounted
## Native canvas portrait: Khalros — Boss/Beast Commander.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 3,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(81, 90, 101),
		"accent": Color8(146, 158, 162),
		"light": Color8(227, 231, 212),
		"skin": Color8(111, 120, 131),
		"top": Color8(55, 63, 73),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
