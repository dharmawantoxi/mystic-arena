# ================================
# tools/analyze_hero_archetypes.py
#
# Kategorikan SEMUA hero yang bisa dimainkan (starter + unlock boss)
# ke dalam arketipe: PHYSICAL / MAGIC / TANK.
#
# Kelas boss sumber (boss_class): "mini" atau "true".
#
# Cara kerja (murni dari data di repo, tanpa angka karangan):
#   1. Stat hero = hero_unlock[*] di bosses/boss_data.py (+ HERO_TYPES
#      di _core.py untuk 6 starter).
#   2. Hero melee mendapat pass yang sama dengan runtime
#      (_entity.py: +15% HP, +20% damage, -12% attack cooldown,
#      range di-clamp ke 70; ranged clamp 120..220).
#   3. Skor tipe serangan dari leksikon kata kunci (role/skill_name/
#      skill_desc/description/title + nama skill boss Q-W-E-R) yang
#      digabung dengan rasio burst skill vs DPS basic attack.
#   4. Kelas bermain (TANK / FIGHTER / CARRY) dari persentil EHP,
#      rasio burst, sustain (heal/shield/lifesteal/immortal).
#   5. HERO_RANK = skor power normalisasi (dipakai untuk urutan tabel).
#
# Output:
#   - stdout: ringkasan + daftar per kategori
#   - --csv PATH : tabel lengkap
#   - --md  PATH : dokumen markdown (tabel penuh, dikelompokkan)
# ================================

import argparse
import ast
import csv
import collections
import json
import re
import sys
import os
import statistics

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── LEXIKON TIPE SERANGAN ───────────────────────────────────────────────
MAGIC_WORDS = [
    "arcane", "spell", "magic", "mage", "sorcer", "witch", "wizard",
    "warlock", "enchant", "hex", "curse", "cursed", "rune", "glyph", "void",
    "astral", "astronom", "cosmic", "celestial", "stellar", "nova",
    "supernova", "nebula", "eclipse", "lunar", "solar", "storm", "thunder",
    "lightning", "shock", "volt", "spark", "electro", "fire", "flame",
    "flaming", "inferno", "ember", "burn", "burning", "blaze", "pyro",
    "ignite", "scorch", "magma", "lava", "sulfur", "ice", "frost", "frore",
    "glacial", "winter", "snow", "blizzard", "cryo", "chill", "freeze",
    "holy", "radiant", "divine", "sacred", "light", "dawnforged", "sanct",
    "shadow", "dark", "abyss", "nether", "dusk", "umbra", "nightmare",
    "night", "occult", "grim", "necro", "soul", "spirit", "ghost", "specter",
    "phantom", "wraith", "revenant", "crypt", "tomb", "grave", "undead",
    "blood", "psionic", "psy", "temporal", "chrono", "time", "sonic",
    "dissonance", "resonance", "venom", "plague", "toxic", "acid", "bio",
    "spore", "decay", "poison", "miasma", "corros", "mana", "focus",
    "concentrat", "chant", "song", "dirge", "aria", "ward", "aegis", "sigil",
    "totem", "idol", "omen", "farseer", "prism", "crystal", "gem", "jade",
    "opal", "force", "kinetic", "telekine", "blink", "warp", "portal",
    "summon", "conjures", "petrify", "petrif",
]


PHYSICAL_WORDS = [
    "blade", "blades", "sword", "katana", "saber", "sabre", "dagger",
    "knive", "knife", "axe", "ax ", "cleaver", "chop", "mace", "hammer",
    "hammerstrike", "gavel", "flail", "spear", "pike", "lance", "halberd",
    "scythe", "sickle", "claw", "talon", "fang", "bite", "tear", "rip",
    "rend", "smash", "crush", "bash", "cleave", "slash", "cut", "pierce",
    "shot", "arrow", "bolt", "quiver", "bow", "gun", "rifle", "pistol",
    "musk", "cannon", "grenade", "bomb", "trap", "net", "hook", "chain",
    "shackle", "anchor", "punch", "fist", "kick", "strike", "rush", "dash",
    "lunge", "charge", "leap", "dive", "throw", "spin", "whirl", "windmill",
    "execution", "execute", "reaper", "hunter", "ranger", "archer", "sniper",
    "marksman", "gunner", "slinger", "brawler", "berserk", "fury", "wrath",
    "combo", "martial", "monk", "samurai", "ronin", "ninja", "kunoichi",
    "shinobi", "pirate", "jolly", "buccaneer", "raider", "marauder",
    "gladiator", "war", "warrior", "fighter", "duelist", "skirmish", "jugg",
    "lifesteal", "bleed", "mutilate", "gash", "lacerat",
]


TANK_WORDS = [
    "guardian", "sentinel", "warden", "bastion", "bulwark", "rampart",
    "fortress", "fortified", "wall", "shield", "shielded", "aegis",
    "protector", "defender", "barrier", "titan", "colossus", "golem",
    "gargantua", "behemoth", "juggernaut", "brute", "bruiser", "tank", "dur",
    "stone", "rock", "granite", "marble", "iron", "steel", "obsidian",
    "basalt", "diamond", "crystal ward", "treant", "ent ", "oak", "bark",
    "thorn", "root", "moss", "mountain", "earth", "terra", "geo", "quake",
    "seismic", "tide", "kraken", "leviathan", "turtle", "shell", "carapace",
    "immortal", "revive", "second life", "rebirth",
]


