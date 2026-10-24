extends RefCounted
## Native canvas portrait: Thal'ryndel — True Boss/Storm Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "storm",
		"variant": 4,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(61, 88, 132),
		"accent": Color8(87, 172, 212),
		"light": Color8(231, 241, 174),
		"skin": Color8(207, 168, 142),
		"top": Color8(51, 73, 113),
		"bottom": Color8(23, 28, 45)
	}
	RENDERER.paint(canvas, box, spec)
