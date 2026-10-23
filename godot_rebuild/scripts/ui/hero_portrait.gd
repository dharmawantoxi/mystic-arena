extends Control
## Presentation-only native Hero Shop portraits with a deterministic generic fallback bust.

const SIZE := 96.0
const GENERIC_PAINTER = preload("res://scripts/ui/hero_portrait_generic.gd")
const ALCHEMIST_PAINTER = preload("res://scripts/ui/hero_portrait_alchemist.gd")
const ABADDON_PAINTER = preload("res://scripts/ui/hero_portrait_abaddon.gd")
const APPARITION_PAINTER = preload("res://scripts/ui/hero_portrait_ancient_apparition.gd")
const AURETHZAR_PAINTER = preload("res://scripts/ui/hero_portrait_aurethzar.gd")
const COGSWORTH_PAINTER = preload("res://scripts/ui/hero_portrait_cogsworth.gd")
const DRAKAR_PAINTER = preload("res://scripts/ui/hero_portrait_drakar.gd")
const GORNAK_PAINTER = preload("res://scripts/ui/hero_portrait_gornak.gd")
const GRONDMAURIS_PAINTER = preload("res://scripts/ui/hero_portrait_grondmauris.gd")
const IGNIS_PAINTER = preload("res://scripts/ui/hero_portrait_ignis_drachorn.gd")
const KAIZEN_PAINTER = preload("res://scripts/ui/hero_portrait_kaizen.gd")
const KUNKKA_PAINTER = preload("res://scripts/ui/hero_portrait_kunkka.gd")
const MORGATH_PAINTER = preload("res://scripts/ui/hero_portrait_morgath.gd")
const MORTHRAXIS_PAINTER = preload("res://scripts/ui/hero_portrait_morthraxis.gd")
const ZEPHYR_PAINTER = preload("res://scripts/ui/hero_portrait_zephyr.gd")
const AELYRION_PAINTER = preload("res://scripts/ui/hero_portrait_aelyrion.gd")
const AERALITH_PAINTER = preload("res://scripts/ui/hero_portrait_aeralith.gd")
const AKAHIME_PAINTER = preload("res://scripts/ui/hero_portrait_akahime.gd")
const AKAROTH_PAINTER = preload("res://scripts/ui/hero_portrait_akaroth.gd")
const AKASHARI_PAINTER = preload("res://scripts/ui/hero_portrait_akashari.gd")
const AKIRAKUMO_PAINTER = preload("res://scripts/ui/hero_portrait_akirakumo.gd")
const AKIRAZE_PAINTER = preload("res://scripts/ui/hero_portrait_akiraze.gd")
const ASTRAELION_PAINTER = preload("res://scripts/ui/hero_portrait_astraelion.gd")
const AURELIAN_PAINTER = preload("res://scripts/ui/hero_portrait_aurelian.gd")
const AURELION_PAINTER = preload("res://scripts/ui/hero_portrait_aurelion.gd")
const AURELIX_PAINTER = preload("res://scripts/ui/hero_portrait_aurelix.gd")
const AURELYSSA_PAINTER = preload("res://scripts/ui/hero_portrait_aurelyssa.gd")
const AUREX_PAINTER = preload("res://scripts/ui/hero_portrait_aurex.gd")
const AUROTH_PAINTER = preload("res://scripts/ui/hero_portrait_auroth.gd")
const AZKHARION_PAINTER = preload("res://scripts/ui/hero_portrait_azkharion.gd")
const AZURETH_PAINTER = preload("res://scripts/ui/hero_portrait_azureth.gd")
const BHORGATHUL_PAINTER = preload("res://scripts/ui/hero_portrait_bhorgathul.gd")
const BROGGMAR_PAINTER = preload("res://scripts/ui/hero_portrait_broggmar.gd")
const BRUMHAR_PAINTER = preload("res://scripts/ui/hero_portrait_brumhar.gd")
const CELWYNN_PAINTER = preload("res://scripts/ui/hero_portrait_celwynn.gd")
const CRYSSALIA_PAINTER = preload("res://scripts/ui/hero_portrait_cryssalia.gd")
const DEIDARA_PAINTER = preload("res://scripts/ui/hero_portrait_deidara.gd")
const DORAKAI_PAINTER = preload("res://scripts/ui/hero_portrait_dorakai.gd")
const DRAV_PAINTER = preload("res://scripts/ui/hero_portrait_drav.gd")
const EMBERWICK_PAINTER = preload("res://scripts/ui/hero_portrait_emberwick.gd")
const GARUMENSHI_PAINTER = preload("res://scripts/ui/hero_portrait_garumenshi.gd")
const GHRAKMAAL_PAINTER = preload("res://scripts/ui/hero_portrait_ghrakmaal.gd")
const GORATH_PAINTER = preload("res://scripts/ui/hero_portrait_gorath.gd")
const GRAVEFANG_PAINTER = preload("res://scripts/ui/hero_portrait_gravefang.gd")
const GRAVEWAKE_PAINTER = preload("res://scripts/ui/hero_portrait_gravewake.gd")
const GRIMJACK_PAINTER = preload("res://scripts/ui/hero_portrait_grimjack.gd")
const GRIMKOR_PAINTER = preload("res://scripts/ui/hero_portrait_grimkor.gd")
const GRIMSTALKER_PAINTER = preload("res://scripts/ui/hero_portrait_grimstalker.gd")
const GRONDARTHUL_PAINTER = preload("res://scripts/ui/hero_portrait_grondarthul.gd")
const HITOKAGE_PAINTER = preload("res://scripts/ui/hero_portrait_hitokage.gd")
const HOLLOWBANE_PAINTER = preload("res://scripts/ui/hero_portrait_hollowbane.gd")
const IGNAKHOR_PAINTER = preload("res://scripts/ui/hero_portrait_ignakhor.gd")
const IGNIRUS_PAINTER = preload("res://scripts/ui/hero_portrait_ignirus.gd")
const INFRAKZAAR_PAINTER = preload("res://scripts/ui/hero_portrait_infrakzaar.gd")
const KAERISSA_PAINTER = preload("res://scripts/ui/hero_portrait_kaerissa.gd")
const XARNATHUL_PAINTER = preload("res://scripts/ui/hero_portrait_xarnathul.gd")
const ZHYRAKAAN_PAINTER = preload("res://scripts/ui/hero_portrait_zhyrakaan.gd")
const NYXALLARIA_PAINTER = preload("res://scripts/ui/hero_portrait_nyxallaria.gd")
const THORGARUK_PAINTER = preload("res://scripts/ui/hero_portrait_thorgaruk.gd")
const ZORATHIEL_PAINTER = preload("res://scripts/ui/hero_portrait_zorathiel.gd")
const OKEANORA_PAINTER = preload("res://scripts/ui/hero_portrait_okeanora.gd")
const GORNAK := "gornak"
const GRIMJAW := "grimjaw"
const KAIZEN := "kaizen"
const SYLARA := "sylara"
const THORNE := "thorne"
const VEX := "vex"
const ZEPHYR := "zephyr"

