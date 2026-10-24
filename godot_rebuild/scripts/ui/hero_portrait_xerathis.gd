extends RefCounted
## Native canvas portrait: Xerathis — Boss/Crystal Sorceress.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "crystal",
		"variant": 5,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(86, 72, 136),
		"accent": Color8(161, 123, 216),
		"light": Color8(230, 220, 250),
		"skin": Color8(214, 183, 156),
		"top": Color8(65, 57, 105),
		"bottom": Color8(26, 26, 46)
	}
	RENDERER.paint(canvas, box, spec)
