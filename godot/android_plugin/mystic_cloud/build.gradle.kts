plugins {
    id("com.android.library") version "8.10.1" apply false
}

val projectIdPattern = Regex("^[0-9]{1,20}$")
val envProjectId = providers.environmentVariable("MYSTIC_GAMES_PROJECT_ID")
    .orNull?.trim().orEmpty()
val localProjectIdFile = layout.projectDirectory
    .file("../../../android_games_app_id.txt").asFile
val localProjectId = if (localProjectIdFile.isFile) {
    localProjectIdFile.readText().trim()
} else {
    ""
}
val gamesProjectId = (if (envProjectId.isNotEmpty()) envProjectId else localProjectId)
    .takeIf { projectIdPattern.matches(it) }
    .orEmpty()
rootProject.extra["gamesProjectId"] = gamesProjectId

// Copy both variants into the Godot export add-on. Generated AARs are ignored
// by Git; CI and local Android export build them from this source project.
tasks.register<Copy>("copyGodotPluginAars") {
    dependsOn(":MysticCloudSave:assembleDebug", ":MysticCloudSave:assembleRelease")
    from(layout.projectDirectory.file("plugin/build/outputs/aar/MysticCloudSave-debug.aar")) {
        into("debug")
    }
    from(layout.projectDirectory.file("plugin/build/outputs/aar/MysticCloudSave-release.aar")) {
        into("release")
    }
    into(layout.projectDirectory.dir("../../addons/mystic_cloud/bin"))
}
