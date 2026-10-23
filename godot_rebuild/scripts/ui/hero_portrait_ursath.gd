extends RefCounted
## Native canvas portrait: Ursath — Boss/Wildcaller.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "nature",
		"variant": 4,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(71, 109, 69),
		"accent": Color8(118, 159, 75),
		"light": Color8(215, 230, 151),
		"skin": Color8(190, 145, 124),
		"top": Color8(55, 80, 50),
		"bottom": Color8(26, 35, 30)
	}
	RENDERER.paint(canvas, box, spec)
