# ================================
# HeroBalance.gd — Port 1:1 hero_balance.py (Pygame -> Godot)
#
# Satu-satunya tempat balance hero GAME DIKALIBRASI. Di Pygame, modul ini
# membaca katalog yang sudah disusun _core.get_all_hero_types(), menghitung
# multiplier per hero, lalu menulis hasilnya kembali ke katalog itu (in-place)
# supaya toko, preview skill, unit test, Hero, dan AI membaca ANGKA YANG SAMA.
#
# Di Godot, angka BALANCED-nya sudah di-bake ke res://data/heroes.json oleh
# tools/convert_to_godot.py (yang memanggil get_all_hero_types() Pygame =
# angka final sesudah balance). Class ini mem-port LOGIKANYA 1:1 supaya:
#   1. Godot bisa menghitung ulang angka yang sama dari katalog MENTAH
#      (dibuktikan HeroBalanceParityTest: hitung-ulang == heroes.json bake),
#   2. rumus catch-up starter + hitung unlock menjadi satu-satunya sumber
#      kebenaran (HeroDB/GameManager mendelegasikan ke sini),
#   3. kalibrasi resistansi boss (alat) tersedia tanpa Pygame.
#
# Seperti modul Pygame-nya (yang hanya mengimpor hero_archetypes +
# bosses.boss_data), class ini SENGAJA hampir mandiri: semua static, satu
# dependensi (HeroArchetypes, twin dari hero_archetypes.py). Data mentah
# boss (padanan bosses.boss_data) TIDAK dibaca dari autoload — disuntik
# lewat parameter `pristine`/`boss_tables` supaya fungsinya murni dan bisa
# diuji tanpa BossDB (lihat pristine_boss_stats).
#
# Adaptasi GDScript (perilaku identik, dikunci paritas):
#   - tuple Python -> Array (urutan indeks sama), tuple-key dict -> String
#     "A|B" (format laporannya memang "%s|%s" di kedua sisi),
#   - None -> null (atau Array/Dictionary kosong untuk "tidak ada"),
#   - round() -> _py_round (banker's, half-to-even persis Python),
#     round(x, n) -> _py_round_n,
#   - statistics.fmean/mean -> _fmean (penjumlahan exact gaya math.fsum +
#     bagi; bit-identik untuk data game, divalidasi fuzz vs CPython),
#   - statistics.median -> _median (sort + tengah; genap -> (a+b)/2 polos),
#   - ** -> pow() dengan urutan operasi yang sama persis,
#   - __main__.game_instance (jumlah unlock saat resolve) -> parameter
#     eksplisit `boss_unlocks`/`level` (di runtime diisi
#     GameManager.catchup_unlocks() oleh pemanggil).
#
# Twin Pygame: hero_balance.py (lihat header modul itu untuk angka dasar
# 2026-08-30, metrik yang dikejar, dan peringatan yang dibuang).
# Dikunci: godot/tests/HeroBalanceParityTest.gd (+ fixture
# tests/fixtures/match_parity.json["hero_balance"]).
# ================================
extends RefCounted
class_name HeroBalance


# ─── SAKLAR (hero_balance.py:39-45) ─────────────────────────────────────
const ENABLE_REBUDGET := true
const ENABLE_SCHOOL_MOD := false
const ENABLE_STARTER_CATCHUP := true
const SCHOOL_PARITY := true
const CELL_PARITY := true
const POOL_MEAN_ANCHOR := true
const FINAL_FIXPOINT := true

# ─── A. RE-BUDGET (hero_balance.py:49-56) ───────────────────────────────
const W_DPS := 0.72
const W_EHP := 0.28
const EHP_PER_HP := 1.0 / 6.0
const TARGET_RATIO := {"TANK": [9.5, 13.0], "FIGHTER": [6.0, 7.5],
	"CARRY": [3.4, 4.6]}
const SCHOOL_RATIO_BONUS := {"PHYSICAL": -0.04, "MAGIC": 0.04}
const RATIO_BLEND := 0.55
const BUDGET_COMPRESS := 0.45
const STYLE_POWER := {"TANK": 0.74, "FIGHTER": 1.06, "CARRY": 1.08}

const HP_MULT_RANGE := [0.66, 1.50]
const DMG_MULT_RANGE := [0.68, 1.45]

const SCHOOL_PARITY_CAP := 1.45
const CELL_PARITY_CAP := 1.30
const POOL_MEAN_TOL_MAX := 0.18
const FINAL_CORR_CAP := 1.35

# ─── guard "worth it" (hero_balance.py:70-75) ───────────────────────────
const COST_BUCKET := 1000
const COST_EFF_BAND := [0.78, 1.28]
const COST_EFF_DAMP := 0.60
const COST_EFF_MIN_GROUP := 8
const META_EFF_BAND := [0.80, 1.25]
const META_EFF_DAMP := 0.75

# ─── B. MODIFIER SEKOLAH KE MENARA (hero_balance.py:79-85) ──────────────
const TOWER_ARMOR_AT_L3 := 5.0
const SCHOOL_MOD_CAP := 1.06

## 1/(1+5*0.06) — di py dihitung sekali di level modul dari
## hero_archetypes.ARMOR_FACTOR; di sini fungsi supaya tidak ada const
## lintas-class (hasilnya bit-identik: operasi & urutan sama).
static func tower_phys_factor() -> float:
	return 1.0 / (1.0 + TOWER_ARMOR_AT_L3 * HeroArchetypes.ARMOR_FACTOR)

# ─── C. CATCH-UP STARTER (hero_balance.py:88-94) ────────────────────────
const STARTER_CATCHUP_MAX := 1.32
const STARTER_CATCHUP_REF := 12
const STARTER_CATCHUP_LV0 := 1
const STARTER_CATCHUP_LV1 := 8
const STARTER_CATCHUP_DECAY := 0.20
## Duplikat HeroDB.STARTER_HEROES (disengaja, seperti konstanta lintas
## modul lain di repo ini) — kesamaannya dikunci HeroBalanceParityTest.
const STARTER_HEROES := ["kaizen", "grimjaw", "sylara", "thorne",
	"vex", "zephyr"]
## Bagi bonus catch-up: ~60% HP / ~40% damage (hero_balance.py:241-244).
const STARTER_HP_SHARE := 1.25
const STARTER_DMG_SHARE := 0.85
## Ambang "bonus habis" (hero_balance.py:242).
const STARTER_CATCHUP_EPS := 1.001

## Kunci stat skill Q/W/E/R yang ikut dikalikan mult skill (muncul di tiga
## tempat di py: apply_to_catalog, _pool_mean_rescale, _final_fixpoint).
const SKILL_QWER_KEYS := ["skill_q_damage", "skill_w_damage",
	"skill_e_damage", "skill_r_damage"]

