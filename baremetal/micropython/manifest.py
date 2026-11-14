# SPDX-License-Identifier: MIT
# Only reviewed port code; no host filesystem or implicit third-party modules.
import os
modules = ("seedsigner_port/__init__.py", "seedsigner_port/buttons.py", "seedsigner_port/native_ui.py", "seedsigner_port/navigation.py", "seedsigner_port/screen_defaults.py", "seedsigner_port/screen_contracts.py")
# The schema contains original floating-point constants and belongs to the
# native app build, which provides double precision and full libm.
if os.environ.get("BM_NATIVE_UI") == "1":
    modules += ("hashlib.py", "hmac.py", "base64.py", "seedsigner_port/scan_loop.py", "seedsigner_port/scan_screen.py", "seedsigner_port/qr_type.py", "seedsigner_port/decode_platform.py", "seedsigner_port/decode_qr.py", "re.py", "seedsigner_port/camera_preview.py", "seedsigner_port/settings_schema.py", "seedsigner_port/settings_platform.py", "seedsigner_port/settings_store.py")
freeze("$(PORT_DIR)/../app", modules)
