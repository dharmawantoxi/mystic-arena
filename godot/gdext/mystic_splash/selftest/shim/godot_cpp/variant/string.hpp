// Shim kosong untuk self-test (BUKAN bagian lib GDExtension).
//
// splash_processor.cpp yang di-generate meng-include header godot-cpp berikut;
// di self-test header itu tidak tersedia (kita sengaja tidak menarik godot-cpp),
// jadi include path -Ishim mengarahkannya ke berkas kosong ini. Semua tipe yang
// dibutuhkan disediakan godot_stub.hpp yang sudah di-include lebih dulu oleh
// splash_selftest.cpp. Kalau generator menambah include godot-cpp baru,
// tambahkan shim padanannya di sini — kalau tidak, self-test gagal build.
#pragma once
