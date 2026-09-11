# FrustumCuller.gd — port _system.py:40-50 (blok `performance.py`).
#
# pygame memakai ini untuk melewatkan BLIT entitas di luar layar: alloc
# `pygame.Surface` + `blit` itu CPU dan mahal, jadi "di luar layar" berarti
# "jangan digambar sama sekali". Godot men-cull CanvasItem sendiri di GPU,
# sehingga padanan yang SETIA bukan "jangan gambar unit" (sudah gratis),
# melainkan "jangan siapkan gambar yang dibangun dengan draw_* per frame"
# — dipakai `scenes/fx/WorldPopups.gd` (antrean 300 teks rusak = draw_string
# 2x per entri per frame).
#
# Aturan batas diambil apa adanya: margin 80 px + radius entitas, dan
# layarnya 1280x720 (`SCREEN_WIDTH`/`SCREEN_HEIGHT` dari `_core.py:88-89`).
# Di Godot koordinat popup adalah KOORDINAT LAYAR hasil transform camera, jadi
# pemanggil mengirim ukuran viewport — bukan asumsi konstanta.
extends RefCounted
class_name FrustumCuller

## Paritas `FrustumCuller.MARGIN = 80`
const MARGIN := 80.0
## Paritas `_core.py:88-89` (viewport project.godot sama: 1280x720)
const SCREEN_WIDTH := 1280.0
const SCREEN_HEIGHT := 720.0
## Paritas `is_visible(x, y, radius=30)` — pemanggil pygame selalu mengirim
## radius-nya sendiri (`m.radius`, `h.radius`, partikel 10 di `_core.py:2899`).
const DEFAULT_RADIUS := 30.0


## `radius` default 30.0 = paritas `is_visible(x, y, radius=30)`; unit pygame
## selalu memanggil dengan radius-nya sendiri (`m.radius`, `h.radius`,
## partikel 10 di `_core.py:2899`).
static func is_visible(x: float, y: float, radius: float = DEFAULT_RADIUS,
		screen: Vector2 = Vector2(SCREEN_WIDTH, SCREEN_HEIGHT)) -> bool:
	var m := MARGIN + radius
	return (-m <= x and x <= screen.x + m
			and -m <= y and y <= screen.y + m)


## Versi world-space untuk pemanggil yang punya camera: titik dunia diproyeksi
## ke layar lewat transform canvas dulu, baru di-cull (pygame tidak punya
## camera, jadi world == screen di sana).
static func is_visible_world(world: Vector2, xform: Transform2D,
		screen: Vector2, radius: float = 30.0) -> bool:
	var p := xform * world
	return is_visible(p.x, p.y, radius, screen)
