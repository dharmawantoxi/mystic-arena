extends RefCounted
## Native canvas portrait: Vhyssarion — Boss/Venomancer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "venom",
		"variant": 4,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(74, 95, 50),
		"accent": Color8(142, 181, 65),
		"light": Color8(218, 238, 143),
		"skin": Color8(104, 125, 80),
		"top": Color8(54, 69, 40),
		"bottom": Color8(24, 30, 25)
	}
	RENDERER.paint(canvas, box, spec)