var hero_type := ""
var draw_pass_count: int = 0
var _definition: Variant = null


static func custom_ids() -> Array[String]:
	var ids: Array[String] = [
		"abaddon",
		"aelyrion",
		"aeralith",
		"akahime",
		"akaroth",
		"akashari",
		"akirakumo",
		"akiraze",
		"alchemist",
		"ancient_apparition",
		"astraelion",
		"aurelian",
		"aurelion",
		"aurelix",
		"aurelyssa",
		"aurethzar",
		"aurex",
		"auroth",
		"azkharion",
		"azureth",
		"bhorgathul",
		"broggmar",
		"brumhar",
		"celwynn",
		"cogsworth",
		"cryssalia",
		"deidara",
		"dorakai",
		"drakar",
		"drav",
		"emberwick",
		"garumenshi",
		"ghrakmaal",
		"gorath",
		GORNAK,
		"gravefang",
		"gravewake",
		"grimjack",
		GRIMJAW,
		"grimkor",
		"grimstalker",
		"grondarthul",
		"grondmauris",
		"hitokage",
		"hollowbane"
	]
	ids.append_array(["ignakhor", "ignirus", "ignis_drachorn", "infrakzaar"])
	ids.append_array(
		["kaerissa", KAIZEN, "kunkka", "morgath", "morthraxis", "nyxallaria", "okeanora"]
	)
	ids.append_array(
		[SYLARA, "thorgaruk", THORNE, VEX, "xarnathul", ZEPHYR, "zhyrakaan", "zorathiel"]
	)
	return ids


static func has_custom(id: String) -> bool:
	return id in custom_ids()


static func hue_for(id: String) -> float:
	var total := 0
	for byte in id.to_utf8_buffer():
		total = (total * 31 + int(byte)) % 360
	return float(total) / 360.0


