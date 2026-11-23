#!/usr/bin/env python3
"""Entrypoint for the news-image-20261123 entry (Python 3.13, stdlib only).

Copies the pre-rendered entry.png (drawn by render.py, held in this
repository) to the output directory, after validating it: PNG magic,
IHDR checksum, 1024x1024, at most 1 MiB. The copy is byte-identical, so
both grader runs write the same bytes.

Run:  python3 main.py --output out --verbose
      MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import argparse
import hashlib
import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

MAX_BYTES = 1048576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def fail(msg):
    print(f"main.py: {msg}", file=sys.stderr)
    return 1


def validate(path):
    """Validate entry.png; return (width, height, size)."""
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError(f"entry.png is {len(data)} bytes, over 1 MiB")
    if data[:8] != PNG_MAGIC:
        raise ValueError("entry.png is not a PNG (bad magic)")
    if len(data) < 33 or data[12:16] != b"IHDR":
        raise ValueError("entry.png has no IHDR chunk")
    ihdr = data[16:29]
    width, height = struct.unpack(">II", ihdr[:8])
    crc_stored = struct.unpack(">I", data[29:33])[0]
    crc_actual = zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF
    if crc_stored != crc_actual:
        raise ValueError("entry.png IHDR checksum mismatch")
    if (width, height) != (1024, 1024):
        raise ValueError(f"entry.png is {width}x{height}, need 1024x1024")
    return width, height, len(data)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    out_dir = args.output or os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    here = Path(__file__).resolve().parent
    src = here / "entry.png"
    if not src.is_file():
        return fail(f"entry.png not found next to main.py ({here})")

    try:
        width, height, size = validate(src)
    except ValueError as exc:
        return fail(str(exc))

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    dest = out_path / "entry.png"
    shutil.copyfile(src, dest)

    # Copy integrity: the copy must be byte-identical to the validated source.
    src_digest = hashlib.sha256(src.read_bytes()).hexdigest()
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    if digest != src_digest:
        return fail("copy mismatch: output differs from validated entry.png")
    if args.verbose:
        print(f"entry.png: {width}x{height}, {size} bytes, "
              f"IHDR CRC ok, copied to {dest}")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
