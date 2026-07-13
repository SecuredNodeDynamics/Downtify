# Embedded (serverless) Android backend

By default the Downtify APK can run the *entire* Python backend in-process so it
can search, download, transcode and tag audio fully on-device — no external
server required. Users can still point the app at a remote Downtify server in
Settings → API; that remote URL overrides the embedded backend.

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
  APK it starts the server and waits for `/api/version`. The Vue app mounts
  immediately and shows the "Starting local engine..." overlay while the Python
  backend comes up. If `/api/version` does not become reachable, the overlay
  shows an error and a retry button instead of leaving the user on a blank
  screen. `serverConnection.js` defaults the native server URL to the embedded
  one (a user-set remote URL in Settings still takes precedence).
- Frontend warmups are intentionally delayed until after the UI has mounted,
  painted, and the backend session confirms `/api/version`. Library prefetch,
  WebSocket startup, and cover cache warming should not happen at module import
  time on the APK.
- Backend warmups are staggered after FastAPI startup so `/api/version` is
  available quickly. The monitor loop starts immediately, then non-critical
  jobs are delayed: download-history reconciliation, library-file cache warming,
  monitor image backfill, and genre warmup.

## Key constraints (read before building)

1. **Pydantic v1 is pinned.** FastAPI normally uses Pydantic v2, whose
   `pydantic-core` is a Rust extension with **no prebuilt Android wheel**
   ([chaquopy#1017](https://github.com/chaquo/chaquopy/issues/1017)). We install
   `pydantic<2` (pure Python) in the Chaquopy `pip` block; FastAPI runs fine on
   it. If you bump FastAPI, verify it still supports Pydantic v1.
2. **ffmpeg must be supplied per ABI for MP3/FLAC.** Build it with
   `bash scripts/build-android-ffmpeg.sh` (cross-compiles libmp3lame + a static
   ffmpeg/ffprobe CLI into `jniLibs/<abi>/lib*.so`). See
   `frontend/android/app/src/main/jniLibs/README.md`. Without it, search/browse
   work and downloads still succeed as native **M4A (AAC)**, but MP3/FLAC
   conversion is unavailable. The app probes ffmpeg's encoders at runtime
   (`downtify/audio_caps.py`, `/api/capabilities`) and only offers formats it
   can produce.
3. **APK size.** The Python runtime + dependencies + ffmpeg add tens of MB.
4. **AGP/Chaquopy compatibility.** The Android Gradle Plugin version must be one
   Chaquopy supports. If the build fails at the Chaquopy step, align versions per
   the [Chaquopy version table](https://chaquo.com/chaquopy/doc/current/versions.html).
5. **yt-dlp freshness.** On-device extraction depends on the bundled yt-dlp
   version; ship app updates regularly so YouTube changes don't break downloads.

## Building

1. Provide ffmpeg binaries for `arm64-v8a` (devices) and `x86_64` (emulator):

   ```bash
   bash scripts/build-android-ffmpeg.sh
   ```

   (see the jniLibs README for prerequisites and options).
2. Build as usual:

   ```bash
   bash scripts/build-android-apk.sh
   ```

   The Gradle build stages `main.py` + `downtify/` into the Chaquopy source set
   and installs the Python dependencies. The build script warns if no ffmpeg is
   present.
3. Before release, run the [APK smoke-test checklist](android-apk-smoke-test.md).

   It includes launch, local engine startup, Health/ffmpeg detection, search,
   M4A download, playback, monitor, update install, Android Auto, and large
   library scrolling checks.

## Startup sequence

The APK startup path is optimized so the user sees UI before expensive work
starts:

1. Android launches the Capacitor WebView and the Java `EmbeddedServerPlugin`.
2. Vue mounts immediately and renders the normal shell plus `StarField`.
3. `bootstrapEmbeddedServer()` starts or reconnects to the embedded Python
   backend.
4. While `/api/version` is not ready, the app shows **Starting local engine...**.
5. When `/api/version` responds, the app dispatches
   `downtify-embedded-server-ready` so cover/monitor components can retry any
   early failed local requests.
6. After two animation frames, `API.startBackendSession()` writes the connected
   server version, opens the WebSocket, and schedules library prefetch/cover
   warming.
7. FastAPI startup keeps `/api/version` responsive first, then runs heavier
   background warmups on delays.

Avoid reintroducing API calls at frontend module import time. Anything that can
scan the library, warm images, open WebSockets, or hit the embedded backend
should run from mounted app code after the version check.

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

- **App shows "Starting local engine..." for a long time:** the Python server is
  still booting or `/api/version` is not reachable yet. First launch after
  install can be slower than warm launches.
- **App shows "Local engine did not start":** tap **Retry** once. If it still
  fails, check `adb logcat` for the `EmbeddedServer` tag and Python tracebacks.
- **App shows "server required" / blank data:** make sure Settings → API is set
  to the intended mode. A saved remote server URL overrides the embedded
  default; clearing the URL returns to the on-device backend.
- **Downloads fail at "Converting":** ffmpeg isn't bundled or isn't executable.
  Verify `adb shell <nativeLibraryDir>/libffmpeg.so -version`.
- **Build fails installing `pydantic`/`fastapi`:** a version is pulling in
  Pydantic v2. Keep `pydantic<2` and a FastAPI release that supports it.
