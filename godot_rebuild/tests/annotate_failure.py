"""Surface concise native engine diagnostics in Checks, even if log download fails."""
from pathlib import Path
import re
import sys

ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
DIAGNOSTIC = re.compile(r"SCRIPT ERROR|ERROR:|Parse Error|FAIL:|CRASH", re.IGNORECASE)
# The engine prints the offending script location on the line(s) after an error,
# for example "   at: _draw (res://scenes/prototype/prototype_view.gd:412)".
LOCATION = re.compile(r"^\s+at: ")
raw_lines = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
rows = []
for raw in raw_lines:
    clean = ANSI_ESCAPE.sub("", raw).replace("\r", "").strip()
    if clean:
        rows.append((raw.replace("\r", ""), clean))
selected: list[str] = []
for index, (_raw, clean) in enumerate(rows):
    if not DIAGNOSTIC.search(clean):
        continue
    selected.append(clean)
    for offset in range(1, 3):
        if index + offset >= len(rows):
            break
        raw_next, clean_next = rows[index + offset]
        if not LOCATION.match(raw_next):
            break
        selected.append(clean_next)
diagnostics = selected[-40:]
fallback = [clean for _raw, clean in rows[-16:]]
text = "\n".join(diagnostics if diagnostics else fallback)
text = text[-5000:]
text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
print(f"::error title=Native Godot diagnostics::{text}")
