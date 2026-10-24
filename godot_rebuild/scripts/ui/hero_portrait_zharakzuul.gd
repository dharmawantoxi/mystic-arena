extends RefCounted
## Native canvas portrait: Zharakzuul — True Boss/Void Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "void",
		"variant": 2,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(50, 38, 81),
		"accent": Color8(137, 77, 179),
		"light": Color8(213, 196, 243),
		"skin": Color8(133, 127, 151),
		"top": Color8(37, 30, 64),
		"bottom": Color8(19, 21, 35)
	}
	RENDERER.paint(canvas, box, spec)