# ─── METRIK (hero_balance.py:97-117) ────────────────────────────────────
## DPS/HP/EHP/budget dari stats hero MENTAH (sebelum buff melee).
static func metrics(stats: Dictionary) -> Dictionary:
	var hp := _fnum(stats, "hp", 0.0)
	var dmg := _fnum(stats, "damage", 0.0)
	var cd := maxf(1.0, _fnum(stats, "attack_cooldown", 30.0))
	var sk := _fnum(stats, "skill_damage", 0.0)
	var skcd := maxf(1.0, _fnum(stats, "skill_cooldown", 240.0))
	var basic_dps := dmg * 60.0 / cd
	var skill_dps := sk * 60.0 / skcd
	var dps := basic_dps + skill_dps
	var armor := _fnum(stats, "armor", 0.0)
	var mr := clampf(_fnum(stats, "magic_resist", 0.0), 0.0, 0.75)
	var ehp := hp * (1.0 + armor * 0.06) / maxf(0.25, 1.0 - mr)
	var cost := _fnum(stats, "cost", 0.0)
	return {
		"hp": hp, "dmg": dmg, "skill": sk, "cd": cd, "skcd": skcd,
		"basic_dps": basic_dps, "skill_dps": skill_dps, "dps": dps,
		"ehp": ehp, "cost": cost,
		"burst": (skill_dps / dps) if dps > 0.0 else 0.0,
		"budget": W_DPS * dps + W_EHP * ehp * EHP_PER_HP,
	}


## float(stats.get(key, default) or default) — `or` Python memaksa 0/None
## hilang menjadi default (penting untuk attack_cooldown/skill_cooldown yang
## defaultnya bukan nol). Nilai non-numerik diperlakukan seperti None.
static func _fnum(stats: Dictionary, key: String, default: float) -> float:
	if not stats.has(key):
		return default
	var v: Variant = stats[key]
	if v is float:
		return v if v != 0.0 else default
	if v is int:
		return float(v) if v != 0 else default
	if v is bool:
		return default if not v else 1.0
	return default


## _clamp Python (hero_balance.py:120): max(lo, min(hi, v)).
static func _clamp(v: float, lo_hi: Array) -> float:
	return maxf(float(lo_hi[0]), minf(float(lo_hi[1]), v))


## d.get(key) or default — None/""/hilang -> default (persis `or` Python).
static func _str_or(d: Dictionary, key: String, default: String) -> String:
	var v: Variant = d.get(key, default)
	if v is String and v != "":
		return v
	return default


## statistics.median (hero_balance.py:124 + pemakaian langsung st.median):
## sort, ganjil -> tengah, genap -> (a+b)/2 POLOS (bukan fsum); kosong
## -> 0.0 (helper _median; pemanggil langsung tak pernah kosong).
static func _median(vals: Array) -> float:
	if vals.is_empty():
		return 0.0
	var s := vals.duplicate()
	s.sort()
	var n := s.size()
	if n % 2 == 1:
		return float(s[n / 2])
	return (float(s[n / 2 - 1]) + float(s[n / 2])) / 2.0


## statistics.fmean == statistics.mean untuk data float (keduanya
## math.fsum/n): _fsum exact + bagi; kosong -> 0.0 (helper _mean).
static func _fmean(vals: Array) -> float:
	if vals.is_empty():
		return 0.0
	return _fsum(vals) / float(vals.size())


## math.fsum: penjumlahan exact (Shewchuk partials) lalu dibulatkan sekali.
## Python menjumlah dengan exact lalu round-half-even di akhir; loop naif
## `total += x` menyimpang ~1e-12 pada 216 nilai dan BISA menggeser
## keputusan batas (pecah-iterasi fixpoint, argmin grid kalibrasi).
## Implementasi: partials non-overlapping (ascending), lalu dijumlah dari
## yang terkecil — bit-identik dengan CPython untuk seluruh data game
## (divalidasi fuzz jutaan kasus vs math.fsum, termasuk kancellation).
## Input game selalu finite & non-negatif; NaN merambat seperti fsum.
static func _fsum(vals: Array) -> float:
	var partials: Array = []
	for x0 in vals:
		var x := float(x0)
		var i := 0
		for y0 in partials:
			var y := float(y0)
			if absf(x) < absf(y):
				var t := x
				x = y
				y = t
			var hi := x + y
			var lo := y - (hi - x)
			if lo != 0.0:
				partials[i] = lo
				i += 1
			x = hi
		# partials[i:] = [x] — potong ekor lalu tambah hi berjalan.
		partials = partials.slice(0, i)
		partials.append(x)
	# Jumlahkan dari partial terkecil (ascending) — error <= ~1 ulp total.
	var total := 0.0
	for p in partials:
		total += float(p)
	return total


## round() Python = banker's rounding (half-to-even). Mirror
## HeroArchetypes._py_round (dibuat lokal supaya API port mandiri).
static func _py_round(v: float) -> int:
	var f := floorf(v)
	var diff := v - f
	if diff > 0.5:
		return int(f) + 1
	if diff < 0.5:
		return int(f)
	return int(f) if int(f) % 2 == 0 else int(f) + 1


## round(x, n) Python untuk n = 1/3/4 (situs balance): half-even atas nilai
## biner, dikembalikan sebagai float (double terdekat ke desimalnya).
## Kalikan-bulatkan-bagi POLOS SALAH bila fl(v*m) mendarat TEPAT di batas
## .5 sementara nilai exact-nya tidak (kasus nyata pipeline: 1.46475 dan
## 1.32975 pada n=4) — "double rounding". Diperbaiki dengan TwoProd
## Dekker: v*m exact = q + err, keputusan batas memakai tanda
## (q - floor(q) - 0.5) + err. Terikat: input game normal & |v*m| < 1e11
## sehingga split-nya exact (Dekker 1971); seri komputasi -> genap.
static func _py_round_n(v: float, n: int) -> float:
	var m := 10.0
	if n == 1:
		m = 10.0
	elif n == 3:
		m = 1000.0
	elif n == 4:
		m = 10000.0
	else:
		m = pow(10.0, float(n))
	var q := v * m
	var c := 134217729.0 * v  # 2^27 + 1 (Dekker split)
	var v_hi := c - (c - v)
	var v_lo := v - v_hi
	# m kecil & exact -> split (m, 0); kedua suku exact (<= 41 bit).
	var err := (v_hi * m - q) + v_lo * m
	var f := floorf(q)
	var s := (q - f - 0.5) + err
	var k := int(f)
	if s > 0.0:
		k += 1
	elif s == 0.0 and k % 2 != 0:
		k += 1
	return float(k) / m


