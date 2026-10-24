extends RefCounted
## Native canvas portrait: Nyxareva — Boss/Fallen Queen.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "neutral",
		"variant": 0,
		"sigil": 7,
		"crowned": true,
		"horned": false,
		"primary": Color8(71, 80, 91),
		"accent": Color8(150, 162, 166),
		"light": Color8(227, 231, 212),
		"skin": Color8(214, 183, 156),
		"top": Color8(57, 65, 75),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
