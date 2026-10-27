#!/usr/bin/env python3
"""Compare explicit enabled profile blocks with a captured Rust startup mask."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import re

BLOCKS = [
    ("CCM", 8, "ccm_calib_v2/control/enable", "Calibrated color correction"),
    ("LSC", 4, "lsc_v2/common/enable", "Lens shading correction"),
    ("DPCC", 0, "adpcc_calib/DpccTuningPara/Enable", "Defect pixel correction"),
    ("BAYNR", 36, "bayer2dnr_v23/TuningPara/enable", "Spatial Bayer noise reduction"),
    ("BAY3D", 37, "bayertnr_v23/TuningPara/enable", "Temporal Bayer noise reduction"),
    ("YNR", 38, "ynr_v22/TuningPara/enable", "Luma noise reduction"),
    ("CNR", 39, "cnr_v30/TuningPara/enable", "Chroma noise reduction"),
    ("SHARP", 40, "sharp_v33/TuningPara/enable", "Sharpening"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("iq", type=Path)
    parser.add_argument("startup", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--uapi",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / ".tools/reverse-engineering/kernel-uapi/linux",
    )
    args = parser.parse_args()
    macros = {}
    headers = [
        args.uapi / name
        for name in (
            "rk-isp2-config.h",
            "rk-isp21-config.h",
            "rk-isp3-config.h",
            "rk-isp32-config.h",
        )
    ]
    for header in headers:
        macros.update(
            re.findall(r"^#define\s+(ISP\w+)\s+([^\n]+)", header.read_text(), re.M)
        )

    def resolve(name):
        value = macros.get(name, name).strip()
        while value.startswith("(") and value.endswith(")"):
            value = value[1:-1].strip()
        bit = re.fullmatch(r"BIT_ULL\((\w+)\)", value)
        if bit:
            return 1 << resolve(bit[1])
        if value.isdecimal():
            return int(value)
        assert value != name and value in macros, "Unsupported UAPI macro: " + name
        return resolve(value)

    for name, bit, _, _ in BLOCKS:
        assert resolve("ISP32_MODULE_" + name) == 1 << bit

    scene = json.loads(args.iq.read_text())["main_scene"][0]["sub_scene"][0][
        "scene_isp32"
    ]
    raw = args.startup.read_bytes()
    assert len(raw) == 11145
    en_update, enabled, cfg_update = struct.unpack_from("<QQQ", raw)
    rows = []
    for name, bit, pointer, purpose in BLOCKS:
        value = scene
        for key in pointer.split("/"):
            value = value[key]
        assert value in (True, False, 0, 1) and not isinstance(value, (dict, list))
        rows.append(
            {
                "name": name,
                "bit": bit,
                "purpose": purpose,
                "profilePointer": "/main_scene/0/sub_scene/0/scene_isp32/" + pointer,
                "profileConfiguredEnabled": bool(value),
                "startupEnableUpdated": bool(en_update & (1 << bit)),
                "rustStartupEnabled": bool(enabled & (1 << bit)),
                "startupConfigurationUpdated": bool(cfg_update & (1 << bit)),
            }
        )
    report = {
        "kind": "selected-profile-vs-rust-startup-module-audit",
        "iqSha256": hashlib.sha256(args.iq.read_bytes()).hexdigest(),
        "startupSha256": hashlib.sha256(raw).hexdigest(),
        "uapiSha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in headers
        },
        "startupMasks": [hex(x) for x in (en_update, enabled, cfg_update)],
        "blocks": rows,
        "profileEnabledButRustDisabled": [
            r["name"]
            for r in rows
            if r["profileConfiguredEnabled"] and not r["rustStartupEnabled"]
        ],
        "limitations": [
            "Profile enable flags do not prove the vendor daemon enabled these blocks on hardware.",
            "The captured startup request is not independent register readback.",
            "This selected-block audit does not inventory all calibration sections or establish whether a block is necessary for QR decoding.",
            "BLS has separately controlled internal stages; its module-enable bit alone must not be used to classify all black-level processing.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {"profileEnabledButRustDisabled": report["profileEnabledButRustDisabled"]}
        )
    )


if __name__ == "__main__":
    main()
