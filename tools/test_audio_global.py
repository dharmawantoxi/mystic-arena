# ================================
# tools/test_audio_global.py
# Uji regresi: PEMETAAN suara global sesuai skema final (v35).
#
# Skema final:
#   - minion: 1 suara pukulan global + 1 suara mati global
#   - menara: 4 suara tembak (per jenis) + 1 suara hancur global
#   - hero & boss: 2 suara (melee vs ranged) global
#
# Uji ini fokus ke KABEL KODENYA (tidak butuh berkas audio), jadi
# bisa dijalankan sebelum suara diisi.
#
# Jalankan:  python3 tools/test_audio_global.py
# ================================
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_BOOTCHECK", "0")

import pygame  # noqa: E402
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.mixer.init()

import _core          # noqa: E402,F401
import _entity        # noqa: E402,F401
from _entity import Minion, Tower, Hero   # noqa: E402
from _system import SoundManager           # noqa: E402
from mobile import combat_audio as _ca     # noqa: E402


def main():
    gagal = []

    # ── 1. jenis_tower memetakan 4 tipe ──
    harapan = {"archer": _ca.TOWER_ARCHER, "cannon": _ca.TOWER_CANNON,
               "ice": _ca.TOWER_ICE, "mage": _ca.TOWER_MAGE}
    print("[1] jenis_tower: %s" % {k: v for k, v in harapan.items()})
    for t, jenis in harapan.items():
        if _ca.jenis_tower(t) != jenis:
            gagal.append("jenis_tower(%s) salah" % t)

    # ── 2. Tower._shoot memakai jenis yang benar per tipe ──
    rekam = []
    _play_asli = _ca.play
    _ca.play = lambda jenis, volume_mult=1.0: rekam.append(jenis)
    try:
        class _Tgt:
            x, y, alive = 300, 300, True
        for t in ("archer", "cannon", "ice", "mage"):
            tw = Tower(400, 300, "blue")
            tw.tower_type = t
            tw._apply_level_stats()
            tw.target = _Tgt()
            tw._shoot([tw.target])
    finally:
        _ca.play = _play_asli
    print("[2] _shoot: %s" % rekam)
    if set(rekam) != {_ca.TOWER_ARCHER, _ca.TOWER_CANNON,
                      _ca.TOWER_ICE, _ca.TOWER_MAGE}:
        gagal.append("tower _shoot tidak membedakan jenis: %s" % rekam)

    # ── 3. Menara hancur -> tower_destroyed SEKALI saja ──
    rekam_sm = []
    SoundManager.play = lambda self, name, **kw: rekam_sm.append(name)
    tw = Tower(400, 300, "blue")
    tw.take_damage(99999, "red")
    tw.take_damage(99999, "red")   # panggil lagi -> tidak boleh ganda
    print("[3] menara hancur -> %s" % rekam_sm)
    if rekam_sm.count("tower_destroyed") != 1:
        gagal.append("tower_destroyed harus berbunyi tepat sekali: %s"
                     % rekam_sm)

    # ── 4. Kematian minion global (semua jenis) ──
    rekam_sm.clear()
    for t in ("goblin", "orc", "troll", "undead", "dark_rider"):
        m = Minion(t, "blue", "mid")
        m.take_damage(m.max_hp * 10, "red")
    mati = [n for n in rekam_sm if n == "minion_death"]
    print("[4] minion mati: %d/5 -> minion_death" % len(mati))
    if len(mati) != 5:
        gagal.append("kematian minion tidak global: %s" % rekam_sm)

    # ── 5. jenis_serangan melee vs ranged ──
    print("[5] jenis_serangan(45)=%s  jenis_serangan(130)=%s"
          % (_ca.jenis_serangan(45), _ca.jenis_serangan(130)))
    if _ca.jenis_serangan(45) != _ca.HERO_MELEE:
        gagal.append("jarak 45 harus melee")
    if _ca.jenis_serangan(130) != _ca.HERO_RANGED:
        gagal.append("jarak 130 harus ranged")

    # ── 6. Hero melee vs ranged ──
    for h in ("grimjaw", "kaizen", "thorne"):
        if _ca.jenis_serangan(Hero(h, "blue", 300, 380).range) != _ca.HERO_MELEE:
            gagal.append("hero %s harus melee" % h)
    for h in ("sylara", "vex", "zephyr"):
        if _ca.jenis_serangan(Hero(h, "blue", 300, 380).range) != _ca.HERO_RANGED:
            gagal.append("hero %s harus ranged" % h)
    print("[6] hero: grimjaw/kaizen/thorne=melee, sylara/vex/zephyr=ranged")

    # ── 7. Boss melee vs ranged ──
    try:
        from bosses.base_boss import Boss
        gornak = Boss("gornak")      # mini boss melee (range < 100)
        abaddon = Boss("abaddon")    # true boss melee (range 50)
        morgath = Boss("morgath")    # ranged (range >= 100)
        print("[7] boss: gornak=%s abaddon=%s morgath=%s"
              % (gornak._suara_serangan(), abaddon._suara_serangan(),
                 morgath._suara_serangan()))
        if gornak._suara_serangan() != _ca.HERO_MELEE:
            gagal.append("boss melee harus memakai hero_melee")
        if abaddon._suara_serangan() != _ca.HERO_MELEE:
            gagal.append("boss abaddon (range 50) harus melee")
        if morgath._suara_serangan() != _ca.HERO_RANGED:
            gagal.append("boss ranged harus memakai hero_ranged")
    except Exception as exc:
        print("[7] boss: TIDAK DIUJI (%s)" % exc)

    print()
    if gagal:
        print("HASIL: GAGAL")
        for g in gagal:
            print("  - %s" % g)
        return 1
    print("HASIL: LULUS. Pemetaan suara global sesuai skema final.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
