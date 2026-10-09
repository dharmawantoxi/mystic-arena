plugins {
    id("com.android.library")
}

val pluginPackage = "io.github.dharmawantoxi.mysticarena.godot"
val idFile = rootProject.file("../../android_games_app_id.txt")
val configuredProjectId = providers.gradleProperty("mysticGamesProjectId").orNull
    ?: System.getenv("MYSTIC_GODOT_GAMES_PROJECT_ID")
    ?: if (idFile.isFile) idFile.readText().trim() else ""
val gamesProjectId = configuredProjectId.takeIf { it.matches(Regex("[1-9][0-9]{5,19}")) } ?: "0"

android {
    namespace = pluginPackage
    compileSdk = 36

    defaultConfig {
        minSdk = 24
        resValue("string", "game_services_project_id", gamesProjectId)
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    sourceSets {
        getByName("main").java.srcDirs("src/main/java", "../../../../src")
    }
}

dependencies {
    implementation("org.godotengine:godot:4.7.2.stable")
    implementation("com.google.android.gms:play-services-games-v2:22.0.0")
}
