extends RefCounted
## Native canvas portrait: Zharok — Boss/Flaming Archer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "archer",
		"feature": "fire",
		"variant": 0,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(146, 61, 50),
		"accent": Color8(238, 116, 47),
		"light": Color8(255, 221, 128),
		"skin": Color8(181, 132, 116),
		"top": Color8(96, 44, 37),
		"bottom": Color8(30, 23, 30)
	}
	RENDERER.paint(canvas, box, spec)
