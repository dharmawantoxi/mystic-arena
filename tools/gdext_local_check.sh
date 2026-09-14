#!/usr/bin/env bash
# tools/gdext_local_check.sh — jalankan VERIFIKASI GDExtension di mesin sendiri,
# tanpa menunggu GitHub Actions (yang ±40-75 menit karena harus compile
# godot-cpp ±950 berkas + build 6 lib + 10 langkah engine).
#
# Ide dasarnya: workflow godot-gdext.yml sudah tersusun berlapis, dan TIGA
# lapis pertama tidak butuh godot-cpp sama sekali — cukup python3 + g++.
# Lapis itu yang menutup ±90% kelas bug nyata (data basi, logika helper salah,
# tabel perintah tidak closed-world, API godot-cpp salah nama). Skrip ini
# menjalankan lapis yang sama, dengan perintah yang sama, di lokal.
#
#   L0  kesegaran transpile      python3 saja            < 1 detik
#   L1  paritas statis           python3 saja            ± 5 detik
#   L2  self-test C++ (stub)     g++ (tanpa godot-cpp)   ± 20 detik
#   L3  sintaks vs godot-cpp     g++ + header gen/       ± 30 detik
#   L4  build .so sungguhan      scons + godot-cpp       LAMBAT pertama kali,
#                                                       ±1-3 menit/lib setelahnya
#   L5  tes engine headless      binary Godot 4.3        ± 1-3 menit
#
# PAKAI:
#   tools/gdext_local_check.sh                 # L0-L2 (default: cepat, ±25 detik)
#   tools/gdext_local_check.sh --lapis 3       # + cek sintaks vs header asli
#   tools/gdext_local_check.sh --lapis 4       # + build .so + cek nm/strings
#   tools/gdext_local_check.sh --lapis 5       # + jalankan tes paritas di engine
#   tools/gdext_local_check.sh --lib levels    # hanya satu lib (levels/maps/ui/
#                                              # mobile/splash/skills)
#   tools/gdext_local_check.sh --gdsyntax      # + gdparse semua .gd (gdtoolkit)
#
# Butuh: python3 (3.11), g++. Untuk L4: scons (`pip install scons`) + git.
# Untuk L5: binary Godot 4.3 (diunduh otomatis ke ~/.cache/mystic-arena).
# pygame hanya dibutuhkan generator --check untuk splash/ui kalau mau oracle
# penuh; tanpa pygame skrip tetap jalan (self-test membaca AST).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ── python + compiler ───────────────────────────────────────────────────────
# Venv repo (.venv/ atau ~/.venv-mystic milik .devcontainer/setup.sh) dipakai
# kalau ada, supaya scons/gdtoolkit/pygame yang diinstal di sana ikut kepakai.
PY="python3"
for cand in "$ROOT/.venv/bin/python" "$HOME/.venv-mystic/bin/python"; do
  [ -x "$cand" ] && { PY="$cand"; break; }
done
CXX="${CXX:-g++}"
GODOT_VERSION="${GODOT_VERSION:-4.3}"
GODOT_RELEASE="${GODOT_RELEASE:-stable}"
GODOT_CPP_REF="${GODOT_CPP_REF:-godot-${GODOT_VERSION}-${GODOT_RELEASE}}"
# Sama dengan env SCONS_FLAGS di godot-gdext.yml: yang diuji paritas, bukan
# kecepatan, jadi optimize=none memangkas waktu compile drastis.
SCONS_FLAGS="${SCONS_FLAGS:-platform=linux target=template_debug optimize=none debug_symbols=no}"
JOBS="${JOBS:-$( (nproc 2>/dev/null || echo 2) )}"

LAPIS=2
LIB_FILTER=""
GDSYNTAX=0
while [ $# -gt 0 ]; do
  case "$1" in
    --lapis|--tier) LAPIS="$2"; shift 2 ;;
    --lib)          LIB_FILTER="$2"; shift 2 ;;
    --gdsyntax)     GDSYNTAX=1; shift ;;
    --all)          LAPIS=5; shift ;;
    -h|--help)      sed -n '2,40p' "$0"; exit 0 ;;
    *) echo "[gdext-lokal] argumen tidak dikenal: $1" >&2; exit 2 ;;
  esac
done

