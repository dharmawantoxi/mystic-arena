extends RefCounted
## Native canvas portrait: Verdanix — Boss/Nature Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "nature",
		"variant": 3,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(67, 105, 65),
		"accent": Color8(117, 158, 74),
		"light": Color8(215, 230, 151),
		"skin": Color8(153, 109, 92),
		"top": Color8(58, 83, 53),
		"bottom": Color8(21, 30, 25)
	}
	RENDERER.paint(canvas, box, spec)
