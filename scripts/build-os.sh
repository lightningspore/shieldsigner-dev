#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
os_dir="$(python3 "$project_dir/scripts/firmware_paths.py" os-source)"
os_work="$(python3 "$project_dir/scripts/firmware_paths.py" os-work)"
staging_root="$(python3 "$project_dir/scripts/firmware_paths.py" staging)"
legacy_os_dir="$project_dir/tools/os/seedsigner-os"
os_commit=e7589465aff172f4f510ad46d18776ccc8d2c203
image_variant="${SHIELDSIGNER_IMAGE_VARIANT:-production}"
case "$image_variant" in production) upstream_variant=non-dev; usb_mode=auto ;; dev) upstream_variant=dev; usb_mode=gadget ;; *) echo 'Image variant must be production or dev' >&2; exit 1 ;; esac
export SHIELDSIGNER_IMAGE_VARIANT="$image_variant"
reader_variant="${SHIELDSIGNER_READER_VARIANT:-UR2}"
case "$reader_variant" in UR2|URT) ;; *) echo "Reader variant must be UR2 or URT" >&2; exit 1 ;; esac
camera_backend="${SHIELDSIGNER_CAMERA_BACKEND:-rust}"
case "$camera_backend" in rust|vendor) ;; *) echo "Camera backend must be rust or vendor" >&2; exit 1 ;; esac
app_commit=efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f
build_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
default_output="$os_work/os-$reader_variant-$camera_backend-$image_variant-$build_stamp"
output_dir="${SHIELDSIGNER_OUTPUT_DIR:-$default_output}"
mkdir -p "$(dirname "$os_dir")" "$output_dir" "$staging_root"
# Preserve the existing SDK/Docker bind-mount cache when adopting the layout.
# Never move a checkout which may be in use by an older launcher.
if [[ ! -e "$os_dir" && -d "$legacy_os_dir/.git" && ! -L "$legacy_os_dir" ]]; then
  # Reuse the wrapper's inherited descriptor; direct invocations acquire the same lock.
  if ! { true >&9; } 2>/dev/null; then
    exec 9>"$project_dir/dist/os-image-build.lock"
  fi
  flock -n 9 || { echo 'Another image job owns the workspace/cache' >&2; exit 2; }
  active_containers="$(docker ps --format '{{.Names}}')" || { echo 'Cannot verify SDK build inactivity' >&2; exit 2; }
  if grep -q '^seedsigner-build-' <<< "$active_containers"; then
    echo 'An SDK build is active; leave its legacy checkout in place and retry later' >&2
    exit 2
  fi
  [[ "$(git -C "$legacy_os_dir" rev-parse HEAD)" == "$os_commit" ]] || { echo 'Legacy OS checkout differs from the pinned revision' >&2; exit 1; }
  mv "$legacy_os_dir" "$os_dir"
  ln -s "$os_dir" "$legacy_os_dir"
fi
if [[ ! -d "$os_dir/.git" ]]; then
  git clone --no-checkout https://github.com/3rdIteration/seedsigner-os.git "$os_dir"
  git -C "$os_dir" checkout --detach "$os_commit"
fi
[[ "$(git -C "$os_dir" rev-parse HEAD)" == "$os_commit" ]] || { echo 'OS checkout differs from the pinned revision' >&2; exit 1; }
# Restore only our known hook changes before the reader preparer checks that the
# pinned upstream tree has no unrelated edits. Unknown camera edits are rejected.
uv run "$project_dir/scripts/configure-os-camera.py" "$os_dir" --mode vendor >/dev/null
uv run "$project_dir/scripts/configure-os-reader.py" "$os_dir" --variant "$reader_variant" --manifest "$output_dir/reader-config.json"
if [[ "$camera_backend" == rust ]]; then
  uv run "$project_dir/scripts/configure-os-camera.py" "$os_dir" --mode rust --manifest "$output_dir/camera-hooks.json"
fi
[[ "${SHIELDSIGNER_PREPARE_ONLY:-0}" == 1 ]] && exit 0
if [[ "$camera_backend" == rust ]]; then
  export MINI_CMA_SIZE=12M
  if [[ -z "${SHIELDSIGNER_CAMERA_BUNDLE:-}" ]]; then
    mise run camera:rust:arm
    mise run camera:qr:native-build
    stage_dir="$(mktemp -d "$staging_root/camera-$build_stamp.XXXXXX")"
    bundle_dir="$stage_dir/camera-bundle"
    uv run "$project_dir/scripts/prepare-camera-image.py" --output "$bundle_dir" --variant "$image_variant" > "$output_dir/camera-bundle.json"
    export SHIELDSIGNER_CAMERA_BUNDLE="$bundle_dir"
  else
    uv run "$project_dir/scripts/prepare-camera-image.py" --verify "$SHIELDSIGNER_CAMERA_BUNDLE" > "$output_dir/camera-bundle.json"
  fi
else
  unset SHIELDSIGNER_CAMERA_BUNDLE
fi
if [[ "$camera_backend" == rust ]]; then
python3 - "$SHIELDSIGNER_CAMERA_BUNDLE/manifest.json" "$image_variant" <<'PY_CHECK'
import json,sys
m=json.load(open(sys.argv[1]))
if m.get('imageVariant','production') != sys.argv[2]: raise SystemExit('Camera bundle image variant mismatch')
if m.get('kernelProofPending') and not __import__('os').environ.get('SHIELDSIGNER_KERNEL_PROBE_ONLY') == '1': raise SystemExit('Probe-only bundle cannot build an image')
PY_CHECK
fi
cd "$os_dir"
set +e
./build.sh --luckfox build --microsd --model mini --jobs "${SHIELDSIGNER_BUILD_JOBS:-4}" \
  --variant "$upstream_variant" --usb-mode "$usb_mode" --readonly-rootfs on --disable-uart2-console-debug true \
  --seedsigner-ref "$app_commit" --output "$output_dir" 2>&1 | tee "$output_dir/build.log"
result=${PIPESTATUS[0]}
exit "$result"
