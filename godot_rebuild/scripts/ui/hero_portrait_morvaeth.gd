extends RefCounted
## Native canvas portrait: Morvaeth — Boss/Crimson Assassin.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "blood",
		"variant": 4,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(121, 39, 53),
		"accent": Color8(199, 51, 62),
		"light": Color8(255, 194, 162),
		"skin": Color8(190, 145, 124),
		"top": Color8(94, 40, 52),
		"bottom": Color8(26, 20, 29)
	}
	RENDERER.paint(canvas, box, spec)
