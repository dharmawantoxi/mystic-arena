extends RefCounted
## Native canvas portrait: Kaelthorn — Boss/Azure Warrior.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 4,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(81, 90, 101),
		"accent": Color8(145, 157, 161),
		"light": Color8(227, 231, 212),
		"skin": Color8(181, 132, 116),
		"top": Color8(60, 68, 78),
		"bottom": Color8(19, 23, 29)
	}
	RENDERER.paint(canvas, box, spec)
