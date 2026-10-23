extends RefCounted
## Native canvas portrait: Kyumirra — Boss/Nine-Tailed Fox.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 4,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(68, 77, 88),
		"accent": Color8(153, 165, 169),
		"light": Color8(227, 231, 212),
		"skin": Color8(98, 107, 118),
		"top": Color8(56, 64, 74),
		"bottom": Color8(22, 26, 32)
	}
	RENDERER.paint(canvas, box, spec)
