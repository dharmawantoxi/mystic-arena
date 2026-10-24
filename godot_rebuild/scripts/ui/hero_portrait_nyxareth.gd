extends RefCounted
## Native canvas portrait: Nyxareth — True Boss/Cosmic Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "void",
		"variant": 4,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(54, 42, 85),
		"accent": Color8(148, 88, 190),
		"light": Color8(213, 196, 243),
		"skin": Color8(145, 139, 163),
		"top": Color8(39, 32, 66),
		"bottom": Color8(20, 22, 36)
	}
	RENDERER.paint(canvas, box, spec)
