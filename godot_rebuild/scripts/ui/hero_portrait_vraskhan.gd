extends RefCounted
## Native canvas portrait: Vraskhan — Boss/Shadow Assassin.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "shadow",
		"variant": 3,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(40, 41, 63),
		"accent": Color8(103, 97, 146),
		"light": Color8(196, 216, 222),
		"skin": Color8(133, 127, 151),
		"top": Color8(41, 42, 62),
		"bottom": Color8(18, 21, 31)
	}
	RENDERER.paint(canvas, box, spec)
