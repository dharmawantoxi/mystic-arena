# Status & handoff — Godot Rebuild

Diperbarui: 25 September 2026. Pengguna memakai **Windows 11, Godot 4.7.2 standard** dan meminta implementasi langsung di repo.

## Aturan pekerjaan

- Gunakan proyek **`godot_rebuild/`**, bukan migrasi lama. Python/Pygame tetap referensi; jangan mengubahnya agar port lolos.
- Branch tetap **`arena/01a0d776-mystic-arena`**. Push checkpoint berkala sebelum sesi habis; tidak ada indikator batas sesi yang pasti.
- [PR #278](https://github.com/dharmawantoxi/mystic-arena/pull/278) **OPEN, belum di-merge**. Push memperbarui PR yang sama. Jangan pindah branch atau membuat PR pengganti.
- Jangan mengklaim seluruh migrasi selesai karena laboratorium/prototipe ini berjalan.

## Checkpoint yang sudah dipush dan diverifikasi

| Commit | Cakupan | Bukti native |
|---|---|---|
| `f4a71ee` | Fondasi menu, sandbox, pause/restart, tests/CI | [CI fondasi](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36113676693) |
| `741b660` | Combat minion dan fixture sumber | [745 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36114379895) |
| `5d2d0e0` | Archer/nexus/projectile, oracle numerik | [1.072 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36116716287) |
| `d09ce35` | UI siege, hasil dan lifecycle | [1.158 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36117033161) |
| `e3b592d` | Dokumen siege/handoff | [1.158 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36117480660) |
| `868cfc2` → `a218073` | Wave otomatis, ledger, slot dan transaksi; perbaikan pembanding JSON tes | [1.418 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36151766743) |
| `ff5d2af` | Mode **Pertandingan awal**, HUD/build/sell/hasil dan lifecycle | [1.511 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36152202295) |

Commit dokumentasi setelahnya tercatat di `git log`; periksa CI terbaru pada branch untuk hasil HEAD terbaru. Check-run untuk checkpoint UI: **108127972332**, annotation `Native Godot tests`, PASS 1511.

## Yang tersedia saat F5

Import `godot_rebuild/project.godot` → F5; tidak perlu membuat scene/script manual.

- **Pertandingan awal**: subset level 1/normal, 1000 G, 9 slot biru, Archer 100 G / refund 50 G; wave otomatis; lawan sementara membeli tiga Archer berbayar; hasil nexus, pause/restart. Bukan AI asli atau seluruh level Python.
- **Tower & nexus**: enam Archer dan dua nexus, projectile/shield, wave manual satu/dua tim, hasil. Laboratorium ini tidak diganti prototipe.
- **Laboratorium minion**: tiga lane asli, lima tipe minion, combat/regen/death, wave manual, inspeksi.
- **Uji input**: sandbox penanda hijau untuk regresi input/lifecycle. Bukan hero hasil porting.
- **Keluar**.

## Validasi dan batas bukti

- Import + **1.511 native checks Godot 4.7.2** di GitHub Actions Linux telah lulus untuk UI prototipe. Termasuk suite fondasi/minion/siege, fixture wave/income/slots/build-sale, ledger, stale/dead/duplicate transactions, replay 4.200 tick, tiga lifecycle prototype serta kedua pemenang.
- Lokal: 511 guardrail, tiga checker/oracle Python sumber, parser/lint/format GDScript. Scene/resource syntax juga diperiksa; parser pihak ketiga bukan pengganti engine.
- **Belum diuji:** tampilan GPU/screenshots, Windows fisik, resize visual, pertandingan manual panjang/balance, Android export, multi-touch HP, thermal/performa, save/cloud/pembayaran.
- Binary engine di sandbox gagal diunduh karena TLS host aset; jangan mengulang probe atau memakai binary tidak tepercaya. Bukti runtime melalui engine resmi yang dipin dalam CI.
- Log archive CI dapat gagal diunduh; hasil penting diterbitkan sebagai **Checks annotations**, bisa dibaca lewat `gh api`.
- Kegagalan pertama inti (6 dari 1.418 checks) disebabkan nested Array comparison terhadap angka float JSON. Sudah diperbaiki dengan perbandingan scalar exact, tanpa truncation/toleransi dan tanpa mengubah scheduler; CI sesudahnya lulus.

## File utama dan aturan penting

- [`../godot_rebuild/README.md`](../godot_rebuild/README.md): cara menjalankan di Windows dan checklist manual.
- [`../godot_rebuild/COMBAT_CONTRACT.md`](../godot_rebuild/COMBAT_CONTRACT.md), [`SIEGE_CONTRACT.md`](../godot_rebuild/SIEGE_CONTRACT.md), [`MATCH_CONTRACT.md`](../godot_rebuild/MATCH_CONTRACT.md): aturan sumber, batas scope, deviasi yang disengaja.
- `app/app.gd`: navigasi deferred/satu screen; `start_prototype`, `start_siege`, `start_combat`, `start_match` (sandbox). Restart terikat ke scene asal.
- `scripts/combat/`: RefCounted worlds, ID monotonic, satu death/credit, shield dan projectile. `structure_limit()` default 16, override prototipe 20.
- `scripts/match/`: `wave_scheduler`, `match_economy`, `slot_layout`, `build_slot`, `prototype_battle`.
- `scripts/simulation/prototype_session.gd`: immutable command IDs, satu command/tick, cancel saat pause/focus. Tidak ada manual wave dalam mode ini.
- `scenes/prototype/`: HUD, hasil otomatis, input berskala dan view read-only yang memakai renderer siege.
- `tests/match_source_oracle.py`: potongan AST sumber asli; `fixtures/match_source.json`; `prototype_checks.gd` dan `run_all.gd` untuk domain/lifecycle.
- `tests/check_source_contract.py`, `structure_source_oracle.py`: minion/lane serta metode numerik Tower/Castle.
- `.github/workflows/godot-rebuild.yml`: engine resmi 4.7.2, oracle/parser/lint, import + tes native. Memantau sumber kontrak termasuk `levels/level_data.py`.

Ringkasan aturan yang rawan salah:

- Wave pertama **tick 301**, queue tetap dikuras setiap 20 tick saat timer 1500 berjalan; wave berikutnya menunggu lapangan bersih. Komposisi berdasarkan castle tier 1, bukan indeks nomor wave.
- Level 1 normal **1000 G**; lawan 350 G. Passive milli-gold memakai ties-to-even Python; income sebelum scheduler. Jual tier 1 **50 G** berasal dari fallback UI, bukan `Tower.sell_value()` yang bernilai 0.
- Build/sale harus validasi sebelum mutasi; dead/duplicate/stale sale tidak memberi refund. Death membebaskan slot (perbaikan bug sumber yang disengaja). Sale membatalkan projectile terkait tanpa kill reward.
- Lawan sementara membeli pada tick 300/600/900, bukan AIPlayer asli. Tidak ada castle auto-scaling, upgrade, hero/boss, save, ekonomi permanen atau paid shield.
- Archer HP efektif 2000 + shield 800; armor sebelum shield. Nexus shield dulu, lalu reduksi 88% saat perlindungan aktif; jangan menyamakan formulanya. Nexus wave 11 mematikan shield gratis.
- Batas prototipe: 120 minion / 20 struktur / 256 projectile / 64 event; antrean menahan spawn bila penuh. Hasil nexus membekukan economy/world dan membatalkan antrean.

## Langkah berikutnya

1. Minta/terima hasil uji Windows melalui F5 → **Pertandingan awal**; perbaiki error sebelum menambah konten.
2. Audit upgrade Archer/nexus, harga/refund sesudah upgrade serta formula level sebelum memperluas transaksi; buat oracle baru, jangan menebak tabel stat mentah.
3. Audit satu hero/skill dan AI sumber secara bertahap. Ganti lawan sementara hanya setelah perilakunya diuji; jangan mengklaim scripted builder sebagai AI penuh.
4. Lengkapi satu pertandingan kecil, lalu level/boss/konten/UI/audio. Android pilot dan profiling harus dibuktikan pada perangkat, bukan dengan headless Linux.
5. Push bertahap pada branch yang sama, pantau CI dan perbarui handoff ini.

## Perintah praktis

```text
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
python godot_rebuild/tests/structure_source_oracle.py
python godot_rebuild/tests/match_source_oracle.py
gh run list --branch arena/01a0d776-mystic-arena --limit 5 --json databaseId,status,conclusion,headSha,url
gh api repos/dharmawantoxi/mystic-arena/check-runs/CHECK_ID/annotations
git push origin arena/01a0d776-mystic-arena
```

Windows: `powershell -ExecutionPolicy Bypass -File .\tests\run_windows.ps1 -Godot "C:\Tools\Godot_v4.7.2-stable_win64_console.exe"` dari `godot_rebuild/`.

`gh pr edit` pada versi CLI sandbox pernah gagal karena Projects classic deprecated. Gunakan REST PATCH `gh api --method PATCH repos/dharmawantoxi/mystic-arena/pulls/278` untuk title/body. Jangan menyimpan credential, binary engine, `.godot/`, save nyata atau output build di repo. Jangan menjalankan generator migrasi lama atau scratch script lama yang dapat menimpa proyek ini.

## Checkpoint lanjutan: inti upgrade Archer (native CI menunggu)

- Audit nexus menunjukkan dependensi minion scaling/composition/AI tier; belum diaktifkan agar tidak menjadi upgrade HP parsial.
- Archer level 1–6: resource native, full HP/shield reset saat upgrade, cooldown/regen timer/shot yang sudah terbang tetap; harga 175/325/550/850/1300 G, refund 50/87/250/525/950/1600 G.
- Level 5 dua panah, level 6 tiga; source `_shoot_archer` menentukan perilaku, bukan label tabel “double shot”. Whole-volley cap atomik merupakan guard tambahan.
- `upgrade_source_oracle.py` menjalankan metode asli upgrade/refund/muzzle/volley; 36 skenario volley. Tes domain ditambahkan. Inti belum ada tombol UI pada checkpoint ini; menunggu native CI sebelum klaim runtime.