## (rasio_target, budget_target) untuk satu hero (hero_balance.py:132-176).
## Return [] kalau DPS/EHP <= 0 (None di py); kalau tidak Array 6 elemen
## [m, ratio, budget, price_corr, school, style] (urutan tuple py).
static func hero_target(stats: Dictionary, pool: Dictionary) -> Array:
	var m := metrics(stats)
	var ht := str(stats.get("__hero_type__", ""))
	var arch := HeroArchetypes.get_archetype(ht, stats)
	if float(m["dps"]) <= 0.0 or float(m["ehp"]) <= 0.0:
		return []
	var style := _str_or(arch, "playstyle", "FIGHTER")
	var school := _str_or(arch, "dmg_type", "PHYSICAL")
	var band: Array = TARGET_RATIO.get(style, TARGET_RATIO["FIGHTER"])
	var tgt_ratio := 0.5 * (float(band[0]) + float(band[1])) \
		* (1.0 + float(SCHOOL_RATIO_BONUS.get(school, 0.0)))
	var cur_ratio := float(m["ehp"]) / float(m["dps"])
	var ratio := cur_ratio * (1.0 - RATIO_BLEND) + tgt_ratio * RATIO_BLEND
	var b := float(m["budget"]) * float(STYLE_POWER.get(style, 1.0))
	if BUDGET_COMPRESS > 0.0 and float(pool.get("p50_budget", 0.0)) > 0.0:
		b = b * pow(float(pool["p50_budget"]) / maxf(b, 1e-9),
			BUDGET_COMPRESS)
	var price_corr := 1.0
	# pool.get("meta_med") bisa None (dibangun pemanggil) -> 0.0 = lewati.
	var meta_med_v: Variant = pool.get("meta_med", 0.0)
	var meta_med := 0.0
	if meta_med_v is float:
		meta_med = meta_med_v
	elif meta_med_v is int:
		meta_med = float(meta_med_v)
	if meta_med > 0.0:
		var rel := float(m["budget"]) / meta_med
		if rel > float(META_EFF_BAND[1]):
			b *= pow(float(META_EFF_BAND[1]) / rel, META_EFF_DAMP)
		elif rel < float(META_EFF_BAND[0]):
			b *= pow(float(META_EFF_BAND[0]) / rel, META_EFF_DAMP)
	# pool.get("eff_by_bucket") or {} — None -> {} (persis `or` Python).
	var eff_by_bucket_v: Variant = pool.get("eff_by_bucket", {})
	var eff_by_bucket := {}
	if eff_by_bucket_v is Dictionary:
		eff_by_bucket = eff_by_bucket_v
	var bucket := _py_round(float(m["cost"]) / float(COST_BUCKET)) \
		* COST_BUCKET
	var med_eff := float(eff_by_bucket.get(bucket, 0.0))
	if med_eff != 0.0 and float(m["cost"]) > 0.0:
		var rel2 := (float(m["budget"]) / float(m["cost"])) / med_eff
		if rel2 > float(COST_EFF_BAND[1]):
			price_corr = pow(float(COST_EFF_BAND[1]) / rel2, COST_EFF_DAMP)
		elif rel2 < float(COST_EFF_BAND[0]):
			price_corr = pow(float(COST_EFF_BAND[0]) / rel2, COST_EFF_DAMP)
		b *= price_corr
	return [m, ratio, b, price_corr, school, style]


## (mult_hp, mult_damage, mult_skill) satu hero (hero_balance.py:179-200).
## Return [y, x_dmg, x_sk, t] (t = Array hero_target, atau null).
static func stat_multipliers(stats: Dictionary, pool: Dictionary) -> Array:
	var t := hero_target(stats, pool)
	if t.is_empty():
		return [1.0, 1.0, 1.0, null]
	var m: Dictionary = t[0]
	var ratio := float(t[1])
	var b := float(t[2])
	var share := 1.0 / (1.0 + (W_EHP * EHP_PER_HP * ratio) / W_DPS)
	var new_dps := b * share / W_DPS
	var new_ehp := b * (1.0 - share) / (W_EHP * EHP_PER_HP)
	var x := new_dps / float(m["dps"]) if float(m["dps"]) > 0.0 else 1.0
	var y := new_ehp / float(m["ehp"]) if float(m["ehp"]) > 0.0 else 1.0
	var x_dmg := 1.0 + (x - 1.0) * (1.0 - float(m["burst"]) * 1.15)
	var x_sk := 1.0 + (x - 1.0) * (float(m["burst"]) * 1.15)
	return [_clamp(y, HP_MULT_RANGE), _clamp(x_dmg, DMG_MULT_RANGE),
		_clamp(x_sk, DMG_MULT_RANGE), t]


## Faktor koreksi damage fisik (hero_balance.py:203-207). Mati di game
## (ENABLE_SCHOOL_MOD false + SCHOOL_PARITY true) — dipertahankan 1:1.
static func school_mod(school: String) -> float:
	if not ENABLE_SCHOOL_MOD or school != "physical":
		return 1.0
	return minf(SCHOOL_MOD_CAP, 1.0 / tower_phys_factor())


# ─── C. CATCH-UP STARTER (hero_balance.py:210-263) ───────────────────────
## Sisa catch-up menurut level (hero_balance.py:211-223).
static func starter_level_factor(level: int) -> float:
	var lv := maxi(1, level)
	var t := float(lv - STARTER_CATCHUP_LV0) / float(maxi(
		1, STARTER_CATCHUP_LV1 - STARTER_CATCHUP_LV0))
	t = clampf(t, 0.0, 1.0)
	return 1.0 - (1.0 - STARTER_CATCHUP_DECAY) * t


## Multiplier (hp, dmg) hero starter (hero_balance.py:226-246). Urutan
## operasi disalin PERSIS (validasi: bit-identik dengan Pygame).
static func starter_catchup(hero_type: String, boss_unlocks: int,
		level: int) -> Vector2:
	if not ENABLE_STARTER_CATCHUP or not (hero_type in STARTER_HEROES):
		return Vector2.ONE
	var t := clampf(float(maxi(0, boss_unlocks))
		/ float(STARTER_CATCHUP_REF), 0.0, 1.0)
	var k := 1.0 + (STARTER_CATCHUP_MAX - 1.0) * (1.0 - t) \
		* starter_level_factor(level)
	if k <= STARTER_CATCHUP_EPS:
		return Vector2.ONE
	return Vector2(1.0 + (k - 1.0) * STARTER_HP_SHARE,
		1.0 + (k - 1.0) * STARTER_DMG_SHARE)


## (hp, damage) starter SESUDAH catch-up (hero_balance.py:249-254).
static func starter_catchup_stats(hero_type: String, stats: Dictionary,
		boss_unlocks: int, level: int) -> Vector2i:
	var mult := starter_catchup(hero_type, boss_unlocks, level)
	return Vector2i(
		maxi(1, _py_round(_fnum(stats, "hp", 1.0) * mult.x)),
		maxi(1, _py_round(_fnum(stats, "damage", 1.0) * mult.y)))


## Jumlah hero unlock (bukan starter) yang sudah dibeli
## (hero_balance.py:257-260). `purchased` non-Array (None di py) -> 0;
## entri kembar ikut terhitung (len() polos).
static func boss_unlocks_for_purchases(purchased: Variant) -> int:
	if not (purchased is Array):
		return 0
	if (purchased as Array).is_empty():
		return 0
	var n := 0
	for h in (purchased as Array):
		if not (str(h) in STARTER_HEROES):
			n += 1
	return maxi(0, n)


# ─── B. KOREKSI SEKOLAH (hero_balance.py:266-352) ────────────────────────
## DPS yang benar-benar masuk ke boss lawan hero ini
## (hero_balance.py:266-283). Parameter `m` di py tidak dipakai badannya
## (hanya dps) sehingga tidak dibawa ke sini.
static func _eff_dps(ht: String, s: Dictionary, dps: float) -> float:
	var arch := HeroArchetypes.get_archetype(ht, s)
	var rbv: Variant = s.get("unlock_require_boss", ht)
	var rb := ht
	if rbv is String and rbv != "":
		rb = rbv
	var r: Variant = HeroArchetypes.BOSS_RESISTANCES.get(rb, {})
	var armor := 0
	var mr := 0.0
	if r is Dictionary and not (r as Dictionary).is_empty():
		armor = int((r as Dictionary)["armor"])
		mr = float((r as Dictionary)["magic_resist"])
	else:
		var rr := HeroArchetypes._resist_from_profile("balanced",
			str(s.get("boss_class", "mini")))
		armor = int(rr[0])
		mr = float(rr[1])
	var mult := 0.0
	if str(arch["dmg_type"]) == "PHYSICAL":
		mult = HeroArchetypes.physical_mitigation(float(armor))
	else:
		mult = 1.0 - mr
	return dps * mult


