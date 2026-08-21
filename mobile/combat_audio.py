# ================================
# mobile/combat_audio.py
# LAPISAN SUARA TEMPUR
#
# Kenapa lapisan tersendiri, bukan SoundManager.play() bertebaran
# ─────────────────────────────────────────────────────────────────
# Di layar bisa ada 40 minion, 8 menara, 5 hero, dan seekor boss yang
# semuanya menyerang. Kalau setiap serangan langsung memutar suara:
#
#   - bunyinya jadi kebisingan, bukan umpan balik
#   - channel mixer habis, suara penting (boss) kalah oleh minion
#   - biaya mixing naik dan FPS yang susah payah dikejar ikut turun
#
# Modul ini menaruh tiga pengaman di antara game dan mixer:
#
#   1. JEDA PER JENIS    - satu jenis suara tidak boleh berbunyi lebih
#                          rapat dari jedanya (minion 140 ms, boss 320 ms)
#   2. ANGGARAN PER FRAME - maksimal 4 suara baru per frame, apa pun
#                          yang terjadi di layar
#   3. PRIORITAS         - saat channel penuh, boss/mini boss boleh
#                          merebut channel; minion tidak pernah
#
# Berkas suaranya dibuat oleh tools/gen_sounds.py (sintesis, bebas
# lisensi). Tiap jenis punya 3 variasi yang dipilih acak supaya
# serangan beruntun tidak terdengar seperti mesin tik.
# ================================

import os
import random

import pygame

# ── jenis suara ──
HERO_MELEE = "hero_melee"
HERO_RANGED = "hero_ranged"
TOWER = "tower_shoot"
MINION = "minion_attack"
MINIBOSS = "miniboss_attack"
BOSS = "boss_attack"

# jenis -> (volume dasar, jeda minimum ms, boleh rebut channel)
_KONFIG = {
    HERO_MELEE:  (0.55, 90, False),
    HERO_RANGED: (0.50, 90, False),
    TOWER:       (0.40, 110, False),
    MINION:      (0.26, 140, False),   # paling pelan: jumlahnya paling banyak
    MINIBOSS:    (0.70, 260, True),
    BOSS:        (0.90, 320, True),
}

VARIASI = 3
MAKS_PER_FRAME = 4

_bank = {}            # jenis -> [Sound, ...]
_terakhir = {}        # jenis -> ticks terakhir berbunyi
_sisa_frame = [MAKS_PER_FRAME]
_siap = [False]
_mati = [False]
_stats = {"main": 0, "tolak_jeda": 0, "tolak_anggaran": 0, "tolak_channel": 0}


def _dir_suara():
    akar = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(akar, "assets", "sounds")


def init():
    """
    Muat semua berkas. Aman dipanggil berkali-kali.

    Kalau mixer mati atau berkasnya tidak ada, modul MENONAKTIFKAN
    DIRI dengan tenang - game tetap jalan tanpa suara, tidak crash.
    """
    if _siap[0] or _mati[0]:
        return _siap[0]
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception as exc:
        print("[AUDIO] mixer tidak tersedia: %s" % exc)
        _mati[0] = True
        return False

    d = _dir_suara()
    total = 0
    for jenis in _KONFIG:
        daftar = []
        for i in range(1, VARIASI + 1):
            path = os.path.join(d, "%s_%d.wav" % (jenis, i))
            if not os.path.exists(path):
                continue
            try:
                daftar.append(pygame.mixer.Sound(path))
            except Exception as exc:
                print("[AUDIO] gagal memuat %s: %s" % (path, exc))
        if daftar:
            _bank[jenis] = daftar
            total += len(daftar)

    if not _bank:
        print("[AUDIO] tidak ada berkas suara di %s - suara tempur mati. "
              "Jalankan: python3 tools/gen_sounds.py" % d)
        _mati[0] = True
        return False

    # Sisakan channel untuk BGM/UI: suara tempur maksimal 12 channel.
    try:
        if pygame.mixer.get_num_channels() < 24:
            pygame.mixer.set_num_channels(24)
    except Exception:
        pass

    _siap[0] = True
    print("[AUDIO] suara tempur siap: %d berkas, %d jenis"
          % (total, len(_bank)))
    return True


def new_frame():
    """Panggil sekali per frame dari main loop."""
    _sisa_frame[0] = MAKS_PER_FRAME


def _volume_global():
    """Ikut pengaturan volume pemain kalau SoundManager tersedia."""
    try:
        from _system import SoundManager
        sm = SoundManager()
        if not getattr(sm, "enabled", True):
            return 0.0
        return float(sm.master_volume) * float(sm.sfx_volume)
    except Exception:
        return 0.6


def play(jenis, volume_mult=1.0):
    """
    Bunyikan suara serangan. Kembalikan True kalau benar-benar bunyi.

    Dirancang supaya AMAN dipanggil dari mana saja di jalur update -
    semua kegagalan ditelan, tidak ada pengecualian yang bocor ke
    logika permainan.
    """
    if _mati[0]:
        return False
    if not _siap[0] and not init():
        return False
    daftar = _bank.get(jenis)
    if not daftar:
        return False

    dasar, jeda, boleh_rebut = _KONFIG[jenis]

    try:
        sekarang = pygame.time.get_ticks()
    except Exception:
        return False

    if sekarang - _terakhir.get(jenis, -99999) < jeda:
        _stats["tolak_jeda"] += 1
        return False

    # Suara boss selalu boleh lewat anggaran frame: kalau boss
    # menghantam, itu informasi yang harus terdengar.
    if not boleh_rebut and _sisa_frame[0] <= 0:
        _stats["tolak_anggaran"] += 1
        return False

    try:
        kanal = pygame.mixer.find_channel(boleh_rebut)
        if kanal is None:
            _stats["tolak_channel"] += 1
            return False
        suara = random.choice(daftar)
        suara.set_volume(max(0.0, min(1.0,
                                      dasar * volume_mult
                                      * _volume_global())))
        kanal.play(suara)
    except Exception:
        return False

    _terakhir[jenis] = sekarang
    if not boleh_rebut:
        _sisa_frame[0] -= 1
    _stats["main"] += 1
    return True


def play_hero_basic(hero):
    """
    Suara serangan dasar hero, dipilih dari JANGKAUANNYA.

    Hero jarak dekat (Grimjaw range 25, Kaizen 30, Thorne 28) mendapat
    tebasan; hero jarak jauh (Sylara 150, Vex 165, Zephyr 180) mendapat
    petikan busur / lesatan sihir. Ambang 100 memisahkan keduanya
    dengan jarak aman - tidak ada hero di antara 35 dan 150.
    """
    try:
        jarak = float(getattr(hero, "range", 40) or 40)
    except Exception:
        jarak = 40.0
    return play(HERO_RANGED if jarak >= 100 else HERO_MELEE)


def stats():
    return dict(_stats)


def ringkas():
    s = _stats
    total_tolak = s["tolak_jeda"] + s["tolak_anggaran"] + s["tolak_channel"]
    return ("suara: main %d  ditolak %d (jeda %d / anggaran %d / kanal %d)"
            % (s["main"], total_tolak, s["tolak_jeda"],
               s["tolak_anggaran"], s["tolak_channel"]))
