"""Image preparation for the photo path (FR-51, 57; S-03, S-04).

Checks size and magic bytes, decodes in a guarded step with a pixel limit, drops
every metadata block (EXIF, GPS, maker notes) by re-encoding the pixels only,
downscales and returns JPEG bytes. Bytes stay in memory: nothing is written to disk.
"""
from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 40_000_000
MAX_SIDE = 1280
MAGIC = {b"\xff\xd8\xff": "JPEG", b"\x89PNG\r\n\x1a\n": "PNG", b"RIFF": "WEBP"}


class ImageRejected(ValueError):
    pass


def prepare_image(data: bytes) -> bytes:
    if len(data) > MAX_BYTES:
        raise ImageRejected("image larger than 5 MB")
    if not any(data.startswith(m) for m in MAGIC):
        raise ImageRejected("not a JPEG, PNG or WebP image")
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in set(MAGIC.values()):
                raise ImageRejected("unsupported image type")
            if img.width * img.height > MAX_PIXELS:
                raise ImageRejected("image has too many pixels")
            img.load()
            rgb = img.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise ImageRejected("image could not be decoded") from e
    clean = Image.frombytes("RGB", rgb.size, rgb.tobytes())  # pixels only: no EXIF, GPS or other metadata survives
    clean.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    clean.save(out, "JPEG", quality=85)
    return out.getvalue()