## Skor power hero SETELAH multiplier (hero_balance.py:286-300): rumus
## 0.8*DPS + 0.2*EHP relatif median pool, SAMA PERSIS dengan audit.
static func _final_power(m: Dictionary, y: float, x_dmg: float,
		x_sk: float, med_dps: float, med_ehp: float) -> float:
	var dps := (float(m["dmg"]) * x_dmg) * 60.0 / float(m["cd"]) \
		+ (float(m["skill"]) * x_sk) * 60.0 / float(m["skcd"])
	var ehp := float(m["ehp"]) * y
	return 0.8 * dps / med_dps + 0.2 * ehp / med_ehp


## Multiplier DAMAGE per sel arketipe (hero_balance.py:303-352).
## Return [faktor, laporan] (faktor: {"SEKOLAH|GAYA": g}, laporan null
## kalau tak ada hero valid). IPF/raking dua arah, iters tetap.
static func cell_parity_factors(boss: Dictionary, met: Dictionary,
		raw: Dictionary, med_dps: float, med_ehp: float,
		iters: int = 18) -> Array:
	var cell := {}
	var base := {}
	var valid: Array = []
	for ht in boss:
		var s: Dictionary = boss[ht]
		var m: Dictionary = met[ht]
		if float(m["dps"]) <= 0.0:
			continue
		var arch := HeroArchetypes.get_archetype(str(ht), s)
		# dmg_type LANGSUNG (py: arch["dmg_type"] -> KeyError kalau hilang).
		cell[ht] = str(arch["dmg_type"]) + "|" \
			+ _str_or(arch, "playstyle", "FIGHTER")
		var r: Array = raw[ht]
		base[ht] = [float(r[0]), float(r[1]), float(r[2])]
		valid.append(ht)
	if valid.is_empty():
		return [{}, null]
	var boots: Array = []
	for ht in valid:
		var bb: Array = base[ht]
		boots.append(_final_power(met[ht], bb[0], bb[1], bb[2],
			med_dps, med_ehp))
	var target := _fmean(boots)
	var f := {}
	for ht in valid:
		f[cell[ht]] = 1.0
	var by_cell := {}
	for ht in valid:
		var c := str(cell[ht])
		if not by_cell.has(c):
			by_cell[c] = []
		(by_cell[c] as Array).append(ht)
	for _i in range(iters):
		for c in by_cell:
			var hts: Array = by_cell[c]
			var vals: Array = []
			for h in hts:
				var bb2: Array = base[h]
				var g := float(f[c])
				vals.append(_final_power(met[h], bb2[0], bb2[1] * g,
					bb2[2] * g, med_dps, med_ehp))
			var cur := _fmean(vals)
			if cur > 0.0:
				f[c] = _clamp(float(f[c]) * (target / cur),
					[1.0 / CELL_PARITY_CAP, CELL_PARITY_CAP])
		var all_vals: Array = []
		for h in valid:
			var bb3: Array = base[h]
			var g2 := float(f[cell[h]])
			all_vals.append(_final_power(met[h], bb3[0], bb3[1] * g2,
				bb3[2] * g2, med_dps, med_ehp))
		var mean_all := _fmean(all_vals)
		if mean_all > 0.0:
			var g3 := pow(target / mean_all, 0.9)
			for c2 in f:
				f[c2] = _clamp(float(f[c2]) * g3,
					[1.0 / CELL_PARITY_CAP, CELL_PARITY_CAP])
	var cells := {}
	for c3 in f:
		cells[c3] = _py_round_n(float(f[c3]), 4)
	var report := {"pool_target": _py_round_n(target, 3), "cells": cells}
	return [f, report]


## Stat hero unlock SEBELUM balance (hero_balance.py:355-381). Di py dibaca
## dari bosses.boss_data; di sini `boss_tables` disuntik =
## {"mini": {boss_type: entri}, "true": {...}} agar fungsinya murni.
static func pristine_boss_stats(boss_tables: Dictionary) -> Dictionary:
	var out := {}
	for boss_class in ["mini", "true"]:
		var table: Dictionary = boss_tables.get(boss_class, {})
		for boss_type in table:
			var bd: Dictionary = table[boss_type]
			var hu: Variant = bd.get("hero_unlock", null)
			if not (hu is Dictionary) or (hu as Dictionary).is_empty():
				continue
			var d := (hu as Dictionary).duplicate()
			if not d.has("unlock_cost"):
				d["unlock_cost"] = 4500
			d["unlock_require_boss"] = boss_type
			d["is_boss_hero"] = true
			d["boss_class"] = boss_class
			out[boss_type] = d
	return out


