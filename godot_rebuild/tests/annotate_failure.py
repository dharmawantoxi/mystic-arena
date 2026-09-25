"""Surface native engine diagnostics in Checks API, even if log download is unavailable."""
from pathlib import Path
import sys

lines = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
text = "\n".join(lines[-60:])
text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
print(f"::error title=Native Godot diagnostics::{text}")
