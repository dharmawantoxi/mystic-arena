extends RefCounted
## Native canvas portrait: Seth'rakhaar — Boss/Sunforged Butcher.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "fire",
		"variant": 2,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(145, 60, 49),
		"accent": Color8(235, 113, 44),
		"light": Color8(255, 221, 128),
		"skin": Color8(181, 132, 116),
		"top": Color8(96, 44, 37),
		"bottom": Color8(33, 26, 33)
	}
	RENDERER.paint(canvas, box, spec)
