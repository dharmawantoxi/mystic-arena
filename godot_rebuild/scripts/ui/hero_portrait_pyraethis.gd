extends RefCounted
## Native canvas portrait: Pyraethis — True Boss/Firebird.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "fire",
		"variant": 0,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(144, 59, 48),
		"accent": Color8(245, 123, 54),
		"light": Color8(255, 221, 128),
		"skin": Color8(174, 89, 78),
		"top": Color8(100, 48, 41),
		"bottom": Color8(30, 23, 30)
	}
	RENDERER.paint(canvas, box, spec)
