#!/usr/bin/env bash
# .devcontainer/setup.sh — dijalankan SEKALI saat container/Codespace dibuat
# (lihat "postCreateCommand" di .devcontainer/devcontainer.json).
#
# Tugasnya hanya menyiapkan alat supaya perintah yang sama dengan CI bisa
# dipakai di dalam Codespace:
#   * Godot 4.3 (VERSI = default .github/workflows/godot-run.yml; disamakan
#     oleh tools/test_godot_debug_runner.py),
#   * X11 + Mesa software GL (tanpa GPU, llvmpipe),
#   * ffmpeg (movie AVI -> mp4),
#   * venv python untuk oracle paritas pygame.
set -euo pipefail

GODOT_VERSION="4.3"
GODOT_RELEASE="stable"
VENV="$HOME/.venv-mystic"

echo "== Mystic Arena: menyiapkan Godot ${GODOT_VERSION}-${GODOT_RELEASE} =="

# ── 1. Paket sistem ────────────────────────────────────────────────────────
# libgl1-mesa-dri = llvmpipe (OpenGL di CPU). Tanpa itu Godot berhenti dengan
# "Unable to create an OpenGL context" dan tidak ada satu pun screenshot.
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  xvfb libgl1-mesa-dri libglx-mesa0 libegl-mesa0 x11-utils \
  libasound2t64 libpulse0 ffmpeg unzip curl ca-certificates \
  || sudo apt-get install -y --no-install-recommends \
       xvfb libgl1-mesa-dri libglx-mesa0 libegl-mesa0 x11-utils \
       libasound2 libpulse0 ffmpeg unzip curl ca-certificates

# ── 2. Godot (editor build: bisa --import, --export, dan menjalankan project) ─
if ! command -v godot >/dev/null 2>&1; then
  V="${GODOT_VERSION}-${GODOT_RELEASE}"
  URL="https://github.com/godotengine/godot/releases/download/${V}/Godot_v${V}_linux.x86_64.zip"
  curl -fsSL -o /tmp/godot.zip "$URL"
  sudo unzip -q -o /tmp/godot.zip -d /tmp/godot
  sudo mv "/tmp/godot/Godot_v${V}_linux.x86_64" /usr/local/bin/godot
  sudo chmod +x /usr/local/bin/godot
  rm -rf /tmp/godot /tmp/godot.zip
fi
godot --headless --version

# ── 3. DISPLAY milik desktop-lite (biasanya :1, tapi jangan ditebak) ───────
DISPLAY_NUM="$( (pgrep -a Xvfb || true) | grep -o ' :[0-9]\+' | head -1 | tr -d ' :' )"
DISPLAY_NUM="${DISPLAY_NUM:-1}"
if ! grep -q "MYSTIC_DISPLAY" "$HOME/.bashrc" 2>/dev/null; then
  printf '\nexport DISPLAY=:%s   # MYSTIC_DISPLAY (desktop-lite / Xvfb)\n' \
    "$DISPLAY_NUM" >> "$HOME/.bashrc"
fi
echo "Layar maya: DISPLAY=:${DISPLAY_NUM} (terminal baru sudah otomatis)"

# ── 4. Venv python (oracle paritas pygame + alat debug) ────────────────────
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet "pygame-ce==2.5.*" pillow numpy "gdtoolkit==4.*"
fi
if ! grep -q "venv-mystic" "$HOME/.bashrc" 2>/dev/null; then
  printf 'export PATH="$HOME/.venv-mystic/bin:$PATH"   # oracle paritas\n' \
    >> "$HOME/.bashrc"
fi

cat <<'PESAN'

== Siap. Tiga hal yang bisa langsung dilakukan ==

1. Buka EDITOR Godot di browser:
     tab "Ports" -> 6080 (Desktop noVNC) -> di terminal: godot --editor --path godot

2. Jalankan game + screenshot (layar maya, hasil di debug_out/):
     python3 tools/godot_debug_run.py --scenario battle --level 1 --seconds 30

3. Jalankan tes paritas yang sama dengan CI (headless, tanpa layar):
     python3 tools/godot_debug_run.py --scenario scene \
       --scene res://tests/BattleSmokeTest.tscn --display headless \
       --expect "[BattleSmokeTest] PASS"

Panduan lengkap: docs/GODOT_DEBUG_DI_GITHUB.md
PESAN
