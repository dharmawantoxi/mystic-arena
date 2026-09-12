# ================================
# BossData.gd — Port 1:1 bosses/boss_data.py (bagian LOGIKA, FASE 32)
#
# Di Pygame, `bosses/boss_data.py` bukan cuma tabel: begitu modul diimpor,
# lima fungsi berjalan berurutan dan MENIMPA tabelnya sendiri in-place —
#
#   1. `_apply_boss_rebalancing()`      boost piecewise HP/damage/ability/skill
#   2. `_smooth_boss_progression()`     paksa kurva monoton (per slot wave mini,
#                                       per level true) — baca levels/
#   3. `_apply_boss_curve_overrides()`  3 kurva eksplisit true boss
#   4. `_normalize_hero_unlock_stats()` least-squares trend per kelas + clamp
#                                       outlier + running-max monoton
#   5. `_normalize_hero_unlock_range()` melee 70 / ranged clamp 120..220
#
# Jadi angka yang dipakai game (dan yang di-bake `tools/convert_to_godot.py`
# ke `bosses.json` / `boss_stats_full.json`) adalah HASIL pipeline itu, dan
# input mentahnya tidak pernah terlihat setelah import. Kelas ini mem-port
# LOGIKANYA supaya Godot bisa MENGHITUNG ULANG angka yang sama dari tabel
# MENTAH (`res://data/boss_pristine.json`, diekspor converter lewat AST
# literal SEBELUM mutasi) — pola yang sama dengan HeroBalance.gd (FASE 28)
# dan HeroItems.gd (FASE 29).
#
# Semua static + data disuntik (pristine & jadwal level lewat parameter),
# jadi tidak ada dependensi autoload dan bisa diuji tanpa BossDB.
# `BossDB` memakainya sebagai jalur pemulihan: tanpa `bosses.json`, tabel
# 216 boss dihitung ulang dari pristine alih-alih 3 boss hardcode.
#
# Adaptasi GDScript (perilaku identik, dikunci BossDataParityTest):
#   - `/` GDScript antara dua int = PEMBULATAN integer (Python: float) →
#     semua bagi di sini eksplisit `float(a) / float(b)`.
#   - `(c - mx) ** 2` Python memanggil libm pow, dan untuk ~1% nilai hasil
#     pow(x, 2) BEDA 1 ulp dari x*x (terukur di data nyata: 9 dari 864) →
#     port memakai `pow(d, 2.0)`, bukan `d * d`, supaya `sxx` bit-identik.
#   - `round()` Python = banker's (half-to-even) → `_py_round` (bukan
#     `round()` Godot yang half-up).
#   - `list.sort(key=...)` Python STABIL → `Array.sort_custom` TIDAK dijamin
#     stabil, jadi urutannya direplikasi eksplisit (indeks asal jadi
#     tie-break) — penting karena cost hero_unlock banyak yang seri.
#   - Dictionary Godot & dict Python sama-sama insertion-ordered, dan
#     `JSON.parse_string` mempertahankan urutan berkas → urutan tabel
#     pristine (yang menentukan hasil sort stabil) ikut terbawa.
extends RefCounted
class_name BossData

## Nama field boss yang disentuh pipeline (sama dengan yang diekspor
## `boss_pristine.json` — lihat tools/convert_to_godot.py).
const BOSS_FIELDS: Array = ["hp", "damage", "ability_damage",
	"skill_q_damage", "skill_w_damage", "skill_e_damage", "skill_r_damage"]
## Field skill yang di-boost piecewise (urutan persis sumber).
const SKILL_DMG_FIELDS: Array = ["skill_q_damage", "skill_w_damage",
	"skill_e_damage", "skill_r_damage"]
## MELEE_ROLE_HINTS (boss_data.py:11805) — default; pristine membawanya juga.
const MELEE_ROLE_HINTS: Array = [
	"fighter", "warrior", "assassin", "berserker", "brawler",
	"bruiser", "tank", "knight", "swordsman", "slayer", "ninja",
	"shinigami", "kunoichi", "charger", "beast", "guardian",
	"ghoul", "duelist", "warlord", "scorpion", "voidwalker",
	"vampire", "demon lord", "tidehunter", "lancer", "terror",
	"moon demon",
]


