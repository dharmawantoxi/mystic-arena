extends RefCounted
## Native canvas portrait: Seraphienne — True Boss/Angelic Warrior.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "holy",
		"variant": 3,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(156, 124, 62),
		"accent": Color8(223, 184, 85),
		"light": Color8(255, 244, 190),
		"skin": Color8(126, 91, 82),
		"top": Color8(107, 87, 53),
		"bottom": Color8(28, 25, 24)
	}
	RENDERER.paint(canvas, box, spec)
