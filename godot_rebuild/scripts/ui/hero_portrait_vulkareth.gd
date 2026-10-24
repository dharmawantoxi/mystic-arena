extends RefCounted
## Native canvas portrait: Vulkareth — Boss/Ember Titan.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "golem",
		"feature": "fire",
		"variant": 0,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(142, 57, 46),
		"accent": Color8(244, 122, 53),
		"light": Color8(255, 221, 128),
		"skin": Color8(111, 115, 100),
		"top": Color8(98, 46, 39),
		"bottom": Color8(30, 23, 30)
	}
	RENDERER.paint(canvas, box, spec)
