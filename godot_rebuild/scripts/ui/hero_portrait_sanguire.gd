extends RefCounted
## Native canvas portrait: Sanguire Voxthal — Boss/Blood Mage.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "blood",
		"variant": 1,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(123, 41, 55),
		"accent": Color8(201, 53, 64),
		"light": Color8(255, 194, 162),
		"skin": Color8(214, 183, 156),
		"top": Color8(90, 36, 48),
		"bottom": Color8(26, 20, 29)
	}
	RENDERER.paint(canvas, box, spec)
