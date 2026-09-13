# DebugMarker.gd — uji MINIMAL "apakah engine ini benar-benar menjalankan scene
# dari repo?" (preflight tools/godot_debug_run.py).
#
# KENAPA ADA
# ==========
# Kegagalan "harness tidak mencetak satu baris pun" pernah memakan beberapa run
# CI untuk dijelaskan, karena tiga sebab yang sangat berbeda tampak sama saja di
# artifact:
#   * skrip `DebugRun.gd` gagal DIKOMPILASI (analyzer GDScript menolak panggilan
#     method di luar `Node` tanpa `has_method`),
#   * scene tidak ditemukan/dijalankan engine,
#   * konteks render (Xvfb/GL) tidak siap sehingga scene mati sebelum _ready.
# Scene ini sengaja TIDAK memakai satu pun API game (tanpa autoload, tanpa
# `get_tree().get_first_node_in_group`, tanpa panggilan dinamis): yang diuji
# hanya "engine + scene dari repo + tulis berkas". Kalau penanda ini lulus,
# maka harness yang bisu PASTI masalah skrip harness, bukan lingkungan.
#
# Dipanggil headless (tanpa layar) supaya murah:
#   godot --headless --path godot res://scenes/debug/DebugMarker.tscn -- --out=/tmp/x
extends Node


func _ready() -> void:
	var out_dir := ""
	for raw in OS.get_cmdline_user_args():
		var text := str(raw)
		if text.begins_with("--out="):
			out_dir = text.substr("--out=".length())
	if out_dir.is_empty():
		print("[DebugMarker] FAIL: --out= tidak ada di argumen scene")
		get_tree().quit(1)
		return
	var path := out_dir.path_join("marker.txt")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		print("[DebugMarker] FAIL: %s tidak bisa ditulis" % path)
		get_tree().quit(1)
		return
	file.store_string("engine menjalankan scene %s dari repo\n" % scene_file_path)
	file.close()
	print("[DebugMarker] PASS — engine menjalankan scene dari repo (%s)" % path)
	get_tree().quit(0)