SELF_SUSTAIN_WORDS = [
    "heal", "rejuv", "regen", "lifesteal", "leech", "siphon", "drain",
    "vampir", "blood price", "aphotic shield", "shield", "absorb", "convert",
    "feed", "feast", "devour", "harvest", "sustain", "second life",
    "immortal", "reincarnat", "revive",
]


CONTROL_WORDS = [
    "stun", "sleep", "charm", "silence", "lock", "bind", "snare", "root",
    "tangle", "web", "net", "slow", "freeze", "petrif", "bansh", "disarm",
    "taunt", "fear", "mute", "trap", "anchor", "flux", "magnetic",
    "ice path", "counter",
]


# Nama skill boss (di entri boss, bukan hero_unlock) - signal kuat
SKILL_NAME_KEYS = [
    "skill_q_name", "skill_w_name", "skill_e_name", "skill_r_name",
    "ability2_name",
]

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


# ─── MEMBACA DATA ────────────────────────────────────────────────────────
def _tables_from_ast(path):
    """Parse module (tanpa di-import) dan ambil dict literal level atas.

    Aman untuk file besar: tidak ada `import pygame`, tidak ada kode yang
    benar-benar dijalankan. Entri yang memuat ekspresi non-literal (mis.
    nama konstanta) di-eval lewat namespace konstanta modul; kalau tetap
    gagal, entri itu dilewati.
    """
    source = open(path, encoding="utf-8").read()
    tree = ast.parse(source)

    consts = {}
    for node in tree.body:                      # NAME = angka  (settings)
        if isinstance(node, ast.Assign) and isinstance(
                node.value, (ast.Constant, ast.UnaryOp)):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    try:
                        consts[t.id] = ast.literal_eval(node.value)
                    except Exception:
                        pass

    out = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Dict):
            continue
        seg = ast.get_source_segment(source, value)
        try:
            data = ast.literal_eval(value)
        except Exception:
            try:
                env = dict(consts)
                env["__builtins__"] = {}
                data = eval("(" + seg + ")", env, {})
            except Exception:
                continue
        for tgt in (node.targets if isinstance(node, ast.Assign)
                    else [node.target]):
            if isinstance(tgt, ast.Name):
                out[tgt.id] = data
    return out


def _exec_module_dict(rel_path, extra_globals=None):
    """Jalankan modul game yang bersih dari pygame lewat exec().

    boss_data.py harus dieksekusi (bukan cuma di-parse) karena ada
    beberapa balance pass di akhir file yang MENGUBAH hero_unlock
    (_normalize_hero_unlock_stats / _normalize_hero_unlock_range).
    Angka mentah di awal file = data basi.
    """
    src = open(os.path.join(REPO, rel_path), encoding="utf-8").read()
    ns = {"__name__": "_boss_data_analysis", "__file__": rel_path}
    ns.update(extra_globals or {})
    exec(compile(src, rel_path, "exec"), ns)
    return ns


def load_heroes():
    """Daftar hero yang bisa dimainkan + statnya + kelas boss sumber."""
    out = []

    core = _tables_from_ast(os.path.join(REPO, "_core.py"))
    starters = core.get("HERO_TYPES", {})
    for htype, stats in starters.items():
        row = dict(stats)
        row["hero_type"] = htype
        row["boss_class"] = "starter"
        row["source_boss"] = None
        row["_boss_entry"] = {}
        out.append(row)

    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    ns = _exec_module_dict(os.path.join("bosses", "boss_data.py"))
    for cls, var in (("mini", "MINI_BOSS_TYPES"),
                     ("true", "TRUE_BOSS_TYPES")):
        for btype, bdata in (ns.get(var) or {}).items():
            hu = bdata.get("hero_unlock")
            if not hu:
                continue
            row = dict(hu)
            row["hero_type"] = btype
            row["boss_class"] = cls
            row["source_boss"] = bdata.get("name", btype)
            row["_boss_entry"] = bdata
            out.append(row)
    return out


def registered_heroes():
    """hero_type yang punya recipe skill khusus di hero_skills/_bundle.py.

    Sisanya pakai _fallback_cast (damage generik) -> di praktiknya
    saat ini semuanya 'fisik' karena belum ada split magic/physical.
    """
    path = os.path.join(REPO, "hero_skills", "_bundle.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = set()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        names = [t.id for t in (node.targets if isinstance(node, ast.Assign)
                                else [node.target])
                 if isinstance(t, ast.Name)]
        if "_SKILL_REGISTRY" not in names or not isinstance(node.value,
                                                            ast.Dict):
            continue
        for k in node.value.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                out.add(k.value)
    return out