func setup(id: String, definition: Variant = null, pixel_size: float = SIZE) -> void:
	hero_type = id
	_definition = definition
	draw_pass_count = 0
	custom_minimum_size = Vector2(pixel_size, pixel_size)
	queue_redraw()


func _draw() -> void:
	var box := Rect2(Vector2.ZERO, size)
	if box.size.x < 8.0 or box.size.y < 8.0:
		return
	draw_pass_count += 1
	match hero_type:
		"aelyrion":
			AELYRION_PAINTER.paint(self, box)
		"aeralith":
			AERALITH_PAINTER.paint(self, box)
		"akahime":
			AKAHIME_PAINTER.paint(self, box)
		"akaroth":
			AKAROTH_PAINTER.paint(self, box)
		"akashari":
			AKASHARI_PAINTER.paint(self, box)
		"akirakumo":
			AKIRAKUMO_PAINTER.paint(self, box)
		"akiraze":
			AKIRAZE_PAINTER.paint(self, box)
		"astraelion":
			ASTRAELION_PAINTER.paint(self, box)
		"aurelian":
			AURELIAN_PAINTER.paint(self, box)
		"aurelion":
			AURELION_PAINTER.paint(self, box)
		"aurelix":
			AURELIX_PAINTER.paint(self, box)
		"aurelyssa":
			AURELYSSA_PAINTER.paint(self, box)
		"aurex":
			AUREX_PAINTER.paint(self, box)
		"auroth":
			AUROTH_PAINTER.paint(self, box)
		"azkharion":
			AZKHARION_PAINTER.paint(self, box)
		"azureth":
			AZURETH_PAINTER.paint(self, box)
		"bhorgathul":
			BHORGATHUL_PAINTER.paint(self, box)
		"broggmar":
			BROGGMAR_PAINTER.paint(self, box)
		"brumhar":
			BRUMHAR_PAINTER.paint(self, box)
		"celwynn":
			CELWYNN_PAINTER.paint(self, box)
		"cryssalia":
			CRYSSALIA_PAINTER.paint(self, box)
		"deidara":
			DEIDARA_PAINTER.paint(self, box)
		"dorakai":
			DORAKAI_PAINTER.paint(self, box)
		"drav":
			DRAV_PAINTER.paint(self, box)
		"emberwick":
			EMBERWICK_PAINTER.paint(self, box)
		"garumenshi":
			GARUMENSHI_PAINTER.paint(self, box)
		"ghrakmaal":
			GHRAKMAAL_PAINTER.paint(self, box)
		"gorath":
			GORATH_PAINTER.paint(self, box)
		"gravefang":
			GRAVEFANG_PAINTER.paint(self, box)
		"gravewake":
			GRAVEWAKE_PAINTER.paint(self, box)
		"grimjack":
			GRIMJACK_PAINTER.paint(self, box)
		"grimkor":
			GRIMKOR_PAINTER.paint(self, box)
		"grimstalker":
			GRIMSTALKER_PAINTER.paint(self, box)
		"grondarthul":
			GRONDARTHUL_PAINTER.paint(self, box)
		"hitokage":
			HITOKAGE_PAINTER.paint(self, box)
		"hollowbane":
			HOLLOWBANE_PAINTER.paint(self, box)
		"ignakhor":
			IGNAKHOR_PAINTER.paint(self, box)
		"ignirus":
			IGNIRUS_PAINTER.paint(self, box)
		"infrakzaar":
			INFRAKZAAR_PAINTER.paint(self, box)
		"kaerissa":
			KAERISSA_PAINTER.paint(self, box)
		"xarnathul":
			XARNATHUL_PAINTER.paint(self, box)
		"zhyrakaan":
			ZHYRAKAAN_PAINTER.paint(self, box)
		"nyxallaria":
			NYXALLARIA_PAINTER.paint(self, box)
		"thorgaruk":
			THORGARUK_PAINTER.paint(self, box)
		"zorathiel":
			ZORATHIEL_PAINTER.paint(self, box)
		"abaddon":
			ABADDON_PAINTER.paint(self, box)
		"ancient_apparition":
			APPARITION_PAINTER.paint(self, box)
		"aurethzar":
			AURETHZAR_PAINTER.paint(self, box)
		"cogsworth":
			COGSWORTH_PAINTER.paint(self, box)
		"alchemist":
			ALCHEMIST_PAINTER.paint(self, box)
		"drakar":
			DRAKAR_PAINTER.paint(self, box)
		GORNAK:
			GORNAK_PAINTER.paint(self, box)
		GRIMJAW:
			_draw_grimjaw(box)
		"grondmauris":
			GRONDMAURIS_PAINTER.paint(self, box)
		"ignis_drachorn":
			IGNIS_PAINTER.paint(self, box)
		KAIZEN:
			KAIZEN_PAINTER.paint(self, box)
		"kunkka":
			KUNKKA_PAINTER.paint(self, box)
		"morgath":
			MORGATH_PAINTER.paint(self, box)
		"morthraxis":
			MORTHRAXIS_PAINTER.paint(self, box)
		"okeanora":
			OKEANORA_PAINTER.paint(self, box)
		SYLARA:
			_draw_sylara(box)
		THORNE:
			_draw_thorne(box)
		VEX:
			_draw_vex(box)
		ZEPHYR:
			ZEPHYR_PAINTER.paint(self, box)
		_:
			GENERIC_PAINTER.paint(self, box, hue_for(hero_type), _accent())
	draw_rect(box.grow(-1.0), Color8(10, 16, 24), false, 2.0)


