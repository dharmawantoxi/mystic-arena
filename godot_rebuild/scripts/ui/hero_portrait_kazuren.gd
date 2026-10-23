extends RefCounted
## Native canvas portrait: Kazuren — Boss/Shadow Ninja.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "shadow",
		"variant": 4,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(39, 40, 62),
		"accent": Color8(98, 92, 141),
		"light": Color8(196, 216, 222),
		"skin": Color8(131, 125, 149),
		"top": Color8(42, 43, 63),
		"bottom": Color8(21, 24, 34)
	}
	RENDERER.paint(canvas, box, spec)
