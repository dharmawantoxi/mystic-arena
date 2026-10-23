extends RefCounted
## Native canvas portrait: Vaerith — Boss/Broodmother.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "venom",
		"variant": 3,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(79, 100, 55),
		"accent": Color8(143, 182, 66),
		"light": Color8(218, 238, 143),
		"skin": Color8(109, 130, 85),
		"top": Color8(53, 68, 39),
		"bottom": Color8(24, 30, 25)
	}
	RENDERER.paint(canvas, box, spec)
