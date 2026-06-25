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

## Where to get static ffmpeg for Android

Use a **statically linked** ffmpeg compiled for `android` with the NDK (so it
has no `libc++_shared`/`libgcc_s` runtime dependencies). Options:

- Build from source with the Android NDK (`--enable-static --disable-shared`,
  target `aarch64-linux-android` / `x86_64-linux-android`).
- Use a prebuilt static ffmpeg for Android from a trusted source and rename the
  executable to `libffmpeg.so`.

Verify it runs on-device with `adb shell <nativeLibraryDir>/libffmpeg.so -version`.

These binaries are intentionally **git-ignored** (large/per-environment).
Without them, search/browse still work but downloads that require conversion
will fail.
