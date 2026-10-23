extends RefCounted
## Native canvas portrait: Thorvak — Boss/Grovewarden Treant.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "treant",
		"feature": "nature",
		"variant": 3,
		"sigil": 3,
		"crowned": false,
		"horned": false,
		"primary": Color8(62, 100, 60),
		"accent": Color8(110, 151, 67),
		"light": Color8(215, 230, 151),
		"skin": Color8(103, 94, 67),
		"top": Color8(57, 82, 52),
		"bottom": Color8(18, 27, 22)
	}
	RENDERER.paint(canvas, box, spec)
