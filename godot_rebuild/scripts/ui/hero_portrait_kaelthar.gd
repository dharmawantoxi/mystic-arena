extends RefCounted
## Native canvas portrait: Kaelthar — Boss/Storm Martial.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "fighter",
		"feature": "storm",
		"variant": 3,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(47, 74, 118),
		"accent": Color8(85, 170, 210),
		"light": Color8(231, 241, 174),
		"skin": Color8(207, 168, 142),
		"top": Color8(47, 69, 109),
		"bottom": Color8(23, 28, 45)
	}
	RENDERER.paint(canvas, box, spec)
