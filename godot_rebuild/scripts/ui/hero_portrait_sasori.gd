extends RefCounted
## Native canvas portrait: Sasori — Boss/Puppeteer.

const RENDERER = preload("res://scripts/ui/hero_portrait_expansion_renderer.gd")


static func paint(canvas: CanvasItem, box: Rect2) -> void:
	var spec := {
		"family": "mage",
		"feature": "neutral",
		"variant": 2,
		"sigil": 6,
		"crowned": false,
		"horned": false,
		"primary": Color8(79, 88, 99),
		"accent": Color8(153, 165, 169),
		"light": Color8(227, 231, 212),
		"skin": Color8(181, 132, 116),
		"top": Color8(53, 61, 71),
		"bottom": Color8(24, 28, 34)
	}
	RENDERER.paint(canvas, box, spec)
