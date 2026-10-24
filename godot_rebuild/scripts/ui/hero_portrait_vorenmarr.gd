extends RefCounted
## Native canvas portrait: Vorenmarr — Boss/Warlock.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "arcane",
		"variant": 3,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(61, 51, 112),
		"accent": Color8(97, 178, 202),
		"light": Color8(224, 241, 228),
		"skin": Color8(207, 168, 142),
		"top": Color8(47, 42, 87),
		"bottom": Color8(24, 26, 45)
	}
	RENDERER.paint(canvas, box, spec)
