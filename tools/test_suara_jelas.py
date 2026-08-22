# ================================
# tools/test_suara_jelas.py
# Uji regresi: suara tempur HARUS valid, tidak klip, dan tidak
# terlalu pelan. (Kriteria diringkas dari versi sebelumnya yang
# memaksa hubungan spektral antar kategori - justru menghasilkan
# suara lapis yang aneh.)
#
# Yang diperiksa:
#   1. Semua berkas WAV valid dimuat pygame.mixer.
#   2. Puncak <= 0 dB (tidak klip) dan >= -6 dB (cukup keras).
#   3. Durasi masuk akal (0,05 s - 3 s) dan tidak senyap.
#   4. Varian serangan tidak identik (berkasnya berbeda).
#
# Jalankan:  python3 tools/test_suara_jelas.py
# ================================
import os
import sys
import math
import glob
import subprocess
import wave

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

TEMPUR = ["minion_hit", "hero_melee", "hero_ranged",
          "tower_archer", "tower_cannon", "tower_ice", "tower_mage"]


def _load(path):
    r = subprocess.run([FF, "-v", "error", "-i", path,
                        "-ac", "1", "-ar", "44100", "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return np.frombuffer(r.stdout, dtype=np.float32)


def _stats(path):
    a = _load(path)
    if a is None or len(a) == 0:
        return None
    dur = len(a) / 44100.0
    rms = math.sqrt(float(np.mean(a ** 2)))
    peak = float(np.max(np.abs(a)))
    return dur, rms, peak


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

    # ── 2. suara tempur (skip kalau belum diisi pemilik proyek) ──
    hilang = [k for k in TEMPUR
              if not os.path.exists(os.path.join(DIR, "%s.wav" % k))
              and not glob.glob(os.path.join(DIR, "%s_1.wav" % k))]
    if hilang:
        print("[2] suara tempur BELUM diisi: %s" % ", ".join(hilang))
        print("    (wajar sebelum pemilik proyek mengisi sendiri - SKIP)")
    else:
        print("[2] cek suara tempur (peak -6..0 dB, durasi 0.05-3s, tidak senyap):")
        for k in TEMPUR:
            for i in range(1, 4):
                p = os.path.join(DIR, "%s_%d.wav" % (k, i))
                if not os.path.exists(p):
                    continue
                s = _stats(p)
                if s is None:
                    gagal.append("%s_%d gagal dibaca" % (k, i))
                    continue
                dur, rms, peak = s
                ok = True
                if peak > 1.001:
                    gagal.append("%s_%d klip (peak %.2f)" % (k, i, peak)); ok = False
                if peak < 0.5:
                    gagal.append("%s_%d terlalu pelan (peak %.2f)" % (k, i, peak)); ok = False
                if not (0.05 <= dur <= 3.0):
                    gagal.append("%s_%d durasi aneh (%.2fs)" % (k, i, dur)); ok = False
                if rms < 0.005:
                    gagal.append("%s_%d senyap (rms %.4f)" % (k, i, rms)); ok = False
                print("    %-18s_%d  dur=%.2fs  peak=%.2f  %s"
                      % (k, i, dur, peak, "OK" if ok else "PERIKSA"))

    # ── 3. varian tidak identik (hanya jenis yang ber-variasi) ──
    print("[3] varian tidak identik:")
    for k in TEMPUR:
        data = []
        for i in range(1, 4):
            p = os.path.join(DIR, "%s_%d.wav" % (k, i))
            data.append(open(p, "rb").read() if os.path.exists(p) else None)
        ada = [d for d in data if d is not None]
        unik = len(set(ada))
        print("    %-18s %d varian" % (k, len(ada)))
        if len(ada) >= 2 and unik < 2:
            gagal.append("%s: varian terlalu mirip" % k)

    print()
    if gagal:
        print("HASIL: GAGAL")
        for g in gagal:
            print("  - %s" % g)
        return 1
    print("HASIL: LULUS (atau suara tempur belum diisi = wajar).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
