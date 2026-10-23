extends RefCounted
## Native canvas portrait: Kaerinya — True Boss/Fire Brawler.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "fire",
		"variant": 2,
		"sigil": 7,
		"crowned": false,
		"horned": false,
		"primary": Color8(143, 58, 47),
		"accent": Color8(240, 118, 49),
		"light": Color8(255, 221, 128),
		"skin": Color8(126, 91, 82),
		"top": Color8(104, 52, 45),
		"bottom": Color8(35, 28, 35)
	}
	RENDERER.paint(canvas, box, spec)
