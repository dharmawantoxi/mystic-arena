extends RefCounted
## Native canvas portrait: Kaineroth — True Boss/Crimson Prodigy.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "blood",
		"variant": 4,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(121, 39, 53),
		"accent": Color8(206, 58, 69),
		"light": Color8(255, 194, 162),
		"skin": Color8(190, 145, 124),
		"top": Color8(86, 32, 44),
		"bottom": Color8(25, 19, 28)
	}
	RENDERER.paint(canvas, box, spec)