## round() Python: half-to-even (banker's). Sama dengan HeroBalance._py_round.
static func _py_round(v: float) -> int:
	var f := floorf(v)
	var diff := v - f
	if diff > 0.5:
		return int(f) + 1
	if diff < 0.5:
		return int(f)
	return int(f) if int(f) % 2 == 0 else int(f) + 1


## int() Python: pemotongan ke arah nol (dipakai `int(hp * 2.2)` dkk.).
static func _py_int(v: float) -> int:
	return int(v)


static func _inum(d: Dictionary, key: String, fallback: int) -> int:
	if d == null or not d.has(key):
		return fallback
	var v = d[key]
	if v == null:
		return fallback
	return int(v)


static func _fnum(d: Dictionary, key: String, fallback: float) -> float:
	if d == null or not d.has(key):
		return fallback
	var v = d[key]
	if v == null:
		return fallback
	return float(v)


## Truthiness Python untuk `bd.get("hero_unlock")`: None DAN dict kosong
## sama-sama falsy (boss tanpa hero unlock tidak ikut dinormalisasi).
static func _truthy_hu(bd: Dictionary) -> bool:
	if bd == null or not bd.has("hero_unlock"):
		return false
	var hu = bd["hero_unlock"]
	if hu == null:
		return false
	if hu is Dictionary:
		return not (hu as Dictionary).is_empty()
	return true


## Salin dalam tabel pristine supaya pipeline tidak menulis ke data yang
## dimuat dari disk (paritas: pygame menulis in-place ke tabel modul, tapi
#  Godot memuat JSON sekali dan bisa dipanggil berulang dari tes).
static func clone_tables(pristine: Dictionary) -> Array:
	var out: Array = []
	for key in ["mini", "true"]:
		var src: Dictionary = pristine.get(key, {})
		var copy := {}
		for btype in src:
			var row: Dictionary = src[btype]
			var dup := row.duplicate(false)
			if row.has("hero_unlock") and row["hero_unlock"] is Dictionary:
				dup["hero_unlock"] = (row["hero_unlock"] as Dictionary).duplicate(false)
			copy[str(btype)] = dup
		out.append(copy)
	return out


