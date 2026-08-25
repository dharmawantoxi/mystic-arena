// ================================================================
// CloudSaveBridge.java
// Jembatan Cloud Save Mystic Arena ke Google Play Games Saved Games
// (Snapshots API, Play Games Services v2 / com.google.android.gms:play-services-games-v2).
//
// DIPANGGIL DARI PYTHON (pyjnius) — kelas ini sangat tipis dan SEMUA
// error dibungkus try/catch supaya:
//   * Kalau perangkat tidak punya Google Play Services -> fitur mati
//     diam-diam, game tetap jalan.
//   * Kalau APP_ID belum diset di Play Console -> fitur mati
//     diam-diam, game tetap jalan + log jelas.
//   * File save sama sekali TIDAK boleh hilang karena cloud gagal.
//
// PROTOKOL KOMUNIKASI KE PYTHON (file based, tanpa listener Java):
//      <workdir>/cloud_status.json
// Java menulis ulang file ini setiap kali operasi selesai, lalu
// Python membacanya. Python tidak perlu meng-implementasikan
// interface Java (tidak perlu PythonJavaClass).
//
// Format cloud_status.json:
// {
//   "op_id": "<id operasi dari Python>",
//   "kind":  "init|check|signin|upload|download",
//   "ok":    true/false,
//   "code":  <0 sukses, !=0 gagal>,
//   "message": "...",
//   "file_path": "<path file hasil download (opsional)>",
//   "signed_in": true/false,
//   "ts": <epoch millis>
// }
// ================================================================

package io.github.dharmawantoxi.mysticarena;

import android.app.Activity;
import android.content.Context;
import android.util.Log;

