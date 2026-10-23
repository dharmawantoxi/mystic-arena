extends RefCounted
## Native canvas portrait: Xy'rael — Boss/Cyan Assassin.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "neutral",
		"variant": 1,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(69, 78, 89),
		"accent": Color8(144, 156, 160),
		"light": Color8(227, 231, 212),
		"skin": Color8(181, 132, 116),
		"top": Color8(53, 61, 71),
		"bottom": Color8(19, 23, 29)
	}
	RENDERER.paint(canvas, box, spec)
