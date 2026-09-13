#!/usr/bin/env python3
"""godot_debug_run — JALANKAN project Godot untuk debug, di laptop atau di CI.

KENAPA ADA
==========
Sebelum ini, "coba jalankan port Godot" hanya bisa dijawab dengan salah satu
dari dua cara yang dua-duanya mahal:

  * memasang Godot + GPU + X11 di mesin sendiri (tidak mungkin di server tanpa
    layar, dan tidak bisa dilakukan dari halaman GitHub), atau
  * membuka `.github/workflows/godot-check.yml` — 60+ langkah paritas yang
    butuh ±10 menit, TIDAK menampilkan layar, dan gagal/berhasil hanya
    memberi tahu "ada yang salah" tanpa gambar.

Alat ini mengisi celah itu: satu perintah (atau satu klik di tab Actions) yang

  1. menyiapkan aset biner yang di-gitignore (sounds/items/presplash),
  2. mengimpor project sekali,
  3. menjalankan scene lewat **Xvfb** (layar virtual) dengan skenario yang bisa
     dipilih — menu / level / battle / shop / scene apa pun,
  4. merekam **PNG tiap N detik + report.json** lewat harness dalam-engine
     `res://scenes/debug/DebugRun.tscn` (lihat godot/scenes/debug/DebugRun.gd),
     opsional **video** lewat `--write-movie` milik engine,
  5. menjalankan **gerbang log** yang sama dengan CI
     (`godot/tools/godot_log_gate.py`) supaya SCRIPT ERROR / Parse Error
     tidak pernah lolos hanya karena exit code Godot 0.

Semua keluaran masuk ke satu direktori (`debug_out/…`, di-gitignore) yang di
CI langsung diunggah sebagai artifact — jadi hasil debug bisa dilihat tanpa
memasang apa pun.

CONTOH
======
    # Lihat menu utama, ambil 1 screenshot tiap detik, 20 detik (paling ringan)
    python3 tools/godot_debug_run.py --scenario menu --seconds 20

    # Level 3: intro dilewati, hero dibeli, wave berjalan
    python3 tools/godot_debug_run.py --scenario battle --level 3 --seconds 40

    # Layar toko (ITEM/HERO/MENARA/NEXUS) — debugging UI in-match
    python3 tools/godot_debug_run.py --scenario shop --level 1 --seconds 25

    # Scene uji/test apa pun, headless (tanpa layar, tanpa screenshot)
    python3 tools/godot_debug_run.py --scenario scene \
        --scene res://tests/BattleSmokeTest.tscn --display headless \
        --expect "[BattleSmokeTest] PASS"

    # Video 15 fps dari run 20 detik (ffmpeg mengubahnya jadi .mp4)
    python3 tools/godot_debug_run.py --scenario battle --seconds 20 --movie

CATATAN JUJUR
=============
  * Screenshot BUTUH konteks render. `--display headless` (display driver
    dummy) tidak bisa menghasilkan gambar — report.json menulis
    `headless: true` dan tidak ada berkas di `shots/`. Gerbang log tetap jalan.
  * Di CI dipakai **gl_compatibility + OpenGL software (llvmpipe)** karena
    runner tidak punya GPU. Tata letak UI, teks, dan posisi sama; pencampuran
    cahaya/glow bisa sedikit berbeda dari Forward+ desktop. Untuk bug "render
    meleset", jalankan lokal dengan `--renderer vulkan`.
  * `--seconds` SELALU detik jam dinding. Game-nya sendiri bisa lebih lambat:
    `Engine.time_scale` (hit-stop hero/boss 0.05, setting Game Speed 0.5x-2x)
    mengalikan `delta`, jadi "30 detik game" bisa jauh lebih panjang dari 30
    detik nyata — laporan menulis kedua angka (`elapsed` vs `elapsed_game`).
    `--fixed-fps` (movie) tidak mengubah batas ini: video bisa jadi lebih
    pendek dari `--seconds` kalau mesinnya lambat.

KONTRAK
=======
Nama skenario dan kunci argumen engine di bawah ini adalah SATU-SATUNYA
sumber kebenaran; `godot/scenes/debug/DebugRun.gd` dan workflow
`.github/workflows/godot-run.yml` harus memakai daftar yang sama — dijaga oleh
`python3 tools/test_godot_debug_runner.py` (tanpa engine, hitungan detik).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "godot"
CONVERTER = ROOT / "tools" / "convert_to_godot.py"
LOG_GATE = ROOT / "godot" / "tools" / "godot_log_gate.py"
DEBUG_SCENE = "res://scenes/debug/DebugRun.tscn"
## Scene penanda preflight — sengaja tanpa API game (lihat DebugMarker.gd).
MARKER_SCENE = "res://scenes/debug/DebugMarker.tscn"
MAIN_SCENE = "res://scenes/main.tscn"

## Nama skenario — HARUS sama dengan DebugRun.gd SCENARIOS + dropdown workflow.
SCENARIOS = ("menu", "level", "battle", "shop", "scene")
## Argumen yang diteruskan ke engine setelah `--` (OS.get_cmdline_user_args()).
## HARUS sama dengan DebugRun.gd ARG_KEYS.
ENGINE_ARGS = (
    "scenario",
    "scene",
    "level",
    "seconds",
    "shot-every",
    "max-shots",
    "max-frames",
    "fps",
    "out",
    "label",
)

DEFAULT_GODOT_VERSION = "4.3"
DEFAULT_SECONDS = 30.0
DEFAULT_SHOT_EVERY = 1.0
DEFAULT_MAX_SHOTS = 40
DEFAULT_FIXED_FPS = 15
DEFAULT_EXPECT = "[DebugRun] PASS"
## Cadangan frame sebelum engine menyerah sendiri kalau harness macet.
QUIT_AFTER_SLACK = 300

ENGINE_URL = ("https://github.com/godotengine/godot/releases/download/"
              "{version}/Godot_v{version}_linux.x86_64.zip")


# ══════════════════════════════════════════════════════════════════════════
#  ARGUMEN
# ══════════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="godot_debug_run",
        description="Jalankan project Godot (godot/) untuk debug + rekam "
                    "screenshot/report, lokal maupun di GitHub Actions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Kunci argumen engine: " + ", ".join(ENGINE_ARGS),
    )
    p.add_argument("--scenario", choices=SCENARIOS, default="menu",
                   help="menu (boot apa adanya) · level (mulai match) · "
                        "battle (level + beli hero) · shop (level + buka toko) "
                        "· scene (scene apa adanya)")
    p.add_argument("--scene", default="", metavar="res://…",
                   help="scene yang dijalankan (default res://scenes/main.tscn)")
    p.add_argument("--level", type=int, default=1, help="nomor level (1-54)")
    p.add_argument("--seconds", type=float, default=DEFAULT_SECONDS,
                   help="lama run (detik); 0 = tanpa batas waktu")
    p.add_argument("--shot-every", type=float, default=None, metavar="DETIK",
                   help=f"jarak antar screenshot (default {DEFAULT_SHOT_EVERY}); "
                        "0 = tanpa screenshot")
    p.add_argument("--max-shots", type=int, default=DEFAULT_MAX_SHOTS,
                   help="batas jumlah screenshot (jaga ukuran artifact)")
    p.add_argument("--fps", type=int, default=0,
                   help="batas FPS lewat AppShell.apply_fps_limit (0 = "
                        "biarkan AppShell memutuskan; diabaikan saat headless)")
    p.add_argument("--label", default="", help="nama run untuk report.json")
    p.add_argument("--display", choices=("auto", "x11", "xvfb", "headless"),
                   default="auto",
                   help="auto (pakai $DISPLAY kalau ada, lalu Xvfb, lalu "
                        "headless) · x11 (layar yang ada) · xvfb (layar "
                        "virtual) · headless (tanpa layar, tanpa screenshot)")
    p.add_argument("--renderer", choices=("opengl3", "vulkan"),
                   default="opengl3",
                   help="opengl3 (gl_compatibility + software GL, aman di CI) "
                        "· vulkan (Forward+ sungguhan, butuh GPU/lavapipe)")
    p.add_argument("--movie", action="store_true",
                   help="rekam video lewat --write-movie (Movie Maker, "
                        "--fixed-fps, tanpa audio)")
    p.add_argument("--fixed-fps", type=int, default=DEFAULT_FIXED_FPS,
                   help="FPS rekaman movie (default 15; makin kecil makin "
                        "ringan, gerak makin patah)")
    p.add_argument("--godot", default="", metavar="PATH",
                   help="binary Godot (default: $MYSTIC_GODOT, lalu `godot` "
                        "di PATH, lalu unduh bila --download)")
    p.add_argument("--godot-version", default=DEFAULT_GODOT_VERSION,
                   help=f"versi yang diunduh oleh --download "
                        f"(default {DEFAULT_GODOT_VERSION})")
    p.add_argument("--download", action="store_true",
                   help="unduh binary Godot ke cache kalau tidak ditemukan")
    p.add_argument("--out", default="", metavar="DIR",
                   help="direktori keluaran (default debug_out/<stempel waktu>)")
    p.add_argument("--expect", default=DEFAULT_EXPECT,
                   help="baris wajib di log (kosong = hanya cek error)")
    p.add_argument("--no-preflight", action="store_true",
                   help="lewati uji penanda (engine+scene dari repo) sebelum "
                        "run sungguhan")
    p.add_argument("--no-gate", action="store_true",
                   help="jangan jalankan gerbang log (untuk menguji alat ini)")
    p.add_argument("--touch", action="store_true",
                   help="MYSTIC_FORCE_TOUCH=1 — uji tata letak HP di desktop")
    p.add_argument("--splash", action="store_true",
                   help="biarkan splash screen boot berjalan (default: "
                        "MYSTIC_NO_SPLASH=1 supaya langsung ke menu)")
    p.add_argument("--no-assets", action="store_true",
                   help="jangan salin aset biner (sounds/items/presplash)")
    p.add_argument("--no-import", action="store_true",
                   help="jangan jalankan `godot --import` walau .godot/ kosong")
    p.add_argument("--force-import", action="store_true",
                   help="jalankan `godot --import` apa pun keadaannya")
    p.add_argument("--timeout", type=float, default=0.0,
                   help="rem darurat detik (default: max(--seconds*4 + 120, "
                        "300) — harness keluar sendiri jauh sebelum ini)")
    p.add_argument("--extra", action="append", default=[], metavar="ARG",
                   help="argumen tambahan untuk engine (boleh diulang)")
    p.add_argument("--dry-run", action="store_true",
                   help="cetak perintah yang akan dijalankan, tidak menjalankan")
    return p


# ══════════════════════════════════════════════════════════════════════════
#  BINARY GODOT
# ══════════════════════════════════════════════════════════════════════════

def cache_dir(version: str) -> Path:
    base = (os.environ.get("MYSTIC_GODOT_CACHE")
            or str(Path.home() / ".cache" / "mystic-arena"))
    return Path(base) / f"godot-{version}"


def download_godot(version: str) -> Path:
    """Unduh Godot linux-x86_64 ke cache (URL sama dengan godot-check.yml)."""
    target = cache_dir(version) / "godot"
    if target.exists():
        print(f"[aset] Godot {version} sudah ada: {target}")
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    url = ENGINE_URL.format(version=version)
    print(f"[aset] unduh {url}")
    zip_path = target.parent / "godot.zip"
    with urllib.request.urlopen(url, timeout=300) as resp, zip_path.open("wb") as fh:
        shutil.copyfileobj(resp, fh)
    with zipfile.ZipFile(zip_path) as zf:
        member = next(n for n in zf.namelist()
                      if n.startswith("Godot_v") and not n.endswith("/"))
        with zf.open(member) as src, target.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    target.chmod(0o755)
    zip_path.unlink(missing_ok=True)
    print(f"[aset] Godot siap: {target}")
    return target


def resolve_godot(args: argparse.Namespace) -> Path | None:
    for cand in (args.godot, os.environ.get("MYSTIC_GODOT", "")):
        if cand:
            path = Path(cand).expanduser()
            if path.exists():
                return path
            print(f"[aset] PERINGATAN: --godot {cand} tidak ada; dilewati")
    found = shutil.which("godot") or shutil.which("godot4")
    if found:
        return Path(found)
    if args.download:
        return download_godot(args.godot_version)
    return None


# ══════════════════════════════════════════════════════════════════════════
#  PERSIAPAN PROJECT
# ══════════════════════════════════════════════════════════════════════════

def copy_assets(out_dir: Path) -> None:
    """sounds/items/presplash ada di .gitignore -> disalin tiap clone.

    Memakai converter yang sudah ada (`--assets` hanya butuh os+shutil, tidak
    perlu pygame/numpy) supaya daftar berkasnya tidak pernah diduplikasi.
    """
    print("[aset] python3 tools/convert_to_godot.py --assets")
    res = subprocess.run([sys.executable, str(CONVERTER), "--assets"],
                         cwd=str(ROOT), capture_output=True, text=True)
    (out_dir / "assets.log").write_text(res.stdout + res.stderr, encoding="utf-8")
    if res.returncode != 0:
        print(res.stdout[-2000:])
        print(res.stderr[-2000:], file=sys.stderr)
        raise SystemExit("[aset] GAGAL menyalin aset biner (lihat assets.log)")
    for line in [ln for ln in res.stdout.splitlines() if ln.strip()][-3:]:
        print("       " + line)


def import_project(godot: Path, out_dir: Path, env: dict, force: bool) -> None:
    if not (force or not (PROJECT / ".godot").exists()):
        print("[import] godot/.godot sudah ada — dilewati "
              "(--force-import untuk memaksa)")
        return
    cmd = [str(godot), "--headless", "--path", "godot", "--import"]
    print("[import] " + " ".join(cmd))
    with (out_dir / "import.log").open("w", encoding="utf-8") as log:
        subprocess.run(cmd, cwd=str(ROOT), env=env, stdout=log,
                       stderr=subprocess.STDOUT, text=True)
    print("[import] selesai — log: import.log")
    # Exit code import tidak bisa dipercaya (lihat komentar godot-check.yml):
    # yang menilai adalah gerbang log pada log run-nya nanti.


# ══════════════════════════════════════════════════════════════════════════
#  PREFLIGHT (engine + scene dari repo)
# ══════════════════════════════════════════════════════════════════════════

## Rem preflight: scene penanda hanya butuh beberapa detik; angka ini jaring
## kalau engine menggantung SEBELUM run sungguhan dimulai.
PREFLIGHT_TIMEOUT = 90.0


def preflight(godot: Path, out_dir: Path, env: dict,
              timeout: float = PREFLIGHT_TIMEOUT) -> bool:
    """Buktikan dulu engine ini bisa menjalankan scene dari repo.

    Hanya butuh satu start headless beberapa detik, tetapi memisahkan tiga
    penyebab yang di artifact terlihat sama (harness sunyi lalu mati di rem
    darurat): skrip debug gagal dikompilasi, scene tidak dijalankan engine, atau
    engine tidak bisa membuka project. Dijalankan TANPA Xvfb supaya tetap murah.
    """
    marker = out_dir / "marker.txt"
    marker.unlink(missing_ok=True)
    cmd = [str(godot), "--headless", "--path", "godot", MARKER_SCENE, "--",
           f"--out={out_dir}"]
    if shutil.which("stdbuf"):
        cmd = ["stdbuf", "-oL", "-eL"] + cmd
    print("[preflight] " + " ".join(cmd))
    try:
        res = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True,
                             text=True, timeout=timeout)
        out = (res.stdout or "") + (res.stderr or "")
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") + (exc.stderr or "") if isinstance(
            exc.stdout, str) else ""
        out += "\n[preflight] TIMEOUT %.0f detik\n" % timeout
    except OSError as exc:
        out = "[preflight] gagal menjalankan engine: %s\n" % exc
    (out_dir / "preflight.log").write_text(out, encoding="utf-8")
    ok = marker.exists() and "[DebugMarker] PASS" in out
    if ok:
        print("[preflight] OK — engine menjalankan scene dari repo")
    else:
        print("[preflight] GAGAL — engine tidak menyelesaikan penanda; "
              "lihat preflight.log")
        for line in out.splitlines()[-12:]:
            print("       | " + line)
    return ok


# ══════════════════════════════════════════════════════════════════════════
#  PERINTAH ENGINE
# ══════════════════════════════════════════════════════════════════════════

def engine_args(args: argparse.Namespace, out_dir: Path, scene: str,
                max_frames: int, fps: int) -> list[str]:
    shot_every = DEFAULT_SHOT_EVERY if args.shot_every is None else args.shot_every
    values = {
        "scenario": args.scenario,
        "scene": scene,
        "level": args.level,
        "seconds": args.seconds,
        "shot-every": shot_every,
        "max-shots": args.max_shots,
        "max-frames": max_frames,
        "fps": fps,
        "out": str(out_dir),
        "label": args.label or args.scenario,
    }
    return [f"--{key}={values[key]}" for key in ENGINE_ARGS]


def build_command(args: argparse.Namespace, godot: Path, out_dir: Path,
                  scene: str, display: str) -> tuple[list[str], int, int]:
    """Kembalikan (perintah, max_frames, fps yang benar-benar dikirim)."""
    max_frames = 0
    if args.movie and args.seconds > 0:
        # Movie Maker memaksa --fixed-fps: batas frame dipakai sebagai jaring
        # kedua, tetapi batas utama tetap detik jam dinding (harness).
        max_frames = int(args.seconds * args.fixed_fps) + args.fixed_fps

    fps = args.fps if (args.fps > 0 and display != "headless") else 0
    if args.fps > 0 and fps == 0:
        print("[siap] PERINGATAN: --fps diabaikan saat headless "
              "(tanpa vsync, batas FPS hanya memperlambat run berbasis frame)")

    opts: list[str] = [str(godot), "--path", "godot"]
    # stdbuf: Godot menulis lewat stdio, dan saat stdout-nya pipa (CI), libc
    # memakai buffer BLOK. Akibatnya: kalau proses dibunuh (rem darurat/CI
    # cancel), semua yang belum menembus 4 KB hilang dari run.log — persis
    # kejadian yang membuat kegagalan pertama sulit dibaca. Buffer baris
    # membuat setiap baris sampai ke berkas/log CI saat ditulis.
    if shutil.which("stdbuf"):
        opts = ["stdbuf", "-oL", "-eL"] + opts
    if display == "headless":
        opts.append("--headless")
    elif args.renderer == "vulkan":
        opts += ["--rendering-method", "forward_plus",
                 "--rendering-driver", "vulkan"]
    else:
        opts += ["--rendering-method", "gl_compatibility",
                 "--rendering-driver", "opengl3"]

    if args.movie:
        opts += ["--write-movie", str(out_dir / "movie.avi"),
                 "--fixed-fps", str(args.fixed_fps), "--disable-vsync"]
    if args.seconds > 0:
        # Rem darurat level engine: kalau harness macet, run tetap berakhir.
        frames = max_frames if max_frames > 0 else int(args.seconds * 60)
        opts += ["--quit-after", str(frames + QUIT_AFTER_SLACK)]
    opts += list(args.extra)
    opts.append(scene)
    opts.append("--")
    opts += engine_args(args, out_dir, scene, max_frames, fps)

    if display == "xvfb":
        opts = ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24"] + opts
    return opts, max_frames, fps


def run_engine(cmd: list[str], out_dir: Path, env: dict, timeout: float) -> int:
    log_path = out_dir / "run.log"
    print("[jalan] " + " ".join(cmd))
    killed = {"by": ""}
    with log_path.open("w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n\n")
        log.flush()
        # start_new_session: perintah dijalankan di process group sendiri.
        # Penting untuk mode xvfb — di sana argv[0] adalah skrip `xvfb-run`,
        # jadi `proc.kill()` hanya membunuh pembungkusnya, dan Godot yang
        # masih hidup terus menulis ke pipa kita (rem darurat jadi tidak
        # berfungsi: run 30 detik bisa berjalan 9 menit).
        proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace",
                                bufsize=1, start_new_session=True)

        def _watchdog() -> None:
            if proc.poll() is None:
                killed["by"] = "timeout"
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    proc.kill()

        timer = threading.Timer(timeout, _watchdog)
        timer.daemon = True
        timer.start()
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                log.write(line)
            log.flush()
            rc = proc.wait()
        finally:
            timer.cancel()
    if killed["by"]:
        print(f"\n[jalan] DIHENTIKAN: melewati batas {timeout:.0f} detik",
              file=sys.stderr)
        return 124
    print(f"[jalan] engine keluar dengan exit {rc}")
    return rc


# ══════════════════════════════════════════════════════════════════════════
#  GERBANG LOG + VIDEO
# ══════════════════════════════════════════════════════════════════════════

def run_gate(log_path: Path, label: str, expect: str) -> bool:
    cmd = [sys.executable, str(LOG_GATE), str(log_path), "--label", label]
    if expect:
        cmd += ["--require", expect]
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    out = (res.stdout + res.stderr).strip()
    print("[gerbang] " + ("\n[gerbang] ".join(out.splitlines()) if out
                          else "(tanpa keluaran)"))
    return res.returncode == 0


def make_video(out_dir: Path) -> str:
    """AVI Movie Maker -> MP4 kalau ffmpeg ada (kalau tidak, apa adanya)."""
    avi = out_dir / "movie.avi"
    if not avi.exists():
        return ""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("[video] ffmpeg tidak ada — movie.avi dibiarkan apa adanya")
        return avi.name
    mp4 = out_dir / "movie.mp4"
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(avi),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           str(mp4)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and mp4.exists():
        avi.unlink(missing_ok=True)
        print(f"[video] {mp4.name} ({mp4.stat().st_size / 1e6:.1f} MB)")
        return mp4.name
    print("[video] ffmpeg gagal — movie.avi dibiarkan apa adanya: "
          + (res.stderr or "").strip()[:300])
    return avi.name


# ══════════════════════════════════════════════════════════════════════════
#  RINGKASAN
# ══════════════════════════════════════════════════════════════════════════

def load_report(out_dir: Path) -> dict:
    path = out_dir / "report.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:  # laporan rusak jangan menutupi log
        print(f"[lapor] report.json tidak terbaca: {exc}")
        return {}


def harness_started(log_path: Path) -> bool:
    """Apakah skrip harness di dalam engine pernah jalan?

    Bedanya penting: `[DebugRun] PASS` yang hilang karena harness gagal
    DIKOMPILASI (analyzer GDScript menolak panggilan method di luar Node tanpa
    `has_method`) terlihat sama saja dengan harness yang macet. Kalau satu baris
    pun tidak ada, penyebabnya bukan skenario/level — dan itu harus dikatakan.
    """
    if not log_path.exists():
        return False
    try:
        return "[DebugRun]" in log_path.read_text(encoding="utf-8",
                                                   errors="replace")
    except OSError:
        return False


def write_summary(out_dir: Path, args: argparse.Namespace, report: dict,
                  shots: list[Path], video: str, gate_ok: bool, rc: int,
                  seconds_run: float, marker_ok: bool = True) -> Path:
    started = harness_started(out_dir / "run.log")
    ok = gate_ok and rc == 0 and marker_ok
    head = "LULUS" if ok else "GAGAL"
    lines = [
        f"# Godot Debug Run — {head}",
        "",
        "| | |",
        "|---|---|",
        f"| skenario | `{report.get('scenario', args.scenario)}` |",
        f"| scene | `{report.get('scene', args.scene or MAIN_SCENE)}` |",
        f"| level | {args.level} |",
        f"| tampilan | `{report.get('display_driver', '?')}` · "
        f"{report.get('rendering_method', '?')}/"
        f"{report.get('rendering_driver', '?')}"
        f"{' · HEADLESS' if report.get('headless') else ''} |",
        f"| engine | {report.get('engine', '?')} |",
        f"| lama | {seconds_run:.1f} detik nyata · {report.get('frames', '?')} "
        f"frame · jam game {report.get('elapsed_game', '?')} detik "
        f"(time_scale {report.get('time_scale', '?')}) |",
        f"| fps | rata-rata {report.get('fps_avg', '?')} · "
        f"min {report.get('fps_min', '?')} · maks {report.get('fps_max', '?')} |",
        f"| screenshot | {len(shots)} berkas |",
        f"| video | {video or '—'} |",
        f"| gerbang log | {'lulus' if gate_ok else 'GAGAL'} |",
        f"| exit engine | {rc} |",
        f"| preflight (engine+scene) | "
        f"{'OK' if marker_ok else 'GAGAL — lihat preflight.log'} |",
        f"| harness | {'jalan' if started else 'TIDAK PERNAH JALAN'} |",
        "",
    ]
    if not marker_ok:
        lines += [
            "> **Preflight GAGAL**: engine tidak bisa menjalankan scene",
            "> `scenes/debug/DebugMarker.tscn` (tanpa satu pun API game).",
            "> Jadi penyebabnya ada di engine/project, bukan di skenario debug:",
            "> lihat `preflight.log` (mis. `Parse Error`, project tidak",
            "> termuat, atau dependensi GL/X11 tidak ada).",
            "",
        ]
    if not started:
        lines += [
            "> **Harness tidak mencetak satu baris pun.** Artinya masalahnya ada",
            "> SEBELUM skenario dijalankan — bukan level/skenario:",
            ">",
            "> 1. skrip `scenes/debug/DebugRun.gd` gagal dikompilasi oleh engine:",
            ">    cari `Parse Error` / `SCRIPT ERROR` di `run.log`. Analyzer",
            ">    GDScript menolak panggilan method di luar `Node` tanpa",
            ">    `has_method(...)` (lihat komentar di `_start_match()`);",
            "> 2. scene tidak dijalankan sama sekali: lihat baris `$ …` pertama",
            ">    `run.log` (perintah yang benar-benar dipakai engine).",
            ">",
            f"> `trace.log` {'ada' if (out_dir / 'trace.log').exists() else 'tidak ada'}"
            " — kalau ada, baris terakhirnya menyebut tahap boot terakhir.",
            "",
        ]
    samples = report.get("samples") or []
    if samples:
        lines += ["## Cuplikan keadaan", "",
                  "| detik nyata | jam game | time_scale | fps | state | wave | "
                  "gold | hero biru | hero merah | minion |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for s in samples[:60]:
            lines.append(
                "| {t} | {t_game} | {time_scale} | {fps} | {state} | {wave} "
                "| {gold} | {blue} | {red} | {minions} |".format(
                    **{k: s.get(k, "")
                       for k in ("t", "t_game", "time_scale", "fps", "state",
                                 "wave", "gold", "blue", "red", "minions")}))
        lines.append("")
    if shots:
        lines += ["## Berkas", ""]
        lines += [f"- `shots/{s.name}`" for s in shots[:20]]
        if len(shots) > 20:
            lines.append(f"- … {len(shots) - 20} berkas lagi di artifact")
        lines.append("")
    lines += [
        "## Langkah berikutnya",
        "",
        "1. Unduh artifact run ini (tab **Artifacts**) — isinya `shots/`, "
        "`run.log`, `report.json`, "
        + ("`movie.mp4`, " if video else "") + "`summary.md`.",
        "2. `run.log` = keluaran engine apa adanya; baris `SCRIPT ERROR`, "
        "`Parse Error`, `[DebugRun] FAIL` adalah petunjuk pertama.",
        "3. Kolom `jam game` vs `detik nyata` menerangkan `Engine.time_scale` "
        "game (hit-stop/game speed): run bisa lebih lambat dari jam dinding, "
        "tapi batas run selalu dihitung dari jam dinding.",
        "4. Ulangi dengan skenario/level lain: tab Actions → "
        "**Godot Debug Run** → Run workflow.",
        "",
    ]
    path = out_dir / "summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ══════════════════════════════════════════════════════════════════════════
#  UTAMA
# ══════════════════════════════════════════════════════════════════════════

def default_out() -> Path:
    return ROOT / "debug_out" / time.strftime("run-%Y%m%d-%H%M%S")


def environment(args: argparse.Namespace, out_dir: Path, display: str) -> dict:
    env = dict(os.environ)
    # Save + setelan diisolasi ke dalam run: hasil debug tidak boleh mengubah
    # save pemain, dan sebaliknya save lama tidak boleh mengubah hasil debug.
    env["XDG_DATA_HOME"] = str(out_dir / "userdata")
    if sys.platform.startswith("win"):
        env["APPDATA"] = str(out_dir / "userdata")
    if not args.splash:
        env["MYSTIC_NO_SPLASH"] = "1"
    if args.touch:
        env["MYSTIC_FORCE_TOUCH"] = "1"
    if display == "xvfb" and args.renderer == "opengl3":
        # llvmpipe: runner CI tidak punya GPU. FPS di mode ini tidak bermakna.
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        env["GALLIUM_DRIVER"] = "llvmpipe"
    return env


def pick_display(args: argparse.Namespace) -> str:
    if args.display != "auto":
        return args.display
    if os.environ.get("DISPLAY") and sys.platform.startswith("linux"):
        return "x11"
    if sys.platform.startswith("linux") and shutil.which("xvfb-run"):
        return "xvfb"
    return "headless"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    display = pick_display(args)
    if display == "xvfb" and not shutil.which("xvfb-run"):
        if args.display == "xvfb":
            print("[siap] --display xvfb diminta tetapi xvfb-run tidak ada "
                  "(sudo apt-get install -y xvfb)", file=sys.stderr)
            return 2
        print("[siap] PERINGATAN: xvfb-run tidak ada — jatuh ke headless "
              "(tanpa screenshot)")
        display = "headless"

    scene = args.scene or MAIN_SCENE
    if args.scenario in ("level", "battle", "shop") and args.scene:
        print("[siap] PERINGATAN: skenario butuh scene utama; --scene diabaikan")
        scene = MAIN_SCENE

    expect = args.expect
    if args.scenario == "scene" and expect == DEFAULT_EXPECT:
        # Scene uji (res://tests/*.tscn) punya baris PASS sendiri dan memanggil
        # get_tree().quit() di akhir — harness tidak akan pernah sampai
        # mencetak "[DebugRun] PASS". Gerbang log tetap menolak semua error.
        expect = ""
        print("[siap] skenario scene: baris wajib '[DebugRun] PASS' dilewati "
              "(pakai --expect kalau scene-nya tidak punya baris sendiri)")

    out_dir = Path(args.out).expanduser() if args.out else default_out()
    out_dir = out_dir if out_dir.is_absolute() else (ROOT / out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "shots").mkdir(exist_ok=True)

    print("=" * 72)
    print(f"  GODOT DEBUG RUN · skenario={args.scenario} · level={args.level}"
          f" · {args.seconds:g}s · tampilan={display} · renderer={args.renderer}")
    print(f"  keluaran: {out_dir}")
    print("=" * 72)

    godot = resolve_godot(args)
    if godot is None:
        print("[siap] Godot tidak ditemukan. Pilihan:", file=sys.stderr)
        print("      * binary lokal : --godot /path/ke/godot", file=sys.stderr)
        print("      * PATH         : pasang godot / set MYSTIC_GODOT",
              file=sys.stderr)
        print("      * unduh        : --download", file=sys.stderr)
        return 2

    t0 = time.time()
    if not args.no_assets:
        copy_assets(out_dir)

    env = environment(args, out_dir, display)
    # Rem darurat DIHITUNG DARI WAKTU NYATA, bukan dari janji harness: harness
    # keluar sendiri setelah `--seconds` jam dinding, jadi batas ini hanya jaring
    # kalau harness/engine macet. Rentangnya dilebihkan untuk CI tanpa GPU
    # (llvmpipe bisa ~4 fps) dan untuk movie mode yang menyimpan tiap frame.
    # Catatan sejarah: `--seconds + 120` pernah memicu kill pada run sehat,
    # tetapi kill-nya hanya mengenai skrip pembungkus xvfb-run — Godot terus
    # hidup sampai `--quit-after` dan langkah 30 detik itu berjalan 9 menit.
    # Sekarang kill memakai os.killpg (lihat run_engine).
    timeout = args.timeout if args.timeout > 0 else max(args.seconds * 4 + 120,
                                                        300.0)

    if not args.no_import:
        import_project(godot, out_dir, env, args.force_import)
    prep_s = time.time() - t0

    cmd, _max_frames, _fps = build_command(args, godot, out_dir, scene, display)
    if args.dry_run:
        print("[kering] " + " ".join(cmd))
        return 0

    print(f"[waktu] aset + import: {prep_s:.0f} detik · rem darurat: "
          f"{timeout:.0f} detik")
    marker_ok = True
    if not args.no_preflight:
        marker_ok = preflight(godot, out_dir, env,
                              min(PREFLIGHT_TIMEOUT, args.timeout)
                              if args.timeout > 0 else PREFLIGHT_TIMEOUT)
    started = time.time()
    rc = run_engine(cmd, out_dir, env, timeout)
    elapsed = time.time() - started
    print(f"[waktu] engine: {elapsed:.0f} detik (exit {rc}) · "
          f"total {prep_s + elapsed:.0f} detik")

    shots = sorted((out_dir / "shots").glob("*.png"))
    video = make_video(out_dir) if args.movie else ""
    report = load_report(out_dir)
    if not harness_started(out_dir / "run.log"):
        print("[jalan] PERINGATAN: skrip harness tidak mencetak satu baris pun "
              "— engine mungkin menolak mengompilasi skrip debug (cari "
              "'Parse Error'/'SCRIPT ERROR' di run.log) atau scene tidak "
              "dijalankan (lihat baris '$ …' pertama run.log).")
    gate_ok = True
    if not args.no_gate:
        gate_ok = run_gate(out_dir / "run.log", args.label or args.scenario,
                           expect)

    summary = write_summary(out_dir, args, report, shots, video, gate_ok, rc,
                            elapsed, marker_ok)

    print("-" * 72)
    print(f"  screenshot : {len(shots)} → {out_dir / 'shots'}")
    print(f"  log        : {out_dir / 'run.log'}")
    print(f"  laporan    : {out_dir / 'report.json'} · {summary.name}")
    passed = gate_ok and rc == 0 and marker_ok
    print(f"  preflight  : {'OK' if marker_ok else 'GAGAL'}")
    print(f"  hasil      : {'PASS' if passed else 'FAIL'}")
    print("-" * 72)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
