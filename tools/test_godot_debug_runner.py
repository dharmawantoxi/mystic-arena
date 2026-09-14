#!/usr/bin/env python3
"""Gerbang statis untuk "Godot bisa dijalankan dari repo" (jalur debug).

    python3 tools/test_godot_debug_runner.py

TIDAK butuh pygame dan TIDAK butuh Godot — hampir semuanya dibaca dari berkas,
jadi cek ini jalan di langkah "Linter statis" godot-check.yml sebelum engine
diunduh (hitungan milidetik). Pengecualiannya cek terakhir: rem darurat diuji
dengan stub pembungkus shell (bukan Godot) selama ~2 detik.

KENAPA PERLU
============
Jalur debug ini punya EMPAT pemilik yang harus sepakat, dan tidak satu pun
dari mereka akan mengeluh kalau salah satu berubah sendiri:

    .github/workflows/godot-run.yml   (dropdown skenario + flag CLI yang dikirim)
        -> tools/godot_debug_run.py   (SCENARIOS/ENGINE_ARGS + perintah engine)
            -> godot/scenes/debug/DebugRun.gd  (ARG_KEYS + cabang skenario)
                -> godot/scenes/debug/DebugProbe.gd (berkas yang ditulis)

Kalau nama skenario berubah di satu tempat saja, gejalanya bukan error: harness
cukup mencetak "PERINGATAN: skenario tidak dikenal" lalu berjalan sebagai
`menu` — dan artifact berisi 30 screenshot layar menu tanpa ada yang tahu
kenapa. Sama untuk `--shot-every` yang salah ketik (Godot mengabaikan argumen
tak dikenal dalam diam) atau `debug_out/` yang lupa di-gitignore (ratusan PNG
masuk commit berikutnya).

YANG DIKUNCI
  1. SCENARIOS + ARG_KEYS Python == GDScript == dropdown workflow (closed-world);
  2. tiap flag CLI yang dipakai workflow benar-benar ada di argparse alat itu,
     dan alat itu benar-benar menulis `--out` ke tempat artifact mengunduhnya;
  3. tiap kunci ENGINE_ARGS punya cabang di GDScript, dan tiap skenario
     benar-benar dipakai (bukan cuma ada di daftar);
  4. aset biner (gitignored) disalin SEBELUM engine dijalankan, dan
     `debug_out/` ditutup .gitignore;
  5. baris `[DebugRun] PASS` yang diminta gerbang log == yang dicetak harness;
  6. berkas scene/probe/devcontainer benar-benar ada dan versi Godot-nya
     tidak berbeda antara workflow dan devcontainer;
  7. gate ini tidak bisa dihapus diam-diam: godot-check.yml harus tetap
     memanggilnya dan tetap memantau berkas baru ini di filter `paths`;
  8. jalur debug ini punya satu mode kegagalan yang mahal — MENGGANTUNG:
     (a) rem darurat harus mematikan SELURUH process group (mode xvfb: pembunuh
         proc.kill() hanya mengenai skrip xvfb-run, Godot-nya lanjut hidup),
     (b) stdout engine tidak boleh tertahan buffer blok (stdbuf), kalau tidak
         log yang dibutuhkan justru hilang saat proses dibunuh,
     (c) harness wajib punya jejak boot (trace.log, di-flush) + batas boot,
     (d) ketiganya harus ikut terunggah sebagai artifact;
  9. preflight punya DUA bagian: kompilasi skrip debug dengan engine yang
     sama dengan run (`--check-only -s`) dan scene penanda `DebugMarker` yang
     TIDAK memakai satu pun API game. Hasilnya ikut artifact — supaya 'harness
     sunyi' bisa dipisahkan dari 'engine tidak bisa menjalankan scene/project';
 10. tidak ada API yang baru ada SETELAH 4.3 (versi CI + devcontainer) yang
     dipanggil langsung dari skrip debug: di engine 4.3 panggilan itu jadi
     parse error / `Invalid call` — skrip bisu dan log kotor, sementara gdparse
     (sintaks saja) tidak bisa melihatnya;
 11. panggilan dinamis pada hasil `get_first_node_in_group()` (bertipe `Node`)
     wajib lewat `has_method(...)` seperti `scenes/main/Main.gd`; kalau tidak,
     salah nama method = `Invalid call. Nonexistent function … in base Node`,
     satu baris SCRIPT ERROR yang membuat gerbang log menolak run;
 12. rem darurat diuji dengan stub pembungkus shell (bukan Godot, ~2 detik).
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "godot_debug_run.py"
WORKFLOW = ROOT / ".github" / "workflows" / "godot-run.yml"
CHECK_WORKFLOW = ROOT / ".github" / "workflows" / "godot-check.yml"
RUN_GD = ROOT / "godot" / "scenes" / "debug" / "DebugRun.gd"
PROBE_GD = ROOT / "godot" / "scenes" / "debug" / "DebugProbe.gd"
RUN_TSCN = ROOT / "godot" / "scenes" / "debug" / "DebugRun.tscn"
MARKER_GD = ROOT / "godot" / "scenes" / "debug" / "DebugMarker.gd"
MARKER_TSCN = ROOT / "godot" / "scenes" / "debug" / "DebugMarker.tscn"
DEVCONTAINER = ROOT / ".devcontainer" / "devcontainer.json"
DEVCONTAINER_SETUP = ROOT / ".devcontainer" / "setup.sh"
DOC = ROOT / "docs" / "GODOT_DEBUG_DI_GITHUB.md"
GITIGNORE = ROOT / ".gitignore"

FLAG_RE = re.compile(r"--([a-z0-9][a-z0-9-]*)")


def read(path: Path) -> str:
    if not path.exists():
        raise AssertionError("berkas tidak ada: %s" % path.relative_to(ROOT))
    return path.read_text(encoding="utf-8")


def load_tool():
    spec = importlib.util.spec_from_file_location("godot_debug_run", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gd_list(source: str, name: str) -> list[str]:
    """Ambil isi `const NAME: Array = [...]` (satu konstanta, apa adanya)."""
    match = re.search(r"const\s+%s[^=]*=\s*\[(.*?)\]" % name, source, re.S)
    if not match:
        raise AssertionError("tidak menemukan daftar %s di DebugRun.gd" % name)
    return re.findall(r'"([^"]+)"', match.group(1))


def gd_match_keys(source: str, marker: str) -> list[str]:
    """Kunci cabang `match key:` (baris `"kunci":` sampai baris kosong)."""
    start = source.index(marker)
    block = source[start:source.index("\n\n", start)]
    return re.findall(r'^\s+"([a-z][a-z0-9-]*)":', block, re.M)


def check_contract_lists() -> None:
    tool = load_tool()
    run_gd = read(RUN_GD)
    workflow = read(WORKFLOW)

    py_scenarios = list(tool.SCENARIOS)
    py_args = list(tool.ENGINE_ARGS)
    gd_scenarios = gd_list(run_gd, "SCENARIOS")
    gd_args = gd_list(run_gd, "ARG_KEYS")

    if py_scenarios != gd_scenarios:
        raise AssertionError(
            "daftar skenario Python != GDScript: %s vs %s — ubah keduanya "
            "(dan dropdown di %s)" % (py_scenarios, gd_scenarios,
                                      WORKFLOW.name))
    if py_args != gd_args:
        raise AssertionError(
            "ENGINE_ARGS Python != ARG_KEYS GDScript: %s vs %s"
            % (py_args, gd_args))

    # Dropdown workflow: blok `options:` pertama sesudah `scenario:`.
    scenario_block = workflow[workflow.index("scenario:"):]
    options = re.search(r"options:\s*\[([^\]]+)\]", scenario_block)
    if not options:
        raise AssertionError("%s: input `scenario` tidak punya daftar options"
                             % WORKFLOW.name)
    drop_down = [item.strip() for item in options.group(1).split(",")]
    if drop_down != py_scenarios:
        raise AssertionError(
            "dropdown skenario workflow != SCENARIOS: %s vs %s"
            % (drop_down, py_scenarios))
    if "options: [menu, level, battle, shop, scene]" not in workflow:
        raise AssertionError("dropdown skenario workflow berubah bentuk — "
                             "perbarui cek ini sekalian")
    print("[kontrak] skenario %s + %d kunci argumen: Python == GDScript == "
          "workflow" % (py_scenarios, len(py_args)))


def check_workflow_flags() -> None:
    tool = load_tool()
    workflow = read(WORKFLOW)

    # Hanya blok step yang memanggil alat ini — jangan menilai flag engine
    # yang dikirim lewat --extra (itu urusan pemakai).
    start = workflow.index("Jalankan Godot (harness debug)")
    step = workflow[start:workflow.index("- name:", start)]
    used = set(FLAG_RE.findall(step))
    known = {flag.lstrip("-") for flag in tool.build_parser()._option_string_actions}
    unknown = sorted(used - known)
    if unknown:
        raise AssertionError(
            "%s mengirim flag yang tidak dikenal tools/godot_debug_run.py: %s "
            "(argparse akan menolak dan run gagal total)"
            % (WORKFLOW.name, ", ".join("--" + u for u in unknown)))

    # `used` berisi NAMA flag (tanpa --), lihat FLAG_RE.
    if "out" not in used:
        raise AssertionError("%s tidak menentukan --out — artifact tidak bisa "
                             "diprediksi" % WORKFLOW.name)
    # Artifact harus mengambil dari direktori yang sama dengan --out.
    out_dir = re.search(r"OUT_DIR:\s*(debug_out)/", workflow)
    if not out_dir:
        raise AssertionError("env OUT_DIR workflow harus di dalam debug_out/")
    artifact = workflow[workflow.index("Unggah artifact"):]
    if "debug_out/*/shots" not in artifact or "debug_out/*/run.log" not in artifact:
        raise AssertionError("artifact workflow tidak mengunggah shots/ dan "
                             "run.log")
    if "GITHUB_STEP_SUMMARY" not in workflow:
        raise AssertionError("%s tidak menulis ringkasan ke GITHUB_STEP_SUMMARY"
                             % WORKFLOW.name)
    print("[workflow] %d flag CLI dikenal · artifact dari %s · ringkasan "
          "Summary aktif" % (len(used), out_dir.group(1)))


def check_gdscript_contract() -> None:
    run_gd = read(RUN_GD)
    probe_gd = read(PROBE_GD)
    tool = load_tool()

    branches = gd_match_keys(run_gd, "match key:")
    missing = [key for key in tool.ENGINE_ARGS if key not in branches]
    extra = [key for key in branches if key not in tool.ENGINE_ARGS]
    if missing or extra:
        raise AssertionError(
            "cabang `match key:` DebugRun.gd tidak sama dengan ENGINE_ARGS "
            "(kurang: %s · lebih: %s)" % (missing or "-", extra or "-"))
    if "get_cmdline_user_args" not in run_gd:
        raise AssertionError("DebugRun.gd tidak membaca OS.get_cmdline_user_args()")

    # Tiap skenario harus benar-benar dipakai di cabang, bukan cuma di daftar.
    for name in tool.SCENARIOS:
        body = run_gd.replace(re.search(r"const SCENARIOS[^\]]*\]", run_gd,
                                       re.S).group(0), "")
        if '"%s"' % name not in body:
            raise AssertionError("skenario '%s' ada di daftar tapi tidak "
                                 "dipakai di cabang mana pun" % name)

    # Baris lulus yang dicetak harness == yang diminta gerbang log.
    if tool.DEFAULT_EXPECT not in run_gd:
        raise AssertionError(
            "harness tidak mencetak '%s' yang ditunggu gerbang log "
            "(DEFAULT_EXPECT di %s)" % (tool.DEFAULT_EXPECT, TOOL.name))

    # Berkas yang ditulis probe == yang diunggah workflow & dirapikan Python.
    for name in ("report.json", "shots", "run.log", "summary.md"):
        if name not in probe_gd and name not in read(TOOL) :
            raise AssertionError("tidak ada kode yang menulis '%s'" % name)
    if "frame_%04d.png" not in probe_gd:
        raise AssertionError("DebugProbe.gd tidak menamai screenshot "
                             "frame_NNNN.png")
    if "frame_post_draw" not in probe_gd:
        raise AssertionError("DebugProbe.gd tidak menunggu "
                             "RenderingServer.frame_post_draw (screenshot "
                             "bisa balapan dengan renderer)")
    print("[harness] %d kunci argumen tercabang · %d skenario terpakai · "
          "PASS-line + frame_post_draw ada" % (len(branches),
                                               len(tool.SCENARIOS)))


def check_outputs_and_gitignore() -> None:
    tool = load_tool()
    source = read(TOOL)
    gitignore = read(GITIGNORE)

    if '"debug_out"' not in source or "def default_out()" not in source:
        raise AssertionError("direktori default alat bukan debug_out/")
    if not re.search(r"^debug_out/\s*$", gitignore, re.M):
        raise AssertionError(
            ".gitignore tidak menutup `debug_out/` — screenshot/report debug "
            "akan ikut ter-commit")

    # Aset biner (sounds/items/presplash, gitignored) harus siap SEBELUM
    # engine dijalankan, kalau tidak item icon jadi badge prosedural.
    if '"--assets"' not in source:
        raise AssertionError("alat tidak memanggil `convert_to_godot.py --assets`")
    if source.index("copy_assets(") > source.index("run_engine(cmd"):
        raise AssertionError("penyalinan aset terjadi SESUDAH engine dijalankan")
    if "MYSTIC_NO_SPLASH" not in source:
        raise AssertionError("alat tidak menyetel MYSTIC_NO_SPLASH=1 (boot "
                             "langsung ke menu; skenario menu/level/… jadi "
                             "lebih pendek dan bisa diprediksi)")
    if "XDG_DATA_HOME" not in source:
        raise AssertionError("alat tidak mengisolasi XDG_DATA_HOME — debug run "
                             "bisa mengubah save pemain")
    for name in ("run.log", "report.json", "summary.md", "shots"):
        if name not in source:
            raise AssertionError("alat tidak menyebut keluaran '%s'" % name)
    print("[keluaran] debug_out/ di-gitignore · aset sebelum engine · "
          "userdata terisolasi · log+report+summary+shots lengkap")


def check_files_and_devcontainer() -> None:
    tool = load_tool()
    scene = tool.DEBUG_SCENE  # res://…
    on_disk = ROOT / "godot" / scene.replace("res://", "")
    if not on_disk.exists():
        raise AssertionError("DEBUG_SCENE %s tidak ada di disk" % scene)
    tscn = read(RUN_TSCN)
    for script in ("res://scenes/debug/DebugRun.gd",
                   "res://scenes/debug/DebugProbe.gd"):
        if script not in tscn:
            raise AssertionError("%s tidak memasang %s" % (RUN_TSCN.name, script))

    # Devcontainer (Codespaces) harus ada dan tidak boleh menua sendiri:
    # versi Godot-nya = env GODOT_VERSION default workflow.
    raw = read(DEVCONTAINER)
    # devcontainer.json mengizinkan komentar // (JSONC); json.loads tidak.
    stripped = re.sub(r"^\s*//.*$", "", raw, flags=re.M)
    try:
        data = json.loads(stripped)
    except ValueError as exc:
        raise AssertionError("devcontainer.json bukan JSON yang sah: %s" % exc)
    if not DEVCONTAINER_SETUP.exists():
        raise AssertionError("devcontainer.json menunjuk setup.sh yang tidak ada")
    setup = read(DEVCONTAINER_SETUP)
    workflow = read(WORKFLOW)
    version = re.search(r"GODOT_VERSION:\s*\$\{\{\s*inputs\.godot_version\s*\|\|\s*'([0-9.]+)'",
                        workflow)
    if not version:
        raise AssertionError("tidak menemukan default GODOT_VERSION di %s"
                             % WORKFLOW.name)
    if "GODOT_VERSION=\"%s\"" % version.group(1) not in setup:
        raise AssertionError(
            "versi Godot devcontainer != default workflow (%s) — samakan "
            "supaya 'berhasil di Codespace' berarti 'berhasil di CI'"
            % version.group(1))
    if "postCreateCommand" not in json.dumps(data):
        raise AssertionError("devcontainer.json tidak menyiapkan apa pun "
                             "(postCreateCommand)")
    print("[berkas] scene+probe ada · devcontainer ada · versi Godot "
          "devcontainer == workflow (%s)" % version.group(1))


def documentasi_cek_ok(sumber: str) -> bool:
    """Apakah hasil kompilasi skrip benar-benar ikut menentukan lulus/gagal?"""
    return "    ok = scripts_ok and marker_ok" in sumber


def check_preflight() -> None:
    """Scene penanda harus benar-benar bebas dari API game.

    Preflight hanya berguna sebagai pembanding kalau ia TIDAK bisa gagal karena
    alasan yang sama dengan harness: tanpa autoload, tanpa grup, tanpa panggilan
    dinamis. Kalau suatu hari ia memakai GameManager, preflight kehilangan
    maknanya (dua-duanya gagal bersamaan, dan penyebabnya kembali ambigu).
    """
    tool = load_tool()
    sumber = read(TOOL)
    # Preflight bagian 1: kompilasi skrip debug oleh engine yang sama dengan
    # run. Tanpa langkah ini, API yang tidak ada di versi engine (4.4 di 4.3)
    # baru ketahuan setelah run berjalan menit-menit lalu mati.
    # Dicari dengan tanda kutip supaya yang terdeteksi adalah PERINTAH yang
    # benar-benar dijalankan, bukan penyebutan di komentar/dokstring.
    if '"--check-only"' not in sumber or 'scripts_ok, lines, gagal = check_scripts(' not in sumber:
        raise AssertionError("preflight tidak mengompilasi skrip debug "
                             "(--check-only) — trap versi API kembali tak "
                             "terjaga")
    if not documentasi_cek_ok(sumber):
        raise AssertionError("preflight tidak menjadikan hasil kompilasi "
                             "sebagai syarat lulus (scripts_ok)")
    for script in tool.CHECK_SCRIPTS:
        berkas = ROOT / "godot" / script.replace("res://", "")
        if not berkas.exists():
            raise AssertionError("preflight memeriksa %s, yang tidak ada di "
                                 "disk" % script)
    wajib = {"res://scenes/debug/DebugRun.gd", "res://scenes/debug/DebugProbe.gd"}
    hilang = sorted(wajib - set(tool.CHECK_SCRIPTS))
    if hilang:
        raise AssertionError("CHECK_SCRIPTS tidak memeriksa %s — skrip itu bisa "
                             "bisu tanpa ketahuan" % ", ".join(hilang))
    if "passed = gate_ok and rc == 0 and preflight_ok" not in sumber:
        raise AssertionError("hasil preflight tidak ikut menentukan PASS/FAIL "
                             "run — preflight yang gagal bisa lolos diam-diam")
    scene = tool.MARKER_SCENE  # res://…
    on_disk = ROOT / "godot" / scene.replace("res://", "")
    if not on_disk.exists():
        raise AssertionError("MARKER_SCENE %s tidak ada di disk" % scene)
    tscn = read(MARKER_TSCN)
    if "res://scenes/debug/DebugMarker.gd" not in tscn:
        raise AssertionError("%s tidak menunjuk DebugMarker.gd"
                             % MARKER_TSCN.name)
    # Komentar boleh menyebut API game (mis. "tanpa get_first_node_in_group");
    # yang diperiksa adalah kodenya.
    gd = "\n".join(line.split("#", 1)[0]
                   for line in read(MARKER_GD).splitlines())
    for terlarang, kenapa in (("GameManager", "autoload game"),
                              ("get_first_node_in_group", "panggilan dynamic"),
                              ("get_tree().get_first_node", "grup node game"),
                              ("AppShell", "autoload game")):
        if terlarang in gd:
            raise AssertionError(
                "DebugMarker.gd memakai %s (%s) — preflight jadi ikut gagal "
                "saat masalahnya justru di skrip game" % (terlarang, kenapa))
    if "[DebugMarker] PASS" not in gd:
        raise AssertionError("DebugMarker.gd tidak mencetak baris PASS yang "
                             "dicari preflight")
    print("[preflight] 2 bagian terkunci: kompilasi skrip (--check-only) + "
          "scene penanda tanpa API game; hasilnya menentukan PASS/FAIL")


def check_docs() -> None:
    doc = read(DOC)
    for needle in (".github/workflows/godot-run.yml",
                   "tools/godot_debug_run.py",
                   "scenes/debug/DebugRun.tscn",
                   ".devcontainer/devcontainer.json"):
        if needle not in doc:
            raise AssertionError("dokumen %s tidak menyebut %s"
                                 % (DOC.name, needle))
    read(ROOT / "godot" / "tools" / "godot_log_gate.py")  # dipakai sebagai gerbang
    print("[dokumen] %s menyebut workflow, alat, scene, dan devcontainer"
          % DOC.name)


def check_resiliensi() -> None:
    """Kegagalan "menggantung" harus selalu meninggalkan bukti yang bisa dibaca."""
    source = read(TOOL)
    run_gd = read(RUN_GD)
    workflow = read(WORKFLOW)

    if "start_new_session" not in source or "killpg" not in source:
        raise AssertionError(
            "alat tidak membunuh seluruh process group saat rem darurat aktif — "
            "di mode xvfb, `proc.kill()` hanya membunuh skrip xvfb-run")
    if "stdbuf" not in source:
        raise AssertionError(
            "alat tidak menjalankan engine dengan stdbuf: stdout Godot "
            "ter-buffer blok, jadi log hilang begitu proses dibunuh")
    for token, why in (("trace.log", "jejak boot yang di-flush ke berkas"),
                       ("BOOT_DEADLINE", "batas boot di dalam engine"),
                       ("flush()", "flush tiap baris jejak")):
        if token not in run_gd:
            raise AssertionError("DebugRun.gd tidak punya %s (%s)" % (token, why))
    for berkas in ("trace.log", "preflight.log"):
        if berkas not in workflow:
            raise AssertionError("artifact workflow tidak mengunggah %s — "
                                 "jejak kegagalan hilang bersama runner"
                                 % berkas)
    print("[ketahanan] process group dibunuh · stdbuf (log tak tertahan) · "
          "trace.log + batas boot ikut artifact")
    return


def check_watchdog() -> None:
    """Rem darurat harus membunuh pembungkus + enginenya, bukan cuma pembungkus.

    Bentuk `xvfb-run` = skrip shell yang menjalankan perintah sebagai ANAK.
    `Popen.kill()` biasa hanya membunuh skripnya; anaknya tetap menulis ke pipa
    stdout kita, jadi `run_engine` ikut menunggu sampai anak itu selesai sendiri
    (inilah kenapa run 30 detik pernah berjalan 9 menit di CI). Stub di bawah
    meniru bentuk itu tanpa Godot: anaknya hidup 40 detik kalau tidak dibunuh.
    """
    tool = load_tool()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        wrapper = tmp_path / "wrap.sh"
        wrapper.write_text(
            "#!/usr/bin/env bash\n"
            "# Meniru xvfb-run: pembungkus + anak yang menulis ke stdout.\n"
            "$0-child &\n"
            "wait\n",
            encoding="utf-8")
        child = tmp_path / "wrap.sh-child"
        child.write_text(
            "#!/usr/bin/env bash\n"
            "for i in $(seq 1 40); do echo \"anak masih hidup $i\"; sleep 1; done\n",
            encoding="utf-8")
        wrapper.chmod(0o755)
        child.chmod(0o755)

        out = tmp_path / "out"
        out.mkdir()
        started = time.time()
        # Keluaran stub ditelan: yang penting waktunya, bukan echo-nya di log CI.
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            rc = tool.run_engine([str(wrapper)], out, os.environ.copy(),
                                 timeout=2.0)
        elapsed = time.time() - started

    if rc != 124:
        raise AssertionError("rem darurat tidak melaporkan 124 (rc=%s)" % rc)
    if elapsed > 20.0:
        raise AssertionError(
            "rem darurat tidak membunuh seluruh process group: dibutuhkan "
            "%.1f detik untuk timeout 2 detik — anak pembungkus (seperti Godot "
            "di dalam xvfb-run) masih hidup" % elapsed)
    print("[watchdog] --timeout %.0fs → berhenti %.1fs (process group dibunuh, "
          "tanpa proses yatim)" % (2.0, elapsed))


## API engine yang BARU ada setelah 4.3 — versi yang dipakai CI
## (godot-check.yml) dan devcontainer. Memanggilnya langsung dari skrip debug
## membuat run gagal di engine 4.3 (parse error atau "Invalid call"), dan
## gejalanya persis "harness bisu": gdparse tidak melihatnya karena
## sintaksnya benar.
API_TERLALU_BARU = {
    "get_current_rendering_method": "4.4",
    "get_current_rendering_driver_name": "4.4",
}


def check_api_versi() -> None:
    """Skrip debug tidak boleh memanggil API yang belum ada di engine CI (4.3).

    Info renderer yang hanya ada di versi baru (mis. RenderingServer
    .get_current_rendering_method) harus diambil lewat helper yang memeriksa
    `has_method` dulu — lihat `DebugProbe._server_field()`. Di 4.3 helper itu
    hanya menuliskan "?" alih-alih menggagalkan seluruh skrip.
    """
    for berkas in (RUN_GD, PROBE_GD, MARKER_GD):
        kode = "\n".join(line.split("#", 1)[0]
                         for line in read(berkas).splitlines())
        for api, versi in API_TERLALU_BARU.items():
            if re.search(r"RenderingServer\s*\.\s*%s\s*\(" % api, kode):
                raise AssertionError(
                    "%s memanggil RenderingServer.%s() langsung — API itu baru "
                    "ada di Godot %s, sedangkan CI memakai 4.3: skripnya tidak "
                    "bisa dikompilasi / gagal saat runtime. Pakai helper "
                    "has_method + call (lihat DebugProbe._server_field)"
                    % (berkas.name, api, versi))
    probe = read(PROBE_GD)
    if "_server_field" not in probe or "has_method(method)" not in probe:
        raise AssertionError(
            "DebugProbe.gd tidak mengambil info renderer lewat helper "
            "has_method — penjaga versi API hilang")
    print("[api] tidak ada API 4.4+ yang dipanggil langsung; info renderer "
          "lewat has_method + call (aman di 4.3 dan 4.4+)")


def check_panggilan_dinamis() -> None:
    """Konvensi jalur debug: panggilan dinamis lewat `has_method(...)` dulu.

    `get_first_node_in_group()` bertipe `Node`, jadi memanggil method di luar
    Node BUKAN kesalahan sintaks (gdparse lolos) — dan bukan pula kesalahan
    kompilasi: `scenes/main/Main.gd` memakai pola bertipe sama dan lolos CI.
    Yang benar-benar terjadi kalau nama method-nya salah (atau scene-nya bukan
    main.tscn): engine mencetak `Invalid call. Nonexistent function … in base
    Node` — satu baris SCRIPT ERROR yang membuat gerbang log menolak run,
    padahal yang diuji cuma jalur debug. Karena itu pola tests/*.gd
    (`has_method(...)` lebih dulu) diwajibkan di sini.
    """
    node_methods = {"has_method"}
    for berkas in (RUN_GD, PROBE_GD):
        source = read(berkas)
        # Perhatikan: RHS-nya `get_tree().get_first_node_in_group(...)`, jadi
        # polanya tidak boleh menempel ketat setelah `:=`.
        for var in re.findall(
                r"var\s+(\w+)\s*:=\s*[^\n]*get_first_node_in_group\(",
                source):
            dipanggil = set(re.findall(r"\b%s\.(\w+)\(" % re.escape(var),
                                       source)) - node_methods
            kurang = sorted(m for m in dipanggil
                            if 'has_method("%s")' % m not in source)
            if kurang:
                raise AssertionError(
                    "%s: %s.%s() dipanggil tanpa has_method(...) — kalau "
                    "method-nya tidak ada, engine menulis SCRIPT ERROR "
                    "('Invalid call. Nonexistent function') yang membuat "
                    "gerbang log menolak run"
                    % (berkas.name, var, kurang[0]))
    print("[kompilasi] panggilan dynamic dari get_first_node_in_group selalu "
          "lewat has_method (konvensi Main.gd/tests)")


def check_wiring() -> None:
    workflow = read(CHECK_WORKFLOW)
    if "tools/test_godot_debug_runner.py" not in workflow:
        raise AssertionError(
            "godot-check.yml tidak memanggil tools/test_godot_debug_runner.py "
            "— gate ini bisa dihapus tanpa ada yang protes")
    paths = workflow[:workflow.index("jobs:")]
    for path in ("tools/godot_debug_run.py", "tools/test_godot_debug_runner.py",
                 ".github/workflows/godot-run.yml"):
        if "'%s'" % path not in paths:
            raise AssertionError("filter `paths` godot-check.yml tidak memantau "
                                 "%s (perubahan jalur debug tidak akan diuji)"
                                 % path)
    print("[wiring] godot-check.yml memanggil gate ini + memantau berkas "
          "jalur debug")


def main() -> int:
    check_contract_lists()
    check_workflow_flags()
    check_gdscript_contract()
    check_outputs_and_gitignore()
    check_files_and_devcontainer()
    check_docs()
    check_wiring()
    check_resiliensi()
    check_preflight()
    check_api_versi()
    check_panggilan_dinamis()
    check_watchdog()
    print("Godot debug runner: OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print("FAIL: %s" % exc)
        sys.exit(1)
