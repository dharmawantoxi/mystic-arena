"""
tools/gen_sounds.py

Membuat SEMUA efek suara tempur Mystic Arena secara sintesis.

Kenapa disintesis, bukan diunduh
────────────────────────────────
  - assets/sounds/ kosong total, jadi seluruh SoundManager selama ini
    memuat berkas yang tidak ada dan gagal diam-diam
  - bebas lisensi sepenuhnya, aman untuk Google Play
  - ukurannya kecil dan bisa diatur (penting untuk batas APK)
  - bisa dibangun ulang kapan saja dan hasilnya SAMA PERSIS
    (semua acak diberi benih tetap)

Yang dibuat
───────────
  hero_melee       tebasan pedang + benturan          3 variasi
  hero_ranged      petikan busur / lesatan sihir      3 variasi
  tower_shoot      dentum menara                      3 variasi
  minion_attack    pukulan kecil pasukan              3 variasi
  miniboss_attack  ayunan berat mini boss             3 variasi
  boss_attack      hentakan dalam true boss           3 variasi

Tiga variasi per jenis itu penting: dengan 40 minion menyerang,
satu berkas yang sama persis akan terdengar seperti mesin tik.

Jalankan:  python3 tools/gen_sounds.py
"""

import math
import os
import struct
import sys
import wave

SR = 44100
KELUARAN = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "sounds")

try:
    import numpy as np
except ImportError:
    print("Butuh numpy:  pip install numpy")
    sys.exit(1)


# ══════════════════════════════════════════════════════
# Balok bangunan
# ══════════════════════════════════════════════════════
def n_sampel(detik):
    return int(SR * detik)


def waktu(detik):
    return np.arange(n_sampel(detik)) / float(SR)


def derau(detik, rng):
    return rng.uniform(-1.0, 1.0, n_sampel(detik))


def sinus(detik, f0, f1=None):
    """Sinus dengan sapuan frekuensi f0 -> f1 (eksponensial)."""
    t = waktu(detik)
    if f1 is None or abs(f1 - f0) < 1e-6:
        fase = 2 * math.pi * f0 * t
    else:
        k = (f1 / float(f0)) ** (1.0 / max(1e-6, detik))
        fase = 2 * math.pi * f0 * (k ** t - 1.0) / math.log(k)
    return np.sin(fase)


def peluruhan(detik, kekuatan=6.0):
    """Amplop turun eksponensial: keras di awal, hilang di akhir."""
    t = np.linspace(0.0, 1.0, n_sampel(detik))
    return np.exp(-kekuatan * t)


def ayunan(detik, puncak=0.45):
    """
    Amplop 'whoosh': naik pelan lalu turun cepat.
    Meniru pedang yang diayun melewati telinga.
    """
    t = np.linspace(0.0, 1.0, n_sampel(detik))
    naik = np.clip(t / puncak, 0.0, 1.0) ** 1.6
    turun = np.clip((1.0 - t) / (1.0 - puncak), 0.0, 1.0) ** 1.4
    return naik * turun


def lolos_bawah(x, fc):
    """Tapis lolos-bawah satu kutub - membulatkan suara yang terlalu tajam."""
    a = math.exp(-2.0 * math.pi * fc / SR)
    y = np.empty_like(x)
    akum = 0.0
    for i in range(x.size):
        akum = (1.0 - a) * x[i] + a * akum
        y[i] = akum
    return y


def lolos_atas(x, fc):
    return x - lolos_bawah(x, fc)


def pita(x, f_bawah, f_atas):
    return lolos_bawah(lolos_atas(x, f_bawah), f_atas)


def tumpuk(*potongan):
    """Jumlahkan beberapa larik dengan panjang berbeda, mulai di offset."""
    total = 0
    for data, mulai in potongan:
        total = max(total, mulai + data.size)
    keluar = np.zeros(total)
    for data, mulai in potongan:
        keluar[mulai:mulai + data.size] += data
    return keluar


