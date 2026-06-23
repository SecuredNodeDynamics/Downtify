#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo "Usage: $0 [--current|patch|minor|major|X.Y.Z]"
  echo
  echo "Examples:"
  echo "  $0 --current"
  echo "  $0 patch"
  echo "  $0 minor"
  echo "  $0 major"
  echo "  $0 2.6.0"
  exit 1
}

current_version() {
  grep -m1 "__version__" "$REPO_ROOT/downtify/__init__.py" \
    | sed -E "s/.*__version__ = ['\"]([^'\"]+)['\"].*/\1/"
}

validate_semver() {
  if ! echo "$1" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "Error: '$1' is not a valid semver version (expected X.Y.Z)." >&2
    exit 1
  fi
}

bump_version() {
  local version="$1"
  local part="$2"
  local major minor patch
  IFS='.' read -r major minor patch <<< "$version"

  case "$part" in
    patch) patch=$((patch + 1)) ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    major) major=$((major + 1)); minor=0; patch=0 ;;
    *) echo "Error: unknown bump part '$part'" >&2; exit 1 ;;
  esac

  echo "${major}.${minor}.${patch}"
}

[[ $# -eq 1 ]] || usage

if [[ "${1:-}" == "--current" ]]; then
  echo "$(current_version)"
  exit 0
fi

OLD_VERSION="$(current_version)"

if [[ "$1" == patch || "$1" == minor || "$1" == major ]]; then
  NEW_VERSION="$(bump_version "$OLD_VERSION" "$1")"
else
  NEW_VERSION="$1"
  validate_semver "$NEW_VERSION"
fi

if [[ "$OLD_VERSION" == "$NEW_VERSION" ]]; then
  echo "Already at version $NEW_VERSION — nothing to do."
  exit 0
fi

echo "Bumping $OLD_VERSION → $NEW_VERSION"

"${PYTHON:-python}" - <<PY
from pathlib import Path
import re

root = Path(r"$REPO_ROOT")
old = "$OLD_VERSION"
new = "$NEW_VERSION"

files = {
    root / "downtify/__init__.py": [(f"__version__ = '{old}'", f"__version__ = '{new}'")],
    root / "pyproject.toml": [(f'version = "{old}"', f'version = "{new}"')],
    root / "frontend/package.json": [(f'"version": "{old}"', f'"version": "{new}"')],
    root / "Makefile": [(f"DOWNTIFY_VERSION := {old}", f"DOWNTIFY_VERSION := {new}")],
    root / "frontend/src/components/Hero.vue": [(f"|| '{old}'", f"|| '{new}'")],
}

dockerfile = root / "Dockerfile"
if dockerfile.exists():
    files[dockerfile] = [
        (f'LABEL version="{old}"', f'LABEL version="{new}"'),
        (f'org.opencontainers.image.version="{old}"', f'org.opencontainers.image.version="{new}"'),
    ]

for path, replacements in files.items():
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    original = text
    for a, b in replacements:
        text = text.replace(a, b)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"updated {path.relative_to(root)}")

uv_lock = root / "uv.lock"
if uv_lock.exists():
    text = uv_lock.read_text(encoding="utf-8")
    updated = re.sub(
        r'(\[\[package\]\]\nname = "downtify"\nversion = ")[^"]+(")',
        rf'\g<1>{new}\2',
        text,
        count=1,
    )
    if updated != text:
        uv_lock.write_text(updated, encoding="utf-8")
        print(f"updated {uv_lock.relative_to(root)}")

lockfile = root / "frontend/package-lock.json"
if lockfile.exists():
    import json

    data = json.loads(lockfile.read_text(encoding="utf-8"))
    changed = False
    if data.get("version") == old:
        data["version"] = new
        changed = True
    root_package = data.get("packages", {}).get("")
    if isinstance(root_package, dict) and root_package.get("version") == old:
        root_package["version"] = new
        changed = True
    if changed:
        lockfile.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"updated {lockfile.relative_to(root)}")

gradle = root / "frontend/android/app/build.gradle"
if gradle.exists():
    major_s, minor_s, patch_s = new.split(".")
    major = int(major_s)
    minor = int(minor_s)
    patch = int(patch_s)
    if minor > 99 or patch > 99:
        raise SystemExit(
            f"Android versionCode supports minor/patch <= 99: {new}"
        )
    version_code = major * 10000 + minor * 100 + patch
    text = gradle.read_text(encoding="utf-8")
    updated = re.sub(r"versionCode\s+\d+", f"versionCode {version_code}", text)
    updated = re.sub(r'versionName\s+"[^"]+"', f'versionName "{new}"', updated)
    if updated != text:
        gradle.write_text(updated, encoding="utf-8")
        print(f"updated {gradle.relative_to(root)}")
PY

echo
echo "Verification:"
grep "__version__" "$REPO_ROOT/downtify/__init__.py"
grep '^version' "$REPO_ROOT/pyproject.toml"
grep '"version"' "$REPO_ROOT/frontend/package.json" | head -1
