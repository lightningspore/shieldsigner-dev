"""Actual ARM worker through installed SeedSigner: public synthetic bytes and UR.

These are decoder/app integration fixtures, not physical optical qualification.
No private seed, PSBT, camera image or decoded payload is written to the report.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from PIL import Image
import qrcode
from qrcode.util import QRData, MODE_8BIT_BYTE
from shieldsigner_integration import install_camera_backend


def image(data):
    code = qrcode.QRCode(box_size=4, border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
    code.add_data(QRData(data, mode=MODE_8BIT_BYTE))
    code.make(fit=True)
    return code.make_image().convert("RGB")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--camera-config", type=Path,
                        help="Also exercise this app version's real Camera.get_instance/start/read/stop")
    parser.add_argument("--runtime-profile", choices=["luckfox_22", "luckfox_40", "luckfox_pi"],
                        help="Test-only explicit profile; does not qualify device-tree autodetection")
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Choose a new report filename")
    os.environ["SHIELDSIGNER_QR_READER"] = str(args.reader.resolve())
    installed = [args.app_root/"seedsigner/hardware/camera.py", args.app_root/"seedsigner/models/decode_qr.py"]
    before = [digest(path) for path in installed]
    module = install_camera_backend(args.app_root)
    assert install_camera_backend(args.app_root) is module
    client = module.__shieldsigner_qr_client__
    from seedsigner.models.decode_qr import DecodeQR, DecodeQRStatus
    from seedsigner.helpers.ur2.ur import UR
    from seedsigner.helpers.ur2.ur_encoder import UREncoder
    from urtypes.crypto import PSBT as UR_PSBT
    from embit import bip39, psbt, transaction, script

    report = {"passed": False, "opticalScanQualified": False, "nativeWorkerSha256": digest(args.reader),
              "scope": "ARM native worker and actual installed DecodeQR; public synthetic fixtures, no camera input",
              "appSourceSha256": {str(p.relative_to(args.app_root)): digest(p) for p in installed},
              "pythonSourcesSha256": {p.name: digest(p) for p in Path(__file__).parent.glob("*.py")},
              "binaryCases": [], "compactSeedCases": []}
    try:
        for data in [b"\x00\xff\x80\xfe\x00hello\x00\xc0\x81", bytes(range(256)), bytes(range(32))]:
            started = time.monotonic()
            extracted = DecodeQR.extract_qr_data(image(data), is_binary=True)
            assert extracted == data
            report["binaryCases"].append({"payloadBytes": len(data), "byteExact": True,
                                           "seconds": time.monotonic()-started})
        for length in (16, 32):
            entropy = bytes(range(length))
            decoder = DecodeQR()
            assert decoder.add_image(image(entropy)) == DecodeQRStatus.COMPLETE
            assert decoder.get_seed_phrase() == bip39.mnemonic_from_bytes(entropy).split()
            report["compactSeedCases"].append({"entropyBytes": length, "expectedPublicFixture": True})
        # A public synthetic unsigned transaction, no signing keys or real inputs.
        tx = transaction.Transaction(vin=[transaction.TransactionInput(bytes(32), 0)],
                                     vout=[transaction.TransactionOutput(0, script.Script(b"\x6a\x4c\xc8"+bytes(range(200))))])
        payload = psbt.PSBT(tx).serialize()
        encoder = UREncoder(UR("crypto-psbt", UR_PSBT(payload).to_cbor()), max_fragment_len=60)
        decoder = DecodeQR()
        reference = DecodeQR()
        fragments = []
        for _ in range(20):
            part = encoder.next_part()
            fragments.append(part)
            if encoder.is_complete():
                break
        assert len(fragments) > 1
        # Reverse order and duplicate the first fragment to exercise assembly.
        frames = list(reversed(fragments))
        statuses = []
        for part in [frames[0], *frames]:
            data = part.encode("ascii")
            status = decoder.add_image(image(data))
            assert status == reference.add_data(data)
            statuses.append(int(status))
        assert decoder.complete and decoder.get_data_psbt() == payload
        assert reference.complete and reference.get_data_psbt() == payload
        report["animatedUr"] = {"fragments": len(fragments), "framesSubmitted": len(statuses),
                                "reversedOrder": True, "duplicateHandled": True,
                                "duplicateStatus": statuses[1], "matchesInstalledDirectDataStatuses": True,
                                "byteExactReassembledPsbt": True}
        process = client._process
        assert client.stats["starts"] == 1 and client.stats["errors"] == 0
        client.close()
        assert process.poll() == 0
        assert DecodeQR.extract_qr_data(image(b"1BoatSLRHtKNngkdXEeobR76b53LETtpyT"), is_binary=True) == b"1BoatSLRHtKNngkdXEeobR76b53LETtpyT"
        assert client.stats["starts"] == 2
        report["cleanStopAndRestart"] = True
        if args.camera_config:
            os.environ["SHIELDSIGNER_CAMERA_CONFIG"] = str(args.camera_config.resolve())
            if args.runtime_profile:
                from seedsigner.models.settings import Settings
                Settings.RUNTIME_PROFILE = args.runtime_profile
            camera = module.Camera.get_instance()
            received = []
            try:
                camera.start_video_stream_mode()
                stream = camera._video_stream
                deadline = time.monotonic()+15
                while len(received) < 6 and time.monotonic() < deadline:
                    frame = camera.read_video_stream()
                    if frame is None or stream.sequence in received:
                        time.sleep(.02)
                        continue
                    received.append(stream.sequence)
                    assert frame.mode == "RGB" and frame.size == (640,480)
                    DecodeQR.extract_qr_data(frame, is_binary=True)
                assert len(received) == 6
                preview = camera.read_video_stream(as_image=True)
                report["realCamera"] = {"samples": len(received), "received": stream.frames_received,
                                        "nativeSize": list(frame.size), "previewSize": list(preview.size),
                                        "runtimeProfile": getattr(camera, "_runtime_profile", "legacy"),
                                        "testProfileOverride": args.runtime_profile,
                                        "backendInfo": getattr(stream, "backend_info", None)}
            finally:
                camera.stop_video_stream_mode()
            report["realCamera"].update(ownerExitCode=stream.owner_exit_code,
                                        workerClosedOnCameraStop=client._process is None,
                                        logInfo=stream.log_info)
            assert stream.owner_exit_code == 0 and client._process is None
            if args.runtime_profile:
                try:
                    camera.start_single_frame_mode()
                    still = camera._capture
                    deadline = time.monotonic()+15
                    captured = None
                    while captured is None and time.monotonic() < deadline:
                        captured = camera.capture_frame()
                        if captured is None:
                            time.sleep(.02)
                    assert captured is not None and captured.mode == "RGB"
                finally:
                    camera.stop_single_frame_mode()
                assert still.owner_exit_code == 0 and camera._capture is None
                report["realStillCapture"] = {"returnedImageSize": list(captured.size),
                                             "backendInfo": still.backend_info,
                                             "ownerExitCode": still.owner_exit_code,
                                             "cleanStop": True}
        report["installedAppUnchanged"] = before == [digest(path) for path in installed]
        assert report["installedAppUnchanged"]
        report["passed"] = True
    finally:
        client.close()
        report["nativeStats"] = client.stats
        args.report.write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps(report))


if __name__ == "__main__":
    main()
