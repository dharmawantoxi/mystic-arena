extends RefCounted
## Native canvas portrait: Kagetsuka — True Boss/Sharingan Warlord.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 2,
		"sigil": 3,
		"crowned": true,
		"horned": false,
		"primary": Color8(73, 82, 93),
		"accent": Color8(149, 161, 165),
		"light": Color8(227, 231, 212),
		"skin": Color8(181, 132, 116),
		"top": Color8(61, 69, 79),
		"bottom": Color8(25, 29, 35)
	}
	RENDERER.paint(canvas, box, spec)
