# ================================
# tools/test_audio_global.py
# Uji regresi: suara serangan GLOBAL untuk semua unit.
#
# Memastikan janji-janji berikut benar-benar terpenuhi di kode:
#   1. SEMUA jenis minion (goblin, orc, troll, undead, dark_rider)
#      memakai SATU suara serangan global - bukan cuma goblin.
#   2. SEMUA jenis menara (archer, cannon, ice, mage) memakai SATU
#      suara tembak global - cannon tidak lagi punya ledakan khusus
#      yang hanya berbunyi untuk tim biru.
#   3. SEMUA minion memakai SATU suara kematian global.
#   4. Hero melee vs ranged terdengar BERBEDA.
#   5. Semua berkas WAV valid dimuat pygame.mixer.
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
from _entity import Minion, Tower, Hero            # noqa: E402
from _system import SoundManager                    # noqa: E402
from mobile import combat_audio as _ca             # noqa: E402


def main():
    gagal = []

    # ── 0. berkas WAV valid ──
    import glob
    wav = sorted(glob.glob("assets/sounds/*.wav"))
    buruk = []
    for f in wav:
        try:
            pygame.mixer.Sound(f)
        except Exception as exc:
            buruk.append("%s (%s)" % (f, exc))
    print("[0] berkas WAV: %d, gagal muat: %d" % (len(wav), len(buruk)))
    if buruk:
        gagal.extend(buruk)

    # ── 1. pola MINION bersih dari suara goblin ──
    pola_minion = _ca.POLA[_ca.MINION]
    bocor = [p for p in pola_minion if "goblin" in p]
    print("[1] pola MINION: %s" % pola_minion)
    if bocor:
        gagal.append("pola MINION masih mengandung goblin: %s" % bocor)

    # ── 2. suara serangan minion global ──
    #     _spawn_slash_effect() TIDAK boleh memutar slash/goblin_attack
    #     (dulu khusus goblin). Suara serangan minion datang dari
    #     combat_audio.play(MINION) di blok serangan update().
    rekam_sm = []
    SoundManager.play = lambda self, name, **kw: rekam_sm.append(name)
    for t in ("goblin", "orc", "troll", "undead", "dark_rider"):
        m = Minion(t, "blue", "mid")
        m._spawn_slash_effect()
    salah = [n for n in rekam_sm if n in ("slash", "goblin_attack")]
    print("[2] _spawn_slash_effect -> diputar: %s" % (rekam_sm or "(kosong)"))
    if salah:
        gagal.append("_spawn_slash_effect masih memutar suara khusus: %s"
                     % salah)

    # ── 3. suara kematian minion global ──
    rekam_sm.clear()
    for t in ("goblin", "orc", "troll", "undead", "dark_rider"):
        m = Minion(t, "blue", "mid")
        m.take_damage(m.max_hp * 10, "red")
    mati = [n for n in rekam_sm if n == "minion_death"]
    print("[3] take_damage fatal: %d minion mati -> %d suara minion_death"
          % (5, len(mati)))
    if len(mati) != 5:
        gagal.append("kematian minion tidak global: %s" % rekam_sm)

    # ── 4. suara tembak menara global + cannon tanpa ledakan khusus ──
    rekam_ca = []
    _ca.play = lambda jenis, volume_mult=1.0: rekam_ca.append(jenis)
    class _Tgt:
        x, y, alive = 300, 300, True
    for t in ("archer", "cannon", "ice", "mage"):
        tw = Tower(400, 300, "blue")
        tw.tower_type = t
        tw._apply_level_stats()
        tw.target = _Tgt()
        tw._shoot([tw.target])
    jenis_tower = set(rekam_ca)
    print("[4] _shoot 4 jenis menara -> jenis suara: %s" % sorted(jenis_tower))
    if jenis_tower != {_ca.TOWER}:
        gagal.append("menara memutar jenis lain: %s" % sorted(jenis_tower))
    if "explosion" in rekam_sm:
        gagal.append("cannon masih memutar explosion khusus")

    # ── 5. hero melee vs ranged berbeda ──
    rekam_ca.clear()
    _ca.play = lambda jenis, volume_mult=1.0: rekam_ca.append(jenis)
    for h in ("grimjaw", "kaizen", "thorne", "sylara", "vex", "zephyr"):
        hh = Hero(h, "blue", 300, 380)
        _ca.play_hero_basic(hh)
    print("[5] play_hero_basic: %s" % list(zip(
        ("grimjaw", "kaizen", "thorne", "sylara", "vex", "zephyr"),
        rekam_ca)))
    melee = set(rekam_ca[:3])
    ranged = set(rekam_ca[3:])
    if melee != {_ca.HERO_MELEE} or ranged != {_ca.HERO_RANGED}:
        gagal.append("hero melee/ranged tidak terbedakan: %s" % rekam_ca)
    if melee == ranged:
        gagal.append("suara melee dan ranged SAMA")

    # ── 6. ringkasan ──
    print()
    if gagal:
        print("HASIL: GAGAL")
        for g in gagal:
            print("  - %s" % g)
        return 1
    print("HASIL: LULUS. Semua suara serangan/kematian sudah global "
          "dan melee/ranged terbedakan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
