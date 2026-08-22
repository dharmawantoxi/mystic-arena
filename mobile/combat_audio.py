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
# Volume dasar dinaikkan (v33): sebelumnya minion 0,26 dan tower 0,40
# dikali lagi master(0,7)*sfx(0,6)=0,42, sehingga efektif hanya ~0,11
# dan ~0,17 - tenggelam di bawah BGM di speaker HP. Sekarang efektif
# ~0,21-0,33, cukup keras terdengar tapi tidak menutup BGM.
_KONFIG = {
    HERO_MELEE:  (0.78, 90, False),
    HERO_RANGED: (0.72, 90, False),
    TOWER:       (0.62, 110, False),
    MINION:      (0.50, 140, False),   # paling pelan: jumlahnya paling banyak
    MINIBOSS:    (0.85, 260, True),
    BOSS:        (1.00, 320, True),
}

VARIASI = 3
MAKS_PER_FRAME = 4

# ═══ PENEMUAN BERKAS OTOMATIS ═══
# Tiap jenis suara tempur punya DAFTAR POLA berurut. Semua berkas
# yang cocok dikumpulkan jadi satu kolam variasi. Skema "global":
#   - SEMUA minion memakai satu suara serangan yang sama (minion_attack_*)
#   - SEMUA menara memakai satu suara tembak yang sama (tower_shoot_*)
#   - SEMUA hero memakai satu suara serangan dasar, dibedakan
#     melee (hero_melee_*) vs ranged (hero_ranged_*)
#   - mini boss (miniboss_attack_*) vs true boss (boss_attack_*)
# Menambah berkas baru dengan nama yang cocok otomatis ikut terpakai.
POLA = {
    HERO_MELEE:  ["hero_melee_*", "hero_melee", "slash", "slash_*",
                  "sword*", "hero_attack*", "melee*"],
    HERO_RANGED: ["hero_ranged_*", "hero_ranged", "arrow*", "bow*",
                  "hero_shoot*", "ranged*", "magic_bolt*"],
    TOWER:       ["tower_shoot_*", "tower_shoot", "tower_attack*",
                  "archer*", "arrow_shoot*"],
    MINION:      ["minion_attack_*", "minion_attack", "minion_hit*"],
    MINIBOSS:    ["miniboss_attack_*", "miniboss_attack",
                  "mini_boss*", "miniboss*"],
    BOSS:        ["boss_attack_*", "boss_attack", "true_boss*",
                  "boss_hit*"],
}

EKSTENSI = (".wav", ".ogg", ".mp3")

_bank = {}            # jenis -> [Sound, ...]
_terakhir = {}        # jenis -> ticks terakhir berbunyi
_sisa_frame = [MAKS_PER_FRAME]
_siap = [False]
_mati = [False]
_stats = {"main": 0, "tolak_jeda": 0, "tolak_anggaran": 0, "tolak_channel": 0}

# Laporan lengkap untuk layar diagnostik. Inilah yang menjawab
# pertanyaan "kenapa suaranya tidak keluar" tanpa menebak.
LAPORAN = {
    "dir": "",
    "dir_ada": False,
    "mixer": "belum",
    "berkas": [],          # semua berkas audio yang ditemukan
    "per_jenis": {},       # jenis -> [nama berkas terpakai]
    "gagal": [],           # berkas yang ada tapi gagal dimuat
    "catatan": "",
}


def _dir_suara():
    akar = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(akar, "assets", "sounds")


def _cocok(nama_tanpa_ext, pola):
    import fnmatch
    return fnmatch.fnmatch(nama_tanpa_ext, pola)


def init(paksa=False):
    """
    Temukan dan muat semua berkas suara tempur.

    Aman dipanggil berkali-kali. Kalau mixer mati atau tidak ada
    berkas sama sekali, modul MENONAKTIFKAN DIRI dengan tenang -
    game tetap jalan tanpa suara, tidak pernah crash.
    """
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
        LAPORAN["catatan"] = ("folder ada tapi KOSONG - berkas .wav "
                              "belum ikut terunggah / tidak masuk APK")
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
                              "cocok dengan pola nama" % len(berkas))
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


def uji_semua(jeda_ms=520):
    """
    Bunyikan satu contoh tiap jenis, berurutan.

    Dipakai tombol "UJI SUARA" di layar diagnostik supaya bisa
    memastikan audio hidup TANPA harus masuk permainan dulu.
    Mengembalikan daftar (jenis, berhasil).
    """
    hasil = []
    if not _siap[0]:
        init()
    for jenis in (HERO_MELEE, HERO_RANGED, TOWER, MINION, MINIBOSS, BOSS):
        _terakhir.pop(jenis, None)
        _sisa_frame[0] = MAKS_PER_FRAME
        ok = play(jenis, volume_mult=1.0)
        hasil.append((jenis, ok))
        try:
            pygame.time.wait(jeda_ms)
        except Exception:
            pass
    return hasil
