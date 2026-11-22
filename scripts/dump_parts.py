"""Dump parts.json from the live viewer: one entry per spec component with its direct-mesh triangle count; unnamedMeshes counts meshes outside any component."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page

JS = """() => { const v = __IMG2THREEJS_VIEWER__, parts = [], seen = new Set(); let unnamed = 0;
  const tri = m => (m.geometry.index ? m.geometry.index.count : m.geometry.attributes.position.count) / 3;
  v.scene.traverse(o => { const id = o.userData?.sculptComponent?.id;
    if (o.isMesh) { if (o.name === 'shadow-catcher' || o.name === 'contact-shadows') return; if (!o.parent?.userData?.sculptComponent && !o.userData?.sculptComponent) unnamed++; return; }
    if (!id || seen.has(id)) return; seen.add(id);
    parts.push({name: id, kind: 'part', module: id, triangles: o.children.filter(m => m.isMesh).reduce((s, m) => s + tri(m), 0)}); });
  return {parts, unnamedMeshes: unnamed}; }"""
with gate_page() as page:
    d = page.evaluate(JS)
Path("parts.json").write_text(json.dumps(d, indent=1) + "\n")
print(len(d["parts"]), "parts,", d["unnamedMeshes"], "unnamed")
