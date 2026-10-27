#!/usr/bin/env python3
"""Compare captured AWB translation with original ARM using its actual snapshot.
Inputs/output reports may contain private scene statistics; keep them local.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct
from awb_translation_reference import OriginalTranslation
from differential import BINARY


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("sdk", type=Path)
    parser.add_argument("translated", type=Path)
    parser.add_argument("--configuration-id", type=int, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raw = args.raw.read_bytes()
    sdk = args.sdk.read_bytes()
    actual = args.translated.read_bytes()
    assert len(raw) in (13036, 13040) and len(sdk) == 1204 and len(actual) == 7680
    parameters = struct.unpack_from("<I", raw, 0x32E8)[0]
    assert parameters == args.configuration_id
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    native = OriginalTranslation()
    status, expected, valid, info, frame, sequence = native.run(
        raw, sdk, 0, zero_destination=True
    )
    assert (
        status == 0
        and valid
        and info
        and frame == sequence == struct.unpack_from("<I", raw, 0x32E4)[0]
    )
    assert actual == expected, next(
        (i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), None
    )
    report = dict(
        binarySha256=sha,
        statisticsSha256=hashlib.sha256(raw).hexdigest(),
        snapshotSha256=hashlib.sha256(sdk).hexdigest(),
        translatedSha256=hashlib.sha256(actual).hexdigest(),
        frameId=frame,
        parametersId=parameters,
        bytesCompared=len(actual),
        mismatches=0,
        scope="Real captured ISP32 statistics plus exact supplied SDK snapshot, full original single-ISP translation",
        limitations=[
            "Object access and single-ISP routing are controlled oracle boundaries; actual translation instructions execute.",
            "Does not qualify automatic white balance, physical exposure timing or vendor-free cold startup.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
