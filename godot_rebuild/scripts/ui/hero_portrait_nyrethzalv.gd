extends RefCounted
## Native canvas portrait: Nyreth'zalvarin — True Boss/Shadow Empress.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "shadow",
		"variant": 2,
		"sigil": 3,
		"crowned": true,
		"horned": false,
		"primary": Color8(45, 46, 68),
		"accent": Color8(100, 94, 143),
		"light": Color8(196, 216, 222),
		"skin": Color8(135, 129, 153),
		"top": Color8(39, 40, 60),
		"bottom": Color8(18, 21, 31)
	}
	RENDERER.paint(canvas, box, spec)
