# GameManager.gd — Autoload, port dari _core.py Game class
# Menggantikan Game loop pygame (60 FPS) dengan Godot SceneTree
#
# Yang diport di sesi ini (sebelumnya cuma print + emit signal):
#   • EKONOMI paritas _core.py: GOLD_PER_SECOND 3 (+0.3/level), starting gold
#     base + 100/level, multiplier difficulty (easy 1.25 / normal 1.0 / hard 0.75),
#     akumulasi pecahan lewat _gold_income_milli (bukan int() per detik).
#   • STATE MATCH: "playing" / "victory" / "defeat" / "idle" — nexus hancur
#     menentukan hasil (paritas Game.update 2281-2292), wave & gold berhenti
#     saat match usai; "idle" = sedang di menu utama (in_menu).
#   • MINION_TYPES + komposisi wave dibaca dari data/economy.json (hasil convert),
#     komposisi berdasarkan nexus + elite wave, stat berdasarkan nexus sendiri.
#   • gold AI (tim red) terpisah supaya AI bisa membangun/meng-upgrade menara.
#   • aura item diproses 4×/detik (paritas hero_items.update_auras).
#
# Update sesi progresi level + menu utama:
#   • PROGRESI LEVEL: is_replay + next_level() (ENTER setelah menang lanjut ke
#     level berikutnya, paritas get_next_level main.py:566-576), restart_match()
#     kini is_replay=true, return_to_menu() (paritas main.py:582-586).
#   • META REWARD paritas _grant_meta_reward (_core.py:2365-2456): menang
#     pertama meta_gold_reward_win (3000), replay 1500 sekali lalu 200
#     unlimited lewat save replay_reward_counts, kalah 0 — ditulis ke kunci
#     save "meta_gold" (bukan "gold"), di-guard _meta_reward_granted.
#   • ENEMY SCALING (paritas _core.py:1460/1476-1483): aktif hanya difficulty
#     hard; enemy_hp_mult x1.15, damage x1.10 dari levels.json — diterapkan
#     ke minion merah (1792-1796) dan boss (1822/2097) saat spawn.
#   • AUTO-UNLOCK HERO BOSS (paritas _auto_unlock_defeated_boss_heroes
#     _core.py:2322): boss yang dikalahkan + match menang -> hero gratis masuk
#     SaveManager.unlocked_heroes (muncul di HERO SHOP + tab HERO toko).
#   • Hook BGM per level: levels.json["bgm_track"] -> AudioManager.play_bgm.
#
# Update FASE 11 (progresi — sumber unlock catch-up):
#   • purchased_heroes: daftar hero yang dimiliki pemain LINTAS-SAVE
#     (paritas Game.purchased_heroes _core.py:1596-1604) — referensi ke
#     array save "unlocked_heroes", diikat bind_purchased_heroes() saat
#     start_level dan dilepas (bukan dihapus!) di return_to_menu.
#   • catchup_unlocks() = boss_unlocks_for_purchases() — input catch-up
#     starter yang dibaca Hero._catchup_unlocks (dulu selalu 0, sehingga
#     tiap save berperilaku seperti save BARU pygame).
extends Node

signal level_started(level_num: int)
signal wave_started(wave_num: int)
signal boss_spawned(boss_type: String)
signal hero_died(hero: Node)
signal hero_respawned(hero: Node)
signal gold_changed(new_gold: int)
signal minion_died(minion: Node, killer_team: String)
signal tower_destroyed(tower: Node, killer_team: String)
signal nexus_destroyed(team: String, killer_team: String)
signal nexus_upgraded(team: String, level: int)
signal game_over(victory: bool)
signal difficulty_changed(difficulty: String)
signal selection_changed
signal shop_changed
signal tower_built(tower: Node)
## Paritas EffectManager.unlock_achievement (_render.py:813): minta popup
## achievement di layar arena. Signal, bukan node — GameManager tidak
## menggambar; HUD yang subscribe (AchievementPopup). Payload =
## (title, description, icon) persis argumen pygame.
signal achievement_unlocked(title: String, description: String, icon: String)
## Koordinat kejadian sebelum offset FloatingText (boss.x, boss.y).
signal gold_popup_added(x: float, y: float, amount: int)
signal boss_defeated(boss: Node)
## Game.update menyelesaikan EffectManager.update di frame kematian,
## BARU frame berikutnya dibekukan cinematic. HUD men-tick popup sekali.
signal boss_reward_effects_tick


const FPS := 60.0
const ComboCounterScript = preload("res://scripts/utils/ComboCounter.gd")
const FloatingTextQueueScript = preload("res://scripts/utils/FloatingTextQueue.gd")
const SparkFieldScript = preload("res://scripts/render/SparkField.gd")

# ═══ FALLBACK MINION_TYPES — port persis dari _core.py (dipakai kalau
# data/economy.json belum di-generate; warna = GRASS/GOBLIN_COLOR dkk) ═══
const FALLBACK_MINION_TYPES: Dictionary = {
	"goblin": {"name": "Goblin", "hp": 45, "damage": 5, "speed": 1.5, "range": 25,
		"attack_cooldown": 45, "gold_reward": 8, "radius": 9, "color": "#64b450"},
	"orc": {"name": "Orc", "hp": 110, "damage": 13, "speed": 0.95, "range": 30,
		"attack_cooldown": 60, "gold_reward": 18, "radius": 12, "color": "#c8643c"},
	"troll": {"name": "Troll", "hp": 320, "damage": 18, "speed": 0.65, "range": 28,
		"attack_cooldown": 75, "gold_reward": 45, "radius": 14, "color": "#648caa",
		"armor": 2, "magic_resist": 0.05, "regen": 0.6},
	"undead": {"name": "Undead", "hp": 65, "damage": 11, "speed": 0.85, "range": 100,
		"attack_cooldown": 60, "gold_reward": 16, "radius": 10, "color": "#c8c8dc",
		"armor": 0, "magic_resist": 0.15},
	"dark_rider": {"name": "Dark Rider", "hp": 280, "damage": 32, "speed": 2.0, "range": 35,
		"attack_cooldown": 50, "gold_reward": 65, "radius": 13, "color": "#643c8c",
		"armor": 1, "magic_resist": 0.05},
}

# ═══ FALLBACK NEXUS_WAVE_COMPOSITION (level nexus 1-5) ═══
const FALLBACK_WAVE_COMPOSITION: Dictionary = {
	1: ["goblin", "goblin", "goblin"],
	2: ["goblin", "goblin", "goblin", "orc"],
	3: ["goblin", "orc", "goblin", "orc", "undead"],
	4: ["orc", "goblin", "orc", "undead", "goblin", "goblin"],
	5: ["orc", "orc", "undead", "troll", "goblin", "goblin"],
}
## Game.reset: persiapan 300 frame; hero yang mati kembali setelah 600 frame.
const FIRST_WAVE_DELAY := 300.0 / FPS
const HERO_RESPAWN_DELAY := 600.0 / FPS
const WAVE_LANES: Array = ["top", "mid", "bot"]
const WAVE_TEAMS: Array = ["blue", "red"]

# ═══ FALLBACK EKONOMI — paritas _core.py 209-229, 253 ═══
const FALLBACK_ECONOMY: Dictionary = {
	"starting_gold": 350,
	"gold_per_second": 3,
	"gold_per_second_level_bonus": 0.3,
	"gold_per_level_bonus": 100,
	"difficulty_gold_mult": {"easy": 1.25, "normal": 1.0, "hard": 0.75},
	"minion_wave_interval_frames": 1500,
	"minion_spawn_delay_frames": 20,
	"max_heroes_owned": 5,
}

const ECONOMY_PATH := "res://data/economy.json"

# State global (mirip _core.Game)
var level_number: int = 1
var wave_number: int = 0
var gold: int = 1000:
	set(v):
		gold = v
		gold_changed.emit(v)
var is_paused: bool = false
## "playing" | "victory" | "defeat" | "idle" — paritas Game.state; "idle" =
## sedang di menu utama (belum/tidak ada match berjalan).
var state: String = "idle"
## "easy" | "normal" | "hard"
var difficulty: String = "normal"

