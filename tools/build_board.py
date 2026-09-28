"""Stitch the printed board tiles into a single board image.

The board in shared/SSZemo_Stand_Ups-n-Board.pdf is printed as nine
portrait tiles (pages 2-10) that form a 3x3 grid, rotated 90 degrees.

Usage (from the repo root):
    uv run --with pillow python tools/build_board.py

Requires `pdftoppm` (poppler). Writes frontend/public/board.webp.
All coordinates in backend/app/data/board.json are pixels in this image,
so the DPI and crop box must not change without re-tracing the board.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "shared" / "SSZemo_Stand_Ups-n-Board.pdf"
OUT = ROOT / "frontend" / "public" / "board.webp"

DPI = 100
FIRST_PAGE, LAST_PAGE = 2, 10
# Printed content box of every tile, in 60-dpi pixels (identical on all pages)
CONTENT_BOX_60DPI = (36, 43, 476, 618)


def _hide_seams(board: Image.Image, tile_w: int, tile_h: int) -> Image.Image:
    """Paint over the white print margins where tiles meet, keeping the image size.

    Each seam band is replaced by a linear blend of the pixels just outside it.
    """
    px = board.load()
    width, height = board.size
    for b in (tile_w, 2 * tile_w):
        x0, x1 = b - 5, b + 4  # untouched columns either side of the seam
        for y in range(height):
            left, right = px[x0, y], px[x1, y]
            for x in range(x0 + 1, x1):
                t = (x - x0) / (x1 - x0)
                px[x, y] = tuple(round(l + (r - l) * t) for l, r in zip(left, right))
    for b in (tile_h, 2 * tile_h):
        y0, y1 = b - 5, b + 4
        for x in range(width):
            top, bottom = px[x, y0], px[x, y1]
            for y in range(y0 + 1, y1):
                t = (y - y0) / (y1 - y0)
                px[x, y] = tuple(round(u + (d - u) * t) for u, d in zip(top, bottom))
    return board


def main() -> None:
    scale = DPI / 60
    box = tuple(round(v * scale) for v in CONTENT_BOX_60DPI)

    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "tile"
        subprocess.run(
            ["pdftoppm", "-r", str(DPI), "-f", str(FIRST_PAGE), "-l", str(LAST_PAGE),
             "-png", str(PDF), str(prefix)],
            check=True,
        )
        tiles = [
            Image.open(f"{prefix}-{page:02d}.png").convert("RGB").crop(box)
            for page in range(FIRST_PAGE, LAST_PAGE + 1)
        ]

    w, h = tiles[0].size
    sheet = Image.new("RGB", (w * 3, h * 3))
    for idx, tile in enumerate(tiles):
        row, col = divmod(idx, 3)
        sheet.paste(tile, (col * w, row * h))

    board = _hide_seams(sheet.rotate(90, expand=True), tile_w=h, tile_h=w)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    board.save(OUT, "WEBP", quality=85, method=6)
    print(f"Wrote {OUT.relative_to(ROOT)} ({board.width}x{board.height})")


if __name__ == "__main__":
    main()
