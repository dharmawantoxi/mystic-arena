# AIPlayer.gd — Port _entity.AIPlayer (tim Dire/merah), _entity.py:6003-6580.
#
# pygame: AIPlayer punya saldo sendiri (self.gold), list hero sendiri, dan
# dipanggil sekali per frame dari Game.update (_core.py:2268-2270). Di Godot
# saldo AI sudah ada di GameManager.ai_gold (income di GameManager._process),
# jadi module ini TIDAK menduplikasi gold — semua belanja lewat ai_spend().
#
# Yang diport 1:1:
#   • _ai_brain / _ai_elite / _ai_reserve  (kecerdasan & tabungan draft hero)
#   • update()      -> think_timer + beberapa aksi sekaligus per tick
#   • _ai_step()    -> 6 prioritas aksi (build/beli hero/upgrade hero/
#                      beli item/upgrade menara/Regen Shield/Castle
#                      Shield/upgrade nexus)
#   • _control_heroes() + _assign_hero_lane()  (kontrol per-gerak hero AI)
#   • _get_hero_pool / _choose_hero_purchase_target / _try_buy_hero
#   • _try_buy_item (lewat ItemDB.suggest_item — paritas
#                    hero_items.suggest_item_for_hero)
#
# PENYEDERHANAAN terdokumentasi vs pygame:
#   1. Pygame AI mulai dengan roster KOSONG dan membeli semua hero sendiri
#      (AI_THINK_INTERVAL dsb. _entity.py:6008). Godot sudah meng-seed 6 hero
#      merah di Main._start_battle (ENEMY_ROSTER) — keputusan port sebelumnya
#      yang mempertahankan alur battle existing. Karena 6 >= AI_MAX_HEROES (5),
#      cabang _try_buy_hero tetap ada untuk paritas tetapi tidak menambah hero
#      baru sampai jumlah roster turun di bawah 5.
#   2. Jumlah hero AI diambil dari group "heroes" (scene tree), bukan list
#      sendiri — jadi respawn roster (_on_hero_died) tidak membuat referensi
#      basi. Statistik total_built/total_upgraded/dst. pygame TIDAK diport
#      (dipakai hanya untuk debug/HUD, tidak memengaruhi keputusan).
#   3. Auto-cast skill ditangani Hero._auto_cast sendiri (paritas
#      hero._try_auto_cast dengan pemeriksaan tiap 20 frame);
#      _control_heroes di sini hanya menugaskan jalur, seperti kondisi
#      `not hero.target and not hero.destination` di _entity.py:6252.
extends Node

const FPS := 60.0

# ── Konstanta AI (paritas _core.py:1090-1102) ──
const AI_THINK_INTERVAL := 90.0            # frame antar "berpikir" @ level 1
const AI_UPGRADE_TOWER_CHANCE := 0.30
const AI_NEXUS_UPGRADE_PRIORITY := 0.35
const AI_HERO_BUY_PRIORITY := 0.45
const AI_HERO_UPGRADE_PRIORITY := 0.40
const AI_HERO_PREFERENCES: Array = [
	"thorne", "grimjaw", "vex", "sylara", "kaizen", "zephyr",
]
const AI_MAX_HEROES := 5

# ── Batas level AI (paritas _entity.py:6041 _ai_elite) ──
const ELITE_START_LEVEL := 20
## Level terakhir ("elite_end") diambil runtime dari GameManager.level_count()
## — bukan konstanta — supaya kalau level baru ditambahkan AI tetap naik
## sampai akhir (paritas levels.get_level_count() _entity.py:6044-6047).

# ── Menara (paritas _entity.py:6084-6103 _try_build_tower) ──
const BUILD_COST := 100
const TOWER_TYPES: Array = ["archer", "cannon", "ice", "mage"]
const TOWER_WEIGHTS: Array = [0.35, 0.25, 0.20, 0.20]
## Jalur favorit saat upgrade tower dari level 1 (paritas _entity.py:6204).
const PREFERRED_UPGRADE_PATH: Array = ["cannon", "ice", "archer", "mage"]

# ── Jalur (paritas _core.py:144-146 LANE_Y_*) ──
const LANE_Y: Dictionary = {"top": 150.0, "mid": 380.0, "bot": 610.0}
## Base Dire (paritas RED_BASE_X/Y _core.py:153-154 = ArenaMap.RED_BASE)
const RED_BASE := Vector2(1180, 100)


