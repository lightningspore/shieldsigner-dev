#!/usr/bin/env bash
# Read actual launcher/container state; log activity alone is not liveness.
set -euo pipefail
job="${1:-}"
if [[ "$job" == --help || "$job" == -h ]]; then
  echo 'Usage: SHIELDSIGNER_BUILD_HOST=builder scripts/os-remote-status.sh [job-name]'
  exit 0
fi
[[ $# -le 1 && ( -z "$job" || "$job" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ) ]] || { echo 'Supply one job name (letters, digits, dots, dashes, underscores)' >&2; exit 2; }
ssh -o BatchMode=yes -o ConnectTimeout=10 "${SHIELDSIGNER_BUILD_HOST:?Set SHIELDSIGNER_BUILD_HOST to the SSH builder host}" "pct exec 610 -- bash -s -- '$job'" <<'REMOTE'
set -euo pipefail
root=/opt/shieldsigner-build
job="${1:-}"
inspect() {
  local directory="$1" pid='' state='' exit_code=''
  echo "Image job: $directory"
  if [[ -f "$directory/exit-code" ]]; then
    exit_code="$(cat "$directory/exit-code")"
    if [[ "$exit_code" =~ ^[0-9]+$ ]]; then
      echo "Terminal exit-code: $exit_code"
    else
      echo 'Invalid terminal exit-code; result unknown'
    fi
  else
    if [[ -f "$directory/launcher.pid" ]]; then pid="$(cat "$directory/launcher.pid")"; fi
    if [[ "$pid" =~ ^[0-9]+$ && -r "/proc/$pid/cmdline" && -r "/proc/$pid/environ" ]]; then
      state="$(ps -p "$pid" -o stat= 2>/dev/null || true)"
      if [[ -n "$state" && "$state" != *Z* ]] &&
         tr '\0' '\n' < "/proc/$pid/cmdline" | grep -F 'scripts/run-os-image-job.sh' > /dev/null &&
         tr '\0' '\n' < "/proc/$pid/environ" | grep -Fx "SHIELDSIGNER_OUTPUT_DIR=$directory" > /dev/null; then
        echo 'Matching live launcher:'
        ps -p "$pid" -o pid,etime,stat,args || true
      else
        echo 'No matching live launcher; no terminal result. State unknown.'
      fi
    else
      echo 'No matching live launcher; no terminal result. State unknown.'
    fi
  fi
  if [[ -f "$directory/launcher.log" ]]; then tail -n 5 "$directory/launcher.log" | cut -c 1-300; fi
}
echo 'Current Docker containers (separate from launcher/result evidence):'
docker ps --format '{{.Names}} {{.Status}}' || echo 'Docker status unavailable'
found=0
if [[ -n "$job" ]]; then
  for directory in "$root/dist/firmware/work/os/$job" "$root/dist/os-$job" "$root/dist/os/$job"; do
    [[ -d "$directory" ]] || continue
    inspect "$directory"
    found=1
  done
  [[ "$found" == 1 ]] || { echo "No output directory found for job: $job" >&2; exit 1; }
else
  for directory in "$root"/dist/firmware/work/os/* "$root"/dist/os-* "$root/dist/os"; do
    [[ -d "$directory" ]] || continue
    [[ -f "$directory/launcher.log" || -f "$directory/launcher.pid" || -f "$directory/exit-code" ]] || continue
    inspect "$directory"
    found=1
  done
  [[ "$found" == 1 ]] || echo 'No recorded image jobs found'
fi
REMOTE
