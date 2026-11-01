#!/bin/sh
set -eu
# Explicit tested Mini memory policy; keep GPIO/display selection separate.
ulimit -l 4096
export SHIELDSIGNER_SMALL_RAM=1
export SHIELDSIGNER_CAMERA_LOCK_CODE=1
# Required memory setup; failure holds the application before imports.
/usr/lib/shieldsigner-camera/enable-zram-image.sh
export SHIELDSIGNER_LCD_BACKEND=rust
export SHIELDSIGNER_FRONTEND_BACKEND=rust
umask 077
mkdir -p /tmp/shieldsigner-camera
/usr/lib/shieldsigner-camera/cold-camera-modules.sh
unset SHIELDSIGNER_CAMERA_STREAM_FORMAT
export PYTHONPATH=/usr/lib/shieldsigner-camera/python${PYTHONPATH:+:$PYTHONPATH}
export SHIELDSIGNER_QR_READER=/usr/lib/shieldsigner-camera/shieldsigner-qr-reader
cd /opt/src
exec python3 -u /usr/lib/shieldsigner-camera/python/shieldsigner_integration.py \
  --app-root /opt/src --config /usr/lib/shieldsigner-camera/owner.json \
  --qr-reader /usr/lib/shieldsigner-camera/shieldsigner-qr-reader "$@"