# ── PROGRESI LEVEL + MENU (paritas _core.py 1578-1584) ──
## True kalau level ini dimulai ULANG padahal sudah pernah ditamatkan
## (pygame: Game(screen, level_number, is_replay=True) dari main.py:576).
## Menentukan reward replay di end_match() (_core.py:2387).
var is_replay: bool = false
## True saat menu utama terbuka (boot + MAIN MENU dari pause/menang-kalah).
## _process gold/wave berhenti; pygame menjalankan menu di state terpisah.
var in_menu: bool = true
## Reward meta yang TERAKHIR diberikan (dibaca HUD; paritas Game.meta_reward_earned)
var meta_reward_earned: int = 0
## Guard anti dobel reward (paritas _meta_reward_granted _core.py:1581/2456)
var _meta_reward_granted: bool = false
## Boss (mini/true) yang dikalahkan di match INI — baru di-unlock gratis
## kalau match dimenangkan (paritas bosses_defeated_this_match _core.py:1594).
var bosses_defeated_this_match: Array = []
## FASE 14: setiap kematian dihitung, tetapi daftar tipe di atas unik.
var bosses_defeated_this_run: int = 0
## REFERENSI ke save, bukan array yang boleh di-clear saat restart/menu.
## Boss dicatat langsung saat mati, TIDAK perlu menunggu kemenangan.
var unlocked_bosses: Array = []
var miniboss_kill_count: int = 0
var trueboss_kill_count: int = 0
## Set ID achievement in-match (Dictionary sebagai set GDScript).
var achievements_unlocked: Dictionary = {}
var world_popups = FloatingTextQueueScript.new()
## Percikan pukulan + ledakan kematian (port `EffectManager.particles` /
## `explosions` `_render.py:615-616`). Digambar `scenes/fx/SparkLayer.gd`;
## di-tick `_process` di bawah (`spark_fx.advance`) persis seperti popup.
var spark_fx = SparkFieldScript.new()
## Tipe hero yang BARU di-unlock gratis dari match ini (paritas
## heroes_unlocked_this_match _core.py:2347 — ditulis _auto_unlock..., DIBACA
## HUD untuk baris "NEW HERO" panel game-over).
var heroes_unlocked_this_match: Array = []
## Skor match (paritas Game.score _core.py:2195 + 2227-2235: gold_reward
## minion/menara/boss yang hancur + 150 per hero merah mati; hero biru
## mati membayar AI — lihat register_hero_death).
var score: int = 0
## Kill minion tim blue match ini (paritas Game.total_kills: minion SAJA).
var total_kills: int = 0
## Counter combo kill minion red (paritas Game.effects.combo_counter —
## ComboCounter pygame _render.py:841, mesin frame @60fps). Dijalankan
## _tick_combo dari _process; harness replay men-step manual.
var combo = ComboCounterScript.new()
## Combo terbesar match ini (paritas Game.max_combo _core.py:1378/1547 —
## dibaca SEBELUM add_kill di loop reward, jadi rantai N kill menghasilkan
## max_combo N-1; dikunci fixture match_scoring).
var max_combo: int = 0
## Flag NEW BEST! panel menang/kalah (paritas Game.new_best_score/
## new_best_time _core.py:1552-1553 — diisi _grant_meta_reward dari
## SaveManager.update_level_stats lalu dibaca HUD game-over).
var new_best_score: bool = false
var new_best_time: bool = false
## Akumulator kadens 60Hz mesin combo (ComboCounter pygame update per
## frame 60fps — bukan per delta bebas).
var _combo_accum: float = 0.0
## Jam dinding mulai match, msec (paritas match_start_time; match_time
## pygame memakai wall-clock TERMASUK pause, jadi tanpa penyesuaian pause).
var match_start_msec: int = 0
## Tab toko yang diminta sekali-buka (mis. SkillBar ITEM FORGE -> "item");
## dikonsumsi ShopPanel._on_shop_changed lalu dikosongkan lagi.
var requested_shop_tab: String = ""

# ── PROGRESI LINTAS-SAVE: daftar hero yang dimiliki pemain ──
## Paritas `Game.purchased_heroes` (_core.py:1596-1604): daftar hero yang
## sudah dibuka PERMANEN oleh pemain — bertambah lewat Hero Shop meta
## (_unlock_hero_in_meta_shop) dan unlock gratis boss yang dikalahkan
## (_auto_unlock_defeated_boss_heroes). BUKAN roster in-match.
##
## Isinya adalah REFERENSI ke array save `unlocked_heroes` (padanan kunci
## pygame `purchased_heroes`), persis seperti pygame yang memegang list
## milik `save_data` — unlock yang terjadi di tengah match langsung
## terbaca tanpa sinkronisasi tambahan.
##
## KOSONG = tidak ada match berjalan, paritas `__main__.game_instance is
## None` di menu utama: `Hero.__init__` pygame memakai 0 unlock di situ.
## JANGAN `clear()` array ini saat kembali ke menu — itu akan menghapus
## unlock pemain di save; `return_to_menu()` melepas ikatannya dengan
## MENGGANTI binding ke array kosong baru.
var purchased_heroes: Array = []

# ── ENEMY SCALING (Hard mode; paritas _core.py:1460 + 1476-1483) ──
## enemy_scaling_enabled = (difficulty == "hard"); multiplier HP/dmg/speed
## musuh (merah) diambil dari levels.json lalu dikali 1.15/1.10/1.0.
var enemy_scaling_enabled: bool = false
var enemy_hp_mult: float = 1.0
var enemy_damage_mult: float = 1.0
var enemy_speed_mult: float = 1.0

# Referensi node yang di-set oleh Main.tscn (lewat GameManagerConnector)
var hero_container: Node
var boss_container: Node
var minion_container: Node
var tower_container: Node
var fx_container: Node

# Nexus (Castle) per tim — diisi Nexus.gd saat _ready
var blue_nexus = null
var red_nexus = null

# Data hasil convert
var economy: Dictionary = {}
var minion_types: Dictionary = {}
var wave_composition_table: Dictionary = {}

# Config dari levels (port dari _core.NEXUS_LEVELS)
var starting_gold: int = 1000
var gold_per_second: float = 3.0

## Gold AI (tim red). pygame: AIPlayer punya saldo sendiri untuk build/upgrade.
var ai_gold: int = 0

# Gelombang minion — paritas _core.MINION_WAVE_INTERVAL = 1500 frame @60fps
@export var waves_enabled: bool = true
@export var wave_interval: float = 25.0
var minion_spawn_delay: float = 20.0 / FPS
var max_heroes_owned: int = 5
## Antrean terpisah per tim; satu komposisi LENGKAP untuk SETIAP lane.
## Tidak ada cap 24: itu dulu memotong wave elite dan menghilangkan bot lane.
var spawn_queues: Dictionary = {"blue": [], "red": []}
var _spawn_timers: Dictionary = {"blue": 0.0, "red": 0.0}
var _hero_respawn_timers: Dictionary = {}

var _gold_timer: float = 0.0
var _gold_income_milli: int = 0
var _wave_timer: float = 0.0
var _aura_timer: float = 0.0
var _hit_stop_active: bool = false
var _hit_stop_until_ms: int = 0
## Basis Engine.time_scale dari setting Game Speed (apply_game_speed) —
## hit-stop menumpuk di atasnya dan watchdog mengembalikan ke nilai ini.
var game_speed_scale: float = 1.0


func _ready():
	# Autoload harus tetap jalan walau SceneTree di-pause (P/ESC dari Main.gd):
	# watchdog Engine.time_scale tinggal di sini. Flag is_paused sudah menahan
	# timer gold/wave, jadi "pause" tetap benar.
	process_mode = Node.PROCESS_MODE_ALWAYS
	load_economy()
	nexus_destroyed.connect(_on_nexus_destroyed)
	hero_died.connect(_on_hero_died)
	# Paritas GameSettings pygame (_system.py:9135/9138 + 9164/9166):
	# game_speed & fps_limit persist di save dan berlaku sejak boot.
	apply_game_speed(SaveManager.get_setting("game_speed", 1.0))
	apply_fps_limit(SaveManager.get_setting("fps_limit", 0.0))


## Game Speed — paritas Game.update (_core.py:1958-1977): pygame >1.0
## menjalankan _update_gameplay() sebanyak int(mult)-1 kali EKSTRA, akibatnya
## 1.5x TIDAK berpengaruh (int(1.5)-1 = 0) — hanya 0.5x/1.0x/2.0x yang beda.
## Quirk itu dipertahankan: nilai >= 1.0 dipetakan lewat rumus yang sama.
## Clamp 0.5..2.0 = set_game_speed (_system.py:9268-9269).
func apply_game_speed(speed: float) -> void:
	var eff := clampf(speed, 0.5, 2.0)
	if eff >= 1.0:
		eff = 1.0 + (int(eff) - 1)
	game_speed_scale = eff
	if not _hit_stop_active:
		Engine.time_scale = game_speed_scale


## FPS Limit — paritas main.py:637 (clock.tick(fps_limit)); 0 = tanpa batas,
## persis konvensi Engine.max_fps Godot.
##
## DITERUSKAN ke AppShell (port baris main.py:620-641, yang menghitung batas
## TIAP frame dari setting + preset kualitas): di perangkat sentuh setting
## pemain hanya boleh MENURUNKAN batas, dan 0 berarti "ikut target kualitas"
## (30 FPS di LOW, 60 selainnya) — bukan tanpa batas. Tanpa penerusan ini,
## slider SETTINGS bisa melangkahi pembatas 30 FPS yang menahan HP kentang.
func apply_fps_limit(fps: float) -> void:
	var shell := get_node_or_null("/root/AppShell")
	if shell != null and shell.has_method("apply_fps_limit"):
		shell.apply_fps_limit(fps)
		return
	# AppShell belum terpasang (boot: GameManager._ready jalan lebih dulu
	# karena urutan autoload) — pakai nilai mentah, AppShell._ready akan
	# menimpanya beberapa milidetik kemudian.
	Engine.max_fps = int(fps)


