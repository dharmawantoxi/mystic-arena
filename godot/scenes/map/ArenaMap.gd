# ArenaMap.gd — Port dari map_components/ + _render.MapRenderer
# Di Pygame: 6 layer blit manual (terrain, river, lane, decor, shop, wall) + cache static_map
# Di Godot (Fase 3): SATU tekstur statik per tema — bake output pygame sendiri
# (_render.MapRenderer._render_static_map via tools/convert_to_godot.py --maps-png),
# ditampilkan lewat Sprite2D + cache GPU. Cuaca (partikel+kabut) & layer dinamis
# tetap digambar live di atasnya, persis urutan draw pygame.
#
# Kenapa tekstur tunggal, bukan TileSet .tres (rencana awal Fase 3)? Diukur:
# 533 dari 576 sel 40px di 1280x720 adalah tile UNIK (speckle terrain + kurva
# river/lane) — atlas TileSet akan sama besar dengan peta itu sendiri dan
# TileMapLayer 576 sel hanya menambah overhead. Arsitektur pygame sendiri =
# satu Surface statik di-cache lalu blit tiap frame (_render.py:141/196);
# padanan persisnya di Godot ya Texture2D + Sprite2D ini. Paritas sempurna
# dengan konstruksi karena bake memakai renderer asli.
#
# JARING PENGAMAN: selama bake belum ada (converter belum dijalankan), map
# digambar prosedural di _draw() memakai palette ASLI dari
# map_components/themes.py + lane path dari PathGenerator.generate_lanes().
# apply_theme() menyalakan fallback ini otomatis kalau tekstur tidak ketemu.
#
# TEMA PER LEVEL (FASE 35 — migrasi map_components/ -> godot++): 54 palet
# runtime dihitung saat _ready dari MapDBLoader.theme_palette() — dict tema
# mentah (backend GDScript MapDB.gd + data/themes_raw.json, atau C++
# MysticMaps kalau lib GDExt dibuild + flag mystic/maps/use_gdext_maps true)
# + derive_palette() yang bit-eksak dengan export_themes() converter
# (termasuk round() bankir Python — lihat MapDB.round_half_even).
# res://data/themes.json TIDAK dibaca lagi; berkas itu tinggal sebagai
# pembanding independen (MapDataParityTest baterai 13 membuktikan loader ==
# converter untuk semua 54 tema). const THEMES di bawah tinggal sebagai
# (a) override kurasi modulate/light/energy untuk 4 tema pertama
# (forest/desert/ice/abyss — art direction Godot tanpa padanan pygame), dan
# (b) jaring pengaman kalau loader kosong (themes_raw.json hilang).
extends Node2D

const MapDB = preload("res://scripts/core/MapDBLoader.gd")

## Tema level — diisi dari levels.json["map_theme"] (54 nama; lihat
## map_components/themes.py THEMES). Nama tak dikenal -> fallback forest.
@export var theme_name: String = "forest"
## Ukuran arena — paritas _core.SCREEN_WIDTH/SCREEN_HEIGHT
@export var arena_size: Vector2 = Vector2(1280, 720)
## true = gambar fallback prosedural; otomatis false begitu Ground punya TileSet
@export var procedural_fallback: bool = true

@onready var light: DirectionalLight2D = $SunLight
@onready var canvas_modulate: CanvasModulate = $CanvasModulate

# Shop positions (mirip _render.py radiant/dire)
var radiant_shop_pos := Vector2(340, 540)
var dire_shop_pos := Vector2(940, 180)
## Radius klik bangunan toko — paritas `shop_size = 60` (_render.py:109).
const SHOP_CLICK_RADIUS := 60.0

# Base positions (paritas _core.BLUE_BASE_X/Y, RED_BASE_X/Y)
const BLUE_BASE := Vector2(100, 620)
const RED_BASE := Vector2(1180, 100)

# Lebar jalur (paritas StaticRenderer.draw_lane: lane_width=42, radius = 42/2+4)
const LANE_HALF_WIDTH := 25.0
const RIVER_HALF_WIDTH := 30.0
const TILE := 40.0 # ukuran "tile" ditheran prosedural

# ═══ PALETTE — dipindah dari map_components/themes.py (radiant_grass_*, dire_earth_*,
# path_stone_*, river_*) supaya fallback warna = palette game asli, bukan asal pilih.
const THEMES: Dictionary = {
	"forest": {
		"modulate": Color(1, 1, 1), "light": Color(1, 0.95, 0.9, 1), "energy": 0.85,
		"grass_dark": Color("#1c3720"), "grass_mid": Color("#26482a"),
		"grass": Color("#345c37"), "grass_light": Color("#447346"),
		"moss": Color("#375a28"),
		"earth_dark": Color("#2d201c"), "earth": Color("#412d26"),
		"earth_light": Color("#553c30"), "ash": Color("#3c3732"),
		"path": Color("#554c41"), "path_light": Color("#73695a"),
		"path_bright": Color("#91826c"), "path_border": Color("#3a342d"),
		"river": Color("#230c22"), "river_dark": Color("#080812"),
		"river_glow": Color("#b12e4b"), "river_foam": Color("#ff828c"),
		"tree": Color("#19371e"), "tree_light": Color("#2d5a32"),
		"stone": Color("#555046"),
	},
	"desert": {
		"modulate": Color(1, 0.92, 0.75), "light": Color(1, 0.85, 0.6, 1), "energy": 1.1,
		"grass_dark": Color("#9b733c"), "grass_mid": Color("#b4874b"),
		"grass": Color("#d2a55f"), "grass_light": Color("#e6be78"),
		"moss": Color("#8c6e37"),
		"earth_dark": Color("#5f371e"), "earth": Color("#7d4b28"),
		"earth_light": Color("#965f37"), "ash": Color("#af8c5a"),
		"path": Color("#91734b"), "path_light": Color("#b49164"),
		"path_bright": Color("#d7b482"), "path_border": Color("#6e5537"),
		"river": Color("#194f22"), "river_dark": Color("#081d12"),
		"river_glow": Color("#96dc44"), "river_foam": Color("#dcffa0"),
		"tree": Color("#785f2d"), "tree_light": Color("#a08246"),
		"stone": Color("#aa966e"),
	},
	"ice": {
		"modulate": Color(0.85, 0.9, 1), "light": Color(0.7, 0.85, 1, 1), "energy": 0.9,
		"grass_dark": Color("#b4c8dc"), "grass_mid": Color("#c8dceb"),
		"grass": Color("#dcebf5"), "grass_light": Color("#ebf5fa"),
		"moss": Color("#96b4d2"),
		"earth_dark": Color("#3c5069"), "earth": Color("#556982"),
		"earth_light": Color("#6e87a0"), "ash": Color("#96afc8"),
		"path": Color("#7d91aa"), "path_light": Color("#a0b4cd"),
		"path_bright": Color("#c3d7eb"), "path_border": Color("#5a6e87"),
		"river": Color("#326496"), "river_dark": Color("#14325a"),
		"river_glow": Color("#aadcff"), "river_foam": Color("#e6f5ff"),
		"tree": Color("#7896b4"), "tree_light": Color("#aac8e1"),
		"stone": Color("#96a5b9"),
	},
	"abyss": {
		"modulate": Color(1, 0.75, 0.75), "light": Color(1, 0.5, 0.5, 1), "energy": 0.6,
		"grass_dark": Color("#050406"), "grass_mid": Color("#0c080a"),
		"grass": Color("#160e10"), "grass_light": Color("#231416"),
		"moss": Color("#120a0c"),
		"earth_dark": Color("#020203"), "earth": Color("#080506"),
		"earth_light": Color("#100a0c"), "ash": Color("#1e1012"),
		"path": Color("#140e0e"), "path_light": Color("#281918"),
		"path_bright": Color("#412823"), "path_border": Color("#080607"),
		"river": Color("#550f0f"), "river_dark": Color("#190508"),
		"river_glow": Color("#f04b2d"), "river_foam": Color("#ff9150"),
		"tree": Color("#0a0608"), "tree_light": Color("#1c1012"),
		"stone": Color("#281c1a"),
	},
}

