extends RefCounted
## Native canvas portrait: Yamako — True Boss/Woodshaper.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "treant",
		"feature": "nature",
		"variant": 3,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(60, 98, 58),
		"accent": Color8(119, 160, 76),
		"light": Color8(215, 230, 151),
		"skin": Color8(101, 92, 65),
		"top": Color8(62, 87, 57),
		"bottom": Color8(18, 27, 22)
	}
	RENDERER.paint(canvas, box, spec)
