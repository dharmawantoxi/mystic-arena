extends RefCounted
## Native canvas portrait: Kyrenzai — True Boss/Kagune Ghoul.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 1,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(66, 75, 86),
		"accent": Color8(143, 155, 159),
		"light": Color8(227, 231, 212),
		"skin": Color8(96, 105, 116),
		"top": Color8(61, 69, 79),
		"bottom": Color8(27, 31, 37)
	}
	RENDERER.paint(canvas, box, spec)
