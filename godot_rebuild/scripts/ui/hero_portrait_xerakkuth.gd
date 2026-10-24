extends RefCounted
## Native canvas portrait: Xerakkuth — Boss/Desert Scorpion.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "sand",
		"variant": 1,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(125, 92, 54),
		"accent": Color8(205, 166, 96),
		"light": Color8(249, 224, 165),
		"skin": Color8(155, 122, 84),
		"top": Color8(92, 70, 48),
		"bottom": Color8(29, 25, 24)
	}
	RENDERER.paint(canvas, box, spec)
