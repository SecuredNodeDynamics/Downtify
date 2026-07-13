# Android APK smoke-test checklist

Run this checklist on a real Android device before publishing a release APK.
Use a release-signed APK built with `bash scripts/build-android-apk.sh`.

## Install and launch

- [ ] Install or update the release APK without a debug-signing warning.
- [ ] Launch Downtify from a cold start.
- [ ] Confirm the home screen appears quickly.
- [ ] If using the embedded backend, confirm the **Starting local engine...**
      overlay appears only while the local server is booting.
- [ ] Confirm the overlay disappears after `/api/version` is reachable.
- [ ] If the engine is intentionally broken for testing, confirm the error state
      appears and **Retry** attempts startup again.

## Health and capabilities

- [ ] Open **Health**.
- [ ] Confirm backend version is shown.
- [ ] Confirm `yt-dlp` is available.
- [ ] Confirm bundled `ffmpeg` is available in the APK.
- [ ] Confirm MP3/FLAC/M4A/Ogg/Opus availability matches the bundled ffmpeg
      capabilities shown by the app.

## Search and download

- [ ] Search by artist/title text.
- [ ] Search with a Spotify track URL.
- [ ] Search with a Spotify album URL.
- [ ] Download one track as M4A.
- [ ] Download one album.
- [ ] Confirm the Queue tab shows visible progress.
- [ ] Confirm History shows completed downloads.
- [ ] Confirm completed items appear in Library without manually restarting.

## Library and cover art

- [ ] Open Library → Artists.
- [ ] Open Library → Albums.
- [ ] Open Library → Tracks.
- [ ] Scroll a large library for at least 30 seconds.
- [ ] Confirm scrolling remains responsive.
- [ ] Confirm album covers keep loading as more rows render.
- [ ] Open an artist detail page and confirm downloaded albums show cover art.

## Player

- [ ] Play a downloaded track.
- [ ] Confirm album art appears on the now-playing card.
- [ ] Seek using the progress bar.
- [ ] Toggle shuffle, repeat, and volume.
- [ ] Open Similar media.
- [ ] Open a similar artist and confirm Albums show track counts when available.

## Monitor

- [ ] Open Monitor.
- [ ] Add or open a monitored artist.
- [ ] Confirm monitoring status displays correctly.
- [ ] Pause/resume monitoring if existing monitor data is available.

## Android Auto

- [ ] Connect to Android Auto or the Desktop Head Unit.
- [ ] Confirm Downtify appears in the app list.
- [ ] Browse Artists, Albums, Genres, and Tracks.
- [ ] Press play on an artist, album, genre, and track row.
- [ ] Confirm the active track shows in Android Auto.

## Update install

- [ ] Open Settings → Help/Updates.
- [ ] Confirm installed version displays correctly.
- [ ] If an update APK is available, download and start install.
- [ ] Confirm update install does not show a debug certificate warning.
- [ ] Relaunch after update and confirm version changed.

## Final release checks

- [ ] Run `apksigner verify --verbose frontend/dist/downtify-*.apk`.
- [ ] Confirm v2 and v3 signature schemes verify.
- [ ] Confirm the certificate is not `CN=Android Debug`.
- [ ] Confirm APK package is `com.securednodedynamics.downtify`.
- [ ] Confirm GitHub release asset name matches `downtify-<version>.apk`.