func _draw_thorne(box: Rect2) -> void:
	var unit := _scale(box)
	var outline := Color8(38, 26, 10)
	var dark := Color8(96, 60, 14)
	var body := Color8(215, 155, 30)
	var shade := Color8(150, 95, 20)
	var light := Color8(245, 205, 110)
	var goop := Color8(120, 190, 90)

	_backdrop(box, Color8(58, 40, 18), Color8(26, 20, 12))
	var base := _p(box, 48.0, 52.0)
	for index in 7:
		var angle := -PI * 0.92 + PI * 0.84 * (float(index) / 6.0)
		var direction := Vector2(cos(angle), sin(angle))
		var tip := base + direction * 40.0 * unit
		var side := Vector2(-direction.y, direction.x) * 3.5 * unit
		draw_colored_polygon(PackedVector2Array([base - side, base + side, tip]), shade)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(30.0, 38.0),
				Vector2(66.0, 38.0),
				Vector2(72.0, 62.0),
				Vector2(66.0, 86.0),
				Vector2(30.0, 86.0),
				Vector2(24.0, 62.0)
			]
		),
		dark
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(34.0, 42.0),
				Vector2(62.0, 42.0),
				Vector2(67.0, 62.0),
				Vector2(62.0, 84.0),
				Vector2(34.0, 84.0),
				Vector2(29.0, 62.0)
			]
		),
		body
	)
	draw_colored_polygon(
		_poly(
			box,
			[Vector2(40.0, 50.0), Vector2(56.0, 50.0), Vector2(58.0, 66.0), Vector2(38.0, 66.0)]
		),
		light
	)
	draw_circle(_p(box, 48.0, 30.0), 11.0 * unit, body)
	draw_colored_polygon(
		_poly(box, [Vector2(54.0, 30.0), Vector2(72.0, 34.0), Vector2(54.0, 40.0)]), shade
	)
	draw_circle(_p(box, 43.0, 27.0), 2.2 * unit, outline)
	draw_circle(_p(box, 51.0, 27.0), 2.2 * unit, outline)
	draw_circle(_p(box, 77.0, 38.0), 3.0 * unit, goop)
	draw_circle(_p(box, 85.0, 45.0), 2.0 * unit, goop)


