extends RefCounted
## Native canvas portrait: Krognarr — Boss/Stone Golem.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "golem",
		"feature": "neutral",
		"variant": 4,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(68, 77, 88),
		"accent": Color8(143, 155, 159),
		"light": Color8(227, 231, 212),
		"skin": Color8(117, 121, 106),
		"top": Color8(61, 69, 79),
		"bottom": Color8(22, 26, 32)
	}
	RENDERER.paint(canvas, box, spec)
