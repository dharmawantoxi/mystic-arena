# ================================
# mobile/combat_audio.py
# LAPISAN SUARA TEMPUR — SKEMA FINAL (v35)
#
# Skema SEDERHANA, tanpa suara tercampur dari pengembang. Pemilik
# proyek mengisi sendiri berkas suaranya di assets/sounds/ dengan
# nama di bawah; modul ini hanya menyatukannya ke dalam game.
#
# JENIS SUARA (7):
#   hero_melee      -> tebasan SEMUA unit jarak dekat
#                      (hero summon/musuh + boss melee)
#   hero_ranged     -> serangan SEMUA unit jarak jauh
#                      (hero summon/musuh + boss ranged)
#   tower_archer    -> tembakan menara ARCHER
#   tower_cannon    -> tembakan menara CANNON
#   tower_ice       -> tembakan menara ICE
#   tower_mage      -> tembakan menara MAGE
#   minion_hit      -> pukulan SEMUA minion (goblin, orc, troll,
#                      undead, dark_rider)
#
# Suara kematian & ledakan & UI tetap lewat SoundManager (berkas
# .wav bernama tetap: minion_death.wav, tower_destroyed.wav, dll.)
#
# Tiga pengaman tetap dipasang supaya ramai tidak jadi kebisingan:
#   1. JEDA PER JENIS   - satu jenis tidak berbunyi lebih rapat
#                         dari jedanya (minion 140 ms, tower 110 ms)
#   2. ANGGARAN/FRAME   - maksimal 4 suara baru per frame
#   3. PRIORITAS        - boss/hero tidak pernah direbut; suara
#                         penting selalu terdengar
# ================================

import os
import random

import pygame

# ── jenis suara ──
HERO_MELEE = "hero_melee"
HERO_RANGED = "hero_ranged"
TOWER_ARCHER = "tower_archer"
TOWER_CANNON = "tower_cannon"
TOWER_ICE = "tower_ice"
TOWER_MAGE = "tower_mage"
MINION_HIT = "minion_hit"

# jenis -> (volume dasar, jeda minimum ms, boleh rebut channel)
_KONFIG = {
    HERO_MELEE:    (0.78, 90, False),
    HERO_RANGED:   (0.72, 90, False),
    TOWER_ARCHER:  (0.62, 110, False),
    TOWER_CANNON:  (0.62, 110, False),
    TOWER_ICE:     (0.62, 110, False),
    TOWER_MAGE:    (0.62, 110, False),
    MINION_HIT:    (0.50, 140, False),
}

# Ambang jarak serang (sama untuk hero dan boss):
#   jarak >= AMBANG  -> ranged
#   jarak <  AMBANG  -> melee
AMBANG_RANGED = 100

# ═══ PENEMUAN BERKAS ═══
# Nama pokoknya cukup SATU berkas (mis. hero_melee.wav). Kalau ada
# variasi bernomor (_1, _2, _3 ...), semuanya ikut dikumpulkan dan
# dipilih acak supaya serangan beruntun tidak monoton.
POLA = {
    HERO_MELEE:    ["hero_melee", "hero_melee_*"],
    HERO_RANGED:   ["hero_ranged", "hero_ranged_*"],
    TOWER_ARCHER:  ["tower_archer", "tower_archer_*"],
    TOWER_CANNON:  ["tower_cannon", "tower_cannon_*"],
    TOWER_ICE:     ["tower_ice", "tower_ice_*"],
    TOWER_MAGE:    ["tower_mage", "tower_mage_*"],
    MINION_HIT:    ["minion_hit", "minion_hit_*"],
}

EKSTENSI = (".wav", ".ogg", ".mp3")

_bank = {}            # jenis -> [Sound, ...]
_terakhir = {}        # jenis -> ticks terakhir berbunyi
_sisa_frame = [4]
_siap = [False]
_mati = [False]
_stats = {"main": 0, "tolak_jeda": 0, "tolak_anggaran": 0, "tolak_channel": 0}

LAPORAN = {
    "dir": "",
    "dir_ada": False,
    "mixer": "belum",
    "berkas": [],
    "per_jenis": {},
    "gagal": [],
    "catatan": "",
}


def _dir_suara():
    akar = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(akar, "assets", "sounds")


def _cocok(nama_tanpa_ext, pola):
    import fnmatch
    return fnmatch.fnmatch(nama_tanpa_ext, pola)


