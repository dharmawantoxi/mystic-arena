extends RefCounted
## Native canvas portrait: Pyraklos — Boss/Spartan.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 5,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(70, 79, 90),
		"accent": Color8(151, 163, 167),
		"light": Color8(227, 231, 212),
		"skin": Color8(207, 168, 142),
		"top": Color8(58, 66, 76),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
