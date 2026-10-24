extends RefCounted
## Native canvas portrait: Karzhul — Boss/Werewolf.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 2,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(70, 79, 90),
		"accent": Color8(139, 151, 155),
		"light": Color8(227, 231, 212),
		"skin": Color8(100, 109, 120),
		"top": Color8(59, 67, 77),
		"bottom": Color8(19, 23, 29)
	}
	RENDERER.paint(canvas, box, spec)
