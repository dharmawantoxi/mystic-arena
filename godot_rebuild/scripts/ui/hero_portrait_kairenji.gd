extends RefCounted
## Native canvas portrait: Kairenji — Boss/Shadow Ninja.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "shadow",
		"variant": 2,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(51, 52, 74),
		"accent": Color8(104, 98, 147),
		"light": Color8(196, 216, 222),
		"skin": Color8(135, 129, 153),
		"top": Color8(32, 33, 53),
		"bottom": Color8(19, 22, 32)
	}
	RENDERER.paint(canvas, box, spec)
