#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND="$ROOT/frontend"
TOOLS="$ROOT/.tools"

export JAVA_HOME="${JAVA_HOME:-$TOOLS/jdk-21}"
export ANDROID_HOME="${ANDROID_HOME:-$TOOLS/android-sdk}"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

cd "$FRONTEND"

VERSION="$(node -p "require('./package.json').version")"
cp "$ROOT/assets/icon-without-backgroud.svg" "$FRONTEND/assets/logo.svg"
npm run android:icons
npm run build:android
cd android
./gradlew assembleDebug

APK_SRC="$FRONTEND/android/app/build/outputs/apk/debug/app-debug.apk"
APK_DST="$FRONTEND/dist/downtify-${VERSION}-debug.apk"

mkdir -p "$FRONTEND/dist"
cp "$APK_SRC" "$APK_DST"
echo "Built $APK_DST"