# ── definisi lib: folder, generator, self-test offline, api_signature, tes engine ─
# mystic_skills tidak punya self-test offline (oracle-nya match_parity.json yang
# butuh pygame + replay 222 hero) — verifikasi offlinenya L0/L1 saja, sisanya L4/L5.
# mystic_lighting belum dibuild CI dan belum punya generator/self-test.
LIBS_ALL="skills levels maps ui mobile splash"

lib_dir()      { case "$1" in skills) echo mystic_skills ;; *) echo "mystic_$1" ;; esac; }
lib_gens()     { case "$1" in
  skills) echo "gen_hero_skill_kit.py gen_hero_skills_cpp.py" ;;
  levels) echo "gen_levels_cpp.py" ;;
  maps)   echo "gen_maps_cpp.py" ;;
  ui)     echo "gen_ui_cpp.py" ;;
  mobile) echo "gen_mobile_cpp.py" ;;
  splash) echo "gen_splash_cpp.py" ;;
esac; }
lib_selftest() { case "$1" in
  levels) echo "test_levels_cpp_selftest.py" ;;
  maps)   echo "test_maps_cpp_selftest.py" ;;
  ui)     echo "test_ui_cpp_selftest.py" ;;
  mobile) echo "test_mobile_cpp_selftest.py" ;;
  splash) echo "test_splash_cpp_selftest.py" ;;
  *)      echo "" ;;
esac; }
lib_parity()   { case "$1" in
  levels) echo "test_godot_level_data_parity.py" ;;
  maps)   echo "test_godot_map_data_parity.py" ;;
  *)      echo "" ;;
esac; }
# api_signature yang juga dicek CI lewat `strings` pada .so (tahan strip).
lib_signature(){ case "$1" in
  ui)     echo "ui_v1:11mod:80fn:" ;;
  mobile) echo "mobile_v1:8mod:66fn:" ;;
  splash) echo "splash_v1:1mod:62fn:" ;;
  *)      echo "" ;;
esac; }
lib_class()    { case "$1" in
  skills) echo "MysticHeroSkills" ;;
  levels) echo "MysticLevels" ;;
  maps)   echo "MysticMaps" ;;
  ui)     echo "MysticUI" ;;
  mobile) echo "MysticMobile" ;;
  splash) echo "MysticSplash" ;;
esac; }
# scene tes engine + penanda wajib, persis langkah 6-13 godot-gdext.yml.
# ui/mobile sengaja mencantumkan scene yang BELUM ada: CI pun tidak punya
# lapisan engine untuk keduanya, jadi di lokal statusnya LEWAT (bukan OK palsu)
# sampai godot/tests/UiHudGdextParityTest.tscn dkk. benar-benar dibuat.
lib_engine_tests() { case "$1" in
  skills) echo "HeroSkillGdextParityTest:900:[HeroSkillGdextParityTest] PASS|GDExtension MysticHeroSkills aktif
HeroSkillParityTest:900:[HeroSkillParityTest] PASS" ;;
  levels) echo "LevelDataGdextParityTest:120:[LevelDataGdextParityTest] PASS|GDExtension MysticLevels aktif
LevelDataParityTest:120:[LevelDataParityTest] PASS" ;;
  maps)   echo "MapDataGdextParityTest:120:[MapDataGdextParityTest] PASS|GDExtension MysticMaps aktif
MapDataParityTest:120:[MapDataParityTest] PASS" ;;
  splash) echo "SplashGdextParityTest:400:[SplashGdextParityTest] PASS|GDExtension MysticSplash aktif
SplashParityTest:400:[SplashParityTest] PASS" ;;
  ui)     echo "UiHudGdextParityTest:120:[UiHudGdextParityTest] PASS|GDExtension MysticUI aktif" ;;
  mobile) echo "MobileGdextParityTest:120:[MobileGdextParityTest] PASS|GDExtension MysticMobile aktif" ;;
esac; }

if [ -n "$LIB_FILTER" ]; then
  LIBS="$LIB_FILTER"
else
  LIBS="$LIBS_ALL"
fi

FAIL=0
declare -a RINGKASAN=()
MULAI_TOTAL=$SECONDS

step() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
ok()   { printf '  \033[32mOK\033[0m   %s\n' "$*"; RINGKASAN+=("OK   $*"); }
gagal(){ printf '  \033[31mGAGAL\033[0m %s\n' "$*"; RINGKASAN+=("GAGAL $*"); FAIL=1; }
lewat(){ printf '  \033[33mLEWAT\033[0m %s\n' "$*"; RINGKASAN+=("LEWAT $*"); }

