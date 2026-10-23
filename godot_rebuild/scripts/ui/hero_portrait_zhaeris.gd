extends RefCounted
## Native canvas portrait: Zhaeris — Boss/Shadow Ninja.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "shadow",
		"variant": 1,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(41, 42, 64),
		"accent": Color8(104, 98, 147),
		"light": Color8(196, 216, 222),
		"skin": Color8(138, 132, 156),
		"top": Color8(38, 39, 59),
		"bottom": Color8(16, 19, 29)
	}
	RENDERER.paint(canvas, box, spec)
