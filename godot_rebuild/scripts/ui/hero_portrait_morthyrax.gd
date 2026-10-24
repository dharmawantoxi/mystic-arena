extends RefCounted
## Native canvas portrait: Morthyrax — Boss/Decay Prophet.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "venom",
		"variant": 5,
		"sigil": 4,
		"crowned": false,
		"horned": false,
		"primary": Color8(71, 92, 47),
		"accent": Color8(137, 176, 60),
		"light": Color8(218, 238, 143),
		"skin": Color8(181, 132, 116),
		"top": Color8(62, 77, 48),
		"bottom": Color8(20, 26, 21)
	}
	RENDERER.paint(canvas, box, spec)
