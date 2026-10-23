extends RefCounted
## Native canvas portrait: Vokrahn — Boss/Chaos Knight.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 5,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(68, 77, 88),
		"accent": Color8(148, 160, 164),
		"light": Color8(227, 231, 212),
		"skin": Color8(190, 145, 124),
		"top": Color8(56, 64, 74),
		"bottom": Color8(21, 25, 31)
	}
	RENDERER.paint(canvas, box, spec)
