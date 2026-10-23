extends RefCounted
## Native canvas portrait: Zyvareth — True Boss/Crystal Storm Beast.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "beast",
		"feature": "crystal",
		"variant": 4,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(91, 77, 141),
		"accent": Color8(152, 114, 207),
		"light": Color8(230, 220, 250),
		"skin": Color8(121, 107, 171),
		"top": Color8(62, 54, 102),
		"bottom": Color8(19, 19, 39)
	}
	RENDERER.paint(canvas, box, spec)
