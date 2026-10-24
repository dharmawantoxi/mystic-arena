extends RefCounted
## Native canvas portrait: Zarethyr — True Boss/Cosmic Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "void",
		"variant": 4,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(61, 49, 92),
		"accent": Color8(136, 76, 178),
		"light": Color8(213, 196, 243),
		"skin": Color8(132, 126, 150),
		"top": Color8(41, 34, 68),
		"bottom": Color8(16, 16, 29)
	}
	RENDERER.paint(canvas, box, spec)
