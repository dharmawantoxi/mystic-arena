extends RefCounted
## Native canvas portrait: Nyxariel — Boss/Abyssal Trickster.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "void",
		"variant": 5,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(52, 40, 83),
		"accent": Color8(145, 85, 187),
		"light": Color8(213, 196, 243),
		"skin": Color8(144, 138, 162),
		"top": Color8(44, 37, 71),
		"bottom": Color8(16, 16, 30)
	}
	RENDERER.paint(canvas, box, spec)
