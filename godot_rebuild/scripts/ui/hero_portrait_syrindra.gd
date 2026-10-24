extends RefCounted
## Native canvas portrait: Syrindra — Boss/Dark Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "shadow",
		"variant": 1,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(40, 41, 63),
		"accent": Color8(101, 95, 144),
		"light": Color8(196, 216, 222),
		"skin": Color8(146, 140, 164),
		"top": Color8(37, 38, 58),
		"bottom": Color8(21, 24, 34)
	}
	RENDERER.paint(canvas, box, spec)
