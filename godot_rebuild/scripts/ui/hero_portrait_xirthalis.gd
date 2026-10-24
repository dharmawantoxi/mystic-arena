extends RefCounted
## Native canvas portrait: Xir'thalis — Boss/Weaver.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 3,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(71, 80, 91),
		"accent": Color8(141, 153, 157),
		"light": Color8(227, 231, 212),
		"skin": Color8(101, 110, 121),
		"top": Color8(58, 66, 76),
		"bottom": Color8(19, 23, 29)
	}
	RENDERER.paint(canvas, box, spec)
