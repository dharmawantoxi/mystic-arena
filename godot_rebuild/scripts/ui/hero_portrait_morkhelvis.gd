extends RefCounted
## Native canvas portrait: Mor'khelvis — Boss/Necrogargoyle.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 1,
		"sigil": 4,
		"crowned": false,
		"horned": true,
		"primary": Color8(76, 85, 96),
		"accent": Color8(139, 151, 155),
		"light": Color8(227, 231, 212),
		"skin": Color8(106, 115, 126),
		"top": Color8(53, 61, 71),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