## Sisa waktu sampai AI "berpikir" lagi (detik). pygame memakai frame
## (AI_THINK_INTERVAL=90 @60fps = 1.5s); dikonversi FPS di reset()/_process.
var think_timer: float = 0.0

# Draft hero persisten (paritas _entity.py:6018-6022 _hero_purchase_target):
# disimpan sampai gold cukup — tanpa ini AI selalu membeli hero termurah dan
# roster level tinggi tetap berisi boss level 1.
var _hero_purchase_target: String = ""
var _hero_purchase_target_cost: int = 0
var _hero_source_levels: Dictionary = {}


func _ready() -> void:
	# Node anak Main yang PROCESS_MODE_ALWAYS -> harus dipaksa PAUSABLE supaya
	# pause (P/ESC) benar-benar membekukan AI (Main._ready melakukan hal yang
	# sama untuk Containers/ArenaMap).
	process_mode = Node.PROCESS_MODE_PAUSABLE
	if not GameManager.level_started.is_connected(_on_level_started):
		GameManager.level_started.connect(_on_level_started)
	reset()


func _exit_tree() -> void:
	if GameManager.level_started.is_connected(_on_level_started):
		GameManager.level_started.disconnect(_on_level_started)


func _on_level_started(_level_num: int) -> void:
	reset()


## Reset state AI tiap match baru (paritas Game.reset yang membuat ulang
## AIPlayer — _core.py:1485).
func reset() -> void:
	think_timer = AI_THINK_INTERVAL / FPS
	_hero_purchase_target = ""
	_hero_purchase_target_cost = 0
	_hero_source_levels = {}


# ══════════════════════════════════════════════════════════
#  KECERDASAN
# ══════════════════════════════════════════════════════════

## 0.0 (level 1) -> 1.0 (level 20). Hanya otak dasar; level 20+ naik lewat
## _ai_elite() (paritas _entity.py:6027-6036).
func _ai_brain() -> float:
	var lvl := maxi(1, int(GameManager.level_number))
	return minf(1.0, float(lvl - 1) / 19.0)


## 0.0 (level 20) -> 1.0 (level terakhir). AI elite berpikir jauh lebih cepat
## dan melakukan 2-3 aksi sekaligus per tick (paritas _entity.py:6038-6051).
func _ai_elite() -> float:
	var lvl := maxi(1, int(GameManager.level_number))
	var elite_end := maxi(ELITE_START_LEVEL + 1, GameManager.level_count())
	if lvl <= ELITE_START_LEVEL:
		return 0.0
	return minf(1.0, float(lvl - ELITE_START_LEVEL) \
		/ float(maxi(1, elite_end - ELITE_START_LEVEL)))


## Gold yang ditabung untuk draft hero berikutnya — bukan bonus/handicap:
## AI hanya tidak menghabiskan tabungan target hero untuk tower/item sebelum
## biaya summon-nya terkumpul (paritas _entity.py:6064-6072).
func _ai_reserve() -> int:
	if _hero_purchase_target_cost <= 0:
		return 0
	return maxi(0, _hero_purchase_target_cost)


func _gold() -> int:
	return GameManager.ai_gold


# ══════════════════════════════════════════════════════════
#  LOOP (paritas AIPlayer.update _entity.py:6074-6096)
# ══════════════════════════════════════════════════════════

func _process(delta: float) -> void:
	if GameManager.state != "playing":
		return
	_control_heroes()
	think_timer -= delta
	if think_timer > 0.0:
		return
	var brain := _ai_brain()
	var elite := _ai_elite()
	# Interval berpikir: makin pintar makin cepat; elite (level 20+) menurunkan
	# lantai interval (paritas _entity.py:6082-6086 — max(8, int(...)) frame).
	var frames := maxi(8, floori(AI_THINK_INTERVAL * (1.0 - 0.65 * brain) \
		- 22.0 * elite))
	think_timer = float(frames) / FPS
	# AI elite melakukan beberapa aksi per tick berpikir (1 -> 3) — paritas
	# _entity.py:6088-6096. round() dipakai juga di pygame; nilai 2*elite tidak
	# pernah tepat *.5 (penyebut 34), jadi banker's rounding vs away-from-zero
	# tidak berpengaruh.
	var actions := 1 + int(round(2.0 * elite))
	for _i in range(actions):
		if not _ai_step(brain, elite):
			break


# ══════════════════════════════════════════════════════════
#  STEP — satu putaran prioritas (paritas _entity.py:6098-6164)
# ══════════════════════════════════════════════════════════

