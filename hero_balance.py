# ================================
# hero_balance.py
#
# Satu-satunya tempat balance hero GAME DIKALIBRASI. Data mentah di
# bosses/boss_data.py tidak pernah diubah; fungsi ini membaca katalog yang
# sudah disusun _core.get_all_hero_types(), menghitung multiplier per hero,
# lalu menulis hasilnya kembali ke katalog itu (in-place) supaya toko,
# preview skill, unit test, Hero, dan AI membaca ANGKA YANG SAMA.
#
# ── ANGKA YANG MENJADI DASAR (tools/balance_audit.py, 2026-08-30) ──
# A. SEBELUM balance:
#      corr(HP, DPS) = 0.956          -> tidak ada trade-off arketipe:
#                                        hero mahal menang di DUA sumbu
#      TANK 986 DPS / 4982 EHP        -> PHYSICAL|TANK 2.0x DPS carry
#      magic 1.32x lebih efektif      -> vs mini boss (armor 12, MR .10)
#        vs boss fisik                   hero fisik cuma jadi pajak
#      starter 8.51x lebih lemah      -> 6 hero awal tidak bisa dipakai
#      <2k gem 2.79x "worth it"       -> hero murah jelas optimal
# B. SESUDAH balance pass ini (mode --ingame, n=216 hero unlock):
#      corr(HP, DPS)   0.53           trade-off nyata, tiap arketipe beda
#      identity spread 1.6x           sel terkuat/terlemah (power)
#      school ratio    1.000 / 1.000  vs mini & true boss (target 0.90-1.15)
#      boss pref       1.49           tiap boss tetap punya favorit
#      price spread    1.9x           di dalam satu band harga
#      pool mean       1.000x         REDISTRIBUSI, bukan buff/nerf global
# C. PERINGATAN YANG DIBUANG (jangan diulang):
#      - menormalkan multiplier ke MEDIAN membuat rata-rata pool -25%
#        (nerf diam-diam); yang dipakai sekarang jangkar RATA-RATA
#      - paritas hanya per SEKOLAH mengerek semua fisik (komposisi pool
#        bias: 39 tank fisik vs 25 tank sihir) dan merusak corr lagi
#      - paritas dihitung di DALAM normalisasi budget = two-way loop yang
#        tidak konvergen; paritas harus SESUDAH normalisasi
#      - paritas sel pada DPS EFEKTIF saja membuat satu sel menang di dua
#        sumbu; pakai skor POWER (0.8 DPS + 0.2 EHP) seperti audit
#      - guard di fungsi bantu ("kalau data X kosong, return {}") pernah
#        melumpuhkan SEMUA koreksi tanpa error; selalu pakai fallback
#
# Metrik yang dikejar adalah metrik yang DIUKUR audit, dengan rumus yang
# sama persis (_final_power vs identity_grid). Kalau tidak, "lolos test"
# tidak berarti apa-apa.
# ================================
"""Kalkulator balance hero (dipakai dari _core.get_all_hero_types())."""
import statistics as st

import hero_archetypes

# ─── SAKLAR ──────────────────────────────────────────────────────────────
ENABLE_REBUDGET = True          # A: trade-off tank/carry/fighter
ENABLE_SCHOOL_MOD = False       # B: dipakai hanya kalau paritas dimatikan
ENABLE_STARTER_CATCHUP = True   # C: starter tidak tenggelam
SCHOOL_PARITY = True            # paritas sekolah vs boss (per kelas boss)
CELL_PARITY = True              # paritas sel arketipe (sekolah x gaya main)
POOL_MEAN_ANCHOR = True         # kunci rata-rata DPS/EHP pool = angka lama
FINAL_FIXPOINT = True           # koreksi akhir dengan rumus audit

# ─── A. RE-BUDGET: pindahkan daya, jangan tambah daya ────────────────────
# Skor power hero = W_DPS * DPS + W_EHP * EHP. Target ratio EHP/DPS per
# gaya main membuat tiap arketipe BAYAR di sumbu yang berbeda.
W_DPS, W_EHP, EHP_PER_HP = 0.72, 0.28, 1.0 / 6.0
TARGET_RATIO = {"TANK": (9.5, 13.0), "FIGHTER": (6.0, 7.5),
                "CARRY": (3.4, 4.6)}
# hero fisik butuh armor boss untuk "dibayar", jadi rasio targetnya digeser
SCHOOL_RATIO_BONUS = {"PHYSICAL": -0.04, "MAGIC": 0.04}
RATIO_BLEND = 0.55     # 0 = biarkan data lama, 1 = paksa target arketipe
BUDGET_COMPRESS = 0.45  # 1 = semua hero dipaksa ke budget median pool
STYLE_POWER = {"TANK": 0.74, "FIGHTER": 1.06, "CARRY": 1.08}

# Batas multiplier per hero. DULU (0.72,1.35)/(0.75,1.30) - clamp SEBELUM
# jangkar itulah yang merusak paritas: hero yang sudah dijepit tidak bisa
# digeser lagi oleh koreksi berikutnya. Sekarang cukup longgar untuk
# menampung koreksi, tetap jauh dari "hero baru".
HP_MULT_RANGE = (0.66, 1.50)
DMG_MULT_RANGE = (0.68, 1.45)

SCHOOL_PARITY_CAP = 1.45   # per (kelas boss x sekolah)
CELL_PARITY_CAP = 1.30
POOL_MEAN_TOL_MAX = 0.18   # seberapa besar jangkar boleh mengoreksi
FINAL_CORR_CAP = 1.35      # koreksi akhir maksimum per hero (x atau /)

# ─── guard "worth it": hero murah tidak boleh jadi optimal ──────────────
COST_BUCKET = 1000
COST_EFF_BAND = (0.78, 1.28)
COST_EFF_DAMP = 0.60
COST_EFF_MIN_GROUP = 8
META_EFF_BAND = (0.80, 1.25)
META_EFF_DAMP = 0.75

