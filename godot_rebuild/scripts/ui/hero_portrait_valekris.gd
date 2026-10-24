extends RefCounted
## Native canvas portrait: Valekris — Boss/Cyan Wraith.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "wraith",
		"feature": "shadow",
		"variant": 5,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(50, 51, 73),
		"accent": Color8(94, 88, 137),
		"light": Color8(196, 216, 222),
		"skin": Color8(145, 139, 163),
		"top": Color8(32, 33, 53),
		"bottom": Color8(18, 21, 31)
	}
	RENDERER.paint(canvas, box, spec)
