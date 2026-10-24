extends RefCounted
## Native canvas portrait: Vhaerith — Boss/Magic.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "neutral",
		"variant": 3,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(73, 82, 93),
		"accent": Color8(147, 159, 163),
		"light": Color8(227, 231, 212),
		"skin": Color8(153, 109, 92),
		"top": Color8(56, 64, 74),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
