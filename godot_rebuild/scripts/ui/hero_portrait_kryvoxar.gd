extends RefCounted
## Native canvas portrait: Kryvoxar — Boss/Crystal Wraith.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "wraith",
		"feature": "crystal",
		"variant": 1,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(76, 62, 126),
		"accent": Color8(155, 117, 210),
		"light": Color8(230, 220, 250),
		"skin": Color8(134, 128, 152),
		"top": Color8(67, 59, 107),
		"bottom": Color8(23, 23, 43)
	}
	RENDERER.paint(canvas, box, spec)