def init(paksa=False):
    """Temukan & muat semua berkas suara tempur. Aman dipanggil
    berkali-kali; gagal = modul menonaktifkan diri dengan tenang."""
    if paksa:
        _siap[0] = False
        _mati[0] = False
        _bank.clear()
    if _siap[0] or _mati[0]:
        return _siap[0]

    d = _dir_suara()
    LAPORAN["dir"] = d
    LAPORAN["dir_ada"] = os.path.isdir(d)
    LAPORAN["berkas"] = []
    LAPORAN["per_jenis"] = {}
    LAPORAN["gagal"] = []

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        info = pygame.mixer.get_init()
        LAPORAN["mixer"] = ("%d Hz, %d kanal" % (info[0], info[2])
                            if info else "gagal")
    except Exception as exc:
        LAPORAN["mixer"] = "gagal: %s" % exc
        LAPORAN["catatan"] = "mixer tidak bisa dinyalakan"
        print("[AUDIO] mixer tidak tersedia: %s" % exc)
        _mati[0] = True
        return False

    if not LAPORAN["dir_ada"]:
        LAPORAN["catatan"] = "folder assets/sounds TIDAK ADA di APK"
        print("[AUDIO] %s tidak ada" % d)
        _mati[0] = True
        return False

    try:
        semua = sorted(os.listdir(d))
    except OSError as exc:
        LAPORAN["catatan"] = "folder tidak terbaca: %s" % exc
        _mati[0] = True
        return False

    berkas = [f for f in semua if f.lower().endswith(EKSTENSI)]
    LAPORAN["berkas"] = berkas
    if not berkas:
        LAPORAN["catatan"] = ("folder ada tapi KOSONG - berkas audio "
                              "belum terunggah / tidak masuk APK")
        print("[AUDIO] tidak ada berkas audio di %s" % d)
        _mati[0] = True
        return False

    tanpa_ext = {}
    for f in berkas:
        tanpa_ext.setdefault(os.path.splitext(f)[0], f)

    total = 0
    for jenis, pola_list in POLA.items():
        terpilih = []
        for pola in pola_list:
            for nama in sorted(tanpa_ext):
                if nama in [os.path.splitext(x)[0] for x in terpilih]:
                    continue
                if _cocok(nama, pola):
                    terpilih.append(tanpa_ext[nama])
        daftar = []
        dipakai = []
        for f in terpilih:
            try:
                daftar.append(pygame.mixer.Sound(os.path.join(d, f)))
                dipakai.append(f)
            except Exception as exc:
                LAPORAN["gagal"].append("%s (%s)" % (f, exc))
        if daftar:
            _bank[jenis] = daftar
            total += len(daftar)
        LAPORAN["per_jenis"][jenis] = dipakai

    if not _bank:
        LAPORAN["catatan"] = ("%d berkas audio ada, tapi tidak satu pun "
                              "cocok dengan pola nama suara tempur"
                              % len(berkas))
        print("[AUDIO] %s" % LAPORAN["catatan"])
        _mati[0] = True
        return False

    try:
        if pygame.mixer.get_num_channels() < 24:
            pygame.mixer.set_num_channels(24)
    except Exception:
        pass

    kosong = [k for k in POLA if not LAPORAN["per_jenis"].get(k)]
    LAPORAN["catatan"] = ("siap - %d berkas dipakai dari %d yang ada"
                          % (total, len(berkas)))
    if kosong:
        LAPORAN["catatan"] += "; belum ada suara untuk: " + ", ".join(kosong)

    _siap[0] = True
    print("[AUDIO] %s" % LAPORAN["catatan"])
    for jenis, files in LAPORAN["per_jenis"].items():
        print("[AUDIO]   %-16s <- %s" % (jenis, ", ".join(files) or "(kosong)"))
    return True


def new_frame():
    """Panggil sekali per frame dari main loop."""
    _sisa_frame[0] = 4


def _volume_global():
    try:
        from _system import SoundManager
        sm = SoundManager()
        if not getattr(sm, "enabled", True):
            return 0.0
        return float(sm.master_volume) * float(sm.sfx_volume)
    except Exception:
        return 0.6


def play(jenis, volume_mult=1.0):
    """Bunyikan suara jenis tertentu. Aman dipanggil dari mana saja."""
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


def jenis_serangan(jarak):
    """Melee vs ranged dari jarak serang. Dipakai hero DAN boss."""
    try:
        jarak = float(jarak or 0)
    except Exception:
        jarak = 0.0
    return HERO_RANGED if jarak >= AMBANG_RANGED else HERO_MELEE


def jenis_tower(tower_type):
    """Jenis suara tembakan berdasarkan tipe menara."""
    return {
        "archer": TOWER_ARCHER,
        "cannon": TOWER_CANNON,
        "ice": TOWER_ICE,
        "mage": TOWER_MAGE,
    }.get(tower_type, TOWER_ARCHER)


def play_hero_basic(hero):
    """Suara serangan dasar hero (melee/ranged dari jangkauan)."""
    return play(jenis_serangan(getattr(hero, "range", 40)))


def stats():
    return dict(_stats)


def ringkas():
    s = _stats
    total_tolak = s["tolak_jeda"] + s["tolak_anggaran"] + s["tolak_channel"]
    return ("suara: main %d  ditolak %d (jeda %d / anggaran %d / kanal %d)"
            % (s["main"], total_tolak, s["tolak_jeda"],
               s["tolak_anggaran"], s["tolak_channel"]))


def uji_semua(jeda_ms=520):
    """Bunyikan satu contoh tiap jenis, berurutan (tombol UJI SUARA)."""
    hasil = []
    if not _siap[0]:
        init()
    urutan = (HERO_MELEE, HERO_RANGED, TOWER_ARCHER, TOWER_CANNON,
              TOWER_ICE, TOWER_MAGE, MINION_HIT)
    for jenis in urutan:
        _terakhir.pop(jenis, None)
        _sisa_frame[0] = 4
        ok = play(jenis, volume_mult=1.0)
        hasil.append((jenis, ok))
        try:
            pygame.time.wait(jeda_ms)
        except Exception:
            pass
    return hasil
