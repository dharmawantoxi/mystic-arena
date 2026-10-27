extends RefCounted
## Hero Shop native custom portrait dispatch, fallback, and shared draw-pass counter.
## Every roster hero has a native custom canvas; unknown IDs retain the generic fallback.
## Draw tests cover card and 96-unit sizes, including Raz's source-informed Fire Monk palette.

const HeroPortrait = preload("res://scripts/ui/hero_portrait.gd")
const HeroShopCard = preload("res://scripts/ui/hero_shop_card.gd")
const RazPainter = preload("res://scripts/ui/hero_portrait_raz.gd")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS
const RAZ_FIXTURE := "res://tests/fixtures/hero_portrait_raz_source.json"

const MATCH_PANEL := "res://scripts/ui/hero_shop_panel.gd"
const META_PANEL := "res://scripts/ui/meta_hero_shop_panel.gd"
const SAMPLE: Array[String] = [
	"kaizen",
	"thorne",
	"grimjaw",
	"vex",
	"sylara",
	"zephyr",
	"gornak",
	"morgath",
	"alchemist",
	"drakar",
	"abaddon",
	"ancient_apparition",
	"aurethzar",
	"cogsworth",
	"grondmauris",
	"morthraxis",
	"okeanora",
	"kunkka",
	"ignis_drachorn",
	"aelyrion",
	"aeralith",
	"akahime",
	"akaroth",
	"akashari",
	"akirakumo",
	"akiraze",
	"astraelion",
	"aurelian",
	"aurelion",
	"aurelix",
	"aurelyssa",
	"aurex",
	"auroth",
	"azkharion",
	"azureth",
	"bhorgathul",
	"broggmar",
	"brumhar",
	"celwynn",
	"cryssalia",
	"deidara",
	"dorakai",
	"drav",
	"emberwick",
	"garumenshi",
	"ghrakmaal",
	"gorath",
	"gravefang",
	"gravewake",
	"grimjack",
	"grimkor",
	"grimstalker",
	"grondarthul",
	"hitokage",
	"hollowbane",
	"ignakhor",
	"ignirus",
	"infrakzaar",
	"kaerissa",
	"xarnathul",
	"zhyrakaan",
	"thorgaruk",
	"zorathiel",
	"nyxallaria",
	"vhaerinth",
	"xharokh",
	"kazreth",
	"varkuthar",
	"zhyvrek",
	"thargoroth",
	"raz"
]


func run(tree: SceneTree, check: Callable) -> void:
	_dispatch(check)
	_fallback(check)
	_raz_palette(check)
	_card(check)
	_wiring(check)
	await _draw_counter(tree, check)


func _dispatch(check: Callable) -> void:
	var custom := HeroPortrait.custom_ids()
	var expected: Array[String] = []
	for id in HERO_ROSTER:
		expected.append(str(id))
	expected.sort()
	check.call(custom == expected, "Portrait list covers every roster hero")
	for id in expected:
		check.call(HeroPortrait.has_custom(id), "%s dispatches to a native custom canvas" % id)
	check.call(HeroPortrait.has_custom("raz"), "Raz dispatches to the native Fire Monk portrait")
	check.call(
		not HeroPortrait.has_custom("unknown_portrait_test"), "Unknown id keeps generic fallback"
	)
	check.call(not HeroPortrait.has_custom(""), "Empty id falls back to the generic bust")


func _fallback(check: Callable) -> void:
	check.call(
		is_equal_approx(HeroPortrait.hue_for("raz"), 3.0 / 360.0), "Hero hue hash is deterministic"
	)
	check.call(
		HeroPortrait.hue_for("raz") != HeroPortrait.hue_for("zephyr"),
		"Hero hue hash separates identifiers"
	)
	for hero_type in SAMPLE:
		var hue := HeroPortrait.hue_for(hero_type)
		check.call(hue >= 0.0 and hue < 1.0, "Hero hue stays inside the HSV range: %s" % hero_type)
	for hero_type in SAMPLE:
		var portrait := HeroPortrait.new()
		portrait.setup(hero_type, HERO_ROSTER[hero_type])
		check.call(portrait.hero_type == hero_type, "Portrait stores the id for %s" % hero_type)
		portrait.free()