## Palet runtime 54 tema — dihitung _load_themes() dari MapDBLoader (backend
## GDScript MapDB.gd + data/themes_raw.json, atau C++ MysticMaps). Kunci dan
## nilainya bit-eksak dengan res://data/themes.json (converter), yang tinggal
## sebagai pembanding independen di MapDataParityTest.
## Nama tema fallback untuk nama yang benar-benar tak dikenal
## (paritas get_theme: THEMES.get(theme_name, FOREST_THEME)).
const FALLBACK_THEME := "forest"

## Palet RUNTIME = const THEMES + themes.json. const THEMES tidak bisa dipakai
## langsung: Dictionary const di Godot 4 read-only rekursif, jadi merge() ke
## sana akan error "Cannot assign a new value to a constant".
var themes: Dictionary = {}

# ═══ CUACA / ATMOSFER — port DynamicRenderer partikel + fog ═══
# pygame: _init_particles (_bundle.py:5370-5422), update() (:5453-5503),
# _draw_particles (:5666-5737), _init_fog (:5424-5447), _draw_fog (:5542-5560).
# Di sana partikel adalah dict Python yang diblit satu per satu tiap frame;
# di Godot dua CPUParticles2D sudah cukup (satu batch draw, tidak ada loop
# per partikel di GDScript).
#
# KENAPA CPUParticles2D, bukan GPUParticles2D: GPUParticles butuh
# ParticleProcessMaterial + (di beberapa backend) shader compile saat runtime,
# dan target port ini termasuk Android/GLES di mana GPU particles sering
# di-fallback. CPUParticles2D memberi hasil identik untuk jumlah kecil
# (30-60 partikel, sama seperti particle_count pygame) dan bisa diatur
# sepenuhnya dari kode tanpa resource tambahan.
#
# Kunci parity-nya BUKAN warna, tapi GERAK — pygame memilih kecepatan per
# particle_type (_bundle.py:5397-5412): snow turun (vy 0.3..0.8), ember naik
# (vy -0.8..-0.3), sand menyapu horizontal, firefly melayang acak. Itu yang
# ditiru _weather_profile() di bawah, jadi level 3 (ice/snow), 4 (volcanic/
# ember) dan 5 (haunted/spirit) terasa beda gerakannya.
#
# Skala kecepatan: pygame menambah vx/vy per FRAME pada 60 FPS, sedangkan
# CPUParticles2D memakai piksel/DETIK — karena itu semua nilai pygame
# dikalikan PYGAME_FPS.
const PYGAME_FPS := 60.0
## particle_count default kalau themes.json belum punya kunci itu
## (paritas default pygame _init_particles).
const PARTICLE_COUNT_DEFAULT := 40
## Jumlah gumpalan kabut default (_init_fog: fog_count 15)
const FOG_COUNT_DEFAULT := 15
## Sisi tekstur bulat prosedural (px). Tanpa tekstur, CPUParticles2D
## menggambar kotak 1x1 px sehingga salju/bara terlihat seperti piksel keras;
## pygame menggambar titik + lingkaran glow (_draw_particles :5680-5737) dan
## kabut sebagai ELIPS lembut (_draw_fog :5551-5556). Dua tekstur gradien
## radial di bawah meniru itu tanpa file aset apa pun.
const DOT_TEX_SIZE := 16
const FOG_TEX_SIZE := 64

var _dot_tex: Texture2D = null
var _fog_tex: Texture2D = null

var _particles: CPUParticles2D = null
var _fog: CPUParticles2D = null
## Sprite2D map statik bake (Fase 3); null sampai bake pertama kali ketemu.
var _baked_map: Sprite2D = null

var _decor_points: PackedFloat32Array = PackedFloat32Array() # [x, y, size, kind] x N
## kind 2/3 hanya muncul kalau tema punya kristal / nisan (flag has_* pygame)
var _decor_wants_crystal: bool = false
var _decor_wants_grave: bool = false
## Flag dekor lain yang pygame pakai di DecorationRenderer.draw_all
## (_bundle.py:6088-6107) tapi port ini belum pernah baca.
var _decor_wants_dead_tree: bool = false
var _decor_wants_dark_tree: bool = false
var _decor_wants_bones: bool = false
var _decor_wants_moss_rock: bool = false

## Jenis dekor (nilai `kind` di _decor_points). Dulu angka telanjang 0-3
## tersebar di _build_decor + _draw_decor; dinamai supaya penambahan jenis
## tidak salah cocok antara yang menaruh dan yang menggambar.
const DECOR_TREE := 0
const DECOR_ROCK := 1
const DECOR_CRYSTAL := 2
const DECOR_GRAVE := 3
const DECOR_DEAD_TREE := 4
const DECOR_BONES := 5
var _lane_cache: Dictionary = {}

