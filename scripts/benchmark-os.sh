#!/usr/bin/env bash
# Guest-side watcher: wait for the existing first run, then compare a cached run.
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
first="$project_dir/dist/os"
second="$project_dir/dist/os-second"
metrics="$project_dir/dist/os-benchmark"
mkdir -p "$metrics"
exec 9>"$metrics/watcher.lock"
flock -n 9 || { echo 'Benchmark watcher already running'; exit 1; }
test ! -e "$second/exit-code" || { echo 'Second run already completed; preserve results before restarting'; exit 1; }
echo 'Watching the first build; second run starts only on success.'
while [[ ! -f "$first/exit-code" ]]; do sleep 30; done
first_status="$(cat "$first/exit-code")"
[[ "$first_status" == 0 ]] || { echo "First build failed: $first_status; second run skipped"; exit 1; }
first_start="$(stat -c %W "$first/launcher.log")"
[[ "$first_start" -gt 0 ]] || first_start="$(stat -c %Y "$first/launcher.log")"
first_end="$(stat -c %Y "$first/exit-code")"
first_seconds=$((first_end-first_start))
mkdir -p "$second"
second_start="$(date +%s)"
echo "First build succeeded in approximately $first_seconds seconds. Starting cached second build."
set +e
SHIELDSIGNER_OUTPUT_DIR="$second" SHIELDSIGNER_BUILD_JOBS=6 bash "$project_dir/scripts/build-os-cached.sh" > "$second/launcher.log" 2>&1
second_status=$?
set -e
echo "$second_status" > "$second/exit-code"
second_end="$(date +%s)";second_seconds=$((second_end-second_start))
cache_restored=false
if grep -q 'cached Rust toolchain restored:' "$second/build.log" && ! grep -Eq '^>>> host-rust [0-9.]+ Building' "$second/build.log"; then cache_restored=true; fi
faster=false
if [[ "$second_status" == 0 && "$second_seconds" -lt "$first_seconds" ]]; then faster=true; fi
matching=false
if [[ -s "$first/sha256sums.txt" && -s "$second/sha256sums.txt" ]] && cmp -s "$first/sha256sums.txt" "$second/sha256sums.txt"; then matching=true; fi
printf '{"firstExitCode":%s,"firstSeconds":%s,"secondExitCode":%s,"secondSeconds":%s,"rustCacheRestoreObserved":%s,"secondFaster":%s,"artifactChecksumsMatch":%s}\n' \
 "$first_status" "$first_seconds" "$second_status" "$second_seconds" "$cache_restored" "$faster" "$matching" > "$metrics/result.json"
cat "$metrics/result.json"
[[ "$second_status" == 0 && "$cache_restored" == true && "$faster" == true ]]
