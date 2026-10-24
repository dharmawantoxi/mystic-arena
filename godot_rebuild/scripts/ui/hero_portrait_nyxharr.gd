extends RefCounted
## Native canvas portrait: Nyxharr — True Boss/Ghost Rider.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "rider",
		"feature": "shadow",
		"variant": 0,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(51, 52, 74),
		"accent": Color8(97, 91, 140),
		"light": Color8(196, 216, 222),
		"skin": Color8(145, 139, 163),
		"top": Color8(41, 42, 62),
		"bottom": Color8(16, 19, 29)
	}
	RENDERER.paint(canvas, box, spec)
