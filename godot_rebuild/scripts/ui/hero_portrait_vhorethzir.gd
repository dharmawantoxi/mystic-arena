extends RefCounted
## Native canvas portrait: Vhoreth'zir — True Boss/Venom Drake.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "venom",
		"variant": 0,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(77, 98, 53),
		"accent": Color8(146, 185, 69),
		"light": Color8(218, 238, 143),
		"skin": Color8(107, 128, 83),
		"top": Color8(58, 73, 44),
		"bottom": Color8(25, 31, 26)
	}
	RENDERER.paint(canvas, box, spec)
