extends RefCounted
## Native canvas portrait: Shimorakh — Boss/Shadow Root.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "shadow",
		"variant": 2,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(49, 50, 72),
		"accent": Color8(107, 101, 150),
		"light": Color8(196, 216, 222),
		"skin": Color8(135, 129, 153),
		"top": Color8(42, 43, 63),
		"bottom": Color8(18, 21, 31)
	}
	RENDERER.paint(canvas, box, spec)