func load_economy() -> void:
	economy = FALLBACK_ECONOMY.duplicate(true)
	if FileAccess.file_exists(ECONOMY_PATH):
		var f := FileAccess.open(ECONOMY_PATH, FileAccess.READ)
		var parsed = JSON.parse_string(f.get_as_text())
		if parsed is Dictionary:
			economy.merge(parsed, true)
	else:
		push_warning("[GameManager] economy.json belum ada — pakai fallback. "
			+ "Jalankan tools/convert_to_godot.py")
	minion_types = economy.get("minion_types", {})
	if minion_types.is_empty():
		minion_types = FALLBACK_MINION_TYPES.duplicate(true)
	wave_composition_table = economy.get("wave_composition", {})
	if wave_composition_table.is_empty():
		for k in FALLBACK_WAVE_COMPOSITION:
			wave_composition_table[str(k)] = FALLBACK_WAVE_COMPOSITION[k]
	wave_interval = float(economy.get("minion_wave_interval_frames", 1500)) / FPS
	minion_spawn_delay = maxf(1.0 / FPS,
		float(economy.get("minion_spawn_delay_frames", 20)) / FPS)
	max_heroes_owned = maxi(1, int(economy.get("max_heroes_owned", 5)))
	print("[GameManager] ekonomi: %s gold/s · wave tiap %.0fs · %d tipe minion" % [
		format_gold_rate(float(economy.get("gold_per_second", 3))),
		wave_interval, minion_types.size()])


func minion_type_data(minion_type: String) -> Dictionary:
	var d = minion_types.get(minion_type)
	if d is Dictionary:
		return d
	return FALLBACK_MINION_TYPES.get(minion_type, {})


# ══════════════════════════════════════════════════════════
#  EKONOMI (port compute_starting_gold / compute_gold_per_second)
# ══════════════════════════════════════════════════════════

func difficulty_mult(d: String = "") -> float:
	var key := d if d != "" else difficulty
	var mults: Dictionary = economy.get("difficulty_gold_mult",
		FALLBACK_ECONOMY["difficulty_gold_mult"])
	return float(mults.get(key, 1.0))


## (base starting_gold level + 100 × (level-1)) × multiplier kesulitan
func compute_starting_gold(level_config: Dictionary, level_num: int,
		d: String = "") -> int:
	var base := int(level_config.get("starting_gold", 1000))
	var lv := maxi(1, level_num)
	var bonus: float = float(lv - 1) * float(economy.get("gold_per_level_bonus",
		FALLBACK_ECONOMY["gold_per_level_bonus"]))
	return int((float(base) + bonus) * difficulty_mult(d))


## (GOLD_PER_SECOND + 0.3 × (level-1)) × multiplier kesulitan
func compute_gold_per_second(level_num: int, d: String = "") -> float:
	var lv := maxi(1, level_num)
	var bonus: float = float(lv - 1) * float(economy.get("gold_per_second_level_bonus",
		FALLBACK_ECONOMY["gold_per_second_level_bonus"]))
	return (float(economy.get("gold_per_second", 3)) + bonus) * difficulty_mult(d)


## 3.0 -> "3", 5.7 -> "5.7", 3.75 -> "3.8" (paritas _core.format_gold_rate).
## Kanon di HudLayout (banker's rounding bit-eksak); ini delegasi tipis.
static func format_gold_rate(rate: float) -> String:
	return HudLayout.format_gold_rate(rate)


# ── SETTINGS (paritas GameSettings pygame) ──
## Screen shake (GameSettings.screen_shake_enabled). Dikaca dari save agar
## Boss._shake tidak perlu membaca SaveManager tiap frame.
var screen_shake_enabled: bool = true
## Damage numbers (GameSettings.damage_numbers_enabled).
var damage_numbers_enabled: bool = true


## Sinkronkan kedua flag dari save (dipanggil boot + tiap start_level).
func _load_gameplay_settings() -> void:
	screen_shake_enabled = SaveManager.get_setting("screen_shake", 1.0) > 0.5
	damage_numbers_enabled = SaveManager.get_setting(
		"damage_numbers_enabled", 1.0) > 0.5
	world_popups.damage_numbers_enabled = damage_numbers_enabled


func set_screen_shake(enabled: bool) -> void:
	screen_shake_enabled = enabled


func set_damage_numbers(enabled: bool) -> void:
	damage_numbers_enabled = enabled
	# Live: antrean popup yang sedang berjalan ikut berubah (bukan hanya
	# match berikutnya).
	world_popups.damage_numbers_enabled = enabled


func set_difficulty(d: String) -> void:
	if not ["easy", "normal", "hard"].has(d):
		return
	difficulty = d
	# Gold/s mengikuti kesulitan langsung; starting gold hanya saat match mulai.
	gold_per_second = compute_gold_per_second(level_number)
	# Enemy scaling ikut kesulitan (paritas _core.py:1460: aktif hanya "hard").
	# Di pygame difficulty dikunci per run (reset Game); di sini pergantian
	# mid-match (tombol D) hanya memengaruhi unit yang DI-SPAWN berikutnya —
	# minion/boss lama mempertahankan stat spawn-nya (pygame juga menerapkan
	# scaling saat spawn: _core.py:1792 dan 1822).
	var lv_data: Dictionary = BossDB.get_level(level_number)
	enemy_scaling_enabled = (difficulty == "hard")
	if enemy_scaling_enabled:
		enemy_hp_mult = float(lv_data.get("enemy_hp_mult", 1.0)) * 1.15
		enemy_damage_mult = float(lv_data.get("enemy_damage_mult", 1.0)) * 1.10
		enemy_speed_mult = float(lv_data.get("enemy_speed_mult", 1.0))
	else:
		enemy_hp_mult = 1.0
		enemy_damage_mult = 1.0
		enemy_speed_mult = 1.0
	difficulty_changed.emit(difficulty)
	print("[GameManager] difficulty -> %s (gold/s %s)%s" % [
		difficulty, format_gold_rate(gold_per_second),
		" · enemy scaling AKTIF" if enemy_scaling_enabled else ""])


func cycle_difficulty() -> String:
	var order := ["easy", "normal", "hard"]
	var idx := order.find(difficulty)
	set_difficulty(order[(idx + 1) % order.size()])
	return difficulty


# ══════════════════════════════════════════════════════════
#  LOOP
# ══════════════════════════════════════════════════════════

func _process(delta):
	# Watchdog hit-stop DULU: Engine.time_scale tidak boleh bisa "nyangkut" kecil
	_watch_hit_stop()
	if is_paused or in_menu or get_tree().paused:
		return
	if state != "playing":
		return
	# Passive gold (paritas Game: tiap 60 frame, pecahan disimpan di milli)
	_gold_timer += delta
	while _gold_timer >= 1.0:
		_gold_timer -= 1.0
		_gold_income_milli += int(round(gold_per_second * 1000.0))
		var gain: int = _gold_income_milli / 1000
		_gold_income_milli = _gold_income_milli % 1000
		if gain > 0:
			gold += gain
		# _core.Game.update: AI mulai dari STARTING_GOLD, lalu
		# menerima GOLD_PER_SECOND + wave, bukan income pemain × difficulty.
		ai_gold += int(economy.get("gold_per_second", 3)) + maxi(0, wave_number)
	if waves_enabled and get_tree().current_scene != null:
		_update_waves(delta)
	_update_hero_respawns(delta)
	_tick_combo(delta)
	world_popups.advance(delta)
	# Percikan/ledakan ikut kadens frame pygame (EffectManager.update dipanggil
	# sekali per Game.update). Path preview di-tick node-nya sendiri karena
	# state-nya milik scene (jalur lane dibaca dari ArenaMap).
	spark_fx.advance(delta)
	# Aura item (Steel Aegis / Everfrost / Solar Brand / Searbrand)
	_aura_timer += delta
	if _aura_timer >= 0.25:
		_aura_timer = 0.0
		if CombatSystem.has_method("update_auras"):
			CombatSystem.update_auras()


