# Android APK signing and developer verification

Downtify ships a sideloaded APK (`downtify-{version}.apk`) from [GitHub Releases](https://github.com/SecuredNodeDynamics/Downtify/releases).
On **certified Android devices** (phones with Google Play services and Play Protect), Google is rolling out **Android developer verification**: apps must be tied to a **verified developer identity** and a **registered package name + signing key**. Without that, users can still sideload, but only through a one-time **advanced flow** (24-hour wait, extra warnings) starting August 2026 — or via ADB.

This is **not** the same as publishing on Google Play. You can keep distributing the APK from GitHub; verification only links your identity and signing certificate to package `com.securednodedynamics.downtify`.

Official references:

- [Android developer verification overview](https://developer.android.com/developer-verification)
- [Step-by-step guides](https://developer.android.com/developer-verification/guides)
- [FAQ](https://developer.android.com/developer-verification/guides/faq)
- [Timeline](https://support.google.com/android-developer-console/answer/16650243)

## What “Google Play secure verification” means for sideloaded APKs

| Term | Meaning for Downtify |
|------|----------------------|
| **Play Protect** | On-device scanner on certified Android phones. Debug-signed or unknown-developer APKs get extra friction and warnings. |
| **Android developer verification** | Google program (2025–2027 rollout) requiring developers to verify identity and register each app’s **package name** + **signing certificate**. |
| **Certified Android device** | Most consumer phones sold with Google apps. Requirements apply regardless of download source (Play, GitHub, email, etc.). |
| **Advanced flow** | One-time user opt-in (August 2026+) to install apps from **unverified** developers, with a 24-hour security wait and persistent “unverified developer” warnings. |
| **Registered + verified** | Normal install/update experience — no advanced flow, no extra Play Protect scare screens for your certificate. |

**Enforcement timeline (as of mid-2026):**

- **March 2026** — Android Developer Console open to all developers.
- **August 2026** — Advanced flow available for power users who want unverified apps.
- **September 30, 2026** — Unverified apps are blocked on certified devices in **Brazil, Indonesia, Singapore, and Thailand** unless registered to a verified developer (initial enforcement targets specific app stores; GitHub direct sideloading is not in that first store list, but **global rollout is planned for 2027**).
- **2027+** — requirements expand globally for all sideload sources on certified devices.

**ADB installs are unchanged** — developers and testers can always `adb install` without registration.

## Already configured in this repository

You do **not** need app code changes for verification, but release builds should use **v1 + v2 + v3** (and v4 when supported) signing schemes — see `frontend/android/app/build.gradle`. The repo is set up for it:

| Item | Status |
|------|--------|
| Package name `com.securednodedynamics.downtify` | Consistent in `build.gradle`, `capacitor.config.json`, manifest, Java sources |
| Release builds only for distribution | `assembleRelease`; CI and `publish.sh` refuse debug-signed APKs |
| Stable release keystore | `scripts/setup-android-release-keystore.sh` → `frontend/android/keystore/downtify-release.keystore` |
| APK naming | `downtify-{version}.apk` on GitHub Releases |
| CI signing | `.github/workflows/android-apk.yml` + GitHub Actions secrets |
| Signature schemes | v1 + v2 + v3 + v4 signing enabled in `frontend/android/app/build.gradle` |

**You must do manually** (cannot be automated in git):

1. Create and **back up** the release keystore (once per org).
2. Add GitHub Actions secrets for CI builds.
3. Create/verify a **Google developer account** (Play Console or Android Developer Console).
4. Complete **identity verification** (government ID or org docs; $25 fee for full distribution).
5. **Register** package `com.securednodedynamics.downtify` with your release key’s SHA-256 fingerprint and upload a proof APK.

## One-time setup (maintainer)

### 1. Create the release keystore

```bash
chmod +x scripts/setup-android-release-keystore.sh
./scripts/setup-android-release-keystore.sh
```

This creates:

- `frontend/android/keystore/downtify-release.keystore`
- `frontend/android/keystore.properties`

**Back up the keystore and passwords.** If you lose them, users cannot update in place and must uninstall/reinstall. You also cannot complete Google’s key-ownership proof without the private key.

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

### 3. Collect signing info for Google registration

Run the helper script (reads your local release keystore; never prints passwords):

```bash
chmod +x scripts/android-verification-info.sh
./scripts/android-verification-info.sh frontend/dist/downtify-*.apk
```

It prints the package name, key alias, certificate DN, SHA-256 in **colon format** (for the Google console) and hex format, APK signature scheme status (v1–v4), registration links, and a checklist.

Google needs the **SHA-256 certificate fingerprint** of your **release** signing key (not the debug key). Use the **colon format** line (`AA:BB:CC:...`) when pasting into Android Developer Console.

Manual alternatives:

**From the keystore** (replace alias/password as needed):

```bash
keytool -list -v \
  -keystore frontend/android/keystore/downtify-release.keystore \
  -alias downtify \
  -storepass 'YOUR_KEYSTORE_PASSWORD' \
  | grep -A1 'SHA256:'
```

**From a built APK** (after `bash scripts/build-android-apk.sh`):

```bash
BUILD_TOOLS="$(ls -d "$ANDROID_HOME/build-tools"/* | sort -V | tail -1)"
"$BUILD_TOOLS/apksigner" verify --print-certs frontend/dist/downtify-*.apk
```

Look for the `SHA-256 digest:` line. You should **not** see `CN=Android Debug`.

Keep these values handy:

| Field | Downtify value |
|-------|----------------|
| Package name | `com.securednodedynamics.downtify` |
| Key alias | `downtify` (default from setup script) |
| APK to upload as proof | Latest `downtify-x.y.z.apk` from a release build, signed with the same keystore |

## Android developer verification checklist (manual)

Work through this once. Allow a few days if registering as an **organization** (D-U-N-S lookup can take up to 28 days).

### Step A — Choose your console

| How you distribute | Where to verify |
|--------------------|-----------------|
| **Only GitHub / sideload** (Downtify today) | [Android Developer Console](https://developer.android.com/developer-verification/guides/android-developer-console) |
| **Also on Google Play** | [Google Play Console](https://developer.android.com/developer-verification/guides/google-play-console) — can register off-Play apps there too |
| **Play Console account already verified** | Use Play Console; add off-Play package registration under Android developer verification |

Downtify is **GitHub-only**, so use **Android Developer Console** unless you also publish on Play.

Guide links:

- [Register on Android Developer Console](https://developer.android.com/developer-verification/guides/android-developer-console)
- [Register on Google Play Console](https://developer.android.com/developer-verification/guides/google-play-console)
- [Play Console: registering package names](https://support.google.com/googleplay/android-developer/answer/16761053)

### Step B — Pick account type

| Type | Best for | ID verification | Fee | Install reach |
|------|----------|-----------------|-----|---------------|
| **Full distribution** | Public apps like Downtify | Yes (individual or organization) | $25 (ADC) / existing Play fee | Unlimited sideload installs on certified devices |
| **Limited distribution** | Students, hobbyists, personal testing | No government ID | Free | Up to **20 devices** only |

For Downtify GitHub releases, choose **Full distribution**.

**Organization registration** requires a [D-U-N-S number](https://www.dnb.com/duns-number.html) (free, can take weeks). **Individual registration** needs government ID.

### Step C — Create account and verify identity

1. Open [Android Developer Console](https://play.google.com/console/signup) or sign in to [Play Console](https://play.google.com/console) if you already have it.
2. Pay the one-time registration fee if prompted ($25 for ADC full distribution).
3. Complete identity verification:
   - **Individual** — legal name, address, government-issued photo ID.
   - **Organization** — legal business name, address, D-U-N-S, business documentation.
4. Wait for Google to mark the developer account as **Verified** (often same day for individuals; longer for orgs).

### Step D — Register package name and signing key

In the console, go to **Package names** (ADC) or **Android developer verification → Package names** (Play Console).

1. **Add package name:** `com.securednodedynamics.downtify`
2. **Add signing key:** paste the **SHA-256 fingerprint** from [step 3 above](#3-collect-signing-info-for-google-registration).
3. **Prove key ownership** — build and upload a release APK signed with your private key:
   ```bash
   bash scripts/build-android-apk.sh
   ```
   Upload `frontend/dist/downtify-<version>.apk`.

   If Google provides a **challenge snippet** for an existing package, add it to the APK assets as instructed in the console, rebuild, and upload the new signed APK.

4. Wait for status **Registered** (email confirmation when complete).

**Important:** Every future release must be signed with the **same** release keystore. Rotating keys requires registering the new fingerprint in the console before users can update.

### Step E — Confirm and communicate to users

1. In the console, confirm package status shows **Registered**.
2. Optionally check via [Android Developer ID Status API](https://developer.android.com/developer-verification/guides) (for automation).
3. After registration, users on certified devices install/update `downtify-x.y.z.apk` normally — no advanced flow.

If verification is not done before enforcement in a user’s region, tell users they can either wait for you to register, use **advanced flow** (one-time 24h wait), or install via **ADB**.

## Migrating users from old debug APKs

Earlier releases were debug-signed. The first **release-signed** build cannot update over a debug install (Android treats them as different apps). Users must:

1. Uninstall the old Downtify APK once.
2. Install the new release-signed APK from GitHub Releases.

After that, in-app updates keep the same certificate and install in place.

## Verify a built APK locally

```bash
bash scripts/build-android-apk.sh
```

The script runs `apksigner verify` and rejects debug certificates. Release builds must verify **v2 and v3** signature schemes (rebuild after enabling v3 in `build.gradle`).

To inspect the certificate:

```bash
BUILD_TOOLS="$(ls -d "$ANDROID_HOME/build-tools"/* | sort -V | tail -1)"
"$BUILD_TOOLS/apksigner" verify --print-certs frontend/dist/downtify-*.apk
```

You should **not** see `CN=Android Debug`.
