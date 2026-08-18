#!/usr/bin/env python3
"""
Convert a photo into a monochrome ASCII-art SVG that "types" itself in like
a terminal, then holds. One fill color + a density ramp + a hard white-point
cutoff (so backgrounds wash out to blank) reads as clean rather than noisy.

GitHub renders SVGs embedded via <img> and plays their SMIL animation there.
Each row reveals with a left-to-right clip wipe plus a small block cursor
riding the wipe edge, staggered top -> bottom.

Usage:
    python scripts/make_ascii_svg.py path/to/photo.jpg
    python scripts/make_ascii_svg.py path/to/photo.jpg ../portrait.svg
"""
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

SRC = sys.argv[1] if len(sys.argv) > 1 else None
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "portrait.svg")
HANDLE = sys.argv[3] if len(sys.argv) > 3 else "tanishq"
DISPLAY_NAME = sys.argv[4] if len(sys.argv) > 4 else "Tanishq"

if not SRC:
    print("usage: make_ascii_svg.py <photo> [out.svg] [handle] [display name]", file=sys.stderr)
    sys.exit(1)

COLS = 100
ROWS = 53
CELL_W = 8
CELL_H = 15
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense); leading space clears bg

CONTRAST = 1.0
BRIGHTNESS = 1.0
GAMMA = 1.15  # >1 brightens mids (applied as lum**(1/GAMMA) below) -> face lands in sparser chars
WHITE_FLOOR = 0.86  # luminance above this is forced to blank (space)

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30

ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

ROW_DUR = 0.11
STAGGER = 0.11

im = Image.open(SRC).convert("L")

# center-crop to the grid's aspect ratio first so a portrait (or landscape)
# photo doesn't get squashed when it's resized down to COLS x ROWS
target_ratio = ART_W / ART_H
w, h = im.size
cur_ratio = w / h
if cur_ratio > target_ratio:
    new_w = int(h * target_ratio)
    x0 = (w - new_w) // 2
    im = im.crop((x0, 0, x0 + new_w, h))
else:
    new_h = int(w / target_ratio)
    # bias the crop upward a bit so hair/face aren't cut before the chin is
    y0 = max(0, int((h - new_h) * 0.35))
    im = im.crop((0, y0, w, y0 + new_h))

im = ImageOps.autocontrast(im, cutoff=2)
im = im.filter(ImageFilter.UnsharpMask(radius=6, percent=160, threshold=2))
im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
im = ImageEnhance.Contrast(im).enhance(CONTRAST)
im = im.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = px[x, y] / 255.0
        lum = pow(lum, 1.0 / GAMMA)
        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue
        idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        idx = max(0, min(len(RAMP) - 1, idx))
        chars.append(RAMP[idx])
    rows_txt.append("".join(chars))

art_top = TITLEBAR_H + PAD * 0.35

parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
    f'Menlo, Consolas, monospace">'
)
parts.append(
    '<defs>'
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    f'</linearGradient></defs>'
)
parts.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>')
parts.append(
    f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
    f'fill="none" stroke="{FRAME}" stroke-width="1"/>'
)
parts.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(
    f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
    f'text-anchor="middle">{HANDLE}@github: ~$ ./portrait.sh</text>'
)

font_size = CELL_H * 0.86
for ry, line in enumerate(rows_txt):
    y = art_top + ry * CELL_H + CELL_H * 0.74
    row_y = art_top + ry * CELL_H
    delay = ry * STAGGER
    safe = html.escape(line)
    text = (
        f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
        f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>'
    )
    parts.append(
        f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    parts.append(
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
    )

status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
parts.append(
    f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
    f'{HANDLE}@github:~$ whoami <tspan fill="{INK}">{html.escape(DISPLAY_NAME)}</tspan></text>'
)
cursor_x = PAD + 9 * 8 + len(DISPLAY_NAME) * 8 + 12
parts.append(
    f'<rect x="{cursor_x}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
    f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
    f'dur="1s" repeatCount="indefinite"/></rect>'
)
parts.append("</svg>")

svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H)