func _raz_palette(check: Callable) -> void:
	var source: Variant = JSON.parse_string(FileAccess.get_file_as_string(RAZ_FIXTURE))
	check.call(source is Dictionary, "Raz source palette fixture parses")
	if not source is Dictionary:
		return
	var palette: Dictionary = source.get("palette", {})
	var portrait: Dictionary = RazPainter.spec()
	check.call(
		(
			source.get("hero_type") == "raz"
			and source.get("name") == "Raz"
			and source.get("title") == "The Heat of Despair"
			and source.get("role") == "Boss/Fire Monk"
		),
		"Raz portrait fixture keeps the Fire Monk identity"
	)
	check.call(
		(
			portrait.get("family") == "fighter"
			and portrait.get("feature") == "fire"
			and portrait.get("primary") == _source_color(palette.get("red_darkest", []))
			and portrait.get("accent") == _source_color(palette.get("fire_mid", []))
			and portrait.get("light") == _source_color(palette.get("fire_hot", []))
			and portrait.get("skin") == _source_color(palette.get("skin_mid", []))
			and portrait.get("top") == _source_color(palette.get("red_mid", []))
			and portrait.get("bottom") == _source_color(palette.get("cloth_darkest", []))
			and portrait.get("hair") == _source_color(palette.get("hair_mid", []))
			and portrait.get("gold") == _source_color(palette.get("gold_mid", []))
		),
		"Raz portrait uses the source Fire Monk palette"
	)


func _source_color(values: Array) -> Color:
	if values.size() != 3:
		return Color.TRANSPARENT
	return Color8(int(values[0]), int(values[1]), int(values[2]))


func _card(check: Callable) -> void:
	var card := HeroShopCard.new()
	card.setup(
		"kaizen",
		"Kaizen — The Wind Blade\nAssassin  ·  HP 770  ·  400 G",
		false,
		485.0,
		HERO_ROSTER["kaizen"]
	)
	check.call(card is Button, "Shared card stays a Button for the scene suites")
	check.call(card.tooltip_text == "kaizen", "Card row keeps the hero id tooltip")
	check.call(card.text.contains("400 G"), "Card keeps the source status text")
	check.call(not card.disabled, "Affordable card stays pressable")
	check.call(
		card.custom_minimum_size == Vector2(485.0, HeroShopCard.CARD_HEIGHT),
		"Card uses the in-match row width"
	)
	var portrait := card.get_portrait()
	check.call(portrait != null and portrait.name == "Portrait", "Card owns a portrait node")
	check.call(portrait.hero_type == "kaizen", "Card dispatches Kaizen to its portrait")
	check.call(
		portrait.mouse_filter == Control.MOUSE_FILTER_IGNORE, "Portrait never eats the row click"
	)
	var flat := card.get_theme_stylebox("normal") as StyleBoxFlat
	check.call(
		flat != null and flat.content_margin_left >= HeroShopCard.PORTRAIT_SIZE,
		"Card text clears the portrait area"
	)
	check.call(
		card.autowrap_mode == TextServer.AUTOWRAP_WORD_SMART,
		"Card wraps long rows instead of clipping them"
	)
	check.call(
		flat.content_margin_left + flat.content_margin_right < HeroShopCard.CARD_WIDTH * 0.35,
		"Portrait leaves most of the card width for text"
	)
	check.call(
		HeroShopCard.CARD_HEIGHT >= HeroShopCard.PORTRAIT_SIZE + 24.0,
		"Card is tall enough to frame the portrait"
	)

	card.setup(
		"thorne",
		"Thorne — The Quill Sprayer\nBruiser  ·  HP 1960  ·  OWNED",
		true,
		525.0,
		HERO_ROSTER["thorne"]
	)
	check.call(card.disabled, "Owned card is disabled")
	check.call(card.custom_minimum_size.x == 525.0, "Card honours the caller width")
	check.call(card.get_portrait().hero_type == "thorne", "Card dispatches Thorne to its portrait")

	var raz_card := HeroShopCard.new()
	raz_card.setup("raz", "Raz — The Heat of Despair\n1400 G", false, 485.0, HERO_ROSTER["raz"])
	check.call(raz_card.get_portrait().hero_type == "raz", "Card dispatches Raz to his portrait")
	check.call(
		HeroPortrait.has_custom(raz_card.get_portrait().hero_type),
		"Raz card uses the custom portrait"
	)
	raz_card.free()

	var generic := HeroShopCard.new()
	generic.setup("unknown_portrait_test", "Unknown hero\n1400 G", false, 485.0, HERO_ROSTER["raz"])
	check.call(
		generic.get_portrait().hero_type == "unknown_portrait_test",
		"Card preserves an unknown hero id for fallback"
	)
	check.call(
		not HeroPortrait.has_custom(generic.get_portrait().hero_type),
		"Unknown card uses the generic fallback"
	)
	generic.free()
	card.free()


