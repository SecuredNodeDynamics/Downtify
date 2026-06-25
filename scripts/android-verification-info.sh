#!/usr/bin/env bash
# Print signing details needed for Android Developer Verification (Google Play Protect).
#
# Usage:
#   ./scripts/android-verification-info.sh [path/to/app.apk]
#
# Reads release keystore from frontend/android/keystore.properties or ANDROID_* env vars.
# Passwords are never printed.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT/frontend/android"
TOOLS="$ROOT/.tools"
PACKAGE_NAME="com.securednodedynamics.downtify"

export JAVA_HOME="${JAVA_HOME:-$TOOLS/jdk-21}"
export ANDROID_HOME="${ANDROID_HOME:-$TOOLS/android-sdk}"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

APK_PATH="${1:-}"

resolve_signing() {
  local props="$ANDROID_DIR/keystore.properties"
  if [[ -f "$props" ]]; then
    KEYSTORE_STORE_FILE="$ANDROID_DIR/$(grep '^storeFile=' "$props" | cut -d= -f2-)"
    KEYSTORE_STORE_PASSWORD="$(grep '^storePassword=' "$props" | cut -d= -f2-)"
    KEYSTORE_KEY_ALIAS="$(grep '^keyAlias=' "$props" | cut -d= -f2-)"
    KEYSTORE_KEY_PASSWORD="$(grep '^keyPassword=' "$props" | cut -d= -f2-)"
    return 0
  fi
  if [[ -n "${ANDROID_KEYSTORE_PATH:-}" ]]; then
    KEYSTORE_STORE_FILE="$ANDROID_KEYSTORE_PATH"
    KEYSTORE_STORE_PASSWORD="${ANDROID_KEYSTORE_PASSWORD:-}"
    KEYSTORE_KEY_ALIAS="${ANDROID_KEY_ALIAS:-}"
    KEYSTORE_KEY_PASSWORD="${ANDROID_KEY_PASSWORD:-}"
    return 0
  fi
  echo "Release keystore not found." >&2
  echo "Run: ./scripts/setup-android-release-keystore.sh" >&2
  echo "Or set ANDROID_KEYSTORE_PATH and related env vars." >&2
  exit 1
}

colon_to_hex() {
  echo "$1" | tr -d ':' | tr '[:upper:]' '[:lower:]'
}

