#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND="$ROOT/frontend"
ANDROID_DIR="$FRONTEND/android"
TOOLS="$ROOT/.tools"

export JAVA_HOME="${JAVA_HOME:-$TOOLS/jdk-21}"
export ANDROID_HOME="${ANDROID_HOME:-$TOOLS/android-sdk}"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

require_release_signing() {
  if [[ -f "$ANDROID_DIR/keystore.properties" ]]; then
    return 0
  fi
  if [[ -n "${ANDROID_KEYSTORE_PATH:-}" && -n "${ANDROID_KEYSTORE_PASSWORD:-}" && -n "${ANDROID_KEY_ALIAS:-}" && -n "${ANDROID_KEY_PASSWORD:-}" ]]; then
    return 0
  fi
  echo "Release signing is required for Play Protect–friendly APKs." >&2
  echo "Run: ./scripts/setup-android-release-keystore.sh" >&2
  echo "Or set ANDROID_KEYSTORE_PATH and related env vars." >&2
  exit 1
}

verify_apk_signature() {
  local apk="$1"
  local build_tools
  local verify_out
  build_tools="$(ls -d "$ANDROID_HOME/build-tools"/* 2>/dev/null | sort -V | tail -1)"
  if [[ -z "$build_tools" || ! -x "$build_tools/apksigner" ]]; then
    echo "apksigner not found under ANDROID_HOME/build-tools" >&2
    exit 1
  fi

  verify_out="$("$build_tools/apksigner" verify --verbose "$apk" 2>&1)"
  echo "$verify_out" | grep -E '^(Verifies|Verified using)' || true

  if ! echo "$verify_out" | grep -q 'Verified using v2 scheme (APK Signature Scheme v2): true'; then
    echo "APK is not signed with v2 scheme: $apk" >&2
    exit 1
  fi
  if ! echo "$verify_out" | grep -q 'Verified using v3 scheme (APK Signature Scheme v3): true'; then
    echo "APK is not signed with v3 scheme (rebuild after enabling v3SigningEnabled): $apk" >&2
    exit 1
  fi

  if "$build_tools/apksigner" verify --print-certs "$apk" 2>/dev/null | grep -qi 'Android Debug'; then
    echo "Refusing to ship a debug-signed APK: $apk" >&2
    exit 1
  fi
}

require_release_signing

cd "$FRONTEND"

VERSION="$(node "$ROOT/version.js" --sync-android)"
PKG_VERSION="$(node -p "require('./package.json').version")"
if [[ "$PKG_VERSION" != "$VERSION" ]]; then
  echo "Version mismatch: package.json=$PKG_VERSION repo=$VERSION" >&2
  exit 1
fi

cp "$ROOT/assets/icon-without-backgroud.svg" "$FRONTEND/assets/logo.svg"
npm run android:icons
uv run python "$ROOT/scripts/fix-android-adaptive-icons.py"
npm run build:android

# The embedded (serverless) backend needs a bundled ffmpeg per ABI so it can
# transcode to MP3/FLAC on-device. Build it when missing if opted in, otherwise
# warn (search/browse still work; downloads fall back to native M4A).
JNILIBS_DIR="$ANDROID_DIR/app/src/main/jniLibs"
if ! ls "$JNILIBS_DIR"/*/libffmpeg.so >/dev/null 2>&1; then
  if [[ "${DOWNTIFY_AUTO_BUILD_FFMPEG:-0}" == "1" ]]; then
    echo "No bundled ffmpeg found; building it (DOWNTIFY_AUTO_BUILD_FFMPEG=1)..." >&2
    bash "$ROOT/scripts/build-android-ffmpeg.sh"
  else
    echo "WARNING: No bundled ffmpeg found under $JNILIBS_DIR/<abi>/libffmpeg.so" >&2
    echo "         On-device MP3/FLAC conversion will be unavailable (downloads" >&2
    echo "         fall back to native M4A)." >&2
    echo "         Build it once with: bash scripts/build-android-ffmpeg.sh" >&2
    echo "         (or re-run with DOWNTIFY_AUTO_BUILD_FFMPEG=1). See" >&2
    echo "         frontend/android/app/src/main/jniLibs/README.md" >&2
  fi
fi

cd android
./gradlew assembleRelease

APK_SRC="$FRONTEND/android/app/build/outputs/apk/release/app-release.apk"
APK_DST="$FRONTEND/dist/downtify-${VERSION}.apk"

if [[ ! -f "$APK_SRC" ]]; then
  echo "Release APK not found: $APK_SRC" >&2
  echo "Ensure release signing is configured in frontend/android/keystore.properties" >&2
  exit 1
fi

mkdir -p "$FRONTEND/dist"
cp "$APK_SRC" "$APK_DST"
verify_apk_signature "$APK_DST"

GRADLE_VERSION="$(sed -n 's/.*versionName "\([^"]*\)".*/\1/p' "$FRONTEND/android/app/build.gradle" | head -1)"
if [[ "$GRADLE_VERSION" != "$VERSION" ]]; then
  echo "Android versionName ($GRADLE_VERSION) != release ($VERSION)" >&2
  exit 1
fi

echo "Built release-signed $APK_DST"