func _ai_step(brain: float, elite: float) -> bool:
	var my_towers: Array = []
	var all_my_towers: Array = []
	for t in get_tree().get_nodes_in_group("towers"):
		if not is_instance_valid(t) or str(t.get("team")) != "red" \
				or bool(t.get("is_dead")):
			continue
		all_my_towers.append(t)
		if t.can_upgrade():
			my_towers.append(t)

	# ═══ Priority 0: bangun menara baru (kapasitas slot kosong) ═══
	var empty: Array = GameManager.free_slots_for("red")
	if not empty.is_empty() and _gold() >= 150:
		if _roll(0.4 + 0.45 * brain, elite):
			if _try_build_tower(empty):
				return true

	# ═══ Priority 1: beli hero (maks AI_MAX_HEROES) ═══
	# List hero diambil DARI sini ke bawah (bukan di awal step): kalau hero
	# baru terbeli, guard berikutnya langsung melihatnya — paritas pygame
	# yang selalu membaca self.heroes live.
	var heroes := _red_heroes()
	if heroes.size() < AI_MAX_HEROES:
		if _roll(AI_HERO_BUY_PRIORITY * (0.55 + 0.9 * brain), elite):
			if _try_buy_hero():
				return true
	heroes = _red_heroes()

	# ═══ Priority 2: upgrade hero (dulu, kills tertinggi) ═══
	if not heroes.is_empty() \
			and _roll(AI_HERO_UPGRADE_PRIORITY * (0.7 + 0.6 * brain), elite):
		if _try_upgrade_hero():
			return true

	# ═══ Priority 2b: beli ITEM hero (paritas dengan pemain) ═══
	if not heroes.is_empty() \
			and _roll(0.35 + 0.4 * brain + 0.2 * elite, elite):
		if _try_buy_item():
			return true

	# ═══ Priority 3: upgrade menara (favorit = paling banyak kill) ═══
	if not my_towers.is_empty() \
			and _roll(AI_UPGRADE_TOWER_CHANCE + 0.5 * brain, elite):
		if _try_upgrade_tower(my_towers):
			return true

	# ═══ Priority 3b: Regen Shield (lvl 4+, tanpa roll — paritas 6165) ═══
	if not all_my_towers.is_empty() and _try_activate_regen_shield(all_my_towers):
		return true

	# ═══ Priority 4: Castle Shield (lvl 4+, tanpa roll — paritas 6169) ═══
	if _try_activate_castle_shield():
		return true

	# ═══ Priority 5: upgrade nexus ═══
	if _roll(AI_NEXUS_UPGRADE_PRIORITY * (0.7 + 0.6 * brain), elite):
		if _try_upgrade_nexus():
			return true
	return false


## Elite menaikkan peluang tiap aksi, cap 0.98 supaya tetap ada variasi
## (paritas roll() _entity.py:6114-6116).
static func _roll(base: float, elite: float) -> bool:
	return randf() < minf(0.98, base + 0.45 * elite)


# ══════════════════════════════════════════════════════════
#  MENARA
# ══════════════════════════════════════════════════════════

## Build di slot kosong ACAK dengan tipe ber-bobot (paritas
## _try_build_tower _entity.py:6174-6202: archer paling sering).
func _try_build_tower(empty_slots: Array) -> bool:
	if empty_slots.is_empty():
		return false
	if _gold() < BUILD_COST + _ai_reserve():
		return false
	var idx: int = empty_slots[randi() % empty_slots.size()]
	var slot: Dictionary = GameManager.slot(idx)
	if slot.is_empty() or bool(slot.get("taken", false)):
		return false
	var chosen := _weighted_tower_type()
	if not GameManager.ai_spend(BUILD_COST):
		return false
	var tower = GameManager.spawn_tower("red", slot["pos"],
		str(slot.get("lane", "mid")), "outer", chosen, 1)
	slot["taken"] = true
	slot["tower"] = tower
	return true


static func _weighted_tower_type() -> String:
	var total := 0.0
	for w in TOWER_WEIGHTS:
		total += float(w)
	var r := randf() * total
	for i in range(TOWER_TYPES.size()):
		r -= float(TOWER_WEIGHTS[i])
		if r <= 0.0:
			return str(TOWER_TYPES[i])
	return str(TOWER_TYPES[TOWER_TYPES.size() - 1])


