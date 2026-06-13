#!/bin/sh

LOG_LEVEL="${DOWNTIFY_LOG_LEVEL:-info}"
VERSION_FILE="${DOWNTIFY_VERSION_FILE:-/data/app-version}"

if [ "${DOWNTIFY_AUTO_BUMP_VERSION:-1}" = "1" ]; then
    BASE_VERSION="$(python -c 'from downtify import __version__; print(__version__)')"
    python -m downtify.versioning --base "${BASE_VERSION}" --file "${VERSION_FILE}" --bump
fi

exec python main.py web \
    --host 0.0.0.0 \
    --port "${DOWNTIFY_PORT}" \
    --log-level "${LOG_LEVEL}"
