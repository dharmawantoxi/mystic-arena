#!/usr/bin/env python3
"""Parity FASE 32 (B): pipeline data `bosses/boss_data.py` ↔ `godot/scripts/core/BossData.gd`.

`boss_data.py` bukan tabel statis: begitu diimpor, LIMA fungsi berjalan
berurutan dan menimpa tabelnya sendiri in-place —

  1. `_apply_boss_rebalancing()`      boost piecewise HP/damage/ability/skill
  2. `_smooth_boss_progression()`     kurva monoton per slot wave mini
                                     (10-12 / 13-21 / 22+) + per level true
  3. `_apply_boss_curve_overrides()`  tiga kurva eksplisit true boss
  4. `_normalize_hero_unlock_stats()` least-squares trend per kelas + clamp
                                     outlier + running-max toleransi 15%
  5. `_normalize_hero_unlock_range()` melee -> 70, ranged -> clamp 120..220

Input mentahnya tidak pernah terlihat setelah import. `tools/convert_to_godot.py`
mengekstrak literal tabel lewat AST (SEBELUM mutasi) ke
`godot/data/boss_pristine.json`, dan `BossData.gd` menghitung ulang kelima
langkah itu di Godot — jalur pemulihan `BossDB` bila `bosses.json` hilang.

Tes ini tiga lapis:
  1. MODEL pipeline (kembaran BossData.gd, ditulis dari sumber yang sama)
     dijalankan atas pristine + jadwal levels.json, lalu dibandingkan dengan
     nilai AKHIR modul boss_data ASLI untuk seluruh 216 boss (7 field angka +
     7 field hero_unlock).
  2. Invariant pipeline diukur dari hasil nyata: rebalance benar-benar
     menaikkan angka, smoothing monoton per slot, kurva override menang atas
     smoothing, clamp hero_unlock berada dalam pita [0.70..1.30]×prediksi atau
     digantikan batasnya, dan aturan range (melee 70 / ranged 120..220 /
     skill_range >= range) berlaku untuk semua hero unlock.
  3. Cek struktural `BossData.gd`: gotcha GDScript yang diketahui (pembagian
     int, `pow(d, 2)` vs `d*d`, `round()` banker's, sort stabil, truthiness
     dict kosong) harus tetap terpasang, dan `BossDB.gd` benar-benar memanggil
     `BossData.build` sebagai fallback.

Fixture `godot/tests/fixtures/boss_data.json` (hasil pipeline + jadwal) dipakai
`godot/tests/BossDataParityTest.gd` untuk memutar ulang `BossData.gd` di engine
betulan. Wajib segar: kalau `boss_data.py`, `levels.json`, atau
`boss_pristine.json` berubah, jalankan

    python3 tools/test_boss_data_parity.py --write-fixture
"""

import argparse
import ast
import json
import os
import re
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PRISTINE = os.path.join(ROOT, "godot", "data", "boss_pristine.json")
LEVELS = os.path.join(ROOT, "godot", "data", "levels.json")
BOSSES_JSON = os.path.join(ROOT, "godot", "data", "bosses.json")
BOSS_DATA_GD = os.path.join(ROOT, "godot", "scripts", "core", "BossData.gd")
BOSS_DB_GD = os.path.join(ROOT, "godot", "scripts", "core", "BossDB.gd")
FIXTURE = os.path.join(ROOT, "godot", "tests", "fixtures", "boss_data.json")

BOSS_FIELDS = ["hp", "damage", "ability_damage", "skill_q_damage",
               "skill_w_damage", "skill_e_damage", "skill_r_damage"]
HU_FIELDS = ["cost", "hp", "damage", "attack_cooldown", "skill_damage",
             "range", "skill_range"]

_checks = 0
_failures = []


def expect(cond, label):
    global _checks
    _checks += 1
    if not cond:
        _failures.append(label)
        print("FAIL:", label)


# ─────────────────────────────────────────────────────────────────────
# Model pipeline (kembaran BossData.gd; sumber: boss_data.py:11452-11841)
# ─────────────────────────────────────────────────────────────────────


def load_model_tables():
    p = json.load(open(PRISTINE, encoding="utf-8"))
    mini = {k: dict(v) for k, v in p["mini"].items()}
    true = {k: dict(v) for k, v in p["true"].items()}
    for table in (mini, true):
        for row in table.values():
            if row.get("hero_unlock"):
                row["hero_unlock"] = dict(row["hero_unlock"])
    return p, mini, true


