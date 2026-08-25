"""
python-for-android hooks for Mystic Arena.

Cloud Save (Google Play Games Saved Games):
   PGS v2 memerlukan meta-data
       <meta-data android:name="com.google.android.gms.games.APP_ID"
                  android:value="@string/game_services_project_id"/>
   dan string resource `game_services_project_id` di res/values.

   Hook membaca Project ID dari:
       - env MYSTIC_GAMES_PROJECT_ID  (disarankan untuk CI / GitHub Actions)
       - path file dari env MYSTIC_GAMES_PROJECT_ID_FILE (fallback)
   Kalau tidak diset, meta-data TIDAK ditambahkan -> fitur cloud NONAKTIF
   (bridge Java menangkap error dan game tetap jalan).
"""

from __future__ import annotations

import os
from pathlib import Path

GAMES_META_DATA = (
    '<meta-data android:name="com.google.android.gms.games.APP_ID" '
    'android:value="@string/game_services_project_id"/>'
)
GAMES_STRING_NAME = "game_services_project_id"


def _read_games_project_id() -> str | None:
    """Project ID Play Games (numeric). Prioritas: env → file env → file repo."""
    value = os.environ.get("MYSTIC_GAMES_PROJECT_ID", "").strip()
    if value:
        return value
    file_env = os.environ.get("MYSTIC_GAMES_PROJECT_ID_FILE", "").strip()
    if file_env:
        try:
            p = Path(file_env)
            if p.is_file():
                value = p.read_text(encoding="utf-8").strip()
                if value:
                    return value
        except Exception as exc:
            print(f"[p4a-hook] baca project id gagal: {exc}")
    # Fallback: file di root repo yang di-ignore Git (aman untuk build lokal).
    try:
        local = Path("android_games_app_id.txt")
        if local.is_file():
            value = local.read_text(encoding="utf-8").strip()
            if value:
                return value
    except Exception as exc:
        print(f"[p4a-hook] baca android_games_app_id.txt gagal: {exc}")
    return None


def _write_games_strings(project_id: str) -> None:
    """Tulis res/values/mystic_games.xml berisi string project id."""
    values = Path("src/main/res/values")
    values.mkdir(parents=True, exist_ok=True)
    out = values / "mystic_games.xml"
    content = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        f'    <string translatable="false" name="{GAMES_STRING_NAME}">'
        f'{project_id}</string>\n'
        "</resources>\n"
    )
    out.write_text(content, encoding="utf-8")
    print(f"[p4a-hook] Tulis {GAMES_STRING_NAME}={project_id} ke {out}")


def _patch_manifest() -> None:
    manifest = Path("src/main/AndroidManifest.xml")
    if not manifest.exists():
        print(f"[p4a-hook] AndroidManifest.xml tidak ditemukan: {manifest}")
        return

    text = manifest.read_text(encoding="utf-8")

    # ── Cloud Save: Play Games APP_ID meta-data ──
    project_id = _read_games_project_id()
    if project_id:
        _write_games_strings(project_id)
        if "com.google.android.gms.games.APP_ID" not in text:
            app_pos = text.find("<application")
            insert_at = text.find(">", app_pos) + 1 if app_pos >= 0 else -1
            if insert_at > 0:
                text = (text[:insert_at] + "\n                 " + GAMES_META_DATA
                        + text[insert_at:])
                print(f"[p4a-hook] Menambahkan {GAMES_META_DATA} ke {manifest}")
            else:
                print("[p4a-hook] Tag <application> tidak ditemukan, "
                      "meta-data Play Games dilewati")
        else:
            print("[p4a-hook] Play Games APP_ID meta-data sudah ada")
    else:
        print("[p4a-hook] MYSTIC_GAMES_PROJECT_ID tidak diset — "
              "Cloud Save Play Games dalam mode NONAKTIF")

    manifest.write_text(text, encoding="utf-8")


def after_apk_build(toolchain) -> None:
    # Called after p4a generated the Gradle project/manifest and before assemble.
    _patch_manifest()


def before_apk_assemble(toolchain) -> None:
    # Defensive second pass in case p4a changes hook order in a future release.
    _patch_manifest()
