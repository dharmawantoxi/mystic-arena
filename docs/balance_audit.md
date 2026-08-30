# Audit balance hero

Mode: `ingame` - dihasilkan `python3 tools/balance_audit.py --md`.

| Metrik | Nilai | Target |
|---|---|---|
| corr(HP, DPS) semua hero unlock | 0.535 | <= 0.80 |
| sebaran power antar sel arketipe | 1.64 | >= 1.20 (harus ada beda peran) |
| magic/fisik vs boss (min & true) | mini: 1.000, true: 1.001 | 0.90 .. 1.15 |
| preferensi boss p90/p10 | 1.49 | >= 1.20 (lawan alami terasa) |
| sebaran power dalam satu band harga | 1.89 | <= 2.20 |

## Identitas arketipe (1.00 = median pool)

| Sel (sekolah x gaya) | n | DPS | EHP | power |
|---|---|---|---|---|
| MAGIC|CARRY | 11 | 0.83x | 0.92x | 0.84x |
| MAGIC|FIGHTER | 82 | 0.83x | 0.91x | 0.84x |
| MAGIC|TANK | 25 | 0.95x | 1.29x | 1.02x |
| PHYSICAL|CARRY | 10 | 1.27x | 0.90x | 1.19x |
| PHYSICAL|FIGHTER | 49 | 1.26x | 0.86x | 1.18x |
| PHYSICAL|TANK | 39 | 1.42x | 1.23x | 1.38x |

## Sekolah damage vs boss

| Kelas boss | DPS fisik | DPS magic | magic/fisik | p10/p50/p90 preferensi |
|---|---|---|---|---|
| mini | 334.1 | 334.2 | 1.0 | 0.56 / 0.65 / 0.83 |
| true | 324.0 | 324.2 | 1.001 | 0.53 / 0.57 / 0.75 |

## Daya pool (harus redistribusi, bukan buff)

Rata-rata DPS 216 hero unlock: sebelum balance 486.1 -> sesudah 486.1 (**1.000x**). Rata-rata EHP: 2495.4 -> 2495.4 (**1.000x**). Kedua angka memakai rumus yang sama (`hero_balance.metrics`), jadi selisihnya murni hasil balance pass, bukan beda definisi. Toleransi +/-12%.


## Starter vs hero unlock

Starter rata-rata **85.7 DPS**, hero unlock **486.1 DPS** (gap 5.67x). HP starter: [658, 728, 728, 770, 1120, 1960].


## Sisa damage yang dipotong cap anti-burst (12%/8%)

| Kelas | n | median | p90 | % hero rugi >15% |
|---|---|---|---|---|
| mini | 162 | 0.0% | 0.0% | 0.0% |
| true | 54 | 0.0% | 0.0% | 0.0% |

Catatan: cap ini memang disengaja (anti one-shot boss). Angka di atas dipakai untuk memutuskan apakah perlu penyesuaian, bukan sebagai bug.


## hero_balance.py

Diterapkan ke 216 hero unlock; rentang multiplier HP [0.7189, 1.3868], damage [0.5851, 2.0474].

