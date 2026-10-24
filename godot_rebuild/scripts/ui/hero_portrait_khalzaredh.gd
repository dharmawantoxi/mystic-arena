extends RefCounted
## Native canvas portrait: Khal'zaredh — Boss/Sandborn Prince.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "sand",
		"variant": 3,
		"sigil": 2,
		"crowned": true,
		"horned": false,
		"primary": Color8(126, 93, 55),
		"accent": Color8(209, 170, 100),
		"light": Color8(249, 224, 165),
		"skin": Color8(153, 109, 92),
		"top": Color8(96, 74, 52),
		"bottom": Color8(33, 29, 28)
	}
	RENDERER.paint(canvas, box, spec)