# jalankan <label> <perintah...> — ukur waktu, tandai OK/GAGAL.
jalankan() {
  local label="$1"; shift
  local t0=$SECONDS
  if "$@" > /tmp/gdext-lokal-$$.log 2>&1; then
    ok "$label ($((SECONDS - t0))s)"
  else
    gagal "$label ($((SECONDS - t0))s)"
    tail -30 /tmp/gdext-lokal-$$.log | sed 's/^/        /'
  fi
}

echo "[gdext-lokal] root=$ROOT"

# ── kunci build: godot-cpp dipakai bersama SEMUA lib ────────────────────────
# Dua invocation yang build bareng merusak satu sama lain: objek di
# godot/gdext/godot-cpp/gen/src dibongkar-pasang dua scons sekaligus dan link
# .a gagal dengan "ar: ...stream_peer_tcp...o: No such file or directory"
# (terjadi sungguhan saat mengukur dokumen ini). Jadi L>=4 dikunci; jalankan
# SEMUA lib dalam SATU invocation, jangan paralel.
LOCK="/tmp/gdext-local-check-$(id -u).lock"
if [ "$LAPIS" -ge 4 ]; then
  if [ -e "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
    echo "[gdext-lokal] invocation lain sedang build (pid $(cat "$LOCK"))." >&2
    echo "[gdext-lokal] Tunggu selesai, atau: tools/gdext_local_check.sh --lapis 2 (tanpa build)." >&2
    exit 3
  fi
  echo $$ > "$LOCK"
  trap 'rm -f "$LOCK"' EXIT
fi
echo "[gdext-lokal] python=$PY  compiler=$CXX  lapis<=$LAPIS  lib=${LIBS}  jobs=$JOBS"

# ═══════════════ L0: kesegaran transpile (python3 saja) ═══════════════
# .h/.cpp dan HeroSkillKit.gd adalah HASIL GENERATE. Kalau yang ter-commit
# basi, build C++ di CI mengunci perilaku LAMA — jadi ini dicek paling dulu.
if [ "$LAPIS" -ge 0 ]; then
  step "L0 — kesegaran generator (tanpa compiler)"
  for lib in $LIBS; do
    for gen in $(lib_gens "$lib"); do
      jalankan "L0 $gen --check" "$PY" "tools/$gen" --check
    done
  done
fi

# ═══════════════ L1: paritas statis (python3 saja) ═══════════════
# Bandingkan oracle Python ↔ fixture JSON ↔ literal tabel C++ ↔ wiring
# (loader/autoload/project.godot/.gdextension/.gitignore/kedua workflow).
if [ "$LAPIS" -ge 1 ]; then
  step "L1 — paritas statis (tanpa compiler)"
  for lib in $LIBS; do
    for t in $(lib_parity "$lib"); do
      jalankan "L1 $t" "$PY" "tools/$t"
    done
  done
fi

# ═══════════════ L2: self-test C++ di luar engine (g++ saja) ═══════════════
# MENGEKSEKUSI *_processor.cpp apa adanya lewat stub Variant. Ini lapis yang
# paling murah tapi paling sering menangkap regresi: nilai tabel, logika helper,
# tipe, urutan kunci Dictionary, RNG MT19937.
if [ "$LAPIS" -ge 2 ]; then
  step "L2 — self-test C++ tanpa engine (g++ saja, tanpa godot-cpp)"
  command -v "$CXX" >/dev/null 2>&1 || { echo "  compiler $CXX tidak ada — L2 dilewati"; }
  for lib in $LIBS; do
    t="$(lib_selftest "$lib")"
    if [ -z "$t" ]; then
      lewat "L2 $lib (tidak ada self-test offline — verifikasi lewat L4/L5)"
      continue
    fi
    jalankan "L2 $t" "$PY" "tools/$t"
  done
fi

# ═══════════════ L3: sintaks vs header godot-cpp ASLI ═══════════════
# Stub Variant punya API sendiri, jadi salah nama fungsi godot-cpp (kejadian
# nyata PR #234: color.r8() padahal yang ada color.get_r8()) TIDAK ketahuan di
# L2. self-test ui/splash sudah punya langkah ini dan otomatis aktif kalau
# checkout godot-cpp ada + gen/include sudah dibangkitkan.
CPP_DIR="$ROOT/godot/gdext/godot-cpp"
# SConstruct tiap ekstensi mengharapkan godot-cpp DI DALAM direktorinya sendiri;
# symlink ke checkout bersama adalah jembatannya (objek compile-nya jadi
# dipakai bersama: satu compile godot-cpp untuk enam lib — pola CI).
# Dipanggil TERPISAH dari clone-nya, karena checkout biasanya sudah ada
# sementara symlink lib yang sedang diuji belum.
symlink_godot_cpp() {
  [ -d "$CPP_DIR/include/godot_cpp" ] || return 1
  local lib link dir
  for lib in $LIBS_ALL; do
    dir="$ROOT/godot/gdext/$(lib_dir "$lib")"
    link="$dir/godot-cpp"
    [ -d "$dir" ] || continue
    if [ -L "$link" ] || [ -d "$link" ]; then continue; fi
    ln -s ../godot-cpp "$link" && echo "  symlink $(basename "$dir")/godot-cpp -> ../godot-cpp"
  done
  return 0
}

siapkan_godot_cpp() {
  if [ -d "$CPP_DIR/include/godot_cpp" ]; then symlink_godot_cpp; return 0; fi
  command -v git >/dev/null 2>&1 || { echo "  git tidak ada"; return 1; }
  step "Menyiapkan godot-cpp ($GODOT_CPP_REF) — sekali saja"
  rm -rf "$CPP_DIR"
  git clone -q -b "$GODOT_CPP_REF" --depth 1 \
    https://github.com/godotengine/godot-cpp "$CPP_DIR" || return 1
  symlink_godot_cpp
  return 0
}

if [ "$LAPIS" -ge 3 ]; then
  step "L3 — cek sintaks terhadap header godot-cpp asli"
  if siapkan_godot_cpp; then
    # gen/include dibuat binding_generator saat scons jalan. Kalau belum ada,
    # bangkitkan dulu (±1 menit, jauh lebih murah daripada compile penuh).
    if [ ! -f "$CPP_DIR/gen/include/godot_cpp/classes/ref_counted.hpp" ]; then
      if command -v scons >/dev/null 2>&1 || "$PY" -c "import SCons" 2>/dev/null; then
        echo "  membangkitkan header godot-cpp (binding_generator) ..."
        ( cd "$CPP_DIR" && "$PY" -m SCons platform=linux target=template_debug \
            optimize=none debug_symbols=no -j"$JOBS" > /tmp/gdext-lokal-gen.log 2>&1 ) \
          || ( cd "$CPP_DIR" && scons platform=linux target=template_debug \
            optimize=none debug_symbols=no -j"$JOBS" >> /tmp/gdext-lokal-gen.log 2>&1 )
      fi
    fi
    if [ -f "$CPP_DIR/gen/include/godot_cpp/classes/ref_counted.hpp" ]; then
      export GODOT_CPP_DIR="$CPP_DIR"
      for lib in $LIBS; do
        t="$(lib_selftest "$lib")"
        d="$ROOT/godot/gdext/$(lib_dir "$lib")/src"
        if [ -z "$t" ]; then
          # skills: tidak ada self-test offline, jadi -fsyntax-only langsung.
          jalankan "L3 -fsyntax-only $(lib_dir "$lib")" \
            "$CXX" -std=c++17 -fsyntax-only \
            -I "$CPP_DIR/include" -I "$CPP_DIR/gen/include" -I "$CPP_DIR/gdextension" \
            -I "$d" "$d/$(ls "$d" | grep '_processor\.cpp$')" "$d/register_types.cpp"
          continue
        fi
        jalankan "L3 $t (dengan GODOT_CPP_DIR)" "$PY" "tools/$t"
      done
    else
      lewat "L3 (gen/include godot-cpp belum ada — jalankan L4 sekali untuk membangkitkannya)"
    fi
  else
    lewat "L3 (godot-cpp tidak tersedia offline)"
  fi
fi

# ═══════════════ L4: build .so sungguhan + cek symbol/string ═══════════════
# Satu-satunya lapis yang LAMBAT, dan satu-satunya yang memverifikasi lapisan
# binding godot-cpp + link. Setelah jalan sekali, objek build tersimpan di
# godot/gdext/godot-cpp (gitignored) sehingga build berikutnya inkremental.
if [ "$LAPIS" -ge 4 ]; then
  step "L4 — build lib .so (scons) + cek entry symbol & isi modul"
  if ! siapkan_godot_cpp; then
    lewat "L4 (godot-cpp tidak tersedia)"
  else
    if ! command -v scons >/dev/null 2>&1 && ! "$PY" -c "import SCons" 2>/dev/null; then
      lewat "L4 (scons tidak ada — pip install scons)"
    else
      for lib in $LIBS; do
        name="$(lib_dir "$lib")"
        d="$ROOT/godot/gdext/$name"
        so="godot/addons/$name/bin/lib$name.linux.template_debug.x86_64.so"
        # shellcheck disable=SC2086
        if ( cd "$d" && (command -v scons >/dev/null 2>&1 \
              && scons $SCONS_FLAGS -j"$JOBS" \
              || "$PY" -m SCons $SCONS_FLAGS -j"$JOBS") ) > /tmp/gdext-lokal-build-$lib.log 2>&1; then
          ok "L4 build $name ($(tail -1 /tmp/gdext-lokal-build-$lib.log | cut -c1-80))"
        else
          gagal "L4 build $name"
          tail -25 /tmp/gdext-lokal-build-$lib.log | sed 's/^/        /'
          continue
        fi
        if [ ! -s "$ROOT/$so" ]; then gagal "L4 $so tidak dihasilkan"; continue; fi
        entry="${name}_library_init"
        if nm -D --defined-only "$ROOT/$so" | grep -q " T $entry"; then
          ok "L4 entry symbol $entry"
        else
          gagal "L4 entry symbol $entry tidak diekspor"
        fi
        sig="$(lib_signature "$lib")"
        blob="$(strings -a "$ROOT/$so")"
        if [ -n "$sig" ]; then
          case "$blob" in *"$sig"*) ok "L4 api_signature $sig" ;;
                          *) gagal "L4 api_signature $sig tidak ada di .so" ;; esac
        fi
        # -fvisibility=hidden + debug_symbols=no: kelas TIDAK ada di symbol
        # table, jadi buktinya string tahan-strip (catatan PR #234).
        case "$blob" in *"$(lib_class "$lib")"*) ok "L4 string kelas $(lib_class "$lib")" ;;
                        *) gagal "L4 string kelas $(lib_class "$lib") tidak ada di .so" ;; esac
      done
    fi
  fi
