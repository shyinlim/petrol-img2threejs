"""Final-review fixes: (1) right-drag pan cannot put the camera under the ground; (2) roundel back cap is drawn, not hidden."""
import sys
from _viewer import gate_page
fails = []
with gate_page("") as page:
    page.mouse.move(512, 343); page.mouse.down(button="right"); page.mouse.move(512, 343 - 800, steps=20); page.mouse.up(button="right")
    page.wait_for_timeout(3000)
    y = page.evaluate("__IMG2THREEJS_VIEWER__.camera.position.y")
    print("camera y after right-drag pan:", y)
    if y < 0: fails.append(f"pan: camera y {y:.2f} below ground")
    r = page.evaluate("""() => { let m = null; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (o.isMesh && o.userData?.sculptComponent?.id === 'roundel-logo') m = o; });
      return {sum: m.geometry.groups.reduce((a, g) => a + g.count, 0), idx: m.geometry.index.count}; }""")
    print("roundel group triangles vs index:", r)
    if r["sum"] != r["idx"]: fails.append(f"roundel: {r['idx'] - r['sum']} index entries dropped (hidden back cap)")
print("FAIL " + "; ".join(fails) if fails else "PASS"); sys.exit(1 if fails else 0)
