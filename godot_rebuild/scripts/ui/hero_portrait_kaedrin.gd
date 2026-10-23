extends RefCounted
## Native canvas portrait: Kaedrin — Boss/Moonfang Bladebearer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "moon",
		"variant": 2,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(55, 54, 99),
		"accent": Color8(141, 137, 201),
		"light": Color8(229, 230, 246),
		"skin": Color8(181, 132, 116),
		"top": Color8(54, 53, 90),
		"bottom": Color8(17, 19, 36)
	}
	RENDERER.paint(canvas, box, spec)