import com.google.android.gms.games.GamesSignInClient;
import com.google.android.gms.games.AuthenticationResult;
import com.google.android.gms.games.PlayGames;
import com.google.android.gms.games.PlayGamesSdk;
import com.google.android.gms.games.SnapshotsClient;
import com.google.android.gms.games.snapshot.Snapshot;
import com.google.android.gms.games.snapshot.SnapshotMetadata;
import com.google.android.gms.games.snapshot.SnapshotMetadataChange;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public final class CloudSaveBridge {

    private static final String TAG = "MysticCloudSave";

    // Snapshot unik per akun pemain di folder App Data Play Games.
    private static final String DEFAULT_SNAPSHOT_NAME = "mystic_arena_main";

    private static final String STATUS_FILENAME = "cloud_status.json";

    private static Context appContext;
    private static File statusDir;
    private static GamesSignInClient signInClient;
    private static SnapshotsClient snapshotsClient;
    private static volatile boolean signedIn = false;
    private static volatile boolean initialized = false;

    private CloudSaveBridge() {
        // utility class, tidak boleh di-instantiate
    }

    // ----------------------------------------------------------
    // INIT / DETEKSI KETERSEDIAAN
    // ----------------------------------------------------------

    /**
     * Cek (tanpa melempar exception) apakah kelas Play Games
     * tersedia di classpath. Kalau belum / gagal, return false dan
     * Python tidak akan mencoba sign-in.
     */
    public static boolean isAvailable() {
        try {
            Class.forName("com.google.android.gms.games.PlayGamesSdk");
            Class.forName("com.google.android.gms.games.PlayGames");
            return true;
        } catch (Throwable t) {
            Log.w(TAG, "Play Games tidak tersedia di classpath", t);
            return false;
        }
    }

    /**
     * Dipanggil sekali dari Python saat game mulai.
     * workDirPath = folder boleh-tulis yang sama dipakai Python untuk
     * menaruh file upload/download sementara (biasanya ANDROID_PRIVATE).
     */
    public static void init(Activity activity, String workDirPath) {
        if (initialized) {
            return;
        }
        if (activity == null) {
            writeStatus("init", "init", false, 100,
                    "CloudSaveBridge.init tanpa Activity", null, signedIn);
            return;
        }

        appContext = activity.getApplicationContext();
        statusDir = new File(statusDirPath(workDirPath));
        if (!statusDir.exists()) {
            statusDir.mkdirs();
        }

        try {
            // SDK v2: initialize di sini (secara idiomatis di onCreate
            // Application, tapi untuk app yang di-bootstrap p4a kita
            // lakukan saat modul cloud dipakai). Error dilempar kalau
            // meta-data APP_ID belum ada di manifest -> ditangkap.
            PlayGamesSdk.initialize(appContext);
            signInClient = PlayGames.getGamesSignInClient(activity);
            snapshotsClient = PlayGames.getSnapshotsClient(activity);
            initialized = true;
            writeStatus("init", "init", true, 0,
                    "Play Games siap", null, signedIn);
            Log.i(TAG, "Cloud save diinisialisasi.");
        } catch (Throwable t) {
            initialized = false;
            Log.e(TAG, "Init Play Games gagal (APP_ID belum diset?)", t);
            writeStatus("init", "init", false, 101,
                    "Init Play Games gagal: " + shortMessage(t), null, signedIn);
        }
    }

    public static boolean isInitialized() {
        return initialized;
    }

    public static boolean isSignedIn() {
        return signedIn;
    }

    // ----------------------------------------------------------
    // AUTH
    // ----------------------------------------------------------

    /**
     * Cek hasil autentikasi otomatis Play Games (dipanggil saat game
     * mulai). Tidak memunculkan dialog.
     */
    public static void checkAuthAsync(String opId) {
        if (!initialized || signInClient == null) {
            writeStatus("check", opId, false, 102,
                    "Play Games belum siap", null, signedIn);
            return;
        }
        try {
            signInClient.isAuthenticated()
                    .addOnCompleteListener(
                            new OnCompleteListener<AuthenticationResult>() {
                                @Override
                                public void onComplete(
                                        Task<AuthenticationResult> task) {
                                    boolean ok = task.isSuccessful()
                                            && task.getResult() != null
                                            && task.getResult().isAuthenticated();
                                    signedIn = ok;
                                    writeStatus("check", opId, true, 0,
                                            ok ? "Sudah masuk" : "Belum masuk",
                                            null, signedIn);
                                }
                            });
        } catch (Throwable t) {
            Log.e(TAG, "checkAuthAsync gagal", t);
            writeStatus("check", opId, false, 103,
                    "checkAuth gagal: " + shortMessage(t), null, signedIn);
        }
    }

    /**
     * Sign-in interaktif ala Play Games v2 (memunculkan dialog pilih
     * akun kalau perlu).
     */
    public static void signInAsync(String opId) {
        if (!initialized || signInClient == null) {
            writeStatus("signin", opId, false, 104,
                    "Play Games belum siap", null, signedIn);
            return;
        }
        try {
            signInClient.signIn()
                    .addOnCompleteListener(
                            new OnCompleteListener<AuthenticationResult>() {
                                @Override
                                public void onComplete(
                                        Task<AuthenticationResult> task) {
                                    boolean ok = task.isSuccessful()
                                            && task.getResult() != null
                                            && task.getResult().isAuthenticated();
                                    signedIn = ok;
                                    writeStatus("signin", opId, ok, ok ? 0 : 105,
                                            ok ? "Berhasil masuk"
                                                    : "Gagal masuk: "
                                                    + shortMessage(task.getException()),
                                            null, signedIn);
                                }
                            });
        } catch (Throwable t) {
            Log.e(TAG, "signInAsync gagal", t);
            writeStatus("signin", opId, false, 106,
                    "signIn gagal: " + shortMessage(t), null, signedIn);
        }
    }

    // ----------------------------------------------------------
    // SNAPshots (upload / download)
    // ----------------------------------------------------------

    /**
     * Unggah file ke cloud (snapshot App Data pemain, disinkronkan
     * otomatis offline->online oleh Google).
     */
    public static void uploadAsync(String filePath, String opId) {
        uploadAsync(filePath, DEFAULT_SNAPSHOT_NAME, "Mystic Arena save", opId);
    }

    public static void uploadAsync(String filePath, String uniqueName,
                                   String description, String opId) {
        if (!initialized || snapshotsClient == null) {
            writeStatus("upload", opId, false, 107,
                    "Cloud belum siap / belum masuk", null, signedIn);
            return;
        }
        final File src = new File(filePath);
        if (!src.exists()) {
            writeStatus("upload", opId, false, 108,
                    "File upload tidak ditemukan", null, signedIn);
            return;
        }

        try {
            final byte[] data = readAll(src);
            final String name = uniqueName;
            final String desc = description;
            final int policy = SnapshotsClient.RESOLUTION_POLICY_MOST_RECENTLY_MODIFIED;

            snapshotsClient.open(name, true, policy)
                    .addOnCompleteListener(
                            new OnCompleteListener<SnapshotsClient.DataOrConflict<Snapshot>>() {
                                @Override
                                public void onComplete(
                                        Task<SnapshotsClient.DataOrConflict<Snapshot>> task) {
                                    if (!task.isSuccessful()) {
                                        writeStatus("upload", opId, false, 109,
                                                "Buka snapshot gagal: "
                                                        + shortMessage(task.getException()),
                                                null, signedIn);
                                        return;
                                    }
                                    final Snapshot snapshot =
                                            task.getResult().getData();
                                    if (snapshot == null) {
                                        writeStatus("upload", opId, false, 110,
                                                "Snapshot kosong", null, signedIn);
                                        return;
                                    }
                                    try {
                                        snapshot.getSnapshotContents().writeBytes(data);
                                        SnapshotMetadataChange meta =
                                                new SnapshotMetadataChange.Builder()
                                                        .setDescription(desc)
                                                        .build();
                                        snapshotsClient.commitAndClose(snapshot, meta)
                                                .addOnCompleteListener(
                                                        new OnCompleteListener<SnapshotMetadata>() {
                                                            @Override
                                                            public void onComplete(
                                                                    Task<SnapshotMetadata> commit) {
                                                                if (commit.isSuccessful()) {
                                                                    writeStatus("upload", opId,
                                                                            true, 0,
                                                                            "Save terunggah ke cloud",
                                                                            null, signedIn);
                                                                } else {
                                                                    writeStatus("upload", opId,
                                                                            false, 111,
                                                                            "Commit snapshot gagal: "
                                                                                    + shortMessage(commit.getException()),
                                                                            null, signedIn);
                                                                }
                                                            }
                                                        });
                                    } catch (Throwable t) {
                                        writeStatus("upload", opId, false, 112,
                                                "Tulis data snapshot gagal: "
                                                        + shortMessage(t),
                                                null, signedIn);
                                    }
                                }
                            });
        } catch (Throwable t) {
            Log.e(TAG, "uploadAsync gagal", t);
            writeStatus("upload", opId, false, 113,
                    "Upload gagal: " + shortMessage(t), null, signedIn);
        }
    }

    /**
     * Unduh snapshot dari cloud ke file lokal (destFilePath).
     */
    public static void downloadAsync(String destFilePath, String opId) {
        downloadAsync(destFilePath, DEFAULT_SNAPSHOT_NAME, opId);
    }

    public static void downloadAsync(String destFilePath, String uniqueName,
                                     String opId) {
        if (!initialized || snapshotsClient == null) {
            writeStatus("download", opId, false, 114,
                    "Cloud belum siap / belum masuk", null, signedIn);
            return;
        }
        try {
            final int policy = SnapshotsClient.RESOLUTION_POLICY_MOST_RECENTLY_MODIFIED;
            // createIfNotFound=false: JANGAN membuat snapshot kosong
            // saat pemain belum pernah upload (download = hanya baca).
            snapshotsClient.open(uniqueName, false, policy)
                    .addOnCompleteListener(
                            new OnCompleteListener<SnapshotsClient.DataOrConflict<Snapshot>>() {
                                @Override
                                public void onComplete(
                                        Task<SnapshotsClient.DataOrConflict<Snapshot>> task) {
                                    if (!task.isSuccessful()) {
                                        writeStatus("download", opId, false, 115,
                                                "Buka snapshot gagal: "
                                                        + shortMessage(task.getException()),
                                                null, signedIn);
                                        return;
                                    }
                                    final Snapshot snapshot =
                                            task.getResult().getData();
                                    if (snapshot == null) {
                                        writeStatus("download", opId, false, 116,
                                                "Snapshot kosong", null, signedIn);
                                        return;
                                    }
                                    try {
                                        byte[] data = snapshot.getSnapshotContents().readFully();
                                        if (data == null || data.length == 0) {
                                            writeStatus("download", opId, false, 117,
                                                    "Snapshot kosong (belum ada save cloud)",
                                                    null, signedIn);
                                            return;
                                        }
                                        writeAll(new File(destFilePath), data);
                                        writeStatus("download", opId, true, 0,
                                                "Save diunduh dari cloud",
                                                destFilePath, signedIn);
                                    } catch (Throwable t) {
                                        writeStatus("download", opId, false, 118,
                                                "Baca/tulis snapshot gagal: "
                                                        + shortMessage(t),
                                                null, signedIn);
                                    }
                                }
                            });
        } catch (Throwable t) {
            Log.e(TAG, "downloadAsync gagal", t);
            writeStatus("download", opId, false, 119,
                    "Download gagal: " + shortMessage(t), null, signedIn);
        }
    }

    // ----------------------------------------------------------
    // STATUS FILE (dibaca Python)
    // ----------------------------------------------------------

    private static String statusDirPath(String workDirPath) {
        if (workDirPath != null && workDirPath.length() > 0) {
            return workDirPath;
        }
        if (appContext != null) {
            return appContext.getFilesDir().getAbsolutePath();
        }
        return ".";
    }

    private static void writeStatus(String kind, String opId, boolean ok,
                                    int code, String message,
                                    String filePath, boolean signedInFlag) {
        try {
            if (statusDir == null) {
                return;
            }
            File out = new File(statusDir, STATUS_FILENAME);
            File tmp = new File(statusDir, STATUS_FILENAME + ".tmp");
            JSONObject o = new JSONObject();
            o.put("op_id", opId == null ? "" : opId);
            o.put("kind", kind == null ? "" : kind);
            o.put("ok", ok);
            o.put("code", code);
            o.put("message", message == null ? "" : message);
            o.put("file_path", filePath == null ? "" : filePath);
            o.put("signed_in", signedInFlag);
            o.put("ts", System.currentTimeMillis());

            FileOutputStream fos = new FileOutputStream(tmp);
            try {
                fos.write(o.toString().getBytes("UTF-8"));
                fos.flush();
            } finally {
                fos.close();
            }
            if (out.exists()) {
                out.delete();
            }
            if (!tmp.renameTo(out)) {
                // fallback: tulis langsung
                fos2(out, o.toString().getBytes("UTF-8"));
            }
        } catch (Throwable t) {
            Log.e(TAG, "writeStatus gagal", t);
        }
    }

    private static void fos2(File f, byte[] bytes) {
        try (FileOutputStream fos = new FileOutputStream(f)) {
            fos.write(bytes);
        } catch (Exception e) {
            Log.e(TAG, "fos2 gagal", e);
        }
    }

    // ----------------------------------------------------------
    // HELPERS
    // ----------------------------------------------------------

    private static String shortMessage(Throwable t) {
        if (t == null) {
            return "unknown error";
        }
        String m = t.getMessage();
        if (m != null && m.length() > 0) {
            return m;
        }
        return t.getClass().getSimpleName();
    }

    private static byte[] readAll(File f) throws IOException {
        FileInputStream in = new FileInputStream(f);
        try {
            long len = f.length();
            byte[] data = new byte[(int) Math.min(len, Integer.MAX_VALUE - 8)];
            int off = 0;
            int r;
            while (off < data.length && (r = in.read(data, off, data.length - off)) > 0) {
                off += r;
            }
            if (off != data.length) {
                throw new IOException("File berubah saat dibaca: " + f);
            }
            return data;
        } finally {
            in.close();
        }
    }

    private static void writeAll(File f, byte[] data) throws IOException {
        File parent = f.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();
        }
        File tmp = new File(parent, f.getName() + ".tmp");
        try (FileOutputStream fos = new FileOutputStream(tmp)) {
            fos.write(data);
            fos.flush();
        }
        if (f.exists()) {
            f.delete();
        }
        if (!tmp.renameTo(f)) {
            try (FileOutputStream fos = new FileOutputStream(f)) {
                fos.write(data);
            }
            tmp.delete();
        }
    }
}