def rebalance(mini, true):
    """_apply_boss_rebalancing (boss_data.py:11452-11528)."""
    for bdata in mini.values():
        hu = bdata.get("hero_unlock")
        hp = bdata.get("hp", 3000)
        dmg = bdata.get("damage", 50)
        ab = bdata.get("ability_damage", 100)
        if hp < 10000:
            nhp = max(7500, int(hp * 2.2))
        elif hp < 20000:
            nhp = int(hp * 1.6)
        elif hp < 40000:
            nhp = int(hp * 1.4)
        else:
            nhp = int(hp * 1.3)
        if dmg < 100:
            ndmg = max(85, int(dmg * 1.4))
        elif dmg < 200:
            ndmg = int(dmg * 1.25)
        else:
            ndmg = int(dmg * 1.2)
        bdata["hp"] = nhp
        bdata["damage"] = ndmg
        bdata["ability_damage"] = max(ab, int(ab * 1.25))
        for k in ("skill_q_damage", "skill_w_damage", "skill_e_damage",
                  "skill_r_damage"):
            if k in bdata and bdata[k] > 0:
                bdata[k] = int(bdata[k] * 1.25)
        if hu:
            bdata["hero_unlock"] = hu
    for bdata in true.values():
        hu = bdata.get("hero_unlock")
        hp = bdata.get("hp", 15000)
        dmg = bdata.get("damage", 100)
        ab = bdata.get("ability_damage", 200)
        if hp < 20000:
            nhp = max(36000, int(hp * 2.4))
        elif hp < 40000:
            nhp = int(hp * 2.0)
        elif hp < 70000:
            nhp = int(hp * 1.6)
        else:
            nhp = int(hp * 1.45)
        if dmg < 120:
            ndmg = max(145, int(dmg * 1.5))
        elif dmg < 250:
            ndmg = int(dmg * 1.3)
        else:
            ndmg = int(dmg * 1.25)
        bdata["hp"] = nhp
        bdata["damage"] = ndmg
        bdata["ability_damage"] = max(ab, int(ab * 1.35))
        for k in ("skill_q_damage", "skill_w_damage", "skill_e_damage",
                  "skill_r_damage"):
            if k in bdata and bdata[k] > 0:
                bdata[k] = int(bdata[k] * 1.35)
        if hu:
            bdata["hero_unlock"] = hu


def slot_of(wave):
    """_slot_of_mini_wave: 10-12 awal, 13-21 tengah, 22+ akhir."""
    if wave <= 12:
        return "w10"
    if wave <= 21:
        return "w18"
    return "w25"


def smooth(mini, true, schedule):
    """_smooth_boss_progression (boss_data.py:11552-11607)."""
    prev = {"w10": [0, 0, 0], "w18": [0, 0, 0], "w25": [0, 0, 0]}
    for cfg in schedule:
        for wave, name in sorted((cfg.get("mini_bosses") or {}).items()):
            s = slot_of(wave)
            b = mini.get(name)
            if not b:
                continue
            b["hp"] = max(int(b.get("hp", 0)), prev[s][0])
            b["damage"] = max(int(b.get("damage", 0)), prev[s][1])
            b["ability_damage"] = max(int(b.get("ability_damage", 0)), prev[s][2])
            prev[s] = [b["hp"], b["damage"], b["ability_damage"]]
    ph = pd = pa = 0
    for cfg in schedule:
        b = true.get(cfg.get("true_boss"))
        if not b:
            continue
        b["hp"] = max(int(b.get("hp", 0)), ph)
        b["damage"] = max(int(b.get("damage", 0)), pd)
        b["ability_damage"] = max(int(b.get("ability_damage", 0)), pa)
        ph, pd, pa = b["hp"], b["damage"], b["ability_damage"]


def curves(true, pristine):
    """_apply_boss_curve_overrides (boss_data.py:11663-11675)."""
    c = pristine["curves"]
    for n, hp in c["hp"].items():
        if n in true:
            true[n]["hp"] = hp
    for n, d in c["damage"].items():
        if n in true:
            true[n]["damage"] = d
    for n, a in c["ability"].items():
        if n in true:
            true[n]["ability_damage"] = a


