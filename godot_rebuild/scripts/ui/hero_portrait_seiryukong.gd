extends RefCounted
## Native canvas portrait: Seiryukong — True Boss/Celestial Simian.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "holy",
		"variant": 5,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(151, 119, 57),
		"accent": Color8(226, 187, 88),
		"light": Color8(255, 244, 190),
		"skin": Color8(181, 149, 87),
		"top": Color8(103, 83, 49),
		"bottom": Color8(34, 31, 30)
	}
	RENDERER.paint(canvas, box, spec)
