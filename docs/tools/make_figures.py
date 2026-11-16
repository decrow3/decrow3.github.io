"""Generate the site's computed schematics as inline-SVG includes.

Everything here is an illustrative schematic: nothing is measured data or a
fitted model.

* hero_v1v2.html   image -> V1 -> V2 stack. The "V1" layer is a grid of sites
                   with fixed preferred orientations taken from a toy
                   orientation map (a sum of random plane waves). A site
                   responds when the drawn object's edge passes over it at a
                   matching orientation. "V2" units average V1 drive over a
                   larger region. docs/source/_static/hero.js re-applies the
                   same formulas in the browser to animate it.
* tile_maps.html   textbook complex-log retinotopic mesh.
* tile_active.html grating with a random-walk "eye trace".
* tile_running.html concentric eccentricity rings.

Usage:  python docs/tools/make_figures.py
"""
import json
import random
from math import atan2, cos, degrees, exp, hypot, log, pi, radians, sin, sqrt
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "source" / "_includes" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------
W, H = 460, 590
CX, KX, KY = 230, 1.0, 0.5                  # isometric projection of a 200 x 200 plane
TY = {"v2": 20, "v1": 195, "img": 370}
N = 18                                       # V1 sites per side
STIM = {"a": 60.0, "b": 38.0, "sigma": 7.5}  # object semi-axes, edge falloff
START = (100.0, 100.0, 0.6)                  # object centre and rotation (static state)
V2_SIGMA, V2_GAIN = 15.0, 3.2

rng = random.Random(11)
WAVES = [(rng.uniform(0, 2 * pi), rng.uniform(0, 2 * pi)) for _ in range(16)]
K = 2 * pi / 58.0


def preferred(x, y):
    re = sum(cos(K * (x * cos(a) + y * sin(a)) + p) for a, p in WAVES)
    im = sum(sin(K * (x * cos(a) + y * sin(a)) + p) for a, p in WAVES)
    return 0.5 * atan2(im, re)


def drive(x, y, theta, cx, cy, psi):
    """Response of a V1 site: edge proximity x orientation match."""
    dx, dy = x - cx, y - cy
    u = dx * cos(psi) + dy * sin(psi)
    v = -dx * sin(psi) + dy * cos(psi)
    f = sqrt((u / STIM["a"]) ** 2 + (v / STIM["b"]) ** 2)
    if f < 1e-6:
        return 0.0
    gu, gv = u / STIM["a"] ** 2 / f, v / STIM["b"] ** 2 / f
    g = hypot(gu, gv)
    dist = (f - 1) / g
    tangent = atan2(gv, gu) + psi + pi / 2
    return exp(-dist * dist / (2 * STIM["sigma"] ** 2)) * cos(theta - tangent) ** 2


def iso(x, y, level):
    return CX + (x - y) * KX, TY[level] + (x + y) * KY


def plane(level, inner):
    return f'<g transform="matrix({KX},{KY},{-KX},{KY},{CX},{TY[level]})">{inner}</g>'


def slab(level):
    grid = "".join(
        f'<path d="M{v} 0V200M0 {v}H200"/>' for v in (40, 80, 120, 160)
    )
    edge = plane(level, '<rect class="hero-slab-edge" width="200" height="200" rx="10"/>')
    top = plane(level, f'<rect class="hero-slab" width="200" height="200" rx="10"/><g class="hero-grid">{grid}</g>')
    return f'<g transform="translate(0,8)">{edge}</g>{top}'


def cone(src_level, centre, radius, dst_level, target):
    """Receptive field outline on the lower layer, joined to a unit above."""
    cx, cy = centre
    d = radius * 0.7071
    tx, ty = iso(*target, dst_level)
    lines = ""
    for px, py in ((cx - d, cy + d), (cx + d, cy - d)):
        sx, sy = iso(px, py, src_level)
        lines += f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}"/>'
    return (
        plane(src_level, f'<circle class="hero-rf" cx="{cx}" cy="{cy}" r="{radius}"/>')
        + f'<g class="hero-cone">{lines}</g>'
    )


def label(level, title, sub):
    y = TY[level] + 16
    return (
        f'<text class="hero-label" x="2" y="{y}">{title}</text>'
        f'<text class="hero-sublabel" x="2" y="{y + 16}">{sub}</text>'
    )


def hue(theta):
    return (2 * degrees(theta)) % 360