## Hitung multiplier final SEMUA hero sekaligus (hero_balance.py:384-569).
## `boss_unlocks`/`level` = input catch-up starter (py: dibaca dari
## __main__.game_instance; default 0/1 di luar match).
static func resolve_catalog(catalog: Dictionary, boss_unlocks: int = 0,
		level: int = 1) -> Dictionary:
	var out := {}
	var boss := {}
	for ht in catalog:
		var stats: Dictionary = catalog[ht]
		if not bool(stats.get("is_boss_hero", false)):
			continue
		var s := stats.duplicate()
		s["__hero_type__"] = ht
		boss[ht] = s
	if boss.is_empty():
		return out

	var met := {}
	for ht2 in boss:
		met[ht2] = metrics(boss[ht2])
	var ratios: Array = []
	for ht3 in met:
		var m: Dictionary = met[ht3]
		if float(m["dps"]) > 0.0 and float(m["ehp"]) > 0.0:
			ratios.append(float(m["ehp"]) / float(m["dps"]))
	ratios.sort()
	var budgets: Array = []
	for ht4 in met:
		budgets.append(float((met[ht4] as Dictionary)["budget"]))
	budgets.sort()
	var buckets := {}
	for ht5 in met:
		var m2: Dictionary = met[ht5]
		if float(m2["cost"]) <= 0.0 or float(m2["budget"]) <= 0.0:
			continue
		var b := _py_round(float(m2["cost"]) / float(COST_BUCKET)) \
			* COST_BUCKET
		if not buckets.has(b):
			buckets[b] = []
		(buckets[b] as Array).append(
			float(m2["budget"]) / float(m2["cost"]))
	var eff_by_bucket := {}
	for b2 in buckets:
		var v: Array = buckets[b2]
		if v.size() >= COST_EFF_MIN_GROUP:
			eff_by_bucket[b2] = _median(v)
	var meta_costs := {}
	for stats2 in catalog.values():
		if bool((stats2 as Dictionary).get("is_boss_hero", false)):
			var c := _fnum(stats2, "unlock_cost", 0.0)
			if not meta_costs.has(c):
				meta_costs[c] = []
			(meta_costs[c] as Array).append(
				float(metrics(stats2)["budget"]))
	var meta_med := 0.0
	for c2 in meta_costs:
		var vv: Array = meta_costs[c2]
		if float(c2) > 0.0 and vv.size() >= 20:
			meta_med = _median(vv)
			break
	var n_b := budgets.size() if budgets.size() > 0 else 1
	var pool := {"med_ratio": _median(ratios), "med_budget": _median(budgets),
		"p50_budget": float(budgets[n_b / 2]) if not budgets.is_empty() else 0.0,
		"eff_by_bucket": eff_by_bucket, "meta_med": meta_med}
	var dps_vals: Array = []
	var ehp_vals: Array = []
	for ht6 in met:
		dps_vals.append(float((met[ht6] as Dictionary)["dps"]))
		ehp_vals.append(float((met[ht6] as Dictionary)["ehp"]))
	var med_dps := _median(dps_vals)
	if med_dps == 0.0:
		med_dps = 1.0
	var med_ehp := _median(ehp_vals)
	if med_ehp == 0.0:
		med_ehp = 1.0
	pool["med_dps"] = med_dps
	pool["med_ehp"] = med_ehp

	var raw := {}
	for ht7 in boss:
		raw[ht7] = stat_multipliers(boss[ht7], pool)

	# ── paritas SEL arketipe (identitas peran) ──
	if CELL_PARITY:
		var cf := cell_parity_factors(boss, met, raw, med_dps, med_ehp)
		var fac: Dictionary = cf[0]
		var rep: Variant = cf[1]
		last["parity"] = rep if rep is Dictionary else {}
		if not fac.is_empty():
			for ht8 in raw:
				var r: Array = raw[ht8]
				var t: Variant = r[3]
				var key := ""
				if t is Array and not (t as Array).is_empty():
					key = str((t as Array)[4]) + "|" + str((t as Array)[5])
				var g := float(fac.get(key, 1.0))
				raw[ht8] = [float(r[0]), float(r[1]) * g,
					float(r[2]) * g, t]

	# ── JANGKAR: rata-rata multiplier tiap stat = 1.0 ──
	var fin := {}
	for ht9 in raw:
		var r2: Array = raw[ht9]
		fin[ht9] = [float(r2[0]), float(r2[1]), float(r2[2])]
	var ranges := [HP_MULT_RANGE, DMG_MULT_RANGE, DMG_MULT_RANGE]
	for i in range(3):
		var col: Array = []
		for ht10 in fin:
			col.append(float((fin[ht10] as Array)[i]))
		var avg := _fmean(col)
		if avg == 0.0:
			avg = 1.0
		for ht11 in fin:
			var row: Array = fin[ht11]
			row[i] = _clamp(float(row[i]) / avg, ranges[i])

	# ── paritas SEKOLAH pada damage EFEKTIF, PER KELAS BOSS ──
	if SCHOOL_PARITY:
		for _pass in range(8):
			var eff := {}
			for ht12 in boss:
				var s2: Dictionary = boss[ht12]
				var m3: Dictionary = met[ht12]
				if float(m3["dps"]) <= 0.0:
					continue
				var row2: Array = fin[ht12]
				var x_dmg := float(row2[1])
				var x_sk := float(row2[2])
				var dps := (float(m3["dmg"]) * x_dmg) * 60.0 \
						/ float(m3["cd"]) \
					+ (float(m3["skill"]) * x_sk) * 60.0 / float(m3["skcd"])
				var e := _eff_dps(str(ht12), s2, dps)
				var rr: Array = raw[ht12]
				var tt: Array = rr[3]
				var key2 := str(s2.get("boss_class", "mini")) + "|" \
					+ str(tt[4])
				if not eff.has(key2):
					eff[key2] = []
				(eff[key2] as Array).append(e)
			var by_cls := {}
			for key3 in eff:
				var dc := str(key3).split("|")[0]
				if not by_cls.has(dc):
					by_cls[dc] = []
				(by_cls[dc] as Array).append_array(eff[key3])
			var tgt := {}
			for dc2 in by_cls:
				var vv2: Array = by_cls[dc2]
				if not vv2.is_empty():
					tgt[dc2] = _fmean(vv2)
			if tgt.is_empty():
				break
			var moved := 0.0
			var f2 := {}
			for key4 in eff:
				var vals2: Array = eff[key4]
				var cur := _fmean(vals2)
				var dc3 := str(key4).split("|")[0]
				var t_dc := float(tgt.get(dc3, 0.0))
				if t_dc <= 0.0 or cur <= 0.0:
					f2[key4] = 1.0
					continue
				var f := _clamp(t_dc / cur,
					[1.0 / SCHOOL_PARITY_CAP, SCHOOL_PARITY_CAP])
				f2[key4] = f
				moved = maxf(moved, absf(f - 1.0))
			var wavg := {}
			var classes := {}
			for k5 in f2:
				classes[str(k5).split("|")[0]] = true
			for dc4 in classes:
				var ks: Array = []
				for k6 in f2:
					if str(k6).split("|")[0] == str(dc4):
						ks.append(k6)
				var tot := 0
				for k7 in ks:
					tot += ((eff[k7]) as Array).size()
				if tot == 0:
					tot = 1
				var acc := 0.0
				for k8 in ks:
					acc += float(f2[k8]) \
						* float(((eff[k8]) as Array).size())
				wavg[dc4] = acc / float(tot)
			for ht13 in fin:
				var dc5 := str((boss[ht13] as Dictionary).get(
					"boss_class", "mini"))
				var rr2: Array = raw[ht13]
				var tt2: Array = rr2[3]
				var key5 := dc5 + "|" + str(tt2[4])
				var g2 := float(f2.get(key5, 1.0)) \
					/ float(wavg.get(dc5, 1.0))
				var row3: Array = fin[ht13]
				row3[1] = float(row3[1]) * g2
				row3[2] = float(row3[2]) * g2
			var par: Dictionary = last.get("parity", {})
			var schools := {}
			for k9 in f2:
				schools[k9] = _py_round_n(float(f2[k9]), 4)
			par["schools"] = schools
			last["parity"] = par
			if moved < 0.002:
				break

	for ht14 in fin:
		var row4: Array = fin[ht14]
		var y2 := float(row4[0])
		var x2 := float(row4[1])
		var k2 := float(row4[2])
		var rr3: Array = raw[ht14]
		var t3: Array = rr3[3]
		var s_mod := 1.0
		if not SCHOOL_PARITY:
			s_mod = school_mod(str(t3[4]).to_lower())
		var tm: Dictionary = t3[0]
		out[ht14] = {
			"hp": _py_round_n(y2, 4), "dmg": _py_round_n(x2 * s_mod, 4),
			"skill": _py_round_n(k2 * s_mod, 4),
			"dbg": {"ratio_from": _py_round_n(
						float(tm["ehp"]) / float(tm["dps"]), 3)
					if float(tm["dps"]) > 0.0 else 0.0,
					"ratio_to": _py_round_n(float(t3[1]), 3),
					"price_corr": _py_round_n(float(t3[3]), 4),
					"playstyle": str(t3[5]), "dmg_type": str(t3[4]),
					"boss_class": (boss[ht14] as Dictionary).get(
						"boss_class", null)},
		}

	# ── starter: catch-up saja (basis statnya kecil, tidak ikut rebudget)
	for ht15 in catalog:
		var stats3: Dictionary = catalog[ht15]
		if bool(stats3.get("is_boss_hero", false)):
			continue
		var yc := starter_catchup(str(ht15), boss_unlocks, level)
		out[ht15] = {
			"hp": _py_round_n(yc.x, 4), "dmg": _py_round_n(yc.y, 4),
			"skill": 1.0,
			"dbg": {"starter_unlocks": boss_unlocks, "playstyle": null,
					"dmg_type": str(HeroArchetypes.get_archetype(
						str(ht15), stats3)["dmg_type"]),
					"boss_class": null},
		}
	return out


