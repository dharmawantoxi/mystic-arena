extends RefCounted
## Native canvas portrait: Lyrienne — Boss/Twilight Chorister.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "moon",
		"variant": 1,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(68, 67, 112),
		"accent": Color8(134, 130, 194),
		"light": Color8(229, 230, 246),
		"skin": Color8(207, 168, 142),
		"top": Color8(46, 45, 82),
		"bottom": Color8(23, 25, 42)
	}
	RENDERER.paint(canvas, box, spec)
