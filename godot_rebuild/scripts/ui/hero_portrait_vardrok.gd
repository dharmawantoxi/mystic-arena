extends RefCounted
## Native canvas portrait: Vardrok — Boss/Axe-King.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 5,
		"sigil": 6,
		"crowned": true,
		"horned": false,
		"primary": Color8(68, 77, 88),
		"accent": Color8(138, 150, 154),
		"light": Color8(227, 231, 212),
		"skin": Color8(126, 91, 82),
		"top": Color8(61, 69, 79),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
