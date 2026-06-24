# Android APK signing and Play Protect

Downtify ships a sideloaded APK (`downtify-{version}.apk`) from GitHub Releases.
Google Play Protect treats **debug-signed** APKs as high risk and re-scans them
on every install/update. **Release-signed** APKs with a **stable signing key**
and **registered developer verification** give users a normal install experience.

## What we changed in the build

- APKs are built with `./gradlew assembleRelease`, not `assembleDebug`.
- Every release uses the same release keystore (`downtify-release.keystore`).
- The build refuses to publish APKs signed with the Android Debug certificate.

## One-time setup (maintainer)

### 1. Create the release keystore

```bash
chmod +x scripts/setup-android-release-keystore.sh
./scripts/setup-android-release-keystore.sh
```

This creates:

- `frontend/android/keystore/downtify-release.keystore`
- `frontend/android/keystore.properties`

**Back up the keystore and passwords.** If you lose them, users cannot update in
place and must uninstall/reinstall.

### 2. Add GitHub Actions secrets

Encode the keystore for CI:

```bash
base64 -w0 frontend/android/keystore/downtify-release.keystore
```

Add these repository secrets in GitHub (`Settings → Secrets and variables → Actions`):

| Secret | Value |
|--------|--------|
| `ANDROID_KEYSTORE_BASE64` | Base64 output from above |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | `downtify` (or your alias) |
| `ANDROID_KEY_PASSWORD` | Key password |

The `android-apk.yml` workflow and `scripts/publish.sh` both require release signing.

### 3. Register with Android developer verification

Play Protect “approval” for sideloaded apps outside Google Play requires linking
your package and signing key to a verified developer account:

1. Open [Android developer verification](https://developer.android.com/developer-verification/guides).
2. Use **Google Play Console** if you already have one, or create an **Android Developer Console** account for apps distributed only outside Play.
3. Complete identity verification (organization or individual).
4. Register package name **`com.securednodedynamics.downtify`** by uploading an APK signed with your release key.

After registration, certified Android devices install and update your APK without
the extra “advanced flow” friction that applies to unverified developers
(rolling out from September 2026 in some regions, globally in 2027).

References:

- [Developer verification FAQ](https://developer.android.com/developer-verification/guides/faq)
- [Package registration](https://developer.android.com/developer-verification/guides)

## Migrating users from old debug APKs

Earlier releases were debug-signed. The first **release-signed** build cannot
update over a debug install (Android treats them as different apps). Users must:

1. Uninstall the old Downtify APK once.
2. Install the new release-signed APK from GitHub Releases.

After that, in-app updates keep the same certificate and install in place.

## Verify a built APK locally

```bash
bash scripts/build-android-apk.sh
```

The script runs `apksigner verify` and rejects debug certificates.

To inspect the certificate:

```bash
BUILD_TOOLS="$(ls -d "$ANDROID_HOME/build-tools"/* | sort -V | tail -1)"
"$BUILD_TOOLS/apksigner" verify --print-certs frontend/dist/downtify-*.apk
```

You should **not** see `CN=Android Debug`.