# ─── boss resistances: kalibrasi profil (hero_balance.py:572-649) ───────
static func _cal_zero_mean(dc_rows: Array) -> Dictionary:
	var n := dc_rows.size() if dc_rows.size() > 0 else 1
	var g0 := 0.0
	var g1 := 0.0
	for r in dc_rows:
		var mods0: Array = HeroArchetypes.BOSS_RESIST_PROFILE_MODS.get(
			str((r as Dictionary).get("profile", "balanced")), [0.0, 0.0])
		g0 += float(mods0[0])
		g1 += float(mods0[1])
	g0 /= float(n)
	g1 /= float(n)
	var out := {}
	for p in HeroArchetypes.BOSS_RESIST_PROFILE_MODS:
		var v: Array = HeroArchetypes.BOSS_RESIST_PROFILE_MODS[p]
		out[p] = [float(v[0]) - g0, float(v[1]) - g1]
	return out


## [ratio, avg_armor, avg_mr] — akumulasi `+=` SEQUENTIAL persis py (urutan
## baris menentukan bit terakhir; jangan diganti _fsum).
static func _cal_stats_for(dc: String, dc_rows: Array, mods: Dictionary,
		sa: float, sm: float) -> Array:
	var p_sum := 0.0
	var m_sum := 0.0
	var p_n := 0
	var m_n := 0
	var a_sum := 0.0
	var mr_sum := 0.0
	for r in dc_rows:
		var rr := HeroArchetypes._resist_from_profile(
			str((r as Dictionary).get("profile", "balanced")), dc,
			{}, mods, sa, sm)
		var armor := float(rr[0])
		var mr := float(rr[1])
		a_sum += armor
		mr_sum += mr
		var dps := 0.0
		var dv: Variant = (r as Dictionary).get("dps", 0.0)
		if dv is float:
			dps = dv
		elif dv is int:
			dps = float(dv)
		if str((r as Dictionary).get("dmg_type", "")) == "PHYSICAL":
			p_sum += dps * HeroArchetypes.physical_mitigation(armor)
			p_n += 1
		else:
			m_sum += dps * (1.0 - mr)
			m_n += 1
	var n := dc_rows.size() if dc_rows.size() > 0 else 1
	var ratio := 1.0
	if p_n > 0 and m_n > 0:
		ratio = (m_sum / float(maxi(m_n, 1))) \
			/ maxf(p_sum / float(maxi(p_n, 1)), 1e-9)
	return [ratio, a_sum / float(n), mr_sum / float(n)]


## [sa, sm, ratio, avg_armor, avg_mr] — grid n_step×n_step, first-wins
## (`<` ketat) persis py. `scale_lo` TIDAK dipakai py (grid mulai 1.0).
static func _cal_solve(dc: String, dc_rows: Array, mods: Dictionary,
		target: float, scale_hi: float, n_step: int,
		lock: bool) -> Array:
	var b: Array = HeroArchetypes.BOSS_RESIST_BASE[dc]
	var best := 9e9
	var bsa := 1.0
	var bsm := 1.0
	var denom := float(maxi(n_step - 1, 1))
	for i in range(n_step):
		for j in range(n_step):
			var sa := 1.0 + (scale_hi - 1.0) * float(i) / denom
			var sm := 1.0 + (scale_hi - 1.0) * float(j) / denom
			var st := _cal_stats_for(dc, dc_rows, mods, sa, sm)
			var pen := 0.0
			if lock:
				pen += maxf(0.0, absf(float(st[1]) - float(b[0])) - 0.6) \
					* 0.5
				pen += maxf(0.0, absf(float(st[2]) - float(b[1])) - 0.006) \
					* 120.0
			var score := absf(float(st[0]) - target) + pen
			if score < best:
				best = score
				bsa = sa
				bsm = sm
	var fin := _cal_stats_for(dc, dc_rows, mods, bsa, bsm)
	return [bsa, bsm, float(fin[0]), float(fin[1]), float(fin[2])]


## Kalibrasi armor/MR boss -> [tabel BOSS_RESISTANCES, report]
## (hero_balance.py:572-649). Aturan keras: rata-rata armor & MR dikunci di
## baseline kelas; hanya DUA SKALA yang dicari; DPS bahan = sesudah
## re-budget (pemanggil yang menyiapkan rows).
static func calibrate_boss_resistances(rows: Array, target_ratio: float = 0.0,
		scale_lo: float = 0.6, scale_hi: float = 1.8,
		n_step: int = 25) -> Array:
	# target_ratio or TARGET — hanya 0.0 yang diganti (negatif ikut
	# py: dipertahankan, walau tak ada pemanggil waras yang memakainya).
	var target := target_ratio
	if target == 0.0:
		target = HeroArchetypes.BOSS_RESIST_TARGET_RATIO
	# scale_lo disengaja tak dipakai (grid py mulai 1.0) — dipertahankan
	# sebagai parameter agar signature 1:1 dengan calibrate di py.
	var by_class := {}
	for r in rows:
		# LANGSUNG (py: r["boss_class"] -> KeyError kalau hilang).
		var dc := str((r as Dictionary)["boss_class"])
		if not by_class.has(dc):
			by_class[dc] = []
		(by_class[dc] as Array).append(r)
	var mods_by_class := {}
	var report := {}
	var scales := {}
	for dc2 in by_class:
		var dc_rows: Array = by_class[dc2]
		var mods := _cal_zero_mean(dc_rows)
		var solved := _cal_solve(dc2, dc_rows, mods, target, scale_hi,
			n_step, true)
		var sa := float(solved[0])
		var sm := float(solved[1])
		var ratio := float(solved[2])
		var av_a := float(solved[3])
		var av_mr := float(solved[4])
		var b2: Array = HeroArchetypes.BOSS_RESIST_BASE[dc2]
		for _k in range(6):
			var da := {}
			for p in mods:
				var v: Array = mods[p]
				da[p] = [float(v[0]) - (av_a - float(b2[0])), float(v[1])]
			var db := {}
			for p2 in da:
				var v2: Array = da[p2]
				db[p2] = [float(v2[0]),
					float(v2[1]) - (av_mr - float(b2[1]))]
			var s2 := _cal_stats_for(dc2, dc_rows, db, sa, sm)
			var r2 := float(s2[0])
			if absf(r2 - target) <= absf(ratio - target) + 0.02:
				mods = db
				ratio = r2
				av_a = float(s2[1])
				av_mr = float(s2[2])
				break
			var s3 := _cal_stats_for(dc2, dc_rows, da, sa, sm)
			var a3 := float(s3[1])
			if absf(a3 - float(b2[0])) < absf(av_a - float(b2[0])):
				mods = da
				ratio = float(s3[0])
				av_a = a3
				av_mr = float(s3[2])
		mods_by_class[dc2] = mods
		scales[dc2] = {"armor": sa, "mr": sm}
		report[dc2] = {"magic_over_phys": _py_round_n(ratio, 3),
			"avg_armor": _py_round_n(av_a, 1),
			"avg_mr": _py_round_n(av_mr, 4),
			"scale": {"armor": sa, "mr": sm}, "mods": mods}
	var sc_out := {}
	for dc3 in scales:
		var sc: Dictionary = scales[dc3]
		sc_out[dc3] = {"armor_scale": float(sc["armor"]),
			"mr_scale": float(sc["mr"])}
	report["_scales"] = sc_out
	var mini_rep: Dictionary = report.get("mini", {})
	report["_mods_mini"] = mini_rep.get("mods", {})

	var res := {}
	for r2 in rows:
		var dc4 := str((r2 as Dictionary).get("boss_class", ""))
		var sc2: Dictionary = scales.get(dc4, {"armor": 1.0, "mr": 1.0})
		var rr := HeroArchetypes._resist_from_profile(
			str((r2 as Dictionary).get("profile", "balanced")), dc4,
			{}, mods_by_class.get(dc4, {}),
			float(sc2["armor"]), float(sc2["mr"]))
		res[str((r2 as Dictionary)["boss_type"])] = {
			"armor": int(rr[0]),
			"magic_resist": _py_round_n(float(rr[1]), 3),
			"profile": str((r2 as Dictionary).get("profile", "balanced")),
			"boss_class": dc4}
	return [res, report]


