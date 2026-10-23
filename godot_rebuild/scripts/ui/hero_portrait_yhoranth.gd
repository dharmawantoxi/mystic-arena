extends RefCounted
## Native canvas portrait: Yh'oranth — Boss/Unforgiven Wraith.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "wraith",
		"feature": "shadow",
		"variant": 1,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(55, 56, 78),
		"accent": Color8(104, 98, 147),
		"light": Color8(196, 216, 222),
		"skin": Color8(134, 128, 152),
		"top": Color8(36, 37, 57),
		"bottom": Color8(18, 21, 31)
	}
	RENDERER.paint(canvas, box, spec)