def normalkan(x, puncak=0.85):
    m = float(np.max(np.abs(x))) if x.size else 0.0
    if m < 1e-9:
        return x
    return x / m * puncak


def lembutkan_tepi(x, ms=4.0):
    """Fade in/out singkat supaya tidak ada 'klik' di ujung berkas."""
    n = max(1, int(SR * ms / 1000.0))
    n = min(n, x.size // 2)
    if n <= 1:
        return x
    x = x.copy()
    x[:n] *= np.linspace(0.0, 1.0, n)
    x[-n:] *= np.linspace(1.0, 0.0, n)
    return x


def jenuh(x, jumlah=1.6):
    """Sedikit distorsi supaya terdengar berisi, bukan tipis."""
    return np.tanh(x * jumlah) / math.tanh(jumlah)


def simpan(nama, x, keras=1.0):
    x = lembutkan_tepi(normalkan(x) * keras)
    data = np.clip(x, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")
    path = os.path.join(KELUARAN, nama)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path, pcm.size


# ══════════════════════════════════════════════════════
# Resep tiap suara
# ══════════════════════════════════════════════════════
def hero_melee(rng, nada=1.0):
    """Tebasan pedang: desing udara lalu benturan logam."""
    d_desing = 0.15
    desing = pita(derau(d_desing, rng), 700 * nada, 3400 * nada)
    desing *= ayunan(d_desing, 0.55) * 0.9

    d_hantam = 0.14
    hantam = (sinus(d_hantam, 260 * nada, 110 * nada) * 0.7
              + pita(derau(d_hantam, rng), 900, 6000) * 0.5)
    hantam *= peluruhan(d_hantam, 11.0)

    d_dering = 0.20
    dering = (sinus(d_dering, 1850 * nada) * 0.25
              + sinus(d_dering, 2770 * nada) * 0.12)
    dering *= peluruhan(d_dering, 9.0)

    mulai = n_sampel(0.085)
    return jenuh(tumpuk((desing, 0), (hantam, mulai), (dering, mulai)), 1.3)


def hero_ranged(rng, nada=1.0):
    """Busur/sihir: petikan bernada turun + lesatan udara."""
    d_petik = 0.16
    petik = (sinus(d_petik, 780 * nada, 250 * nada) * 0.8
             + sinus(d_petik, 1560 * nada, 500 * nada) * 0.25)
    petik *= peluruhan(d_petik, 13.0)

    d_lesat = 0.22
    lesat = pita(derau(d_lesat, rng), 1400 * nada, 7000 * nada)
    lesat *= peluruhan(d_lesat, 7.0) * 0.5

    d_kilau = 0.18
    kilau = sinus(d_kilau, 2400 * nada, 3600 * nada) * 0.14
    kilau *= peluruhan(d_kilau, 10.0)

    return jenuh(tumpuk((petik, 0), (lesat, n_sampel(0.01)),
                        (kilau, n_sampel(0.02))), 1.2)


def tower_shoot(rng, nada=1.0):
    """Menara: klik mekanis lalu dentum rendah."""
    d_klik = 0.03
    klik = pita(derau(d_klik, rng), 2000, 9000) * peluruhan(d_klik, 30.0)

    d_dentum = 0.30
    dentum = (sinus(d_dentum, 150 * nada, 62 * nada) * 0.95
              + sinus(d_dentum, 300 * nada, 124 * nada) * 0.3)
    dentum *= peluruhan(d_dentum, 8.0)

    d_badan = 0.22
    badan = lolos_bawah(derau(d_badan, rng), 1100) * peluruhan(d_badan, 12.0)

    return jenuh(tumpuk((klik, 0), (dentum, n_sampel(0.012)),
                        (badan * 0.45, n_sampel(0.012))), 1.5)


def minion_attack(rng, nada=1.0):
    """
    Pasukan: pukulan kecil dan PENDEK.

    Sengaja dibuat pelan dan singkat - dengan 40 minion di layar,
    suara yang panjang atau nyaring akan jadi kebisingan.
    """
    d = 0.09
    tubuk = sinus(d, 420 * nada, 190 * nada) * peluruhan(d, 20.0)
    gesek = pita(derau(d, rng), 1200, 5200) * peluruhan(d, 26.0) * 0.45
    return jenuh(tumpuk((tubuk, 0), (gesek, 0)), 1.1) * 0.55


def miniboss_attack(rng, nada=1.0):
    """Mini boss: ayunan berat, lebih rendah dan lebih lama dari hero."""
    d_ayun = 0.22
    ayun = pita(derau(d_ayun, rng), 260 * nada, 1500 * nada)
    ayun *= ayunan(d_ayun, 0.6)

    d_hantam = 0.28
    hantam = (sinus(d_hantam, 150 * nada, 62 * nada) * 0.95
              + sinus(d_hantam, 92 * nada, 45 * nada) * 0.6)
    hantam *= peluruhan(d_hantam, 8.5)

    d_retak = 0.16
    retak = pita(derau(d_retak, rng), 500, 4200) * peluruhan(d_retak, 14.0)

    mulai = n_sampel(0.13)
    return jenuh(tumpuk((ayun * 0.8, 0), (hantam, mulai),
                        (retak * 0.5, mulai)), 1.7)


def boss_attack(rng, nada=1.0):
    """True boss: hentakan sub-bass + gemuruh panjang."""
    d_sub = 0.55
    sub = (sinus(d_sub, 78 * nada, 34 * nada) * 1.0
           + sinus(d_sub, 39 * nada, 22 * nada) * 0.7)
    sub *= peluruhan(d_sub, 5.0)

    d_hantam = 0.18
    hantam = pita(derau(d_hantam, rng), 300, 3600) * peluruhan(d_hantam, 12.0)

    d_gemuruh = 0.70
    gemuruh = lolos_bawah(derau(d_gemuruh, rng), 380)
    gemuruh *= peluruhan(d_gemuruh, 3.4) * 0.8

    d_logam = 0.32
    logam = (sinus(d_logam, 620 * nada, 300 * nada) * 0.3)
    logam *= peluruhan(d_logam, 7.0)

    return jenuh(tumpuk((hantam, 0), (sub, 0), (gemuruh, 0),
                        (logam, n_sampel(0.02))), 2.0)


# nama -> (fungsi, keras, jumlah variasi)
RESEP = {
    "hero_melee": (hero_melee, 0.95, 3),
    "hero_ranged": (hero_ranged, 0.85, 3),
    "tower_shoot": (tower_shoot, 0.90, 3),
    "minion_attack": (minion_attack, 0.55, 3),
    "miniboss_attack": (miniboss_attack, 1.00, 3),
    "boss_attack": (boss_attack, 1.00, 3),
}

# Nada tiap variasi. Bukan sekadar acak: naik-turun sedikit di sekitar
# 1.0 supaya terdengar seperti serangan yang sama, bukan senjata lain.
NADA_VARIASI = (1.0, 0.92, 1.09)


def main():
    os.makedirs(KELUARAN, exist_ok=True)
    total_byte = 0
    print("Membuat efek suara ke %s\n" % KELUARAN)
    print("  %-26s %8s %9s" % ("berkas", "durasi", "ukuran"))
    for nama, (fn, keras, jumlah) in RESEP.items():
        for i in range(jumlah):
            rng = np.random.RandomState(abs(hash(nama)) % 100000 + i)
            x = fn(rng, NADA_VARIASI[i % len(NADA_VARIASI)])
            berkas = "%s_%d.wav" % (nama, i + 1)
            path, sampel = simpan(berkas, x, keras)
            ukuran = os.path.getsize(path)
            total_byte += ukuran
            print("  %-26s %7.2fs %8.1f KB"
                  % (berkas, sampel / float(SR), ukuran / 1024.0))
    print("\nTotal %d berkas, %.1f KB"
          % (sum(v[2] for v in RESEP.values()), total_byte / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
