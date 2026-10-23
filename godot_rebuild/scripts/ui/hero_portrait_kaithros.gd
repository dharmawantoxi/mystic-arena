extends RefCounted
## Native canvas portrait: Kaithros — True Boss/Flame Swordsman.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "fire",
		"variant": 1,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(138, 53, 42),
		"accent": Color8(235, 113, 44),
		"light": Color8(255, 221, 128),
		"skin": Color8(181, 132, 116),
		"top": Color8(99, 47, 40),
		"bottom": Color8(32, 25, 32)
	}
	RENDERER.paint(canvas, box, spec)
