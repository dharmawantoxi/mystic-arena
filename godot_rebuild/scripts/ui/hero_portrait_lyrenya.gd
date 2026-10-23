extends RefCounted
## Native canvas portrait: Lyrenya — Boss/Nature Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "nature",
		"variant": 4,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(61, 99, 59),
		"accent": Color8(108, 149, 65),
		"light": Color8(215, 230, 151),
		"skin": Color8(207, 168, 142),
		"top": Color8(60, 85, 55),
		"bottom": Color8(21, 30, 25)
	}
	RENDERER.paint(canvas, box, spec)