# ─── B. MODIFIER SEKOLAH KE MENARA (hanya aktif kalau paritas DIMATIKAN) ──
# Sengaja dibiarkan TIDAK seimbang saat paritas aktif: armor menara adalah
# trade-off nyata (hero fisik mendorong menara lebih cepat).
TOWER_ARMOR_AT_L3 = 5.0
ARMOR_FACTOR = hero_archetypes.ARMOR_FACTOR
TOWER_PHYS_FACTOR = (1.0 / (1.0 + TOWER_ARMOR_AT_L3 * ARMOR_FACTOR))
SCHOOL_MOD_CAP = 1.06

# ─── C. CATCH-UP STARTER ─────────────────────────────────────────────────
STARTER_CATCHUP_MAX = 1.32
STARTER_CATCHUP_REF = 12
STARTER_CATCHUP_LV0 = 1
STARTER_CATCHUP_LV1 = 8
STARTER_CATCHUP_DECAY = 0.20
STARTER_HEROES = ("kaizen", "grimjaw", "sylara", "thorne", "vex", "zephyr")


# ─── METRIK (harus sama dengan yang dibaca audit) ────────────────────────
def metrics(stats):
    """DPS/HP/EHP/budget dari stats hero MENTAH (sebelum buff melee)."""
    hp = float(stats.get("hp", 0) or 0)
    dmg = float(stats.get("damage", 0) or 0)
    cd = max(1.0, float(stats.get("attack_cooldown", 30) or 30))
    sk = float(stats.get("skill_damage", 0) or 0)
    skcd = max(1.0, float(stats.get("skill_cooldown", 240) or 240))
    basic_dps = dmg * 60.0 / cd
    skill_dps = sk * 60.0 / skcd
    dps = basic_dps + skill_dps
    armor = float(stats.get("armor", 0) or 0)
    mr = min(0.75, max(0.0, float(stats.get("magic_resist", 0) or 0)))
    ehp = hp * (1.0 + armor * 0.06) / max(0.25, 1.0 - mr)
    return {
        "hp": hp, "dmg": dmg, "skill": sk, "cd": cd, "skcd": skcd,
        "basic_dps": basic_dps, "skill_dps": skill_dps, "dps": dps,
        "ehp": ehp, "cost": float(stats.get("cost", 0) or 0),
        "burst": (skill_dps / dps) if dps > 0 else 0.0,
        "budget": W_DPS * dps + W_EHP * ehp * EHP_PER_HP,
    }


def _clamp(v, lo_hi):
    lo, hi = lo_hi
    return max(lo, min(hi, v))


def _median(vals):
    return st.median(vals) if vals else 0.0


def _mean(vals):
    return st.fmean(vals) if vals else 0.0


def hero_target(stats, pool):
    """(rasio_target, budget_target) untuk satu hero, memakai statistik pool.

    pool: dict dengan kunci 'med_ratio', 'med_budget', 'eff_by_bucket'.
    """
    m = metrics(stats)
    arch = hero_archetypes.get_archetype(
        stats.get("__hero_type__", ""), stats)
    if m["dps"] <= 0 or m["ehp"] <= 0:
        return None
    style = arch.get("playstyle") or "FIGHTER"
    school = arch.get("dmg_type") or "PHYSICAL"
    lo_r, hi_r = TARGET_RATIO.get(style, TARGET_RATIO["FIGHTER"])
    tgt_ratio = 0.5 * (lo_r + hi_r) \
        * (1.0 + SCHOOL_RATIO_BONUS.get(school, 0.0))
    cur_ratio = m["ehp"] / m["dps"]
    ratio = cur_ratio * (1.0 - RATIO_BLEND) + tgt_ratio * RATIO_BLEND
    b = m["budget"] * STYLE_POWER.get(style, 1.0)
    if BUDGET_COMPRESS > 0 and pool.get("p50_budget", 0) > 0:
        b = b * (pool["p50_budget"] / max(b, 1e-9)) ** BUDGET_COMPRESS
    price_corr = 1.0
    meta_med = pool.get("meta_med")
    if meta_med and meta_med > 0:
        import statistics as _st
        rel = m["budget"] / meta_med
        lo, hi = META_EFF_BAND
        if rel > hi:
            b *= (hi / rel) ** META_EFF_DAMP
        elif rel < lo:
            b *= (lo / rel) ** META_EFF_DAMP
    eff_by_bucket = pool.get("eff_by_bucket") or {}
    bucket = int(round(m["cost"] / COST_BUCKET)) * COST_BUCKET
    med_eff = eff_by_bucket.get(bucket)
    if med_eff and m["cost"] > 0:
        rel = (m["budget"] / m["cost"]) / med_eff
        lo, hi = COST_EFF_BAND
        if rel > hi:
            price_corr = (hi / rel) ** COST_EFF_DAMP
        elif rel < lo:
            price_corr = (lo / rel) ** COST_EFF_DAMP
        b *= price_corr
    return (m, ratio, b, price_corr, school, style)


def stat_multipliers(stats, pool):
    """(mult_hp, mult_damage, mult_skill) untuk satu hero."""
    t = hero_target(stats, pool)
    if t is None:
        return (1.0, 1.0, 1.0, t)
    # urutan tuple hero_target: (m, ratio, budget, price_corr, school, style)
    m, ratio, b = t[0], t[1], t[2]
    # bagi budget target ke dua sumbu MENURUT RASIO TARGET, bukan menurut
    # rasio lama - di situlah tank "dipaksa" membeli dayanya dengan HP.
    share = 1.0 / (1.0 + (W_EHP * EHP_PER_HP * ratio) / W_DPS)
    new_dps = b * share / W_DPS
    new_ehp = b * (1.0 - share) / (W_EHP * EHP_PER_HP)
    x = new_dps / m["dps"] if m["dps"] > 0 else 1.0
    y = new_ehp / m["ehp"] if m["ehp"] > 0 else 1.0
    # hero burst-heavy: sebagian damage-nya ada di skill, jangan dipotong
    # dua kali (basis + skill) - pindahkan bobot ke yang lebih dominan
    x_dmg = 1.0 + (x - 1.0) * (1.0 - m["burst"] * 1.15)
    x_sk = 1.0 + (x - 1.0) * (m["burst"] * 1.15)
    return (_clamp(y, HP_MULT_RANGE), _clamp(x_dmg, DMG_MULT_RANGE),
            _clamp(x_sk, DMG_MULT_RANGE), t)


