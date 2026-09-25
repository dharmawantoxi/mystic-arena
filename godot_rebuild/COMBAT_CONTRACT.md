# Kontrak laboratorium minion — tahap 2

Dokumen ini menjelaskan mode **Laboratorium minion**, yang tetap terpisah. Mode baru **Tower & nexus** dan perbedaannya dijelaskan di [SIEGE_CONTRACT.md](SIEGE_CONTRACT.md).

Tujuan: memindahkan bagian kecil perilaku minion secara teruji sebelum tower, hero, status effect dan ekonomi ditambahkan. Bukan pengganti pertandingan Python.

## Sumber dan batas kesetaraan

| Bagian | Referensi Python | Implementasi baru |
|---|---|---|
| Lima stat dasar minion | `_core.py:MINION_TYPES` | `data/minions/*.tres`, Resource bertipe |
| Nexus level 1 | `_core.py:NEXUS_LEVELS[1]` | Scale 1.0, AI level 1; scaling level lebih tinggi belum diterapkan |
| Tiga jalur | `map_components/_bundle.py:PathGenerator` | `scripts/data/lane_layout.gd`, Catmull–Rom dan truncation integer yang sama |
| State tiap unit | `_entity.py:Minion.__init__` | `unit_state.gd`, tidak menulis Resource definisi |
| Update cooldown/regen | `_entity.py:Minion.update` | Sekali per tick sebelum targeting/attack |
| Target AI tier 1 | `_find_target_smart` | Musuh hidup terdekat, jangkauan pencarian range + 30; tie berdasarkan urutan spawn ID |
| Gerak mengikuti lane | `_move_forward`, `_move_toward` | Ambang waypoint <15 px, advance index tanpa bergerak pada tick tersebut |
| Physical/magic biasa | Bagian dasar `Minion.take_damage` | `damage_rules.gd`; tanpa amp/shred/status effect |

Pemeriksa Python `tests/check_source_contract.py` membaca AST data asli dan mengeksekusi **hanya kelas PathGenerator murni** untuk memastikan fixture tidak menyimpang. Tidak mengimpor Pygame atau modul game, dan tidak memakai converter migrasi lama. Godot membandingkan seluruh fixture tersebut dengan hasilnya sendiri pada tes native.

## Aturan simulasi

- Clock: 60 physics tick/detik. Tidak ada damage, regen, cooldown atau movement dalam render callback.
- Speed dalam piksel/tick; range dalam piksel; cooldown dalam integer tick; HP dapat pecahan karena regen.
- Definisi minion bersifat read-only. HP, cooldown, target, waypoint dan posisi tersimpan per instance.
- Spawn ID naik monoton dalam satu dunia; restart membuat dunia baru.
- Resolusi serangan **berurutan**, bukan simultan: unit mati tidak mendapat giliran menyerang belakangan di tick yang sama. Spawn ID menentukan urutan, tidak bergantung pada Dictionary atau urutan render.
- Hit memvalidasi attacker/target hidup, tim berbeda, cooldown siap dan range.
- Serangan minion pada sumber saat ini memanggil damage langsung; laboratorium juga memakai hit langsung, termasuk Undead. Garis serangan hanya VFX, bukan projectile kedua.
- Physical: armor positif mereduksi, armor negatif meningkatkan damage dengan cap bonus 100%.
- Magic: memakai magic resist, bukan armor.
- Pembulatan mengikuti Python ties-to-even; misalnya `round(2.5) = 2`, bukan default pembulatan setengah menjauh dari nol.
- Damage positif setelah mitigasi minimum 1 sesuai sumber. Input damage <=0 atau school tidak dikenal ditolak.
- Death ditandai sebelum event/kredit diterbitkan. Death count dan kredit uji hanya bertambah satu kali.
- Dead ID dibuang setelah tick; target ID yang sudah tidak tersedia dibersihkan.
- Histori event dibatasi 64; unit aktif maksimal 120. Spawn wave yang tidak muat ditolak seluruhnya, bukan setengah berhasil.
- UI mengantre satu permintaan wave; world baru berubah pada physics tick. Pause/background membatalkan antrean tersebut.

## Perbedaan yang sengaja belum dipindahkan

1. **Wave adalah tombol laboratorium**, bukan scheduler produksi: satu minion per lane untuk masing-masing tim (6 unit). Wave pertama otomatis pada tick awal. Tidak memakai komposisi/jeda spawn/nexus upgrade produksi.
2. Posisi lane dan offset Y `top=-20`, `mid=0`, `bot=20` dipertahankan. **Random jitter ±8 px tidak diterapkan** agar fixture deterministik. Tidak ada separation/collision antar minion.
3. Saat mencapai ujung jalur, minion dicatat sebagai `exit` lalu dihapus. **Tidak menyerang castle/nexus**; kedua base hanya penanda. Exit bukan kill dan tidak memberi kredit.
4. Tanpa difficulty multiplier, nexus scaling selain tier 1, AI tier 2–5, stun, slow, debuff, item aura, hero/boss interaction atau shield.
5. `credited_gold` hanya audit internal pengujian kill. Bukan gold pemain, bukan reward progres dan tidak tersimpan.
6. HP mati dijepit ke 0 untuk state/presentasi; Python dapat memiliki HP negatif sesudah overkill. Ini normalisasi yang disengaja, bukan klaim kesetaraan nilai HP negatif.
7. Visual hanya lingkaran, health bar dan garis hit, bukan renderer/animasi produksi.
8. `Vector2` memakai precision engine; tes integer lane exact, posisi gerak pecahan tidak diklaim bit-identik lintas engine/platform.
9. Tidak ada kondisi menang/kalah, save, audio atau layanan jaringan.

**Catatan Troll:** regen sumber adalah 0.6 HP/tick (36 HP/detik), bukan 0.6 HP/detik. Duel seimbang Troll bisa berlangsung sangat lama atau tidak menghasilkan kill. Jangan memperbaikinya diam-diam dengan mengubah satuan. Gunakan Goblin/Orc untuk uji kill cepat; rebalance adalah pekerjaan terpisah.

## Pemisahan kode

```text
CombatScreen (input/UI, tetap aktif untuk resume)
├── CombatSession (Node pausable, satu step per physics tick)
│   └── MinionBattle (RefCounted, simulasi murni)
│       ├── UnitState[] + registry ID
│       ├── MinionDefinition (read-only Resource)
│       ├── LaneLayout
│       └── DamageRules
└── MinionView (read-only, boleh dinonaktifkan tanpa mengubah hasil)
```

Arena menggunakan transform uniform 0.7 untuk menampilkan seluruh koordinat 1280×720 di antara HUD. Klik dikonversi melalui inverse canvas transform; ini diuji lewat viewport, bukan hanya memanggil fungsi seleksi langsung.

## Kriteria sebelum memperluas gameplay

- Semua fixture lane dan minion tetap lulus.
- Tes damage/cooldown/death/reward tidak mundur.
- Rendering/FX tidak menjadi pemilik hit.
- Restart/pause/menu tidak menyisakan antrean atau state dunia lama.
- Fitur berikutnya menambah tes sendiri; jangan mengganti baseline dengan hasil implementasi baru tanpa membandingkan sumber.

Milestone tower/nexus tier 1, projectile dan hasil siege sudah ditambahkan sebagai mode terpisah. Berikutnya: scheduler wave/ekonomi → build/sell minimum → satu pertandingan kecil utuh. Audit formula sumber dan urutan efek sebelum porting; jangan menganggap aturan damage minion otomatis benar untuk hero/tower/boss.
