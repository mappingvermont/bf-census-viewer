"""Cut a FamilySearch 1900 census page image into readable tiles for transcription.

Usage: python3 -I scripts/fs_tiles.py <page.jpg> <out_dir> [TOWN]

Produces, per page:
  <stem>_overview.jpg        whole page, downscaled
  <stem>_L<k>.jpg            left half (street .. immigration columns) for line band k
  <stem>_R<k>.jpg            right half (citizenship .. ownership columns) for line band k
  <stem>_street.jpg          the vertical street-name column, rotated to read horizontally

The 1900 schedule has 50 lines per side. Line positions are fixed page fractions measured on FamilySearch
scans (the `layout` in TOWN's town.json, or town.DEFAULT_LAYOUT); check the overview if a page is skewed.
Bands overlap by `overlap` lines; printed line numbers are on both outer edges of the form, so every tile
carries line numbers for alignment.
"""
import os
import sys

from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import town  # noqa: E402

BAND_LINES = 10


def line_centers(h, layout):
    top, bottom = layout["line1"], layout["line50"]
    step = (bottom - top) / 49
    return [(top + i * step) * h for i in range(50)], step * h


def bands(h, layout):
    """(y0, y1) pixel ranges of the line bands: BAND_LINES lines each, padded by `overlap` lines."""
    centers, step = line_centers(h, layout)
    pad = step * (0.5 + layout["overlap"])
    out, a = [], 0
    while a < 50:
        b = min(a + BAND_LINES, 50)
        out.append((int(max(0, centers[a] - pad)), int(min(h, centers[b - 1] + pad))))
        a = b
    return out


def main(src, out, layout=town.DEFAULT_LAYOUT):
    os.makedirs(out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(src))[0]
    im = ImageOps.autocontrast(Image.open(src).convert("L"), cutoff=0.5)
    w, h = im.size

    im.resize((1400, int(1400 * h / w))).save(f"{out}/{stem}_overview.jpg", quality=80)

    for k, (y0, y1) in enumerate(bands(h, layout), 1):
        left = im.crop((0, y0, int(0.67 * w), y1))
        left.resize((1900, int(1900 * left.size[1] / left.size[0]))).save(
            f"{out}/{stem}_L{k}.jpg", quality=88)
        right = im.crop((int(0.63 * w), y0, w, y1))
        right.resize((1900, int(1900 * right.size[1] / right.size[0]))).save(
            f"{out}/{stem}_R{k}.jpg", quality=88)

    # Street column: narrow strip at the far left, text runs vertically.
    s = im.crop((int(0.04 * w), int(0.26 * h), int(0.075 * w), h)).rotate(90, expand=True)
    sw, sh = s.size
    parts = [s.crop((int(sw * j / 2), 0, int(sw * (j + 1) / 2), sh)) for j in range(2)]
    sheet = Image.new("L", (parts[0].size[0], sh * 2 + 20), 255)
    for j, p in enumerate(parts):
        sheet.paste(p, (0, j * (sh + 20)))
    sheet.save(f"{out}/{stem}_street.jpg", quality=88)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *([town.load(sys.argv[3]).layout] if len(sys.argv) > 3 else []))