func _ready():
	z_index = -10 # map selalu di bawah unit/FX
	# Hero/Minion/Boss menanyakan posisi base + lane ke node ini lewat group,
	# jadi tidak ada koordinat arena yang di-hardcode di AI.
	add_to_group("arena_map")
	_load_themes()
	_setup_weather_nodes()
	apply_theme(theme_name)

## Bangun 54 palet runtime dari MapDBLoader (FASE 35).
##
## Urutan menang:
##   1. seluruh palet -> MapDBLoader.theme_palette() (dict tema mentah dari
##      backend GDScript/C++ + derive_palette() yang bit-eksak dengan
##      export_themes() converter — 23 warna + flag + kabut + extras).
##   2. modulate/light/energy -> const THEMES kalau tema itu sudah dikurasi
##      manual (forest/desert/ice/abyss). Tiga kunci ini konsep Godot
##      (CanvasModulate + DirectionalLight2D) yang tidak ada padanannya di
##      palet pygame, jadi kurasi manual untuk 4 level pertama dipertahankan
##      agar tampilannya tidak berubah (dikunci MapDataParityTest baterai 14).
## Loader kosong (themes_raw.json hilang + lib C++ tidak ada) -> palet runtime
## = const THEMES (jaring pengaman; perilaku lama persis terjaga).
func _load_themes() -> void:
	themes.clear()
	for tname in MapDB.theme_names():
		var pal := MapDB.theme_palette(str(tname))
		if not pal.is_empty():
			themes[str(tname)] = pal
	if themes.is_empty():
		for k in THEMES:
			themes[k] = (THEMES[k] as Dictionary).duplicate(true)
		push_warning("[ArenaMap] MapDBLoader kosong — hanya %d tema (const THEMES). "
			% themes.size() + "Jalankan tools/convert_to_godot.py --map-raw.")
		return
	if THEMES.has(FALLBACK_THEME):
		for tname in THEMES:
			if themes.has(tname):
				for k in ["modulate", "light", "energy"]:
					(themes[tname] as Dictionary)[k] = (THEMES[tname] as Dictionary)[k]
	print("[ArenaMap] %d tema palet dari MapDBLoader (backend %s)"
		% [themes.size(), MapDB.backend_name()])

## Palet tema aktif (fallback forest — paritas get_theme pygame).
func palette(t: String = "") -> Dictionary:
	var key := t if t != "" else theme_name
	if themes.has(key):
		return themes[key]
	return themes.get(FALLBACK_THEME, THEMES[FALLBACK_THEME])

func apply_theme(t: String):
	theme_name = t
	var d := palette(t)
	if canvas_modulate:
		canvas_modulate.color = Color(d["modulate"].r, d["modulate"].g, d["modulate"].b, 1.0)
	if light:
		light.color = d["light"]
		light.energy = d["energy"]
	# Fase 3: bake map statik pygame (lihat header). Tekstur ada = tekstur itu
	# sendiri yang jadi map (paritas sempurna, satu blit — padanan cache
	# static_map pygame); tidak ada = fallback prosedural menggambar sendiri.
	var bake_path := "res://assets/maps/%s.png" % t
	if ResourceLoader.exists(bake_path):
		_show_baked_map(bake_path)
		procedural_fallback = false
	else:
		_hide_baked_map()
		procedural_fallback = true
	# Cuaca ikut tema: particle_type + fog_* dari themes.json (data itu sudah
	# lama ada di pygame tapi belum pernah dipakai port ini).
	_apply_weather(d)
	# Dekor hanya perlu dibangkitkan untuk fallback prosedural — pada bake
	# dekor sudah terpanggang di dalam tekstur.
	if procedural_fallback:
		_build_decor()
	queue_redraw()

## Pasang tekstur map statik hasil bake converter sebagai Sprite2D (anak
## pertama, di bawah partikel cuaca). Lazy-create supaya _ready tidak perlu
## menyentuh aset yang boleh belum ada.
func _show_baked_map(path: String) -> void:
	var tex = load(path)
	if tex == null:
		push_warning("[ArenaMap] bake %s gagal dimuat — fallback prosedural" % path)
		return
	if _baked_map == null:
		_baked_map = Sprite2D.new()
		_baked_map.name = "BakedMap"
		_baked_map.centered = false # piksel (0,0) bake = sudut arena, sama dengan _draw()
		add_child(_baked_map)
		move_child(_baked_map, 0)
	_baked_map.texture = tex
	_baked_map.visible = true

func _hide_baked_map() -> void:
	if _baked_map != null:
		_baked_map.visible = false

# ══════════════════════════════════════════════════════════
#  CUACA: partikel atmosfer + kabut per tema
# ══════════════════════════════════════════════════════════

## Buat dua node partikel sekali saja (bukan per ganti tema) supaya
## cycle_theme() tidak menumpuk node. Keduanya anak ArenaMap, jadi ikut
## z_index map — kabut sengaja di atas partikel (pygame juga menggambar fog
## setelah particles, _bundle.py draw order).
func _setup_weather_nodes() -> void:
	_dot_tex = _make_soft_dot(DOT_TEX_SIZE, 1.6)
	# Kabut pakai gradien yang jauh lebih landai supaya tepinya tidak kelihatan
	# sebagai lingkaran, persis kesan elips tipis pygame.
	_fog_tex = _make_soft_dot(FOG_TEX_SIZE, 2.6)
	_particles = CPUParticles2D.new()
	_particles.name = "WeatherParticles"
	_particles.texture = _dot_tex
	_particles.z_index = 5
	add_child(_particles)
	_fog = CPUParticles2D.new()
	_fog.name = "WeatherFog"
	_fog.texture = _fog_tex
	_fog.z_index = 6
	add_child(_fog)


## Bikin tekstur bulat lembut (putih, alpha memudar ke tepi) langsung di kode.
## `falloff` besar = tepi lebih cepat hilang (kabut), kecil = inti lebih padat
## (partikel + glow). Warna diambil dari properti `color` CPUParticles2D, jadi
## tekstur ini cukup putih sekali dipakai semua tema.
static func _make_soft_dot(size: int, falloff: float) -> Texture2D:
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var c := float(size) * 0.5
	for y in range(size):
		for x in range(size):
			var dist := Vector2(float(x) + 0.5 - c, float(y) + 0.5 - c).length() / c
			var a: float = pow(clampf(1.0 - dist, 0.0, 1.0), falloff)
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)


