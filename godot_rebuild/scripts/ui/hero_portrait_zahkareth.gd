extends RefCounted
## Native canvas portrait: Zahkareth — Boss/Golden Tyrant.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "holy",
		"variant": 5,
		"sigil": 0,
		"crowned": true,
		"horned": false,
		"primary": Color8(152, 120, 58),
		"accent": Color8(225, 186, 87),
		"light": Color8(255, 244, 190),
		"skin": Color8(190, 145, 124),
		"top": Color8(108, 88, 54),
		"bottom": Color8(34, 31, 30)
	}
	RENDERER.paint(canvas, box, spec)
