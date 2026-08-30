# ================================
# tools/balance_audit.py
#
# Audit balance hero: MENGUKUR masalah, bukan menghitung ulang opini.
# Angka di sini yang jadi dasar tiap perubahan di hero_balance.py /
# hero_archetypes.py, dan angka yang sama dipakai lagi setelah patch
# (lihat docs/hero_kategori.md "Balance pass 2026-08-30").
#
# Dua mode:
#   --static : baca bosses/boss_data.py (DATA MENTAH, tanpa engine)
#   --ingame : import _core -> memakai angka FINAL (setelah hero_balance)
#              + tabel resistansi boss asli. Ini angka "yang dirasakan
#              pemain"; mode default.
#
# Metrik (semua punya target eksplisit, lihat TARGETS):
#   1. CORR-HP-DPS   korelasi HP vs DPS. Dekat 1.0 = tidak ada trade-off
#                    arketipe (semua mahal menang di dua sumbu).
#   2. IDENTITY-GRID DPS & EHP per sel (sekolah x gaya main). Tank harus
#                    bayar di DPS; carry bayar di HP; power tiap sel
#                    0.85..1.25 = sehat.
#   3. SCHOOL-PARITY rata-rata (magic DPS efektif)/(fisik DPS efektif) vs
#                    boss mini & true. 0.95..1.10 = sehat; >1.25 berarti
#                    satu sekolah cuma jadi pajak.
#   4. BOSS-PREF     sebaran preferensi per boss (p90/p10). >1.25 berarti
#                    "bawa hero sesuai lawan" terasa.
#   5. PRICE-SPREAD  sebaran power di dalam satu band harga in-game.
#   6. BURST-WASTE   % damage yang dipotong cap anti-burst (12%/8% HP boss)
#                    - hanya informasi: cap memang disengaja.
#   7. STARTER-GAP   DPS starter vs rata-rata hero unlock.
#
#   python3 tools/balance_audit.py                  # ringkas (ingame)
#   python3 tools/balance_audit.py --static --json /tmp/before.json
#   python3 tools/balance_audit.py --md docs/balance_audit.md
# ================================
import argparse
import importlib.util
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

# target: (longgar, bawah, atas) - dipakai --check untuk CI-style gate
TARGETS = {
    "corr_hp_dps": (None, None, 0.80),
    "identity_spread_x": (1.20, None, None),
    "school_ratio": (None, 0.90, 1.15),
    "boss_pref_ratio": (1.20, None, None),
    "price_spread_x": (None, None, 2.20),
}
# power pool tidak boleh bergeser jauh (redistribusi, bukan buff/nerf)
POWER_DELTA_MAX = 0.12


def _load_analyzer():
    spec = importlib.util.spec_from_file_location(
        "ah", os.path.join(HERE, "analyze_hero_archetypes.py"))
    ah = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ah)
    return ah


def _corr(xs, ys):
    if len(xs) < 3:
        return 0.0
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = (sum((a - mx) ** 2 for a in xs)
           * sum((b - my) ** 2 for b in ys)) ** 0.5
    return num / den if den else 0.0


def armor_mult(a):
    return 1.0 - a * 0.06 / (1.0 + a * 0.06) if a > 0 else 1.0


# ── MODE 1: STATIK (data mentah saja, tanpa pygame) ─────────────────────
def audit_static():
    ah = _load_analyzer()
    rows = ah.load_heroes()
    reg = ah.registered_heroes()
    for r in rows:
        r["_m"] = ah.metrics(r)
    ah.classify(rows)
    for r in rows:
        r["_m"]["profile"] = ah.resist_profile(r)
    boss = [r for r in rows if r["boss_class"] != "starter"]
    st = [r for r in rows if r["boss_class"] == "starter"]

    out = {"mode": "static", "n_hero": len(rows), "n_boss_hero": len(boss)}
    out["corr_hp_dps"] = round(_corr([r["_m"]["safety"] for r in boss],
                                     [r["_m"]["total_dps"] for r in boss]), 3)
    grid = {}
    for r in boss:
        k = "%s|%s" % (r["_m"]["dmg_type"], r["_m"]["role_class"])
        g = grid.setdefault(k, {"n": 0, "dps": [], "ehp": []})
        g["n"] += 1
        g["dps"].append(r["_m"]["total_dps"])
        g["ehp"].append(r["_m"]["safety"])
    med_dps = statistics.median([r["_m"]["total_dps"] for r in boss])
    med_ehp = statistics.median([r["_m"]["safety"] for r in boss])
    out["identity_grid"] = {
        k: {"n": v["n"], "avg_dps": round(statistics.mean(v["dps"]), 0),
            "avg_ehp": round(statistics.mean(v["ehp"]), 0),
            "dps_x": round(statistics.mean(v["dps"]) / med_dps, 2),
            "ehp_x": round(statistics.mean(v["ehp"]) / med_ehp, 2),
            "power": round(0.8 * statistics.mean(v["dps"]) / med_dps
                           + 0.2 * statistics.mean(v["ehp"]) / med_ehp, 2)}
        for k, v in sorted(grid.items())}
    pow_vals = [v["power"] for v in out["identity_grid"].values()]
    out["identity_spread_x"] = round(max(pow_vals) / max(min(pow_vals), 1e-9),
                                     2)
    out["starter_gap"] = {
        "starter_avg_dps": round(statistics.mean(
            [r["_m"]["total_dps"] for r in st]), 1),
        "unlock_avg_dps": round(statistics.mean(
            [r["_m"]["total_dps"] for r in boss]), 1),
        "gap_x": round(statistics.mean([r["_m"]["total_dps"] for r in boss])
                       / max(statistics.mean(
                           [r["_m"]["total_dps"] for r in st]), 1), 2)}
    return out


