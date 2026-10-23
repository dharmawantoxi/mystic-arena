extends RefCounted
## Native canvas portrait: Morvaeth — Boss/Mirrorborn Marauder.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 4,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(81, 90, 101),
		"accent": Color8(145, 157, 161),
		"light": Color8(227, 231, 212),
		"skin": Color8(214, 183, 156),
		"top": Color8(55, 63, 73),
		"bottom": Color8(21, 25, 31)
	}
	RENDERER.paint(canvas, box, spec)
