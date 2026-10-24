extends RefCounted
## Native canvas portrait: Xael'moran — True Boss/Elemental Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "elemental",
		"feature": "arcane",
		"variant": 4,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(73, 63, 124),
		"accent": Color8(92, 173, 197),
		"light": Color8(224, 241, 228),
		"skin": Color8(153, 109, 92),
		"top": Color8(52, 47, 92),
		"bottom": Color8(17, 19, 38)
	}
	RENDERER.paint(canvas, box, spec)