# ─── METRIK ──────────────────────────────────────────────────────────────
def metrics(row):
    hp = float(row.get("hp", 0) or 0)
    dmg = float(row.get("damage", 0) or 0)
    rng = float(row.get("range", 0) or 0)
    cd = float(row.get("attack_cooldown", 40) or 40)
    sk_dmg = float(row.get("skill_damage", 0) or 0)
    sk_cd = float(row.get("skill_cooldown", 300) or 300)
    sk_rng = float(row.get("skill_range", 0) or 0)
    spd = float(row.get("speed", 1) or 1)

    melee = rng < 110
    # samakan dengan BALANCE PASS di _entity.Hero.__init__
    if melee:
        hp *= 1.15
        dmg *= 1.20
        cd = max(18.0, cd * 0.88)
        rng = 70.0
    else:
        rng = max(120.0, min(220.0, rng))

    b = row["_boss_entry"]
    sk4 = sum(float(b.get("skill_%s_damage" % k, 0) or 0) for k in "qwer")
    ability = float(b.get("ability_damage", 0) or 0)
    burst = max(sk_dmg, sk4 / 4.0 if sk4 else 0.0) + ability / 4.0

    basic_dps = dmg / max(cd, 1.0) * 60.0          # damage/detik
    skill_dps = burst / max(sk_cd, 1.0) * 60.0     # damage/skill/detik
    total_dps = basic_dps + skill_dps
    burst_ratio = skill_dps / max(total_dps, 0.001)

    # Effective HP vs serangan biasa: berdiri di garis depan = lebih sakit
    ehp = hp * (1.25 if melee else 1.0)
    # vs skill AOE: jangkauan skill besar = bisa berdiri di belakang
    poke = 1.15 if (not melee and sk_rng >= 200) else 1.0

    return {
        "hp": round(hp),
        "dmg": round(dmg, 1),
        "range": round(rng),
        "melee": melee,
        "speed": spd,
        "basic_dps": round(basic_dps, 1),
        "skill_dps": round(skill_dps, 1),
        "total_dps": round(total_dps, 1),
        "burst_ratio": round(burst_ratio, 3),
        "ehp": round(ehp),
        "safety": round(ehp * poke),
        "cost": row.get("cost", 0),
        "skill_name": row.get("skill_name", ""),
        "skill_desc": row.get("skill_desc", ""),
        "role": row.get("role", ""),
        "title": row.get("title", ""),
        "description": row.get("description", ""),
    }


def text_blob(row):
    b = row["_boss_entry"]
    parts = [row.get("role", ""), row.get("title", ""), row.get("name", ""),
             row.get("skill_name", ""), row.get("skill_desc", ""),
             row.get("description", "")]
    for k in SKILL_NAME_KEYS:
        if b.get(k):
            parts.append(str(b[k]))
    for k in ("entrance_text",):
        if b.get(k):
            parts.append(str(b[k]))
    return " ".join(str(p).lower() for p in parts)


def count_hits(blob, words):
    return sum(1 for w in words if w in blob)


def percentile(sorted_vals, v):
    if not sorted_vals:
        return 0.5
    lo = 0
    hi = len(sorted_vals)
    import bisect
    lo = bisect.bisect_left(sorted_vals, v)
    hi = bisect.bisect_right(sorted_vals, v)
    return (lo + hi) / 2.0 / len(sorted_vals)


def _tier(ratio):
    """Label tier dari rasio stat terhadap median kelas boss-nya."""
    if ratio >= 1.45:
        return "S"
    if ratio >= 1.20:
        return "A"
    if ratio >= 0.90:
        return "B"
    if ratio >= 0.65:
        return "C"
    return "D"


# ─── PROFIL RESISTANSI BOSS (armor vs magic resist) ──────────────────────
# Kata kunci yang menandakan boss "keras" (berzirah/batu/baja) vs boss
# "sihir" (arcane/undead/void). Dipakai untuk menyebar armor & MR boss
# supaya sekolah damage punya lawan alami, bukan satu angka seragam.
ARMORED_WORDS = [
    "steel", "iron", "stone", "granite", "obsidian", "fortress", "bulwark",
    "rampart", "wall", "shield", "golem", "colossus", "titan",
    "juggernaut", "brute", "brawler", "mountain", "diamond", "carapace",
    "shell", "turtle", "oak", "bark", "thorn", "siege", "knight",
    "gladiator", "basalt", "marble", "armor", "maiden", "bastion",
    "guardian", "sentinel", "warden", "defender", "protector", "barrier",
]

# Kata penanda "casters" - sengaja JAUH lebih sempit daripada MAGIC_WORDS
# (yang untuk klasifikasi sekolah damage hero): MAGIC_WORDS memuat
# "light", "time", "blood", "song", "force", "gem"... yang membuat 91/162
# boss mini salah label jadi "magic" dan merata-ratakan resistansinya.
CASTER_WORDS = [
    "arcane", "spell", "magic", "mage", "sorcer", "witch", "wizard",
    "warlock", "enchant", "hex", "curse", "cursed", "rune", "glyph",
    "void", "necro", "soul", "spirit", "ghost", "wraith", "phantom",
    "specter", "revenant", "undead", "crypt", "tomb", "grave", "abyss",
    "nether", "occult", "plague", "venom", "toxic", "acid", "poison",
    "miasma", "chaos", "eclipse", "astral", "cosmic", "celestial",
    "nova", "storm", "thunder", "lightning", "inferno", "ember",
    "blaze", "pyro", "magma", "lava", "frost", "glacial", "blizzard",
    "cryo", "freeze", "necromant", "sorcery", "conjurer", "summoner",
]


def resist_profile(row):
    """'armored' | 'magic' | 'brute' | 'soft' | 'balanced'."""
    blob = text_blob(row)
    a = count_hits(blob, ARMORED_WORDS)
    m = count_hits(blob, CASTER_WORDS)
    if a >= 2 and a > m:
        return "armored"
    if m >= 2 and m > a:
        return "magic"
    if m > a:
        return "soft"
    if a > m:
        return "brute"
    return "balanced"


