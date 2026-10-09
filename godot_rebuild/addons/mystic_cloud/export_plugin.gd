@tool
extends EditorPlugin

var _export_plugin: EditorExportPlugin


func _enter_tree() -> void:
	_export_plugin = _MysticCloudExportPlugin.new()
	add_export_plugin(_export_plugin)


func _exit_tree() -> void:
	if _export_plugin != null:
		remove_export_plugin(_export_plugin)
	_export_plugin = null


class _MysticCloudExportPlugin:
	extends EditorExportPlugin
	const PLUGIN_NAME := "MysticCloudSave"
	const LIBRARY_DIR := "mystic_cloud/bin"
	const PLAY_GAMES_DEPENDENCY := "com.google.android.gms:play-services-games-v2:22.0.0"

	func _supports_platform(platform: EditorExportPlatform) -> bool:
		return platform is EditorExportPlatformAndroid

	func _get_name() -> String:
		return PLUGIN_NAME

	func _aar_path(debug: bool) -> String:
		var variant := "debug" if debug else "release"
		return "%s/%s/%s-%s.aar" % [LIBRARY_DIR, variant, PLUGIN_NAME, variant]

	func _get_android_libraries(_platform: EditorExportPlatform, debug: bool) -> PackedStringArray:
		var relative_path := _aar_path(debug)
		if not FileAccess.file_exists("res://addons/" + relative_path):
			push_warning(
				"Mystic Cloud Save AAR is not built; Android cloud save will be unavailable."
			)
			return PackedStringArray()
		return PackedStringArray([relative_path])

	func _get_android_dependencies(
		_platform: EditorExportPlatform, debug: bool
	) -> PackedStringArray:
		return (
			PackedStringArray([PLAY_GAMES_DEPENDENCY])
			if FileAccess.file_exists("res://addons/" + _aar_path(debug))
			else PackedStringArray()
		)