func _draw_grimjaw(box: Rect2) -> void:
	var unit := _scale(box)
	var outline := Color8(36, 19, 16)
	var armor := Color8(117, 58, 35)
	var leather := Color8(78, 39, 28)
	var steel := Color8(187, 151, 110)
	var skin := Color8(188, 125, 83)
	var hair := Color8(49, 27, 23)
	var ember := Color8(241, 96, 47)

	_backdrop(box, Color8(126, 57, 34), Color8(26, 17, 20))
	draw_arc(
		_p(box, 48.0, 43.0),
		34.0 * unit,
		-PI * 0.78,
		PI * 0.78,
		28,
		Color(ember.r, ember.g, ember.b, 0.30),
		maxf(2.0 * unit, 1.0),
		true
	)
	draw_line(_p(box, 20.0, 80.0), _p(box, 40.0, 46.0), outline, maxf(8.0 * unit, 2.0), true)
	draw_line(_p(box, 20.0, 80.0), _p(box, 40.0, 46.0), steel, maxf(3.0 * unit, 1.0), true)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(35.0, 48.0),
				Vector2(38.0, 35.0),
				Vector2(48.0, 42.0),
				Vector2(43.0, 53.0),
			]
		),
		steel
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(11.0, 68.0),
				Vector2(25.0, 55.0),
				Vector2(39.0, 53.0),
				Vector2(57.0, 53.0),
				Vector2(72.0, 57.0),
				Vector2(85.0, 71.0),
				Vector2(80.0, 88.0),
				Vector2(16.0, 88.0),
			]
		),
		outline
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(18.0, 69.0),
				Vector2(29.0, 60.0),
				Vector2(41.0, 59.0),
				Vector2(57.0, 59.0),
				Vector2(68.0, 62.0),
				Vector2(78.0, 72.0),
				Vector2(74.0, 84.0),
				Vector2(22.0, 84.0),
			]
		),
		armor
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(18.0, 61.0),
				Vector2(28.0, 51.0),
				Vector2(39.0, 58.0),
				Vector2(33.0, 72.0),
				Vector2(19.0, 74.0),
			]
		),
		steel
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(78.0, 60.0),
				Vector2(68.0, 51.0),
				Vector2(57.0, 58.0),
				Vector2(63.0, 72.0),
				Vector2(77.0, 74.0),
			]
		),
		steel
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(32.0, 18.0),
				Vector2(44.0, 10.0),
				Vector2(58.0, 17.0),
				Vector2(66.0, 31.0),
				Vector2(63.0, 46.0),
				Vector2(55.0, 55.0),
				Vector2(40.0, 54.0),
				Vector2(30.0, 43.0),
			]
		),
		hair
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(38.0, 23.0),
				Vector2(48.0, 18.0),
				Vector2(58.0, 24.0),
				Vector2(60.0, 39.0),
				Vector2(54.0, 48.0),
				Vector2(43.0, 47.0),
				Vector2(36.0, 39.0),
			]
		),
		skin
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(28.0, 31.0),
				Vector2(26.0, 20.0),
				Vector2(36.0, 23.0),
				Vector2(39.0, 13.0),
				Vector2(47.0, 19.0),
				Vector2(56.0, 11.0),
				Vector2(59.0, 21.0),
				Vector2(69.0, 18.0),
				Vector2(64.0, 33.0),
				Vector2(55.0, 28.0),
				Vector2(47.0, 25.0),
				Vector2(39.0, 30.0),
			]
		),
		hair
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(37.0, 40.0),
				Vector2(44.0, 45.0),
				Vector2(53.0, 45.0),
				Vector2(59.0, 39.0),
				Vector2(57.0, 52.0),
				Vector2(48.0, 61.0),
				Vector2(39.0, 53.0),
			]
		),
		leather
	)
	draw_line(_p(box, 40.0, 34.0), _p(box, 44.0, 34.0), ember, maxf(2.5 * unit, 1.0))
	draw_line(_p(box, 52.0, 34.0), _p(box, 56.0, 34.0), ember, maxf(2.5 * unit, 1.0))
	draw_line(_p(box, 37.0, 30.0), _p(box, 56.0, 39.0), outline, maxf(2.0 * unit, 1.0))
	draw_line(_p(box, 31.0, 65.0), _p(box, 62.0, 74.0), leather, maxf(3.0 * unit, 1.0), true)
	draw_circle(_p(box, 48.0, 72.0), 3.0 * unit, steel)


