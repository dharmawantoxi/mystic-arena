extends RefCounted
## Native canvas portrait: Kassadin — Boss/Void Walker.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "void",
		"variant": 0,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(59, 47, 90),
		"accent": Color8(148, 88, 190),
		"light": Color8(213, 196, 243),
		"skin": Color8(135, 129, 153),
		"top": Color8(47, 40, 74),
		"bottom": Color8(16, 16, 30)
	}
	RENDERER.paint(canvas, box, spec)
