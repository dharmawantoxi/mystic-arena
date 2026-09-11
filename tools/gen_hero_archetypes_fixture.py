#!/usr/bin/env python3
"""gen_hero_archetypes_fixture — oracle pygame untuk HeroArchetypesParityTest.

Menjalankan helper ASLI hero_archetypes.py (get_archetype, school_of,
get_boss_resistances, _resist_from_profile, physical_mitigation) pada
seluruh katalog + kasus tepi (override dmg_type, hero tak dikenal, boss
tak dikenal, semua profil x kelas) dan menulis hasilnya ke

    godot/tests/fixtures/hero_archetypes.json

yang direplay godot/tests/HeroArchetypesParityTest.gd terhadap
godot/scripts/core/HeroArchetypes.gd. Modul ini sengaja TIDAK butuh pygame
(hero_archetypes.py juga tidak), jadi bisa jalan di CI langkah statis.

Jalankan:   python3 tools/gen_hero_archetypes_fixture.py
Cek saja:   python3 tools/gen_hero_archetypes_fixture.py --check
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import hero_archetypes as ha  # noqa: E402

OUT = os.path.join(ROOT, "godot", "tests", "fixtures", "hero_archetypes.json")

# stats override yang dites di get_archetype (mirip kunci hero_unlock)
OVERRIDE_CASES = [
    {},                              # tanpa stats
    {"dmg_type": "MAGIC"},
    {"dmg_type": "physical"},        # case-insensitive
    {"dmg_type": "fire"},            # tidak valid -> DEFAULT_DMG_TYPE
    {"dmg_type": ""},                # falsy -> tidak dianggap override
    {"dmg_type": None},              # None -> tidak dianggap override
    {"hp": 1},                       # stats tanpa dmg_type
]
UNKNOWN_HEROES = ["__tidak_ada__", "boss_baru_x"]
UNKNOWN_BOSSES = ["__tidak_ada__", "boss_baru_x"]


def build():
    heroes = sorted(ha.ARCHETYPES) + UNKNOWN_HEROES
    arche = []
    for ht in heroes:
        for i, st in enumerate(OVERRIDE_CASES):
            entry = ha.get_archetype(ht, st)
            arche.append({
                "hero": ht,
                "case": i,
                "stats": {k: v for k, v in st.items()},
                "dmg_type": entry["dmg_type"],
                "playstyle": entry.get("playstyle", "FIGHTER"),
                "tier": entry.get("tier", ""),
                "power": int(entry.get("power", 0)),
                "derived": bool(entry.get("derived", False)),
                "school": ha.school_of(ht, st),
            })
    res = []
    for bt in sorted(ha.BOSS_RESISTANCES) + UNKNOWN_BOSSES:
        for cls in ("mini", "true"):
            armor, mr = ha.get_boss_resistances(bt, cls)
            res.append({"boss": bt, "boss_class": cls,
                        "armor": int(armor), "magic_resist": float(mr)})
    prof = []
    for p in sorted(ha.BOSS_RESIST_PROFILE_MODS) + ["__unknown__"]:
        for cls in ("mini", "true", "__unknown__"):
            sc = ha.BOSS_RESIST_SCALE.get(cls, {})
            a, m = ha._resist_from_profile(
                p, cls, armor_scale=sc.get("armor", 1.0),
                mr_scale=sc.get("mr", 1.0))
            a1, m1 = ha._resist_from_profile(p, cls)
            prof.append({"profile": p, "boss_class": cls,
                         "scaled": [int(a), float(m)],
                         "raw": [int(a1), float(m1)]})
    mit = [{"armor": a, "mult": ha.physical_mitigation(a)}
           for a in [-5, 0, 1, 8, 10, 12, 13, 17, 18, 19, 23, 26, 32, 40, 55]]
    return {
        "constants": {
            "ARMOR_FACTOR": ha.ARMOR_FACTOR,
            "ARMOR_MAX": ha.ARMOR_MAX,
            "MR_MAX": ha.MR_MAX,
            "DEFAULT_DMG_TYPE": ha.DEFAULT_DMG_TYPE,
            "BOSS_RESIST_TARGET_RATIO": ha.BOSS_RESIST_TARGET_RATIO,
            "BOSS_RESIST_BASE": {k: list(v) for k, v in ha.BOSS_RESIST_BASE.items()},
            "BOSS_RESIST_PROFILE_MODS": {k: list(v) for k, v in ha.BOSS_RESIST_PROFILE_MODS.items()},
            "BOSS_RESIST_SCALE": ha.BOSS_RESIST_SCALE,
        },
        "archetype_count": len(ha.ARCHETYPES),
        "boss_resist_count": len(ha.BOSS_RESISTANCES),
        "archetypes": arche,
        "boss_resistances": res,
        "profiles": prof,
        "mitigation": mit,
    }


def main(argv):
    data = build()
    text = json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if "--check" in argv:
        if not os.path.exists(OUT):
            print(f"[fixture] {OUT} belum ada — jalankan tanpa --check")
            return 1
        cur = open(OUT, encoding="utf-8").read()
        if cur != text:
            print("[fixture] hero_archetypes.json USANG — regenerasi: "
                  "python3 tools/gen_hero_archetypes_fixture.py")
            return 1
        print("[fixture] hero_archetypes.json mutakhir")
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[fixture] {len(data['archetypes'])} kasus arketipe, "
          f"{len(data['boss_resistances'])} resistansi, "
          f"{len(data['profiles'])} profil -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
