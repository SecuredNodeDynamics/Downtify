#!/usr/bin/env bash
# Build self-contained ffmpeg + ffprobe CLI binaries for Android and stage them
# for the serverless APK so it can transcode on-device (MP3 via libmp3lame,
# FLAC via ffmpeg's native encoder, plus AAC/Ogg/Opus).
#
# Why a static CLI (and not ffmpeg-android-maker's shared libs): Android only
# extracts files named lib*.so from jniLibs and cannot ship versioned sonames
# like libavcodec.so.60. So we build ffmpeg with --enable-static --disable-shared
# (libav* linked into the program) and ship the single executable renamed to
# libffmpeg.so — exactly what downtify/mobile.py:prepare_ffmpeg expects.
#
# Output:
#   frontend/android/app/src/main/jniLibs/<abi>/libffmpeg.so   (ffmpeg CLI)
#   frontend/android/app/src/main/jniLibs/<abi>/libffprobe.so  (ffprobe CLI)
#
# Requirements: Android NDK (r26+), curl, make, a C toolchain for the host,
# tar/xz, and (for lame) autotools. Set ANDROID_NDK_HOME or have an NDK under
# $ANDROID_HOME/ndk/* or .tools/android-sdk/ndk/*.
#
# Usage:
#   bash scripts/build-android-ffmpeg.sh
#   ABIS="arm64-v8a" bash scripts/build-android-ffmpeg.sh   # subset
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JNILIBS_DIR="$ROOT/frontend/android/app/src/main/jniLibs"
WORK="${FFMPEG_BUILD_DIR:-$ROOT/.tools/ffmpeg-build}"

ABIS="${ABIS:-arm64-v8a x86_64}"
API_LEVEL="${ANDROID_API_LEVEL:-24}"
LAME_VERSION="${LAME_VERSION:-3.100}"
FFMPEG_VERSION="${FFMPEG_VERSION:-7.1.1}"

# Known-good checksum for lame (override via env for other versions).
LAME_SHA256="${LAME_SHA256:-ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e}"
# ffmpeg tarball checksum is verified against ffmpeg.org's published .sha256
# when available; set FFMPEG_SHA256 to pin it explicitly.
FFMPEG_SHA256="${FFMPEG_SHA256:-}"

log() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWARNING:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

require_cmd curl
require_cmd make
require_cmd tar

detect_ndk() {
  if [[ -n "${ANDROID_NDK_HOME:-}" && -d "$ANDROID_NDK_HOME" ]]; then
    echo "$ANDROID_NDK_HOME"; return 0
  fi
  if [[ -n "${ANDROID_NDK_ROOT:-}" && -d "$ANDROID_NDK_ROOT" ]]; then
    echo "$ANDROID_NDK_ROOT"; return 0
  fi
  for base in "${ANDROID_HOME:-}" "$ROOT/.tools/android-sdk" "${ANDROID_SDK_ROOT:-}"; do
    [[ -n "$base" && -d "$base/ndk" ]] || continue
    local latest
    latest="$(ls -d "$base"/ndk/* 2>/dev/null | sort -V | tail -1)"
    [[ -n "$latest" ]] && { echo "$latest"; return 0; }
  done
  return 1
}

NDK="$(detect_ndk)" || die "Android NDK not found. Set ANDROID_NDK_HOME."
log "Using NDK: $NDK"

HOST_TAG="linux-x86_64"
case "$(uname -s)" in
  Darwin) HOST_TAG="darwin-x86_64" ;;
esac
TOOLCHAIN="$NDK/toolchains/llvm/prebuilt/$HOST_TAG"
[[ -d "$TOOLCHAIN" ]] || die "Toolchain not found: $TOOLCHAIN"
SYSROOT="$TOOLCHAIN/sysroot"

mkdir -p "$WORK"

verify_sha256() {
  local file="$1" expected="$2"
  [[ -n "$expected" ]] || return 0
  local actual
  actual="$(sha256sum "$file" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || die "Checksum mismatch for $file
  expected: $expected
  actual:   $actual"
}

fetch() {
  local url="$1" out="$2"
  [[ -f "$out" ]] && return 0
  log "Downloading $url"
  curl -fL --retry 3 -o "$out" "$url"
}

# --- Download sources -------------------------------------------------------

LAME_TARBALL="$WORK/lame-$LAME_VERSION.tar.gz"
FFMPEG_TARBALL="$WORK/ffmpeg-$FFMPEG_VERSION.tar.xz"

fetch "https://downloads.sourceforge.net/project/lame/lame/$LAME_VERSION/lame-$LAME_VERSION.tar.gz" "$LAME_TARBALL"
verify_sha256 "$LAME_TARBALL" "$LAME_SHA256"

fetch "https://ffmpeg.org/releases/ffmpeg-$FFMPEG_VERSION.tar.xz" "$FFMPEG_TARBALL"
if [[ -z "$FFMPEG_SHA256" ]]; then
  if curl -fsL "https://ffmpeg.org/releases/ffmpeg-$FFMPEG_VERSION.tar.xz.sha256" -o "$FFMPEG_TARBALL.sha256" 2>/dev/null; then
    FFMPEG_SHA256="$(awk '{print $1}' "$FFMPEG_TARBALL.sha256" | head -1)"
  else
    warn "Could not fetch ffmpeg checksum; set FFMPEG_SHA256 to verify the download."
  fi
fi
verify_sha256 "$FFMPEG_TARBALL" "$FFMPEG_SHA256"