## Profil gerak per particle_type — INI yang membedakan tema, bukan warnanya.
## Angka vx/vy diambil dari _init_particles pygame (_bundle.py:5397-5412)
## dalam piksel/frame; dikali PYGAME_FPS jadi piksel/detik untuk Godot.
##
## Kunci:
##   dir      arah utama (Godot: +y ke bawah, sama seperti pygame)
##   speed    kecepatan rata-rata piksel/detik
##   spread   sebaran sudut (derajat) di sekitar dir
##   damping  perlambatan (partikel melayang lebih terasa "berat")
##   scale    ukuran titik (pygame size 1-2 px, ember/spirit diberi glow)
##   life     umur detik — dihitung supaya partikel menyeberangi arena
##   palette  kunci palet tema untuk warna (pygame memakai
##            particle_colors_radiant/dire; di Godot satu warna aksen per
##            tema sudah cukup karena partikel kecil dan ada glow HDR)
##   glow     >1.0 = warna dilebihkan supaya kena bloom (project.godot
##            glow/enabled=true) — dipakai ember/spirit/firefly.
##
## Tipe yang di pygame TIDAK tergambar sama sekali (ash/spirit/mist/acid —
## _draw_particles hanya punya cabang firefly/snow/sand/ember, lihat catatan
## _bundle.py:809) tetap diberi profil di sini: datanya sudah ada di tema dan
## di Godot tidak ada alasan membiarkannya mati. Gerakannya dipilih sesuai
## nama: ash melayang turun pelan, spirit naik berombak, mist menyapu
## mendatar, acid naik seperti ember.
static func _weather_profile(kind: String) -> Dictionary:
	match kind:
		"snow":
			# vy 0.3..0.8 px/frame turun + goyang sin (update() :5471-5476)
			return {"dir": Vector2(0, 1), "speed": 0.55 * PYGAME_FPS, "spread": 12.0,
				"damping": 0.0, "scale": 2.4, "life": 14.0,
				"palette": "river_foam", "glow": 1.0}
		"ember":
			# vy -0.8..-0.3 px/frame NAIK (bara api) :5405-5408
			return {"dir": Vector2(0, -1), "speed": 0.55 * PYGAME_FPS, "spread": 18.0,
				"damping": 4.0, "scale": 2.0, "life": 9.0,
				"palette": "river_glow", "glow": 1.6}
		"acid":
			# tema racun: sengaja memakai "ember" di pygame agar spora NAIK
			# (komentar _bundle.py:812-813) — profil sama, warna dari moss.
			return {"dir": Vector2(0, -1), "speed": 0.5 * PYGAME_FPS, "spread": 22.0,
				"damping": 6.0, "scale": 2.2, "life": 10.0,
				"palette": "moss", "glow": 1.4}
		"sand":
			# vx 0.5..1.5 px/frame menyapu mendatar + gelombang vertikal :5401-5404
			return {"dir": Vector2(1, 0), "speed": 1.0 * PYGAME_FPS, "spread": 10.0,
				"damping": 0.0, "scale": 1.8, "life": 8.0,
				"palette": "path_bright", "glow": 1.0}
		"mist":
			# kabut laut: seperti sand tapi jauh lebih lambat & besar
			return {"dir": Vector2(1, 0), "speed": 0.35 * PYGAME_FPS, "spread": 8.0,
				"damping": 0.0, "scale": 4.0, "life": 16.0,
				"palette": "river_light", "glow": 1.0}
		"spirit":
			# arwah: naik pelan, sebaran lebar + damping besar = melayang
			return {"dir": Vector2(0, -1), "speed": 0.28 * PYGAME_FPS, "spread": 45.0,
				"damping": 8.0, "scale": 3.0, "life": 12.0,
				"palette": "river_glow", "glow": 1.7}
		"ash":
			# abu: turun sangat pelan, sebaran lebar (melayang tak tentu arah)
			return {"dir": Vector2(0, 1), "speed": 0.25 * PYGAME_FPS, "spread": 60.0,
				"damping": 5.0, "scale": 2.2, "life": 16.0,
				"palette": "ash", "glow": 1.0}
		_:
			# firefly (default pygame): melayang acak ke segala arah,
			# vx/vy -0.4..0.4 px/frame :5410-5412
			return {"dir": Vector2(0, -1), "speed": 0.4 * PYGAME_FPS, "spread": 180.0,
				"damping": 2.0, "scale": 2.2, "life": 6.0,
				"palette": "river_glow", "glow": 1.5}


## Terapkan particle_type + fog_* tema aktif ke dua node CPUParticles2D.
## Dipanggil dari apply_theme(), jadi cycle_theme() (tombol debug T) langsung
## mengganti cuaca juga.
func _apply_weather(d: Dictionary) -> void:
	if _particles == null or _fog == null:
		return # scene dipakai tanpa _ready (unit test) — jangan crash
	var kind := str(d.get("particle_type", "firefly"))
	var prof := _weather_profile(kind)
	var base: Color = d.get(prof["palette"], d.get("river_glow", Color.WHITE))
	var glow := float(prof["glow"])
	var col := Color(base.r * glow, base.g * glow, base.b * glow, 0.85)

	# Jumlah partikel: particle_count tema (pygame _init_particles memakainya
	# apa adanya; di sana ada juga preset kualitas mobile.perf.Quality yang
	# TIDAK diport — Godot punya rendering/quality sendiri).
	_particles.emitting = false
	_particles.amount = maxi(4, int(d.get("particle_count", PARTICLE_COUNT_DEFAULT)))
	_particles.lifetime = float(prof["life"])
	# preprocess = arena sudah penuh partikel sejak frame pertama, bukan
	# kosong lalu terisi pelan-pelan (pygame menaburnya acak saat init).
	_particles.preprocess = float(prof["life"])
	_particles.local_coords = false
	_particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_particles.emission_rect_extents = arena_size * 0.5
	_particles.position = arena_size * 0.5
	_particles.direction = prof["dir"] as Vector2
	_particles.spread = float(prof["spread"])
	_particles.initial_velocity_min = float(prof["speed"]) * 0.6
	_particles.initial_velocity_max = float(prof["speed"]) * 1.4
	# CPUParticles2D memakai pasangan min/max (tidak ada properti "damping"
	# tunggal seperti ParticleProcessMaterial) — salah nama di sini tidak
	# ketahuan gdparse, tapi jadi error "Invalid assignment" saat jalan.
	_particles.damping_min = float(prof["damping"]) * 0.5
	_particles.damping_max = float(prof["damping"])
	_particles.gravity = Vector2.ZERO # semua gerak sudah dari direction/speed
	# scale_amount = PENGALI ukuran tekstur, bukan piksel — profil menyimpan
	# diameter yang diinginkan (pygame: size 1-2 px + glow ~3-4 px), jadi
	# dibagi DOT_TEX_SIZE dulu.
	var dot_scale := float(prof["scale"]) / float(DOT_TEX_SIZE)
	_particles.scale_amount_min = dot_scale * 0.7
	_particles.scale_amount_max = dot_scale
	_particles.color = col
	_particles.emitting = true

	# ── KABUT (fog_enabled / fog_color / fog_alpha / fog_count) ──
	# pygame: gumpalan elips besar yang menyapu mendatar sangat pelan
	# (_init_fog vx -0.1..0.1 px/frame, _draw_fog ellipse size 30-60).
	var fog_on := bool(d.get("fog_enabled", true))
	_fog.emitting = false
	if not fog_on:
		return
	var fog_col: Color = d.get("fog_color", Color(0.31, 0.24, 0.24))
	var fog_alpha := float(d.get("fog_alpha", 0.12))
	_fog.amount = maxi(3, int(d.get("fog_count", FOG_COUNT_DEFAULT)))
	_fog.lifetime = 26.0
	_fog.preprocess = 26.0
	_fog.local_coords = false
	_fog.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_fog.emission_rect_extents = Vector2(arena_size.x * 0.5, arena_size.y * 0.35)
	_fog.position = Vector2(arena_size.x * 0.5, arena_size.y * 0.45)
	_fog.direction = Vector2(1, 0)
	_fog.spread = 6.0
	_fog.initial_velocity_min = 0.05 * PYGAME_FPS
	_fog.initial_velocity_max = 0.1 * PYGAME_FPS
	_fog.damping_min = 0.0
	_fog.damping_max = 0.0
	_fog.gravity = Vector2.ZERO
	# Gumpalan besar & tipis: lebar elips pygame 60-120 px (_init_fog size
	# 30-60, _draw_fog menggambar size*2 mendatar) -> pengali tekstur 64 px.
	_fog.scale_amount_min = 60.0 / float(FOG_TEX_SIZE)
	_fog.scale_amount_max = 120.0 / float(FOG_TEX_SIZE)
	_fog.color = Color(fog_col.r, fog_col.g, fog_col.b, fog_alpha)
	_fog.emitting = true


