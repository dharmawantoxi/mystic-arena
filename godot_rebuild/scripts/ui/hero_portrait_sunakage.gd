extends RefCounted
## Native canvas portrait: Sunakage — True Boss/Sand Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "sand",
		"variant": 0,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(134, 101, 63),
		"accent": Color8(199, 160, 90),
		"light": Color8(249, 224, 165),
		"skin": Color8(214, 183, 156),
		"top": Color8(91, 69, 47),
		"bottom": Color8(35, 31, 30)
	}
	RENDERER.paint(canvas, box, spec)