# ─── KLASIFIKASI ─────────────────────────────────────────────────────────
def classify(rows):
    ehp_list = sorted(r["_m"]["safety"] for r in rows)
    dps_list = sorted(r["_m"]["total_dps"] for r in rows)
    p98_dps = dps_list[min(len(dps_list) - 1, int(0.98 * len(dps_list)))]
    p98_ehp = ehp_list[min(len(ehp_list) - 1, int(0.98 * len(ehp_list)))]

    for r in rows:
        m = r["_m"]
        blob = text_blob(r)
        magic_hits = count_hits(blob, MAGIC_WORDS)
        phys_hits = count_hits(blob, PHYSICAL_WORDS)
        tank_hits = count_hits(blob, TANK_WORDS)
        sustain_hits = count_hits(blob, SELF_SUSTAIN_WORDS)
        control_hits = count_hits(blob, CONTROL_WORDS)

        p_ehp = percentile(ehp_list, m["safety"])
        p_dps = percentile(dps_list, m["total_dps"])
        br = m["burst_ratio"]

        # --- tipe serangan: leksikon + ketergantungan skill ---
        mag_score = magic_hits * 3.0 + (1.5 if m["melee"] else 0.0) \
            + (2.0 if m["range"] >= 160 else 0.0) \
            + max(0.0, (br - 0.45)) * 8.0
        phys_score = phys_hits * 3.0 + (2.5 if m["melee"] else 0.0) \
            + max(0.0, (0.45 - br)) * 8.0

        # --- kelas bermain ---
        is_tank = (p_ehp >= 0.72 and br <= 0.60) or (p_ehp >= 0.86) \
            or (tank_hits >= 3 and p_ehp >= 0.60)
        is_carry = (p_dps >= 0.62 or br >= 0.58) and p_ehp < 0.80

        if is_tank:
            role_class = "TANK"
        elif is_carry:
            role_class = "CARRY"
        else:
            role_class = "FIGHTER"

        if phys_score > mag_score * 1.12:
            dmg_type = "PHYSICAL"
        elif mag_score > phys_score * 1.12:
            dmg_type = "MAGIC"
        else:
            # seri: melee -> fisik, ranged -> magic (default konvensi MOBA)
            dmg_type = "PHYSICAL" if m["melee"] else "MAGIC"

        # label 1 kata yang diminta user
        category = "TANK" if role_class == "TANK" else dmg_type

        r["_m"].update({
            "p_ehp": round(p_ehp, 3),
            "p_dps": round(p_dps, 3),
            "magic_score": round(mag_score, 2),
            "physical_score": round(phys_score, 2),
            "tank_score": tank_hits,
            "sustain_score": sustain_hits,
            "control_score": control_hits,
            "dmg_type": dmg_type,
            "role_class": role_class,
            "category": category,
            "hybrid": "HYBRID" if abs(mag_score - phys_score) <= 1.5 else "",
            "rank": round((p_dps * 0.60 + p_ehp * 0.30 + br * 0.10) * 100),
            "power": round(min(1.0, m["total_dps"] / max(p98_dps, 1)) * 82
                           + min(1.0, m["safety"] / max(p98_ehp, 1)) * 18),
        })

    # tier relatif: DPS & HP dibandingkan dengan median kelas boss-nya,
    # supaya starter (murah/gratis) dan hero unlock (mahal) dinilai adil.
    # pool pembanding: 6 starter digabung dengan 216 hero boss, supaya
    # starter (gratis) tidak otomatis "tier D" hanya karena murah.
    by_cls = {}
    for r in rows:
        by_cls.setdefault(r["boss_class"], []).append(r)
    # tiap kelas dibandingkan dengan sesamanya (starter vs starter)
    pool_map = dict(by_cls)
    for _cls, sel in pool_map.items():
        med_dps = statistics.median([x["_m"]["total_dps"] for x in sel])
        med_ehp = statistics.median([x["_m"]["safety"] for x in sel])
        for x in sel:
            x["_m"]["tier"] = _tier(x["_m"]["total_dps"] / max(med_dps, 1))
            x["_m"]["tier_hp"] = _tier(x["_m"]["safety"] / max(med_ehp, 1))
    return rows


# ─── OUTPUT ──────────────────────────────────────────────────────────────


def build(rows, reg):
    for r in rows:
        r["_m"]["name"] = r.get("name", r["hero_type"])
        r["_m"]["hero_type"] = r["hero_type"]
        r["_m"]["boss_class"] = r["boss_class"]
        r["_m"]["source_boss"] = r.get("source_boss")
        r["_m"]["registered"] = r["hero_type"] in reg
        if not r["_m"]["registered"] and r["boss_class"] != "starter":
            r["_m"]["note"] = "skill fallback generik"
    return rows


def stats_summary(rows):
    """Angka-angka temuan yang dipakai di dokumen."""
    import statistics as st
    boss = [r for r in rows if r["boss_class"] != "starter"]
    dps = [r["_m"]["total_dps"] for r in rows]
    hp = [r["_m"]["safety"] for r in rows]
    med_dps = st.median(dps)
    med_hp = st.median(hp)
    cov_dps = sum((a - med_dps) * (b - med_hp) for a, b in zip(dps, hp))
    var = (sum((a - med_dps) ** 2 for a in dps)
           * sum((b - med_hp) ** 2 for b in hp)) ** 0.5
    names = collections.Counter(r.get("name", r["hero_type"]) for r in rows)
    return {
        "n": len(rows),
        "n_boss": len(boss),
        "corr": cov_dps / max(var, 1e-9),
        "fallback": sum(1 for r in boss if not r["_m"]["registered"]),
        "dupes": sorted(k for k, v in names.items() if v > 1),
        "med_hp": round(med_hp),
        "med_dps": round(med_dps),
        "burst_hi": sum(1 for r in rows if r["_m"]["burst_ratio"] >= 0.50),
        "burst_lo": sum(1 for r in rows if r["_m"]["burst_ratio"] <= 0.25),
    }


def group_key(r):
    return (r["boss_class"], r["_m"]["category"], -r["_m"]["power"])