## Ganti ke tema berikutnya dalam palette (dipakai tombol debug T di Main.gd)
func cycle_theme() -> String:
	var names: Array = themes.keys()
	var idx := maxi(names.find(theme_name), 0)
	var nxt: String = names[(idx + 1) % names.size()]
	apply_theme(nxt)
	return nxt

# ═══ LANE PATH — via MapDBLoader (FASE 35) ═══
# Dulu waypoint + interpolasi Catmull-Rom ditulis tangan di sini (duplikat
# PathGenerator dengan DUA deviasi: titik float tanpa trunc int() Python, dan
# lane mid memakai smoothness 10 bukan 8 -> minion berjalan di jalur yang
# sedikit beda). Sekarang satu sumber (MapDB.gd/MysticMaps, dibuktikan
# MapDataParityTest baterai 9-10) — fungsi ini tinggal cache + override bake.
func get_lane_path(lane: String) -> PackedVector2Array:
	if _lane_cache.has(lane):
		return _lane_cache[lane]
	# Curve2D hasil bake (kalau nanti ada di data/paths) lebih dulu
	var curve_path = "res://data/paths/%s.tres" % lane
	if ResourceLoader.exists(curve_path):
		var curve: Curve2D = load(curve_path)
		var baked: PackedVector2Array = curve.get_baked_points()
		_lane_cache[lane] = baked
		return baked
	var lanes := MapDB.generate_lanes(int(arena_size.x), int(arena_size.y))
	var key := lane if (lanes as Dictionary).has(lane) else "mid"
	var pts: PackedVector2Array = (lanes as Dictionary)[key]
	_lane_cache[lane] = pts
	return pts

func get_river_path() -> PackedVector2Array:
	if _lane_cache.has("river"):
		return _lane_cache["river"]
	var pts := MapDB.generate_river(int(arena_size.x), int(arena_size.y))
	_lane_cache["river"] = pts
	return pts

# Titik dekor (pohon/batu) — deterministik seed 42.
#
# SENGAJA tidak memakai MapDBLoader.generate_decorations(): scatter di sini
# adalah sistem kurasi Godot (74 titik + picker jenis per sisi peta dengan
# ambang bertumpuk) yang tampilannya sudah dikunci; 14 kategori pygame
# (posisi + ukuran + varian) tidak dipetakan 1:1 ke 6 jenis DECOR_* di sini.
# Posisi pygame ASLI tersedia lewat loader (dibuktikan MapDataParityTest
# baterai 11 + A/B C++) untuk dipakai nanti tanpa mengubah visual sekarang.
func _build_decor():
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	_decor_points.clear()
	# Flag dekor tema aktif (hasil export_themes; pygame memakainya di
	# DecorationRenderer). Dibaca ulang tiap ganti tema.
	var d := palette()
	_decor_wants_crystal = bool(d.get("has_ice_crystals", false)) \
		or bool(d.get("has_crystals_blue", false)) or bool(d.get("has_crystals_red", false))
	_decor_wants_grave = bool(d.get("has_gravestones", false))
	# Empat flag di bawah sudah lama diekspor converter tapi tak pernah
	# dibaca (lihat docs/AUDIT_PARITAS.md A1-A4): tanpa ini tema tulang dan
	# tema hutan mati sama-sama tampil "pohon + batu" walau warnanya beda.
	_decor_wants_dead_tree = bool(d.get("has_dead_trees", false))
	_decor_wants_dark_tree = bool(d.get("has_dark_trees", false))
	_decor_wants_bones = bool(d.get("has_bones", false))
	_decor_wants_moss_rock = bool(d.get("has_rocks_mossy", false))
	var lane_pts := PackedVector2Array()
	for l in ["top", "mid", "bot"]:
		lane_pts.append_array(get_lane_path(l))
	lane_pts.append_array(get_river_path())
	for _i in range(74):
		var p := Vector2(rng.randf_range(24.0, arena_size.x - 24.0),
			rng.randf_range(24.0, arena_size.y - 24.0))
		if _min_dist_to(lane_pts, p) < 70.0:
			continue # jangan nutupi jalur / river
		if p.distance_to(BLUE_BASE) < 130.0 or p.distance_to(RED_BASE) < 130.0:
			continue
		var size := rng.randf_range(11.0, 21.0)
		_decor_points.append(p.x)
		_decor_points.append(p.y)
		_decor_points.append(size)
		_decor_points.append(float(_pick_decor_kind(rng.randf(), p)))