def trend(values_by_cost):
    """_hero_unlock_trend: least-squares stat ~ cost (tanpa numpy)."""
    n = len(values_by_cost)
    if n == 0:
        return 0.0, 0.0
    costs = [c for c, _ in values_by_cost]
    vals = [v for _, v in values_by_cost]
    mx = sum(costs) / n
    my = sum(vals) / n
    sxx = sum((c - mx) ** 2 for c in costs)
    sxy = sum((c - mx) * (v - my) for c, v in zip(costs, vals))
    if sxx == 0:
        return 0.0, my
    a = sxy / sxx
    return a, my - a * mx


def _clamp(v, pred):
    """clamp() di _normalize_hero_unlock_stats (boss_data.py:11745-11752)."""
    if pred <= 0:
        return v
    if v <= 0 or v < 0.70 * pred:
        return max(v, 0.80 * pred)
    if v > 1.30 * pred:
        return min(v, 1.20 * pred)
    return v


def norm_stats(mini, true):
    """_normalize_hero_unlock_stats (boss_data.py:11703-11802)."""
    for table in (mini, true):
        heroes = [(bt, bd["hero_unlock"]) for bt, bd in table.items()
                  if bd.get("hero_unlock")]
        heroes.sort(key=lambda h: h[1].get("cost", 0))  # sort Python STABIL
        hp_fit = trend([(hu.get("cost", 0), hu.get("hp", 0)) for _, hu in heroes])
        dps_fit = trend([(hu.get("cost", 0),
                          hu.get("damage", 0) / max(1, hu.get("attack_cooldown", 30)) * 60.0)
                         for _, hu in heroes])
        sk_fit = trend([(hu.get("cost", 0), hu.get("skill_damage", 0))
                        for _, hu in heroes])
        for _, hu in heroes:
            cost = hu.get("cost", 0)
            hu["skill_damage"] = int(round(_clamp(hu.get("skill_damage", 0),
                                                  sk_fit[0] * cost + sk_fit[1])))
            hu["hp"] = int(round(_clamp(hu.get("hp", 0),
                                        hp_fit[0] * cost + hp_fit[1])))
            cd = max(1, hu.get("attack_cooldown", 30))
            cur = hu.get("damage", 0) / cd * 60.0
            new = _clamp(cur, dps_fit[0] * cost + dps_fit[1])
            if new != cur:
                hu["damage"] = int(round(new * cd / 60.0))
        m_hp = m_dmg = m_sk = 0
        for _, hu in heroes:
            if hu["hp"] < 0.85 * m_hp:
                hu["hp"] = m_hp
            else:
                m_hp = max(m_hp, hu["hp"])
            if hu["damage"] < 0.85 * m_dmg:
                hu["damage"] = m_dmg
            else:
                m_dmg = max(m_dmg, hu["damage"])
            if hu["skill_damage"] < 0.85 * m_sk:
                hu["skill_damage"] = m_sk
            else:
                m_sk = max(m_sk, hu["skill_damage"])


def norm_range(mini, true, hints):
    """_normalize_hero_unlock_range (boss_data.py:11815-11832)."""
    for table in (mini, true):
        for bd in table.values():
            hu = bd.get("hero_unlock")
            if not hu:
                continue
            role = (hu.get("role") or "").lower()
            orig = int(hu.get("range", 70) or 70)
            is_melee = any(k in role for k in hints)
            if is_melee or orig <= 90:
                hu["range"] = 70
            else:
                hu["range"] = max(120, min(220, orig))
            sr = int(hu.get("skill_range", 0) or 0)
            if sr and sr < hu["range"]:
                hu["skill_range"] = hu["range"]


def schedule_from_levels():
    """Padanan levels.get_level_config(lvl) dari levels.json (urut level)."""
    levels = json.load(open(LEVELS, encoding="utf-8"))
    out = []
    for lv in sorted(levels, key=lambda z: z["level_number"]):
        out.append({
            "mini_bosses": {int(k): v for k, v in (lv.get("mini_bosses") or {}).items()},
            "true_boss": lv.get("true_boss"),
        })
    return out


