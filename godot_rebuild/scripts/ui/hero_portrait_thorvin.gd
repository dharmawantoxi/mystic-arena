extends RefCounted
## Native canvas portrait: Thorvin — Boss/Ironbound Warden.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 5,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(75, 84, 95),
		"accent": Color8(137, 149, 153),
		"light": Color8(227, 231, 212),
		"skin": Color8(207, 168, 142),
		"top": Color8(54, 62, 72),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
