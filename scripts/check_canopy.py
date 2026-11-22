"""Roundel sits next to CALTEX and above the roof, fascia lips exist, roundel does not cut the roof corner. Exit 0 = pass."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page
from _geom import boxes

# Corner point in the roundel mesh's local frame: worldToLocal handles the 45-degree tilt; a world AABB of a tilted disc always contains the corner.
CORNER_JS = """([c]) => { const v = __IMG2THREEJS_VIEWER__; let out = null;
  v.scene.traverse(o => { if (out || o.userData?.sculptComponent?.id !== 'roundel-logo' || o.isMesh) return;
    const m = o.children.find(k => k.isMesh); m.updateWorldMatrix(true, false);
    const p = m.worldToLocal(v.camera.position.clone().set(c[0], c[1], c[2]));
    m.geometry.computeBoundingBox(); const b = m.geometry.boundingBox;
    out = { radial: Math.hypot(p.x, p.z), axial: p.y, r: (b.max.x - b.min.x) / 2, h: (b.max.y - b.min.y) / 2 }; });
  return out; }"""

with gate_page() as page:
    bx = boxes(page)
    cn = bx["canopy"]
    corner = [cn[0][0], (cn[0][1] + cn[1][1]) / 2, cn[1][2]]
    c = page.evaluate(CORNER_JS, [corner])
bad = []
rd, wm = bx["roundel-logo"], bx["canopy-wordmark"]
gap = rd[0][2] - wm[1][2]
if gap > 1.6: bad.append(f"1 roundel-wordmark gap {gap:.2f} > 1.6")
if rd[1][1] - cn[1][1] < 0.5: bad.append(f"2 roundel top {rd[1][1]:.2f} not >= roof top {cn[1][1]:.2f} + 0.5")
for lip in ("fascia-lip-top", "fascia-lip-end"):
    if lip not in bx: bad.append(f"3 {lip} missing"); continue
    lb = bx[lip]
    if not lb[0][0] < cn[0][0]: bad.append(f"3 {lip} min x {lb[0][0]:.2f} not in front of canopy {cn[0][0]:.2f}")
    if all(lb[0][k] < wm[1][k] and wm[0][k] < lb[1][k] for k in range(3)): bad.append(f"3 {lip} overlaps wordmark")
# signed: the corner must sit behind the disc's back face (axial < -h); a disc pushed into the roof gives axial > -h
if c and c["radial"] <= c["r"] and c["axial"] > -c["h"]: bad.append(f"4 roof corner not behind roundel (radial {c['radial']:.2f}, axial {c['axial']:.2f}, h {c['h']:.2f})")
print("canopy", "FAIL" if bad else "OK", *bad, sep="\n  " if bad else " ")
sys.exit(1 if bad else 0)
