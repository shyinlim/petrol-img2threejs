"""python3 scripts/color_check.py <render.png>: pump orange in v3 vs the render (CIE76 dE <= 12).
Reference crop (470,380)-(560,465) of reference/diorama.png; render crop = projected bbox of pump-1 in the ?gate=1 reference view.
Both sides keep pixels with H 0-25 deg, S > 0.45, V > 0.35 and take the per-channel median."""
import colorsys, statistics, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page

def median_orange(im):
    px = []
    for r, g, b in im.convert("RGB").getdata():
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if h * 360 <= 25 and s > 0.45 and v > 0.35: px.append((r, g, b))
    if not px: sys.exit("no orange pixels in crop")
    return tuple(statistics.median(c[i] for c in px) for i in range(3)), len(px)

def lab(rgb):
    def lin(c): c /= 255; return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(lin, rgb)
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b, (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))

render = Image.open(sys.argv[1]).convert("RGB")
with gate_page() as page:
    bb = page.evaluate("""(() => { const v = __IMG2THREEJS_VIEWER__, c = v.camera, V = c.position; let n = null;
      v.scene.traverse(o => { if (!n && o.userData?.sculptComponent?.id === 'pump-1' && !o.isMesh) n = o; });
      let xs = [], ys = [];
      n.traverse(m => { if (!m.isMesh) return; m.geometry.computeBoundingBox(); const b = m.geometry.boundingBox;
        for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) {
          const q = V.clone().set(x, y, z).applyMatrix4(m.matrixWorld).project(c); xs.push((q.x + 1) / 2 * 1024); ys.push((1 - q.y) / 2 * 687); } });
      return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]; })()""")
ref_rgb, n1 = median_orange(Image.open("reference/diorama.png").crop((470, 380, 560, 465)))
ren_rgb, n2 = median_orange(render.crop(tuple(int(round(v)) for v in bb)))
l1, l2 = lab(ref_rgb), lab(ren_rgb)
de = sum((a - b) ** 2 for a, b in zip(l1, l2)) ** 0.5
print(f"ref rgb {ref_rgb} ({n1}px)  render rgb {ren_rgb} ({n2}px)  dE76 {de:.1f}")
sys.exit(0 if de <= 12 else 1)
