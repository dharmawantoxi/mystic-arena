extends RefCounted
## Native canvas portrait: Kaervosth — Boss/Stormblade Knight.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "storm",
		"variant": 4,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(51, 78, 122),
		"accent": Color8(100, 185, 225),
		"light": Color8(231, 241, 174),
		"skin": Color8(190, 145, 124),
		"top": Color8(49, 71, 111),
		"bottom": Color8(24, 29, 46)
	}
	RENDERER.paint(canvas, box, spec)
