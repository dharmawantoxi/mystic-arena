extends RefCounted
## Native canvas portrait: Wiro — Boss/Martial Artist.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "neutral",
		"variant": 2,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(75, 84, 95),
		"accent": Color8(138, 150, 154),
		"light": Color8(227, 231, 212),
		"skin": Color8(126, 91, 82),
		"top": Color8(53, 61, 71),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
