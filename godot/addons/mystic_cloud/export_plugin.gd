@tool
extends EditorPlugin

const PLUGIN_NAME := "MysticCloudSave"
const PLAY_GAMES_DEPENDENCY := "com.google.android.gms:play-services-games-v2:22.0.0"

var _export_plugin: AndroidExportPlugin


func _enter_tree() -> void:
	_export_plugin = AndroidExportPlugin.new()
	add_export_plugin(_export_plugin)


func _exit_tree() -> void:
	if _export_plugin != null:
		remove_export_plugin(_export_plugin)
	_export_plugin = null


class AndroidExportPlugin extends EditorExportPlugin:
	const NAME := "MysticCloudSave"
	const GAMES_DEPENDENCY := "com.google.android.gms:play-services-games-v2:22.0.0"

	func _supports_platform(platform: EditorExportPlatform) -> bool:
		return platform is EditorExportPlatformAndroid

	func _get_android_libraries(_platform: EditorExportPlatform,
			debug: bool) -> PackedStringArray:
		var variant := "debug" if debug else "release"
		return PackedStringArray([
			"mystic_cloud/bin/%s/MysticCloudSave-%s.aar" % [variant, variant],
		])

	func _get_android_dependencies(_platform: EditorExportPlatform,
			_debug: bool) -> PackedStringArray:
		return PackedStringArray([GAMES_DEPENDENCY])

	func _get_android_manifest_application_element_contents(
			_platform: EditorExportPlatform, _debug: bool) -> String:
		var project_id := _games_project_id()
		if project_id.is_empty():
			return ""
		return ("<meta-data android:name=\"com.google.android.gms.games.APP_ID\" "
			+ "android:value=\"@string/game_services_project_id\" />")

	func _get_name() -> String:
		return NAME

	func _games_project_id() -> String:
		var project_id := OS.get_environment("MYSTIC_GAMES_PROJECT_ID").strip_edges()
		if project_id.is_empty():
			var local_path := ProjectSettings.globalize_path(
				"res://../android_games_app_id.txt")
			if FileAccess.file_exists(local_path):
				project_id = FileAccess.get_file_as_string(local_path).strip_edges()
		var digits := RegEx.new()
		digits.compile("^[0-9]{1,20}$")
		return project_id if digits.search(project_id) != null else ""
