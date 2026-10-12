#!/usr/bin/env bash
set -euo pipefail
ssh -o BatchMode=yes -o ConnectTimeout=10 "${SHIELDSIGNER_BUILD_HOST:?Set SHIELDSIGNER_BUILD_HOST to the SSH builder host}" 'pct exec 610 -- bash -s' <<'REMOTE'
tail -n 8 /opt/shieldsigner-build/dist/os/launcher.log | cut -c 1-300
if test -f /opt/shieldsigner-build/dist/os/exit-code; then
  echo Exit-code:
  cat /opt/shieldsigner-build/dist/os/exit-code
else
  echo Build-not-finished
fi
docker ps --format '{{.Names}} {{.Status}}'
if test -f /opt/shieldsigner-build/dist/os-benchmark/watcher.log; then
  tail -n 4 /opt/shieldsigner-build/dist/os-benchmark/watcher.log
fi
if test -f /opt/shieldsigner-build/dist/os-second/launcher.log; then
  echo Second-build:
  tail -n 6 /opt/shieldsigner-build/dist/os-second/launcher.log | cut -c 1-300
fi
if test -f /opt/shieldsigner-build/dist/os-benchmark/result.json; then
  cat /opt/shieldsigner-build/dist/os-benchmark/result.json
fi
REMOTE
