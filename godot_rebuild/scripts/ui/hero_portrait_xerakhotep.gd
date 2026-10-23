extends RefCounted
## Native canvas portrait: Xerakhotep — Boss/Sun Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "fire",
		"variant": 1,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(136, 51, 40),
		"accent": Color8(237, 115, 46),
		"light": Color8(255, 221, 128),
		"skin": Color8(214, 183, 156),
		"top": Color8(102, 50, 43),
		"bottom": Color8(30, 23, 30)
	}
	RENDERER.paint(canvas, box, spec)
