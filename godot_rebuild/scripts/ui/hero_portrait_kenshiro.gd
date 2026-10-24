extends RefCounted
## Native canvas portrait: Kenshiro — Boss/Ronin.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 5,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(72, 81, 92),
		"accent": Color8(149, 161, 165),
		"light": Color8(227, 231, 212),
		"skin": Color8(126, 91, 82),
		"top": Color8(57, 65, 75),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