func start_level(lv: int, replay: bool = false):
	level_number = lv
	state = "playing"
	in_menu = false
	is_replay = replay
	# Daftar unlock permanen diikat ulang tiap match dimulai — paritas
	# Game.reset (_core.py:1593-1604) yang membaca save lalu memberi starter.
	bind_purchased_heroes()
	bind_unlocked_bosses()
	var lv_data = BossDB.get_level(lv)
	# paritas Game.reset: gold awal & laju pasif dihitung dari level + difficulty
	starting_gold = compute_starting_gold(lv_data, lv)
	gold_per_second = compute_gold_per_second(lv)
	gold = starting_gold
	ai_gold = int(economy.get("starting_gold", 350))
	_gold_income_milli = 0
	_gold_timer = 0.0
	_reset_wave_state(FIRST_WAVE_DELAY)
	_hero_respawn_timers.clear()
	wave_number = 0
	# ── Meta reward match ini direset (paritas _core.py:1578-1581) ──
	meta_reward_earned = 0
	_meta_reward_granted = false
	bosses_defeated_this_match.clear()
	bosses_defeated_this_run = 0
	miniboss_kill_count = 0
	trueboss_kill_count = 0
	achievements_unlocked.clear()
	world_popups.reset()
	spark_fx.reset()
	_load_gameplay_settings()
	var popup_settings: Dictionary = SaveManager.data.get("settings", {})
	var quality := str(popup_settings.get("quality", "medium"))
	world_popups.max_damage_numbers = 8 if quality == "low" else (16 if quality == "medium" else 32)
	# ── Skor/kill/timer/unlock match (paritas Game.reset/score) ──
	score = 0
	total_kills = 0
	# Combo + flag NEW BEST direset tiap match (paritas Game.reset
	# _core.py:1547 + 1552-1553).
	combo.reset()
	max_combo = 0
	new_best_score = false
	new_best_time = false
	_combo_accum = 0.0
	match_start_msec = Time.get_ticks_msec()
	heroes_unlocked_this_match.clear()
	requested_shop_tab = ""
	# ── ENEMY SCALING (paritas _core.py:1460 + 1476-1483): hanya Hard ──
	enemy_scaling_enabled = (difficulty == "hard")
	if enemy_scaling_enabled:
		enemy_hp_mult = float(lv_data.get("enemy_hp_mult", 1.0)) * 1.15
		enemy_damage_mult = float(lv_data.get("enemy_damage_mult", 1.0)) * 1.10
		enemy_speed_mult = float(lv_data.get("enemy_speed_mult", 1.0))
	else:
		enemy_hp_mult = 1.0
		enemy_damage_mult = 1.0
		enemy_speed_mult = 1.0
	# Hook BGM per level (levels.json["bgm_track"]; pygame main.py:521).
	# AudioManager no-op + log kalau aset wav belum disalin converter.
	AudioManager.play_bgm(str(lv_data.get("bgm_track", "bgm_battle.wav")))
	# Ambient loop hutan (paritas main.py:164 sound_mgr.play_ambient(
	# 'ambient_forest', volume_mult=0.8)). Kanal terpisah dari BGM, jadi
	# musik dan suara lingkungan berbunyi bersamaan seperti di pygame.
	AudioManager.play_ambient()
	print("[GameManager] Start Level %d%s — gold %d (%s/s, %s)%s" % [
		lv, " (replay)" if replay else "", gold, format_gold_rate(gold_per_second),
		difficulty, " · enemy scaling x%.2f HP" % enemy_hp_mult if enemy_scaling_enabled else ""])
	level_started.emit(lv)
	# Wave 1 TIDAK dibuat selama intro. Countdown 5 detik baru berjalan
	# setelah cinematic dilewati, persis Game.reset + update_waves pygame.


## Mulai ulang match yang sama (R setelah menang/kalah, atau ENTER saat kalah).
## Replay level yang sudah ditamatkan -> is_replay=true (paritas main.py:576:
## Game(screen, level_number=..., is_replay=True)) sehingga end_match()
## membayar reward replay, bukan reward menang pertama.
func restart_match() -> void:
	print("[GameManager] replay level %d" % level_number)
	start_level(level_number, true)


## Lanjut ke level berikutnya setelah VICTORY (ENTER). Paritas
## levels/level_data.py get_next_level (2340-2346): level+1 kalau masih ada
## konfigurasinya, kalau terakhir -> balik False dan pemain tinggal replay.
func next_level() -> bool:
	var nxt := next_level_number(level_number)
	if nxt <= 0:
		print("[GameManager] sudah level terakhir (%d) — tidak ada level berikutnya" % level_number)
		return false
	print("[GameManager] lanjut ke level %d" % nxt)
	start_level(nxt, false)
	return true


## Nomor level berikutnya (0 = tidak ada) — paritas get_next_level.
func next_level_number(after: int = -1) -> int:
	var cur := level_number if after < 0 else after
	var nxt := cur + 1
	var cfg: Dictionary = BossDB.get_level(nxt)
	if cfg.is_empty():
		return 0
	return nxt


## Total level (paritas levels/level_data.py get_level_count).
func level_count() -> int:
	return BossDB.levels.size()


## Kunci level di LEVEL_SELECT (paritas is_level_unlocked level_data.py:2318-2337):
## unlock_after_level == null -> selalu terbuka; selain itu butuh level itu
## ada di SaveManager.completed_levels.
func is_level_unlocked(level_num: int) -> bool:
	var cfg: Dictionary = BossDB.get_level(level_num)
	if cfg.is_empty():
		return false
	var required = cfg.get("unlock_after_level")
	if required == null:
		return true
	return SaveManager.is_level_completed(int(required))


## Kembali ke menu utama dari dalam match (PAUSE -> MAIN MENU, atau ESC
## setelah menang/kalah; paritas return_to_menu_requested main.py:582-586).
func return_to_menu() -> void:
	in_menu = true
	is_paused = false
	state = "idle"
	wave_number = 0
	_reset_wave_state()
	_hero_respawn_timers.clear()
	shop_open = false
	# Lepas ikatan daftar unlock (paritas main.py:587 `game_instance = None`,
	# yang membuat Hero.__init__ memakai 0 unlock di luar match). MENGGANTI
	# binding, BUKAN clear(): array yang lama milik save pemain.
	purchased_heroes = []
	unlocked_bosses = []
	world_popups.reset()
	spark_fx.reset()
	AudioManager.stop_bgm()
	# Ambient ikut mati di menu — pygame memulainya sekali di main() dan
	# hanya hidup selama sesi match; di sini pasangan stop-nya eksplisit.
	AudioManager.stop_ambient()
	print("[GameManager] kembali ke menu utama")


# ══════════════════════════════════════════════════════════
#  PROGRESI LINTAS-SAVE — daftar hero yang dimiliki pemain
#  (port Game.purchased_heroes _core.py:1596-1604 +
#   hero_balance.boss_unlocks_for_purchases hero_balance.py:257-260)
# ══════════════════════════════════════════════════════════

## Ikat `purchased_heroes` ke array save `unlocked_heroes` (kunci Godot,
## padanan `purchased_heroes` pygame) lalu terapkan AUTO-GRANT STARTER:
##
##     self.purchased_heroes = self.save_data.get('purchased_heroes', [])
##     if not self.purchased_heroes:
##         self.purchased_heroes.append('kaizen')
##         self.save_data['purchased_heroes'] = self.purchased_heroes
##         SaveManager.save(self.save_data)
##
## Save pemain TIDAK pernah dimigrasi/dihapus di sini: unlock lama dipakai
## apa adanya, dan penulisan hanya terjadi kalau starter benar-benar baru
## di-grant. `persist=false` dipakai harness paritas supaya tes tidak
## menulis berkas save sama sekali.
func bind_purchased_heroes(persist: bool = true) -> void:
	var arr = SaveManager.data.get("unlocked_heroes")
	if not (arr is Array):
		arr = []
		SaveManager.data["unlocked_heroes"] = arr
	purchased_heroes = arr
	if purchased_heroes.is_empty():
		purchased_heroes.append(HeroDB.STARTER_HEROES[0])
		print("[STARTER] %s granted as starter hero!" % HeroDB.STARTER_HEROES[0])
		if persist:
			SaveManager.save()


## Game.reset: unlocked_bosses milik save, terpisah dari purchased_heroes.
func bind_unlocked_bosses() -> void:
	var arr = SaveManager.data.get("unlocked_bosses", [])
	if not (arr is Array):
		arr = []
	SaveManager.data["unlocked_bosses"] = arr
	unlocked_bosses = arr


## Jumlah hero NON-starter yang dimiliki pemain — input catch-up hero.
## Paritas hero_balance.boss_unlocks_for_purchases: `len()` polos atas
## daftar save (entri kembar ikut terhitung; SaveManager sendiri menolak
## duplikat saat menulis), starter tidak pernah dihitung.
func boss_unlocks_for_purchases(purchased) -> int:
	if not (purchased is Array):
		return 0
	var n := 0
	for hero_type in purchased:
		if not (str(hero_type) in HeroDB.STARTER_HEROES):
			n += 1
	return maxi(0, n)


## Dibaca `Hero._catchup_unlocks()` saat unit dibuat. Di luar match daftar
## ini kosong (tidak diikat), jadi hasilnya 0 — paritas `game_instance is
## None` pygame yang membuat catch-up starter memakai bonus PENUH.
func catchup_unlocks() -> int:
	return boss_unlocks_for_purchases(purchased_heroes)


func _reset_wave_state(delay: float = 0.0) -> void:
	_wave_timer = delay
	for team in WAVE_TEAMS:
		spawn_queues[team].clear()
		_spawn_timers[team] = 0.0


func can_start_wave() -> bool:
	if state != "playing" or in_menu or is_paused or get_tree().paused:
		return false
	if _wave_timer > 0.000001:
		return false
	for team in WAVE_TEAMS:
		if not spawn_queues[team].is_empty() or count_alive("minions", team) > 0:
			return false
	return true


