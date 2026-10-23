extends RefCounted
## Native canvas portrait: Ur'gharun — Boss/Feral Beast.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 1,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(75, 84, 95),
		"accent": Color8(137, 149, 153),
		"light": Color8(227, 231, 212),
		"skin": Color8(105, 114, 125),
		"top": Color8(61, 69, 79),
		"bottom": Color8(21, 25, 31)
	}
	RENDERER.paint(canvas, box, spec)