# ═══════════════════════════════════════════════════════════════════
# 1. _apply_boss_rebalancing()  (boss_data.py:11452-11528)
# ═══════════════════════════════════════════════════════════════════
static func apply_boss_rebalancing(mini: Dictionary, true_table: Dictionary) -> void:
	# ── Mini boss ──
	for btype in mini:
		var bdata: Dictionary = mini[btype]
		var hu = bdata.get("hero_unlock")
		var hp := _inum(bdata, "hp", 3000)
		var dmg := _inum(bdata, "damage", 50)
		var ab_dmg := _inum(bdata, "ability_damage", 100)
		var new_hp := 0
		if hp < 10000:
			new_hp = maxi(7500, _py_int(float(hp) * 2.2))
		elif hp < 20000:
			new_hp = _py_int(float(hp) * 1.6)
		elif hp < 40000:
			new_hp = _py_int(float(hp) * 1.4)
		else:
			new_hp = _py_int(float(hp) * 1.3)
		var new_dmg := 0
		if dmg < 100:
			new_dmg = maxi(85, _py_int(float(dmg) * 1.4))
		elif dmg < 200:
			new_dmg = _py_int(float(dmg) * 1.25)
		else:
			new_dmg = _py_int(float(dmg) * 1.2)
		bdata["hp"] = new_hp
		bdata["damage"] = new_dmg
		bdata["ability_damage"] = maxi(ab_dmg, _py_int(float(ab_dmg) * 1.25))
		for k in SKILL_DMG_FIELDS:
			if bdata.has(k) and int(bdata[k]) > 0:
				bdata[k] = _py_int(float(int(bdata[k])) * 1.25)
		if hu != null:
			bdata["hero_unlock"] = hu
	# ── True boss ──
	for btype in true_table:
		var bdata2: Dictionary = true_table[btype]
		var hu2 = bdata2.get("hero_unlock")
		var hp2 := _inum(bdata2, "hp", 15000)
		var dmg2 := _inum(bdata2, "damage", 100)
		var ab2 := _inum(bdata2, "ability_damage", 200)
		var nhp := 0
		if hp2 < 20000:
			nhp = maxi(36000, _py_int(float(hp2) * 2.4))
		elif hp2 < 40000:
			nhp = _py_int(float(hp2) * 2.0)
		elif hp2 < 70000:
			nhp = _py_int(float(hp2) * 1.6)
		else:
			nhp = _py_int(float(hp2) * 1.45)
		var ndmg := 0
		if dmg2 < 120:
			ndmg = maxi(145, _py_int(float(dmg2) * 1.5))
		elif dmg2 < 250:
			ndmg = _py_int(float(dmg2) * 1.3)
		else:
			ndmg = _py_int(float(dmg2) * 1.25)
		bdata2["hp"] = nhp
		bdata2["damage"] = ndmg
		bdata2["ability_damage"] = maxi(ab2, _py_int(float(ab2) * 1.35))
		for k2 in SKILL_DMG_FIELDS:
			if bdata2.has(k2) and int(bdata2[k2]) > 0:
				bdata2[k2] = _py_int(float(int(bdata2[k2])) * 1.35)
		if hu2 != null:
			bdata2["hero_unlock"] = hu2


# ═══════════════════════════════════════════════════════════════════
# 2. _slot_of_mini_wave() + _smooth_boss_progression()  (:11552-11607)
# ═══════════════════════════════════════════════════════════════════
## Kelompok wave mini boss: 10-12 awal, 13-21 tengah, 22+ akhir.
static func slot_of_mini_wave(wave: int) -> String:
	if wave <= 12:
		return "w10"
	if wave <= 21:
		return "w18"
	return "w25"


## `schedule` = daftar per level (urut 1..N) berisi
## {"mini_bosses": {wave:int -> nama}, "true_boss": nama} — padanan
## `levels.get_level_config(lvl)`. Di produksi diambil dari
## `res://data/levels.json` (BossDB.levels); di tes disuntik dari fixture.
static func smooth_boss_progression(mini: Dictionary, true_table: Dictionary,
		schedule: Array) -> void:
	if schedule.is_empty():
		return # paritas: `except Exception: return` pygame (levels tak ada)
	var n := schedule.size()
	# Mini boss: monoton per slot wave (w10 / w18 / w25)
	var prev_hp := {"w10": 0, "w18": 0, "w25": 0}
	var prev_dmg := {"w10": 0, "w18": 0, "w25": 0}
	var prev_ab := {"w10": 0, "w18": 0, "w25": 0}
	for i in range(n):
		var cfg: Dictionary = schedule[i] if schedule[i] is Dictionary else {}
		var waves := _sorted_wave_items(cfg.get("mini_bosses"))
		for item in waves:
			var s := slot_of_mini_wave(int(item[0]))
			var b = mini.get(str(item[1]))
			if b == null:
				continue
			b["hp"] = maxi(_inum(b, "hp", 0), int(prev_hp[s]))
			b["damage"] = maxi(_inum(b, "damage", 0), int(prev_dmg[s]))
			b["ability_damage"] = maxi(_inum(b, "ability_damage", 0), int(prev_ab[s]))
			prev_hp[s] = int(b["hp"])
			prev_dmg[s] = int(b["damage"])
			prev_ab[s] = int(b["ability_damage"])
	# True boss: monoton per level
	var thp := 0
	var tdmg := 0
	var tab := 0
	for i2 in range(n):
		var cfg2: Dictionary = schedule[i2] if schedule[i2] is Dictionary else {}
		var tb = cfg2.get("true_boss")
		if tb == null:
			continue
		var b2 = true_table.get(str(tb))
		if b2 == null:
			continue
		b2["hp"] = maxi(_inum(b2, "hp", 0), thp)
		b2["damage"] = maxi(_inum(b2, "damage", 0), tdmg)
		b2["ability_damage"] = maxi(_inum(b2, "ability_damage", 0), tab)
		thp = int(b2["hp"])
		tdmg = int(b2["damage"])
		tab = int(b2["ability_damage"])


