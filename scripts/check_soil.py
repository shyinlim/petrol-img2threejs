"""Task 6: base-slab side faces carry a canvas map; top/bottom keep the plain material."""
import sys
from _viewer import ensure_server, gate_page
ensure_server()
with gate_page() as page:
    r = page.evaluate("""() => {
      const v = window.__IMG2THREEJS_VIEWER__; let m = null;
      v.scene.traverse(o => { if (o.isMesh && o.userData?.sculptComponent?.id === 'base-slab') m = o; });
      const mats = Array.isArray(m.material) ? m.material : [m.material];
      const g = (m.geometry.groups.length ? m.geometry.groups : [{materialIndex: 0, start: 0, count: 0}]).map(x => ({i: x.materialIndex, mapped: !!(mats[x.materialIndex ?? 0] ?? mats[0]).map, start: x.start, count: x.count}));
      return {n: mats.length, g};
    }""")
print(r)
mapped = [x for x in r['g'] if x['mapped']]
ok = len(mapped) >= 1 and len(r['g']) >= 2 and any(not x['mapped'] for x in r['g'])
print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
