extends RefCounted
## Native canvas portrait: Krobellus — Boss/Spirit Prophet.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "neutral",
		"variant": 2,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(66, 75, 86),
		"accent": Color8(144, 156, 160),
		"light": Color8(227, 231, 212),
		"skin": Color8(153, 109, 92),
		"top": Color8(59, 67, 77),
		"bottom": Color8(19, 23, 29)
	}
	RENDERER.paint(canvas, box, spec)
