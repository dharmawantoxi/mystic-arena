"""Surface concise native engine diagnostics in Checks, even if log download fails."""
from pathlib import Path
import re
import sys

ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
DIAGNOSTIC = re.compile(r"SCRIPT ERROR|ERROR:|Parse Error|FAIL:|CRASH", re.IGNORECASE)
lines = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
clean_lines = [ANSI_ESCAPE.sub("", line).replace("\r", "").strip() for line in lines]
clean_lines = [line for line in clean_lines if line]
diagnostics = [line for line in clean_lines if DIAGNOSTIC.search(line)]
text = "\n".join((diagnostics[-40:] if diagnostics else clean_lines[-16:]))
text = text[-5000:]
text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
print(f"::error title=Native Godot diagnostics::{text}")
