extends RefCounted
## Native canvas portrait: Morvath — Boss/Strength.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "neutral",
		"variant": 4,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(67, 76, 87),
		"accent": Color8(137, 149, 153),
		"light": Color8(227, 231, 212),
		"skin": Color8(190, 145, 124),
		"top": Color8(54, 62, 72),
		"bottom": Color8(26, 30, 36)
	}
	RENDERER.paint(canvas, box, spec)
