#!/usr/bin/env bash
# Create the Downtify release keystore used for Play Protect–friendly APK signing.
#
# Run once per machine/org. Back up the generated keystore and passwords securely.
# Losing the keystore means users cannot update in place and must reinstall.
#
# Usage:
#   ./scripts/setup-android-release-keystore.sh
#
# Optional env (non-interactive):
#   DOWNTIFY_KEYSTORE_PASSWORD, DOWNTIFY_KEY_PASSWORD
#   DOWNTIFY_KEY_ALIAS (default: downtify)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT/frontend/android"
KEYSTORE_DIR="$ANDROID_DIR/keystore"
KEYSTORE_FILE="$KEYSTORE_DIR/downtify-release.keystore"
PROPS_FILE="$ANDROID_DIR/keystore.properties"
KEY_ALIAS="${DOWNTIFY_KEY_ALIAS:-downtify}"

export JAVA_HOME="${JAVA_HOME:-$ROOT/.tools/jdk-21}"
if [[ ! -x "$JAVA_HOME/bin/keytool" ]]; then
  JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v keytool)")")")"
fi

if [[ -f "$KEYSTORE_FILE" ]]; then
  echo "Release keystore already exists: $KEYSTORE_FILE"
  exit 0
fi

mkdir -p "$KEYSTORE_DIR"

if [[ -z "${DOWNTIFY_KEYSTORE_PASSWORD:-}" ]]; then
  read -r -s -p "Keystore password: " DOWNTIFY_KEYSTORE_PASSWORD
  echo
  read -r -s -p "Confirm keystore password: " confirm
  echo
  if [[ "$DOWNTIFY_KEYSTORE_PASSWORD" != "$confirm" ]]; then
    echo "Passwords do not match." >&2
    exit 1
  fi
fi

if [[ -z "${DOWNTIFY_KEY_PASSWORD:-}" ]]; then
  read -r -s -p "Key password (Enter to match keystore password): " DOWNTIFY_KEY_PASSWORD
  echo
  if [[ -z "$DOWNTIFY_KEY_PASSWORD" ]]; then
    DOWNTIFY_KEY_PASSWORD="$DOWNTIFY_KEYSTORE_PASSWORD"
  fi
fi

"$JAVA_HOME/bin/keytool" -genkeypair -v \
  -keystore "$KEYSTORE_FILE" \
  -alias "$KEY_ALIAS" \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -storepass "$DOWNTIFY_KEYSTORE_PASSWORD" \
  -keypass "$DOWNTIFY_KEY_PASSWORD" \
  -dname "CN=Secured Node Dynamics, OU=Mobile, O=Secured Node Dynamics, L=Unknown, ST=Unknown, C=US"

cat >"$PROPS_FILE" <<EOF
storeFile=keystore/downtify-release.keystore
storePassword=${DOWNTIFY_KEYSTORE_PASSWORD}
keyAlias=${KEY_ALIAS}
keyPassword=${DOWNTIFY_KEY_PASSWORD}
EOF

chmod 600 "$PROPS_FILE" "$KEYSTORE_FILE"

echo
echo "Created release keystore:"
echo "  $KEYSTORE_FILE"
echo "  $PROPS_FILE"
echo
echo "Next steps:"
echo "  1. Back up the keystore file and passwords in a password manager."
echo "  2. Add GitHub Actions secrets for CI builds (see docs/android-apk-signing.md)."
echo "  3. Register the app with Android developer verification:"
echo "     https://developer.android.com/developer-verification/guides"
echo "     Package: com.securednodedynamics.downtify"
