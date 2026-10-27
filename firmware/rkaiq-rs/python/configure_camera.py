"""Create a managed camera configuration on the board using explicit paths."""
import argparse
import json
import os
from pathlib import Path
import stat


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--iq", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parameters", default="/dev/video20")
    parser.add_argument("--image", default="/dev/video11")
    parser.add_argument("--statistics", default="/dev/video19")
    args = parser.parse_args()
    config = {"binary": str((args.kit / "bin/camera-probe").resolve()),
              "plan": str(args.plan.resolve()), "iq": str(args.iq.resolve()),
              "output_directory": str(args.results.resolve()),
              "parameters": str(Path(args.parameters).resolve()),
              "image": str(Path(args.image).resolve()),
              "statistics": str(Path(args.statistics).resolve())}
    for name in ["binary", "plan", "iq"]:
        if not Path(config[name]).is_file():
            parser.error("Missing " + name + " file: " + config[name])
    if not os.access(config["binary"], os.X_OK):
        parser.error("camera-probe is not executable; preserve extraction permissions or chmod +x it")
    for name in ["parameters", "image", "statistics"]:
        if not stat.S_ISCHR(Path(config[name]).stat().st_mode):
            parser.error(name + " must name a camera character device")
    if args.output.exists():
        parser.error("Output already exists; choose a new configuration filename")
    args.results.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(config, output, indent=2)
        output.write("\n")
    print("Created " + str(args.output.resolve()))


if __name__ == "__main__":
    main()
