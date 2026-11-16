"""Generate the homepage hero schematic (image -> V1 -> V2) as inline SVG.

Illustrative schematic only: nothing here is measured data or a fitted model.
The "V1" layer is the tangent orientation of a drawn circle, and the "V2"
layer is a plain local average of it.

Usage:  python docs/tools/make_hero_figure.py
Writes: docs/source/_includes/figures/hero_v1v2.html
"""
from math import atan2, cos, degrees, exp, hypot, pi, sin
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "source" / "_includes" / "figures" / "hero_v1v2.html"

W, H = 400, 550
CX = 200
KX, KY = 0.866, 0.45          # isometric projection of a 200 x 200 plane
TY = {"v2": 20, "v1": 185, "img": 350}
R0, SIGMA = 62.0, 13.0        # stimulus circle radius, V1 response falloff


def iso(x, y, level):
    return CX + (x - y) * KX, TY[level] + (x + y) * KY


def plane_open(level):
    return f'<g transform="matrix({KX},{KY},{-KX},{KY},{CX},{TY[level]})">'


def strength(x, y):
    r = hypot(x - 100, y - 100)
    return exp(-((r - R0) ** 2) / (2 * SIGMA**2))


def slab(level):
    """Plane with a thin visible edge so the layers read as stacked sheets."""
    return (
        f'<g transform="translate(0,7)">{plane_open(level)}'
        '<rect class="hero-slab-edge" width="200" height="200" rx="12"/></g></g>'
        f'{plane_open(level)}<rect class="hero-slab" width="200" height="200" rx="12"/></g>'
    )


def cone(src_level, patch, dst_level, target):
    """Lines from the corners of a source patch to one unit in the next layer."""
    x0, y0, x1, y1 = patch
    tx, ty = iso(*target, dst_level)
    out = []
    for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        sx, sy = iso(px, py, src_level)
        out.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}"/>')
    return '<g class="hero-cone">' + "".join(out) + "</g>"


def patch_outline(level, patch):
    x0, y0, x1, y1 = patch
    return (
        f'{plane_open(level)}<rect class="hero-patch" x="{x0}" y="{y0}" '
        f'width="{x1 - x0}" height="{y1 - y0}" rx="3"/></g>'
    )


def label(level, title, sub):
    y = TY[level] + 14
    return (
        f'<text class="hero-label" x="4" y="{y}">{title}</text>'
        f'<text class="hero-sublabel" x="4" y="{y + 15}">{sub}</text>'
    )


parts = []

# --- visual input -----------------------------------------------------------
parts.append(slab("img"))
parts.append(f'{plane_open("img")}<circle class="hero-object" cx="100" cy="100" r="{R0:.0f}"/></g>')
img_patch = (140, 120, 160, 140)
parts.append(patch_outline("img", img_patch))

# --- V1: local orientation --------------------------------------------------
parts.append(slab("v1"))
parts.append(cone("img", img_patch, "v1", (150, 130)))
bars = []
for i in range(10):
    for j in range(10):
        x, y = 10 + 20 * i, 10 + 20 * j
        s = strength(x, y)
        theta = atan2(y - 100, x - 100) + pi / 2      # tangent to the circle
        dx, dy = 6.5 * cos(theta), 6.5 * sin(theta)
        if s < 0.12:
            bars.append(f'<circle class="hero-idle" cx="{x}" cy="{y}" r="1.6"/>')
            continue
        hue = (2 * degrees(theta)) % 360
        bars.append(
            f'<line x1="{x - dx:.1f}" y1="{y - dy:.1f}" x2="{x + dx:.1f}" y2="{y + dy:.1f}" '
            f'stroke="hsl({hue:.0f} 68% 50%)" stroke-opacity="{0.25 + 0.75 * s:.2f}"/>'
        )
parts.append(f'{plane_open("v1")}<g class="hero-bars">{"".join(bars)}</g></g>')
v1_patch = (40, 120, 80, 160)
parts.append(patch_outline("v1", v1_patch))

# --- V2: larger receptive fields --------------------------------------------
parts.append(slab("v2"))
v2_target = (60, 140)
parts.append(cone("v1", v1_patch, "v2", v2_target))
units = []
for i in range(5):
    for j in range(5):
        x, y = 20 + 40 * i, 20 + 40 * j
        a = sum(strength(x + ox, y + oy) for ox in (-10, 10) for oy in (-10, 10)) / 4
        cls = "hero-unit hero-unit--target" if (x, y) == v2_target else "hero-unit"
        units.append(f'<circle class="{cls}" cx="{x}" cy="{y}" r="14" fill-opacity="{0.06 + 0.8 * a:.2f}"/>')
parts.append(f'{plane_open("v2")}{"".join(units)}</g>')

# "?" badge on the V1 -> V2 projection
sx, sy = iso(60, 140, "v1")
tx, ty = iso(*v2_target, "v2")
bx, by = (sx + tx) / 2, (sy + ty) / 2 + 12
parts.append(
    f'<g class="hero-badge"><circle cx="{bx:.1f}" cy="{by:.1f}" r="12"/>'
    f'<text x="{bx:.1f}" y="{by + 5:.1f}" text-anchor="middle">?</text></g>'
)

parts.append(label("v2", "V2", "larger receptive fields"))
parts.append(label("v1", "V1", "local orientation"))
parts.append(label("img", "Visual input", "an object's outline"))

svg = (
    f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="hero-fig-title">'
    '<title id="hero-fig-title">Schematic of three stacked layers: a visual input, '
    'V1 neurons signalling local orientation, and V2 neurons with larger receptive fields. '
    'A question mark sits on the projection from V1 to V2.</title>'
    + "".join(parts)
    + "</svg>"
)

html = f"""<!-- Generated by docs/tools/make_hero_figure.py. Illustrative schematic, not data. -->
<figure class="hero-figure">
{svg}
<figcaption><span class="fig-kind">Illustrative schematic</span> The same image is represented differently at each stage. Color marks preferred orientation in V1. How the circuit between V1 and V2 transforms that representation is the open question.</figcaption>
</figure>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT}")
