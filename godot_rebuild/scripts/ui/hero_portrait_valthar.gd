extends RefCounted
## Native canvas portrait: Valthar — Boss/Golden Sentinel.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "holy",
		"variant": 0,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(153, 121, 59),
		"accent": Color8(229, 190, 91),
		"light": Color8(255, 244, 190),
		"skin": Color8(214, 183, 156),
		"top": Color8(99, 79, 45),
		"bottom": Color8(32, 29, 28)
	}
	RENDERER.paint(canvas, box, spec)
