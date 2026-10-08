#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PLUGIN_DIR="$ROOT/godot_rebuild/android_plugin/cloud_save"
ID_FILE="$ROOT/godot_rebuild/android_games_app_id.txt"
PROJECT_ID="${MYSTIC_GODOT_GAMES_PROJECT_ID:-}"
if [[ -z "$PROJECT_ID" && -f "$ID_FILE" ]]; then
  PROJECT_ID="$(tr -d '[:space:]' < "$ID_FILE")"
fi
if [[ -n "$PROJECT_ID" && ! "$PROJECT_ID" =~ ^[1-9][0-9]{5,19}$ ]]; then
  echo "Invalid Google Play Games project ID; expected 6-20 digits." >&2
  exit 2
fi

cd "$PLUGIN_DIR"
if [[ -n "$PROJECT_ID" ]]; then
  gradle --no-daemon --console=plain :plugin:copyGodotPluginAars -PmysticGamesProjectId="$PROJECT_ID"
else
  echo "No Godot Google Play Games project ID configured; building an inert plugin."
  gradle --no-daemon --console=plain :plugin:copyGodotPluginAars
fi

test -s "$ROOT/godot_rebuild/addons/mystic_cloud/bin/debug/MysticCloudSave-debug.aar"
test -s "$ROOT/godot_rebuild/addons/mystic_cloud/bin/release/MysticCloudSave-release.aar"
