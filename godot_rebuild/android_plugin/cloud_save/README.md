# Godot Android Cloud Save plugin

`godot_rebuild/addons/mystic_cloud` is the Godot Android plugin-v2 export addon. Build its ignored debug/release AARs before Android export with JDK 17, Android SDK 36, and Gradle 8.14.3:

```sh
godot_rebuild/android_plugin/cloud_save/build_plugin.sh
```

Set the Google Play Games project ID using `MYSTIC_GODOT_GAMES_PROJECT_ID` or the local, gitignored `godot_rebuild/android_games_app_id.txt`. The build embeds it as `game_services_project_id`; without a valid ID the plugin loads inertly and the game keeps its local Godot saves. Runtime slot, speed-setting, status, and transfer files stay under Godot's own user-data directory; the plugin never reads Pygame save storage.
