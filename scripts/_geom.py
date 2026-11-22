"""World AABBs of spec components (union of each component's direct meshes), read from the live viewer."""
JS = """ids => { const v = __IMG2THREEJS_VIEWER__, V = v.camera.position, out = {};
  v.scene.traverse(o => { const id = o.userData?.sculptComponent?.id;
    if (!id || o.isMesh || out[id]) return;
    let mn = [1e9,1e9,1e9], mx = [-1e9,-1e9,-1e9], n = 0;
    o.children.forEach(m => { if (!m.isMesh) return; n++;
      m.updateWorldMatrix(true, false); m.geometry.computeBoundingBox(); const b = m.geometry.boundingBox;
      for (const x of [b.min.x,b.max.x]) for (const y of [b.min.y,b.max.y]) for (const z of [b.min.z,b.max.z]) {
        const p = V.clone().set(x,y,z).applyMatrix4(m.matrixWorld), a = [p.x,p.y,p.z];
        mn = mn.map((c,i) => Math.min(c,a[i])); mx = mx.map((c,i) => Math.max(c,a[i])); } });
    if (n) out[id] = {min: mn, max: mx}; });
  return out; }"""


def boxes(page, ids=None):
    """{id: (min[3], max[3])} for every component with meshes (ids=None means all)."""
    r = page.evaluate(JS, ids)
    return {k: (v["min"], v["max"]) for k, v in r.items() if ids is None or k in ids}


SCREEN_JS = """ids => { const v = __IMG2THREEJS_VIEWER__, c = v.camera, V = c.position, out = {};
  const r = v.renderer.domElement.getBoundingClientRect();
  v.scene.traverse(o => { const id = o.userData?.sculptComponent?.id;
    if (!id || o.isMesh || out[id] || (ids && !ids.includes(id))) return;
    let xs = [], ys = [];
    o.children.forEach(m => { if (!m.isMesh) return; m.updateWorldMatrix(true, false); m.geometry.computeBoundingBox(); const b = m.geometry.boundingBox;
      for (const x of [b.min.x,b.max.x]) for (const y of [b.min.y,b.max.y]) for (const z of [b.min.z,b.max.z]) {
        const q = V.clone().set(x,y,z).applyMatrix4(m.matrixWorld).project(c);
        xs.push(r.left + (q.x + 1) / 2 * r.width); ys.push(r.top + (1 - q.y) / 2 * r.height); } });
    if (xs.length) out[id] = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]; });
  return out; }"""


def screen_boxes(page, ids=None):
    """{id: (x0, y0, x1, y1)} CSS-pixel bbox of each component's projected (oriented) mesh boxes."""
    return {k: tuple(v) for k, v in page.evaluate(SCREEN_JS, ids).items()}