func _draw_sylara(box: Rect2) -> void:
	var unit := _scale(box)
	var outline := Color8(29, 30, 31)
	var cloak := Color8(31, 75, 75)
	var body := Color8(53, 128, 115)
	var hair := Color8(145, 63, 49)
	var skin := Color8(233, 190, 146)
	var trim := Color8(229, 192, 119)
	var wind := Color8(145, 220, 202)

	_backdrop(box, Color8(31, 83, 83), Color8(14, 25, 32))
	draw_arc(
		_p(box, 62.0, 49.0),
		30.0 * unit,
		-PI * 0.43,
		PI * 0.43,
		32,
		outline,
		maxf(5.0 * unit, 1.5),
		true
	)
	draw_arc(
		_p(box, 62.0, 49.0),
		30.0 * unit,
		-PI * 0.43,
		PI * 0.43,
		32,
		trim,
		maxf(2.0 * unit, 1.0),
		true
	)
	draw_line(_p(box, 68.5, 20.0), _p(box, 68.5, 78.0), wind, maxf(1.5 * unit, 1.0), true)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(15.0, 48.0),
				Vector2(26.0, 39.0),
				Vector2(29.0, 73.0),
				Vector2(19.0, 84.0),
			]
		),
		outline
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(19.0, 50.0),
				Vector2(24.0, 46.0),
				Vector2(26.0, 72.0),
				Vector2(20.0, 78.0),
			]
		),
		trim
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(48.0, 50.0),
				Vector2(65.0, 58.0),
				Vector2(78.0, 87.0),
				Vector2(18.0, 87.0),
				Vector2(27.0, 61.0),
			]
		),
		outline
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(48.0, 55.0),
				Vector2(62.0, 62.0),
				Vector2(71.0, 83.0),
				Vector2(25.0, 83.0),
				Vector2(32.0, 64.0),
			]
		),
		body
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(27.0, 65.0),
				Vector2(35.0, 59.0),
				Vector2(41.0, 63.0),
				Vector2(34.0, 82.0),
				Vector2(24.0, 82.0),
			]
		),
		cloak
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(33.0, 17.0),
				Vector2(48.0, 10.0),
				Vector2(63.0, 17.0),
				Vector2(68.0, 35.0),
				Vector2(63.0, 51.0),
				Vector2(53.0, 59.0),
				Vector2(37.0, 55.0),
				Vector2(27.0, 43.0),
				Vector2(28.0, 27.0),
			]
		),
		hair
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(37.0, 24.0),
				Vector2(48.0, 19.0),
				Vector2(59.0, 24.0),
				Vector2(61.0, 40.0),
				Vector2(54.0, 51.0),
				Vector2(43.0, 51.0),
				Vector2(36.0, 43.0),
			]
		),
		skin
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(28.0, 31.0),
				Vector2(34.0, 18.0),
				Vector2(48.0, 12.0),
				Vector2(63.0, 20.0),
				Vector2(66.0, 32.0),
				Vector2(56.0, 27.0),
				Vector2(47.0, 25.0),
				Vector2(38.0, 31.0),
			]
		),
		hair
	)
	draw_line(_p(box, 40.0, 36.0), _p(box, 44.0, 36.0), outline, maxf(2.0 * unit, 1.0))
	draw_line(_p(box, 52.0, 36.0), _p(box, 56.0, 36.0), outline, maxf(2.0 * unit, 1.0))
	draw_line(_p(box, 38.0, 59.0), _p(box, 58.0, 69.0), trim, maxf(2.0 * unit, 1.0), true)
	draw_line(_p(box, 39.0, 64.0), _p(box, 76.0, 46.0), outline, maxf(4.0 * unit, 1.0), true)
	draw_line(_p(box, 39.0, 64.0), _p(box, 76.0, 46.0), trim, maxf(1.5 * unit, 1.0), true)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(79.0, 45.0),
				Vector2(72.0, 44.0),
				Vector2(76.0, 51.0),
			]
		),
		trim
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(30.0, 19.0),
				Vector2(22.0, 8.0),
				Vector2(37.0, 14.0),
			]
		),
		wind
	)