## `sorted(cfg["mini_bosses"].items())` Python: urut NAIK menurut wave.
## Kunci JSON bisa berupa String ("10") atau int (10) — dinormalkan ke int
## dulu supaya urutannya numerik, bukan leksikal ("10" < "25" < "5").
static func _sorted_wave_items(mini_bosses) -> Array:
	var items: Array = []
	if mini_bosses is Dictionary:
		for wave in mini_bosses:
			items.append([int(wave), mini_bosses[wave]])
	items.sort_custom(func(a, b): return int(a[0]) < int(b[0]))
	return items


# ═══════════════════════════════════════════════════════════════════
# 3. _apply_boss_curve_overrides()  (:11663-11675)
# ═══════════════════════════════════════════════════════════════════
static func apply_boss_curve_overrides(true_table: Dictionary, curves: Dictionary) -> void:
	var hp_curve: Dictionary = curves.get("hp", {})
	for name in hp_curve:
		var b = true_table.get(str(name))
		if b != null:
			b["hp"] = int(hp_curve[name])
	var dmg_curve: Dictionary = curves.get("damage", {})
	for name2 in dmg_curve:
		var b2 = true_table.get(str(name2))
		if b2 != null:
			b2["damage"] = int(dmg_curve[name2])
	var ab_curve: Dictionary = curves.get("ability", {})
	for name3 in ab_curve:
		var b3 = true_table.get(str(name3))
		if b3 != null:
			b3["ability_damage"] = int(ab_curve[name3])


# ═══════════════════════════════════════════════════════════════════
# 4. _hero_unlock_trend() + _normalize_hero_unlock_stats()  (:11703-11802)
# ═══════════════════════════════════════════════════════════════════
## Least-squares linear fit stat ~ cost (tanpa numpy). Input: Array of
## [cost, value]; return [a, b] dengan pred = a*cost + b.
static func hero_unlock_trend(values_by_cost: Array) -> Array:
	var n := values_by_cost.size()
	if n == 0:
		return [0.0, 0.0]
	var sum_c := 0
	var sum_v := 0.0
	var costs: Array = []
	var vals: Array = []
	for pair in values_by_cost:
		var c := float(pair[0])
		var v := float(pair[1])
		costs.append(c)
		vals.append(v)
	# Python `sum(costs)` atas int = exact; di sini cost dibaca apa adanya
	# (int di pristine) lalu dijumlahkan sebagai float — identik karena
	# seluruh cost < 2^53 dan penjumlahannya berurutan sama.
	for c2 in costs:
		sum_c += int(c2)
	for v2 in vals:
		sum_v += v2
	var mx := float(sum_c) / float(n)
	var my := sum_v / float(n)
	var sxx := 0.0
	for c3 in costs:
		sxx += pow(c3 - mx, 2.0)
	var sxy := 0.0
	for i in range(n):
		sxy += (float(costs[i]) - mx) * (float(vals[i]) - my)
	if sxx == 0.0:
		return [0.0, my]
	var a := sxy / sxx
	return [a, my - a * mx]


