"""Max draw calls over 12 angles (gate and normal mode) + triangles + parts piercing the canopy. Writes shots/v8_scene.json. Budget comes from the spec (performanceBudget); normal mode (shadows on) may use 2x the gate draw calls. Exit 0 = within budget and no piercing."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page, set_camera, ANGLES

SOFFIT_BOTTOM = 4.84
# World AABB of the meshes under `o` (optionally direct children only), built from geometry boxes; no THREE global needed.
JS = """({direct}) => {
  const v = __IMG2THREEJS_VIEWER__, V = v.camera.position;
  const isPart = o => o.userData?.sculptComponent && !o.isMesh;
  const bbox = (o, onlyDirect) => {
    let mn = [1e9,1e9,1e9], mx = [-1e9,-1e9,-1e9];
    const visit = m => {
      if (!m.isMesh) return;
      m.updateWorldMatrix(true, false); m.geometry.computeBoundingBox();
      const b = m.geometry.boundingBox;
      for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) {
        const p = V.clone().set(x, y, z).applyMatrix4(m.matrixWorld);
        mn = [Math.min(mn[0],p.x),Math.min(mn[1],p.y),Math.min(mn[2],p.z)]; mx = [Math.max(mx[0],p.x),Math.max(mx[1],p.y),Math.max(mx[2],p.z)];
      }
    };
    if (onlyDirect) o.children.forEach(visit); else o.traverse(visit);
    return [mn, mx];
  };
  let canopy = null, parts = [];
  v.scene.traverse(o => { if (isPart(o)) { parts.push(o); if (!canopy && o.userData.sculptComponent.id === 'canopy') canopy = o; } });
  const cb = bbox(canopy, true);
  const inCanopy = o => { for (let n = o; n; n = n.parent) if (n === canopy) return true; return false; };
  const piercing = [];
  for (const o of parts) {
    if (inCanopy(o) || o.userData.sculptComponent.id === 'root') continue;
    const b = bbox(o, false);
    if (b[1][1] > %s && b[0][0] < cb[1][0] && b[1][0] > cb[0][0] && b[0][2] < cb[1][2] && b[1][2] > cb[0][2]) piercing.push(o.userData.sculptComponent.id);
  }
  return { piercing, canopy: cb };
}""" % SOFFIT_BOTTOM

budget = json.loads((Path(__file__).resolve().parent.parent / "object-sculpt-spec.json").read_text())["performanceBudget"]
LIMIT, TRIS = budget["maxDrawCalls"], budget["targetTriangles"]
calls = {}
with gate_page() as page:
    for n, cam in ANGLES.items():
        set_camera(page, cam)
        calls[n] = page.evaluate("__IMG2THREEJS_VIEWER__.renderer.info.render.calls")
    res = page.evaluate(JS, {"direct": True})
    page.evaluate("(() => { const v = __IMG2THREEJS_VIEWER__; v.renderer.render(v.scene, v.camera); })()")
    tris = page.evaluate("__IMG2THREEJS_VIEWER__.renderer.info.render.triangles")
ncalls = {}
with gate_page("") as page:
    for n, cam in ANGLES.items():
        set_camera(page, cam)
        ncalls[n] = page.evaluate("__IMG2THREEJS_VIEWER__.renderer.info.render.calls")
r = {"drawCallsMax": max(calls.values()), "drawCallsByAngle": calls, "drawCallsNormalMax": max(ncalls.values()), "drawCallsNormalByAngle": ncalls,
     "triangles": tris, "piercing": res["piercing"], "canopyBox": res["canopy"]}
Path("shots").mkdir(exist_ok=True)
Path("shots/v8_scene.json").write_text(json.dumps(r, indent=1))
print(json.dumps({k: r[k] for k in ("drawCallsMax", "drawCallsNormalMax", "triangles", "piercing")}), f"limits: gate {LIMIT}, normal {2 * LIMIT}, triangles {TRIS}")
sys.exit(0 if r["drawCallsMax"] <= LIMIT and r["drawCallsNormalMax"] <= 2 * LIMIT and tris <= TRIS and not r["piercing"] else 1)
