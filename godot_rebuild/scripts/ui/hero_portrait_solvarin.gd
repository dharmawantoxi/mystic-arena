extends RefCounted
## Native canvas portrait: Solvarin — True Boss/Paladin.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "holy",
		"variant": 2,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(154, 122, 60),
		"accent": Color8(228, 189, 90),
		"light": Color8(255, 244, 190),
		"skin": Color8(126, 91, 82),
		"top": Color8(108, 88, 54),
		"bottom": Color8(27, 24, 23)
	}
	RENDERER.paint(canvas, box, spec)
