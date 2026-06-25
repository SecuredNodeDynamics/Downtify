# Bundled native binaries for the embedded backend

The serverless APK runs `yt-dlp` on-device, which needs an **ffmpeg** binary to
extract/convert audio. Android only allows executing binaries from the app's
native library directory, and only files named `lib*.so` are placed there, so
ffmpeg must be shipped as `libffmpeg.so` (and optionally `libffprobe.so`).

Place a **static** ffmpeg build for each ABI you ship here:

```
src/main/jniLibs/
  arm64-v8a/libffmpeg.so      # required for real devices
  arm64-v8a/libffprobe.so     # optional
  x86_64/libffmpeg.so         # required for the emulator
  x86_64/libffprobe.so        # optional
```

At runtime, `downtify/mobile.py` (`prepare_ffmpeg`) creates `ffmpeg`/`ffprobe`
symlinks pointing at these extracted libraries and passes the directory to
yt-dlp via `DOWNTIFY_FFMPEG_LOCATION`, so they are discovered by name.

## Building them (recommended)

Run the helper script, which cross-compiles **libmp3lame** (for MP3) and a
statically linked **ffmpeg/ffprobe** CLI (FLAC/AAC/Ogg/Opus are native) for each
ABI and stages them here automatically:

```bash
bash scripts/build-android-ffmpeg.sh
# or as part of the APK build:
DOWNTIFY_AUTO_BUILD_FFMPEG=1 bash scripts/build-android-apk.sh
```

Requires the Android NDK (set `ANDROID_NDK_HOME`, or have one under
`$ANDROID_HOME/ndk/*` or `.tools/android-sdk/ndk/*`). Tune with env vars:
`ABIS`, `ANDROID_API_LEVEL`, `FFMPEG_VERSION`, `LAME_VERSION`.

The script builds `--enable-static --disable-shared` so the `libav*` code is
linked into the program, producing a single self-contained executable that we
ship renamed to `libffmpeg.so` (Android only extracts `lib*.so` and cannot ship
versioned sonames like `libavcodec.so.60`).

## Where downloads format depends on this

`downtify/audio_caps.py` probes the bundled ffmpeg's encoders at runtime and the
app only offers formats it can actually produce. With ffmpeg present you get
MP3/FLAC/M4A/Ogg/Opus; without it, downloads fall back to native **M4A (AAC)**.

## Verifying on-device

```bash
adb shell "$(pm path com.securednodedynamics.downtify | sed 's/package://;s|base.apk|lib/arm64|')/libffmpeg.so" -encoders | grep -E 'libmp3lame|flac'
```

These binaries are intentionally **git-ignored** (large/per-environment).
Without them, search/browse still work and downloads succeed as native M4A, but
MP3/FLAC conversion is unavailable.
