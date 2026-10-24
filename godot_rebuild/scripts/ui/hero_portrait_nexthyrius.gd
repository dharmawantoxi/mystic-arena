extends RefCounted
## Native canvas portrait: Nexthyrius — True Boss/Spectral Chain Warden.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "wraith",
		"feature": "shadow",
		"variant": 5,
		"sigil": 2,
		"crowned": false,
		"horned": false,
		"primary": Color8(50, 51, 73),
		"accent": Color8(101, 95, 144),
		"light": Color8(196, 216, 222),
		"skin": Color8(131, 125, 149),
		"top": Color8(40, 41, 61),
		"bottom": Color8(17, 20, 30)
	}
	RENDERER.paint(canvas, box, spec)
