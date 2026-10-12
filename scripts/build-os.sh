#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
os_dir="$project_dir/tools/os/seedsigner-os"
os_commit=e7589465aff172f4f510ad46d18776ccc8d2c203
app_commit=efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f
output_dir="${SHIELDSIGNER_OUTPUT_DIR:-$project_dir/dist/os}"
mkdir -p "$project_dir/tools/os" "$output_dir"
if [[ ! -d "$os_dir/.git" ]]; then
  git clone --no-checkout https://github.com/3rdIteration/seedsigner-os.git "$os_dir"
  git -C "$os_dir" checkout --detach "$os_commit"
fi
[[ "$(git -C "$os_dir" rev-parse HEAD)" == "$os_commit" ]] || { echo 'OS checkout differs from the pinned revision' >&2; exit 1; }
[[ -z "$(git -C "$os_dir" status --porcelain)" ]] || { echo 'OS checkout has local changes; review them before building' >&2; exit 1; }
cd "$os_dir"
set +e
./build.sh --luckfox build --microsd --model mini --jobs "${SHIELDSIGNER_BUILD_JOBS:-4}" \
  --seedsigner-ref "$app_commit" --output "$output_dir" 2>&1 | tee "$output_dir/build.log"
result=${PIPESTATUS[0]}
exit "$result"