hex_to_colon() {
  local hex="${1,,}"
  local out=""
  local i
  for ((i = 0; i < ${#hex}; i += 2)); do
    if [[ -n "$out" ]]; then
      out+=":"
    fi
    out+="${hex:i:2}"
  done
  echo "$out" | tr '[:lower:]' '[:upper:]'
}

find_apksigner() {
  local build_tools
  build_tools="$(ls -d "$ANDROID_HOME/build-tools"/* 2>/dev/null | sort -V | tail -1)"
  if [[ -n "$build_tools" && -x "$build_tools/apksigner" ]]; then
    echo "$build_tools/apksigner"
    return 0
  fi
  if command -v apksigner >/dev/null 2>&1; then
    command -v apksigner
    return 0
  fi
  return 1
}

resolve_signing

if [[ ! -f "$KEYSTORE_STORE_FILE" ]]; then
  echo "Keystore file not found: $KEYSTORE_STORE_FILE" >&2
  exit 1
fi

if [[ -z "${KEYSTORE_KEY_ALIAS:-}" ]]; then
  echo "Key alias is not configured." >&2
  exit 1
fi

KEYTOOL_OUT="$("$JAVA_HOME/bin/keytool" -list -v \
  -keystore "$KEYSTORE_STORE_FILE" \
  -alias "$KEYSTORE_KEY_ALIAS" \
  -storepass "$KEYSTORE_STORE_PASSWORD" 2>/dev/null)"

SHA256_COLON="$(echo "$KEYTOOL_OUT" | awk -F': ' '/SHA256:/{print $2; exit}')"
if [[ -z "$SHA256_COLON" ]]; then
  echo "Could not read SHA-256 fingerprint from keystore." >&2
  exit 1
fi

SHA256_HEX="$(colon_to_hex "$SHA256_COLON")"
CERT_DN="$(echo "$KEYTOOL_OUT" | awk -F': ' '/Owner:/{print $2; exit}')"

if [[ -z "$APK_PATH" ]]; then
  latest="$(ls -t "$ROOT/frontend/dist"/downtify-*.apk 2>/dev/null | head -1 || true)"
  if [[ -n "$latest" ]]; then
    APK_PATH="$latest"
  fi
fi

echo "================================================================"
echo " Android Developer Verification — Downtify signing info"
echo "================================================================"
echo
echo "Package name : $PACKAGE_NAME"
echo "Key alias    : $KEYSTORE_KEY_ALIAS"
echo "Certificate  : $CERT_DN"
echo
echo "SHA-256 fingerprint (colon format — paste into Google console):"
echo "  $SHA256_COLON"
echo
echo "SHA-256 fingerprint (hex format, no colons):"
echo "  $SHA256_HEX"
echo

if [[ -n "$APK_PATH" && -f "$APK_PATH" ]]; then
  echo "APK inspected: $APK_PATH"
  if APKSIGNER="$(find_apksigner)"; then
    echo
    "$APKSIGNER" verify --verbose "$APK_PATH" 2>&1 | grep -E '^(Verifies|Verified using)' || true
    APK_CERT_DN="$("$APKSIGNER" verify --print-certs "$APK_PATH" 2>/dev/null | awk -F': ' '/Signer #1 certificate DN:/{print $2; exit}')"
    APK_SHA256_HEX="$("$APKSIGNER" verify --print-certs "$APK_PATH" 2>/dev/null | awk -F': ' '/SHA-256 digest:/{print $2; exit}')"
    if [[ -n "$APK_SHA256_HEX" ]]; then
      APK_SHA256_COLON="$(hex_to_colon "$APK_SHA256_HEX")"
      echo
      echo "APK certificate DN : ${APK_CERT_DN:-unknown}"
      echo "APK SHA-256 (colon) : $APK_SHA256_COLON"
      if [[ "${APK_SHA256_HEX,,}" != "${SHA256_HEX,,}" ]]; then
        echo
        echo "WARNING: APK fingerprint does not match the release keystore above." >&2
      fi
      if echo "$APK_CERT_DN" | grep -qi 'Android Debug'; then
        echo "WARNING: APK appears debug-signed. Use a release build." >&2
      fi
    fi
  else
    echo "apksigner not found — install Android SDK build-tools to verify APK schemes." >&2
  fi
  echo
else
  echo "No APK found. Pass a path or build one: bash scripts/build-android-apk.sh"
  echo
fi

echo "----------------------------------------------------------------"
echo " Registration links"
echo "----------------------------------------------------------------"
echo "  Overview     : https://developer.android.com/developer-verification"
echo "  ADC guide    : https://developer.android.com/developer-verification/guides/android-developer-console"
echo "  Play Console : https://developer.android.com/developer-verification/guides/google-play-console"
echo "  Package help : https://support.google.com/googleplay/android-developer/answer/16761053"
echo "  ADC signup   : https://play.google.com/console/signup"
echo
echo "----------------------------------------------------------------"
echo " Next steps (manual — cannot be automated in git)"
echo "----------------------------------------------------------------"
cat <<EOF
  [ ] 1. Back up frontend/android/keystore/downtify-release.keystore and passwords.
  [ ] 2. Create or sign in to Android Developer Console (GitHub-only → use ADC).
  [ ] 3. Complete identity verification (Full distribution; \$25 fee for public sideload).
  [ ] 4. Open Package names → Add: $PACKAGE_NAME
  [ ] 5. Add signing key → paste SHA-256 (colon format) shown above.
  [ ] 6. Prove key ownership → upload release APK:
        bash scripts/build-android-apk.sh
        Upload frontend/dist/downtify-<version>.apk (same keystore as above).
  [ ] 7. Wait for status Registered; future releases must use the same keystore.
EOF
echo "================================================================"
