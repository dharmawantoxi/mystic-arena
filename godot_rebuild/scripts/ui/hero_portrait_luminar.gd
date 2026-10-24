extends RefCounted
## Native canvas portrait: Luminar — Boss/Light Custodian.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "holy",
		"variant": 0,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(146, 114, 52),
		"accent": Color8(227, 188, 89),
		"light": Color8(255, 244, 190),
		"skin": Color8(126, 91, 82),
		"top": Color8(100, 80, 46),
		"bottom": Color8(35, 32, 31)
	}
	RENDERER.paint(canvas, box, spec)
