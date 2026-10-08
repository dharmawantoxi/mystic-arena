package io.github.dharmawantoxi.mysticarena.godot;

import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;

import org.godotengine.godot.Godot;
import org.godotengine.godot.plugin.GodotPlugin;
import org.godotengine.godot.plugin.UsedByGodot;

import io.github.dharmawantoxi.mysticarena.CloudSaveBridge;

public final class GodotCloudSavePlugin extends GodotPlugin {
    private volatile boolean available;

    public GodotCloudSavePlugin(Godot godot) {
        super(godot);
    }

    @Override
    public String getPluginName() {
        return "MysticCloudSave";
    }

    @UsedByGodot
    public synchronized boolean initialize(String workDirectory) {
        if (available) {
            return true;
        }
        if (getActivity() == null || !hasProjectId()) {
            return false;
        }
        try {
            CloudSaveBridge.init(getActivity(), workDirectory);
            available = CloudSaveBridge.isAvailable() && CloudSaveBridge.isInitialized();
        } catch (Throwable ignored) {
            available = false;
        }
        return available;
    }

    @UsedByGodot
    public boolean isAvailable() {
        return available;
    }

    @UsedByGodot
    public boolean isSignedIn() {
        return available && CloudSaveBridge.isSignedIn();
    }

    @UsedByGodot
    public void checkAuthAsync(String operationId) {
        if (available) {
            CloudSaveBridge.checkAuthAsync(operationId);
        }
    }

    @UsedByGodot
    public void signInAsync(String operationId) {
        if (available) {
            CloudSaveBridge.signInAsync(operationId);
        }
    }

    @UsedByGodot
    public void uploadAsync(String filePath, String operationId) {
        if (available) {
            CloudSaveBridge.uploadAsync(filePath, operationId);
        }
    }

    @UsedByGodot
    public void downloadAsync(String filePath, String operationId) {
        if (available) {
            CloudSaveBridge.downloadAsync(filePath, operationId);
        }
    }

    private boolean hasProjectId() {
        try {
            ApplicationInfo info = getActivity().getPackageManager().getApplicationInfo(
                    getActivity().getPackageName(), PackageManager.GET_META_DATA);
            Bundle metadata = info.metaData;
            if (metadata == null) {
                return false;
            }
            Object value = metadata.get("com.google.android.gms.games.APP_ID");
            if (value == null) {
                return false;
            }
            String projectId = String.valueOf(value).trim();
            return projectId.matches("[1-9][0-9]{5,19}");
        } catch (Throwable ignored) {
            return false;
        }
    }
}
