extends RefCounted
## Native canvas portrait: Sirakzan — Boss/Blade Duelist.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 4,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(77, 86, 97),
		"accent": Color8(142, 154, 158),
		"light": Color8(227, 231, 212),
		"skin": Color8(190, 145, 124),
		"top": Color8(53, 61, 71),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
