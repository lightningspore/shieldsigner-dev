"""Display-only RGBW bench for the confirmed base-fork wiring, not FOX_22.

Requires exclusive LCD GPIO/SPI ownership. Does not instantiate Renderer,
HardwareButtons or Camera, and does not change app/image configuration.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

MAPPING = {"dc": ["/dev/gpiochip1", 24], "rst": ["/dev/gpiochip1", 25],
           "bl": "disabled", "spi_bus": 0, "spi_device": 0, "spi_hz": 1000000}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, default=Path("/opt/src"))
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--hold-seconds", type=float, default=30)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not 0 <= args.hold_seconds <= 120:
        parser.error("hold-seconds must be between 0 and 120")
    if args.report and args.report.exists():
        parser.error("Choose a new report filename")
    profile = json.loads(args.profile.read_text())
    if profile.get("display") != MAPPING:
        parser.error("Only the confirmed base-fork display mapping is supported")
    sys.path.insert(0, str(args.app_root))
    from PIL import Image, ImageDraw, ImageFont
    import seedsigner.hardware.displays.ST7789 as driver
    # Only the imported driver's configuration lookup is overridden in this
    # process. Installed source/configuration and runtime profile stay intact.
    driver.get_hardware_pin_mapping = lambda _: {"display": MAPPING}
    driver.Settings.get_platform_default_hardware_config = staticmethod(lambda: "bench-base-fork")
    image = Image.new("RGB", (240, 240), "black")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(args.app_root / "seedsigner/resources/fonts/OpenSans-SemiBold.ttf"), 18)
    for box, color, label, pos in [((0, 0, 119, 99), "red", "RED", (10, 32)),
                                   ((120, 0, 239, 99), "green", "GREEN", (130, 32)),
                                   ((0, 100, 119, 199), "blue", "BLUE", (10, 132)),
                                   ((120, 100, 239, 199), "white", "WHITE", (130, 132))]:
        draw.rectangle(box, fill=color)
        draw.text(pos, label, font=font, fill="black" if color == "white" else "white")
    draw.text((8, 208), "BLACK / DC56 R57", font=font, fill="white")
    source = Path(driver.__file__)
    report = {"kind": "base-fork-display-only-bench", "mapping": MAPPING,
              "helperSha256": digest(__file__), "driverSha256": digest(source),
              "profileSha256": digest(args.profile), "spiWriteCompleted": False,
              "normalColorBaseline": "set_color_inversion(False): raw INVON",
              "physicalAppearanceQualified": False, "closed": False,
              "scope": "SPI write success does not verify visible colors; requires human observation. No button/camera/backlight initialization."}
    display = None
    try:
        display = driver.ST7789(240, 240)
        display.set_color_inversion(False)
        display.show_image(image, 0, 0)
        report["spiWriteCompleted"] = True
        print(json.dumps(report), flush=True)
        time.sleep(args.hold_seconds)
    finally:
        if display is not None:
            display.close()
            report["closed"] = True
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
