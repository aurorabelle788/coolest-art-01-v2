# coolest-art-01 entry (Python 3.13, standard library only).
#
# The art is the entry.png beside this file: a white-haired samurai
# with a glowing red katana, a white dragon coiling behind him under a
# huge blood-red moon, red torii gate, pagoda and waterfalls, red maple
# leaves. The program copies it to the output directory. The file holds
# JPEG bytes (first bytes FF D8 FF) under the name entry.png, which the
# rules allow: a file is told apart by its first bytes, and the name
# stays entry.png either way.
#
# Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
# /output:
#   mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

import hashlib
import os
import shutil
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

MAX_BYTES = 1_048_576
MAX_SIDE = 1024


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Width and height from a PNG's IHDR chunk (stdlib only)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: missing signature")
    if data[12:16] != b"IHDR":
        raise ValueError("not a PNG: missing IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Width and height from a JPEG's first frame header (stdlib only)."""
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG: missing SOI marker")
    i = 2
    while i + 1 < len(data):
        if data[i] != 0xFF:
            raise ValueError("corrupt JPEG marker stream")
        marker = data[i + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):  # SOF0/1/2: precision, height, width
            height, width = struct.unpack(">HH", data[i + 5 : i + 9])
            return width, height
        i += 2 + length
    raise ValueError("no JPEG frame header found")


def image_dimensions(data: bytes) -> tuple[int, int]:
    """Dispatch on magic bytes: PNG or JPEG, like the gate scorer."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return png_dimensions(data)
    if data[:2] == b"\xff\xd8":
        return jpeg_dimensions(data)
    raise ValueError("entry.png is neither PNG nor JPEG")


def image_complete(data: bytes) -> bool:
    """True when the file runs through to its end marker: PNG's 12-byte
    IEND chunk (length 0, 'IEND', CRC) or JPEG's EOI marker. A truncated
    file is not a whole image."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return len(data) >= 12 and data[-12:-8] == b"\x00\x00\x00\x00" and data[-8:-4] == b"IEND"
    if data[:2] == b"\xff\xd8":
        return data.rstrip(b"\x00")[-2:] == b"\xff\xd9"
    return False


def main() -> None:
    src = HERE / "entry.png"
    data = src.read_bytes()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"entry.png is {len(data)} bytes, over the {MAX_BYTES} cap")
    width, height = image_dimensions(data)
    if width > MAX_SIDE or height > MAX_SIDE:
        raise SystemExit(f"entry.png is {width}x{height}, over the {MAX_SIDE} cap")
    if not image_complete(data):
        raise SystemExit("entry.png is truncated: no end marker")
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "entry.png"
    shutil.copyfile(src, dest)
    if hashlib.sha256(dest.read_bytes()).hexdigest() != hashlib.sha256(data).hexdigest():
        raise SystemExit("copied bytes differ from the source image")


if __name__ == "__main__":
    main()
