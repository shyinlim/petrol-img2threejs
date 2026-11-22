"""Pump islands, wheel stops, columns and pump children must not sink into concrete-top (top y 0.16)."""
import sys
from _viewer import gate_page
with gate_page() as page:
    r = page.evaluate("""() => {
      const v = window.__IMG2THREEJS_VIEWER__, out = {}; v.scene.updateMatrixWorld(true);
      v.scene.traverse(o => { const id = o.userData?.sculptComponent?.id;
        if (!o.isMesh || !id || !/^(pump-island|wheel-stop|pump-\\d|pump-cabinet|pump-poster)/.test(id)) return;
        o.geometry.computeBoundingBox(); const b = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
        out[id] = [+b.min.y.toFixed(3), +b.max.y.toFixed(3)]; });
      return out; }""")
bad = {k: v for k, v in r.items() if v[0] < 0.15}
print(r); print('buried:', bad); print('FAIL' if bad else 'PASS'); sys.exit(1 if bad else 0)
