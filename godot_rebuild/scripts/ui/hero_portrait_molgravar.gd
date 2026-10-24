extends RefCounted
## Native canvas portrait: Molgravar — True Boss/Stone Golem.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "golem",
		"feature": "neutral",
		"variant": 4,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(74, 83, 94),
		"accent": Color8(153, 165, 169),
		"light": Color8(227, 231, 212),
		"skin": Color8(113, 117, 102),
		"top": Color8(57, 65, 75),
		"bottom": Color8(20, 24, 30)
	}
	RENDERER.paint(canvas, box, spec)