static func normalize_hero_unlock_stats(mini: Dictionary, true_table: Dictionary) -> void:
	for table in [mini, true_table]:
		var heroes: Array = []
		var idx := 0
		for bt in table:
			var bd: Dictionary = table[bt]
			if _truthy_hu(bd):
				# Indeks asal disimpan: sort Python STABIL, dan banyak cost
				# yang seri — tanpa tie-break urutannya bisa berbeda.
				heroes.append([bt, bd["hero_unlock"], idx])
			idx += 1
		_sort_by_cost(heroes)
		var hp_pairs: Array = []
		var dps_pairs: Array = []
		var sk_pairs: Array = []
		for h in heroes:
			var hu: Dictionary = h[1]
			var cost := _inum(hu, "cost", 0)
			hp_pairs.append([cost, _inum(hu, "hp", 0)])
			dps_pairs.append([cost, float(_inum(hu, "damage", 0)) \
				/ float(maxi(1, _inum(hu, "attack_cooldown", 30))) * 60.0])
			sk_pairs.append([cost, _inum(hu, "skill_damage", 0)])
		var hp_fit := hero_unlock_trend(hp_pairs)
		var dps_fit := hero_unlock_trend(dps_pairs)
		var sk_fit := hero_unlock_trend(sk_pairs)
		for h2 in heroes:
			var hu2: Dictionary = h2[1]
			var cost2 := _inum(hu2, "cost", 0)
			# 1) Fix skill_damage <= 0 + clamp skill
			hu2["skill_damage"] = _py_round(_clamp_unlock(
				float(_inum(hu2, "skill_damage", 0)),
				float(sk_fit[0]) * float(cost2) + float(sk_fit[1])))
			# 2) Clamp hp
			hu2["hp"] = _py_round(_clamp_unlock(float(_inum(hu2, "hp", 0)),
				float(hp_fit[0]) * float(cost2) + float(hp_fit[1])))
			# 3) Clamp dps -> konversi balik ke damage
			var cd := maxi(1, _inum(hu2, "attack_cooldown", 30))
			var cur_dps := float(_inum(hu2, "damage", 0)) / float(cd) * 60.0
			var new_dps := _clamp_unlock(cur_dps,
				float(dps_fit[0]) * float(cost2) + float(dps_fit[1]))
			if new_dps != cur_dps:
				hu2["damage"] = _py_round(new_dps * float(cd) / 60.0)
		# 4) Monoton dengan toleransi 15% (dip kecil = variasi desain)
		var m_hp := 0
		var m_dmg := 0
		var m_sk := 0
		for h3 in heroes:
			var hu3: Dictionary = h3[1]
			# Pembanding Python adalah FLOAT `0.85 * m` (bukan int terpangkas).
			if _lt_tol(int(hu3["hp"]), m_hp):
				hu3["hp"] = m_hp
			else:
				m_hp = maxi(m_hp, int(hu3["hp"]))
			if _lt_tol(int(hu3["damage"]), m_dmg):
				hu3["damage"] = m_dmg
			else:
				m_dmg = maxi(m_dmg, int(hu3["damage"]))
			if _lt_tol(int(hu3["skill_damage"]), m_sk):
				hu3["skill_damage"] = m_sk
			else:
				m_sk = maxi(m_sk, int(hu3["skill_damage"]))


## `hu["hp"] < 0.85 * m_hp` Python membandingkan int dengan FLOAT hasil kali
## (bukan int yang dipotong) — jadi pembandingnya harus float juga.
static func _lt_tol(value: int, running_max: int) -> bool:
	return float(value) < 0.85 * float(running_max)


## clamp() di dalam _normalize_hero_unlock_stats (boss_data.py:11745-11752).
static func _clamp_unlock(v: float, pred: float) -> float:
	if pred <= 0.0:
		return v
	if v <= 0.0 or v < 0.70 * pred:
		return maxf(v, 0.80 * pred)
	if v > 1.30 * pred:
		return minf(v, 1.20 * pred)
	return v


## `heroes.sort(key=lambda h: h[1].get("cost", 0))` — STABIL.
static func _sort_by_cost(heroes: Array) -> void:
	heroes.sort_custom(func(a, b):
		var ca := _inum(a[1], "cost", 0)
		var cb := _inum(b[1], "cost", 0)
		if ca != cb:
			return ca < cb
		return int(a[2]) < int(b[2]))


