package io.github.dharmawantoxi.mysticarena;

import android.app.Activity;
import android.util.Log;

import org.godotengine.godot.Godot;
import org.godotengine.godot.plugin.GodotPlugin;
import org.godotengine.godot.plugin.UsedByGodot;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/** Godot Android v2 adapter around the shared Play Games Snapshots bridge. */
public final class MysticCloudSavePlugin extends GodotPlugin {

    private static final String TAG = "MysticCloudSavePlugin";
    private static final String WORK_DIR_NAME = "mystic_cloud";
    private volatile File statusFile;

    public MysticCloudSavePlugin(Godot godot) {
        super(godot);
        Activity activity = godot.getActivity();
        if (activity != null) {
            statusFile = new File(
                    new File(activity.getFilesDir(), WORK_DIR_NAME),
                    "cloud_status.json");
        }
    }

    @Override
    public String getPluginName() {
        return "MysticCloudSave";
    }

    @UsedByGodot
    public boolean initializeBridge() {
        Activity activity = getActivity();
        if (activity == null) {
            Log.w(TAG, "Godot Activity belum tersedia");
            return false;
        }
        File workDir = new File(activity.getFilesDir(), WORK_DIR_NAME);
        if (!workDir.exists() && !workDir.mkdirs()) {
            Log.w(TAG, "Folder status cloud tidak dapat dibuat");
            return false;
        }
        statusFile = new File(workDir, "cloud_status.json");
        CloudSaveBridge.init(activity, workDir.getAbsolutePath());
        return CloudSaveBridge.isAvailable() && CloudSaveBridge.isInitialized();
    }

    @UsedByGodot
    public boolean isAvailable() {
        return CloudSaveBridge.isAvailable() && CloudSaveBridge.isInitialized();
    }

    @UsedByGodot
    public boolean isSignedIn() {
        return CloudSaveBridge.isSignedIn();
    }

    @UsedByGodot
    public void checkAuthAsync(String opId) {
        CloudSaveBridge.checkAuthAsync(opId);
    }

    @UsedByGodot
    public void signInAsync(String opId) {
        CloudSaveBridge.signInAsync(opId);
    }

    @UsedByGodot
    public void uploadAsync(String absolutePath, String opId) {
        CloudSaveBridge.uploadAsync(absolutePath, opId);
    }

    @UsedByGodot
    public void downloadAsync(String absolutePath, String opId) {
        CloudSaveBridge.downloadAsync(absolutePath, opId);
    }

    /** Read at most 64 KiB; the status protocol is a single small JSON object. */
    @UsedByGodot
    public String readStatusJson() {
        File file = statusFile;
        if (file == null || !file.isFile() || file.length() > 65536L) {
            return "";
        }
        try (FileInputStream input = new FileInputStream(file);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[2048];
            int count;
            while ((count = input.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            return output.toString(StandardCharsets.UTF_8.name());
        } catch (IOException exception) {
            Log.w(TAG, "Status cloud tidak terbaca", exception);
            return "";
        }
    }
}
