"""Generate public synthetic byte-mode QR fixtures for the ARM reader check."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
import qrcode
from qrcode.util import QRData, MODE_8BIT_BYTE

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
fixtures = {"nul-highbit": b"\x00\xff\x80\xfe\x00hello\x00\xc0\x81",
            "all-byte-values": bytes(range(256)),
            "binary32-bytes": bytes((x * 37) % 256 for x in range(32))}
manifest = []
for name, payload in fixtures.items():
    qr = qrcode.QRCode(box_size=5, border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(QRData(payload, mode=MODE_8BIT_BYTE))
    qr.make(fit=True)
    image = qr.make_image().convert("L")
    assert image.width <= 640 and image.height <= 480
    frame = Image.new("L", (640, 480), 255)
    frame.paste(image, ((640-image.width)//2, (480-image.height)//2))
    (args.output / (name + ".luma")).write_bytes(frame.tobytes())
    (args.output / (name + ".payload")).write_bytes(payload)
    manifest.append({"name": name, "payloadBytes": len(payload),
                     "payloadSha256": hashlib.sha256(payload).hexdigest(),
                     "inputSha256": hashlib.sha256(frame.tobytes()).hexdigest()})
(args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
