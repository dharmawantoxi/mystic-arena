extends RefCounted
## Native canvas portrait: Khazan — Boss/Executioner.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 0,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(66, 75, 86),
		"accent": Color8(149, 161, 165),
		"light": Color8(227, 231, 212),
		"skin": Color8(190, 145, 124),
		"top": Color8(57, 65, 75),
		"bottom": Color8(25, 29, 35)
	}
	RENDERER.paint(canvas, box, spec)
