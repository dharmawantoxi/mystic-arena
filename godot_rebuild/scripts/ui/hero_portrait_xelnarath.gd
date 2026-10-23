extends RefCounted
## Native canvas portrait: Xel'Narath — True Boss/Void Sovereign.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "void",
		"variant": 0,
		"sigil": 7,
		"crowned": true,
		"horned": false,
		"primary": Color8(48, 36, 79),
		"accent": Color8(149, 89, 191),
		"light": Color8(213, 196, 243),
		"skin": Color8(135, 129, 153),
		"top": Color8(47, 40, 74),
		"bottom": Color8(21, 23, 37)
	}
	RENDERER.paint(canvas, box, spec)
