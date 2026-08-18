#!/usr/bin/env python3
"""
Render a word as a pseudo-3D "extruded" terminal wordmark: many stacked
copies of the same <text>, offset by one pixel per layer along a diagonal,
darkening toward the back, with a bright front face on top and a thin
highlight edge. That stack-of-offsets trick is what makes flat SVG text
read as a solid, chunky, extruded block letter -- no image/font assets
needed, just layered text.

Usage:
    python scripts/make_wordmark_svg.py "TANISHQ"
    python scripts/make_wordmark_svg.py "TANISHQ" --out ../wordmark.svg --rock
"""
import argparse
import os

HERE = os.path.dirname(os.path.abspath(__file__))

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
FRONT = "#22d3ee"     # bright front face
EDGE_HI = "#a5f3fc"   # thin top highlight
DEPTH_DARK = "#0b3b45"  # far end of the extrusion gradient
DEPTH_LAYERS = 14
DEPTH_STEP = 1.6  # px per layer, along the diagonal

PAD = 24
TITLEBAR_H = 30
FONT_SIZE = 92
LETTER_SPACING = 6


def lerp_hex(c1, c2, t):
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def build(word, out_path, rock, handle):
    word = word.upper()
    # bold ui-monospace at this weight runs close to 0.82em per glyph advance
    text_w = len(word) * (FONT_SIZE * 0.82) + LETTER_SPACING * max(0, len(word) - 1)
    depth_w = DEPTH_LAYERS * DEPTH_STEP
    canvas_w = int(text_w + depth_w + PAD * 2 + 30)
    canvas_h = int(TITLEBAR_H + FONT_SIZE * 1.55 + PAD + depth_w)

    cx = PAD
    cy = TITLEBAR_H + PAD * 0.5 + FONT_SIZE * 0.92

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">'
    )
    parts.append(
        '<defs>'
        f'<linearGradient id="wbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient></defs>'
    )
    parts.append(f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#wbg)"/>')
    parts.append(
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>'
    )
    parts.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
        f'text-anchor="middle">{handle}@github ~$ ./wordmark.sh {"--rock" if rock else "--3d"}</text>'
    )

    group_attrs = ""
    anim = ""
    if rock:
        group_attrs = f' transform-origin="{canvas_w/2}px {cy - FONT_SIZE/3}px"'
        anim = (
            f'<animateTransform attributeName="transform" type="rotate" '
            f'values="-4;4;-4" keyTimes="0;0.5;1" dur="4.5s" '
            f'repeatCount="indefinite" additive="sum" calcMode="spline" '
            f'keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/>'
        )

    parts.append(f'<g{group_attrs}>')
    if anim:
        parts.append(anim)

    common = (
        f'font-size="{FONT_SIZE}" font-weight="800" letter-spacing="{LETTER_SPACING}" '
        f'text-anchor="start"'
    )

    # back-to-front stack builds the extrusion "side wall"
    for i in range(DEPTH_LAYERS, 0, -1):
        t = i / DEPTH_LAYERS
        color = lerp_hex(FRONT, DEPTH_DARK, t)
        off = i * DEPTH_STEP
        parts.append(
            f'<text x="{cx + off:.1f}" y="{cy + off:.1f}" fill="{color}" {common}>{word}</text>'
        )

    # front face
    parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" fill="{FRONT}" {common}>{word}</text>')
    # thin highlight riding the top edge of the front face
    parts.append(
        f'<text x="{cx:.1f}" y="{cy:.1f}" fill="none" stroke="{EDGE_HI}" '
        f'stroke-width="0.6" stroke-opacity="0.9" {common}>{word}</text>'
    )
    parts.append('</g>')
    parts.append('</svg>')

    svg = "".join(parts)
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"wrote {out_path} ({len(svg)} bytes); {canvas_w}x{canvas_h}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("word", nargs="?", default="TANISHQ")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "wordmark.svg"))
    ap.add_argument("--rock", action="store_true", help="add a subtle rocking animation")
    ap.add_argument("--handle", default="tanishq")
    args = ap.parse_args()
    build(args.word, args.out, args.rock, args.handle)
