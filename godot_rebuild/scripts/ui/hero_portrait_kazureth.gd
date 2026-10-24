extends RefCounted
## Native canvas portrait: Kazureth — Boss/Thunder Samurai.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "storm",
		"variant": 2,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(48, 75, 119),
		"accent": Color8(87, 172, 212),
		"light": Color8(231, 241, 174),
		"skin": Color8(126, 91, 82),
		"top": Color8(47, 69, 109),
		"bottom": Color8(16, 21, 38)
	}
	RENDERER.paint(canvas, box, spec)
