extends RefCounted
## Native canvas portrait: Thornvaegrim — Boss/Elderwood Treant.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "treant",
		"feature": "nature",
		"variant": 3,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(65, 103, 63),
		"accent": Color8(115, 156, 72),
		"light": Color8(215, 230, 151),
		"skin": Color8(116, 107, 80),
		"top": Color8(56, 81, 51),
		"bottom": Color8(23, 32, 27)
	}
	RENDERER.paint(canvas, box, spec)