def md_table(rows):  # noqa: C901
    out = ["| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS "
           "| POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | "
           "Melee | Skill |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, r in enumerate(rows, 1):
        m = r["_m"]
        star = "" if m["registered"] or r["boss_class"] == "starter" else " ◦"
        out.append(
            "| %d | **%s**%s | %s | %s | %s | %s | %s | %d | %d | %.1f | "
            "%.1f | %.1f | %.0f%% | %s | %s |" % (
                n, r.get("name", r["hero_type"]), star, r["boss_class"],
                m["category"], m["dmg_type"], m["role_class"], m["tier"],
                m["power"],
                m["hp"], m["dmg"], m["basic_dps"], m["skill_dps"],
                m["burst_ratio"] * 100.0, "ya" if m["melee"] else "tidak",
                m["skill_name"]))
    return "\n".join(out)


def findings_md(rows):
    s = stats_summary(rows)
    out = ["## Cara baca 1 kata (yang ditanya)", ""]
    out.append(
        "- **PHYSICAL** — damage utamanya datang dari *basic attack* "
        "(bagian skill < 45% dari total DPS). Biasanya melee (range "
        "di-clamp ke 70) atau marksman.")
    out.append(
        "- **MAGIC** — damage utamanya *spell burst* (bagian skill >= 45% "
        "dari total DPS) dan/atau kit bertema arcane/elemental (fire, ice, "
        "void, necro, storm, dll.).")
    out.append(
        "- **TANK** — bukan tipe damage, tapi gaya main: Effective HP "
        "(HP sudah termasuk bonus melee +15% dari BALANCE PASS di "
        "_entity.py dan multiplier garis depan 1.25x) ada di persentil "
        ">= 72 dengan ketergantungan burst <= 60%. Kategori ini menyerap "
        "tipe aslinya — kolom `Tipe dmg` tetap menyimpan "
        "PHYSICAL/MAGIC-nya.")
    out.append("")
    out.append("## Temuan penting (hasil ukur dari data)")
    out.append("")
    out.append(
        "1. **Dulu engine tidak membedakan PHYSICAL vs MAGIC.** "
        "Boss hanya punya pengurangan flat — TRUE boss `damage_reduction` "
        "0.30, MINI 0.20 (`bosses/base_boss.py:382`) dan dipakai untuk "
        "semua `take_damage`. Tidak ada armor vs magic resist. Yang "
        "benar-benar punya interaksi adalah 3 hal: `damage_type='fire'` "
        "kebal armor-shred item (`base_boss.py:5142`, `_entity.py:5477`), "
        "`damage_type='projectile'` bisa dibanjiri Wind Wall Kaizen "
        "(`_entity.py:4301`), dan Mage Tower memangkas skill damage lewat "
        "`skill_down_amount` (`_entity.py:3151`).")
    out.append(
        "2. **ANTI-BURST CAP mengubah arti kategori.** TRUE boss memotong "
        "satu pukulan maksimal 8%% HP (`max_damage_per_hit`, "
        "`base_boss.py:386`), MINI 12%%. Jadi %d hero dengan burst ratio "
        ">= 50%% (skill = sebagian besar DPS-nya) paling banyak "
        "kerugiannya vs TRUE boss; %d hero burst <= 25%% (mesin multi-hit) "
        "justru paling efisien." % (s["burst_hi"], s["burst_lo"]))
    out.append(
        "3. **Korelasi HP vs DPS = %.2f.** Setelah `_normalize_hero_"
        "unlock_stats()` (monotonic running-max per stat), hero mahal "
        "hampir selalu menang di DUA stat sekaligus - tidak ada trade-off "
        "archetype. Efeknya: kategori TANK berisi hero top-tier "
        "(median EHP %d vs DPS median %d adalah pool yang sama), bukan "
        "hero murah yang kuat di badan." % (s["corr"], s["med_hp"],
                                            s["med_dps"]))
    out.append(
        "4. **%d dari %d hero boss tidak punya skill sendiri.** "
        "`_SKILL_REGISTRY` di `hero_skills/_bundle.py:458` hanya berisi 64 "
        "entri; sisanya masuk `_fallback_cast` (damage generik, Q 1.0x / "
        "W 1.2x / E 1.5x / R 2.5x). Artinya label MAGIC untuk hero-hero itu "
        "masih cosmetic: di lapangan skill mereka hanya angka." % (
            s["fallback"], s["n_boss"]))
    out.append("")
    out.append("## Implementasi v1 (AKTIF di engine)")
    out.append("")
    out.append("Kategori tidak lagi jadi dokumen mati - datanya dipakai "
               "runtime:")
    out.append("")
    out.append("| Berkas | Peran |")
    out.append("|---|---|")
    out.append("| `hero_archetypes.py` | tabel `hero_type -> "
               "{dmg_type, playstyle, tier, power}`; file ini yang dibaca "
               "engine. Regenerate lewat tool ini |")
    out.append("| `hero_archetypes.json` | versi data mentah (untuk "
               "tools/UI eksternal) |")
    out.append("| `_entity.py` | `Hero.dmg_school`, "
               "`resolve_damage_school()`, `Bullet` & proyektil hero "
               "membawa `school`, mitigasi di `Tower`/`Minion` |")
    out.append("| `bosses/base_boss.py` | `armor` (12 mini / 18 true) & "
               "`magic_resist` (0.10 / 0.20) + penerapannya di "
               "`Boss.take_damage` |")
    out.append("| `_core.py` | chip PHY/MAG/TNK di kartu Hero Shop + "
               "legenda di header tab |")
    out.append("| `tools/test_damage_school.py` | 36 assert: mitigasi per "
               "sekolah, paritas Wind Wall/Windrun/fire, fallback "
               "arketype |")
    out.append("")
    out.append("Rumus mitigasi (semua di atas `damage_reduction` bawaan, "
               "di bawah anti-burst cap):")
    out.append("")
    out.append("```")
    out.append("physical: dmg * (1 - armor*0.06/(1 + armor*0.06))   # 12 "
               "armor = -42%, 18 = -52%")
    out.append("magic   : dmg * (1 - magic_resist)                  # 10% "
               "/ 20%")
    out.append("```")
    out.append("")
    out.append(
        "Override: tambah kunci `dmg_type` (`PHYSICAL` / `MAGIC`) di "
        "`hero_unlock` boss di `bosses/boss_data.py` - menang atas tabel. "
        "Override ketahanan boss: kunci `armor` / `magic_resist` di entri "
        "boss (golem armor tinggi, mage boss MR tinggi).")
    out.append("")
    out.append(
        "Test regresi: `python3 tools/test_damage_school.py` (36 assert) "
        "dan `python3 tools/test_damage_school_integration.py` (400 frame "
        "Game sungguhan: 2 hero + mini boss).")
    out.append("")
    out.append("TODO v2 (sengaja belum dikerjakan):")
    out.append("")
    out.append("1. %d hero boss belum punya recipe skill khusus - sekolah "
               "damage baru terasa di basic attack, belum di skill "
               "uniknya." % s["fallback"])
    out.append("2. Basic attack boss diberi `school=physical` supaya item "
               "armor berguna; ability boss masih `None` (perilaku lama).")
    out.append("3. Peluru Mage Tower sengaja masih dihitung FISIK "
               "(paritas lama) supaya item armor tidak kehilangan nilai "
               "sekaligus.")
    out.append("4. Skill bertema api (Dragon Breath, Flux, dll.) belum "
               "di-flag `fire`, jadi belum kebal armor-shred.")
    if s["dupes"]:
        out.append(
            "5. **Nama hero tabrakan:** %s. Kalau dipakai di UI/ledger, "
            "pakailah `hero_type` (key), bukan `name`." % ", ".join(
                "`%s`" % d for d in s["dupes"]))
    out.append("")
    return out


def picks_md(rows):
    out = ["## Rekomendasi per lawanan", ""]
    out.append("| Situasi | Pilihan terbaik | Kenapa (dari data) |")
    out.append("|---|---|---|")
    for cls in ("mini", "true"):
        sel = sorted([r for r in rows if r["boss_class"] == cls],
                     key=lambda r: -r["_m"]["total_dps"])
        lo = [r for r in sel if r["_m"]["burst_ratio"] <= 0.35][:6]
        hi = [r for r in sel if r["_m"]["burst_ratio"] >= 0.48][:6]
        nm = lambda a: ", ".join(
            "%s·%s" % (r.get("name", r["hero_type"]),
                       r["_m"]["category"][:3]) for r in a) or "-"
        cap = "8" if cls == "true" else "12"
        out.append("| **%s boss** — cap %s%% HP/pukul | %s | DPS multi-hit, "
                   "burst rendah: jarang kepotong cap |" % (
                       "MINI" if cls == "mini" else "TRUE", cap, nm(lo)))
        out.append("| %s boss — hero burst tinggi (paling terbuang) | %s | "
                   "lebih dari separuh DPS-nya di-cap, hindari kalau butuh "
                   "kill cepat |" % ("MINI" if cls == "mini" else "TRUE",
                                     nm(hi)))
    tank = sorted([r for r in rows if r["_m"]["category"] == "TANK"],
                  key=lambda r: -r["_m"]["safety"])[:6]
    squish = sorted([r for r in rows if r["_m"]["p_ehp"] <= 0.35],
                    key=lambda r: -r["_m"]["total_dps"])[:6]
    nm = lambda a: ", ".join(r.get("name", r["hero_type"]) for r in a)
    out.append("| Dinding untuk menahan aggro | %s | EHP tertinggi; melee "
               "TANK sudah dapat bonus runtime +15%% HP, +20%% dmg, +18%% "
               "speed |" % nm(tank))
    out.append("| Damage murah per HP (EHP < median) | %s | DPS tinggi "
               "dengan badan tipis - rawan, butuh tower di belakangnya |"
               % nm(squish))
    out.append("")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--md")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--emit-module", default="hero_archetypes.py",
                    help="tulis ulang dict ARCHETYPES di modul game "
                         "(dipakai engine untuk damage school)")
    ap.add_argument("--emit-json",
                    help="tulis tabel kategori ke file JSON")
    ap.add_argument("--emit-boss-res", action="store_true",
                    help="kalibrasi armor/magic_resist tiap boss "
                         "(hero_archetypes.BOSS_RESISTANCES)")
    args = ap.parse_args()

    rows = load_heroes()
    reg = registered_heroes()
    for r in rows:
        r["_m"] = metrics(r)
    classify(rows)
    build(rows, reg)

    import collections
    by_cat = collections.Counter(r["_m"]["category"] for r in rows)
    by_type = collections.Counter(r["_m"]["dmg_type"] for r in rows)
    by_class = collections.Counter(r["_m"]["role_class"] for r in rows)
    by_bc = collections.Counter(
        (r["boss_class"], r["_m"]["category"]) for r in rows)
    unreg = [r for r in rows
             if r["boss_class"] != "starter" and not r["_m"]["registered"]]

    if not args.quiet:
        print("Total hero playable: %d (starter %d, mini boss %d, "
              "true boss %d)" % (
                  len(rows),
                  sum(1 for r in rows if r["boss_class"] == "starter"),
                  sum(1 for r in rows if r["boss_class"] == "mini"),
                  sum(1 for r in rows if r["boss_class"] == "true")))
        print("\nKategori :", dict(by_cat))
        print("Tipe     :", dict(by_type))
        print("Gaya      :", dict(by_class))
        print("\nPer kelas boss:")
        for cls in ("starter", "mini", "true"):
            line = {c: by_bc.get((cls, c), 0)
                    for c in ("PHYSICAL", "MAGIC", "TANK")}
            print("  %-8s %s" % (cls, line))
        print("\nHero tanpa recipe skill khusus (pakai fallback generik): "
              "%d/%d" % (len(unreg), sum(
                  1 for r in rows if r["boss_class"] != "starter")))
        for title, key in (("PHYSICAL", "PHYSICAL"), ("MAGIC", "MAGIC"),
                           ("TANK", "TANK")):
            top = sorted([r for r in rows if r["_m"]["category"] == key],
                         key=lambda r: -r["_m"]["power"])[:12]
            print("\nTop %s (power, nama·kelas·role):" % title)
            for r in top:
                m = r["_m"]
                print("   %-20s %-8s %-9s pow=%-3d HP=%-5s DPS=%-6.1f "
                      "burst=%-3.0f%% %s" % (
                          r.get("name", r["hero_type"]), r["boss_class"],
                          m["role_class"], m["power"], m["hp"],
                          m["total_dps"], m["burst_ratio"] * 100.0,
                          m["role"].replace("Boss/", "").replace(
                              "True Boss/", "TRUE: ")))

    if args.emit_boss_res:
        # ── armor/magic_resist tiap boss + skala/modifier ternormalisasi ──
        import importlib.util
        _mod_path = args.emit_module or "hero_archetypes.py"
        if not os.path.isabs(_mod_path):
            _mod_path = os.path.join(REPO, _mod_path)
        _spec = importlib.util.spec_from_file_location(
            "hero_balance", os.path.join(REPO, "hero_balance.py"))
        hb = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(hb)
        res_rows = [{
            "boss_type": r["hero_type"],
            "boss_class": r["boss_class"],
            "profile": resist_profile(r),
            "dmg_type": r["_m"]["dmg_type"],
            "dps": r["_m"]["total_dps"],
        } for r in rows if r["boss_class"] != "starter"]
        table, rep = hb.calibrate_boss_resistances(res_rows)

        # 1) tabel per boss
        lines = []
        for k in sorted(table):
            v = table[k]
            lines.append('    "%s": {"armor": %d, "magic_resist": %.3f, '
                         '"profile": "%s", "boss_class": "%s"},' % (
                             k, v["armor"], v["magic_resist"],
                             v["profile"], v["boss_class"]))
        src2 = open(_mod_path, encoding="utf-8").read()
        mk = "BOSS_RESISTANCES = {"
        st = src2.index(mk)
        he = st + len(mk)
        # penutup = "}" pada kolom 0 pertama sesudah marker (entri dict
        # selalu indent > 0, jadi tidak pernah salah potong)
        en = src2.index("\n}", he) + 2
        src2 = (src2[:st] + "BOSS_RESISTANCES = {\n"
                + "\n".join(lines) + "\n}" + src2[en:])

        # 2) modifier TIDAK ditulis ulang - itu desain dasar manual
        #    (BOSS_RESIST_PROFILE_MODS). Yang dibekukan cuma tabel per
        #    boss di atas, supaya tools/ tidak bisa melumpuhkan variasinya
        #    kalau dijalankan dua kali.
        # 3) skala hasil kalibrasi
        lines2 = []
        for dc in ("mini", "true"):
            if dc not in rep:
                continue
            sc = rep[dc]["scale"]
            lines2.append('    "%s": {"armor": %.4f, "mr": %.4f},' % (
                dc, sc["armor"], sc["mr"]))
        st4 = src2.index("BOSS_RESIST_SCALE = {")
        en4 = src2.index("\n}", st4 + len("BOSS_RESIST_SCALE = {")) + 2
        src2 = (src2[:st4] + "BOSS_RESIST_SCALE = {\n" + "\n".join(lines2)
                + "\n}" + src2[en4:])
        open(_mod_path, "w", encoding="utf-8").write(src2)
        boss_res_payload = {"report": rep, "boss_resistances": table}
        print("BOSS-RES -> %d boss; parity magic/fisik %s" % (
            len(table), {k: rep[k]["magic_over_phys"] for k in ("mini", "true")
                         if k in rep}))

    if args.emit_json:
        payload = {  # noqa: E999
            "meta": {
                "generated_by": "tools/analyze_hero_archetypes.py",
                "total_hero": len(rows),
                "counts": dict(by_cat),
                "note": "dmg_type menentukan mitigasi (armor vs magic "
                        "resist); playstyle hanya label UI.",
            },
            "heroes": {
                r["hero_type"]: {
                    "name": r.get("name", r["hero_type"]),
                    "boss_class": r["boss_class"],
                    "role": r["_m"]["role"],
                    "dmg_type": r["_m"]["dmg_type"],
                    "category": r["_m"]["category"],
                    "playstyle": r["_m"]["role_class"],
                    "tier": r["_m"]["tier"],
                    "power": r["_m"]["power"],
                    "hp": r["_m"]["hp"],
                    "total_dps": r["_m"]["total_dps"],
                    "burst_ratio": r["_m"]["burst_ratio"],
                    "melee": r["_m"]["melee"],
                    "custom_skill": r["_m"]["registered"],
                } for r in rows
            },
        }
        if args.emit_boss_res:
            payload["boss_resistances"] = boss_res_payload["boss_resistances"]
            payload["meta"]["boss_resist_report"] = boss_res_payload["report"]
        with open(args.emit_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False,
                      sort_keys=True)
        print("JSON -> %s" % args.emit_json)

    if args.emit_module:
        lines = []
        for r in sorted(rows, key=lambda r: (r["boss_class"],
                                             r["hero_type"])):
            m = r["_m"]
            lines.append('    "%s": {"dmg_type": "%s", "playstyle": "%s", '
                         '"tier": "%s", "power": %d},' % (
                             r["hero_type"], m["dmg_type"], m["role_class"],
                             m["tier"], m["power"]))
        body = "\n".join(lines)
        path = _mod_path if args.emit_boss_res else args.emit_module
        if not os.path.isabs(path):
            path = os.path.join(REPO, path)
        src = open(path, encoding="utf-8").read()
        mk = "ARCHETYPES = {"
        start = src.index(mk)
        # Penutup = "}" di kolom 0 PERTAMA sesudah marker. Baris entri
        # selalu ber-indent, dan di bawah ARCHETYPES ada konstanta dict
