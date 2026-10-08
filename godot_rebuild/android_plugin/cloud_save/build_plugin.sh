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
  gradle --no-daemon --console=plain :plugin:assembleDebug :plugin:assembleRelease \
    -PmysticGamesProjectId="$PROJECT_ID"
else
  echo "No Godot Google Play Games project ID configured; building an inert plugin."
  gradle --no-daemon --console=plain :plugin:assembleDebug :plugin:assembleRelease
fi

OUTPUT_DIR="$PLUGIN_DIR/plugin/build/outputs/aar"
DEST_DIR="$ROOT/godot_rebuild/addons/mystic_cloud/bin"
for variant in debug release; do
  candidates=()
  while IFS= read -r -d '' candidate; do
    candidates+=("$candidate")
  done < <(find "$OUTPUT_DIR" -maxdepth 1 -type f -name "*-$variant.aar" -print0)
  if [[ "${#candidates[@]}" != 1 ]]; then
    echo "Expected one $variant AAR in $OUTPUT_DIR; found ${#candidates[@]}." >&2
    find "$OUTPUT_DIR" -maxdepth 1 -type f -name '*.aar' -print >&2 || true
    exit 1
  fi
  mkdir -p "$DEST_DIR/$variant"
  aar="$DEST_DIR/$variant/MysticCloudSave-$variant.aar"
  cp "${candidates[0]}" "$aar"
  if [[ ! -s "$aar" ]]; then
    echo "Android plugin artifact is empty: $aar" >&2
    exit 1
  fi
done
