# ================================
# BossPlate.gd — HP bar + papan nama boss (langkah 8-9 `Boss.draw`)
#
# Anak Node2D dari Boss, diletakkan SESUDAH `Visual` di Boss.tscn sehingga
# digambar DI ATAS badan (CanvasItem menggambar dirinya dulu, lalu anak-anak
# berurutan). Lapisan BAWAH badan (aura, bayangan, debuff, badan generik)
# digambar node Boss sendiri — lihat BossOverlay.gd.
#
# Tidak ada geometri di berkas ini: semua angka datang dari
# `BossOverlay.over_ops(boss.overlay_state())` (port base_boss.py:6225-6276).
#
# Dikunci: tools/test_boss_draw_parity.py + godot/tests/BossDrawParityTest.tscn
extends Node2D

const BossOverlay = preload("res://scripts/render/BossOverlay.gd")

## Boss.gd pemilik (diisi `_ready` Boss). Sengaja Variant: plate hanya butuh
## `overlay_state()` + `is_dead`, jadi bisa dites dengan stub.
var boss = null


func _draw() -> void:
	if boss == null or not is_instance_valid(boss):
		return
	if bool(boss.get("is_dead")):
		return
	# Op memakai koordinat dunia; node ini di local (0,0) relatif Boss, jadi
	# origin = posisi global Boss (sama seperti Boss._draw).
	var origin: Vector2 = (boss as Node2D).global_position
	BossOverlay.exec(self, BossOverlay.over_ops(boss.overlay_state()), origin)
