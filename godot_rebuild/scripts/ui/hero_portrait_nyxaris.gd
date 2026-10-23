extends RefCounted
## Native canvas portrait: Nyxaris — True Boss/Marksman.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "archer",
		"feature": "neutral",
		"variant": 1,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(81, 90, 101),
		"accent": Color8(150, 162, 166),
		"light": Color8(227, 231, 212),
		"skin": Color8(214, 183, 156),
		"top": Color8(52, 60, 70),
		"bottom": Color8(27, 31, 37)
	}
	RENDERER.paint(canvas, box, spec)