## Countdown menahan wave BERIKUTNYA, bukan antrean wave yang sedang keluar.
## Minion wave lama harus bersih dahulu (Game.update_waves pygame).
func _update_waves(delta: float) -> void:
	_wave_timer = maxf(0.0, _wave_timer - delta)
	for team in WAVE_TEAMS:
		_spawn_timers[team] = float(_spawn_timers[team]) + delta
		# Clamp BEFORE a new queue is populated: idle time permits its first
		# minion immediately, not a whole-wave burst or a shortened second gap.
		if spawn_queues[team].is_empty():
			_spawn_timers[team] = minf(float(_spawn_timers[team]), minion_spawn_delay)
	if can_start_wave():
		next_wave()
	for team in WAVE_TEAMS:
		while not spawn_queues[team].is_empty() \
				and float(_spawn_timers[team]) + 0.000001 >= minion_spawn_delay:
			_spawn_timers[team] = maxf(0.0, float(_spawn_timers[team]) - minion_spawn_delay)
			_spawn_wave_minion(team, spawn_queues[team].pop_front())
		if spawn_queues[team].is_empty():
			_spawn_timers[team] = minf(float(_spawn_timers[team]), minion_spawn_delay)


func next_wave() -> bool:
	if not can_start_wave():
		return false
	wave_number += 1
	_wave_timer = wave_interval
	for nexus in [blue_nexus, red_nexus]:
		if is_instance_valid(nexus):
			nexus.set_wave(wave_number)
	_auto_scale_ai_nexus()
	for team in WAVE_TEAMS:
		var composition := wave_composition(wave_number, team)
		for lane in WAVE_LANES:
			for minion_type in composition:
				spawn_queues[team].append({"type": minion_type, "lane": lane})
	AudioManager.play_sfx("wave_start", 0.6)
	print("[GameManager] Wave %d" % wave_number)
	wave_started.emit(wave_number)
	return true


## _auto_scale_ai_castle: Lv2/3/4/5 pada wave 4/7/10/13, tanpa biaya.
func _auto_scale_ai_nexus() -> void:
	if not is_instance_valid(red_nexus):
		return
	var target_level := mini(5, 1 + maxi(0, wave_number - 1) / 3)
	while red_nexus.level < target_level and red_nexus.can_upgrade():
		red_nexus.upgrade()


## NEXUS_WAVE_COMPOSITION diindeks LEVEL CASTLE, BUKAN nomor wave.
## Tambahan elite per wave persis Game._get_wave_composition (_core.py).
func wave_composition(wave: int, team: String = "blue") -> Array:
	var nexus = blue_nexus if team == "blue" else red_nexus
	var castle_level := int(nexus.level) if is_instance_valid(nexus) else 1
	var base: Array = wave_composition_table.get(str(castle_level),
		FALLBACK_WAVE_COMPOSITION.get(castle_level, FALLBACK_WAVE_COMPOSITION[1]))
	var result := base.duplicate()
	if wave >= 13:
		result.append_array(["troll", "troll", "dark_rider", "dark_rider", "undead"])
	elif wave >= 10:
		result.append_array(["troll", "dark_rider", "undead"])
	elif wave >= 7:
		result.append_array(["orc", "undead"])
	elif wave >= 4:
		result.append("orc")
	return result


## Hanya level nexus TIM SENDIRI yang mengubah stat minion.
func minion_scale_for(team: String = "blue") -> float:
	var nexus = blue_nexus if team == "blue" else red_nexus
	return float(nexus.minion_scale) if is_instance_valid(nexus) else 1.0


func _spawn_wave_minion(team: String, entry: Dictionary) -> void:
	var lane := str(entry["lane"])
	var path := PackedVector2Array()
	var arena = get_tree().get_first_node_in_group("arena_map")
	if arena != null:
		path = arena.get_lane_path(lane)
	var pos := base_spawn_point(team)
	if not path.is_empty():
		pos = path[0] if team == "blue" else path[path.size() - 1]
	var minion = spawn_minion(str(entry["type"]), team, pos,
		minion_scale_for(team), lane, path)
	var nexus = blue_nexus if team == "blue" else red_nexus
	minion.ai_level = int(nexus.level) if is_instance_valid(nexus) else 1
	if team == "red" and enemy_scaling_enabled:
		minion.apply_enemy_scaling(enemy_hp_mult, enemy_damage_mult, enemy_speed_mult)


# ══════════════════════════════════════════════════════════
#  HERO RESPAWN — satu hero, bukan reset seluruh arena
# ══════════════════════════════════════════════════════════

func _on_hero_died(hero: Node) -> void:
	if state != "playing" or in_menu or _hero_respawn_timers.has(hero):
		return
	_hero_respawn_timers[hero] = HERO_RESPAWN_DELAY
	if selected_hero == hero:
		clear_selection()


func hero_respawn_remaining(hero: Node) -> float:
	return float(_hero_respawn_timers.get(hero, 0.0))


func _update_hero_respawns(delta: float) -> void:
	for hero in _hero_respawn_timers.keys():
		if not is_instance_valid(hero) or not hero.is_dead:
			_hero_respawn_timers.erase(hero)
			continue
		var remaining := float(_hero_respawn_timers[hero]) - delta
		if remaining <= 0.000001:
			_hero_respawn_timers.erase(hero)
			hero.respawn()
			hero_respawned.emit(hero)
		else:
			_hero_respawn_timers[hero] = remaining


# ══════════════════════════════════════════════════════════
#  GOLD
# ══════════════════════════════════════════════════════════

func spend_gold(amount: int) -> bool:
	if gold >= amount:
		gold -= amount
		return true
	return false


func ai_spend(amount: int) -> bool:
	if ai_gold >= amount:
		ai_gold -= amount
		return true
	return false


## Loop reward Game.update pygame — kematian MINION dinilai dari TIM KORBAN,
## bukan tim pembunuh (_core.py:2196-2216): minion RED yang mati oleh damage
## apa pun (termasuk netral tanpa sumber) tetap membayar gold+skor ke pemain,
## memunculkan popup gold +nG (EffectManager.add_gold_popup → FloatingTextQueue
## FASE 14), menambah total_kills, dan menyalakan combo; minion biru membayar
## AI TANPA popup. Urutan operasi persis pygame: gold → score → popup →
## total_kills → max_combo (dibaca SEBELUM add_kill) → add_kill.
## Dipanggil Minion.die(); flag per instans = `_rewarded` pygame
## (kunci anti pembayaran ganda — kematian yang sama tak boleh membayar dua
## kali walau die()/callback dipanggil ulang).
func register_minion_death(minion) -> void:
	if not is_instance_valid(minion) or bool(minion.get("reward_processed")):
		return
	minion.reward_processed = true
	var reward := int(minion.get("gold_reward"))
	if str(minion.get("team")) == "red":
		gold += reward
		score += reward
		# add_gold_popup(m.x, m.y, gold_reward) — offset -10/warna/velocity/
		# lifetime 50 hidup di FloatingTextQueue; piksel font di WorldPopups.
		add_gold_popup(minion.global_position.x, minion.global_position.y,
			reward)
		total_kills += 1
		# Combo terbesar disimpan untuk layar statistik — DIBACA SEBELUM
		# add_kill (paritas _core.py:2209-2214; quirk: rantai N kill
		# menghasilkan max_combo N-1).
		if combo.count > max_combo:
			max_combo = combo.count
		combo.add_kill()
	else:
		ai_gold += reward


## Loop reward hero (_core.py:2227-2235): +150 FLAT ke tim lawan korban —
## hero RED mati (dibunuh apa pun) -> gold+skor pemain; hero biru mati ->
## saldo AI. TIDAK menyalakan combo (combo hanya kill minion red) dan
## tidak bergantung siapa pembunuhnya. Dipanggil Hero.die(); flag per
## instans = `_rewarded` pygame (dibuka ulang saat respawn, Hero.gd).
const HERO_KILL_REWARD := 150


func register_hero_death(hero) -> void:
	if not is_instance_valid(hero) or bool(hero.get("reward_processed")):
		return
	hero.reward_processed = true
	if str(hero.get("team")) == "red":
		gold += HERO_KILL_REWARD
		score += HERO_KILL_REWARD
	else:
		ai_gold += HERO_KILL_REWARD


## Satu frame pygame untuk mesin combo (ComboCounter.update dipanggil
## EffectManager.update sekali per Game.update @60fps). _process memanggil
## ini dengan akumulator supaya kadens tetap 60Hz di refresh rate berapa
## pun; harness replay memanggilnya langsung dengan 1/60 per frame script.
func _tick_combo(delta: float) -> void:
	_combo_accum += delta
	while _combo_accum >= 1.0 / FPS:
		_combo_accum -= 1.0 / FPS
		combo.update()


## Paritas EffectManager.unlock_achievement (_render.py:813): antri popup
## achievement di layar arena (FX peta). Dipancarkan sebagai signal —
## node FX HUD yang subscribe dan menggambar.
func unlock_achievement(title: String, description: String,
		icon: String = "star") -> void:
	achievement_unlocked.emit(title, description, icon)


## Loop reward Game.update pygame — kematian MENARA juga dinilai dari TIM
## KORBAN, bukan tim pembunuh (_core.py:2218-2227): menara RED hancur oleh
## damage apa pun (hero biru, sumber netral/tanpa killer, bahkan tim sendiri)
## membayar gold+skor pemain; menara biru membayar AI. TIDAK ada popup gold
## untuk menara (pygame tidak memanggil add_gold_popup di blok ini) dan
## total_kills TIDAK naik (pygame hanya menghitung minion). Dipanggil
## Tower.die(); flag per instans = `_rewarded` pygame (anti pembayaran ganda).
## `red_towers_destroyed` (syarat true boss, >= 6) dinaikkan Main lewat
## signal tower_destroyed — sekali per die(), sama satu-nya dengan transaksi
## reward ini.
func register_tower_death(tower) -> void:
	if not is_instance_valid(tower) or bool(tower.get("reward_processed")):
		return
	tower.reward_processed = true
	var reward := int(tower.get("gold_reward"))
	if str(tower.get("team")) == "red":
		gold += reward
		score += reward
	else:
		ai_gold += reward


