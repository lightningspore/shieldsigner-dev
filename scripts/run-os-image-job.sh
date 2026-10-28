#!/usr/bin/env bash
# Detached Linux-builder runner: preserve the actual build exit status atomically.
set -uo pipefail
export PATH="/usr/local/bin:$PATH"
: "${SHIELDSIGNER_OUTPUT_DIR:?Set a new output directory for this image attempt}"
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$SHIELDSIGNER_OUTPUT_DIR"
mkdir -p "$project_dir/dist"
if [[ "${SHIELDSIGNER_IMAGE_LOCK_INHERITED:-0}" != 1 ]]; then
  exec 9>"$project_dir/dist/os-image-build.lock"
fi
if ! flock -n 9; then
  echo "Another image build owns this workspace/cache" >&2
  printf '2\n' > "$SHIELDSIGNER_OUTPUT_DIR/exit-code"
  exit 2
fi
cd "$project_dir"
date -u +%Y-%m-%dT%H:%M:%SZ > "$SHIELDSIGNER_OUTPUT_DIR/started-at"
bash scripts/build-os.sh
result=$?
printf '%s\n' "$result" > "$SHIELDSIGNER_OUTPUT_DIR/exit-code.tmp"
mv "$SHIELDSIGNER_OUTPUT_DIR/exit-code.tmp" "$SHIELDSIGNER_OUTPUT_DIR/exit-code"
date -u +%Y-%m-%dT%H:%M:%SZ > "$SHIELDSIGNER_OUTPUT_DIR/finished-at"
exit "$result"
