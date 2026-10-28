extends RefCounted
## Layer 9bv17: replays `source_fonts_source_oracle.py`'s fixture through the
## native style lookup, and proves the five Godot TTFs are byte copies of the
## source bundle. The source oracle runs the real `_render.py` maps with `ast`,
## so no filename or hash below is invented by the native suite.

const SourceFonts = preload("res://scripts/ui/source_fonts.gd")
const FIXTURE := "res://tests/fixtures/source_fonts_source.json"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Source font map fixture parses")
	if not (data is Dictionary):
		return
	var style_map: Dictionary = data.get("style_font_map", {})
	var body_map: Dictionary = data.get("body_font_files", {})
	check.call(style_map.size() == 5, "The source pins five font styles")
	check.call(body_map.size() == 4, "The source pins four body weights")
	check.call(
		String(data.get("title_font_file", "")) == "Cinzel.ttf", "The source title face is Cinzel"
	)
	check.call(
		String(data.get("font_path_default", "")) == "Barlow-Regular.ttf",
		"An unknown style falls back to Barlow-Regular in the source"
	)
	check.call(
		bool(data.get("copies_match", false)),
		"The source oracle proves every Godot TTF copy matches"
	)

	check.call(
		SourceFonts.STYLE_FILES == style_map,
		"Native STYLE_FILES mirrors _render.py::_STYLE_FONT_MAP"
	)
	check.call(
		SourceFonts.DEFAULT_FILE == String(data.get("font_path_default", "")),
		"Native default mirrors _font_path's fallback"
	)
	for style in style_map:
		check.call(
			SourceFonts.has_style(style),
			"Native lookup recognises the source style " + String(style)
		)
		check.call(
			SourceFonts.file_for_style(style) == String(style_map[style]),
			"Native filename mirrors _font_path for " + String(style)
		)
	check.call(
		not SourceFonts.has_style("not_a_source_style"),
		"An unknown style is not a declared source style"
	)
	check.call(
		SourceFonts.file_for_style("not_a_source_style") == "Barlow-Regular.ttf",
		"An unknown style resolves to the source default file"
	)

	check.call(
		SourceFonts.for_style("title") == SourceFonts.TITLE,
		"Title ops get Cinzel, not Barlow-SemiBold"
	)
	check.call(SourceFonts.for_style("body") == SourceFonts.REGULAR, "Body ops get Barlow-Regular")
	check.call(
		SourceFonts.for_style("body_medium") == SourceFonts.MEDIUM,
		"Medium ops get the newly copied Barlow-Medium"
	)
	check.call(
		SourceFonts.for_style("body_bold") == SourceFonts.BOLD,
		"Bold ops get the newly copied Barlow-Bold"
	)
	check.call(
		SourceFonts.for_style("body_semibold") == SourceFonts.SEMI_BOLD,
		"Semibold ops get Barlow-SemiBold"
	)
	check.call(
		SourceFonts.for_style("unknown") == SourceFonts.REGULAR,
		"Unknown styles get the source default font"
	)

	var godot_hashes: Dictionary = data.get("godot_font_sha256", {})
	var source_hashes: Dictionary = data.get("source_font_sha256", {})
	check.call(
		godot_hashes == source_hashes and godot_hashes.size() == 5,
		"Source and Godot SHA-256 tables agree for all five TTFs"
	)
	for name in godot_hashes:
		var path := "res://assets/fonts/" + String(name)
		check.call(FileAccess.file_exists(path), "Godot ships " + String(name))
		check.call(
			FileAccess.get_sha256(path) == String(godot_hashes[name]),
			"Native Godot copy of " + String(name) + " matches the source bytes"
		)
