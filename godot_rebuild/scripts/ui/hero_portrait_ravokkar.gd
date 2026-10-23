extends RefCounted
## Native canvas portrait: Ravokkar — True Boss/Outlaw Gunslinger.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "gunner",
		"feature": "neutral",
		"variant": 1,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(80, 89, 100),
		"accent": Color8(138, 150, 154),
		"light": Color8(227, 231, 212),
		"skin": Color8(126, 91, 82),
		"top": Color8(54, 62, 72),
		"bottom": Color8(19, 23, 29)
	}
	RENDERER.paint(canvas, box, spec)