# lain - memotong dengan index("}") atau "\n}\n" pernah
        # menghapus separuh modul.
        end = src.index("\n}", start + len(mk)) + 2
        src = (src[:start] + "ARCHETYPES = {\n%s\n}" % body + src[end:])
        open(path, "w", encoding="utf-8").write(src)
        print("MODULE -> %s (%d hero)" % (path, len(rows)))

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["hero", "hero_type", "boss_class", "role",
                        "category", "damage_type", "playstyle", "hybrid",
                        "rank", "hp_eff", "damage_eff", "range", "melee",
                        "basic_dps", "skill_dps", "total_dps", "burst_ratio",
                        "pct_ehp", "pct_dps", "power", "tier_dps",
                        "tier_hp", "magic_score",
                        "physical_score", "tank_kw", "sustain_kw",
                        "control_kw", "skill_name", "custom_skill_recipe",
                        "source_boss"])
            for r in sorted(rows, key=group_key):
                m = r["_m"]
                w.writerow([r.get("name", r["hero_type"]), r["hero_type"],
                            r["boss_class"], m["role"], m["category"],
                            m["dmg_type"], m["role_class"], m["hybrid"],
                            m["rank"], m["hp"], m["dmg"], m["range"],
                            int(m["melee"]), m["basic_dps"], m["skill_dps"],
                            m["total_dps"], m["burst_ratio"], m["p_ehp"],
                            m["p_dps"], m["power"], m["tier"], m["tier_hp"],
                            m["magic_score"],
                            m["physical_score"], m["tank_score"],
                            m["sustain_score"], m["control_score"],
                            m["skill_name"], int(m["registered"]),
                            r.get("source_boss") or ""])
        print("\nCSV -> %s" % args.csv)

    if args.md:
        lines = ["# Kategori Hero Mystic Arena — PHYSICAL / MAGIC / TANK", ""]
        lines.append("Dibuat otomatis oleh `tools/analyze_hero_archetypes.py` "
                     "dari data hero di repo (tidak ada angka karangan).")
        lines.append("")
        lines.append("> `Tier DPS` = DPS total hero dibanding median "
                     "sesama kelas boss-nya (S >= 1.45x, A >= 1.20x, "
                     "B >= 0.90x, C >= 0.65x, D < 0.65x). `POWER` = skor "
                     "absolut 82% DPS + 18% EHP terhadap p98 pool "
                     "(starter & hero murah otomatis kecil). `Burst` = "
                     "porsi DPS yang datang dari skill - makin besar, "
                     "makin sering kepotong cap anti-burst boss.")
        lines.append("")
        lines.append("## Ringkasan")
        lines.append("")
        lines.append("| Kelas boss | PHYSICAL | MAGIC | TANK | Total |")
        lines.append("|---|---|---|---|---|")
        for cls, label in (("starter", "Starter"),
                           ("mini", "MINI BOSS"), ("true", "TRUE BOSS")):
            n = sum(1 for r in rows if r["boss_class"] == cls)
            lines.append("| %s | %d | %d | %d | %d |" % (
                label,
                by_bc.get((cls, "PHYSICAL"), 0),
                by_bc.get((cls, "MAGIC"), 0),
                by_bc.get((cls, "TANK"), 0), n))
        lines.append("| **TOTAL** | %d | %d | %d | %d |" % (
            by_cat["PHYSICAL"], by_cat["MAGIC"], by_cat["TANK"], len(rows)))
        lines.append("")
        lines += findings_md(rows)
        lines += picks_md(rows)
        lines.append("")
        for cls, label in (("starter", "Starter Hero"),
                           ("mini", "MINI BOSS"), ("true", "TRUE BOSS")):
            lines.append("## %s" % label)
            lines.append("")
            for cat in ("PHYSICAL", "MAGIC", "TANK"):
                sel = sorted([r for r in rows
                              if r["boss_class"] == cls
                              and r["_m"]["category"] == cat],
                             key=lambda r: -r["_m"]["power"])
                if not sel:
                    continue
                lines.append("### %s (%d)" % (cat, len(sel)))
                lines.append("")
                lines.append(md_table(sel))
                lines.append("")
        lines.append("◦ = hero unlock yang belum punya recipe skill khusus "
                     "(skill-nya masih `_fallback_cast` generik di "
                     "`hero_skills/_bundle.py`).")
        with open(args.md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("MD  -> %s" % args.md)


if __name__ == "__main__":
    main()