# ═══════════════════════════════════════════════════════════════════
# 5. _normalize_hero_unlock_range()  (:11815-11832)
# ═══════════════════════════════════════════════════════════════════
static func normalize_hero_unlock_range(mini: Dictionary, true_table: Dictionary,
		hints: Array = MELEE_ROLE_HINTS) -> void:
	for table in [mini, true_table]:
		for bt in table:
			var bd: Dictionary = table[bt]
			# `if not hu: continue` Python: hero_unlock kosong/None dilewati
			# (kalau tidak, boss tanpa unlock malah diberi kunci range baru).
			if not _truthy_hu(bd):
				continue
			var hu: Dictionary = bd["hero_unlock"]
			var role := str(hu.get("role", "") if hu.get("role") != null else "").to_lower()
			# Python: `int(hu.get("range", 70) or 70)` — nilai falsy (0/None)
			# jatuh ke 70, BUKAN ke 0.
			var raw_range = hu.get("range", 70)
			var orig := 70
			if raw_range != null and float(raw_range) != 0.0:
				orig = _py_int(float(raw_range))
			var is_melee := false
			for k in hints:
				if role.find(str(k)) != -1:
					is_melee = true
					break
			if is_melee or orig <= 90:
				hu["range"] = 70
			else:
				hu["range"] = maxi(120, mini(220, orig))
			# Skill selalu bisa dijangkau (skill_range >= range)
			var sr := _inum(hu, "skill_range", 0)
			if sr != 0 and sr < int(hu["range"]):
				hu["skill_range"] = int(hu["range"])


# ═══════════════════════════════════════════════════════════════════
# get_all_boss_types()  (:11837-11841)
# ═══════════════════════════════════════════════════════════════════
## Gabungan mini + true (true MENIMPA mini bila namanya bentrok — paritas
## `all_bosses.update(TRUE_BOSS_TYPES)` yang dipanggil terakhir).
static func get_all_boss_types(mini: Dictionary, true_table: Dictionary) -> Dictionary:
	var out := {}
	for k in mini:
		out[str(k)] = mini[k]
	for k2 in true_table:
		out[str(k2)] = true_table[k2]
	return out


# ═══════════════════════════════════════════════════════════════════
# Pipeline penuh
# ═══════════════════════════════════════════════════════════════════
## Jalankan KELIMA langkah persis urutan import boss_data.py.
## Return {"mini":…, "true":…, "all":…} — tabel hasil (bukan pristine).
static func build(pristine: Dictionary, schedule: Array) -> Dictionary:
	var tables := clone_tables(pristine)
	var mini: Dictionary = tables[0]
	var true_table: Dictionary = tables[1]
	apply_boss_rebalancing(mini, true_table)
	smooth_boss_progression(mini, true_table, schedule)
	apply_boss_curve_overrides(true_table, pristine.get("curves", {}))
	normalize_hero_unlock_stats(mini, true_table)
	normalize_hero_unlock_range(mini, true_table,
		pristine.get("melee_role_hints", MELEE_ROLE_HINTS))
	return {"mini": mini, "true": true_table,
		"all": get_all_boss_types(mini, true_table)}


## Muat tabel pristine dari disk ("" = path bawaan).
static func load_pristine(path: String = "res://data/boss_pristine.json") -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if parsed is Dictionary else {}


## Jadwal level untuk smooth_boss_progression dari entri levels.json
## (padanan levels.get_level_config: mini_bosses + true_boss per level).
static func schedule_from_levels(levels: Array) -> Array:
	var rows: Array = []
	for lv in levels:
		if not (lv is Dictionary):
			continue
		rows.append([int((lv as Dictionary).get("level_number", rows.size() + 1)), lv])
	rows.sort_custom(func(a, b): return int(a[0]) < int(b[0]))
	var out: Array = []
	for row in rows:
		var lv2: Dictionary = row[1]
		var mb := {}
		var raw = lv2.get("mini_bosses")
		if raw is Dictionary:
			for wave in raw:
				mb[int(wave)] = raw[wave]
		out.append({"mini_bosses": mb, "true_boss": lv2.get("true_boss")})
	return out