## Hasil antara untuk audit & tools (hero_balance.py:660).
static var last := {"table": {}, "pool": {}, "parity": {}}


static func _is_dbg() -> bool:
	return OS.has_environment("MYSTIC_DEBUG_BALANCE")


## Kalikan stat boss dengan faktor SERAGAM supaya rata-rata pool kembali ke
## angka SEBELUM balance (hero_balance.py:663-702). Return faktornya.
static func _pool_mean_rescale(catalog: Dictionary, before: Dictionary,
		which: String = "dps", tol: float = 0.005) -> float:
	if before.is_empty():
		return 1.0
	var ids: Array = []
	for k in before:
		if catalog.has(k) and bool(
				(catalog[k] as Dictionary).get("is_boss_hero", false)):
			ids.append(k)
	if ids.is_empty():
		return 1.0
	var key := "dps" if which == "dps" else "ehp"
	var cur_vals: Array = []
	for k2 in ids:
		cur_vals.append(float(metrics(catalog[k2])[key]))
	var cur := _fmean(cur_vals)
	if cur == 0.0:
		cur = 1.0
	var want_vals: Array = []
	for k3 in ids:
		want_vals.append(float((before[k3] as Dictionary)[key]))
	var want := _fmean(want_vals)
	if want <= 0.0 or cur <= 0.0:
		return 1.0
	var g := _clamp(want / cur,
		[1.0 - POOL_MEAN_TOL_MAX, 1.0 + POOL_MEAN_TOL_MAX])
	if absf(g - 1.0) < tol:
		return 1.0
	for k4 in ids:
		var v: Dictionary = catalog[k4]
		if which == "dps":
			var keys := ["damage", "skill_damage"]
			keys.append_array(SKILL_QWER_KEYS)
			for kk in keys:
				if float(_fnum(v, kk, 0.0)) != 0.0:
					v[kk] = maxi(0, _py_round(
						_fnum(v, kk, 0.0) * g))
		else:
			v["hp"] = maxi(1, _py_round(_fnum(v, "hp", 1.0) * g))
		var b: Variant = v.get("__bal", null)
		if b is Dictionary and not (b as Dictionary).is_empty():
			var bd: Dictionary = b
			if which == "dps":
				bd["dmg"] = _py_round_n(float(bd["dmg"]) * g, 4)
				bd["skill"] = _py_round_n(float(bd["skill"]) * g, 4)
			else:
				bd["hp"] = _py_round_n(float(bd["hp"]) * g, 4)
	return g


## Koreksi kecil LANGSUNG pada stat final (hero_balance.py:705-837):
## damage dikalikan faktor (dibatasi FINAL_CORR_CAP) sampai DPS efektif
## fisik == sihir per kelas boss. `cell_band` null (jalur game) = hanya
## paritas sekolah; blok sel dihitung tapi faktornya 1.0 (persis py).
static func _final_fixpoint(catalog: Dictionary, school_target: float = 1.0,
		cell_band: Variant = null, passes: int = 40, damp: float = 0.85,
		tol: float = 0.002) -> Dictionary:
	var ids: Array = []
	for ht in catalog:
		var v: Dictionary = catalog[ht]
		if bool(v.get("is_boss_hero", false)) \
				and float(metrics(v)["dps"]) > 0.0:
			ids.append(ht)
	if ids.size() < 20:
		return {"skipped": "hero terlalu sedikit"}
	var fac := {}
	for ht2 in ids:
		fac[ht2] = 1.0
	var info := {}
	for _p in range(passes):
		var f_sch := {}
		var f_cell := {}
		var eff := {}
		for ht3 in ids:
			var v2: Dictionary = catalog[ht3]
			var m := metrics(v2)
			var rbv: Variant = v2.get("unlock_require_boss", ht3)
			var rb := str(ht3)
			if rbv is String and rbv != "":
				rb = rbv
			var rr := HeroArchetypes.get_boss_resistances(rb,
				str(v2.get("boss_class", "mini")))
			var school := str(HeroArchetypes.get_archetype(
				str(ht3), v2)["dmg_type"])
			var mit := 0.0
			if school == "PHYSICAL":
				mit = HeroArchetypes.physical_mitigation(float(rr[0]))
			else:
				mit = 1.0 - float(rr[1])
			var key := str(v2.get("boss_class", "mini")) + "|" + school
			if not eff.has(key):
				eff[key] = []
			(eff[key] as Array).append(
				float(m["dps"]) * float(fac[ht3]) * mit)
		var by_cls := {}
		for key2 in eff:
			var dc := str(key2).split("|")[0]
			if not by_cls.has(dc):
				by_cls[dc] = []
			(by_cls[dc] as Array).append_array(eff[key2])
		for key3 in eff:
			var vals: Array = eff[key3]
			var cur := _fmean(vals)
			var dc2 := str(key3).split("|")[0]
			var cls_vals: Array = by_cls.get(dc2, [])
			var tgt := _fmean(cls_vals) * school_target \
				if not cls_vals.is_empty() else cur
			if cur > 0.0 and tgt > 0.0:
				f_sch[key3] = pow(tgt / cur, damp)
		var dps_all: Array = []
		var ehp_all: Array = []
		for h in ids:
			var mm := metrics(catalog[h])
			dps_all.append(float(mm["dps"]))
			ehp_all.append(float(mm["ehp"]))
		var med_d := _fmean(dps_all)
		if med_d == 0.0:
			med_d = 1.0
		var med_e := _fmean(ehp_all)
		if med_e == 0.0:
			med_e = 1.0
		var cell := {}
		for ht4 in ids:
			var a := HeroArchetypes.get_archetype(str(ht4),
				catalog[ht4])
			var m2 := metrics(catalog[ht4])
			var pw := 0.8 * float(m2["dps"]) * float(fac[ht4]) / med_d \
				+ 0.2 * float(m2["ehp"]) / med_e
			var style := str(a.get("playstyle", ""))
			var key4 := str(a["dmg_type"]) + "|" + style
			if not cell.has(key4):
				cell[key4] = []
			(cell[key4] as Array).append([ht4, pw])
		var allpw: Array = []
		for c in cell:
			for pair in (cell[c] as Array):
				allpw.append(float((pair as Array)[1]))
		var tgt_cell := _fmean(allpw) if not allpw.is_empty() else 1.0
		if cell_band != null:
			var band: Array = cell_band
			for c2 in cell:
				var pws: Array = []
				for pair2 in (cell[c2] as Array):
					pws.append(float((pair2 as Array)[1]))
				var cur2 := _fmean(pws)
				if cur2 > 0.0:
					var gg := pow(tgt_cell / cur2, damp)
					f_cell[c2] = _clamp(gg, band)
		var moved := 0.0
		for ht5 in ids:
			var v3: Dictionary = catalog[ht5]
			var a2 := HeroArchetypes.get_archetype(str(ht5), v3)
			var style2 := str(a2.get("playstyle", ""))
			var g := float(f_sch.get(
				str(v3.get("boss_class", "mini")) + "|"
					+ str(a2["dmg_type"]), 1.0))
			g *= float(f_cell.get(
				str(a2["dmg_type"]) + "|" + style2, 1.0))
			g = _clamp(g, [1.0 / FINAL_CORR_CAP, FINAL_CORR_CAP])
			fac[ht5] = _clamp(float(fac[ht5]) * g,
				[1.0 / FINAL_CORR_CAP, FINAL_CORR_CAP])
			moved = maxf(moved, absf(g - 1.0))
		info["passes_run"] = _p + 1
		info["last_move"] = _py_round_n(moved, 4)
		if moved < tol:
			break
	for ht6 in ids:
		var g2 := float(fac[ht6])
		if absf(g2 - 1.0) < 1e-4:
			continue
		var v4: Dictionary = catalog[ht6]
		var keys2 := ["damage", "skill_damage"]
		keys2.append_array(SKILL_QWER_KEYS)
		for kk2 in keys2:
			if float(_fnum(v4, kk2, 0.0)) != 0.0:
				v4[kk2] = maxi(0, _py_round(_fnum(v4, kk2, 0.0) * g2))
		var b: Variant = v4.get("__bal", null)
		if b is Dictionary and not (b as Dictionary).is_empty():
			var bd: Dictionary = b
			bd["dmg"] = _py_round_n(float(bd["dmg"]) * g2, 4)
			bd["skill"] = _py_round_n(float(bd["skill"]) * g2, 4)
			(bd["dbg"] as Dictionary)["fix"] = _py_round_n(g2, 4)
		fac[ht6] = g2
	var fvals: Array = []
	for ht7 in fac:
		fvals.append(float(fac[ht7]))
	fvals.sort()
	info["factor_min"] = _py_round_n(float(fvals[0]), 4)
	info["factor_max"] = _py_round_n(float(fvals[fvals.size() - 1]), 4)
	info["n"] = ids.size()
	return info


