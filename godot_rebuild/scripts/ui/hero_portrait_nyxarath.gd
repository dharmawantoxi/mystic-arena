extends RefCounted
## Native canvas portrait: Nyxarath — True Boss/Shadow Fiend.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "shadow",
		"variant": 0,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(41, 42, 64),
		"accent": Color8(108, 102, 151),
		"light": Color8(196, 216, 222),
		"skin": Color8(133, 127, 151),
		"top": Color8(35, 36, 56),
		"bottom": Color8(16, 16, 26)
	}
	RENDERER.paint(canvas, box, spec)
