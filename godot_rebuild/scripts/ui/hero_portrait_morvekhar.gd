extends RefCounted
## Native canvas portrait: Morvekhar — Boss/Iron Juggernaut.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "golem",
		"feature": "neutral",
		"variant": 5,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(67, 76, 87),
		"accent": Color8(143, 155, 159),
		"light": Color8(227, 231, 212),
		"skin": Color8(105, 109, 94),
		"top": Color8(56, 64, 74),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
