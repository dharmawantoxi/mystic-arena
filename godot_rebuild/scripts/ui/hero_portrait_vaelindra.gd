extends RefCounted
## Native canvas portrait: Vaelindra — True Boss/Violet Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "arcane",
		"variant": 4,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(64, 54, 115),
		"accent": Color8(104, 185, 209),
		"light": Color8(224, 241, 228),
		"skin": Color8(207, 168, 142),
		"top": Color8(47, 42, 87),
		"bottom": Color8(21, 23, 42)
	}
	RENDERER.paint(canvas, box, spec)
