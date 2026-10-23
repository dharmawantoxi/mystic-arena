extends RefCounted
## Native canvas portrait: Obanai — Boss/Serpent Swordsman.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "serpent",
		"feature": "neutral",
		"variant": 0,
		"sigil": 0,
		"crowned": false,
		"horned": false,
		"primary": Color8(79, 88, 99),
		"accent": Color8(153, 165, 169),
		"light": Color8(227, 231, 212),
		"skin": Color8(109, 118, 129),
		"top": Color8(54, 62, 72),
		"bottom": Color8(19, 23, 29)
	}
	RENDERER.paint(canvas, box, spec)
