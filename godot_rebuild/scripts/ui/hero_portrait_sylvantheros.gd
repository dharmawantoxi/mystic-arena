extends RefCounted
## Native canvas portrait: Sylvantheros — Boss/Verdant Farseer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "nature",
		"variant": 4,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(59, 97, 57),
		"accent": Color8(112, 153, 69),
		"light": Color8(215, 230, 151),
		"skin": Color8(181, 132, 116),
		"top": Color8(60, 85, 55),
		"bottom": Color8(23, 32, 27)
	}
	RENDERER.paint(canvas, box, spec)
