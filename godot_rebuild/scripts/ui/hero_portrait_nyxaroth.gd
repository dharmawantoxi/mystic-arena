extends RefCounted
## Native canvas portrait: Nyxaroth — Boss/Void-Starweaver.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "void",
		"variant": 2,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(59, 47, 90),
		"accent": Color8(147, 87, 189),
		"light": Color8(213, 196, 243),
		"skin": Color8(142, 136, 160),
		"top": Color8(38, 31, 65),
		"bottom": Color8(18, 20, 34)
	}
	RENDERER.paint(canvas, box, spec)