# ── MODE 2: IN-GAME (angka final + resistansi boss asli) ────────────────
def audit_ingame():
    import _core                                    # noqa: F401  (harus dulu)
    import hero_archetypes as ha
    import hero_balance as hb
    cat = _core.get_all_hero_types()
    rows = []
    for ht, s in cat.items():
        m = hb.metrics(s)
        a = ha.get_archetype(ht, s)
        rows.append({"ht": ht, "boss_hero": bool(s.get("is_boss_hero")),
                     "cls": s.get("boss_class", "starter"),
                     "school": a["dmg_type"], "style": a.get("playstyle"),
                     "cost": float(s.get("cost", 0) or 0),
                     "unlock": float(s.get("unlock_cost", 0) or 0),
                     "hp": m["hp"], "dps": m["dps"], "ehp": m["ehp"],
                     "bal": s.get("__bal"), "dmg": m["dmg"], "cd": m["cd"],
                     "sk": m["skill"], "skcd": m["skcd"],
                     "require": s.get("unlock_require_boss")})
    boss = [r for r in rows if r["boss_hero"]]
    st = [r for r in rows if not r["boss_hero"]]

    out = {"mode": "ingame", "n_hero": len(rows), "n_boss_hero": len(boss)}
    out["corr_hp_dps"] = round(_corr([r["hp"] for r in boss],
                                     [r["dps"] for r in boss]), 3)
    med_dps = statistics.median([r["dps"] for r in boss])
    med_ehp = statistics.median([r["ehp"] for r in boss])
    grid = {}
    for r in boss:
        k = "%s|%s" % (r["school"], r["style"])
        g = grid.setdefault(k, {"n": 0, "dps": [], "ehp": []})
        g["n"] += 1
        g["dps"].append(r["dps"])
        g["ehp"].append(r["ehp"])
    out["identity_grid"] = {
        k: {"n": v["n"], "avg_dps": round(statistics.mean(v["dps"]), 0),
            "avg_ehp": round(statistics.mean(v["ehp"]), 0),
            "dps_x": round(statistics.mean(v["dps"]) / med_dps, 2),
            "ehp_x": round(statistics.mean(v["ehp"]) / med_ehp, 2),
            "power": round(0.8 * statistics.mean(v["dps"]) / med_dps
                           + 0.2 * statistics.mean(v["ehp"]) / med_ehp, 2)}
        for k, v in sorted(grid.items())}
    pv = [v["power"] for v in out["identity_grid"].values()]
    out["identity_spread_x"] = round(max(pv) / max(min(pv), 1e-9), 2)

    # sekolah vs boss: pakai tabel resistansi yang benar-benar dipakai
    # base_boss.__init__ (per boss, bukan rata-rata kelas)
    res = ha.BOSS_RESISTANCES
    per = {}
    pref = {"mini": [], "true": []}
    for dc in ("mini", "true"):
        sums = {"PHYSICAL": [], "MAGIC": []}
        for r in boss:
            if r["cls"] != dc:
                continue
            rr = res.get(r["require"] or r["ht"])
            if rr is None:
                continue
            mult = (ha.physical_mitigation(rr["armor"])
                    if r["school"] == "PHYSICAL"
                    else 1.0 - rr["magic_resist"])
            sums[r["school"]].append(r["dps"] * mult)
        if sums["PHYSICAL"] and sums["MAGIC"]:
            p = statistics.mean(sums["PHYSICAL"])
            m = statistics.mean(sums["MAGIC"])
            per[dc] = {"physical": round(p, 1), "magic": round(m, 1),
                       "ratio_magic_over_phys": round(m / max(p, 1e-9), 3)}
    for bt, br in res.items():
        pref[br["boss_class"]].append(
            ha.physical_mitigation(br["armor"]) / max(1e-6,
                                                      1.0 - br["magic_resist"]))
    for dc, v in pref.items():
        v.sort()
        if v:
            per.setdefault(dc, {})["boss_pref_p10_p50_p90"] = [
                round(v[len(v) // 10], 2), round(v[len(v) // 2], 2),
                round(v[int(0.9 * (len(v) - 1))], 2)]
    out["effective_dps_vs_boss"] = per
    pref_all = sorted(x for v in pref.values() for x in v)
    out["boss_pref_ratio"] = round(
        pref_all[int(0.9 * len(pref_all))] / max(pref_all[len(pref_all)//10],
                                                 1e-9), 2)

    # sebaran power dalam band harga in-game
    bands = {}
    for r in boss:
        key = "%dk-%dk" % (int(r["cost"] // 1000),
                           int(r["cost"] // 1000) + 1)
        bands.setdefault(key, []).append(
            0.8 * r["dps"] / med_dps + 0.2 * r["ehp"] / med_ehp)
    sp = {}
    for k, v in sorted(bands.items()):
        if len(v) < 8:
            continue
        sp[k] = {"n": len(v), "spread_x": round(max(v) / max(min(v), 1e-9), 2)}
    out["price_spread_by_band"] = sp
    out["price_spread_x"] = round(statistics.median(
        [v["spread_x"] for v in sp.values()]) if sp else 0.0, 2)

    # burst waste vs cap anti-burst (HP boss asli)
    try:
        from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES
        boss_hp = {}
        for t, tbl in (("mini", MINI_BOSS_TYPES), ("true", TRUE_BOSS_TYPES)):
            for bt, bd in tbl.items():
                boss_hp[bt] = float(bd.get("hp", 0) or 0)
    except Exception:
        boss_hp = {}
    waste = {"mini": [], "true": []}
    for r in boss:
        bh = boss_hp.get(r["require"], 0.0)
        if bh <= 0:
            continue
        cap_pct = 0.08 if r["cls"] == "true" else 0.12
        cap = bh * cap_pct
        hit = r["dmg"] * 60.0 / r["cd"] / 60.0 * 1.0     # damage/pukulan basic
        sk_hit = r["sk"]
        tot = hit + sk_hit
        if tot > 0:
            lost = max(0.0, hit - cap) + max(0.0, sk_hit - cap)
            waste[r["cls"]].append(lost / tot)
    out["burst_waste_vs_cap"] = {
        k: {"n": len(v),
            "median_%": round(100 * statistics.median(v), 1) if v else 0,
            "p90_%": round(100 * sorted(v)[int(0.9 * max(0, len(v) - 1))], 1)
            if v else 0,
            "share_over_15%": round(100.0 * sum(1 for x in v if x > 0.15)
                                    / max(len(v), 1), 1)}
        for k, v in waste.items()}

    # starter: angka HERO sebenarnya (catch-up baru diterapkan saat Hero
    # dibuat, jadi katalog saja tidak cukup)
    st_dps, st_hp = [], []
    try:
        from _entity import Hero
        for r in st:
            h = Hero(r["ht"], "blue")
            st_dps.append(h.base_damage * 60.0 / max(1, h.attack_cooldown)
                          + h.skill_damage_base * 60.0
                          / max(1, h.skill_cooldown_max))
            st_hp.append(h.base_hp)
    except Exception as exc:                     # pragma: no cover
        st_dps = [r["dps"] for r in st]
        st_hp = [int(r["hp"]) for r in st]
        out["starter_gap_error"] = repr(exc)
    out["starter_gap"] = {
        "starter_avg_dps": round(statistics.mean(st_dps), 1),
        "unlock_avg_dps": round(statistics.mean([r["dps"] for r in boss]), 1),
        "gap_x": round(statistics.mean([r["dps"] for r in boss])
                       / max(statistics.mean(st_dps), 1), 2),
        "starter_hp": sorted(st_hp)}
    # ── DELTA POWER POOL: balance harus REDISTRIBUSI, bukan buff ──
    # hero_balance menyimpan rata-rata DPS/EHP PRASEBELUM-multiplier di
    # LAST["pool_means"] dan koreksi jangkarnya di LAST["pool_anchor"].
    # Dihitung dengan rumus hero_balance.metrics() yang sama di kedua sisi
    # (BUKAN metrik tools/analyze_hero_archetypes.py yang memasukkan buff
    # melee + kemampuan boss - membandingkan dua rumus berbeda menghasilkan
    # angka 0.75x palsu yang sempat bikin panik).
    try:
        means = hb.LAST.get("pool_means") or {}
        anchor = hb.LAST.get("pool_anchor") or {}
        got = [r for r in boss]
        if means.get("n") and got:
            cur_d = statistics.mean([r["dps"] for r in got])
            cur_h = statistics.mean([r["ehp"] for r in got])
            out["pool_power_delta"] = {
                "n": means["n"],
                "avg_dps_pristine": round(means["dps"], 1),
                "avg_dps_balanced": round(cur_d, 1),
                "dps_x": round(cur_d / max(means["dps"], 1e-9), 3),
                "avg_ehp_pristine": round(means["ehp"], 1),
                "avg_ehp_balanced": round(cur_h, 1),
                "ehp_x": round(cur_h / max(means["ehp"], 1e-9), 3),
                "anchor_applied": anchor,
            }
        else:
            out["pool_power_delta"] = {"error": "LAST['pool_means'] kosong"}
    except Exception as exc:                 # pragma: no cover
        out["pool_power_delta"] = {"error": repr(exc)}

    out["hero_level_curve"] = {"max_level": _core.MAX_HERO_LEVEL,
                               "dmg_mult": _core.HERO_LEVELS[
                                   _core.MAX_HERO_LEVEL]["dmg_mult"],
                               "hp_mult": _core.HERO_LEVELS[
                                   _core.MAX_HERO_LEVEL]["hp_mult"]}
    applied = [r["bal"] for r in boss if r["bal"]]
    out["balance_pass"] = {
        "applied_to": len(applied),
        "hp_mult": [min(a["hp"] for a in applied), max(a["hp"] for a in applied)]
        if applied else None,
        "dmg_mult": [min(a["dmg"] for a in applied),
                     max(a["dmg"] for a in applied)] if applied else None,
    }
    return out


def check(out):
    """Kembalikan daftar pelanggaran target (kosong = sehat)."""
    bad = []
    for k, (_min, lo, hi) in TARGETS.items():
        v = out.get(k)
        if v is None:
            continue
        if lo is not None and v < lo:
            bad.append("%s=%.3f < %.3f" % (k, v, lo))
        if hi is not None and v > hi:
            bad.append("%s=%.3f > %.3f" % (k, v, hi))
        if _min is not None and v < _min:
            bad.append("%s=%.3f < %.3f (minimal)" % (k, v, _min))
    pd = out.get("pool_power_delta") or {}
    for k in ("dps_x", "ehp_x"):
        v = pd.get(k)
        if v is not None and abs(v - 1.0) > POWER_DELTA_MAX:
            bad.append("pool_power_delta.%s=%.3f (boleh 1.00+/-%.2f)"
                       % (k, v, POWER_DELTA_MAX))
    ratio = (out.get("effective_dps_vs_boss") or {})
    for dc, v in ratio.items():
        r = v.get("ratio_magic_over_phys")
        if r is not None and not (0.90 <= r <= 1.15):
            bad.append("school_ratio[%s]=%.3f di luar 0.90..1.15" % (dc, r))
    return bad


def to_md(out):
    L = ["# Audit balance hero", "",
         "Mode: `%s` - dihasilkan `python3 tools/balance_audit.py --md`."
         % out.get("mode", "?"), ""]
    L.append("| Metrik | Nilai | Target |")
    L.append("|---|---|---|")
    tg = {"corr_hp_dps": ("corr(HP, DPS) semua hero unlock", "<= 0.80"),
          "identity_spread_x": ("sebaran power antar sel arketipe",
                                ">= 1.20 (harus ada beda peran)"),
          "school_ratio": ("magic/fisik vs boss (min & true)",
                           "0.90 .. 1.15"),
          "boss_pref_ratio": ("preferensi boss p90/p10",
                              ">= 1.20 (lawan alami terasa)"),
          "price_spread_x": ("sebaran power dalam satu band harga",
                             "<= 2.20")}
    for k, (label, want) in tg.items():
        if k in ("school_ratio",):
            v = ", ".join("%s: %.3f" % (dc, d["ratio_magic_over_phys"])
                          for dc, d in (out.get("effective_dps_vs_boss")
                                        or {}).items()
                          if "ratio_magic_over_phys" in d)
            L.append("| %s | %s | %s |" % (label, v or "-", want))
        elif k in out:
            L.append("| %s | %s | %s |" % (k if False else label,
                                           out[k], want))
    L += ["", "## Identitas arketipe (1.00 = median pool)", "",
          "| Sel (sekolah x gaya) | n | DPS | EHP | power |", "|---|---|---|---|---|"]
    for k, v in (out.get("identity_grid") or {}).items():
        L.append("| %s | %d | %.2fx | %.2fx | %.2fx |" % (
            k, v["n"], v["dps_x"], v["ehp_x"], v["power"]))
    eb = out.get("effective_dps_vs_boss") or {}
    L += ["", "## Sekolah damage vs boss", "",
          "| Kelas boss | DPS fisik | DPS magic | magic/fisik | p10/p50/p90 "
          "preferensi |", "|---|---|---|---|---|"]
    for dc in ("mini", "true"):
        v = eb.get(dc) or {}
        p = v.get("boss_pref_p10_p50_p90")
        L.append("| %s | %s | %s | %s | %s |" % (
            dc, v.get("physical", "-"), v.get("magic", "-"),
            v.get("ratio_magic_over_phys", "-"),
            " / ".join("%.2f" % x for x in p) if p else "-"))
    st = out.get("starter_gap") or {}
    pd = out.get("pool_power_delta") or {}
    if "dps_x" in pd:
        L += ["", "## Daya pool (harus redistribusi, bukan buff)", "",
              "Rata-rata DPS 216 hero unlock: sebelum balance %.1f -> "
              "sesudah %.1f (**%.3fx**). Rata-rata EHP: %.1f -> %.1f "
              "(**%.3fx**). Kedua angka memakai rumus yang sama "
              "(`hero_balance.metrics`), jadi selisihnya murni hasil "
              "balance pass, bukan beda definisi. Toleransi +/-%.0f%%."
              % (pd["avg_dps_pristine"], pd["avg_dps_balanced"],
                 pd["dps_x"], pd["avg_ehp_pristine"], pd["avg_ehp_balanced"],
                 pd["ehp_x"], 100 * POWER_DELTA_MAX), ""]
    L += ["", "## Starter vs hero unlock", "",
          "Starter rata-rata **%.1f DPS**, hero unlock **%.1f DPS** "
          "(gap %.2fx). HP starter: %s." % (
              st.get("starter_avg_dps", 0), st.get("unlock_avg_dps", 0),
              st.get("gap_x", 0), st.get("starter_hp", [])), ""]
    bw = out.get("burst_waste_vs_cap") or {}
    if bw:
        L += ["", "## Sisa damage yang dipotong cap anti-burst (12%/8%)", "",
              "| Kelas | n | median | p90 | % hero rugi >15% |",
              "|---|---|---|---|---|"]
        for dc, v in bw.items():
            L.append("| %s | %d | %.1f%% | %.1f%% | %.1f%% |" % (
                dc, v["n"], v["median_%"], v["p90_%"], v["share_over_15%"]))
        L += ["", "Catatan: cap ini memang disengaja (anti one-shot boss). "
              "Angka di atas dipakai untuk memutuskan apakah perlu "
              "penyesuaian, bukan sebagai bug.", ""]
    bp = out.get("balance_pass") or {}
    if bp.get("applied_to"):
        L += ["", "## hero_balance.py", "",
              "Diterapkan ke %d hero unlock; rentang multiplier HP %s, "
              "damage %s." % (bp["applied_to"], bp.get("hp_mult"),
                              bp.get("dmg_mult")), ""]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--md")
    ap.add_argument("--static", action="store_true",
                    help="pakai data mentah boss_data.py (tanpa pygame)")
    ap.add_argument("--ingame", action="store_true",
                    help="pakai angka final engine (default)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 kalau ada target yang dilanggar")
    a = ap.parse_args()
    if a.static:
        out = audit_static()
    else:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        out = audit_ingame()
    bad = check(out)
    out["violations"] = bad
    print(json.dumps(out, indent=1))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        print("-> %s" % a.json, file=sys.stderr)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(to_md(out))
        print("-> %s" % a.md, file=sys.stderr)
    if bad:
        print("PELANGGARAN TARGET: %s" % "; ".join(bad), file=sys.stderr)
        if a.check:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
