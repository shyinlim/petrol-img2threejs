"""Default (non-gate) camera (v11): height under the soffit (4.84), elevation >= 4 deg, slab 65-90% of screen width (the panel offset leaves room on the right), fov 30. Exit 0 = pass."""
import math, subprocess, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import ensure_server, URL, ARGS
from playwright.sync_api import sync_playwright

ensure_server()
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS); page = b.new_page(viewport={"width": 1280, "height": 800})
    page.goto(URL); page.wait_for_function("window.__IMG2THREEJS_READY__ === true"); page.wait_for_timeout(800)
    r = page.evaluate("""(() => { const v = __IMG2THREEJS_VIEWER__, c = v.camera, V = c.position;
      let slab = null; v.scene.traverse(o => { if (!slab && o.isMesh && o.userData?.sculptComponent?.id === 'base-slab') slab = o; });
      slab.geometry.computeBoundingBox(); const b = slab.geometry.boundingBox; let xs = [];
      for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) {
        const q = V.clone().set(x, y, z).applyMatrix4(slab.matrixWorld).project(c); xs.push(q.x); }
      const t = v.controls.target;
      return { y: V.y, el: Math.atan2(V.y - t.y, Math.hypot(V.x - t.x, V.z - t.z)) * 180 / Math.PI, frac: (Math.max(...xs) - Math.min(...xs)) / 2, fov: c.fov }; })()""")
    b.close()
print(r)
ok = 3.5 <= r["y"] < 4.84 and r["el"] >= 4 and 0.65 <= r["frac"] <= 0.90 and r["fov"] == 30
sys.exit(0 if ok else 1)