## Detik sejak match mulai (wall-clock; paritas time.time()-match_start_time).
func match_time_seconds() -> int:
	return int(maxi(0, Time.get_ticks_msec() - match_start_msec) / 1000)


# ══════════════════════════════════════════════════════════
#  SPAWN
# ══════════════════════════════════════════════════════════

func spawn_hero(hero_type: String, team: String, pos: Vector2):
	var hero_scene = preload("res://scenes/hero/Hero.tscn")
	var hero = hero_scene.instantiate()
	hero.hero_type = hero_type
	hero.team = team
	hero.position = pos
	(container_or_root(hero_container)).add_child(hero)
	return hero


func spawn_boss(boss_type: String, team: String, pos: Vector2):
	var boss_scene = preload("res://scenes/boss/Boss.tscn")
	var boss = boss_scene.instantiate()
	boss.boss_type = boss_type
	boss.team = team
	boss.position = pos
	(container_or_root(boss_container)).add_child(boss)
	boss_spawned.emit(boss_type)
	return boss


func spawn_minion(minion_type: String, team: String, pos: Vector2,
		scale_mult: float = 1.0, lane: String = "mid",
		lane_path: PackedVector2Array = PackedVector2Array()) -> Node2D:
	var minion_scene = preload("res://scenes/minion/Minion.tscn")
	var m = minion_scene.instantiate()
	m.minion_type = minion_type
	m.team = team
	m.lane = lane
	m.lane_path = lane_path
	m.position = pos
	if scale_mult != 1.0 and "stat_scale" in m:
		m.stat_scale = scale_mult
	(container_or_root(minion_container)).add_child(m)
	return m


func spawn_tower(team: String, pos: Vector2, lane: String = "mid",
		tower_kind: String = "outer", tower_type: String = "archer",
		level: int = 1):
	var tower_scene = preload("res://scenes/tower/Tower.tscn")
	var t = tower_scene.instantiate()
	t.team = team
	t.lane = lane
	t.tower_kind = tower_kind
	t.tower_type = tower_type
	t.level = level
	t.position = pos
	t.is_player_built = (team == "blue")
	(container_or_root(tower_container)).add_child(t)
	return t


func spawn_nexus(team: String, pos: Vector2):
	var nexus_scene = preload("res://scenes/base/Nexus.tscn")
	var n = nexus_scene.instantiate()
	n.team = team
	n.position = pos
	# Nexus itu struktur, jadi satu container dengan menara (digambar di belakang
	# unit) — bukan di Bosses yang digambar paling depan.
	(container_or_root(tower_container)).add_child(n)
	return n


## FX (peluru, damage number) ditaruh di CanvasLayer FX kalau ada
func attach_fx(node: Node) -> void:
	var host: Node = fx_container
	if host == null or not is_instance_valid(host):
		host = get_tree().current_scene
	if host == null:
		host = get_tree().root
	host.add_child(node)


## Container dari Main.tscn bisa belum terpasang (scene lain / sebelum Connector
## jalan). Jangan pernah null-crash: fallback ke current_scene, lalu root.
func container_or_root(container: Node) -> Node:
	if container != null and is_instance_valid(container):
		return container
	var scene := get_tree().current_scene
	if scene != null:
		return scene
	return get_tree().root


func count_alive(group: String, team: String) -> int:
	var tree := get_tree()
	if tree == null:
		return 0
	var n := 0
	for node in tree.get_nodes_in_group(group):
		if is_instance_valid(node) and node.get("team") == team and not bool(node.get("is_dead")):
			n += 1
	return n


# ══════════════════════════════════════════════════════════
#  NEXUS / MENANG-KALAH
# ══════════════════════════════════════════════════════════

func register_nexus(nexus) -> void:
	var team := str(nexus.get("team"))
	if team == "blue":
		blue_nexus = nexus
	else:
		red_nexus = nexus
	nexus.set_wave(wave_number)


func unregister_nexus(nexus) -> void:
	if blue_nexus == nexus:
		blue_nexus = null
	if red_nexus == nexus:
		red_nexus = null


func _on_nexus_destroyed(team: String, killer_team: String) -> void:
	if state != "playing":
		return
	# Radiant (blue) hancur = kalah; Dire (red) hancur = menang
	end_match(team == "red", killer_team)


func end_match(victory: bool, killer_team: String = "") -> void:
	if state != "playing":
		return
	state = "victory" if victory else "defeat"
	_grant_meta_reward(victory)
	AudioManager.stop_bgm()
	AudioManager.stop_ambient()
	AudioManager.play_sfx("victory" if victory else "defeat")
	print("[GameManager] %s — %s menang (meta reward %d gold)" % [
		state.to_upper(), killer_team if killer_team != "" else ("blue" if victory else "red"),
		meta_reward_earned])
	game_over.emit(victory)


## Port _grant_meta_reward (_core.py:2365-2456). KEBIJAKAN REWARD (flat):
##   - Kalah                          : 0 gold
##   - Menang pertama kali level ini  : meta_gold_reward_win  (default 3000)
##   - Replay menang (pertama kali)   : meta_gold_reward_replay (1500, SEKALI)
##   - Replay menang berikutnya       : meta_gold_reward_replay_repeat (200, unlimited)
## Semua ditulis ke save kunci "meta_gold" (bukan "gold"), di-guard
## _meta_reward_granted supaya nexus ganda tidak membayar dua kali.
func _grant_meta_reward(victory: bool) -> void:
	if _meta_reward_granted:
		return
	var reward := 0
	var cfg: Dictionary = BossDB.get_level(level_number)
	if not victory:
		# Kalah: pygame membaca meta_gold_reward_lose dari config level
		# (_core.py:2378-2380 pola cfg.get yang sama dengan jalur menang),
		# BUKAN angka 0 mati. Saat ini 54/54 level memang bernilai 0, tapi
		# meng-hardcode-nya membuat Godot diam-diam menyimpang begitu ada
		# satu level pygame yang memberi hadiah hiburan saat kalah.
		reward = int(cfg.get("meta_gold_reward_lose", 0))
	if victory:
		var win_reward := int(cfg.get("meta_gold_reward_win", 3000))
		var replay_reward := int(cfg.get("meta_gold_reward_replay", 1500))
		# default 200 = META_REPLAY_REPEAT_REWARD (_core.py:75)
		var repeat_reward := int(cfg.get("meta_gold_reward_replay_repeat", 200))
		var replay_key := str(level_number)
		if not (SaveManager.data["replay_reward_counts"] is Dictionary):
			SaveManager.data["replay_reward_counts"] = {}
		var replay_counts: Dictionary = SaveManager.data["replay_reward_counts"]
		var replay_count := int(replay_counts.get(replay_key, 0))
		# "replay" = sengaja mengulang (is_replay) ATAU level ini memang sudah
		# pernah ditamatkan (paritas _core.py:2387-2389).
		if is_replay or SaveManager.is_level_completed(level_number):
			reward = replay_reward if replay_count == 0 else repeat_reward
			replay_counts[replay_key] = replay_count + 1
		else:
			reward = win_reward
	meta_reward_earned = reward
	SaveManager.data["meta_gold"] = SaveManager.meta_gold() + reward

	if victory:
		# ═══ AUTO-UNLOCK HERO BOSS YANG DIKALAHKAN (GRATIS) ═══
		# Paritas _auto_unlock_defeated_boss_heroes (_core.py:2322-2355, dipanggil
		# dari _grant_meta_reward 2406): boss yang mati di match ini masuk
		# unlocked_heroes HANYA kalau castle musuh juga jatuh; unlocked_bosses
		# sudah dicatat saat kematian (register_boss_death).
		_auto_unlock_defeated_boss_heroes()
		# Tandai level tamat (paritas 2408-2414) -> level berikutnya (yang
		# memasang unlock_after_level = level ini) terbuka di LEVEL_SELECT.
		SaveManager.complete_level(level_number)
	# ═══ SAVE LEVEL STATS (paritas _core.py:2436-2453) ═══
	# best per level + flag NEW BEST! — ditulis MENANG ATAU KALAH (attempts/
	# playtime/kills/combo kumulatif selalu naik; best hanya saat menang).
	var match_time := match_time_seconds()
	var result: Dictionary = SaveManager.update_level_stats(
		SaveManager.data, level_number, {
			"won": victory,
			"score": score,
			"time_seconds": match_time,
			"kills": total_kills,
			"combo": max_combo,
			"playtime_seconds": match_time,
		})
	new_best_score = bool(result["is_new_best_score"])
	new_best_time = bool(result["is_new_best_time"])
	SaveManager.save()
	_meta_reward_granted = true