def school_mod(school):
    """Faktor koreksi damage fisik (menara tidak punya magic resist)."""
    if not ENABLE_SCHOOL_MOD or school != "physical":
        return 1.0
    return min(SCHOOL_MOD_CAP, 1.0 / TOWER_PHYS_FACTOR)


# ─── C. CATCH-UP STARTER ─────────────────────────────────────────────────
def starter_level_factor(level):
    """Sisa catch-up menurut level (1.0 di lv<=STARTER_CATCHUP_LV0, lalu
    meluruh sampai STARTER_CATCHUP_DECAY di lv>=STARTER_CATCHUP_LV1)."""
    import math
    lv = max(1, int(level or 1))
    t = (lv - STARTER_CATCHUP_LV0) / float(max(
        1, STARTER_CATCHUP_LV1 - STARTER_CATCHUP_LV0))
    t = min(1.0, max(0.0, t))
    return 1.0 - (1.0 - STARTER_CATCHUP_DECAY) * t


def starter_catchup(hero_type, boss_unlocks, level=1):
    """Multiplier (hp, dmg) hero starter.

    Berbanding TERBALIK dengan koleksi hero unlock pemain: starter itu
    alat bantu pemain baru, bukan pesaing hero 4500-gem bagi pemain yang
    roster-nya sudah penuh. Bonus dipecah ~60% HP / 40% damage supaya
    starter (basis kecil) tidak berubah jadi burst.
    """
    if not ENABLE_STARTER_CATCHUP or hero_type not in STARTER_HEROES:
        # (saklar mati = angka murni data mentah)
        return (1.0, 1.0)
    # 0 hero unlock -> bonus PENUH; roster penuh (>= REF) -> tidak ada
    # bonus sama sekali. (Pernah terbalik: t dihitung "maju" lalu dipakai
    # apa adanya, sehingga pemain baru - yang justru butuh - dapat 1.0x.)
    t = min(1.0, max(0.0, float(boss_unlocks or 0)
                     / float(STARTER_CATCHUP_REF)))
    k = 1.0 + (STARTER_CATCHUP_MAX - 1.0) * (1.0 - t) \
        * starter_level_factor(level)
    if k <= 1.001:
        return (1.0, 1.0)
    return (1.0 + (k - 1.0) * 1.25, 1.0 + (k - 1.0) * 0.85)


def starter_catchup_stats(hero_type, stats, boss_unlocks, level=1):
    """(hp, damage) starter SESUDAH catch-up - inilah yang dibaca Hero."""
    y, x = starter_catchup(hero_type, boss_unlocks, level)
    return (max(1, int(round(float(stats.get("hp", 1) or 1) * y))),
            max(1, int(round(float(stats.get("damage", 1) or 1) * x))))


def boss_unlocks_for_purchases(purchased):
    """Jumlah hero unlock (bukan starter) yang sudah dibeli."""
    if not purchased:
        return 0
    return max(0, len([h for h in purchased if h not in STARTER_HEROES]))


# ─── B. KOREKSI SEKOLAH: paritas, bukan buff ─────────────────────────────
def _eff_dps(ha, res, ht, s, m, dps):
    """DPS yang benar-benar masuk ke boss lawan hero ini."""
    arch = ha.get_archetype(ht, s)
    r = res.get(s.get("unlock_require_boss") or ht)
    if r is None:
        r = ha._resist_from_profile("balanced", s.get("boss_class", "mini"))
        armor, mr = r
    else:
        armor, mr = r["armor"], r["magic_resist"]
    if arch["dmg_type"] == "PHYSICAL":
        mult = ha.physical_mitigation(armor)
    else:
        mult = 1.0 - mr
    return dps * mult


def _final_power(m, y, x_dmg, x_sk, med_dps, med_ehp):
    """Skor power hero SETELAH multiplier.

    Rumusnya 0.8 * DPS + 0.2 * EHP relatif median pool - SAMA PERSIS
    dengan yang dipakai tools/balance_audit.py. Kalau balance mengejar
    metrik lain dari yang diukur audit, "lolos test" tidak berarti apa-apa.
    """
    dps = (m["dmg"] * x_dmg) * 60.0 / m["cd"] \
        + (m["skill"] * x_sk) * 60.0 / m["skcd"]
    ehp = m["ehp"] * y
    return 0.8 * dps / med_dps + 0.2 * ehp / med_ehp


