extends RefCounted
## Native canvas portrait: Kaizoku Raijin — Boss/Lightning Pirate.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "storm",
		"variant": 0,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(54, 81, 125),
		"accent": Color8(91, 176, 216),
		"light": Color8(231, 241, 174),
		"skin": Color8(126, 91, 82),
		"top": Color8(50, 72, 112),
		"bottom": Color8(21, 26, 43)
	}
	RENDERER.paint(canvas, box, spec)
