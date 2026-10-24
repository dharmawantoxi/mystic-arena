extends RefCounted
## Native canvas portrait: Thalgryn — Boss/Water Elemental.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "elemental",
		"feature": "water",
		"variant": 3,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(39, 97, 113),
		"accent": Color8(73, 177, 180),
		"light": Color8(199, 246, 224),
		"skin": Color8(190, 145, 124),
		"top": Color8(41, 83, 100),
		"bottom": Color8(17, 26, 37)
	}
	RENDERER.paint(canvas, box, spec)