def cell_parity_factors(boss, met, raw, med_dps, med_ehp, iters=18):
    """Multiplier DAMAGE per sel (sekolah x gaya main); rata-rata power tiap
    sel disamakan ke median pool, TOTAL power pool ditahan.

    Kenapa per SEL dan bukan per sekolah: kalau hanya sekolah yang
    disamakan, sel yang kebetulan berisi banyak carry (PHYSICAL|CARRY dulu
    1.59x DPS) ikut terkerek dan jadi yang terkuat - persis penyakit yang
    mau dihapus. Kenapa "power" dan bukan "DPS efektif": hero juga punya
    EHP; meratakan DPS saja membuat satu sel menang di dua sumbu lagi.

    Damage dinilai dengan armor/MR boss asli (hero_archetypes
    .BOSS_RESISTANCES), jadi yang diratakan adalah damage yang benar-benar
    masuk ke lawan. Penyelesaiannya IPF/raking dua arah + pengapungan
    per-sel CELL_PARITY_CAP supaya tidak ada sel yang "dibuat" kuat.
    """
    ha = hero_archetypes
    res = ha.BOSS_RESISTANCES
    cell = {}
    base = {}
    valid = []
    for ht, s in boss.items():
        m = met[ht]
        if m["dps"] <= 0:
            continue
        arch = ha.get_archetype(ht, s)
        c = (arch["dmg_type"], arch.get("playstyle") or "FIGHTER")
        cell[ht] = c
        base[ht] = raw[ht][:3]
        valid.append(ht)
    if not valid:
        return {}, None
    target = st.fmean([_final_power(met[ht], base[ht][0], base[ht][1],
                                    base[ht][2], med_dps, med_ehp)
                       for ht in valid])
    f = {c: 1.0 for c in set(cell.values())}
    by_cell = {}
    for ht in valid:
        by_cell.setdefault(cell[ht], []).append(ht)

    def power_of(ht):
        y, x_dmg, x_sk = base[ht]
        g = f[cell[ht]]
        return _final_power(met[ht], y, x_dmg * g, x_sk * g,
                            med_dps, med_ehp)

    for _ in range(iters):
        for c, hts in by_cell.items():
            cur = st.fmean([power_of(h) for h in hts])
            if cur > 0:
                f[c] = f[c] * (target / cur)
                f[c] = _clamp(f[c], (1.0 / CELL_PARITY_CAP, CELL_PARITY_CAP))
        mean_all = st.fmean([power_of(h) for h in valid])
        if mean_all > 0:
            g = (target / mean_all) ** 0.9
            for c in f:
                f[c] = _clamp(f[c] * g, (1.0 / CELL_PARITY_CAP,
                                         CELL_PARITY_CAP))
    report = {"pool_target": round(target, 3),
              "cells": {"%s|%s" % k: round(v, 4) for k, v in f.items()}}
    return f, report


def pristine_boss_stats():
    """Stat hero unlock SEBELUM balance, dibaca ulang dari sumbernya.

    apply_to_catalog() MENULIS in-place ke salinan dict katalog, sehingga
    katalog yang lewat ke-2 kali sudah ber-balance. Sumber aslinya
    (bosses.boss_data[*]["hero_unlock"]) tidak pernah disentuh, jadi
    dari sanalah baseline diambil: balance jadi idempoten dan jangkar
    rata-rata pool punya pembanding yang jujur.
    """
    out = {}
    try:
        from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES
    except Exception:
        return out
    for boss_class, table in (("mini", MINI_BOSS_TYPES),
                              ("true", TRUE_BOSS_TYPES)):
        for boss_type, bd in table.items():
            hu = bd.get("hero_unlock")
            if not hu:
                continue
            d = dict(hu)
            d.setdefault("unlock_cost", 4500)
            d["unlock_require_boss"] = boss_type
            d["is_boss_hero"] = True
            d["boss_class"] = boss_class
            out[boss_type] = d
    return out


