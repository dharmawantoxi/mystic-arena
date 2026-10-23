extends RefCounted
## Native canvas portrait: Vaelkorr — Boss/Thread Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "arcane",
		"variant": 5,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(71, 61, 122),
		"accent": Color8(103, 184, 208),
		"light": Color8(224, 241, 228),
		"skin": Color8(190, 145, 124),
		"top": Color8(53, 48, 93),
		"bottom": Color8(22, 24, 43)
	}
	RENDERER.paint(canvas, box, spec)
