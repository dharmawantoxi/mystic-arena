extends RefCounted
## Native canvas portrait: Varkul — Boss/Frost Sorcerer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "frost",
		"variant": 1,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(66, 107, 142),
		"accent": Color8(103, 194, 216),
		"light": Color8(218, 250, 241),
		"skin": Color8(214, 183, 156),
		"top": Color8(45, 80, 108),
		"bottom": Color8(22, 30, 45)
	}
	RENDERER.paint(canvas, box, spec)
