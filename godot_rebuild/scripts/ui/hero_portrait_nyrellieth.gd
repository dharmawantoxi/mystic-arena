extends RefCounted
## Native canvas portrait: Nyrellieth — True Boss/Frost Archer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "archer",
		"feature": "frost",
		"variant": 1,
		"sigil": 5,
		"crowned": false,
		"horned": false,
		"primary": Color8(57, 98, 133),
		"accent": Color8(107, 198, 220),
		"light": Color8(218, 250, 241),
		"skin": Color8(214, 183, 156),
		"top": Color8(50, 85, 113),
		"bottom": Color8(18, 26, 41)
	}
	RENDERER.paint(canvas, box, spec)