## Upgrade tower paling banyak kill dulu; level 1 memilih jalur dari
## PREFERRED_UPGRADE_PATH (paritas _try_upgrade_tower_new _entity.py:6198-6222).
func _try_upgrade_tower(my_towers: Array) -> bool:
	my_towers.sort_custom(func(a, b): return int(a.get("kills")) > int(b.get("kills")))
	for tower in my_towers:
		if int(tower.get("level")) <= 1:
			for path in PREFERRED_UPGRADE_PATH:
				var cost: int = tower.upgrade_cost(path)
				if _gold() >= cost + _ai_reserve():
					if tower.upgrade(path):
						GameManager.ai_spend(cost)
						return true
		else:
			var cost: int = tower.upgrade_cost()
			if _gold() >= cost + _ai_reserve():
				if tower.upgrade():
					GameManager.ai_spend(cost)
					return true
	return false


## Regen Shield untuk menara eligible (level 4+, belum aktif) — paritas
## _try_activate_regen_shield _entity.py:6224-6242. Menara Dire sekarang
## boleh membeli (lihat Tower.can_activate_regen_shield).
func _try_activate_regen_shield(all_my_towers: Array) -> bool:
	var candidates: Array = []
	for t in all_my_towers:
		if t.has_method("can_activate_regen_shield") and t.can_activate_regen_shield():
			candidates.append(t)
	if candidates.is_empty():
		return false
	candidates.sort_custom(func(a, b): return int(a.get("kills")) > int(b.get("kills")))
	for tower in candidates:
		var cost: int = tower.regen_shield_cost()
		if _gold() >= cost + _ai_reserve():
			if tower.activate_regen_shield():
				GameManager.ai_spend(cost)
				return true
	return false


# ══════════════════════════════════════════════════════════
#  NEXUS / CASTLE SHIELD
# ══════════════════════════════════════════════════════════

## Castle Shield setelah perlindungan gratis wave 10 habis (paritas
## _try_activate_castle_shield _entity.py:6531-6538). Nama Godot:
## can_buy_shield()/shield_cost() (Nexus.gd) = pygame
## can_activate_castle_shield()/castle_shield_cost().
func _try_activate_castle_shield() -> bool:
	var nexus = GameManager.red_nexus
	if nexus == null or not is_instance_valid(nexus) or not nexus.can_buy_shield():
		return false
	var cost: int = nexus.shield_cost()
	if _gold() < cost + _ai_reserve():
		return false
	if nexus.activate_castle_shield():
		GameManager.ai_spend(cost)
		return true
	return false


func _try_upgrade_nexus() -> bool:
	var nexus = GameManager.red_nexus
	if nexus == null or not is_instance_valid(nexus) or not nexus.can_upgrade():
		return false
	var cost: int = nexus.upgrade_cost()
	if _gold() < cost + _ai_reserve():
		return false
	if nexus.upgrade():
		GameManager.ai_spend(cost)
		return true
	return false


# ══════════════════════════════════════════════════════════
#  HERO — kontrol gerak & belanja
# ══════════════════════════════════════════════════════════

func _red_heroes() -> Array:
	var out: Array = []
	for h in get_tree().get_nodes_in_group("heroes"):
		if not is_instance_valid(h) or str(h.get("team")) != "red" \
				or bool(h.get("is_dead")):
			continue
		out.append(h)
	return out


## Kontrol hero per frame (paritas _control_heroes _entity.py:6246-6262).
## Auto-cast di pygame dipanggil di sini saat skill_timer == 0; di Godot
## Hero._auto_cast sudah menjalankan _try_auto_cast dengan timer sendiri,
## jadi yang tersisa adalah penugasan jalur untuk hero yang menganggur.
func _control_heroes() -> void:
	for hero in _red_heroes():
		if hero.get("target") == null and not hero.has_destination():
			_assign_hero_lane(hero)


