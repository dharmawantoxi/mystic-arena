extends RefCounted
## Native canvas portrait: Malzareth — Boss/Shadow Demon.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "shadow",
		"variant": 0,
		"sigil": 4,
		"crowned": false,
		"horned": true,
		"primary": Color8(51, 52, 74),
		"accent": Color8(104, 98, 147),
		"light": Color8(196, 216, 222),
		"skin": Color8(138, 132, 156),
		"top": Color8(40, 41, 61),
		"bottom": Color8(17, 20, 30)
	}
	RENDERER.paint(canvas, box, spec)