## Terapkan hasil resolve_catalog() ke dict katalog (in-place)
## (hero_balance.py:840-936). `pristine` = stat mentah (padanan
## pristine_boss_stats; kalau kosong, entri boss katalog dipakai sebagai
## baseline-nya sendiri). Return katalog yang sama (referensi).
static func apply_to_catalog(catalog: Dictionary, pristine: Dictionary = {},
		boss_unlocks: int = 0, level: int = 1) -> Dictionary:
	var base := pristine
	if base.is_empty():
		base = {}
		for k in catalog:
			if bool((catalog[k] as Dictionary).get("is_boss_hero", false)):
				base[k] = (catalog[k] as Dictionary).duplicate()
	var src := catalog.duplicate(false)
	for k2 in base:
		if src.has(k2):
			src[k2] = base[k2]
	if _is_dbg():
		printerr("[hero_balance] apply_to_catalog n=%d pristine=%d"
			% [catalog.size(), base.size()])
	# py membungkus resolve dengan try/except (gagal -> katalog tak
	# tertulis); GDScript tak punya exception — resolve yang gagal
	# menghentikan test dengan LOUD (tak pernah terjadi di data valid).
	var table := resolve_catalog(src, boss_unlocks, level)
	if _is_dbg():
		printerr("[hero_balance] resolve ok, hero=%d parity=%s"
			% [table.size(), str(last.get("parity", {}))])
	var before := {}
	if POOL_MEAN_ANCHOR:
		for k3 in base:
			var mm := metrics(base[k3])
			if float(mm["dps"]) > 0.0:
				before[k3] = mm
	for ht in base:
		if table.has(ht) and table[ht] is Dictionary \
				and not (table[ht] as Dictionary).is_empty():
			var dbg: Dictionary = (table[ht] as Dictionary)["dbg"]
			var v: Dictionary = base[ht]
			dbg["raw"] = {"hp": v.get("hp"),
				"damage": v.get("damage"),
				"skill_damage": v.get("skill_damage"),
				"attack_cooldown": v.get("attack_cooldown"),
				"skill_cooldown": v.get("skill_cooldown")}
	last["table"] = table
	for ht2 in table:
		var mult: Variant = table[ht2]
		if not (mult is Dictionary) \
				or ((mult is Dictionary)
					and (mult as Dictionary).is_empty()):
			continue
		if not catalog.has(ht2):
			continue
		var stats: Dictionary = catalog[ht2]
		if not bool(stats.get("is_boss_hero", false)):
			# Starter SENGAJA tidak ditulis ke katalog (catch-up mereka
			# bergantung state pemain; satu-satunya penulis = Hero saat
			# unit dibuat, lewat starter_catchup_stats).
			continue
		var raw: Dictionary = src.get(ht2, stats)
		var md: Dictionary = mult
		stats["__bal"] = md
		stats["hp"] = maxi(1, _py_round(
			_fnum(raw, "hp", 1.0) * float(md["hp"])))
		stats["damage"] = maxi(1, _py_round(
			_fnum(raw, "damage", 1.0) * float(md["dmg"])))
		stats["skill_damage"] = maxi(0, _py_round(
			_fnum(raw, "skill_damage", 0.0) * float(md["skill"])))
		for key in SKILL_QWER_KEYS:
			if float(_fnum(raw, key, 0.0)) != 0.0:
				stats[key] = maxi(0, _py_round(
					_fnum(raw, key, 0.0) * float(md["skill"])))

	# ── jangkar rata-rata pool (SEBELUM fixpoint, persis py) ──
	last["pool_anchor"] = {}
	if POOL_MEAN_ANCHOR and not before.is_empty():
		var dps_b: Array = []
		var ehp_b: Array = []
		for k4 in before:
			dps_b.append(float((before[k4] as Dictionary)["dps"]))
			ehp_b.append(float((before[k4] as Dictionary)["ehp"]))
		last["pool_means"] = {"dps": _py_round_n(_fmean(dps_b), 1),
			"ehp": _py_round_n(_fmean(ehp_b), 1), "n": before.size()}
		var anchor := {}
		anchor["dps"] = _pool_mean_rescale(catalog, before, "dps")
		anchor["ehp"] = _pool_mean_rescale(catalog, before, "ehp")
		var kept := {}
		for k5 in anchor:
			var gv := float(anchor[k5])
			if gv != 0.0 and absf(gv - 1.0) >= 0.005:
				kept[k5] = gv
		last["pool_anchor"] = kept

	# ── koreksi akhir: paritas sekolah + sel, diukur rumus audit ──
	if FINAL_FIXPOINT:
		last["fix"] = _final_fixpoint(catalog)

	return catalog
