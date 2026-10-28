"""Verify a camera kit's complete manifest without loading camera devices."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--restore-modes", action="store_true",
                        help="Restore verified manifest file modes after an extractor drops executable bits")
    args = parser.parse_args()
    root = args.directory.resolve()
    manifest = json.loads((root / "manifest.json").read_text())
    names = set()
    total = 0
    modes = 0
    for entry in manifest["files"]:
        name = entry["name"]
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or name in names:
            raise ValueError("Invalid or duplicate manifest path")
        names.add(name)
        path = (root / name).resolve()
        path.relative_to(root)
        if not path.is_file() or path.stat().st_size != entry["bytes"]:
            raise ValueError("Missing/size mismatch: " + name)
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != entry["sha256"]:
            raise ValueError("SHA-256 mismatch: " + name)
        if "mode" in entry:
            expected_mode = int(entry["mode"], 8)
            if expected_mode not in (0o644, 0o755):
                raise ValueError("Unsupported manifest mode: " + name)
            if args.restore_modes:
                path.chmod(expected_mode)
            if path.stat().st_mode & 0o777 != expected_mode:
                raise ValueError("File mode mismatch: " + name + "; use --restore-modes after extraction")
            modes += 1
        total += entry["bytes"]
    if not names:
        raise ValueError("Empty manifest")
    print(json.dumps({"passed": True, "version": manifest["version"],
                      "sourceRevision": manifest["sourceRevision"],
                      "filesVerified": len(names), "bytesVerified": total,
                      "fileModesVerified": modes}))


if __name__ == "__main__":
    main()
