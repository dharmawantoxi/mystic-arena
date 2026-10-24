extends RefCounted
## Native canvas portrait: Tsukiyora — True Boss/Moon Goddess.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "moon",
		"variant": 5,
		"sigil": 7,
		"crowned": true,
		"horned": false,
		"primary": Color8(53, 52, 97),
		"accent": Color8(126, 122, 186),
		"light": Color8(229, 230, 246),
		"skin": Color8(126, 91, 82),
		"top": Color8(53, 52, 89),
		"bottom": Color8(17, 19, 36)
	}
	RENDERER.paint(canvas, box, spec)
