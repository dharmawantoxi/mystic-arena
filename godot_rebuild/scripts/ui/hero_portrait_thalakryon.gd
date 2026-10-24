extends RefCounted
## Native canvas portrait: Thalakryon — True Boss/Mermidon.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "water",
		"variant": 4,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(39, 97, 113),
		"accent": Color8(79, 183, 186),
		"light": Color8(199, 246, 224),
		"skin": Color8(207, 168, 142),
		"top": Color8(37, 79, 96),
		"bottom": Color8(19, 28, 39)
	}
	RENDERER.paint(canvas, box, spec)
