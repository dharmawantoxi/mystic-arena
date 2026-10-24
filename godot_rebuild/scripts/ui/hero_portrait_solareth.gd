extends RefCounted
## Native canvas portrait: Solareth — True Boss/Solar Warrior.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "fire",
		"variant": 2,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(136, 51, 40),
		"accent": Color8(243, 121, 52),
		"light": Color8(255, 221, 128),
		"skin": Color8(190, 145, 124),
		"top": Color8(95, 43, 36),
		"bottom": Color8(33, 26, 33)
	}
	RENDERER.paint(canvas, box, spec)
