# SpatialGrid.gd — port _system.py:52-134 (blok `performance.py`).
#
# Struktur data + aturan kueri dipindah 1:1 dari pygame, BUKAN hanya idenya:
#   * satu entitas masuk PERSIS satu bucket (sel dari titik pusatnya), jadi
#     tidak ada duplikat antar-bucket dan tidak perlu set `seen` per kueri
#     (_system.py:76-80);
#   * radius dibandingkan dengan JARAK KUADRAT tanpa sqrt — pygame mencatat
#     >1,3 juta panggilan hypot/menit di jalur ini (_system.py:81-90);
#   * kotak kasar (bbox) diperiksa sebelum jarak kuadrat, supaya kandidat jauh
#     dari bucket besar terbuang murah (_system.py:103-108);
#   * filter musuh (`entity.team == team or not entity.alive`) terjadi DI
#     DALAM loop kueri, bukan sebagai list comprehension kedua
#     (_system.py:119-133);
#   * hasil mengikuti URUTAN BUCKET (sel dijajak cx lalu cy, isi bucket sesuai
#     urutan insert). Ini bagian yang sering salah di port: pemilih target
#     `in_range[0]` / `best_dist` pertama-menang bergantung urutan.
#
# Sel dihitung dengan `floor(x / cell)` — pygame memakai `x // cell` yang untuk
# float adalah `floor(v/w)`. `int(x / cell)` TIDAK setara: int() di GDScript
# memotong ke nol, jadi entitas di koordinat negatif (kueri yang radiusnya
# melewati tepi kiri/atas layar) masuk sel yang salah. `keys_negatif` di
# fixture mengunci kasus ini.
#
# Pemakaian di Godot: singleton-nya ada di `CombatSystem` (padanan `_grid`
# tingkat modul di _system.py:145) karena di sanalah jalur query unit hidup.
extends RefCounted
class_name SpatialGrid

## Paritas `SpatialGrid(cell_size=60)` + catatan _system.py:136-144: cell 60
## (turun dari 100) ~2x lebih cepat pada kerumunan 400 entitas.
const CELL_SIZE := 60.0

var cell_size: float = CELL_SIZE
## Vector2i sel -> Array entitas (isi = urutan insert, paritas dict-of-list)
var grid: Dictionary = {}


func clear() -> void:
	grid.clear()


## Paritas badan `update_spatial_grid` (_system.py:159-167): bersihkan lalu
## insert minion dan hero/boss berurutan, MELOMPATI unit mati. Diletakkan di
## sini supaya cadence (siapa yang memanggil, tiap berapa frame) tetap milik
## pemanggil (`CombatSystem` / `Main`) sementara aturannya di sini.
func update_from(minions: Array, heroes: Array) -> void:
	clear()
	for m in minions:
		if not _is_dead(m):
			insert(m)
	for h in heroes:
		if not _is_dead(h):
			insert(h)


func insert(entity) -> void:
	var p := _pos(entity)
	var key := Vector2i(_cell(p.x), _cell(p.y))
	var bucket = grid.get(key)
	if bucket == null:
		grid[key] = [entity]
	else:
		bucket.append(entity)


## Paritas `query_range(x, y, radius)` TANPA filter tim (`team=None`):
## tidak menyaring tim maupun `alive` — sama seperti pygame, yang hanya
## menyaring alive saat INSERT (update_spatial_grid melompati unit mati).
func query_range(x: float, y: float, radius: float) -> Array:
	return _query(x, y, radius, "", false)


## Paritas `query_range(x, y, radius, team)` dengan tim diberikan: buang sekutu
## (tim sama, termasuk dua-duanya "") dan unit mati. Tim kosong BUKAN "tanpa
## filter" — di pygame hero netral punya `team == ""` dan tetap difilter.
func query_enemies(x: float, y: float, radius: float, team: String) -> Array:
	return _query(x, y, radius, team, true)


func _query(x: float, y: float, radius: float, team: String,
		filter_team: bool) -> Array:
	var results: Array = []
	var cs := cell_size
	var r2 := radius * radius
	var x0 := x - radius
	var x1 := x + radius
	var y0 := y - radius
	var y1 := y + radius
	var min_cx := _cell(x0)
	var max_cx := _cell(x1)
	var min_cy := _cell(y0)
	var max_cy := _cell(y1)
	for cx in range(min_cx, max_cx + 1):
		for cy in range(min_cy, max_cy + 1):
			var bucket = grid.get(Vector2i(cx, cy))
			if bucket == null or (bucket as Array).is_empty():
				continue
			for entity in bucket:
				var p := _pos(entity)
				if p.x < x0 or p.x > x1 or p.y < y0 or p.y > y1:
					continue
				if filter_team and (str(_team(entity)) == team or _is_dead(entity)):
					continue
				var dx := p.x - x
				var dy := p.y - y
				if dx * dx + dy * dy <= r2:
					results.append(entity)
	return results


## Jumlah entitas terindeks (dipakai tes + debug overlay; pygame tidak punya
## padanan, jadi tidak dipakai jalur permainan).
func count() -> int:
	var n := 0
	for key in grid:
		n += (grid[key] as Array).size()
	return n


# ══════════════════════════════════════════════════════════
#  JEMBATAN ATRIBUT (pygame: entity.x/.y/.team/.alive)
# ══════════════════════════════════════════════════════════

## pygame menyimpan posisi entitas sebagai `x`/`y` world; unit Godot adalah
## Node2D. Harness boleh memakai Node2D telanjang + meta, jadi properti
## `x`/`y` tetap dicoba sebagai fallback.
static func _pos(entity) -> Vector2:
	if entity is Node2D:
		return (entity as Node2D).global_position
	var ex = entity.get("x")
	var ey = entity.get("y")
	if ex != null and ey != null:
		return Vector2(float(ex), float(ey))
	return Vector2.ZERO


static func _team(entity) -> String:
	var t = entity.get("team")
	return "" if t == null else str(t)


## `alive` pygame ↔ `is_dead` Godot (minion/hero/tower/boss/nexus memakai
## flag mati). Unit tanpa kedua properti dianggap hidup.
static func _is_dead(entity) -> bool:
	var d = entity.get("is_dead")
	if d != null:
		return bool(d)
	var a = entity.get("alive")
	if a != null:
		return not bool(a)
	return false


## `int(v / cell)` BUKAN padanan `v // cell`: int() GDScript memotong ke nol,
## sedangkan floor division Python membulatkan ke bawah — bedanya nyata untuk
## koordinat negatif (kueri yang radiusnya melewati tepi kiri/atas layar).
## Karena itu sel dihitung lewat satu fungsi ini, bukan di-inline.
func _cell(v: float) -> int:
	return int(floor(v / cell_size))
