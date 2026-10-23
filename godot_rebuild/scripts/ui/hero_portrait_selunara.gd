extends RefCounted
## Native canvas portrait: Selunara — Boss/Moon Archer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "archer",
		"feature": "moon",
		"variant": 0,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(63, 62, 107),
		"accent": Color8(139, 135, 199),
		"light": Color8(229, 230, 246),
		"skin": Color8(181, 132, 116),
		"top": Color8(52, 51, 88),
		"bottom": Color8(24, 26, 43)
	}
	RENDERER.paint(canvas, box, spec)