## Pilih jenis dekor untuk satu titik.
##
## PENTING — pygame membedakan SISI PETA, bukan cuma tema: pohon gelap hanya
## di belahan Radiant dan pohon mati/tulang hanya di belahan Dire
## (_bundle.py:4767-4821, generate_all memakai _is_radiant()/_is_dire()).
## Tanpa itu peta terasa simetris dan sisi Dire kehilangan kesan gersang.
func _pick_decor_kind(roll: float, p: Vector2) -> int:
	# Ambang DITUMPUK (bukan rentang tetap) supaya jenis opsional jadi AKSEN,
	# bukan mendominasi. Versi pertama memakai ambang tetap dan tema ice
	# keluar 49 kristal dari 70 dekor — kristal menelan porsi batu karena
	# rentangnya melar saat jenis lain mati.
	var t := 0.0
	if _is_dire(p):
		# ── sisi Dire (kanan-atas): gersang, tanpa pohon rimbun ──
		if _decor_wants_dead_tree:
			t += 0.40
			if roll < t:
				return DECOR_DEAD_TREE
		if _decor_wants_bones:
			t += 0.16
			if roll < t:
				return DECOR_BONES
		if _decor_wants_grave:
			t += 0.14
			if roll < t:
				return DECOR_GRAVE
		if _decor_wants_crystal:
			t += 0.12
			if roll < t:
				return DECOR_CRYSTAL
		return DECOR_ROCK
	# ── sisi Radiant (kiri-bawah): vegetasi ──
	# Tema tanpa has_dark_trees (gurun/es) tetap dapat sedikit vegetasi,
	# porsinya lebih kecil daripada tema hutan.
	t += 0.60 if _decor_wants_dark_tree else 0.32
	if roll < t:
		return DECOR_TREE
	if _decor_wants_crystal:
		t += 0.16
		if roll < t:
			return DECOR_CRYSTAL
	if _decor_wants_grave:
		t += 0.08
		if roll < t:
			return DECOR_GRAVE
	return DECOR_ROCK

## Belahan Dire (kanan-atas) — paritas _is_dire (_bundle.py:4870-4872):
## garis batas miring dari kiri-atas ke kanan-bawah, bukan diagonal lurus.
func _is_dire(p: Vector2) -> bool:
	var threshold_y := 200.0 + (arena_size.y - 400.0) * p.x / arena_size.x
	return p.y < threshold_y - 20.0

static func _min_dist_to(points: PackedVector2Array, p: Vector2) -> float:
	var best := 1e9
	for q in points:
		var d := p.distance_to(q)
		if d < best:
			best = d
	return best

# ═══ RENDER ═══
func _draw():
	if not procedural_fallback:
		return # TileMapLayer asli yang menggambar
	var d := palette()
	_draw_terrain(d)
	_draw_river(d)
	for lane in ["top", "mid", "bot"]:
		_draw_lane(get_lane_path(lane), d)
	_draw_bases(d)
	_draw_shops(d)
	_draw_decor(d)
	_draw_walls(d)

func _draw_terrain(d: Dictionary):
	var full := Rect2(Vector2.ZERO, arena_size)
	draw_rect(full, d["grass"], true)
	# Dither 2-tone ala draw_terrain pygame: tile 40px, arah diagonal
	var y := 0.0
	var row := 0
	while y < arena_size.y:
		var x := 0.0
		while x < arena_size.x:
			var c: Color = d["grass_mid"] if int(x + y) % int(TILE * 2.0) < int(TILE) else d["grass"]
			draw_rect(Rect2(Vector2(x, y), Vector2(TILE, TILE)), c, true)
			x += TILE
		# strip rumput terang tiap 3 baris — radiant_grass_high pygame
		# (kunci paling terang palet; jatuh ke grass_light kalau belum ada)
		if row % 3 == 0:
			var hi: Color = d.get("grass_high", d["grass_light"])
			draw_rect(Rect2(Vector2(0, y), Vector2(arena_size.x, 2.0)), hi, true)
		y += TILE
		row += 1
	# Belahan dire (kanan-atas) = tanah kering, dipotong garis river
	var river_pts := get_river_path()
	var poly := PackedVector2Array()
	for i in range(river_pts.size()):
		poly.append(river_pts[i] + Vector2(0, -RIVER_HALF_WIDTH - 6.0))
	poly.append(Vector2(arena_size.x, 0))
	poly.append(Vector2(0, 0))
	draw_colored_polygon(poly, d["earth"])
	# Ash / transisi di tepi dire
	var ash: Color = d["ash"]
	for i in range(0, river_pts.size(), 3):
		var p: Vector2 = river_pts[i] + Vector2(0, -RIVER_HALF_WIDTH - 14.0)
		draw_circle(p, 16.0, Color(ash.r, ash.g, ash.b, 0.25))

func _draw_river(d: Dictionary):
	var pts := get_river_path()
	if pts.size() < 2:
		return
	draw_polyline(pts, d["river_dark"], RIVER_HALF_WIDTH * 2.0 + 10.0)
	draw_polyline(pts, d["river"], RIVER_HALF_WIDTH * 2.0)
	# arus: garis tengah patah-patah (mirip river_foam di pygame)
	var foam: Color = d["river_foam"]
	for i in range(0, pts.size() - 4, 6):
		draw_line(pts[i], pts[i + 4], Color(foam.r, foam.g, foam.b, 0.35), 3.0)

