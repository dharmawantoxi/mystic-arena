"""Render the HERO_ROSTER_STATUS tables straight from the machine manifest.

The exact done/pending lists are generated, never hand-typed, so the handoff
document cannot drift away from hero_migration_status.json or the native
registry. Run with --write after every batch.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "HERO_ROSTER_STATUS.md"
MANIFEST = ROOT / "data/ai/hero_migration_status.json"
DONE_OPEN = "<!-- roster:done -->"
DONE_CLOSE = "<!-- /roster:done -->"
PENDING_OPEN = "<!-- roster:pending -->"
PENDING_CLOSE = "<!-- /roster:pending -->"

RECIPE_HEADERS = ("## Selesai — {count} ID", "## Belum selesai — {count} ID dan recipe yang menjadi blocker")
TITLE = "# Daftar tepat migrasi hero — {done} playable, {pending} pending"
TITLE_PATTERN = re.compile(r"^# Daftar tepat migrasi hero — .*$", re.M)


def load():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    heroes = manifest["heroes"]
    done = [k for k, v in heroes.items() if v["status"] == "playable"]
    pending = [k for k, v in heroes.items() if v["status"] != "playable"]
    order = lambda ids: sorted(ids, key=lambda k: (heroes[k]["source_level"], k))
    return manifest, heroes, order(done), order(pending)


def done_table(heroes, ids):
    lines = ["| ID | Level sumber (0=starter) | Summon G | Handler native | Oracle + tes native |",
             "|---|---:|---:|---|---|"]
    for kind in ids:
        entry = heroes[kind]
        lines.append(f'| `{kind}` | {entry["source_level"]} | {entry["summon_cost"]} | '
                     f'`{entry["native_handler"]}` | `{entry["oracle"]}` / `{entry["native_test"]}` |')
    return "\n".join(lines)


def pending_table(heroes, ids):
    lines = ["| ID | Level sumber | Summon G | Metode Q / W / E / R sumber yang belum diport & diuji |",
             "|---|---:|---:|---|"]
    for kind in ids:
        entry = heroes[kind]
        recipe = " / ".join(f'`{entry["source_recipe"][k]}`' for k in "qwer")
        lines.append(f'| `{kind}` | {entry["source_level"]} | {entry["summon_cost"]} | {recipe} |')
    return "\n".join(lines)


def _swap(text, opener, closer, body):
    pattern = re.compile(re.escape(opener) + r".*?" + re.escape(closer), re.S)
    assert pattern.search(text), f"Missing roster marker: {opener}"
    return pattern.sub(opener + "\n" + body + "\n" + closer, text, count=1)


def _counts(text, done, pending):
    text = TITLE_PATTERN.sub(TITLE.format(done=len(done), pending=len(pending)), text, count=1)
    for header, ids in ((RECIPE_HEADERS[0], done), (RECIPE_HEADERS[1], pending)):
        for drift in (-1, 1):
            text = text.replace(header.format(count=len(ids) + drift),
                                header.format(count=len(ids)), 1)
    return text


def render(text, heroes, done, pending):
    text = _swap(text, DONE_OPEN, DONE_CLOSE, done_table(heroes, done))
    text = _swap(text, PENDING_OPEN, PENDING_CLOSE, pending_table(heroes, pending))
    return _counts(text, done, pending)


def validate(check):
    manifest, heroes, done, pending = load()
    text = DOC.read_text(encoding="utf-8")
    check(TITLE_PATTERN.search(text).group(0) == TITLE.format(done=len(done), pending=len(pending)),
          "Roster doc title count")
    check(f"## Selesai — {len(done)} ID" in text, "Roster doc done header count")
    check(f"## Belum selesai — {len(pending)} ID" in text, "Roster doc pending header count")
    for ids, opener, closer, build in (
        (done, DONE_OPEN, DONE_CLOSE, done_table),
        (pending, PENDING_OPEN, PENDING_CLOSE, pending_table),
    ):
        block = re.search(re.escape(opener) + r".*?" + re.escape(closer), text, re.S)
        check(block is not None, f"Roster doc marker: {opener}")
        if block is not None:
            expected = opener + "\n" + build(heroes, ids) + "\n" + closer
            check(block.group(0) == expected,
                  f"Roster doc table is generated from the manifest: {opener}")


if __name__ == "__main__":
    manifest, heroes, done, pending = load()
    if "--write" in sys.argv:
        DOC.write_text(render(DOC.read_text(encoding="utf-8"), heroes, done, pending),
                       encoding="utf-8")
        print(f"wrote {DOC} ({len(done)} done / {len(pending)} pending)")
    else:
        errors = []
        validate(lambda ok, message: None if ok else errors.append(message))
        assert not errors, errors
        print(f"PASS: roster doc matches the manifest ({len(done)} done / {len(pending)} pending)")
