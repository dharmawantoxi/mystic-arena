extends RefCounted
## Native canvas portrait: Lyssarethys — True Boss/Magenta Soul Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "shadow",
		"variant": 5,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(44, 45, 67),
		"accent": Color8(105, 99, 148),
		"light": Color8(196, 216, 222),
		"skin": Color8(139, 133, 157),
		"top": Color8(32, 33, 53),
		"bottom": Color8(19, 22, 32)
	}
	RENDERER.paint(canvas, box, spec)
