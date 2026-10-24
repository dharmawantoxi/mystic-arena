extends RefCounted
## Native canvas portrait: Zorashi — Boss/Serpent Sage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "serpent",
		"feature": "neutral",
		"variant": 5,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(68, 77, 88),
		"accent": Color8(152, 164, 168),
		"light": Color8(227, 231, 212),
		"skin": Color8(98, 107, 118),
		"top": Color8(52, 60, 70),
		"bottom": Color8(19, 23, 29)
	}
	RENDERER.paint(canvas, box, spec)
