plugins {
    id("com.android.library")
}

val gamesProjectId = rootProject.extra["gamesProjectId"] as String

android {
    namespace = "io.github.dharmawantoxi.mysticarena"
    compileSdk = 36

    defaultConfig {
        minSdk = 24
        // The Android export plugin references this resource only when an
        // actual Play Games project ID is configured.
        resValue("string", "game_services_project_id", gamesProjectId)
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    sourceSets {
        getByName("main") {
            // Reuse the Pygame bridge as the one Java implementation of the
            // Snapshots protocol. Only the thin GodotPlugin wrapper lives here.
            java.srcDir("../../../../src")
        }
    }
}

dependencies {
    implementation("org.godotengine:godot:4.3.0.stable")
    implementation("com.google.android.gms:play-services-games-v2:22.0.0")
}
