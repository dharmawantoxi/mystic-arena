extends RefCounted
## Native canvas portrait: Xaerissa — Boss/Crimson Weaver.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "blood",
		"variant": 0,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(128, 46, 60),
		"accent": Color8(199, 51, 62),
		"light": Color8(255, 194, 162),
		"skin": Color8(181, 132, 116),
		"top": Color8(92, 38, 50),
		"bottom": Color8(27, 21, 30)
	}
	RENDERER.paint(canvas, box, spec)
