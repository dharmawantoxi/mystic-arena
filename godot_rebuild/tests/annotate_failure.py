"""Surface native engine diagnostics in Checks API, even if log download is unavailable."""
from pathlib import Path
import re
import sys

lines = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
pattern = re.compile(r"SCRIPT ERROR:|ERROR:|FAIL:")
report = []
for index, line in enumerate(lines):
    if not pattern.search(line):
        continue
    report.append(line)
    # Godot follows a diagnostic with its source location; keep it attached.
    for extra in lines[index + 1:index + 3]:
        if extra.strip().startswith("at:"):
            report.append(extra)
            break
if not report:
    report = lines[-40:]
if len(sys.argv) > 2 and report:
    report = [f"exit code {sys.argv[2]}", *report]
text = "\n".join(report[:80]).strip()
text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
print(f"::error title=Native Godot diagnostics::{text}")
