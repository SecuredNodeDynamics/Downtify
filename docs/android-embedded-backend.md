# Embedded (serverless) Android backend

By default the Downtify APK is a thin client that talks to a Downtify server.
The **embedded backend** lets the APK run the *entire* Python backend
in-process so it can search, download, transcode and tag audio fully on-device
— no external server required.

This is implemented by embedding a Python runtime in the APK with
[Chaquopy](https://chaquo.com/chaquopy/) and serving the existing FastAPI app
on `http://127.0.0.1:8765`. The Capacitor WebView then talks to that local
server exactly as it would a remote one.

## How it works

```
WebView (Vue app)  ──HTTP──▶  127.0.0.1:8765  (FastAPI via uvicorn)
        ▲                              │
        │                             yt-dlp + bundled ffmpeg + mutagen
   bundled UI assets                   │
                                  downloads on device
```

- `EmbeddedServerPlugin` (Java) starts the Python interpreter via Chaquopy on a
  background thread in `MainActivity.onCreate` and calls
  `downtify.mobile.run_server(...)`.
- `downtify/mobile.py` configures app-writable data/download directories,
  disables the SPA mount (`DOWNTIFY_SERVE_SPA=0`), wires up the bundled ffmpeg,
  and runs uvicorn.
- On the web app, `frontend/src/model/embeddedServer.js` is a no-op. On the
  APK it starts the server, waits for `/api/version`, and reloads once it's
  reachable. `serverConnection.js` defaults the native server URL to the
  embedded one (a user-set remote URL in Settings still takes precedence).

## Key constraints (read before building)

1. **Pydantic v1 is pinned.** FastAPI normally uses Pydantic v2, whose
   `pydantic-core` is a Rust extension with **no prebuilt Android wheel**
   ([chaquopy#1017](https://github.com/chaquo/chaquopy/issues/1017)). We install
   `pydantic<2` (pure Python) in the Chaquopy `pip` block; FastAPI runs fine on
   it. If you bump FastAPI, verify it still supports Pydantic v1.
2. **ffmpeg must be supplied per ABI.** See
   `frontend/android/app/src/main/jniLibs/README.md`. Without it, search/browse
   work but downloads that need conversion fail.
3. **APK size.** The Python runtime + dependencies + ffmpeg add tens of MB.
4. **AGP/Chaquopy compatibility.** The Android Gradle Plugin version must be one
   Chaquopy supports. If the build fails at the Chaquopy step, align versions per
   the [Chaquopy version table](https://chaquo.com/chaquopy/doc/current/versions.html).
5. **yt-dlp freshness.** On-device extraction depends on the bundled yt-dlp
   version; ship app updates regularly so YouTube changes don't break downloads.

## Building

1. Provide ffmpeg binaries (see the jniLibs README) for `arm64-v8a` (devices)
   and `x86_64` (emulator).
2. Build as usual:

   ```bash
   bash scripts/build-android-apk.sh
   ```

   The Gradle build stages `main.py` + `downtify/` into the Chaquopy source set
   and installs the Python dependencies. The build script warns if no ffmpeg is
   present.

## Switching between embedded and remote

- **Default (no config):** uses the on-device server.
- **Use a remote server:** set the server URL in Settings → API. This overrides
  the embedded default.
- **Back to embedded:** clear the server URL in Settings.

## Where downloads go

The embedded server saves into the app's external files directory
(`Android/data/com.securednodedynamics.downtify/files/Music`), visible via file
managers without extra permissions. The SAF folder picker ("This device") is
still available for the web/remote flows.

## Troubleshooting

- **App shows "server required" / blank data:** the Python server may still be
  starting (first launch is slowest) or crashed. Check `adb logcat` for the
  `EmbeddedServer` tag and Python tracebacks.
- **Downloads fail at "Converting":** ffmpeg isn't bundled or isn't executable.
  Verify `adb shell <nativeLibraryDir>/libffmpeg.so -version`.
- **Build fails installing `pydantic`/`fastapi`:** a version is pulling in
  Pydantic v2. Keep `pydantic<2` and a FastAPI release that supports it.