## Port _auto_unlock_defeated_boss_heroes (_core.py:2322): boss (mini/true)
## yang dikalahkan di match yang DIMENANGKAN langsung jadi hero milik pemain
## tanpa memotong meta gold — di Hero Shop statusnya "OWNED".
func _auto_unlock_defeated_boss_heroes() -> void:
	var newly: Array = []
	for boss_type in bosses_defeated_this_match:
		var bt := str(boss_type)
		SaveManager.unlock_boss(bt)
		if not SaveManager.is_unlocked(bt):
			SaveManager.unlock_hero(bt)
			newly.append(bt)
	# Selalu ditulis (bahkan kosong) — paritas _core.py:2347.
	heroes_unlocked_this_match = newly.duplicate()
	if not newly.is_empty():
		var names: Array = []
		for bt in newly:
			names.append(str(HeroDB.get_hero(bt).get("name", bt)))
		print("[HERO UNLOCK] gratis karena castle musuh jatuh: %s" % ", ".join(names))
		# Popup achievement di layar arena (paritas _core.py:2356-2361):
		# judul tetap, deskripsi = daftar nama + " now FREE in Hero Shop!",
		# ikon skull. Baris teks panel game-over tetap dari Fase 12.
		unlock_achievement("NEW HERO UNLOCKED!",
			"%s now FREE in Hero Shop!" % ", ".join(names), "skull")


## Blok Game.update _core.py:2113-2163. Hanya boss mati+defeated;
## flag per instans menggantikan konsumsi active_boss pygame (node Godot
## masih hidup selama tween kematian). Tipe yang sama boleh muncul lagi,
## tetapi callback/tick ganda untuk instans yang sama tidak boleh membayar.
func register_boss_death(boss) -> void:
	if not is_instance_valid(boss) or not boss.is_dead or not boss.defeated \
			or boss.reward_processed:
		return
	boss.reward_processed = true
	_process_boss_kill(boss)
	# Pembayar SELALU pemain, bukan tim pembunuh atau tim boss. Tidak ada
	# combo/total_kills/meta_gold di sini — hanya gold + score in-match.
	gold += boss.gold_reward
	score += boss.gold_reward
	add_gold_popup(boss.global_position.x, boss.global_position.y, boss.gold_reward)
	bosses_defeated_this_run += 1
	if not bosses_defeated_this_match.has(boss.boss_type):
		bosses_defeated_this_match.append(boss.boss_type)
	if not unlocked_bosses.has(boss.boss_type):
		unlocked_bosses.append(boss.boss_type)
		var prefix := "TRUE BOSS" if boss.boss_class == "true" else "BOSS"
		var description := "%s already owned!" % boss.display_name \
			if purchased_heroes.has(boss.boss_type) else \
			"Destroy the enemy castle to unlock %s for FREE!" % boss.display_name
		unlock_achievement("%s: %s Defeated!" % [prefix, boss.display_name],
			description, "skull")
		SaveManager.data["unlocked_bosses"] = unlocked_bosses
		SaveManager.save()
	# EffectManager.register_kill pygame = NO-OP (kill feed dihapus).
	# Main melepas active_boss dan mencoba antrean mini berikutnya.
	boss_defeated.emit(boss)
	# BossDeathFX langsung pause setelah transaksi ini. Tetap selesaikan
	# satu tick efek frame kematian, seperti ekor Game.update pygame.
	_tick_combo(1.0 / FPS)
	world_popups.tick()
	spark_fx.tick()
	boss_reward_effects_tick.emit()


## _killer_is_hero: tidak ada syarat masih hidup! Proyektil/DoT dari hero
## yang sudah mati tetap berhak mendapat atribusi. team SUMBER, bukan
## from_team argumen damage, adalah acuan pemeriksaan lawan.
func _killer_is_hero(killer, victim) -> bool:
	return is_instance_valid(killer) and killer != victim \
		and "hero_type" in killer and "skills" in killer \
		and str(killer.get("team")) != str(victim.get("team"))


## _process_boss_kill pygame: hero lawan dari SEMUA tim dapat kills;
## hanya hero BLUE menghidupkan counter+popup SLAYER, per kelas boss.
func _process_boss_kill(boss) -> void:
	var killer = boss.killed_by
	if not _killer_is_hero(killer, boss):
		return
	killer.kills = int(killer.get("kills")) + 1
	if str(killer.get("team")) != "blue":
		return
	if boss.boss_class == "true":
		trueboss_kill_count += 1
		_unlock_achievement("trueboss_kill_%d" % trueboss_kill_count,
			"TRUE BOSS SLAYER!", "%s slew TRUE BOSS %s" % [
				killer.display_name, boss.display_name], "skull",
			boss.global_position + Vector2(0, -40))
	else:
		miniboss_kill_count += 1
		_unlock_achievement("miniboss_kill_%d" % miniboss_kill_count,
			"MINI BOSS SLAYER!", "%s slew %s" % [
				killer.display_name, boss.display_name], "skull",
			boss.global_position + Vector2(0, -40))


## _unlock_achievement: dedup ID hanya selama match, popup arena + teks
## floating di lokasi kejadian, sound ui_upgrade 0.5. TIDAK dipanggil dari
## kematian hero biasa: popup HERO SLAYER sudah dihapus oleh pemilik game.
func _unlock_achievement(id: String, title: String, description: String,
		icon: String = "star", map_position = null) -> void:
	if achievements_unlocked.has(id):
		return
	achievements_unlocked[id] = true
	unlock_achievement(title, description, icon)
	if map_position != null:
		world_popups.add_slayer_text(map_position.x, map_position.y, title)
	AudioManager.play_sfx("ui_upgrade", 0.5)


func add_gold_popup(x: float, y: float, amount: int) -> void:
	world_popups.add_gold_popup(x, y, amount)
	gold_popup_added.emit(x, y, amount)


func nexus_hp(team: String) -> Array:
	var nexus = blue_nexus if team == "blue" else red_nexus
	if nexus == null or not is_instance_valid(nexus):
		return [0.0, 1.0, 0.0, 0.0]
	return [float(nexus.get("hp")), float(nexus.get("max_hp")),
		float(nexus.get("shield")), float(nexus.get("shield_max"))]


# ══════════════════════════════════════════════════════════
#  HIT-STOP & PAUSE
# ══════════════════════════════════════════════════════════

## Dipanggil Hero/Boss; TIDAK await di node unit (lihat catatan di bawah)
func request_hit_stop(duration: float = 0.03, scale: float = 0.05) -> void:
	if _hit_stop_active:
		return
	_hit_stop_active = true
	_hit_stop_until_ms = Time.get_ticks_msec() + maxi(5, int(duration * 1000.0))
	Engine.time_scale = scale


func _watch_hit_stop() -> void:
	if not _hit_stop_active:
		return
	if Time.get_ticks_msec() >= _hit_stop_until_ms:
		_hit_stop_active = false
		# Kembali ke BASIS game speed dari settings, bukan 1.0 keras
		# (paritas Game.update pygame yang selalu membaca GameSettings).
		Engine.time_scale = game_speed_scale


## Dipanggil Main.gd (P / ESC). Yang membekukan simulasi adalah SceneTree, jadi
## flag ini cuma status untuk yang butuh tahu (mis. HUD / audio).
func set_paused(value: bool) -> void:
	is_paused = value


# ══════════════════════════════════════════════════════════
#  SELEKSI & TOKO
#  (port Game.selected_tower / selected_hero / build_slots / try_build_tower /
#   shop_open — sebelumnya tidak ada sama sekali di versi Godot)
# ══════════════════════════════════════════════════════════

## Slot bangun menara: [{pos, team, lane, taken, tower}] — diisi Main.gd dari
## lane path (paritas Game._generate_build_slots_from_lanes)
var build_slots: Array = []
var selected_hero = null
var selected_tower = null
var selected_nexus = null
## Index ke build_slots yang sedang dipilih (-1 = tidak ada)
var selected_slot: int = -1
var shop_open: bool = false


func clear_build_slots() -> void:
	build_slots.clear()
	selected_slot = -1


func add_build_slot(pos: Vector2, slot_team: String, lane: String) -> int:
	build_slots.append({"pos": pos, "team": slot_team, "lane": lane,
		"taken": false, "tower": null})
	return build_slots.size() - 1


func slot(index: int) -> Dictionary:
	if index < 0 or index >= build_slots.size():
		return {}
	return build_slots[index]


func free_slots_for(slot_team: String) -> Array:
	var out: Array = []
	for i in range(build_slots.size()):
		var s: Dictionary = build_slots[i]
		if str(s["team"]) == slot_team and not bool(s["taken"]):
			out.append(i)
	return out


func select_hero(hero) -> void:
	selected_hero = hero
	selected_tower = null
	selected_nexus = null
	selected_slot = -1
	selection_changed.emit()


func select_tower(tower) -> void:
	selected_tower = tower
	selected_hero = null
	selected_nexus = null
	selected_slot = -1
	selection_changed.emit()


func select_nexus(nexus) -> void:
	selected_nexus = nexus
	selected_hero = null
	selected_tower = null
	selected_slot = -1
	selection_changed.emit()