def fits_for(table):
    """Fit least-squares yang dipakai _normalize_hero_unlock_stats.

    Direkam SEBELUM tabel dimutasi supaya Godot bisa membandingkan angka
    float-nya langsung (bukan cuma hasil bulatnya) — ini mengunci detail
    `pow(d, 2)` vs `d*d` dan urutan penjumlahan.
    """
    heroes = [(bt, bd["hero_unlock"]) for bt, bd in table.items()
              if bd.get("hero_unlock")]
    heroes.sort(key=lambda h: h[1].get("cost", 0))
    return {
        "hp": list(trend([(hu.get("cost", 0), hu.get("hp", 0))
                          for _, hu in heroes])),
        "dps": list(trend([(hu.get("cost", 0),
                            hu.get("damage", 0) / max(1, hu.get("attack_cooldown", 30))
                            * 60.0) for _, hu in heroes])),
        "skill": list(trend([(hu.get("cost", 0), hu.get("skill_damage", 0))
                             for _, hu in heroes])),
        "heroes": len(heroes),
    }


def run_model():
    pristine, mini, true = load_model_tables()
    schedule = schedule_from_levels()
    rebalance(mini, true)
    smooth(mini, true, schedule)
    curves(true, pristine)
    fits = {"mini": fits_for(mini), "true": fits_for(true)}
    norm_stats(mini, true)
    norm_range(mini, true, tuple(pristine["melee_role_hints"]))
    return pristine, mini, true, schedule, fits


# ─────────────────────────────────────────────────────────────────────
# Fixture
# ─────────────────────────────────────────────────────────────────────


def build_probes(fits):
    """Kasus uji kecil untuk helper statis BossData.gd.

    py_round mengunci round() banker's Python (Godot round() half-up),
    slots mengunci batas kelompok wave, trend mengunci least-squares termasuk
    kasus degenerasi (sxx == 0, daftar kosong) dan fit NYATA atas data 216
    boss (dibandingkan dengan toleransi 1e-9; hasil bulatnya harus persis).
    """
    return {
        "py_round": [[0.5, 0], [1.5, 2], [2.5, 2], [3.5, 4], [-0.5, 0],
                     [-1.5, -2], [-2.5, -2], [2.0, 2], [2.4999999, 2],
                     [2.5000001, 3], [1000000.5, 1000000], [0.0, 0]],
        "py_int": [[2.9, 2], [-2.9, -2], [7500.0, 7500], [0.999, 0]],
        "slots": [[1, "w10"], [10, "w10"], [12, "w10"], [13, "w18"],
                  [21, "w18"], [22, "w25"], [30, "w25"]],
        "trend": [
            {"in": [[1, 10], [2, 20], [3, 30]], "out": [10.0, 0.0]},
            {"in": [[0, 5], [10, 5]], "out": [0.0, 5.0]},
            {"in": [[5, 7], [5, 9]], "out": [0.0, 8.0]},
            {"in": [], "out": [0.0, 0.0]},
            {"in": [[100, 800], [250, 1200], [400, 1500], [700, 2600]],
             "out": list(trend([(100, 800), (250, 1200), (400, 1500),
                                (700, 2600)]))},
        ],
        "fits": fits,
    }


def build_fixture(mini, true, schedule, fits):
    final = {}
    for table_name, table in (("mini", mini), ("true", true)):
        for btype, row in table.items():
            entry = {"table": table_name}
            for f in BOSS_FIELDS:
                if f in row:
                    entry[f] = row[f]
            hu = row.get("hero_unlock")
            if hu:
                entry["hero_unlock"] = {f: hu[f] for f in HU_FIELDS if f in hu}
            final[btype] = entry
    return {
        "source": "bosses/boss_data.py (pipeline import-time) dijalankan atas "
                  "godot/data/boss_pristine.json + godot/data/levels.json",
        "boss_fields": BOSS_FIELDS,
        "hu_fields": HU_FIELDS,
        "schedule": [{"mini_bosses": {str(w): n for w, n in cfg["mini_bosses"].items()},
                      "true_boss": cfg["true_boss"]} for cfg in schedule],
        "counts": {"mini": len(mini), "true": len(true),
                   "all": len({**mini, **true})},
        "probes": build_probes(fits),
        "final": final,
    }


