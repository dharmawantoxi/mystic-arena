extends RefCounted
## Native canvas portrait: Yomigetsu — True Boss/Moon Demon Swordsman.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "moon",
		"variant": 2,
		"sigil": 2,
		"crowned": false,
		"horned": true,
		"primary": Color8(61, 60, 105),
		"accent": Color8(136, 132, 196),
		"light": Color8(229, 230, 246),
		"skin": Color8(207, 168, 142),
		"top": Color8(49, 48, 85),
		"bottom": Color8(23, 25, 42)
	}
	RENDERER.paint(canvas, box, spec)
