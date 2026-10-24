extends RefCounted
## Native canvas portrait: Pyrhaan — Boss/Agility.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "neutral",
		"variant": 3,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(72, 81, 92),
		"accent": Color8(142, 154, 158),
		"light": Color8(227, 231, 212),
		"skin": Color8(153, 109, 92),
		"top": Color8(61, 69, 79),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
