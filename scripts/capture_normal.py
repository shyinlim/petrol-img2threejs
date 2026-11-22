"""python3 scripts/capture_normal.py <out.png>: normal-mode screenshot at the v3 angle + CIE76 dE of three colours vs v3.
Exit 0 = all dE <= 10. Targets (sampled from v3.webp, 2026-11-22): canopy front #ED1B2F, ground #E7E2DC, background #E8D4C5."""
import sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page, set_camera
from _geom import boxes

V3 = dict(azimuth=-51, elevation=9.5, distance=30, fov=30, target=[0, 1.5, 0])
TARGETS = {"canopy": "#ED1B2F", "ground": "#E7E2DC", "background": "#E8D4C5"}
MAX_DE = 10
PROJECT = """p => { const v = __IMG2THREEJS_VIEWER__, q = v.camera.position.clone().set(...p).project(v.camera);
  const r = v.renderer.domElement.getBoundingClientRect(); return [r.left + (q.x + 1) / 2 * r.width, r.top + (1 - q.y) / 2 * r.height]; }"""


def lab(rgb):  # copied from color_check.py (that file runs its main code on import)
    def lin(c): c /= 255; return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(lin, rgb)
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b, (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def avg9(im, x, y):
    px = [im.getpixel((int(x) + dx, int(y) + dy)) for dx in range(-4, 5) for dy in range(-4, 5)]
    return tuple(sum(c[i] for c in px) / len(px) for i in range(3))


def main(out):
    with gate_page("", viewport=(1280, 800)) as page:
        set_camera(page, V3); page.wait_for_timeout(1000)
        cb = boxes(page, ["canopy"])["canopy"]
        pts = {"canopy": [cb[0][0] - 0.01, (cb[0][1] + cb[1][1]) / 2, -3.0], "ground": [-7.8, 0.17, 8.6]}
        xy = {k: page.evaluate(PROJECT, p) for k, p in pts.items()}
        xy["background"] = [640, 30]
        page.screenshot(path=out)
    im = Image.open(out).convert("RGB"); bad = []
    for k, (x, y) in xy.items():
        rgb = avg9(im, x, y); t = tuple(int(TARGETS[k][i:i + 2], 16) for i in (1, 3, 5))
        de = sum((a - b) ** 2 for a, b in zip(lab(rgb), lab(t))) ** 0.5
        print(f"{k}: px ({x:.0f},{y:.0f}) rgb {tuple(round(c) for c in rgb)} target {TARGETS[k]} dE {de:.1f}")
        if de > MAX_DE: bad.append(k)
    print("capture_normal", "FAIL " + ",".join(bad) if bad else "OK")
    sys.exit(1 if bad else 0)


main(sys.argv[1])