## Pilih lane dengan ancaman minion musuh terbanyak; hero merah mencari minion
## biru TERDEKAT di lane itu (bukan paling dalam — fix _entity.py:6298-6315
## supaya hero tidak melewati semua musuh menuju titik tertentu). Kalau tidak
## ada minion, cari menara biru terdekat dan berhenti 60 px darinya.
func _assign_hero_lane(hero) -> void:
	var threats := {"top": 0, "mid": 0, "bot": 0}
	for m in get_tree().get_nodes_in_group("minions"):
		if not is_instance_valid(m) or str(m.get("team")) == "red" \
				or bool(m.get("is_dead")):
			continue
		var lane := str(m.get("lane", ""))
		if threats.has(lane):
			threats[lane] = int(threats[lane]) + 1
	var max_lane := "mid"
	var max_count := 0
	for lane in threats:
		if int(threats[lane]) > max_count:
			max_count = int(threats[lane])
			max_lane = lane
	if max_count > 0:
		var target_y := float(LANE_Y[max_lane])
		var best = null
		var best_d := 1e18
		for m in get_tree().get_nodes_in_group("minions"):
			if not is_instance_valid(m) or str(m.get("team")) != "blue" \
					or bool(m.get("is_dead")) or str(m.get("lane", "")) != max_lane:
				continue
			var d: float = hero.global_position.distance_to(m.global_position)
			if d < best_d:
				best_d = d
				best = m
		if best != null:
			hero.set_destination(best.global_position, true)
		else:
			hero.set_destination(Vector2(600.0, target_y), true)
	else:
		var best_tower = null
		var best_d := 1e18
		for t in get_tree().get_nodes_in_group("towers"):
			if not is_instance_valid(t) or str(t.get("team")) != "blue" \
					or bool(t.get("is_dead")):
				continue
			var d: float = hero.global_position.distance_to(t.global_position)
			if d < best_d:
				best_d = d
				best_tower = t
		if best_tower != null:
			var to: Vector2 = hero.global_position - best_tower.global_position
			if to.length() > 0.01:
				hero.set_destination(best_tower.global_position + to.normalized() * 60.0, true)


## Pool summon AI: semua starter + boss hero dari SEMUA level di bawah level
## sekarang (paritas _get_hero_pool _entity.py:6318-6352). Boss level saat ini
## tidak ikut — pemain belum menaklukkannya pada titik itu.
func _get_hero_pool() -> Array:
	var pool: Array = []
	pool.append_array(AI_HERO_PREFERENCES)
	var source_levels: Dictionary = {}
	var lvl := int(GameManager.level_number)
	if lvl >= 2:
		for level_no in range(1, lvl):
			var cfg: Dictionary = BossDB.get_level(level_no)
			if cfg.is_empty():
				continue
			var bosses: Array = []
			var mini: Variant = cfg.get("mini_bosses", {})
			if mini is Dictionary:
				for b in mini.values():
					bosses.append(str(b))
			var true_boss: Variant = cfg.get("true_boss")
			if true_boss != null and str(true_boss) != "":
				bosses.append(str(true_boss))
			for boss_type in bosses:
				if not bool(HeroDB.get_hero(boss_type).get("is_boss_hero", false)):
					continue
				if pool.has(boss_type):
					continue
				pool.append(boss_type)
				source_levels[boss_type] = level_no
	_hero_source_levels = source_levels
	return pool


## Pilih draft dari seluruh pool — paritas _choose_hero_purchase_target
## _entity.py:6354-6411: satu starter jadi fondasi roster, boss pertama dari
## level TERBARU yang sudah lewat, selanjutnya berbobot level sumber.
func _choose_hero_purchase_target(available: Array) -> String:
	var catalog: Dictionary = HeroDB.heroes
	var starter_options: Array = []
	var boss_options: Array = []
	for ht in available:
		if bool(catalog.get(ht, {}).get("is_boss_hero", false)):
			boss_options.append(ht)
		else:
			starter_options.append(ht)
	var has_starter := false
	for hero in _red_heroes():
		var htype := str(hero.get("hero_type"))
		if not bool(catalog.get(htype, {}).get("is_boss_hero", false)):
			has_starter = true
			break
	if not has_starter and not starter_options.is_empty():
		return str(starter_options[randi() % starter_options.size()])
	if not boss_options.is_empty():
		var has_boss := false
		for hero in _red_heroes():
			var htype := str(hero.get("hero_type"))
			if bool(catalog.get(htype, {}).get("is_boss_hero", false)):
				has_boss = true
				break
		if not has_boss:
			var newest := 0
			for ht in boss_options:
				newest = maxi(newest, int(_hero_source_levels.get(str(ht), 0)))
			var newest_options: Array = []
			for ht in boss_options:
				if int(_hero_source_levels.get(str(ht), 0)) == newest:
					newest_options.append(ht)
			return str(newest_options[randi() % newest_options.size()])
		# Level baru diberi bobot lebih besar (paritas random.choices weights).
		var weights: Array = []
		for ht in boss_options:
			weights.append(maxi(1, int(_hero_source_levels.get(str(ht), 1))))
		return str(_weighted_choice(boss_options, weights))
	if not starter_options.is_empty():
		return str(starter_options[randi() % starter_options.size()])
	return ""


