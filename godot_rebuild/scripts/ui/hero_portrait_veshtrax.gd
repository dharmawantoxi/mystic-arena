extends RefCounted
## Native canvas portrait: Veshtrax — Boss/Sapphire Executor.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "crystal",
		"variant": 1,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(79, 65, 129),
		"accent": Color8(151, 113, 206),
		"light": Color8(230, 220, 250),
		"skin": Color8(214, 183, 156),
		"top": Color8(59, 51, 99),
		"bottom": Color8(23, 23, 43)
	}
	RENDERER.paint(canvas, box, spec)
