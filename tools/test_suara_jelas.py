# ================================
# tools/test_suara_jelas.py
# Uji regresi: suara tempur HARUS jelas (cukup keras) dan BISA
# dibedakan satu sama lain secara terukur.
#
# Yang diperiksa (semua angka objektif dari berkas WAV):
#   1. Setiap suara tempur cukup keras (RMS >= 0,05 setelah
#      normalisasi puncak -1 dB) -> tidak "tenggelam".
#   2. Slash MINION lebih TINGGI nadanya daripada slash HERO MELEE
#      (centroid spektral minion > hero) -> beda kelas bunyi.
#   3. Suara RANGED lebih PANJANG daripada tembakan TOWER (durasi
#      ranged > tower) -> whoosh sihir vs bunyi busur pendek.
#   4. Semua berkas valid dimuat pygame.mixer.
#
# Jalankan:  python3 tools/test_suara_jelas.py
# ================================
import os
import sys
import math
import glob
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.mixer.init()

import numpy as np  # noqa: E402

FF = "ffmpeg"
DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "sounds")


def _load(path):
    r = subprocess.run([FF, "-v", "error", "-i", path,
                        "-ac", "1", "-ar", "44100", "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return np.frombuffer(r.stdout, dtype=np.float32)


def _rms(path):
    a = _load(path)
    return math.sqrt(float(np.mean(a ** 2))) if a is not None else 0.0


def _centroid(path):
    a = _load(path)
    if a is None or len(a) == 0:
        return 0.0
    n = len(a)
    spec = np.abs(np.fft.rfft(a))
    f = np.fft.rfftfreq(n, 1 / 44100.0)
    return float(np.sum(spec * f) / max(1e-9, np.sum(spec)))


def _dur(path):
    a = _load(path)
    return (len(a) / 44100.0) if a is not None else 0.0


def main():
    gagal = []

    # ── 1. semua WAV valid ──
    wav = sorted(glob.glob(os.path.join(DIR, "*.wav")))
    buruk = []
    for f in wav:
        try:
            pygame.mixer.Sound(f)
        except Exception as exc:
            buruk.append("%s (%s)" % (os.path.basename(f), exc))
    print("[1] berkas WAV: %d, gagal muat: %d" % (len(wav), len(buruk)))
    if buruk:
        gagal.extend(buruk)

    def rms_of(kind, n=3):
        return [round(_rms(os.path.join(DIR, "%s_%d.wav" % (kind, i))), 3)
                for i in range(1, n + 1)]

    def cen_of(kind, n=3):
        return [round(_centroid(os.path.join(DIR, "%s_%d.wav" % (kind, i))))
                for i in range(1, n + 1)]

    def dur_of(kind, n=3):
        return [round(_dur(os.path.join(DIR, "%s_%d.wav" % (kind, i))), 2)
                for i in range(1, n + 1)]

    # ── 2. keras (RMS) ──
    batas = 0.05
    kinds = ["minion_attack", "hero_melee", "hero_ranged",
             "tower_shoot", "bullet_hit"]
    print("[2] RMS (ambang %.2f):" % batas)
    for k in kinds:
        vals = rms_of(k) if k != "bullet_hit" else [round(_rms(
            os.path.join(DIR, "bullet_hit.wav")), 3)]
        print("    %-16s %s" % (k, vals))
        if any(v < batas for v in vals):
            gagal.append("%s terlalu pelan: %s" % (k, vals))

    # ── 3. minion lebih tinggi dari hero melee ──
    cen_minion = cen_of("minion_attack")
    cen_melee = cen_of("hero_melee")
    print("[3] centroid  minion=%s  hero_melee=%s"
          % (cen_minion, cen_melee))
    if min(cen_minion) <= max(cen_melee):
        gagal.append("slash minion tidak lebih tinggi dari hero melee")

    # ── 4. ranged lebih panjang dari tower ──
    dur_ranged = dur_of("hero_ranged")
    dur_tower = dur_of("tower_shoot")
    print("[4] durasi   ranged=%s  tower=%s" % (dur_ranged, dur_tower))
    if min(dur_ranged) <= max(dur_tower):
        gagal.append("suara ranged tidak lebih panjang dari tower")

    print()
    if gagal:
        print("HASIL: GAGAL")
        for g in gagal:
            print("  - %s" % g)
        return 1
    print("HASIL: LULUS. Semua suara tempur cukup keras dan bisa dibedakan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