fi

# ═══════════════ L5: tes paritas di engine (Godot headless) ═══════════════
# Baru bermakna setelah L4: scene *GdextParityTest memaksa backend ke "gdext"
# dan GAGAL KERAS kalau lib tidak termuat.
if [ "$LAPIS" -ge 5 ]; then
  step "L5 — tes engine headless (Godot $GODOT_VERSION)"
  GODOT_BIN="$(command -v godot || true)"
  [ -n "$GODOT_BIN" ] || GODOT_BIN="${MYSTIC_GODOT:-}"
  cache="${MYSTIC_GODOT_CACHE:-$HOME/.cache/mystic-arena}/godot-$GODOT_VERSION"
  if [ -z "$GODOT_BIN" ] && [ -x "$cache/godot" ]; then GODOT_BIN="$cache/godot"; fi
  if [ -z "$GODOT_BIN" ]; then
    # URL + tata letak cache SAMA dengan tools/godot_debug_run.py (tag rilis
    # Godot selalu "<versi>-<release>"; ".../download/4.3/..." menjawab 404).
    tag="$GODOT_VERSION-$GODOT_RELEASE"
    url="https://github.com/godotengine/godot/releases/download/$tag/Godot_v${tag}_linux.x86_64.zip"
    echo "  mengunduh Godot $tag (sekali, ke $cache) ..."
    mkdir -p "$cache"
    if command -v curl >/dev/null 2>&1 \
       && curl -fsSL --retry 3 -o "$cache/godot.zip" "$url" \
       && command -v unzip >/dev/null 2>&1 \
       && unzip -q -o "$cache/godot.zip" -d "$cache/unzip" \
       && mv "$cache/unzip/Godot_v${tag}_linux.x86_64" "$cache/godot"; then
      chmod +x "$cache/godot"; rm -rf "$cache/godot.zip" "$cache/unzip"
      GODOT_BIN="$cache/godot"
    else
      rm -rf "$cache/godot.zip" "$cache/unzip"
    fi
  fi
  if [ -z "$GODOT_BIN" ]; then
    lewat "L5 (binary godot tidak ditemukan; pasang Godot $GODOT_VERSION atau --download lewat tools/godot_debug_run.py)"
  else
    # Aset biner gitignored (presplash/sounds/items): tanpa presplash boot
    # engine mencetak error yang menutupi error sungguhan.
    jalankan "L5 salin aset biner" "$PY" tools/convert_to_godot.py --assets
    "$GODOT_BIN" --headless --path godot --import > /tmp/gdext-lokal-import.log 2>&1
    if "$PY" godot/tools/godot_log_gate.py /tmp/gdext-lokal-import.log --label "import" > /tmp/gdext-lokal-import.gate 2>&1; then
      ok "L5 import project (lib .so dimuat)"
    else
      gagal "L5 import project"
      tail -15 /tmp/gdext-lokal-import.gate | sed 's/^/        /'
    fi
    for lib in $LIBS; do
      while IFS= read -r spec; do
        [ -z "$spec" ] && continue
        scene="${spec%%:*}"; rest="${spec#*:}"; quit="${rest%%:*}"; requires="${rest#*:}"
        tscn="res://tests/$scene.tscn"
        [ -f "godot/tests/$scene.tscn" ] || { lewat "L5 $scene (scene tidak ada)"; continue; }
        log="/tmp/gdext-lokal-$scene.log"
        # LevelData*Test snapshot + restore data SaveManager -> isolasi XDG.
        isolated="$(mktemp -d)"
        ( export XDG_DATA_HOME="$isolated"
          "$GODOT_BIN" --headless --path "$ROOT/godot" "$tscn" --quit-after "$quit" ) \
          > "$log" 2>&1
        rm -rf "$isolated"
        req_args=()
        IFS='|' read -ra parts <<< "$requires"
        for p in "${parts[@]}"; do req_args+=(--require "$p"); done
        if "$PY" godot/tools/godot_log_gate.py "$log" --label "$scene" \
             "${req_args[@]}" > "$log.gate" 2>&1; then
          ok "L5 $scene"
        else
          gagal "L5 $scene"
          tail -12 "$log.gate" | sed 's/^/        /'
          grep -m10 'FAIL\|SCRIPT ERROR\|Parse Error' "$log" | sed 's/^/        /'
        fi
      done <<< "$(lib_engine_tests "$lib")"
    done
  fi
