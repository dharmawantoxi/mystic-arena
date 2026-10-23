extends RefCounted
## Native canvas portrait: Sanguiveth — Boss/Blood Reaper.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "reaper",
		"feature": "blood",
		"variant": 5,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(126, 44, 58),
		"accent": Color8(208, 60, 71),
		"light": Color8(255, 194, 162),
		"skin": Color8(146, 140, 164),
		"top": Color8(96, 42, 54),
		"bottom": Color8(32, 26, 35)
	}
	RENDERER.paint(canvas, box, spec)
