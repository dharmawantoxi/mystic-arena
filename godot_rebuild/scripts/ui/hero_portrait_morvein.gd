extends RefCounted
## Native canvas portrait: Morvein — Boss/Phantom Lancer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "warrior",
		"feature": "neutral",
		"variant": 5,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(78, 87, 98),
		"accent": Color8(141, 153, 157),
		"light": Color8(227, 231, 212),
		"skin": Color8(126, 91, 82),
		"top": Color8(52, 60, 70),
		"bottom": Color8(21, 25, 31)
	}
	RENDERER.paint(canvas, box, spec)