abi_to_triple() {
  case "$1" in
    arm64-v8a) echo "aarch64-linux-android" ;;
    x86_64)    echo "x86_64-linux-android" ;;
    armeabi-v7a) echo "armv7a-linux-androideabi" ;;
    x86)       echo "i686-linux-android" ;;
    *) die "Unsupported ABI: $1" ;;
  esac
}

abi_to_arch() {
  case "$1" in
    arm64-v8a) echo "aarch64" ;;
    x86_64)    echo "x86_64" ;;
    armeabi-v7a) echo "arm" ;;
    x86)       echo "x86" ;;
  esac
}

build_for_abi() {
  local abi="$1"
  local triple arch cc_prefix
  triple="$(abi_to_triple "$abi")"
  arch="$(abi_to_arch "$abi")"

  # armv7 uses a different clang prefix than its lib triple.
  cc_prefix="$triple"
  [[ "$abi" == "armeabi-v7a" ]] && cc_prefix="armv7a-linux-androideabi"

  export CC="$TOOLCHAIN/bin/${cc_prefix}${API_LEVEL}-clang"
  export CXX="$TOOLCHAIN/bin/${cc_prefix}${API_LEVEL}-clang++"
  export AR="$TOOLCHAIN/bin/llvm-ar"
  export NM="$TOOLCHAIN/bin/llvm-nm"
  export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
  export STRIP="$TOOLCHAIN/bin/llvm-strip"
  [[ -x "$CC" ]] || die "Compiler not found: $CC (try a different ANDROID_API_LEVEL)"

  local prefix="$WORK/out/$abi"
  rm -rf "$prefix"
  mkdir -p "$prefix"

  local x86asm_flags=()
  if [[ "$abi" == "x86" || "$abi" == "x86_64" ]]; then
    if ! command -v nasm >/dev/null 2>&1 && ! command -v yasm >/dev/null 2>&1; then
      warn "[$abi] nasm/yasm not found; building ffmpeg with --disable-x86asm."
      x86asm_flags=(--disable-x86asm)
    fi
  fi

  # --- libmp3lame (static) ---
  log "[$abi] Building libmp3lame $LAME_VERSION"
  local lame_src="$WORK/src/$abi/lame-$LAME_VERSION"
  rm -rf "$lame_src"; mkdir -p "$(dirname "$lame_src")"
  tar -C "$(dirname "$lame_src")" -xf "$LAME_TARBALL"
  (
    cd "$lame_src"
    # lame 3.100 ships a stray symbol that breaks some toolchains; harmless to drop.
    sed -i.bak '/lame_init_old/d' include/libmp3lame.sym 2>/dev/null || true
    ./configure \
      --host="$triple" \
      --prefix="$prefix" \
      --disable-shared --enable-static \
      --disable-frontend \
      CC="$CC" AR="$AR" RANLIB="$RANLIB" \
      CFLAGS="-O2 -fPIC -DANDROID"
    make -j"$(nproc 2>/dev/null || echo 4)"
    make install
  )

  # --- ffmpeg (static libs + static CLI) ---
  log "[$abi] Building ffmpeg $FFMPEG_VERSION"
  local ff_src="$WORK/src/$abi/ffmpeg-$FFMPEG_VERSION"
  rm -rf "$ff_src"; mkdir -p "$(dirname "$ff_src")"
  tar -C "$(dirname "$ff_src")" -xf "$FFMPEG_TARBALL"
  (
    cd "$ff_src"
    ./configure \
      --prefix="$prefix" \
      --target-os=android \
      --arch="$arch" \
      --enable-cross-compile \
      --sysroot="$SYSROOT" \
      --cc="$CC" --cxx="$CXX" \
      --ar="$AR" --nm="$NM" --ranlib="$RANLIB" --strip="$STRIP" \
      --enable-static --disable-shared \
      --enable-small \
      --disable-doc --disable-ffplay --disable-debug \
      --enable-pic \
      --enable-gpl \
      --enable-libmp3lame \
      "${x86asm_flags[@]}" \
      --extra-cflags="-I$prefix/include -O2 -fPIC" \
      --extra-ldflags="-L$prefix/lib" \
      --extra-ldexeflags="-pie" \
      --extra-libs="-lm"
    make -j"$(nproc 2>/dev/null || echo 4)"
  )

  local ffmpeg_bin="$ff_src/ffmpeg"
  local ffprobe_bin="$ff_src/ffprobe"
  [[ -f "$ffmpeg_bin" ]] || die "[$abi] ffmpeg executable not produced"
  [[ -f "$ffprobe_bin" ]] || die "[$abi] ffprobe executable not produced"

  "$STRIP" "$ffmpeg_bin" "$ffprobe_bin" 2>/dev/null || true

  local dest="$JNILIBS_DIR/$abi"
  mkdir -p "$dest"
  cp "$ffmpeg_bin" "$dest/libffmpeg.so"
  cp "$ffprobe_bin" "$dest/libffprobe.so"
  log "[$abi] Staged $(du -h "$dest/libffmpeg.so" | awk '{print $1}') libffmpeg.so + libffprobe.so"
}

for abi in $ABIS; do
  build_for_abi "$abi"
done

log "Done. ffmpeg/ffprobe staged under $JNILIBS_DIR/<abi>/"
echo "Verify on a device with:"
echo "  adb shell \"\$(pm path com.securednodedynamics.downtify | sed 's/package://;s|base.apk|lib/arm64|')/libffmpeg.so\" -encoders | grep -E 'libmp3lame|flac'"
