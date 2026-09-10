## Kamera arena + screen shake — port _render.ScreenShake (_render.py:572-599).
##
## Kenapa kelas ini ada: selama ini Boss.gd / Hero.gd memanggil
## `call_group("camera", "add_trauma", ...)` tetapi TIDAK ada satu pun skrip
## di proyek yang mendefinisikan `add_trauma`. Camera2D polos di
## scenes/main.tscn tidak punya metode itu, dan call_group ke metode yang
## tidak ada = no-op senyap. Akibatnya SEMUA screen shake mati di Godot,
## padahal pygame memanggilnya dari puluhan tempat (hero fx, boss, menara).
##
## Rumus di bawah disalin persis dari pygame, bukan dikira-kira:
##   * decay 0.85 per FRAME (bukan per detik) → dipangkatkan delta*60.
##   * intensity di-`max`, BUKAN dijumlah (beberapa sumber shake bersamaan
##     tidak menumpuk jadi guncangan raksasa).
##   * di bawah 0.5 px langsung dipotong ke 0 (supaya tidak ada getaran
##     setengah piksel yang bikin sprite berkedut selamanya).
##   * offset acak dalam rentang INTEGER → getaran terasa "piksel-per-piksel"
##     seperti pygame, bukan meluncur halus.
##
## Catatan SATUAN: pemanggil yang sudah ada memakai `amount / 60.0`
## (Boss._shake(25.0) → trauma 0.4167). Maka 1.0 trauma = 60 px, sehingga
## trauma * TRAUMA_TO_PX mengembalikan tepat 25 px = add_shake(25.0) pygame.
##
## UI TIDAK ikut bergetar: ini sengaja. Pygame menggeser surface dunia di
## Game.draw (_core.py:2826) dan menggambar UI terpisah di
## EffectManager.draw_ui (_render.py:801-803: "tidak ikut shake"). Di Godot
## hal yang sama dicapai lewat `offset` kamera — CanvasLayer HUD kebal.

extends Camera2D

## 1.0 trauma = 60 px. Mengikat konvensi `amount / 60.0` di Boss/Hero.
const TRAUMA_TO_PX: float = 60.0

## Peluruhan per frame pygame (ScreenShake.decay).
const DECAY: float = 0.85

## Di bawah nilai ini guncangan dianggap selesai (ScreenShake.update).
const CUTOFF: float = 0.5

## Intensitas tersisa, dalam PIKSEL (sama dengan add_shake pygame).
var intensity: float = 0.0


## Port ScreenShake.add_shake — satuan PIKSEL.
func add_shake(px: float) -> void:
	if not GameManager.screen_shake_enabled:
		return
	# `max`, bukan `+=`: dua sumber shake bersamaan tidak menjumlah.
	intensity = maxf(intensity, px)


## Antarmuka yang dipakai Boss.gd / Hero.gd: 1.0 trauma = 60 px.
func add_trauma(trauma: float) -> void:
	add_shake(trauma * TRAUMA_TO_PX)


## Port ScreenShake.get_offset — untuk pemanggil yang butuh angkanya saja.
func get_shake_offset() -> Vector2:
	if intensity <= 0.0:
		return Vector2.ZERO
	var span := int(intensity)
	return Vector2(
		randi_range(-span, span),
		randi_range(-span, span))


func _process(delta: float) -> void:
	# Peluruhan 0.85/frame pygame dinormalkan ke delta (tetap identik di
	# 60 Hz, tidak meledak di layar 144 Hz).
	if intensity > 0.0:
		intensity *= pow(DECAY, delta * 60.0)
		if intensity < CUTOFF:
			intensity = 0.0
	offset = get_shake_offset()
