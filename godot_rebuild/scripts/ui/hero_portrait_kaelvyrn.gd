extends RefCounted
## Native canvas portrait: Kaelvyrn — Boss/Gilded Marauder.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "holy",
		"variant": 4,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(157, 125, 63),
		"accent": Color8(223, 184, 85),
		"light": Color8(255, 244, 190),
		"skin": Color8(181, 132, 116),
		"top": Color8(102, 82, 48),
		"bottom": Color8(34, 31, 30)
	}
	RENDERER.paint(canvas, box, spec)
