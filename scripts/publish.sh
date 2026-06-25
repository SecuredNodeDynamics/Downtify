#!/usr/bin/env bash
# Bump version, build web + APK, push to GitHub, create release, upload APK,
# and dispatch the Docker image build — all aligned to the same semver.
#
# Usage:
#   ./scripts/publish.sh [patch|minor|major|X.Y.Z] [--skip-tests]
#
# Requirements: git, node, npm, gh, Java + Android SDK (or .tools/ from APK setup)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BUMP="patch"
SKIP_TESTS=0

for arg in "$@"; do
  case "$arg" in
    --skip-tests) SKIP_TESTS=1 ;;
    patch|minor|major) BUMP="$arg" ;;
    *)
      if [[ "$arg" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        BUMP="$arg"
      elif [[ "$arg" != "$0" ]]; then
        echo "Unknown argument: $arg" >&2
        exit 1
      fi
      ;;
  esac
done

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd git
require_cmd node
require_cmd npm
require_cmd gh

if [[ "$(git branch --show-current)" != "main" ]]; then
  echo "Publish must be run from the main branch." >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree has uncommitted changes. Commit or stash them first." >&2
  git status --short >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. Run: gh auth login" >&2
  exit 1
fi

verify_versions() {
  local version="$1"
  local pkg gradle repo makefile docker

  pkg="$(node -p "require('./frontend/package.json').version")"
  repo="$(node "$ROOT/version.js" --current)"
  gradle="$(sed -n 's/.*versionName "\([^"]*\)".*/\1/p' frontend/android/app/build.gradle | head -1)"
  makefile="$(grep '^DOWNTIFY_VERSION := ' Makefile | awk '{print $3}')"
  docker="$(grep 'LABEL version=' Dockerfile | head -1 | sed -E 's/.*"([^"]+)".*/\1/')"

  if [[ "$pkg" != "$version" || "$repo" != "$version" || "$gradle" != "$version" || "$makefile" != "$version" || "$docker" != "$version" ]]; then
    echo "Version alignment failed for $version:" >&2
    echo "  package.json=$pkg" >&2
    echo "  downtify/__init__.py=$repo" >&2
    echo "  android build.gradle=$gradle" >&2
    echo "  Makefile=$makefile" >&2
    echo "  Dockerfile=$docker" >&2
    exit 1
  fi
}

echo "==> Bumping version ($BUMP)"
OLD_VERSION="$(node version.js --current)"
node version.js "$BUMP" >/dev/null
VERSION="$(node version.js --current)"
TAG="v${VERSION}"

if [[ "$OLD_VERSION" == "$VERSION" ]]; then
  echo "Version unchanged ($VERSION). Aborting." >&2
  exit 1
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag already exists: $TAG" >&2
  exit 1
fi

verify_versions "$VERSION"
echo "    $OLD_VERSION -> $VERSION"

echo "==> Building frontend"
npm run build --prefix frontend

echo "==> Building Android APK"
bash "$ROOT/scripts/build-android-apk.sh"

APK_PATH="frontend/dist/downtify-${VERSION}.apk"
if [[ ! -f "$APK_PATH" ]]; then
  echo "APK not found: $APK_PATH" >&2
  exit 1
fi

if [[ "$SKIP_TESTS" -eq 0 ]]; then
  echo "==> Running tests"
  npm run test --prefix frontend
  uv run pytest -q
else
  echo "==> Skipping tests (--skip-tests)"
fi

verify_versions "$VERSION"

echo "==> Committing release files"
git add \
  downtify/__init__.py \
  pyproject.toml \
  Makefile \
  Dockerfile \
  version.js \
  version.sh \
  frontend/package.json \
  frontend/package-lock.json \
  frontend/android/app/build.gradle \
  frontend/dist

if git diff --cached --quiet; then
  echo "Nothing to commit after version bump." >&2
  exit 1
fi

git commit -m "$(cat <<EOF
chore: release ${TAG}

Bump Downtify to ${VERSION}, rebuild frontend assets, and sync Android
version metadata for the matching release-signed APK.
EOF
)"

echo "==> Pushing main"
git pull --rebase origin main
git push origin main

echo "==> Creating GitHub release (${TAG})"
gh workflow run release.yml \
  --ref main \
  -f "version=${VERSION}" \
  -f docker=true \
  -f prerelease=false \
  -f draft=false

echo "==> Waiting for release workflow"
sleep 5
RELEASE_RUN_ID="$(
  gh run list --workflow=release.yml --limit 1 --json databaseId -q '.[0].databaseId'
)"
gh run watch "$RELEASE_RUN_ID" --exit-status

if ! gh release view "$TAG" >/dev/null 2>&1; then
  echo "Release $TAG was not created." >&2
  exit 1
fi

echo "==> Uploading APK to ${TAG}"
gh release upload "$TAG" "$APK_PATH" --clobber

echo "==> Waiting for Docker image build"
sleep 5
DOCKER_RUN_ID="$(
  gh run list --workflow=build.yml --limit 1 --json databaseId -q '.[0].databaseId'
)"
gh run watch "$DOCKER_RUN_ID" --exit-status || {
  echo "Docker build failed or timed out. Check Actions for build.yml." >&2
  exit 1
}

echo
echo "Publish complete."
echo "  Version : $VERSION"
echo "  Tag     : $TAG"
echo "  APK     : $APK_PATH"
echo "  Release : https://github.com/SecuredNodeDynamics/Downtify/releases/tag/${TAG}"
echo "  Image   : ghcr.io/securednodedynamics/downtify:${VERSION}"