func _draw_lane(pts: PackedVector2Array, d: Dictionary):
	if pts.size() < 2:
		return
	var w := LANE_HALF_WIDTH * 2.0
	draw_polyline(pts, d["path_border"], w + 10.0)
	draw_polyline(pts, d["path"], w)
	var lit: Color = d["path_light"]
	draw_polyline(pts, Color(lit.r, lit.g, lit.b, 0.55), w * 0.45)
	# cobblestone: titik terang berkala (mirip _draw_cobblestone_tile)
	for i in range(0, pts.size(), 5):
		var p: Vector2 = pts[i]
		var n: Vector2 = pts[min(i + 1, pts.size() - 1)]
		var perp := (n - p).orthogonal().normalized()
		var cobble: Color = d["path_bright"]
		for s in [-1, 1]:
			draw_circle(p + perp * s * LANE_HALF_WIDTH * 0.55, 2.4,
				Color(cobble.r, cobble.g, cobble.b, 0.5))
	# ── LUMUT + RETAKAN JALUR (path_moss / path_crack) ──
	# Dua warna ini sudah lama diekspor converter tapi tidak pernah dibaca,
	# padahal pygame memakainya di _draw_cobblestone_tile (_bundle.py:5206-5207)
	# sebagai varian tiap ubin. Yang paling terasa: tema volcanic memberi
	# path_crack = (255,100,20) alias RETAKAN LAVA MENYALA — tanpa ini semua
	# jalur di 54 tema terlihat abu-abu seragam.
	#
	# pygame memilih varian dengan `(tx * 3 + ty * 7) % 100` per ubin
	# (deterministik, bukan acak). Di sini rumus yang sama dipakai pada
	# koordinat titik jalur, jadi polanya tetap stabil antar frame tanpa
	# perlu menyimpan state.
	var moss: Color = d.get("path_moss", d["path"])
	var crack: Color = d.get("path_crack", d["path_border"])
	for i in range(0, pts.size(), 3):
		var p: Vector2 = pts[i]
		var n: Vector2 = pts[min(i + 1, pts.size() - 1)]
		var fwd := (n - p).normalized()
		var perp := fwd.orthogonal()
		var variant := int(p.x * 3.0 + p.y * 7.0) % 100
		var off := perp * (float((variant % 7) - 3) / 3.0) * LANE_HALF_WIDTH * 0.7
		if variant < 22:
			# bercak lumut: elips kecil menempel di tepi jalur
			draw_circle(p + off, 3.2, Color(moss.r, moss.g, moss.b, 0.45))
		elif variant < 34:
			# retakan: garis pendek searah jalur. Alpha tinggi supaya lava
			# crack benar-benar menyala kena bloom (glow HDR project.godot).
			draw_line(p + off - fwd * 5.0, p + off + fwd * 5.0,
				Color(crack.r, crack.g, crack.b, 0.7), 1.6)

func _draw_bases(d: Dictionary):
	# Radiant (blue) kiri-bawah, Dire (red) kanan-atas — paritas _core base positions
	_draw_base(BLUE_BASE, Color(0.235, 0.47, 1.0), d)
	_draw_base(RED_BASE, Color(0.863, 0.235, 0.235), d)

func _draw_base(center: Vector2, team_color: Color, d: Dictionary):
	draw_circle(center, 112.0, Color(d["stone"].r, d["stone"].g, d["stone"].b, 0.55))
	draw_arc(center, 108.0, 0.0, TAU, 48, team_color, 3.0)
	draw_arc(center, 74.0, 0.0, TAU, 40, Color(team_color.r, team_color.g, team_color.b, 0.55), 2.0)
	# nexus
	draw_rect(Rect2(center - Vector2(26, 26), Vector2(52, 52)), team_color.darkened(0.35), true)
	draw_rect(Rect2(center - Vector2(26, 26), Vector2(52, 52)), Color(1, 1, 1, 0.75), false, 2.0)
	for i in range(4): # turret 4 penjuru
		var a := TAU * float(i) / 4.0
		var p := center + Vector2(cos(a), sin(a)) * 92.0
		draw_circle(p, 11.0, d["stone"].lightened(0.15))
		draw_arc(p, 11.0, 0.0, TAU, 16, team_color, 2.0)

func _draw_shops(d: Dictionary):
	var shop_col: Color = d["path_bright"]
	for pos in [radiant_shop_pos, dire_shop_pos]:
		var r := Rect2(pos - Vector2(34, 26), Vector2(68, 52))
		draw_rect(r, Color(shop_col.r, shop_col.g, shop_col.b, 0.9), true)
		draw_rect(r, Color(1.0, 0.804, 0.333, 0.95), false, 2.0) # gold trim
		# kanopi bergaris ala toko pygame
		for i in range(4):
			var x := r.position.x + 6.0 + float(i) * 16.0
			draw_line(Vector2(x, r.position.y + 2.0), Vector2(x, r.position.y + 12.0),
				Color(0.75, 0.16, 0.24, 0.9), 6.0)

