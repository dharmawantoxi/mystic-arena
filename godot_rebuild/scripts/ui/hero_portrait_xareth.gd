extends RefCounted
## Native canvas portrait: Xareth — Boss/Time Voidwalker.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "void",
		"variant": 5,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(51, 39, 82),
		"accent": Color8(134, 74, 176),
		"light": Color8(213, 196, 243),
		"skin": Color8(131, 125, 149),
		"top": Color8(40, 33, 67),
		"bottom": Color8(21, 23, 37)
	}
	RENDERER.paint(canvas, box, spec)
