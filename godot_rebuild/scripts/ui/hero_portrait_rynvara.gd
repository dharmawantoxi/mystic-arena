extends RefCounted
## Native canvas portrait: Rynvara — Boss/Primal Beast.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 4,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(66, 75, 86),
		"accent": Color8(151, 163, 167),
		"light": Color8(227, 231, 212),
		"skin": Color8(96, 105, 116),
		"top": Color8(57, 65, 75),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
