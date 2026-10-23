extends RefCounted
## Native canvas portrait: Nyzrak — Boss/Wyvern Rider.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "rider",
		"feature": "neutral",
		"variant": 2,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(69, 78, 89),
		"accent": Color8(139, 151, 155),
		"light": Color8(227, 231, 212),
		"skin": Color8(181, 132, 116),
		"top": Color8(57, 65, 75),
		"bottom": Color8(23, 27, 33)
	}
	RENDERER.paint(canvas, box, spec)