func _wiring(check: Callable) -> void:
	var match_panel := FileAccess.get_file_as_string(MATCH_PANEL)
	var meta_panel := FileAccess.get_file_as_string(META_PANEL)
	check.call(
		"HeroShopCard.new()" in match_panel,
		"In-match Hero Shop builds rows through the shared card"
	)
	check.call(
		"HeroShopCard.new()" in meta_panel,
		"Permanent Hero Shop builds rows through the shared card"
	)
	check.call(
		"hero_requested.emit(hero_type)" in match_panel, "Match card keeps its request signal"
	)
	check.call(
		"unlock_requested.emit(hero_type)" in meta_panel, "Permanent card keeps its request signal"
	)


func _draw_counter(tree: SceneTree, check: Callable) -> void:
	var grimjaw_portrait := HeroPortrait.new()
	grimjaw_portrait.setup("grimjaw", HERO_ROSTER["grimjaw"], 96.0)
	grimjaw_portrait.size = Vector2(96.0, 96.0)
	tree.root.add_child(grimjaw_portrait)
	var vex_portrait := HeroPortrait.new()
	vex_portrait.setup("vex", HERO_ROSTER["vex"], 96.0)
	vex_portrait.size = Vector2(96.0, 96.0)
	vex_portrait.position = Vector2(96.0, 0.0)
	tree.root.add_child(vex_portrait)
	var sylara_portrait := HeroPortrait.new()
	sylara_portrait.setup("sylara", HERO_ROSTER["sylara"], 96.0)
	sylara_portrait.size = Vector2(96.0, 96.0)
	sylara_portrait.position = Vector2(192.0, 0.0)
	tree.root.add_child(sylara_portrait)
	var zephyr_portrait := HeroPortrait.new()
	zephyr_portrait.setup("zephyr", HERO_ROSTER["zephyr"], 96.0)
	zephyr_portrait.size = Vector2(96.0, 96.0)
	zephyr_portrait.position = Vector2(288.0, 0.0)
	tree.root.add_child(zephyr_portrait)
	var gornak_portrait := HeroPortrait.new()
	gornak_portrait.setup("gornak", HERO_ROSTER["gornak"], 96.0)
	gornak_portrait.size = Vector2(96.0, 96.0)
	gornak_portrait.position = Vector2(0.0, 96.0)
	tree.root.add_child(gornak_portrait)
	var morgath_portrait := HeroPortrait.new()
	morgath_portrait.setup("morgath", HERO_ROSTER["morgath"], 96.0)
	morgath_portrait.size = Vector2(96.0, 96.0)
	morgath_portrait.position = Vector2(96.0, 96.0)
	tree.root.add_child(morgath_portrait)
	var alchemist_portrait := HeroPortrait.new()
	alchemist_portrait.setup("alchemist", HERO_ROSTER["alchemist"], 96.0)
	alchemist_portrait.size = Vector2(96.0, 96.0)
	alchemist_portrait.position = Vector2(192.0, 96.0)
	tree.root.add_child(alchemist_portrait)
	var drakar_portrait := HeroPortrait.new()
	drakar_portrait.setup("drakar", HERO_ROSTER["drakar"], 96.0)
	drakar_portrait.size = Vector2(96.0, 96.0)
	drakar_portrait.position = Vector2(288.0, 96.0)
	tree.root.add_child(drakar_portrait)
	var abaddon_portrait := HeroPortrait.new()
	abaddon_portrait.setup("abaddon", HERO_ROSTER["abaddon"], 96.0)
	abaddon_portrait.size = Vector2(96.0, 96.0)
	abaddon_portrait.position = Vector2(384.0, 96.0)
	tree.root.add_child(abaddon_portrait)
	var apparition_portrait := HeroPortrait.new()
	apparition_portrait.setup("ancient_apparition", HERO_ROSTER["ancient_apparition"], 96.0)
	apparition_portrait.size = Vector2(96.0, 96.0)
	apparition_portrait.position = Vector2(480.0, 96.0)
	tree.root.add_child(apparition_portrait)
	var aurethzar_portrait := HeroPortrait.new()
	aurethzar_portrait.setup("aurethzar", HERO_ROSTER["aurethzar"], 96.0)
	aurethzar_portrait.size = Vector2(96.0, 96.0)
	aurethzar_portrait.position = Vector2(864.0, 96.0)
	tree.root.add_child(aurethzar_portrait)
	var cogsworth_portrait := HeroPortrait.new()
	cogsworth_portrait.setup("cogsworth", HERO_ROSTER["cogsworth"], 96.0)
	cogsworth_portrait.size = Vector2(96.0, 96.0)
	cogsworth_portrait.position = Vector2(0.0, 192.0)
	tree.root.add_child(cogsworth_portrait)
	var morthraxis_portrait := HeroPortrait.new()
	morthraxis_portrait.setup("morthraxis", HERO_ROSTER["morthraxis"], 96.0)
	morthraxis_portrait.size = Vector2(96.0, 96.0)
	morthraxis_portrait.position = Vector2(96.0, 192.0)
	tree.root.add_child(morthraxis_portrait)
	var grondmauris_portrait := HeroPortrait.new()
	grondmauris_portrait.setup("grondmauris", HERO_ROSTER["grondmauris"], 96.0)
	grondmauris_portrait.size = Vector2(96.0, 96.0)
	grondmauris_portrait.position = Vector2(192.0, 192.0)
	tree.root.add_child(grondmauris_portrait)
	var kaizen_portrait := HeroPortrait.new()
	kaizen_portrait.setup("kaizen", HERO_ROSTER["kaizen"], 96.0)
	kaizen_portrait.size = Vector2(96.0, 96.0)
	kaizen_portrait.position = Vector2(288.0, 192.0)
	tree.root.add_child(kaizen_portrait)
	var okeanora_portrait := HeroPortrait.new()
	okeanora_portrait.setup("okeanora", HERO_ROSTER["okeanora"], 96.0)
	okeanora_portrait.size = Vector2(96.0, 96.0)
	okeanora_portrait.position = Vector2(384.0, 192.0)
	tree.root.add_child(okeanora_portrait)
	var kunkka_portrait := HeroPortrait.new()
	kunkka_portrait.setup("kunkka", HERO_ROSTER["kunkka"], 96.0)
	kunkka_portrait.size = Vector2(96.0, 96.0)
	kunkka_portrait.position = Vector2(576.0, 96.0)
	tree.root.add_child(kunkka_portrait)
	var ignis_drachorn_portrait := HeroPortrait.new()
	ignis_drachorn_portrait.setup("ignis_drachorn", HERO_ROSTER["ignis_drachorn"], 96.0)
	ignis_drachorn_portrait.size = Vector2(96.0, 96.0)
	ignis_drachorn_portrait.position = Vector2(768.0, 96.0)
	tree.root.add_child(ignis_drachorn_portrait)
	var raz_portrait := HeroPortrait.new()
	raz_portrait.setup("raz", HERO_ROSTER["raz"], 96.0)
	raz_portrait.size = Vector2(96.0, 96.0)
	raz_portrait.position = Vector2(672.0, 96.0)
	tree.root.add_child(raz_portrait)
	var fallback_portrait := HeroPortrait.new()
	fallback_portrait.setup("unknown_portrait_test", HERO_ROSTER["raz"], 96.0)
	fallback_portrait.size = Vector2(96.0, 96.0)
	fallback_portrait.position = Vector2(0.0, 672.0)
	tree.root.add_child(fallback_portrait)
	# Exercise every custom painter at card size and the 96-unit design size.
	# Shared draw_pass_count remains unchanged; no per-hero counter assertions.
	var batch_portraits: Array[Control] = []
	for id in HeroPortrait.custom_ids():
		for pixel_size in [HeroShopCard.PORTRAIT_SIZE, 96.0]:
			# Draw each full page before freeing its batch nodes and reusing free slots.
			if batch_portraits.size() == 72:
				await tree.process_frame
				await tree.process_frame
				for previous_portrait in batch_portraits:
					previous_portrait.queue_free()
				batch_portraits.clear()
				await tree.process_frame
			var portrait := HeroPortrait.new()
			portrait.setup(id, HERO_ROSTER[id], pixel_size)
			portrait.size = Vector2(pixel_size, pixel_size)
			# Reserve four old top-row canvases, ten at y=96 and five at y=192.
			# Up to 72 canvases per page fit inside 1280x720 without overlapping old nodes.
			var slot := batch_portraits.size() + 4
			if slot >= 13:
				slot += 10
			if slot >= 26:
				slot += 5
			portrait.position = Vector2((slot % 13) * 96.0, floorf(slot / 13.0) * 96.0)
			tree.root.add_child(portrait)
			batch_portraits.append(portrait)
	await tree.process_frame
	await tree.process_frame
	check.call(
		(
			grimjaw_portrait.draw_pass_count > 0
			and vex_portrait.draw_pass_count > 0
			and sylara_portrait.draw_pass_count > 0
			and zephyr_portrait.draw_pass_count > 0
			and gornak_portrait.draw_pass_count > 0
			and morgath_portrait.draw_pass_count > 0
			and alchemist_portrait.draw_pass_count > 0
			and drakar_portrait.draw_pass_count > 0
			and abaddon_portrait.draw_pass_count > 0
			and apparition_portrait.draw_pass_count > 0
			and aurethzar_portrait.draw_pass_count > 0
			and kunkka_portrait.draw_pass_count > 0
			and ignis_drachorn_portrait.draw_pass_count > 0
			and raz_portrait.draw_pass_count > 0
			and fallback_portrait.draw_pass_count > 0
		),
		"Custom portraits and the generic fallback reach _draw after two frames"
	)
	for portrait in batch_portraits:
		portrait.free()
	grimjaw_portrait.free()
	vex_portrait.free()
	sylara_portrait.free()
	zephyr_portrait.free()
	gornak_portrait.free()
	morgath_portrait.free()
	alchemist_portrait.free()
	drakar_portrait.free()
	abaddon_portrait.free()
	apparition_portrait.free()
	aurethzar_portrait.free()
	cogsworth_portrait.free()
	morthraxis_portrait.free()
	grondmauris_portrait.free()
	kaizen_portrait.free()
	okeanora_portrait.free()
	kunkka_portrait.free()
	ignis_drachorn_portrait.free()
	raz_portrait.free()
	fallback_portrait.free()