fi

# ═══════════════ opsional: sintaks GDScript ═══════════════
if [ "$GDSYNTAX" = "1" ]; then
  step "gdparse — sintaks semua GDScript"
  if "$PY" -c "import gdtoolkit" 2>/dev/null; then
    if "$PY" -m gdtoolkit.parser.gdparse $(find godot -name '*.gd') > /tmp/gdext-lokal-gdparse.log 2>&1; then
      ok "gdparse $(find godot -name '*.gd' | wc -l) berkas .gd"
    else
      gagal "gdparse"
      tail -20 /tmp/gdext-lokal-gdparse.log | sed 's/^/        /'
    fi
  else
    lewat "gdparse (gdtoolkit tidak ada — pip install 'gdtoolkit==4.*')"
  fi
fi

# ═══════════════ ringkasan ═══════════════
printf '\n\033[1m== RINGKASAN (%ds) ==\033[0m\n' "$((SECONDS - MULAI_TOTAL))"
for r in "${RINGKASAN[@]}"; do printf '  %s\n' "$r"; done
rm -f /tmp/gdext-lokal-$$.log
if [ "$FAIL" = "0" ]; then
  printf '\n\033[32mSEMUA LAPIS <= L%s LOLOS\033[0m\n' "$LAPIS"
  [ "$LAPIS" -lt 4 ] && printf '%s\n' \
    "Catatan: L0-L$((LAPIS)) tidak mengompilasi lapisan binding godot-cpp." \
    "Untuk setara penuh dengan CI jalankan: tools/gdext_local_check.sh --lapis 5"
  exit 0
fi
printf '\n\033[31mADA YANG GAGAL\033[0m — perbaiki dulu sebelum push, supaya kuota CI tidak terpakai untuk hal yang sudah ketahuan lokal.\n'
exit 1
