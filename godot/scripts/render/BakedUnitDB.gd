# BakedUnitDB.gd — akses manifest strip PNG hasil bake renderer pygame.
#
# Fase 5 Opsi A: 216 renderer boss (bosses/level1..54.py) + 6 hero
# masterwork (heroes/_bundle.py) terlalu besar untuk di-port 1:1 ke
# GDScript, jadi visualnya dibake sekali oleh
# tools/convert_to_godot.py --units-png menjadi strip PNG per unit
# (godot/assets/units/<type>.png) + manifest godot/data/baked_units.json
# (anchor kaki, frame, skala, fps). File ini adalah pintu baca manifest
# tersebut — SATU tempat supaya BakedSprite.gd dan RendererRegistry.gd
# tidak masing-masing mem-parsing JSON.
#
# Kenapa lazy: 222 strip ≈ 222 tekstur; satu match hanya menampilkan
# ~12 hero + 3 mini boss + 1 true boss. Memuat semuanya saat boot =
# ratusan MB VRAM sia-sia (dan jatuh di Android). Texture dimuat saat
# unit itu benar-benar spawn, FIFO cap 64 entri sebagai pengaman
# (F1 respawn berganti roster tidak boleh menumpuk tanpa batas).
#
# Skala & fps diambil dari manifest, bukan hardcode di sini, karena
# nilainya diukur dari pygame saat bake:
#   hero_scale — _get_hero_scale (heroes/__init__.py:2148, pipeline
#     normalisasi tinggi badan HERO_TARGET_HEIGHT 65 × global 0.78),
#   fps hero 6 / boss 12 — fase idle baru tiap 10 frame hero
#     (pulse += 0.05, _entity.py:1681) vs 5 frame boss
#     (bosses/base_boss.py:580), kunci 8 fase (heroes/__init__.py:1777).
extends Object

const MANIFEST_PATH := "res://data/baked_units.json"

## Cache manifest (dibaca sekali). Dictionary kosong = bake belum ada /
## gagal dibaca; caller mem-fallback ke UnitSilhouette.
static var _manifest: Dictionary = {}
static var _loaded: bool = false

## type -> Texture2D (lazy load + FIFO cap).
static var _textures: Dictionary = {}
const TEXTURE_CAP := 64


static func _ensure_loaded() -> void:
	if _loaded:
		return
	_loaded = true
	if not FileAccess.file_exists(MANIFEST_PATH):
		# Bake belum dijalankan (clone tanpa asset). Bukan error fatal:
		# arena kembali ke UnitSilhouette seperti sebelum Fase 5.
		push_warning("[BakedUnitDB] %s tidak ada — jalankan "
				% MANIFEST_PATH
				+ "tools/convert_to_godot.py --units-png")
		return
	var raw := FileAccess.get_file_as_string(MANIFEST_PATH)
	var parsed = JSON.parse_string(raw)
	if parsed is Dictionary and parsed.get("units") is Dictionary:
		_manifest = parsed["units"]
	else:
		push_warning("[BakedUnitDB] manifest rusak/tidak valid: "
				+ MANIFEST_PATH)


static func has_unit(unit_type: String) -> bool:
	_ensure_loaded()
	return _manifest.has(unit_type)


## Entri manifest unit (frame_w/frame_h/anchor/*_scale/fps/anims).
## Dictionary kosong kalau unit tidak terdaftar.
static func entry(unit_type: String) -> Dictionary:
	_ensure_loaded()
	return _manifest.get(unit_type, {})


## Tekstur strip unit (lazy). Null kalau bake tidak ada / gagal load.
static func texture(unit_type: String) -> Texture2D:
	_ensure_loaded()
	if _textures.has(unit_type):
		return _textures[unit_type] as Texture2D
	var e: Dictionary = _manifest.get(unit_type, {})
	if e.is_empty() or not e.has("png"):
		return null
	var tex = load(str(e["png"]))
	if tex is Texture2D:
		if _textures.size() >= TEXTURE_CAP and not _textures.is_empty():
			# FIFO: buang entri paling lama (Dictionary menjaga urutan
			# penyisipan; for-break = kunci pertama).
			for oldest in _textures:
				_textures.erase(oldest)
				break
		_textures[unit_type] = tex
		return tex as Texture2D
	push_warning("[BakedUnitDB] gagal memuat %s" % str(e["png"]))
	return null
