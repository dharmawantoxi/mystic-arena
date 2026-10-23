extends RefCounted
## Native canvas portrait: Nazulmor — True Boss/Eldritch.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "void",
		"variant": 0,
		"sigil": 0,
		"crowned": false,
		"horned": true,
		"primary": Color8(62, 50, 93),
		"accent": Color8(145, 85, 187),
		"light": Color8(213, 196, 243),
		"skin": Color8(92, 80, 123),
		"top": Color8(38, 31, 65),
		"bottom": Color8(19, 21, 35)
	}
	RENDERER.paint(canvas, box, spec)
