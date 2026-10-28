#!/usr/bin/env bash
set -euo pipefail
ssh -o BatchMode=yes -o ConnectTimeout=10 "${SHIELDSIGNER_BUILD_HOST:?Set SHIELDSIGNER_BUILD_HOST to the SSH builder host}" 'pct exec 610 -- bash -s' <<'REMOTE'
if test -f /opt/shieldsigner-build/dist/os/launcher.log; then
  tail -n 8 /opt/shieldsigner-build/dist/os/launcher.log | cut -c 1-300
else
  echo Legacy-baseline-log-not-present
fi
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
for directory in /opt/shieldsigner-build/dist/os-rust-*; do
  test -d "$directory" || continue
  echo "Rust-camera image: $(basename "$directory")"
  if test -f "$directory/launcher.pid"; then
    pid="$(cat "$directory/launcher.pid")"
    ps -p "$pid" -o pid,args || true
  fi
  tail -n 5 "$directory/launcher.log" 2>/dev/null | cut -c 1-250 || true
  if test -f "$directory/exit-code"; then
    echo "Exit-code: $(cat "$directory/exit-code")"
  else
    echo "No terminal exit status recorded; inspect live process and Docker above"
  fi
done
REMOTE