def hero():
    cx0, cy0, psi0 = START
    step = 200 / N
    sites = []
    for i in range(N):
        for j in range(N):
            x, y = step * (i + 0.5), step * (j + 0.5)
            sites.append((x, y, preferred(x, y)))
    drives = [drive(x, y, t, cx0, cy0, psi0) for x, y, t in sites]

    parts = []

    # visual input
    parts.append(slab("img"))
    parts.append(plane(
        "img",
        f'<ellipse id="hero-stim" class="hero-object" cx="{cx0}" cy="{cy0}" rx="{STIM["a"]:.0f}" '
        f'ry="{STIM["b"]:.0f}" transform="rotate({degrees(psi0):.1f} {cx0} {cy0})"/>',
    ))

    # V1
    v1_site = (61.1, 138.9)                  # a grid site: centre of cell (5, 12)
    parts.append(slab("v1"))
    parts.append(cone("img", v1_site, 9, "v1", v1_site))
    bars = []
    for (x, y, t), d in zip(sites, drives):
        dx, dy = 3.7 * cos(t), 3.7 * sin(t)
        bars.append(
            f'<line data-p="{x:.2f},{y:.2f},{t:.4f}" x1="{x - dx:.1f}" y1="{y - dy:.1f}" '
            f'x2="{x + dx:.1f}" y2="{y + dy:.1f}" stroke="hsl({hue(t):.0f} 92% 64%)" '
            f'stroke-opacity="{0.13 + 0.87 * d:.2f}"/>'
        )
    parts.append(plane("v1", f'<g class="hero-bars">{"".join(bars)}</g>'))
    parts.append(plane("v1", f'<circle class="hero-site" cx="{v1_site[0]}" cy="{v1_site[1]}" r="7"/>'))

    # V2
    v2_target = (140, 60)
    parts.append(slab("v2"))
    parts.append(cone("v1", v2_target, 26, "v2", v2_target))
    units = []
    for i in range(5):
        for j in range(5):
            x, y = 20 + 40 * i, 20 + 40 * j
            num = den = 0.0
            for (sx, sy, _), d in zip(sites, drives):
                w = exp(-((sx - x) ** 2 + (sy - y) ** 2) / (2 * V2_SIGMA**2))
                num += w * d
                den += w
            a = min(1.0, V2_GAIN * num / den)
            cls = "hero-unit hero-unit--target" if (x, y) == v2_target else "hero-unit"
            units.append(
                f'<circle class="{cls}" data-p="{x},{y}" cx="{x}" cy="{y}" r="14" '
                f'fill-opacity="{0.05 + 0.9 * a:.2f}"/>'
            )
    parts.append(plane("v2", "".join(units)))

    sx, sy = iso(*v2_target, "v1")
    tx, ty = iso(*v2_target, "v2")
    bx, by = (sx + tx) / 2, (sy + ty) / 2 + 14
    parts.append(
        f'<g class="hero-badge"><circle cx="{bx:.1f}" cy="{by:.1f}" r="13"/>'
        f'<text x="{bx:.1f}" y="{by + 5.5:.1f}" text-anchor="middle">?</text></g>'
    )

    parts.append(label("v2", "V2", "larger receptive fields"))
    parts.append(label("v1", "V1", "preferred orientation"))
    parts.append(label("img", "Visual input", "an object's outline"))

    # orientation key under the V1 label
    key = ""
    for n, deg in enumerate((0, 45, 90, 135)):
        t = radians(deg)
        kx, ky = 9 + 17 * n, TY["v1"] + 50
        key += (
            f'<line x1="{kx - 6 * cos(t):.1f}" y1="{ky + 6 * sin(t):.1f}" x2="{kx + 6 * cos(t):.1f}" '
            f'y2="{ky - 6 * sin(t):.1f}" stroke="hsl({(2 * deg) % 360} 92% 64%)"/>'
        )
    parts.append(f'<g class="hero-key">{key}</g>')

    cfg = {"cx": CX, "kx": KX, "ky": KY, "ty": TY, "stim": STIM,
           "start": START, "v2Sigma": V2_SIGMA, "v2Gain": V2_GAIN}
    svg = (
        f"<svg viewBox=\"0 0 {W} {H}\" role=\"img\" aria-labelledby=\"hero-fig-title\" data-cfg='{json.dumps(cfg)}'>"
        '<title id="hero-fig-title">Schematic of three stacked layers. An object in the visual input drives '
        'V1 sites whose preferred orientation matches its edge. V2 units cover larger regions of V1. '
        'A question mark sits on the projection from V1 to V2.</title>'
        + "".join(parts) + "</svg>"
    )
    html = f"""<!-- Generated by docs/tools/make_figures.py. Illustrative schematic, not data. -->
<figure class="hero-figure">
{svg}
<figcaption><span class="fig-kind">Illustrative schematic</span> Each V1 site has a fixed preferred orientation (color) and responds when the object's edge matches it. V2 neurons draw on larger regions of V1. How that circuit transforms the signal is the open question. <span class="hero-hint">Move your pointer over a layer to move the object.</span></figcaption>
</figure>
"""
    (OUT / "hero_v1v2.html").write_text(html, encoding="utf-8")