func select_slot_index(index: int) -> void:
	selected_slot = index
	selected_hero = null
	selected_tower = null
	selected_nexus = null
	selection_changed.emit()


func clear_selection() -> void:
	selected_hero = null
	selected_tower = null
	selected_nexus = null
	selected_slot = -1
	selection_changed.emit()


func toggle_shop() -> void:
	shop_open = not shop_open
	shop_changed.emit()


func open_shop() -> void:
	if not shop_open:
		shop_open = true
		shop_changed.emit()


func close_shop() -> void:
	if shop_open:
		shop_open = false
		shop_changed.emit()


## Titik spawn dekat base sendiri (dipakai toko hero)
func base_spawn_point(spawn_team: String, index: int = 0) -> Vector2:
	var am = get_tree().get_first_node_in_group("arena_map")
	if am != null and am.has_method("get_spawn_point"):
		return am.get_spawn_point(spawn_team, index)
	return Vector2(260, 480) if spawn_team == "blue" else Vector2(1020, 240)


# ── MENARA ────────────────────────────────────────────────

## Bangun menara di slot yang sedang dipilih (paritas Game.try_build_tower)
func try_build_tower(tower_type: String) -> bool:
	if state != "playing":
		return false
	var s := slot(selected_slot)
	if s.is_empty():
		print("[Shop] pilih slot bangun dulu")
		return false
	if bool(s["taken"]):
		print("[Shop] slot sudah terisi")
		return false
	if str(s["team"]) != "blue":
		print("[Shop] slot itu milik Dire")
		return false
	var cost := TowerDB.build_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: butuh %d (punya %d)" % [cost, gold])
		return false
	# paritas Game.try_build_tower: tipe apa pun boleh dibangun di Lv1 seharga
	# 100 gold; stat non-archer Lv1 jatuh ke ARCHER_LEVELS[1] (TowerDB sudah
	# meniru fallback itu), jadi keuntungannya baru terasa setelah upgrade Lv2.
	var base_type := tower_type if TowerDB.tower_types().has(tower_type) else "archer"
	s["taken"] = true
	var t = spawn_tower("blue", s["pos"], str(s["lane"]), "outer", base_type, 1)
	s["tower"] = t
	tower_built.emit(t)
	# Paritas build_archer (popup_after null): popup bangun DITUTUP dan
	# menara baru TIDAK dipilih — bukan dibuka detailnya.
	clear_selection()
	close_shop()
	print("[Shop] menara %s dibangun (-%d gold)" % [t.display_name, cost])
	return true


## Upgrade menara yang dipilih. Level 1 -> 2 wajib memilih jalur.
func try_upgrade_tower(target_type: String = "") -> bool:
	if state != "playing":
		return false
	var t = selected_tower
	if t == null or not is_instance_valid(t) or bool(t.get("is_dead")):
		return false
	if str(t.get("team")) != "blue":
		return false
	if not t.can_upgrade():
		print("[Shop] menara sudah level maksimum")
		return false
	var cost: int = t.upgrade_cost(target_type)
	if cost <= 0:
		return false
	if not spend_gold(cost):
		print("[Shop] gold kurang: upgrade butuh %d (punya %d)" % [cost, gold])
		return false
	if not t.upgrade(target_type):
		gold += cost
		return false
	shop_changed.emit()
	print("[Shop] menara jadi %s (-%d gold)" % [t.display_name, cost])
	return true


func try_sell_tower() -> bool:
	var t = selected_tower
	if t == null or not is_instance_valid(t) or bool(t.get("is_dead")):
		return false
	if not bool(t.get("is_player_built")):
		return false
	var refund: int = t.sell_value()
	if refund == 0:
		refund = 50 # refund 50% dari 100G (paritas _try_sell_tower; Lv1
		# tak punya tombol jual di UI, jadi cuma terjangkau via handler)
	for s in build_slots:
		if s.get("tower") == t:
			s["taken"] = false
			s["tower"] = null
	gold += refund
	t.queue_free()
	selected_tower = null
	selection_changed.emit()
	shop_changed.emit()
	print("[Shop] menara dijual (+%d gold)" % refund)
	return true


## Regen Shield menara (fitur berbayar 850 gold, menara Lv4+)
func try_buy_tower_regen_shield() -> bool:
	if state != "playing":
		return false
	var t = selected_tower
	if t == null or not is_instance_valid(t):
		return false
	if not t.can_activate_regen_shield():
		print("[Shop] Regen Shield butuh menara sendiri level %d+" % TowerDB.regen_shield_min_level())
		return false
	var cost: int = t.regen_shield_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: Regen Shield butuh %d (punya %d)" % [cost, gold])
		return false
	if not t.activate_regen_shield():
		gold += cost
		return false
	shop_changed.emit()
	return true


# ── HERO ──────────────────────────────────────────────────

## Roster milik tim, termasuk hero yang sedang menunggu respawn.
func owned_heroes(team: String = "blue") -> Array:
	var result: Array = []
	for hero in get_tree().get_nodes_in_group("heroes"):
		if is_instance_valid(hero) and not hero.is_queued_for_deletion() and hero.team == team:
			result.append(hero)
	return result


func owns_hero(hero_type: String, team: String = "blue") -> bool:
	for hero in owned_heroes(team):
		if hero.hero_type == hero_type:
			return true
	return false


func can_buy_hero(hero_type: String) -> bool:
	var data: Dictionary = HeroDB.get_hero(hero_type)
	return state == "playing" and not in_menu and not is_paused and not get_tree().paused \
		and not data.is_empty() \
		and SaveManager.is_unlocked(hero_type) and not owns_hero(hero_type) \
		and owned_heroes().size() < max_heroes_owned \
		and gold >= int(data.get("cost", 400))


func try_buy_hero(hero_type: String) -> bool:
	if not can_buy_hero(hero_type):
		return false
	var cost := int(HeroDB.get_hero(hero_type).get("cost", 400))
	if not spend_gold(cost):
		return false
	# Game.try_buy_hero: summon di depan toko Radiant, bukan hero gratis di base.
	var index := owned_heroes().size()
	var arena = get_tree().get_first_node_in_group("arena_map")
	var shop_pos: Vector2 = arena.radiant_shop_pos if arena != null else Vector2(340, 540)
	spawn_hero(hero_type, "blue", shop_pos + Vector2(50 + index * 30, 10))
	AudioManager.play_sfx("hero_spawn")
	close_shop()
	print("[Shop] %s dibeli (-%d gold)" % [HeroDB.get_hero(hero_type).get("name", hero_type), cost])
	return true


func try_upgrade_hero() -> bool:
	if state != "playing":
		return false
	var h = selected_hero
	if h == null or not is_instance_valid(h) or bool(h.get("is_dead")):
		return false
	if str(h.get("team")) != "blue":
		return false
	if not h.can_upgrade():
		print("[Shop] hero sudah level maksimum")
		return false
	var cost: int = h.upgrade_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: upgrade hero butuh %d (punya %d)" % [cost, gold])
		return false
	if not h.upgrade():
		gold += cost
		return false
	shop_changed.emit()
	return true


func try_buy_item(item_id: String) -> bool:
	if state != "playing":
		return false
	var h = selected_hero
	if h == null or not is_instance_valid(h) or bool(h.get("is_dead")):
		print("[Shop] pilih hero Radiant dulu untuk membeli item")
		return false
	if str(h.get("team")) != "blue":
		return false
	if not h.items.can_equip(item_id):
		if h.items.is_full():
			print("[Shop] 6 slot item %s sudah penuh" % h.name)
		else:
			print("[Shop] %s tidak bisa memakai %s (melee/magic only)" % [
				h.name, ItemDB.item_name(item_id)])
		return false
	var cost := ItemDB.item_cost(item_id)
	if not spend_gold(cost):
		print("[Shop] gold kurang: %s butuh %d (punya %d)" % [
			ItemDB.item_name(item_id), cost, gold])
		return false
	if not h.buy_item(item_id):
		gold += cost
		return false
	shop_changed.emit()
	return true


# ── NEXUS ─────────────────────────────────────────────────

func try_upgrade_nexus() -> bool:
	if state != "playing" or blue_nexus == null or not is_instance_valid(blue_nexus):
		return false
	if not blue_nexus.can_upgrade():
		return false
	var cost: int = blue_nexus.upgrade_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: upgrade nexus butuh %d (punya %d)" % [cost, gold])
		return false
	if not blue_nexus.upgrade():
		gold += cost
		return false
	shop_changed.emit()
	print("[Shop] Radiant Nexus naik ke level %d (-%d gold)" % [blue_nexus.level, cost])
	return true


func try_buy_nexus_shield() -> bool:
	if state != "playing" or blue_nexus == null or not is_instance_valid(blue_nexus):
		return false
	if not blue_nexus.can_buy_shield():
		return false
	var cost: int = blue_nexus.shield_cost()
	if not spend_gold(cost):
		print("[Shop] gold kurang: Castle Shield butuh %d (punya %d)" % [cost, gold])
		return false
	if not blue_nexus.activate_castle_shield():
		gold += cost
		return false
	shop_changed.emit()
	print("[Shop] Castle Shield aktif (-%d gold)" % cost)
	return true



