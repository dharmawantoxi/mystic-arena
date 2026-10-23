extends RefCounted
## Native canvas portrait: Malzeroth — True Boss/Hex Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "arcane",
		"variant": 5,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(62, 52, 113),
		"accent": Color8(104, 185, 209),
		"light": Color8(224, 241, 228),
		"skin": Color8(181, 132, 116),
		"top": Color8(54, 49, 94),
		"bottom": Color8(21, 23, 42)
	}
	RENDERER.paint(canvas, box, spec)
