extends RefCounted
## Hero Shop portrait slice: the Kaizen/Thorne canvases, the dispatch through
## the shared Hero Shop card and the deterministic generic fallback bust.

const HeroPortrait = preload("res://scripts/ui/hero_portrait.gd")
const HeroShopCard = preload("res://scripts/ui/hero_shop_card.gd")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS

const MATCH_PANEL := "res://scripts/ui/hero_shop_panel.gd"
const META_PANEL := "res://scripts/ui/meta_hero_shop_panel.gd"
const SAMPLE: Array[String] = ["kaizen", "thorne", "grimjaw", "vex", "sylara", "zephyr"]


func run(check: Callable) -> void:
	_dispatch(check)
	_fallback(check)
	_card(check)
	_wiring(check)


func _dispatch(check: Callable) -> void:
	var custom := HeroPortrait.custom_ids()
	check.call(custom == ["kaizen", "thorne"], "Portrait slice covers Kaizen and Thorne only")
	check.call(HeroPortrait.has_custom("kaizen"), "Kaizen dispatches to a hand-authored canvas")
	check.call(HeroPortrait.has_custom("thorne"), "Thorne dispatches to a hand-authored canvas")
	check.call(not HeroPortrait.has_custom("vex"), "Other starters fall back to the generic bust")
	check.call(not HeroPortrait.has_custom("gornak"), "Boss heroes fall back to the generic bust")
	check.call(not HeroPortrait.has_custom(""), "Empty id falls back to the generic bust")


func _fallback(check: Callable) -> void:
	check.call(
		is_equal_approx(HeroPortrait.hue_for("vex"), 9.0 / 360.0), "Fallback hue is deterministic"
	)
	check.call(
		HeroPortrait.hue_for("vex") != HeroPortrait.hue_for("sylara"),
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
	generic.setup("vex", "Vex — Vex\nAssassin  ·  420 G", false, 485.0, HERO_ROSTER["vex"])
	check.call(
		generic.get_portrait().hero_type == "vex", "Card routes other heroes to the fallback"
	)
	check.call(
		not HeroPortrait.has_custom(generic.get_portrait().hero_type), "Vex uses the fallback"
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
