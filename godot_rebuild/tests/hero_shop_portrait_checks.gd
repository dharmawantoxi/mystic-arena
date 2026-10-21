extends RefCounted
## Hero Shop custom portrait dispatch, generic fallback, and native draw-pass counter.
## Canvases: Abaddon, Alchemist, Ancient Apparition, Drakar, Gornak, Grimjaw,
## Kaizen, Kunkka, Morgath, Sylara, Thorne, Vex, and Zephyr.

const HeroPortrait = preload("res://scripts/ui/hero_portrait.gd")
const HeroShopCard = preload("res://scripts/ui/hero_shop_card.gd")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS

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
	"kunkka",
	"raz"
]


func run(tree: SceneTree, check: Callable) -> void:
	_dispatch(check)
	_fallback(check)
	_card(check)
	_wiring(check)
	await _draw_counter(tree, check)


func _dispatch(check: Callable) -> void:
	var custom := HeroPortrait.custom_ids()
	check.call(
		(
			custom
			== [
				"abaddon",
				"alchemist",
				"ancient_apparition",
				"drakar",
				"gornak",
				"grimjaw",
				"kaizen",
				"kunkka",
				"morgath",
				"sylara",
				"thorne",
				"vex",
				"zephyr"
			]
		),
		"Portrait list covers every hand-authored hero canvas"
	)
	check.call(HeroPortrait.has_custom("abaddon"), "Abaddon dispatches to a hand-authored canvas")
	check.call(
		HeroPortrait.has_custom("alchemist"), "Alchemist dispatches to a hand-authored canvas"
	)
	check.call(
		HeroPortrait.has_custom("ancient_apparition"),
		"Ancient Apparition dispatches to a hand-authored canvas"
	)
	check.call(HeroPortrait.has_custom("drakar"), "Drakar dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("gornak"), "Gornak dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("grimjaw"), "Grimjaw dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("kaizen"), "Kaizen dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("kunkka"), "Kunkka dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("morgath"), "Morgath dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("sylara"), "Sylara dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("thorne"), "Thorne dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("vex"), "Vex dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("zephyr"), "Zephyr dispatches to a hand-authored canvas")
	check.call(not HeroPortrait.has_custom("raz"), "Raz keeps the generic fallback bust")
	check.call(not HeroPortrait.has_custom(""), "Empty id falls back to the generic bust")


func _fallback(check: Callable) -> void:
	check.call(
		is_equal_approx(HeroPortrait.hue_for("raz"), 3.0 / 360.0), "Fallback hue is deterministic"
	)
	check.call(
		HeroPortrait.hue_for("raz") != HeroPortrait.hue_for("zephyr"),
		"Fallback hue separates heroes"
	)
	for hero_type in SAMPLE:
		var hue := HeroPortrait.hue_for(hero_type)
		check.call(
			hue >= 0.0 and hue < 1.0, "Fallback hue stays inside the HSV range: %s" % hero_type
		)
	for hero_type in SAMPLE:
		var portrait := HeroPortrait.new()
		portrait.setup(hero_type, HERO_ROSTER[hero_type])
		check.call(portrait.hero_type == hero_type, "Portrait stores the id for %s" % hero_type)
		portrait.free()


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

	var generic := HeroShopCard.new()
	generic.setup("raz", "Raz — The Heat of Despair\n1400 G", false, 485.0, HERO_ROSTER["raz"])
	check.call(
		generic.get_portrait().hero_type == "raz", "Card routes other heroes to the fallback"
	)
	check.call(
		not HeroPortrait.has_custom(generic.get_portrait().hero_type), "Raz uses the fallback"
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
	var kunkka_portrait := HeroPortrait.new()
	kunkka_portrait.setup("kunkka", HERO_ROSTER["kunkka"], 96.0)
	kunkka_portrait.size = Vector2(96.0, 96.0)
	kunkka_portrait.position = Vector2(576.0, 96.0)
	tree.root.add_child(kunkka_portrait)
	var raz_portrait := HeroPortrait.new()
	raz_portrait.setup("raz", HERO_ROSTER["raz"], 96.0)
	raz_portrait.size = Vector2(96.0, 96.0)
	raz_portrait.position = Vector2(672.0, 96.0)
	tree.root.add_child(raz_portrait)
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
			and kunkka_portrait.draw_pass_count > 0
			and raz_portrait.draw_pass_count > 0
		),
		"Kunkka and the generic fallback reach _draw after two frames"
	)
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
	kunkka_portrait.free()
	raz_portrait.free()
