extends RefCounted
## Native canvas portrait: Rakzhan — Boss/Emberfist Fighter.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "fire",
		"variant": 4,
		"sigil": 1,
		"crowned": false,
		"horned": false,
		"primary": Color8(145, 60, 49),
		"accent": Color8(230, 108, 39),
		"light": Color8(255, 221, 128),
		"skin": Color8(214, 183, 156),
		"top": Color8(96, 44, 37),
		"bottom": Color8(28, 21, 28)
	}
	RENDERER.paint(canvas, box, spec)
