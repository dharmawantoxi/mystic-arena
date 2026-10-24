extends RefCounted
## Native canvas portrait: Korokai — Boss/Mirror Shinobi.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "neutral",
		"variant": 2,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(72, 81, 92),
		"accent": Color8(140, 152, 156),
		"light": Color8(227, 231, 212),
		"skin": Color8(207, 168, 142),
		"top": Color8(61, 69, 79),
		"bottom": Color8(25, 29, 35)
	}
	RENDERER.paint(canvas, box, spec)
