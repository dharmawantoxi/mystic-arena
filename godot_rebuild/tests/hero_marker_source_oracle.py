"""9aj: golden arena silhouettes for the whole 222 hero roster.

`ui_components/hero_portraits.py` is missing from the repository, so the arena
art is procedural. `hero_marker.gd::silhouette()` is the readable outline the
prototype view draws (`scenes/prototype/prototype_view.gd:619`), and its generic
branch used to wobble on `(code >> (index % 12)) % 5`: only bits 0-9 of a code
below 1000003, which made 33 pairs of the 220 generic heroes share one figure
(`gravefang`/`hitokage`, `kaerinya`/`kyumirra`, ...).

This oracle mirrors the marker algorithm (fingerprint, Kaizen/Thorne outlines,
the generic base-5 spread) and writes a golden fixture: per hero the vertex
count and a hash of the vertices quantised to 1e-4. The GDScript suite recomputes
the same hashes from the production `silhouette()`, so any accidental change to
the roster art drifts the fixture. The hash granularity is coarse on purpose:
`cos`/`sin` may differ in the last bit between the Python oracle and Godot, and
quantising at 1e-4 keeps that from becoming a false alarm while a real shape
change still moves every vertex. `--write` rewrites the fixture.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_marker_source.json"
ROSTER = ROOT / "godot_rebuild" / "data" / "ai" / "hero_combat_stats.json"

QUANTUM = 10000.0
MAX_REACH = 1.2

KAIZEN_OUTLINE = [
    (0.0, -1.15),
    (0.42, -0.55),
    (0.55, 0.15),
    (0.30, 0.90),
    (0.0, 1.15),
    (-0.30, 0.90),
    (-0.55, 0.15),
    (-0.42, -0.55),
]
THORNE_OUTLINE = [
    (0.0, -1.10),
    (0.50, -0.85),
    (0.85, -0.35),
    (1.00, 0.10),
    (0.80, 0.70),
    (0.35, 1.10),
    (0.0, 1.00),
    (-0.35, 1.10),
    (-0.80, 0.70),
    (-1.00, 0.10),
    (-0.85, -0.35),
    (-0.50, -0.85),
]


def fingerprint(hero_type: str) -> int:
    value = 0
    for character in hero_type:
        value = (value * 31 + ord(character)) % 1000003
    return value


def outline(hero_type: str):
    """Unit-space silhouette vertices, `point` at the origin and `radius` 1."""
    if hero_type == "kaizen":
        return list(KAIZEN_OUTLINE), "kaizen"
    if hero_type == "thorne":
        return list(THORNE_OUTLINE), "thorne"
    spread = fingerprint(hero_type) * 48271 + 1021
    sides = 7 + spread % 4
    vertices = []
    divisor = 1
    for index in range(sides):
        angle = -math.pi / 2.0 + math.tau * float(index) / float(sides)
        wobble = float((spread // divisor) % 5 - 2) * 0.06
        vertices.append((math.cos(angle) * (1.0 + wobble), math.sin(angle) * (1.0 + wobble)))
        divisor *= 5
    return vertices, "generic"


def _quantised(vertices):
    return [
        (
            math.floor(x * QUANTUM + 0.5),
            math.floor(y * QUANTUM + 0.5),
        )
        for x, y in vertices
    ]


def _hash(values) -> int:
    digest = 0
    for value in values:
        digest = (digest * 31 + (value % 1000003)) % 1000003
    return digest


def _entry(hero_type: str) -> dict:
    vertices, family = outline(hero_type)
    quantised = _quantised(vertices)
    reach = max(math.hypot(x, y) for x, y in vertices)
    return {
        "family": family,
        "sides": len(vertices),
        "x_hash": _hash([x for x, _ in quantised]),
        "y_hash": _hash([y for _, y in quantised]),
        "reach_milli": int(round(reach * 1000.0)),
    }


def source_fixture():
    roster = sorted(json.loads(ROSTER.read_text(encoding="utf-8")))
    entries = {hero_type: _entry(hero_type) for hero_type in roster}
    keys = {(entry["sides"], entry["x_hash"], entry["y_hash"]) for entry in entries.values()}
    families = {}
    for entry in entries.values():
        families[entry["family"]] = families.get(entry["family"], 0) + 1
    return {
        "source": "procedural: `godot_rebuild/scripts/ui/hero_marker.gd::silhouette`",
        "callsite": "godot_rebuild/scenes/prototype/prototype_view.gd::_draw_hero",
        "quantum": int(QUANTUM),
        "shape": {
            "roster": len(roster),
            "distinct_outlines": len(keys),
            "collisions": len(roster) - len(keys),
            "families": {key: families[key] for key in sorted(families)},
            "sides": sorted({entry["sides"] for entry in entries.values()}),
            "max_reach_milli": max(entry["reach_milli"] for entry in entries.values()),
            "min_reach_milli": min(entry["reach_milli"] for entry in entries.values()),
            "generic_reach_milli": sorted(
                {entry["reach_milli"] for entry in entries.values() if entry["family"] == "generic"}
            )[-1],
            "digest": hashlib.sha256(
                json.dumps(entries, sort_keys=True).encode("utf-8")
            ).hexdigest()[:16],
        },
        "roster": entries,
    }


def _self_test(fixture):
    problems = []
    shape = fixture["shape"]
    if shape["roster"] != 222:
        problems.append("roster drifted: %d entries" % shape["roster"])
    if shape["distinct_outlines"] != shape["roster"] or shape["collisions"] != 0:
        problems.append(
            "silhouette collisions came back: %d distinct of %d"
            % (shape["distinct_outlines"], shape["roster"])
        )
    if shape["families"] != {"generic": 220, "kaizen": 1, "thorne": 1}:
        problems.append("family split drifted: %s" % shape["families"])
    if shape["sides"] != [7, 8, 9, 10, 12]:
        problems.append("vertex counts drifted: %s" % shape["sides"])
    if shape["max_reach_milli"] > int(MAX_REACH * 1000):
        problems.append("a silhouette leaves the team ring: %d" % shape["max_reach_milli"])
    if shape["generic_reach_milli"] < 1000:
        problems.append("a generic silhouette shrank below its radius")
    kaizen = fixture["roster"]["kaizen"]
    thorne = fixture["roster"]["thorne"]
    if kaizen["sides"] != 8 or thorne["sides"] != 12:
        problems.append("starter outlines drifted: %d/%d" % (kaizen["sides"], thorne["sides"]))
    if kaizen["reach_milli"] != 1150:
        problems.append("Kaizen reach drifted: %d" % kaizen["reach_milli"])
    if problems:
        for problem in problems:
            print("FAIL: %s" % problem)
        return 1
    print(
        "hero marker oracle self-test passed: %d heroes, %d distinct outlines, max reach %d/1000"
        % (shape["roster"], shape["distinct_outlines"], shape["max_reach_milli"])
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fixture = source_fixture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
        print("wrote %s (%d heroes)" % (FIXTURE.name, len(fixture["roster"])))
        return 0
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture != committed:
        print("FAIL: fixture drift vs %s" % FIXTURE.name)
        return 1
    return _self_test(fixture)


if __name__ == "__main__":
    raise SystemExit(main())
