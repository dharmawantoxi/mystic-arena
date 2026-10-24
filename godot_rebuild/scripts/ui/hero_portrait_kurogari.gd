extends RefCounted
## Native canvas portrait: Kurogari — Boss/Shadow Ninja Reaper.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "reaper",
		"feature": "shadow",
		"variant": 3,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(53, 54, 76),
		"accent": Color8(108, 102, 151),
		"light": Color8(196, 216, 222),
		"skin": Color8(131, 125, 149),
		"top": Color8(34, 35, 55),
		"bottom": Color8(16, 18, 28)
	}
	RENDERER.paint(canvas, box, spec)
