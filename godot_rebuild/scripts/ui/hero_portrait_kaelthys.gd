extends RefCounted
## Native canvas portrait: Kaelthys — Boss/Water Swordsman.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "water",
		"variant": 0,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(36, 94, 110),
		"accent": Color8(67, 171, 174),
		"light": Color8(199, 246, 224),
		"skin": Color8(181, 132, 116),
		"top": Color8(38, 80, 97),
		"bottom": Color8(19, 28, 39)
	}
	RENDERER.paint(canvas, box, spec)