static func _weighted_choice(items: Array, weights: Array) -> String:
	var total := 0.0
	for w in weights:
		total += float(w)
	var r := randf() * total
	for i in range(items.size()):
		r -= float(weights[i])
		if r <= 0.0:
			return str(items[i])
	return str(items[items.size() - 1])


## Beli hero: target draft dipertahankan HINGGA gold cukup (paritas
## _try_buy_hero _entity.py:6413-6448). Posisi spawn di samping base Dire:
## RED_BASE_X-60, RED_BASE_Y+30+offset (offset = jumlah hero * 40 - 40).
func _try_buy_hero() -> bool:
	var heroes := _red_heroes()
	var owned: Array = []
	for h in heroes:
		owned.append(str(h.get("hero_type")))
	var available: Array = []
	for ht in _get_hero_pool():
		if not owned.has(ht):
			available.append(ht)
	if available.is_empty():
		_hero_purchase_target = ""
		_hero_purchase_target_cost = 0
		return false
	var hero_type := _hero_purchase_target
	if hero_type == "" or not available.has(hero_type):
		hero_type = _choose_hero_purchase_target(available)
		_hero_purchase_target = hero_type
	if hero_type == "":
		_hero_purchase_target_cost = 0
		return false
	var cost := int(HeroDB.get_hero(hero_type).get("cost", 400))
	_hero_purchase_target_cost = cost
	if _gold() < cost:
		return false
	var pos := RED_BASE + Vector2(-60.0, 30.0 + float(heroes.size()) * 40.0 - 40.0)
	GameManager.spawn_hero(hero_type, "red", pos)
	# Urutan paritas pygame: hero dibuat & masuk roster dulu, baru gold
	# dikurangi (_entity.py:6438-6443).
	GameManager.ai_spend(cost)
	_hero_purchase_target = ""
	_hero_purchase_target_cost = 0
	return true


## Upgrade hero dengan kill terbanyak dulu (paritas _try_upgrade_hero
## _entity.py:6450-6468).
func _try_upgrade_hero() -> bool:
	var upgradeable: Array = []
	for h in _red_heroes():
		if int(h.get("level")) < HeroDB.max_hero_level:
			upgradeable.append(h)
	if upgradeable.is_empty():
		return false
	upgradeable.sort_custom(func(a, b): return int(a.get("kills")) > int(b.get("kills")))
	for hero in upgradeable:
		var cost: int = hero.upgrade_cost()
		if _gold() >= cost + _ai_reserve():
			if hero.upgrade():
				GameManager.ai_spend(cost)
				return true
	return false


## Comparator sortir kandidat (kills, level) menurun — paritas
## `sorted(key=lambda h: (h.kills, h.level), reverse=True)` _entity.py:6495.
func _hero_priority_desc(a, b) -> bool:
	var ak := int(a.get("kills"))
	var bk := int(b.get("kills"))
	if ak != bk:
		return ak > bk
	return int(a.get("level")) > int(b.get("level"))


## Beli item untuk hero paling layak: slot kosong, sortir (kills, level)
## menurun, pakai saran ItemDB.suggest_item (paritas _try_buy_item
## _entity.py:6470-6517 — hero_items.suggest_item_for_hero).
func _try_buy_item() -> bool:
	var candidates: Array = []
	for h in _red_heroes():
		var inv = h.get("items")
		if inv == null or inv.is_full():
			continue
		candidates.append(h)
	if candidates.is_empty():
		return false
	candidates.sort_custom(_hero_priority_desc)
	for hero in candidates:
		var owned: Array = []
		var inv = hero.get("items")
		for s in inv.slots:
			if str(s) != "":
				owned.append(str(s))
		var sid := ItemDB.suggest_item(hero, owned)
		if sid == "":
			continue
		var cost := ItemDB.item_cost(sid)
		if _gold() < cost + _ai_reserve():
			continue
		# buy_item() === pygame hero.items.add(): validasi melee/magic only
		# ada di sana (hero_items.py:1793-1815). Kalau ditolak, coba hero
		# berikutnya — persis alur `if hero.items.add(sid)` pygame.
		if hero.buy_item(sid):
			GameManager.ai_spend(cost)
			return true
	return false