func _draw_decor(d: Dictionary):
	var i := 0
	while i + 3 < _decor_points.size():
		var p := Vector2(_decor_points[i], _decor_points[i + 1])
		var size := _decor_points[i + 2]
		var kind := int(_decor_points[i + 3])
		if kind == DECOR_TREE:
			draw_circle(p + Vector2(0, size * 0.35), size * 0.9, Color(0, 0, 0, 0.22)) # shadow
			draw_rect(Rect2(p + Vector2(-2, 0), Vector2(4, size * 0.8)), d["earth_dark"], true) # trunk
			draw_circle(p, size, d["tree"])
			draw_circle(p + Vector2(-size * 0.3, -size * 0.35), size * 0.62, d["tree_light"])
		elif kind == DECOR_CRYSTAL:
			# Kristal (has_ice_crystals / has_crystals_*): belah ketupat memakai
			# warna aksen tema (river_glow/river_foam) biar ikut palet.
			var glow: Color = d.get("river_glow", d["stone"])
			var foam: Color = d.get("river_foam", d["stone"])
			draw_circle(p + Vector2(0, size * 0.3), size * 0.7, Color(0, 0, 0, 0.2))
			draw_colored_polygon(PackedVector2Array([
				p + Vector2(0, -size), p + Vector2(size * 0.55, 0),
				p + Vector2(0, size * 0.7), p + Vector2(-size * 0.55, 0),
			]), Color(glow.r, glow.g, glow.b, 0.85))
			draw_colored_polygon(PackedVector2Array([
				p + Vector2(0, -size), p + Vector2(size * 0.22, -size * 0.1),
				p + Vector2(0, size * 0.35), p + Vector2(-size * 0.22, -size * 0.1),
			]), Color(foam.r, foam.g, foam.b, 0.7))
		elif kind == DECOR_GRAVE:
			# Nisan (has_gravestones): lempeng batu + salib gelap
			var stone_col: Color = d["stone"]
			draw_circle(p + Vector2(2, size * 0.4), size * 0.7, Color(0, 0, 0, 0.2))
			draw_rect(Rect2(p + Vector2(-size * 0.45, -size * 0.5),
				Vector2(size * 0.9, size)), stone_col, true)
			draw_colored_polygon(PackedVector2Array([
				p + Vector2(-size * 0.45, -size * 0.5),
				p + Vector2(0, -size * 0.95),
				p + Vector2(size * 0.45, -size * 0.5),
			]), stone_col)
			draw_rect(Rect2(p + Vector2(-size * 0.08, -size * 0.3),
				Vector2(size * 0.16, size * 0.55)), d["earth_dark"], true)
			draw_rect(Rect2(p + Vector2(-size * 0.26, -size * 0.16),
				Vector2(size * 0.52, size * 0.14)), d["earth_dark"], true)
		elif kind == DECOR_DEAD_TREE:
			# Pohon mati (has_dead_trees): batang gundul + 4 cabang menjulur,
			# paritas _draw_dead_trees (_bundle.py:6213-6252) yang memang
			# menggambar batang persegi + daftar 4 garis cabang, tanpa kanopi.
			# Warna dari earth_dark/ash supaya ikut palet tema (pygame memakai
			# DEAD_TREE_1/2 global, tapi di sini palet tema lebih konsisten).
			var bark: Color = d["earth_dark"]
			var bark_hi: Color = d.get("ash", d["earth_light"])
			draw_circle(p + Vector2(0, size * 0.35), size * 0.7, Color(0, 0, 0, 0.2))
			draw_rect(Rect2(p + Vector2(-2.0, -size), Vector2(4.0, size * 1.3)), bark, true)
			draw_rect(Rect2(p + Vector2(-2.0, -size), Vector2(1.5, size * 1.3)), bark_hi, true)
			var limbs := [
				[Vector2(0, -size * 0.5), Vector2(-size * 0.5, -size + 4.0), 2.4],
				[Vector2(0, -size * 0.5 + 4.0), Vector2(size * 0.5, -size + 4.0), 2.4],
				[Vector2(0, -size + 4.0), Vector2(-size * 0.33, -size - 4.0), 1.6],
				[Vector2(0, -size + 4.0), Vector2(size * 0.33, -size - 2.0), 1.6],
			]
			for limb in limbs:
				# Cast eksplisit: elemen Array campuran bertipe Variant, dan
				# draw_line() menuntut Vector2/float. Tanpa cast Godot 4 baru
				# mengeluh saat runtime, bukan saat parse.
				draw_line(p + (limb[0] as Vector2), p + (limb[1] as Vector2),
					bark, float(limb[2]))
		elif kind == DECOR_BONES:
			# Tulang (has_bones): tengkorak + tulang rusuk bergantian, paritas
			# _draw_bones (_bundle.py:6275-6297). Warna tulang sengaja TIDAK
			# dari palet tema — pygame memakai BONE_C/BONE_D tetap, dan tulang
			# yang ikut berubah warna per tema malah tidak terbaca sebagai tulang.
			var bone: Color = Color("#dcd2be")
			var bone_d: Color = Color("#a09682")
			draw_circle(p + Vector2(0, size * 0.25), size * 0.45, Color(0, 0, 0, 0.18))
			if int(p.x) % 2 == 0:
				# tengkorak: batok + dua rongga mata
				draw_circle(p, size * 0.34, bone)
				draw_circle(p + Vector2(0, size * 0.08), size * 0.26, bone_d)
				draw_circle(p + Vector2(-size * 0.13, -size * 0.05), size * 0.07, Color(0.1, 0.09, 0.08))
				draw_circle(p + Vector2(size * 0.13, -size * 0.05), size * 0.07, Color(0.1, 0.09, 0.08))
				draw_rect(Rect2(p + Vector2(-size * 0.2, size * 0.2),
					Vector2(size * 0.4, size * 0.13)), bone, true)
			else:
				# rusuk: tulang punggung mendatar + iga vertikal
				draw_line(p + Vector2(-size * 0.45, 0), p + Vector2(size * 0.45, 0), bone, 2.2)
				for r in range(-2, 3):
					var rx := float(r) * size * 0.2
					draw_line(p + Vector2(rx, -size * 0.18), p + Vector2(rx, size * 0.18), bone_d, 1.4)
		else:
			draw_circle(p + Vector2(2, 3), size * 0.8, Color(0, 0, 0, 0.2))
			draw_circle(p, size * 0.75, d["stone"])
			var hl: Color = d["stone"].lightened(0.25)
			draw_circle(p + Vector2(-size * 0.2, -size * 0.25), size * 0.35, hl)
			# Lumut di puncak batu (has_rocks_mossy): pygame menempelkan strip
			# lumut + 3 tetesan ke bawah (_draw_rocks :6366-6373), dan hanya
			# di belahan RADIANT (has_moss = _is_radiant, :4843).
			if _decor_wants_moss_rock and not _is_dire(p):
				var moss: Color = d.get("moss", d["grass_dark"])
				draw_circle(p + Vector2(-size * 0.18, -size * 0.42), size * 0.3,
					Color(moss.r, moss.g, moss.b, 0.85))
				draw_circle(p + Vector2(size * 0.16, -size * 0.34), size * 0.2,
					Color(moss.r, moss.g, moss.b, 0.7))
		i += 4

func _draw_walls(d: Dictionary):
	# Tembok arena (biar jelas batas map, tidak "lubang" hitam di tepi)
	var border: Color = d["path_border"]
	var wall: Color = d["stone"]
	draw_rect(Rect2(Vector2.ZERO, arena_size), Color(border.r, border.g, border.b, 0.9), false, 6.0)
	draw_rect(Rect2(Vector2(6, 6), arena_size - Vector2(12, 12)),
		Color(wall.r, wall.g, wall.b, 0.4), false, 2.0)

# Titik tujuan "push" per tim (mirip PUSH di _entity.Hero) — dipakai Hero & Minion
func get_enemy_base(team: String) -> Vector2:
	return RED_BASE if team == "blue" else BLUE_BASE


## Base sendiri (dipakai Hero untuk retreat + regen 180 HP/s di radius 100)
## Paritas MapRenderer.get_clicked_shop (_render.py:246-260):
## "item" = bangunan Radiant (ITEM FORGE, dekat base biru), "hero" =
## bangunan Dire (HERO SHOP, dekat base merah), "" = tidak kena.
func get_clicked_shop(pos: Vector2) -> String:
	if pos.distance_to(radiant_shop_pos) <= SHOP_CLICK_RADIUS:
		return "item"
	if pos.distance_to(dire_shop_pos) <= SHOP_CLICK_RADIUS:
		return "hero"
	return ""


func get_own_base(team: String) -> Vector2:
	return BLUE_BASE if team == "blue" else RED_BASE

func get_spawn_point(team: String, index: int, lane: String = "mid") -> Vector2:
	var pts := get_lane_path(lane)
	if pts.size() < 4:
		return get_enemy_base(team)
	var idx := 2 + (index % 4)
	if team == "blue":
		return pts[idx]
	return pts[maxi(0, pts.size() - 1 - idx)]