# --------------------------------------------------------------------------
# Contribution tiles (decorative, 200 x 150)
# --------------------------------------------------------------------------
def tile(name, inner):
    html = (
        "<!-- Generated by docs/tools/make_figures.py. Decorative schematic, not data. -->\n"
        '<div class="tile" aria-hidden="true">\n'
        f'<svg viewBox="0 0 200 150" focusable="false">{inner}</svg>\n</div>\n'
    )
    (OUT / name).write_text(html, encoding="utf-8")


def path(points):
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in points)


def tile_maps():
    """Complex-log mapping of one visual hemifield: w = log(z + a)."""
    a, r_max = 1.0, 40.0
    lo, hi = log(a), log(r_max + a)

    def project(r, phi):
        re = 0.5 * log((r * cos(phi) + a) ** 2 + (r * sin(phi)) ** 2)
        im = atan2(r * sin(phi), r * cos(phi) + a)
        return 16 + (re - lo) / (hi - lo) * 168, 75 - im * 41

    out = ""
    for r in (0.6, 1.5, 3, 6, 12, 22, 40):
        pts = [project(r, radians(p)) for p in range(-90, 91, 3)]
        out += f'<path class="tile-ecc" d="{path(pts)}"/>'
    for n, deg in enumerate(range(-90, 91, 15)):
        pts = [project(r_max * (s / 60) ** 2.2, radians(deg)) for s in range(0, 61)]
        out += f'<path d="{path(pts)}" stroke="hsl({20 + n * 25} 90% 64%)"/>'
    tile("tile_maps.html", f'<g class="tile-lines">{out}</g>')


def tile_active():
    r = random.Random(4)
    x, y = 62.0, 96.0
    pts = [(x, y)]
    for n in range(70):
        if n in (24, 50):                       # two larger jumps among the drift
            x += r.uniform(16, 22)
            y -= r.uniform(10, 16)
        else:
            x += r.gauss(0.55, 1.7)
            y += r.gauss(-0.25, 1.7)
        pts.append((x, y))
    inner = (
        "<defs>"
        '<pattern id="tile-act-stripes" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">'
        '<rect class="tile-ink" width="7" height="14"/></pattern>'
        '<radialGradient id="tile-act-fade"><stop offset="0.25" stop-color="#fff"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        '<mask id="tile-act-mask"><circle cx="100" cy="75" r="62" fill="url(#tile-act-fade)"/></mask>'
        "</defs>"
        '<circle cx="100" cy="75" r="62" fill="url(#tile-act-stripes)" mask="url(#tile-act-mask)" opacity="0.8"/>'
        f'<path class="tile-trace" d="{path(pts)}"/>'
        f'<circle class="tile-dot" cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3.6"/>'
    )
    tile("tile_active.html", inner)


def tile_running():
    rings = ""
    for radius, opacity, width in ((14, 0.16, 3), (27, 0.3, 4), (40, 0.5, 5), (53, 0.74, 6), (66, 1.0, 7)):
        rings += f'<circle cx="100" cy="75" r="{radius}" stroke-opacity="{opacity}" stroke-width="{width}"/>'
    inner = (
        '<defs><clipPath id="tile-run-clip"><rect width="200" height="150" rx="10"/></clipPath></defs>'
        f'<g class="tile-rings" clip-path="url(#tile-run-clip)">{rings}</g>'
        '<circle class="tile-dot" cx="100" cy="75" r="3.6"/>'
    )
    tile("tile_running.html", inner)


hero()
tile_maps()
tile_active()
tile_running()
print(f"wrote figures to {OUT}")
