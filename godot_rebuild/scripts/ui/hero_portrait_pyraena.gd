extends RefCounted
## Native canvas portrait: Pyraena — True Boss/Fire Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "fire",
		"variant": 5,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(140, 55, 44),
		"accent": Color8(231, 109, 40),
		"light": Color8(255, 221, 128),
		"skin": Color8(190, 145, 124),
		"top": Color8(99, 47, 40),
		"bottom": Color8(27, 20, 27)
	}
	RENDERER.paint(canvas, box, spec)
