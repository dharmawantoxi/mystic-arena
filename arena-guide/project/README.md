# project/ — salinan exact script user

- `Main.gd` ✅ exact copy dari user (2026-09-22 **pasca-L28**).
  L15–L28 lengkap (terrain density, dead trees, shadows, landmarks, slash polish).
  **REGRESI:** `_flame_t += delta` kembali ter-indent di dalam `if wave_timer`
  → animasi torch/rune/firefly/fog hanya jalan saat wave spawn. Fix 1-baris di L29.
- `Minion.gd` ✅ exact copy dari user (2026-09-22).
- Masih menunggu: script lain (Tower/Hero/Shop/HUD/Nexus/LevelDB/...).

Aturan: file di sini hanya diupdate dari paste/upload user, tidak pernah dikarang agent.
