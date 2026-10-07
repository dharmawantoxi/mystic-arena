"""Surface native engine diagnostics in Checks API, even if log download is unavailable."""
from pathlib import Path
import re
import sys

lines = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
pattern = re.compile(r"SCRIPT ERROR:|ERROR:|FAIL:")
matches = [line for line in lines if pattern.search(line)]
report = matches[:60] if matches else lines[-40:]
if matches:
    report = [f"exit code {sys.argv[2]}" if len(sys.argv) > 2 else "", *report]
text = "\n".join(report).strip()
text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
print(f"::error title=Native Godot diagnostics::{text}")
