extends RefCounted
## Native canvas portrait: Solara — Boss/Dawnforged Sentinel.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "holy",
		"variant": 4,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(149, 117, 55),
		"accent": Color8(219, 180, 81),
		"light": Color8(255, 244, 190),
		"skin": Color8(153, 109, 92),
		"top": Color8(107, 87, 53),
		"bottom": Color8(35, 32, 31)
	}
	RENDERER.paint(canvas, box, spec)
