extends RefCounted
## Native canvas portrait: Vyraeth — Boss/Spectral Wraith.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "wraith",
		"feature": "shadow",
		"variant": 5,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(47, 48, 70),
		"accent": Color8(92, 86, 135),
		"light": Color8(196, 216, 222),
		"skin": Color8(133, 127, 151),
		"top": Color8(41, 42, 62),
		"bottom": Color8(16, 19, 29)
	}
	RENDERER.paint(canvas, box, spec)
