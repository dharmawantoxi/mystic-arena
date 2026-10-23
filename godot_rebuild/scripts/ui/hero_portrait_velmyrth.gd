extends RefCounted
## Native canvas portrait: Velmyrth — Boss/Assassin.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "assassin",
		"feature": "neutral",
		"variant": 5,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(72, 81, 92),
		"accent": Color8(142, 154, 158),
		"light": Color8(227, 231, 212),
		"skin": Color8(214, 183, 156),
		"top": Color8(60, 68, 78),
		"bottom": Color8(20, 24, 30)
	}
	RENDERER.paint(canvas, box, spec)