func _draw_vex(box: Rect2) -> void:
	var unit := _scale(box)
	var outline := Color8(23, 13, 43)
	var mantle := Color8(54, 31, 92)
	var robe := Color8(91, 53, 145)
	var trim := Color8(181, 143, 237)
	var face := Color8(205, 194, 230)
	var arcane := Color8(151, 106, 240)
	var glow := Color8(118, 228, 255)

	_backdrop(box, Color8(54, 29, 93), Color8(14, 12, 30))
	for index in 3:
		var alpha := 0.30 - 0.08 * float(index)
		var radius := (22.0 + 7.0 * float(index)) * unit
		draw_arc(
			_p(box, 48.0, 42.0),
			radius,
			-PI * 0.82,
			PI * 0.18,
			28,
			Color(arcane.r, arcane.g, arcane.b, alpha),
			maxf(1.5 * unit, 1.0),
			true
		)

	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(48.0, 8.0),
				Vector2(69.0, 25.0),
				Vector2(72.0, 49.0),
				Vector2(62.0, 61.0),
				Vector2(79.0, 88.0),
				Vector2(17.0, 88.0),
				Vector2(34.0, 61.0),
				Vector2(24.0, 49.0),
				Vector2(27.0, 25.0),
			]
		),
		outline
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(35.0, 60.0),
				Vector2(43.0, 54.0),
				Vector2(53.0, 54.0),
				Vector2(61.0, 60.0),
				Vector2(66.0, 84.0),
				Vector2(30.0, 84.0),
			]
		),
		robe
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(28.0, 63.0),
				Vector2(39.0, 54.0),
				Vector2(58.0, 54.0),
				Vector2(70.0, 64.0),
				Vector2(76.0, 86.0),
				Vector2(22.0, 86.0),
			]
		),
		mantle
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(44.0, 62.0),
				Vector2(48.0, 58.0),
				Vector2(52.0, 62.0),
				Vector2(58.0, 84.0),
				Vector2(38.0, 84.0),
			]
		),
		robe
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(32.0, 31.0),
				Vector2(37.0, 21.0),
				Vector2(48.0, 15.0),
				Vector2(59.0, 21.0),
				Vector2(64.0, 31.0),
				Vector2(60.0, 48.0),
				Vector2(53.0, 56.0),
				Vector2(43.0, 56.0),
				Vector2(36.0, 48.0),
			]
		),
		face
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(25.0, 36.0),
				Vector2(28.0, 23.0),
				Vector2(48.0, 9.0),
				Vector2(68.0, 23.0),
				Vector2(71.0, 36.0),
				Vector2(59.0, 30.0),
				Vector2(48.0, 26.0),
				Vector2(37.0, 30.0),
			]
		),
		outline
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(30.0, 36.0),
				Vector2(38.0, 31.0),
				Vector2(37.0, 53.0),
				Vector2(29.0, 48.0),
			]
		),
		mantle
	)
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(66.0, 36.0),
				Vector2(58.0, 31.0),
				Vector2(59.0, 53.0),
				Vector2(67.0, 48.0),
			]
		),
		mantle
	)
	draw_line(_p(box, 39.0, 39.0), _p(box, 44.0, 39.0), arcane, maxf(2.0 * unit, 1.0))
	draw_line(_p(box, 52.0, 39.0), _p(box, 57.0, 39.0), arcane, maxf(2.0 * unit, 1.0))
	draw_colored_polygon(
		_poly(
			box,
			[
				Vector2(40.0, 65.0),
				Vector2(48.0, 58.0),
				Vector2(56.0, 65.0),
			]
		),
		trim
	)
	draw_line(_p(box, 30.0, 69.0), _p(box, 43.0, 79.0), trim, maxf(2.0 * unit, 1.0), true)
	draw_line(_p(box, 66.0, 70.0), _p(box, 75.0, 61.0), outline, maxf(4.0 * unit, 1.0), true)
	draw_arc(
		_p(box, 75.0, 53.0), 12.0 * unit, -PI * 0.9, PI * 1.8, 24, glow, maxf(2.0 * unit, 1.0), true
	)
	draw_circle(_p(box, 75.0, 53.0), 8.0 * unit, arcane)
	draw_circle(_p(box, 75.0, 53.0), 3.5 * unit, glow)
	draw_circle(_p(box, 19.0, 29.0), 1.5 * unit, glow)
	draw_circle(_p(box, 79.0, 25.0), 1.5 * unit, trim)


func _accent() -> Color:
	var role := ""
	if _definition is Dictionary:
		role = String((_definition as Dictionary).get("role", ""))
	elif _definition != null and "role" in _definition:
		role = String(_definition.role)
	match role:
		"Assassin":
			return Color8(120, 220, 200)
		"Bruiser":
			return Color8(230, 170, 70)
		"Mage":
			return Color8(170, 140, 240)
		"Marksman":
			return Color8(230, 130, 120)
		_:
			return Color8(150, 170, 175)


func _scale(box: Rect2) -> float:
	return box.size.x / SIZE


func _p(box: Rect2, x: float, y: float) -> Vector2:
	return box.position + Vector2(x, y) * _scale(box)


func _poly(box: Rect2, points: Array[Vector2]) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point in points:
		result.append(box.position + point * _scale(box))
	return result


func _backdrop(box: Rect2, top: Color, bottom: Color) -> void:
	var bands := 18
	var height := box.size.y / float(bands)
	for index in bands:
		var band := Rect2(
			box.position.x, box.position.y + height * float(index), box.size.x, height + 1.0
		)
		draw_rect(band, top.lerp(bottom, float(index) / float(bands - 1)))
