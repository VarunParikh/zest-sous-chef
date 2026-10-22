"""Build AppIcon.icns from the owner-supplied artwork (ADR-011). Run by build_dmg.sh with the bundled Python (Pillow).

The source is a full-bleed rounded square on a white background. The corner radius is measured on the diagonal,
the white corners become transparent, and the artwork is placed on Apple's macOS icon grid: 824 px inside a
1024 px canvas, with a soft shadow, so it sits at the same size as other apps in the Dock and Finder.

Usage: python make_icon.py SOURCE OUT.icns
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

CANVAS, ART, SHADOW_Y, SHADOW_BLUR = 1024, 824, 12, 14
SIZES = [16, 32, 128, 256, 512]


def corner_radius(img: Image.Image) -> float:
    """First non-white pixel on the diagonal sits at r * (1 - 1/sqrt(2)) for a rounded square of radius r."""
    rgb = img.convert("RGB")
    for t in range(min(img.size) // 2):
        if sum(rgb.getpixel((t, t))) < 3 * 235:
            return t / (1 - 2 ** -0.5)
    return 0.0


def icon(source: Path) -> Image.Image:
    src = Image.open(source).convert("RGBA")
    side = min(src.size)
    src = src.crop(((src.width - side) // 2, (src.height - side) // 2, (src.width + side) // 2, (src.height + side) // 2))
    radius = corner_radius(src) * ART / side
    art = src.resize((ART, ART), Image.LANCZOS)
    mask = Image.new("L", (ART * 4, ART * 4), 0)  # drawn at 4x and reduced, for smooth edges
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, ART * 4 - 1, ART * 4 - 1), radius=radius * 4, fill=255)
    art.putalpha(mask.resize((ART, ART), Image.LANCZOS))

    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    off = (CANVAS - ART) // 2
    shadow = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 90), (off, off + SHADOW_Y), art.getchannel("A"))
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR)))
    canvas.alpha_composite(art, (off, off))
    return canvas


def main(source: str, out: str) -> int:
    big = icon(Path(source))
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "AppIcon.iconset"
        iconset.mkdir()
        for s in SIZES:
            big.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
            big.resize((s * 2, s * 2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", "-o", out, str(iconset)], check=True)
    big.save(Path(out).with_suffix(".png"))  # a preview of the 1024 px master
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
