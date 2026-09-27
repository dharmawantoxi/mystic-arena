"""Keep the handoff manifest honest against source recipes and native registry."""
import ast
import json
import re


def validate_manifest(root, check):
    manifest = json.loads((root / "data/ai/hero_migration_status.json").read_text())
    catalog = json.loads((root / "data/ai/recruitment.json").read_text())["catalog"]
    native = set(re.findall(r'"([a-z0-9_]+)": preload',
                            (root / "scripts/data/hero_roster.gd").read_text()))
    heroes = manifest["heroes"]
    done = {key for key, value in heroes.items() if value["status"] == "playable"}
    pending = {key for key, value in heroes.items() if value["status"] == "pending"}
    check(set(heroes) == set(catalog), "Manifest covers exactly all source roster IDs")
    check(done == native, "Manifest playable list equals explicit native registry")
    check(done.isdisjoint(pending) and done | pending == set(catalog), "No ambiguous hero status")
    check(manifest["target"] == len(catalog) == 222, "Do not silently reduce 222 hero target")
    check(manifest["playable"] == len(done) and manifest["pending"] == len(pending),
          "Handoff remaining count equals exact ID lists")
    tree = ast.parse((root.parent / "hero_skills/_bundle.py").read_text())
    cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "BossHeroSkills")
    recipes = ast.literal_eval(next(n.value for n in cls.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "_SKILL_REGISTRY" for t in n.targets)))
    for kind, entry in heroes.items():
        check(entry["summon_cost"] == catalog[kind]["cost"], f"Manifest price: {kind}")
        if kind in done:
            for folder, key in (("scripts/combat", "native_handler"), ("tests", "oracle"),
                                ("tests", "native_test")):
                check(bool(entry[key]) and (root / folder / entry[key]).is_file(),
                      f"Playable hero needs handler/oracle/native suite: {kind} {key}")
            check(entry["blocker"] is None, f"No unfinished playable hero: {kind}")
        else:
            check(entry["source_recipe"] == recipes.get(kind), f"Pending exact source recipe: {kind}")
            check(bool(entry["blocker"]) and entry["native_handler"] is None
                  and entry["oracle"] is None and entry["native_test"] is None,
                  f"Pending implementation/testing blocker explicit: {kind}")
