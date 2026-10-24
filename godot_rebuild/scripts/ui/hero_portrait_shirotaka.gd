extends RefCounted
## Native canvas portrait: Shirotaka — Boss/Tideborn Shinobi.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "water",
		"variant": 3,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(46, 104, 120),
		"accent": Color8(67, 171, 174),
		"light": Color8(199, 246, 224),
		"skin": Color8(181, 132, 116),
		"top": Color8(33, 75, 92),
		"bottom": Color8(17, 26, 37)
	}
	RENDERER.paint(canvas, box, spec)