def stale_report(new_text):
    """Ringkasan perbedaan fixture lama vs baru (untuk pesan stale)."""
    lines = []
    if not os.path.exists(FIXTURE):
        return ["fixture belum ada"]
    try:
        old = json.loads(open(FIXTURE, encoding="utf-8").read())
        new = json.loads(new_text)
    except Exception as exc:
        return [f"fixture lama tidak bisa dibaca: {exc}"]
    if old.get("schedule") != new.get("schedule"):
        lines.append("jadwal level (levels.json) berubah")
    if old.get("counts") != new.get("counts"):
        lines.append("jumlah boss berubah: %s -> %s" % (old.get("counts"), new.get("counts")))
    of, nf = old.get("final", {}), new.get("final", {})
    changed = [k for k in sorted(set(of) | set(nf)) if of.get(k) != nf.get(k)]
    for k in changed[:6]:
        lines.append("%s: %s -> %s" % (k, json.dumps(of.get(k), sort_keys=True)[:110],
                                       json.dumps(nf.get(k), sort_keys=True)[:110]))
    if len(changed) > 6:
        lines.append("... +%d boss lain berubah" % (len(changed) - 6))
    return lines or ["perubahan tak terinci (bandingkan berkas)"]


def write_fixture(fx):
    os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
    text = json.dumps(fx, indent=1, sort_keys=True) + "\n"
    with open(FIXTURE, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


# ─────────────────────────────────────────────────────────────────────
# Cek struktural BossData.gd
# ─────────────────────────────────────────────────────────────────────


def gd_src(path):
    return open(path, encoding="utf-8").read()


def structural_checks(mini, true):
    src = gd_src(BOSS_DATA_GD)
    body = re.sub(r"(?m)^\s*#.*$", "", src)

    # Gotcha GDScript yang diketahui harus tetap terpasang.
    expect("pow(c3 - mx, 2.0)" in body,
           "sxx memakai pow(d, 2.0) — pow() Python dan GDScript sama-sama libm, "
           "sedangkan d*d beda ~1 ulp untuk sebagian nilai")
    expect(re.search(r"static func _py_round", body) is not None,
           "round() Python (banker's) di-port sebagai _py_round, bukan round() Godot")
    expect("return int(f) if int(f) % 2 == 0 else int(f) + 1" in body,
           "_py_round: nilai .5 dibulatkan ke genap (half-to-even)")
    expect(re.search(r"static func _py_int", body) is not None,
           "int() Python (pemotongan ke nol) di-port sebagai _py_int")
    expect(body.count("float(") > 30,
           "pembagian eksplisit float(...) — `/` antar int di GDScript membulatkan")
    expect("return int(a[2]) < int(b[2])" in body,
           "sort hero_unlock STABIL: indeks asal jadi tie-break (banyak cost seri)")
    expect("_truthy_hu(bd)" in body,
           "truthiness Python: hero_unlock None DAN dict kosong sama-sama dilewati")
    expect("float(value) < 0.85 * float(running_max)" in body,
           "running-max 15% membandingkan float (Python: int < 0.85*int = float)")
    expect('if schedule.is_empty():\n\t\treturn' in body,
           "jadwal kosong = no-op (paritas except: return pygame)")

    # Kelima langkah terpanggil berurutan di build().
    order = [body.index(name) for name in (
        "apply_boss_rebalancing(mini, true_table)",
        "smooth_boss_progression(mini, true_table, schedule)",
        "apply_boss_curve_overrides(true_table,",
        "normalize_hero_unlock_stats(mini, true_table)",
        "normalize_hero_unlock_range(mini, true_table,")]
    expect(order == sorted(order), "build() menjalankan 5 langkah persis urutan import")

    # Konstanta kunci.
    expect(re.search(r'slot_of_mini_wave\(wave: int\) -> String:\n\tif wave <= 12:'
                     r'\n\t\treturn "w10"\n\tif wave <= 21:\n\t\treturn "w18"'
                     r'\n\treturn "w25"', body) is not None,
           "slot wave mini 10-12 / 13-21 / 22+ identik sumber")
    for lit in ["7500", "2.2", "1.6", "1.4", "1.3", "85", "1.25", "1.2",
                "36000", "2.4", "2.0", "1.45", "145", "1.5", "1.35",
                "0.70", "0.80", "1.30", "1.20", "0.85"]:
        expect(lit in body, f"konstanta piecewise/clamp {lit} ada di BossData.gd")

    # MELEE_ROLE_HINTS harus sama dengan pristine (sumber kebenaran runtime).
    pristine, _, _ = None, None, None
    hints_gd = re.findall(r'"([a-z ]+)"', re.search(
        r"const MELEE_ROLE_HINTS: Array = \[(.*?)\n\]", src, re.S).group(1))
    hints_py = json.load(open(PRISTINE, encoding="utf-8"))["melee_role_hints"]
    expect(hints_gd == list(hints_py),
           f"MELEE_ROLE_HINTS sama dengan pristine ({len(hints_py)} peran)")

    # BossDB benar-benar memakai BossData sebagai fallback.
    db = gd_src(BOSS_DB_GD)
    expect("BossData" in db and "boss_pristine.json" in db,
           "BossDB memakai BossData + boss_pristine.json sebagai jalur fallback")
    expect(re.search(r"BossData\.build\(", db) is not None,
           "BossDB memanggil BossData.build (bukan cuma load_pristine)")
    expect('"hp": 2500' not in db and "2500" not in db,
           "fallback tabel hardcode 3 boss lama sudah dihapus dari BossDB")

    # pristine harus benar-benar hasil ekstraksi AST (bukan salinan hasil).
    conv = gd_src(os.path.join(ROOT, "tools", "convert_to_godot.py"))
    expect("ast.parse" in conv and "boss_pristine.json" in conv,
           "converter mengekstrak literal tabel boss_data lewat AST")
    expect(len(mini) == 162 and len(true) == 54,
           f"pristine lengkap 162 mini + 54 true (dapat {len(mini)}+{len(true)})")


# ─────────────────────────────────────────────────────────────────────
# 1) Model vs modul boss_data ASLI
# ─────────────────────────────────────────────────────────────────────


def test_against_real_module(mini, true):
    from bosses import boss_data as real
    checked = 0
    diffs = []
    for table, real_table in ((mini, real.MINI_BOSS_TYPES),
                              (true, real.TRUE_BOSS_TYPES)):
        expect(set(table.keys()) == set(real_table.keys()),
               f"kunci tabel sama ({len(table)} boss)")
        for btype, row in table.items():
            r = real_table[btype]
            for f in BOSS_FIELDS:
                if f in row or f in r:
                    checked += 1
                    if row.get(f) != r.get(f):
                        diffs.append(f"{btype}.{f}: {row.get(f)} != {r.get(f)}")
            hu, rhu = row.get("hero_unlock"), r.get("hero_unlock")
            expect(bool(hu) == bool(rhu), f"{btype}: keberadaan hero_unlock sama")
            if hu and rhu:
                for f in HU_FIELDS:
                    checked += 1
                    if hu.get(f) != rhu.get(f):
                        diffs.append(f"{btype}.hero_unlock.{f}: "
                                     f"{hu.get(f)} != {rhu.get(f)}")
    expect(not diffs,
           f"model pipeline == boss_data ASLI untuk {checked} field "
           f"({len(diffs)} selisih: {', '.join(diffs[:6])})")
    print(f"     {checked} field dibandingkan dengan modul asli")
    return checked


# ─────────────────────────────────────────────────────────────────────
# 2) Invariant pipeline diukur dari hasil nyata
# ─────────────────────────────────────────────────────────────────────


def test_invariants(pristine, mini, true, schedule):
    # Rebalance benar-benar menaikkan angka (bukan model no-op).
    raised = 0
    for btype, row in mini.items():
        if row["hp"] > pristine["mini"][btype]["hp"]:
            raised += 1
    expect(raised > 100, f"rebalance menaikkan HP {raised} mini boss (> 100)")
    raised_t = sum(1 for b, r in true.items()
                   if r["hp"] >= pristine["true"][b]["hp"])
    expect(raised_t == len(true), f"HP true boss tak pernah turun ({raised_t}/{len(true)})")

    # Piecewise: mini hp<10000 -> minimal 7500.
    for btype, row in pristine["mini"].items():
        if row.get("hp", 3000) < 10000:
            expect(mini[btype]["hp"] >= 7500,
                   f"{btype}: lantai HP 7500 untuk mini hp<10000")
            break

    # Smoothing: monoton per slot wave untuk mini, per level untuk true.
    prev = {"w10": [0, 0, 0], "w18": [0, 0, 0], "w25": [0, 0, 0]}
    mono = True
    for cfg in schedule:
        for wave, name in sorted(cfg["mini_bosses"].items()):
            b = mini.get(name)
            if not b:
                continue
            s = slot_of(wave)
            if (b["hp"] < prev[s][0] or b["damage"] < prev[s][1]
                    or b["ability_damage"] < prev[s][2]):
                mono = False
            prev[s] = [b["hp"], b["damage"], b["ability_damage"]]
    expect(mono, "mini boss monoton per slot wave (hp/damage/ability)")
    ph = pd = pa = 0
    mono_t = True
    for cfg in schedule:
        b = true.get(cfg["true_boss"])
        if not b:
            continue
        if b["hp"] < ph or b["damage"] < pd or b["ability_damage"] < pa:
            mono_t = False
        ph, pd, pa = b["hp"], b["damage"], b["ability_damage"]
    expect(mono_t, "true boss monoton per level")

    # Kurva override menang atas smoothing (nilai akhir == kurva).
    for name, hp in pristine["curves"]["hp"].items():
        if name in true:
            expect(true[name]["hp"] == hp,
                   f"{name}: curve override HP menang ({true[name]['hp']} == {hp})")
    expect(len(pristine["curves"]["hp"]) > 0, "kurva HP true boss tidak kosong")

    # Aturan hero_unlock setelah normalisasi.
    hints = tuple(pristine["melee_role_hints"])
    heroes = 0
    melee70 = ranged = 0
    for table in (mini, true):
        for btype, row in table.items():
            hu = row.get("hero_unlock")
            if not hu:
                continue
            heroes += 1
            expect(hu["skill_damage"] > 0, f"{btype}: skill_damage ternormalisasi > 0")
            expect(hu["hp"] > 0 and hu["damage"] > 0,
                   f"{btype}: hp/damage ternormalisasi > 0")
            role = (hu.get("role") or "").lower()
            is_melee = any(k in role for k in hints)
            if hu["range"] == 70:
                melee70 += 1
            else:
                ranged += 1
                expect(120 <= hu["range"] <= 220,
                       f"{btype}: range ranged dalam 120..220 ({hu['range']})")
                expect(not is_melee, f"{btype}: peran melee tidak boleh ranged")
            if hu.get("skill_range"):
                expect(hu["skill_range"] >= hu["range"],
                       f"{btype}: skill_range >= range")
    expect(heroes > 150, f"hero_unlock ternormalisasi untuk {heroes} boss (> 150)")
    expect(melee70 > 60 and ranged > 60,
           f"aturan range terpakai dua arah (melee/pendek {melee70}, ranged {ranged})")

    # Running-max: urut cost, stat tidak anjlok lebih dari 15%.
    for table in (mini, true):
        rows = [(bd["hero_unlock"].get("cost", 0), bd["hero_unlock"])
                for bd in table.values() if bd.get("hero_unlock")]
        rows.sort(key=lambda r: r[0])
        for field in ("hp", "damage", "skill_damage"):
            run = 0
            for cost, hu in rows:
                expect(hu[field] >= 0.85 * run - 1e-9,
                       f"{field} tidak anjlok >15% setelah running-max "
                       f"(cost {cost}: {hu[field]} vs {run})")
                run = max(run, hu[field])

    # Clamp outlier: hasil akhir berada dalam pita trend ATAU di batas clamp.
    for table in (mini, true):
        heroes_t = [(bt, bd["hero_unlock"]) for bt, bd in table.items()
                    if bd.get("hero_unlock")]
        heroes_t.sort(key=lambda h: h[1].get("cost", 0))
        if not heroes_t:
            continue
        hp_fit = trend([(hu.get("cost", 0), hu.get("hp", 0)) for _, hu in heroes_t])
        for bt, hu in heroes_t:
            cost = hu.get("cost", 0)
            pred = hp_fit[0] * cost + hp_fit[1]
            if pred <= 0:
                continue
            # Setelah pipeline, hp harus >= 0.80*pred (lantai clamp) atau
            # dinaikkan running-max — keduanya >= 0.70*pred.
            expect(hu["hp"] >= 0.70 * pred - 1e-9,
                   f"{bt}: hp {hu['hp']} tidak di bawah pita clamp (pred {pred:.0f})")


# ─────────────────────────────────────────────────────────────────────
# 3) Ekspor baker (bosses.json) == hasil pipeline
# ─────────────────────────────────────────────────────────────────────


def test_baked_export(mini, true):
    """Dua ekspor baker harus == hasil pipeline.

    `bosses.json` membawa angka runtime (hp/damage/ability/skill), sedangkan
    `boss_stats_full.json` membawa hero_unlock yang sudah dinormalisasi —
    keduanya ditulis converter dari modul boss_data yang SAMA, jadi keduanya
    harus cocok dengan model (dan dengan fixture yang diputar Godot).
    """
    baked = json.load(open(BOSSES_JSON, encoding="utf-8"))
    full = json.load(open(os.path.join(ROOT, "godot", "data",
                                       "boss_stats_full.json"), encoding="utf-8"))
    checked = 0
    bad = []
    for table in (mini, true):
        for btype, row in table.items():
            b = baked.get(btype)
            expect(b is not None, f"{btype} ada di bosses.json")
            if b is not None:
                for f in BOSS_FIELDS:
                    if f in row:
                        checked += 1
                        if b.get(f) != row[f]:
                            bad.append(f"bosses.json {btype}.{f}: "
                                       f"{b.get(f)} != {row[f]}")
            sf = full.get(btype) or {}
            hu, bhu = row.get("hero_unlock"), sf.get("hero_unlock") or {}
            expect(bool(hu) == bool(bhu),
                   f"{btype}: keberadaan hero_unlock sama di baker")
            if hu and bhu:
                for f in HU_FIELDS:
                    if f in hu:
                        checked += 1
                        if bhu.get(f) != hu[f]:
                            bad.append(f"boss_stats_full {btype}.hero_unlock.{f}: "
                                       f"{bhu.get(f)} != {hu[f]}")
    expect(not bad, f"ekspor baker == hasil pipeline ({checked} field; "
                    f"{len(bad)} selisih: {', '.join(bad[:5])})")
    print(f"     {checked} field baker dibandingkan")


def test_probes(fits):
    """Probe yang direkam untuk Godot harus benar terhadap Python juga."""
    for v, want in build_probes(fits)["py_round"]:
        expect(round(v) == want, f"round({v}) Python == {want} (banker's)")
    for w, want in build_probes(fits)["slots"]:
        expect(slot_of(w) == want, f"slot_of({w}) == {want}")
    for case in build_probes(fits)["trend"]:
        got = list(trend([tuple(p) for p in case["in"]]))
        expect(all(abs(g - e) <= 1e-9 * max(1.0, abs(e))
                   for g, e in zip(got, case["out"])),
               f"trend({case['in'][:2]}...) == {case['out']} (dapat {got})")
    expect(fits["mini"]["heroes"] > 100 and fits["true"]["heroes"] > 40,
           "fit direkam untuk mini (%d) dan true (%d) hero unlock"
           % (fits["mini"]["heroes"], fits["true"]["heroes"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write-fixture", action="store_true",
                    help="tulis ulang godot/tests/fixtures/boss_data.json")
    args = ap.parse_args(argv)

    pristine, mini, true, schedule, fits = run_model()
    test_against_real_module(mini, true)
    test_invariants(pristine, mini, true, schedule)
    test_baked_export(mini, true)
    structural_checks(mini, true)
    test_probes(fits)

    fx = build_fixture(mini, true, schedule, fits)
    new_text = json.dumps(fx, indent=1, sort_keys=True) + "\n"
    if args.write_fixture:
        write_fixture(fx)
        print(f"     fixture ditulis: {os.path.relpath(FIXTURE, ROOT)} "
              f"({len(new_text) // 1024} KB, {len(fx['final'])} boss)")
    else:
        expect(os.path.exists(FIXTURE),
               "fixture boss_data.json ada (jalankan --write-fixture)")
        if os.path.exists(FIXTURE):
            old_text = open(FIXTURE, encoding="utf-8").read()
            stale = old_text != new_text
            expect(not stale,
                   "fixture SEGAR terhadap boss_data.py + levels.json + "
                   "boss_pristine.json — jalankan "
                   "`python3 tools/test_boss_data_parity.py --write-fixture`"
                   + ("" if not stale else " — beda: " + "; ".join(stale_report(new_text))))

    print("=" * 64)
    if _failures:
        print(f"[boss_data_parity] FAIL ({len(_failures)}/{_checks})")
        for f in _failures[:25]:
            print("  -", f)
        return 1
    print(f"[boss_data_parity] PASS ({_checks} checks) — pipeline data boss "
          f"1:1 dengan boss_data.py, fixture segar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
