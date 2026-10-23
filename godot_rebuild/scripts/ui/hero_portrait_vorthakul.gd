extends RefCounted
## Native canvas portrait: Vor'thakul — Boss/Abyss Terror.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "void",
		"variant": 1,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(61, 49, 92),
		"accent": Color8(139, 79, 181),
		"light": Color8(213, 196, 243),
		"skin": Color8(91, 79, 122),
		"top": Color8(40, 33, 67),
		"bottom": Color8(21, 23, 37)
	}
	RENDERER.paint(canvas, box, spec)
