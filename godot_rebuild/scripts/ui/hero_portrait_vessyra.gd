extends RefCounted
## Native canvas portrait: Vessyra — Boss/Gorgon Queen.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "serpent",
		"feature": "neutral",
		"variant": 0,
		"sigil": 3,
		"crowned": true,
		"horned": false,
		"primary": Color8(81, 90, 101),
		"accent": Color8(150, 162, 166),
		"light": Color8(227, 231, 212),
		"skin": Color8(111, 120, 131),
		"top": Color8(59, 67, 77),
		"bottom": Color8(21, 25, 31)
	}
	RENDERER.paint(canvas, box, spec)
