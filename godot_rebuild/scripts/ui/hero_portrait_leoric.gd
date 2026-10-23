extends RefCounted
## Native canvas portrait: Leoric — Boss/Lionheart Guardian.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "neutral",
		"variant": 2,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(71, 80, 91),
		"accent": Color8(152, 164, 168),
		"light": Color8(227, 231, 212),
		"skin": Color8(101, 110, 121),
		"top": Color8(59, 67, 77),
		"bottom": Color8(27, 31, 37)
	}
	RENDERER.paint(canvas, box, spec)
