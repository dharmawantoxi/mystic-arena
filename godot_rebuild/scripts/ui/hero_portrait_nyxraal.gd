extends RefCounted
## Native canvas portrait: Nyxraal — Boss/Abyssal Prince.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "void",
		"variant": 5,
		"sigil": 6,
		"crowned": true,
		"horned": false,
		"primary": Color8(56, 44, 87),
		"accent": Color8(144, 84, 186),
		"light": Color8(213, 196, 243),
		"skin": Color8(132, 126, 150),
		"top": Color8(45, 38, 72),
		"bottom": Color8(18, 20, 34)
	}
	RENDERER.paint(canvas, box, spec)
