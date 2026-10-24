extends RefCounted
## Native canvas portrait: Zorothrax — Boss/Rune Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "arcane",
		"variant": 1,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(71, 61, 122),
		"accent": Color8(103, 184, 208),
		"light": Color8(224, 241, 228),
		"skin": Color8(181, 132, 116),
		"top": Color8(55, 50, 95),
		"bottom": Color8(25, 27, 46)
	}
	RENDERER.paint(canvas, box, spec)
