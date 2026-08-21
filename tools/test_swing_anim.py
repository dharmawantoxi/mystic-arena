"""
tools/test_swing_anim.py

Membuktikan perbaikan animasi swing v21 dengan ANGKA.

Cara kerja simulasi
───────────────────
Simulasi game berjalan 60 langkah/detik (fixed timestep).
`attack_timer` di-set ke `attack_cooldown` saat menyerang, lalu
berkurang 1 tiap langkah.

`_update_attack_anim()` dipanggil dari DRAW - jadi hanya sekali per
FRAME GAMBAR, bukan per langkah simulasi. Di HP, satu frame gambar
mencakup 4-12 langkah simulasi. Di situlah animasi lama rusak.

Yang diukur
───────────
  siklus  : berapa kali animasi swing benar-benar dimainkan
            (progres turun tajam = swing baru dimulai)
  serangan: berapa kali hero benar-benar menyerang
            -> siklus HARUS mendekati serangan
  pose    : rata-rata jumlah pose berbeda per swing
            (1 = pose beku, makin besar makin mulus)

Jalankan:  python3 tools/test_swing_anim.py
Bandingkan dengan kode lama:
           python3 tools/test_swing_anim.py /tmp/_bundle.bak.py
"""

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame                                            # noqa: E402

pygame.init()
pygame.display.set_mode((64, 64))

PREFIX = [
    ("grimjaw", "_NS_grimjaw", "_gj", 40),
    ("sylara", "_NS_sylara", "_sy", 45),
    ("kaizen", "_NS_kaizen", "_kz", 45),
    ("thorne", "_NS_thorne", "_th", 45),
    ("vex", "_NS_vex", "_vx", 50),
    ("zephyr", "_NS_zephyr", "_zp", 42),
]

FPS_UJI = (60, 30, 15, 8, 5)


def muat(path=None):
    if path is None:
        import heroes._bundle as m
        return m
    spec = importlib.util.spec_from_file_location("_bundle_lama", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class FakeHero:
    def __init__(self, cooldown):
        self.attack_cooldown = cooldown
        self.timer = 0
        self.x = self.y = 0.0


def simulate(ns, prefix, cooldown, fps, detik=10):
    h = FakeHero(cooldown)
    langkah_per_frame = max(1, int(round(60.0 / fps)))
    total = 60 * detik

    serangan = 0
    siklus = 0
    pose_siklus = []
    pose_kini = set()
    prev_prog = 0.0
    langkah = 0

    while langkah < total:
        for _ in range(langkah_per_frame):
            if h.timer > 0:
                h.timer -= 1
            else:
                h.timer = cooldown
                serangan += 1
            langkah += 1
            if langkah >= total:
                break

        ns._update_attack_anim(h)
        prog = float(getattr(h, prefix + "_attack_progress", 0.0))

        # progres turun tajam = swing baru dimulai
        if prog < prev_prog - 0.25 or (prev_prog == 0.0 and prog > 0.0):
            siklus += 1
            if pose_kini:
                pose_siklus.append(len(pose_kini))
            pose_kini = set()
        if prog > 0.0:
            pose_kini.add(round(prog, 2))
        prev_prog = prog

    if pose_kini:
        pose_siklus.append(len(pose_kini))
    rata_pose = (sum(pose_siklus) / len(pose_siklus)) if pose_siklus else 0.0
    return serangan, siklus, rata_pose


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    mod = muat(path)
    judul = "KODE LAMA (%s)" % path if path else "KODE v21 (sekarang)"

    print("=" * 62)
    print(judul)
    print("=" * 62)
    print("siklus harus mendekati serangan. pose = rata-rata pose/swing.\n")

    gagal = 0
    for nama, nsname, prefix, cd in PREFIX:
        ns = getattr(mod, nsname)
        baris = []
        for fps in FPS_UJI:
            serangan, siklus, pose = simulate(ns, prefix, cd, fps)
            ok = siklus >= serangan - 1
            if not ok:
                gagal += 1
            baris.append("%3d FPS: %2d/%2d siklus, %4.1f pose %s"
                         % (fps, siklus, serangan, pose,
                            "OK " if ok else "GAGAL"))
        print("%-9s | %s" % (nama, "  |  ".join(baris)))

    print()
    if gagal:
        print("HASIL: %d dari %d kombinasi GAGAL"
              % (gagal, len(PREFIX) * len(FPS_UJI)))
        return 1
    print("HASIL: semua %d kombinasi hero x FPS memainkan swing dengan benar."
          % (len(PREFIX) * len(FPS_UJI)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