def resolve_catalog(catalog):
    """Hitung multiplier final SEMUA hero sekaligus.

    Mengembalikan hero_type -> {'hp','dmg','skill','dbg'}. Harus sekaligus
    (bukan per hero) karena tiga hal bersifat pool-relative: median DPS/
    EHP untuk skor power, rata-rata per sel arketipe (paritas), dan median
    grup harga (guard "worth it").
    """
    out = {}
    boss = {}
    for ht, stats in catalog.items():
        if not stats.get("is_boss_hero"):
            continue
        s = dict(stats)
        s["__hero_type__"] = ht
        boss[ht] = s
    if not boss:
        return out

    met = {ht: metrics(s) for ht, s in boss.items()}
    ratios = sorted(m["ehp"] / m["dps"] for m in met.values()
                    if m["dps"] > 0 and m["ehp"] > 0)
    budgets = sorted(m["budget"] for m in met.values())
    buckets = {}
    for ht, m in met.items():
        if m["cost"] <= 0 or m["budget"] <= 0:
            continue
        b = int(round(m["cost"] / COST_BUCKET)) * COST_BUCKET
        buckets.setdefault(b, []).append(m["budget"] / m["cost"])
    eff_by_bucket = {b: _median(v) for b, v in buckets.items()
                     if len(v) >= COST_EFF_MIN_GROUP}
    # toko meta: SEMUA hero unlock harganya sama (4500) - "worth it"
    # diukur terhadap median pool, bukan per band harga in-game.
    meta_costs = {}
    for stats in catalog.values():
        if stats.get("is_boss_hero"):
            meta_costs.setdefault(float(stats.get("unlock_cost", 0) or 0),
                                 []).append(metrics(stats)["budget"])
    meta_med = 0.0
    for c, v in meta_costs.items():
        if c > 0 and len(v) >= 20:
            meta_med = _median(v)
            break
    n_b = len(budgets) or 1
    pool = {"med_ratio": _median(ratios), "med_budget": _median(budgets),
            "p50_budget": budgets[n_b // 2] if budgets else 0.0,
            "eff_by_bucket": eff_by_bucket, "meta_med": meta_med}
    med_dps = _median([m["dps"] for m in met.values()]) or 1.0
    med_ehp = _median([m["ehp"] for m in met.values()]) or 1.0
    pool["med_dps"], pool["med_ehp"] = med_dps, med_ehp

    raw = {ht: stat_multipliers(s, pool) for ht, s in boss.items()}

    # ── paritas SEL arketipe (identitas peran) ──
    if CELL_PARITY:
        fac, rep = cell_parity_factors(boss, met, raw, med_dps, med_ehp)
        LAST["parity"] = rep or {}
        if fac:
            for ht in raw:
                y, x_dmg, x_sk, t = raw[ht]
                g = fac.get((t[4], t[5]), 1.0)
                raw[ht] = (y, x_dmg * g, x_sk * g, t)

    # ── JANGKAR: rata-rata multiplier tiap stat = 1.0 ──
    # Semua koreksi di atas REDISTRIBUSI, bukan buff. Tanpa jangkar ini,
    # "memindahkan power ke carry" diam-diam menaikkan power semua orang.
    fin = {ht: list(v[:3]) for ht, v in raw.items()}
    for i, rng in enumerate((HP_MULT_RANGE, DMG_MULT_RANGE, DMG_MULT_RANGE)):
        avg = _mean([v[i] for v in fin.values()]) or 1.0
        for ht in fin:
            fin[ht][i] = _clamp(fin[ht][i] / avg, rng)

    # ── paritas SEKOLAH pada damage EFEKTIF, PER KELAS BOSS ──
    # URUTAN PENTING: sekolah yang TERAKHIR dan TANPA clamp ganda, karena
    # clamp di langkah sebelumnya membuat magic/fisik tidak bisa dipertukar
    # lagi secara persis; dan paritas sel (identitas) tidak boleh dirusak
    # oleh paritas sekolah. Diukur per kelas boss - hero mini hanya melawan
    # boss mini. ANGKA YANG DIUKUR HARUS TERMASUK multiplier: paritas
    # dihitung di damage FINAL, bukan di data mentah (kesalahan lama:
    # mengukur tanpa x_dmg membuat faktor selalu 1.0 dan bug ini diam).
    if SCHOOL_PARITY:
        ha = hero_archetypes
        res = ha.BOSS_RESISTANCES
        for _pass in range(8):
            eff = {}
            for ht, s in boss.items():
                m = met[ht]
                if m["dps"] <= 0:
                    continue
                x_dmg, x_sk = fin[ht][1], fin[ht][2]
                dps = (m["dmg"] * x_dmg) * 60.0 / m["cd"] \
                    + (m["skill"] * x_sk) * 60.0 / m["skcd"]
                e = _eff_dps(ha, res, ht, s, m, dps)
                if e is None:
                    continue
                eff.setdefault((s.get("boss_class", "mini"),
                                raw[ht][3][4]), []).append(e)
            by_cls = {}
            for (dc, sch), vals in eff.items():
                by_cls.setdefault(dc, []).extend(vals)
            tgt = {dc: st.fmean(v) for dc, v in by_cls.items() if v}
            if not tgt:
                break
            moved = 0.0
            f2 = {}
            for key, vals in eff.items():
                cur = st.fmean(vals)
                t_dc = tgt.get(key[0], 0.0)
                if t_dc <= 0 or cur <= 0:
                    f2[key] = 1.0
                    continue
                f = _clamp(t_dc / cur, (1.0 / SCHOOL_PARITY_CAP,
                                        SCHOOL_PARITY_CAP))
                f2[key] = f
                moved = max(moved, abs(f - 1.0))
            # tahan rata-rata damage pool: faktor dibagi rata-rata tertimbang
            # jumlah hero per kelas, supaya paritas TIDAK jadi buff global
            wavg = {}
            for dc in set(k[0] for k in f2):
                ks = [k for k in f2 if k[0] == dc]
                n = {k: len(eff[k]) for k in ks}
                tot = sum(n.values()) or 1
                wavg[dc] = sum(f2[k] * n[k] for k in ks) / tot
            for ht in fin:
                dc = boss[ht].get("boss_class", "mini")
                g = f2.get((dc, raw[ht][3][4]), 1.0) / wavg.get(dc, 1.0)
                fin[ht][1] *= g
                fin[ht][2] *= g
            LAST["parity"] = dict(LAST.get("parity") or {})
            LAST["parity"]["schools"] = {"%s|%s" % k: round(v, 4)
                                         for k, v in f2.items()}
            if moved < 0.002:
                break

    # RATA-RATA POOL DijAGA di apply_to_catalog (satu-satunya tempat yang
    # memegang angka PRASEBELUM-multiplier dan SESUDAH-multiplier sekaligus)
    # - lihat POOL_MEAN_ANCHOR.

    for ht in fin:
        y2, x2, k2 = fin[ht]
        t = raw[ht][3]
        # school_mod hanya dipakai kalau paritas sel dimatikan (lihat B)
        s_mod = (school_mod(t[4].lower()) if (not SCHOOL_PARITY) else 1.0)
        out[ht] = {
            "hp": round(y2, 4), "dmg": round(x2 * s_mod, 4),
            "skill": round(k2 * s_mod, 4),
            "dbg": {"ratio_from": round(t[0]["ehp"] / t[0]["dps"], 3)
                    if t and t[0]["dps"] > 0 else 0.0,
                    "ratio_to": round(t[1], 3),
                    "price_corr": round(t[3], 4),
                    "playstyle": t[5], "dmg_type": t[4],
                    "boss_class": boss[ht].get("boss_class")},
        }

    # ── starter: catch-up saja (basis statnya kecil, tidak ikut rebudget)
    unlocks, level = 0, 1
    try:
        import __main__
        g = getattr(__main__, "game_instance", None)
        if g is not None:
            unlocks = boss_unlocks_for_purchases(
                getattr(g, "purchased_heroes", None)
                or g.save_data.get("purchased_heroes") or [])
    except Exception:
        unlocks = 0
    for ht, stats in catalog.items():
        if stats.get("is_boss_hero"):
            continue
        y, x = starter_catchup(ht, unlocks, level)
        out[ht] = {
            "hp": round(y, 4), "dmg": round(x, 4), "skill": 1.0,
            "dbg": {"starter_unlocks": unlocks, "playstyle": None,
                    "dmg_type": hero_archetypes.get_archetype(
                        ht, stats)["dmg_type"], "boss_class": None},
        }
    return out


# ─── boss resistances: kalibrasi profil -> paritas, tanpa buff global ────
def calibrate_boss_resistances(rows, target_ratio=None, scale_lo=0.6,
                               scale_hi=1.8, n_step=25):
    """Kalibrasi armor/MR boss -> (tabel BOSS_RESISTANCES, report).

    Aturan keras yang dipatuhi:
      1. modifier profil DINOLKAN rata-ratanya per kelas boss, lalu
         rata-rata armor & MR hasil akhir DIKUNCI persis di baseline
         kelasnya (mini 12/0.10, true 18/0.20). Kalibrasi tidak pernah
         berubah jadi buff/nerf global.
      2. yang dicari hanya DUA SKALA (>0) untuk memperlebar/menyempitkan
         selisih antar profil: armor kuat = anti-fisik, MR tinggi =
         anti-magic. Yang bergeser adalah SIAPA ditahan siapa, bukan
         berapa banyak.
      3. DPS hero yang dipakai sebagai bahan kalibrasi adalah DPS
         SESUDAH re-budget (lihat resolve_catalog) supaya paritas yang
         dijanjikan adalah paritas di game, bukan di data mentah.
         Tools memanggil ini dua kali: pra (data mentah) lalu pasca
         (live) - selisih keduanya dilaporkan.

    Target: rata-rata (magic DPS efektif) / (fisik DPS efektif) vs boss
    kelas itu == TARGET_RATIO. Per-boss tetap jauh berbeda dan arahnya
    berlawanan antar kelas (boss mini bertema baja = wilayah hero magic,
    boss true bertema sihir = wilayah hero fisik).
    """
    ha = hero_archetypes
    base = ha.BOSS_RESIST_BASE
    raw_mods = ha.BOSS_RESIST_PROFILE_MODS
    target = target_ratio or ha.BOSS_RESIST_TARGET_RATIO

    by_class = {}
    for r in rows:
        by_class.setdefault(r["boss_class"], []).append(r)

    def zero_mean(dc, rs):
        n = len(rs) or 1

        def g(key):
            return sum(ha.BOSS_RESIST_PROFILE_MODS.get(
                r.get("profile", "balanced"), (0.0, 0.0))[key] for r in rs) / n
        return {p: (v[0] - g(0), v[1] - g(1))
                for p, v in raw_mods.items()}

    def stats_for(dc, mods, sa, sm):
        p_sum = m_sum = 0.0
        p_n = m_n = 0
        a_sum = mr_sum = 0.0
        for r in by_class.get(dc, []):
            armor, mr = ha._resist_from_profile(
                r.get("profile", "balanced"), dc, base, mods,
                armor_scale=sa, mr_scale=sm)
            a_sum += armor
            mr_sum += mr
            dps = float(r.get("dps", 0.0) or 0.0)
            if r.get("dmg_type") == "PHYSICAL":
                p_sum += dps * ha.physical_mitigation(armor)
                p_n += 1
            else:
                m_sum += dps * (1.0 - mr)
                m_n += 1
        n = len(by_class.get(dc, [])) or 1
        ratio = (m_sum / max(m_n, 1)) / max(p_sum / max(p_n, 1), 1e-9) \
            if p_n and m_n else 1.0
        return ratio, a_sum / n, mr_sum / n

    def solve(dc, mods, lock):
        b_a, b_mr = base[dc]
        grid = [(1.0 + (scale_hi - 1.0) * i / max(n_step - 1, 1),
                 1.0 + (scale_hi - 1.0) * j / max(n_step - 1, 1))
                for i in range(n_step) for j in range(n_step)]
        best = (9e9, 1.0, 1.0)
        for sa, sm in grid:
            ratio, av_a, av_mr = stats_for(dc, mods, sa, sm)
            pen = 0.0
            if lock:
                pen += max(0.0, abs(av_a - b_a) - 0.6) * 0.5
                pen += max(0.0, abs(av_mr - b_mr) - 0.006) * 120.0
            score = abs(ratio - target) + pen
            if score < best[0]:
                best = (score, sa, sm)
        _, sa, sm = best
        return sa, sm, stats_for(dc, mods, sa, sm)

    mods_by_class = {}
    report = {}
    scales = {}
    for dc in list(by_class):
        mods = zero_mean(dc, by_class.get(dc, []))
        sa, sm, (ratio, av_a, av_mr) = solve(dc, mods, True)
        for _ in range(6):
            da = {p: (v[0] - (av_a - base[dc][0]), v[1])
                   for p, v in mods.items()}
            db = {p: (v[0], v[1] - (av_mr - base[dc][1]))
                  for p, v in da.items()}
            r2, a2, m2 = stats_for(dc, db, sa, sm)
            if abs(r2 - target) <= abs(ratio - target) + 0.02:
                mods, ratio, av_a, av_mr = db, r2, a2, m2
                break
            r3, a3, m3 = stats_for(dc, da, sa, sm)
            if abs(a3 - base[dc][0]) < abs(av_a - base[dc][0]):
                mods, ratio, av_a, av_mr = da, r3, a3, m3
        mods_by_class[dc] = mods
        scales[dc] = {"armor": sa, "mr": sm}
        report[dc] = {"magic_over_phys": round(ratio, 3),
                      "avg_armor": round(av_a, 1),
                      "avg_mr": round(av_mr, 4),
                      "scale": {"armor": sa, "mr": sm},
                      "mods": mods}
    report["_scales"] = {dc: {"armor_scale": sc["armor"], "mr_scale": sc["mr"]}
                         for dc, sc in scales.items()}
    report["_mods_mini"] = report.get("mini", {}).get("mods", {})

    res = {}
    for r in rows:
        dc = r["boss_class"]
        sc = scales.get(dc, {"armor": 1.0, "mr": 1.0})
        armor, mr = ha._resist_from_profile(
            r.get("profile", "balanced"), dc, base, mods_by_class.get(dc),
            armor_scale=sc["armor"], mr_scale=sc["mr"])
        res[r["boss_type"]] = {"armor": int(round(armor)),
                               "magic_resist": round(float(mr), 3),
                               "profile": r.get("profile", "balanced"),
                               "boss_class": dc}
    return res, report


import os as _os
import sys as _sys

_DBG = bool(_os.environ.get("MYSTIC_DEBUG_BALANCE"))

# audit & tools membaca hasil antara dari sini (lihat tools/balance_audit.py)
LAST = {"table": {}, "pool": {}, "parity": {}}


def _pool_mean_rescale(catalog, before, which="dps", tol=0.005):
    """Kalikan stat boss dengan faktor SERAGAM supaya rata-rata pool (DPS
    atau EHP) kembali ke angka SEBELUM balance. Return faktornya (1.0 =
    sudah pas). Seragam = tidak mengubah paritas apa pun, hanya geser
    level; koreksi dibatasi POOL_MEAN_TOL_MAX supaya balance tidak pernah
    diam-diam jadi buff/nerf global.
    """
    import statistics as _st
    if not before:
        return 1.0
    ids = [k for k in before
           if k in catalog and catalog[k].get("is_boss_hero")]
    if not ids:
        return 1.0
    key = "dps" if which == "dps" else "ehp"
    cur = _st.fmean([metrics(catalog[k])[key] for k in ids]) or 1.0
    want = _st.fmean([before[k][key] for k in ids])
    if want <= 0 or cur <= 0:
        return 1.0
    g = _clamp(want / cur, (1.0 - POOL_MEAN_TOL_MAX, 1.0 + POOL_MEAN_TOL_MAX))
    if abs(g - 1.0) < tol:
        return 1.0
    for k in ids:
        v = catalog[k]
        if which == "dps":
            for kk in ("damage", "skill_damage", "skill_q_damage",
                       "skill_w_damage", "skill_e_damage", "skill_r_damage"):
                if v.get(kk):
                    v[kk] = max(0, int(round(v[kk] * g)))
        else:
            v["hp"] = max(1, int(round(float(v.get("hp", 1) or 1) * g)))
        b = v.get("__bal")
        if b:
            bk = "dmg" if which == "dps" else "hp"
            b[bk] = round(b[bk] * g, 4)
            if which == "dps":
                b["skill"] = round(b["skill"] * g, 4)
    return g


def _final_fixpoint(catalog, school_target=1.0, cell_band=None,
                    passes=40, damp=0.85, tol=0.002):
    """Koreksi kecil LANGSUNG pada stat final, diukur dengan rumus yang
    sama persis dengan tools/balance_audit.py.

    Kenapa perlu: paritas sel/sekolah di resolve_catalog bekerja pada
    MULTIPLIER, sementara clamp di jangkar lewat dari situ - hasilnya audit
    tetap melihat fisik lebih kuat. Di sini tidak ada lagi perantara:
    damage hero dikalikan faktor (dibatasi FINAL_CORR_CAP) sampai
    (a) DPS efektif fisik == sihir per kelas boss dan (b) power tiap sel
    arketipe == rata-rata pool. Kedua syarat diputar bersama supaya tidak
    saling menjatuhkan (diputar terpisah, salah satunya selalu menang).
    """
    import statistics as _st
    ha = hero_archetypes
    ids = [ht for ht, v in catalog.items()
           if v.get("is_boss_hero") and metrics(v)["dps"] > 0]
    if len(ids) < 20:
        return {"skipped": "hero terlalu sedikit"}
    fac = {ht: 1.0 for ht in ids}
    info = {}
    for _p in range(passes):
        f_sch, f_cell = {}, {}
        # (a) paritas sekolah: DPS TERMITIGASI per (kelas boss, sekolah)
        eff = {}
        for ht in ids:
            v = catalog[ht]
            m = metrics(v)
            armor, mr = ha.get_boss_resistances(
                v.get("unlock_require_boss") or ht,
                v.get("boss_class", "mini"))
            school = ha.get_archetype(ht, v)["dmg_type"]
            mit = (ha.physical_mitigation(armor)
                   if school == "PHYSICAL" else 1.0 - mr)
            eff.setdefault((v.get("boss_class", "mini"), school), []).append(
                m["dps"] * fac[ht] * mit)
        by_cls = {}
        for (dc, sc), vals in eff.items():
            by_cls.setdefault(dc, []).extend(vals)
        for (dc, sc), vals in eff.items():
            cur = _st.fmean(vals)
            tgt = _st.fmean(by_cls[dc]) * school_target if by_cls.get(dc) \
                else cur
            if cur > 0 and tgt > 0:
                f_sch[(dc, sc)] = (tgt / cur) ** damp
        # (b) power per sel arketipe -> rata-rata pool. PENTING: audit
        # membadingkan rata-rata sel dengan MEDIAN pool tapi MEDIAN-nya
        # dihitung dari pool yang sama; memakai rata-rata di kedua sisi
        # membuat kedua metrik tidak pernah bertemu (distribusinya miring).
        med_d = _st.mean([metrics(catalog[h])["dps"] for h in ids]) or 1.0
        med_e = _st.mean([metrics(catalog[h])["ehp"] for h in ids]) or 1.0
        cell = {}
        for ht in ids:
            a = ha.get_archetype(ht, catalog[ht])
            m = metrics(catalog[ht])
            pw = (0.8 * m["dps"] * fac[ht] / med_d
                  + 0.2 * m["ehp"] / med_e)
            cell.setdefault((a["dmg_type"], a.get("playstyle")), []).append(
                (ht, pw))
        allpw = [pw for v in cell.values() for _, pw in v]
        tgt_cell = _st.fmean(allpw) if allpw else 1.0
        if cell_band is not None:
            for c, v in cell.items():
                cur = _st.fmean([p for _, p in v])
                if cur > 0:
                    g = (tgt_cell / cur) ** damp
                    f_cell[c] = _clamp(g, cell_band)
        moved = 0.0
        for ht in ids:
            v = catalog[ht]
            a = ha.get_archetype(ht, v)
            g = f_sch.get((v.get("boss_class", "mini"), a["dmg_type"]), 1.0)
            g *= f_cell.get((a["dmg_type"], a.get("playstyle")), 1.0)
            g = _clamp(g, (1.0 / FINAL_CORR_CAP, FINAL_CORR_CAP))
            fac[ht] = _clamp(fac[ht] * g, (1.0 / FINAL_CORR_CAP,
                                           FINAL_CORR_CAP))
            moved = max(moved, abs(g - 1.0))
        info["passes_run"] = _p + 1
        info["last_move"] = round(moved, 4)
        if moved < tol:
            break
    # tulis faktor ke stat
    for ht in ids:
        g = fac[ht]
        if abs(g - 1.0) < 1e-4:
            continue
        v = catalog[ht]
        for key in ("damage", "skill_damage", "skill_q_damage",
                    "skill_w_damage", "skill_e_damage", "skill_r_damage"):
            if v.get(key):
                v[key] = max(0, int(round(v[key] * g)))
        b = v.get("__bal")
        if b:
            b["dmg"] = round(b["dmg"] * g, 4)
            b["skill"] = round(b["skill"] * g, 4)
            b["dbg"]["fix"] = round(g, 4)
        fac[ht] = g
    info["factor_min"] = round(min(fac.values()), 4)
    info["factor_max"] = round(max(fac.values()), 4)
    info["n"] = len(ids)
    return info


def apply_to_catalog(catalog):
    """Terapkan hasil resolve_catalog() ke dict katalog (in-place).

    Dipanggil dari _core.get_all_hero_types() sehingga toko, preview skill,
    Hero, dan AI membaca ANGKA YANG SAMA. Idempoten terhadap pemanggilan
    berulang karena stat selalu dibaca ulang dari sumber mentahnya
    (pristine_boss_stats) - bukan dari katalog yang mungkin sudah ditulis.
    """
    # PENTING: `catalog` adalah dict MILI PEMANGGIL (_core) dan fungsi ini
    # harus menulis IN-PLACE ke sana - jangan pernah replace bind-nya
    # (pernah dilakukan -> hanya starter yang tertulis, balance hilang).
    pristine = pristine_boss_stats()
    src = dict(catalog)
    for _k, _v in pristine.items():
        if _k in src:
            src[_k] = _v
    if _DBG:
        print("[hero_balance] apply_to_catalog n=%d pristine=%d"
              % (len(catalog), len(pristine)), file=_sys.stderr)
    try:
        table = resolve_catalog(src)
        if _DBG:
            print("[hero_balance] resolve ok, hero=%d parity=%s" % (
                len(table), LAST.get("parity")), file=_sys.stderr)
    except Exception:
        if _DBG:
            import traceback
            traceback.print_exc()
        return catalog
    before = {}
    if POOL_MEAN_ANCHOR:
        for k, v in (pristine or {}).items():
            mm = metrics(v)
            if mm["dps"] > 0:
                before[k] = mm
    # simpan angka MURNI di dbg.raw supaya audit bisa membandingkan
    # "sebelum vs sesudah" dengan rumus yang PERSIS SAMA (bukan lewat
    # tools/analyze_hero_archetypes.py yang memakai metrik lain).
    for ht, v in pristine.items():
        if ht in table and table[ht] is not None:
            table[ht]["dbg"]["raw"] = {"hp": v.get("hp"),
                                       "damage": v.get("damage"),
                                       "skill_damage": v.get("skill_damage"),
                                       "attack_cooldown":
                                           v.get("attack_cooldown"),
                                       "skill_cooldown":
                                           v.get("skill_cooldown")}
    LAST["table"] = table
    for ht, mult in table.items():
        if not mult:
            continue
        stats = catalog.get(ht)
        if stats is None:
            continue
        if not stats.get("is_boss_hero"):
            # Starter SENGAJA tidak ditulis ke katalog. Catch-up mereka
            # bergantung state pemain (jumlah hero unlock + level), jadi
            # satu-satunya penulis adalah _entity.Hero (saat unit dibuat);
            # kalau katalog yang menulis, bonusnya dihitung DUA KALI.
            # Toko/preview memang memperlihatkan angka dasar - itu benar,
            # karena bonus itu tidak ada untuk pemain yang rostersnya penuh.
            continue
        if stats is None:
            continue
        raw = src.get(ht, stats)
        stats["__bal"] = mult
        stats["hp"] = max(1, int(round(raw.get("hp", 1) * mult["hp"])))
        stats["damage"] = max(1, int(round(
            raw.get("damage", 1) * mult["dmg"])))
        stats["skill_damage"] = max(0, int(round(
            raw.get("skill_damage", 0) * mult["skill"])))
        for key in ("skill_q_damage", "skill_w_damage", "skill_e_damage",
                    "skill_r_damage"):
            if raw.get(key):
                stats[key] = max(0, int(round(raw[key] * mult["skill"])))

    # ── jangkar rata-rata pool: balance = REDISTRIBUSI, bukan buff ──
    # Dijalankan SEBELUM fixpoint supaya paritas sekolah tidak dirusak oleh
    # rescale seragam sesudahnya (pernah begitu -> ratio 1.26 & spread
    # harga 2.99x).
    LAST["pool_anchor"] = {}
    if POOL_MEAN_ANCHOR and before:
        LAST["pool_means"] = {
            "dps": round(st.fmean([m["dps"] for m in before.values()]), 1),
            "ehp": round(st.fmean([m["ehp"] for m in before.values()]), 1),
            "n": len(before)}
        LAST["pool_anchor"]["dps"] = _pool_mean_rescale(catalog, before, "dps")
        LAST["pool_anchor"]["ehp"] = _pool_mean_rescale(catalog, before, "ehp")
        LAST["pool_anchor"] = {k: v for k, v in LAST["pool_anchor"].items()
                               if v and abs(v - 1.0) >= 0.005}

    # ── koreksi akhir: paritas sekolah + sel, diukur dengan rumus audit ──
    if FINAL_FIXPOINT:
        LAST["fix"] = _final_fixpoint(catalog)

    return catalog
