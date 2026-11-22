"""python3 scripts/check_details.py --round {1,2,3a,3} | --dump-disc. Each round includes the earlier ones. Exit 0 = all assertions pass.
Normal mode, camera at the v3 angle. --dump-disc writes shots/v10_disc_before.json (world centres of column-disc-1..4)."""
import argparse, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page, set_camera
from _geom import boxes, screen_boxes

ROOT = Path(__file__).resolve().parent.parent
V3 = dict(azimuth=-51, elevation=9.5, distance=30, fov=30, target=[0, 1.5, 0])
ap = argparse.ArgumentParser(); ap.add_argument("--round", choices=["1", "2", "3a", "3"]); ap.add_argument("--dump-disc", action="store_true")
args = ap.parse_args()
spec = json.loads((ROOT / "object-sculpt-spec.json").read_text())
comp = {c["id"]: c for c in spec["componentTree"]}
bevel = lambda c: c.get("geometryDescriptor", {}).get("edgeTreatment", {}).get("bevelRadius", 0)
fails = []


def check(n, fn):
    try:
        ok, msg = fn()
    except Exception as e:
        ok, msg = False, f"{type(e).__name__}: {str(e).splitlines()[0][:120]}"
    print(f"{'PASS' if ok else 'FAIL'} {n} {msg}")
    if not ok: fails.append(n)


# geometry types of each component's direct meshes, plus any ExtrudeGeometry meshes nested below them
TYPES = """ids => { const out = {}; __IMG2THREEJS_VIEWER__.scene.traverse(o => { const id = o.userData?.sculptComponent?.id;
  if (!id || o.isMesh || out[id] || !ids.includes(id)) return; out[id] = o.children.filter(m => m.isMesh).map(m => m.geometry.type); }); return out; }"""
EXTRUDE = """id => { let part = null; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (!part && o.userData?.sculptComponent?.id === id && o.isMesh) part = o; });
  if (!part) return null; const out = []; part.traverse(m => { if (m === part || !m.isMesh || m.geometry.type !== 'ExtrudeGeometry') return;
    m.updateWorldMatrix(true, false); m.geometry.computeBoundingBox(); const b = m.geometry.boundingBox; let mn = [1e9,1e9,1e9], mx = [-1e9,-1e9,-1e9];
    for (const x of [b.min.x,b.max.x]) for (const y of [b.min.y,b.max.y]) for (const z of [b.min.z,b.max.z]) { const p = part.position.clone().set(x,y,z).applyMatrix4(m.matrixWorld), a = [p.x,p.y,p.z];
      mn = mn.map((c,i) => Math.min(c,a[i])); mx = mx.map((c,i) => Math.max(c,a[i])); }
    out.push([mn, mx]); }); return out; }"""
CLICK = """([x, y]) => { const c = __IMG2THREEJS_VIEWER__.renderer.domElement;
  c.dispatchEvent(new PointerEvent('pointerdown', {clientX: x, clientY: y, bubbles: true}));
  c.dispatchEvent(new MouseEvent('click', {clientX: x, clientY: y, bubbles: true})); return document.getElementById('sel').textContent; }"""


def a1(page):
    wind = lambda v: page.evaluate("v => { const e = document.getElementById('s-wind'); if (e) { e.value = v; e.dispatchEvent(new Event('input', {bubbles: true})); } return e ? e.value : null; }", v)
    old = page.evaluate("document.getElementById('s-wind')?.value ?? null"); wind(0); page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r))))")  # measure the flat flag: the wave widens the projected box (v11 wind 0.14)
    sb = screen_boxes(page, ["flagpole-1", "flag-malaysia", "flagpole-2", "flag-johor"]); r = []
    if old is not None: wind(old)
    for pole, flag in (("flagpole-1", "flag-malaysia"), ("flagpole-2", "flag-johor")):
        r.append((sb[flag][2] - sb[flag][0]) / (sb[pole][3] - sb[pole][1]))
    return all(0.19 <= x <= 0.26 for x in r), f"width/pole-height={[round(x, 3) for x in r]} (want 0.19-0.26)"


def a2(page):
    hexes = page.evaluate("""() => { const out = []; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (o.isMesh && o.userData?.sculptComponent?.material === 'glass-dark')
      [].concat(o.material).forEach(m => m.color && out.push(m.color.getHexString())); }); return out; }""")
    return bool(hexes) and "2f3135" not in hexes, f"glass-dark={sorted(set(hexes))}"


def a12(page):
    """Each kerb-verge strip stays on its own verge: no overlap in xz with another verge's lawn, none with a flag-pole foot."""
    bx = boxes(page); bad = []
    hit = lambda A, B, axes: all(A[0][k] < B[1][k] and B[0][k] < A[1][k] for k in axes)
    for v in "abc":
        kb = bx.get(f"kerb-verge-{v}")
        if not kb: bad.append(f"kerb-verge-{v} missing"); continue
        for o in "abc":
            if o != v and hit(kb, bx[f"grass-verge-{o}"], (0, 2)): bad.append(f"kerb-verge-{v} on grass-verge-{o}")
        for n in (1, 2):
            fb = bx.get(f"flagpole-{n}-base")
            if fb and hit(kb, fb, (0, 1, 2)): bad.append(f"kerb-verge-{v} in flagpole-{n}-base")
    return not bad, f"{bad}"


def a3(page):
    ids = ["kerb-verge-a", "kerb-verge-b", "kerb-verge-c"]; live = boxes(page, ids)
    ok = all(i in live and comp.get(i, {}).get("parent") == "base-slab" for i in ids)
    return ok, f"live={[i for i in ids if i in live]} parents={[comp.get(i, {}).get('parent') for i in ids]}"


def a4(page):
    ids = [i for i, c in comp.items() if c["primitive"] == "box" and bevel(c) > 0]; t = page.evaluate(TYPES, ids)
    bad = [i for i in ids if i not in t or not t[i] or any(x != "RoundedBoxGeometry" for x in t[i])]
    return bool(ids) and not bad, f"{len(ids)} beveled boxes, not rounded: {bad[:6]}"


def a5(page):
    ref = json.loads((ROOT / "shots/v10_disc_before.json").read_text()); bx = boxes(page, list(ref)); bad = []
    for i, c in ref.items():
        cur = [(a + b) / 2 for a, b in zip(*bx[i])]
        if max(abs(x - y) for x, y in zip(cur, c)) >= 0.05: bad.append(i)
    cols = [i for i in ("column-1", "column-2", "column-3", "column-4") if comp[i]["primitive"] != "box"]
    return not bad and not cols, f"discs moved={bad} columns not box={cols}"


def a6(page):
    r = page.evaluate(EXTRUDE, "canopy-wordmark")
    if not r: return False, "no ExtrudeGeometry under canopy-wordmark"
    zw = r[0][1][2] - r[0][0][2]; return 2.0 <= zw <= 2.6, f"z width={zw:.2f} (want 2.0-2.6)"


def a7(page):
    bx = boxes(page); bad = []
    for pid, p in comp.items():
        r = bevel(p)
        if p["primitive"] != "box" or r <= 0 or pid not in bx: continue
        P = bx[pid]
        for cid, c in comp.items():
            if c.get("parent") != pid or cid not in bx: continue
            C = bx[cid]
            for a in range(3):
                if not any(abs(x - y) < 0.06 for x in (C[0][a], C[1][a]) for y in (P[0][a], P[1][a])): continue  # not flush on this axis
                for b in range(3):
                    if b == a: continue
                    # the child's upper edge ends in the parent's upper corner band, or its lower edge in the lower band (a child outside the parent is fine)
                    if P[1][b] - r + 1e-3 < C[1][b] <= P[1][b] + 1e-6 or P[0][b] - 1e-6 <= C[0][b] < P[0][b] + r - 1e-3: bad.append(f"{cid}@{pid} axis{'xyz'[b]}")
    return not bad, f"flush children in the rounded corner band: {sorted(set(bad))}"


def a8(page):
    sb = screen_boxes(page, ["mart-sign"])["mart-sign"]; xy = [(sb[0] + sb[2]) / 2, (sb[1] + sb[3]) / 2]
    sel = page.evaluate(CLICK, xy); page.evaluate("__IMG2THREEJS_PICK__.select(null)")
    return sel == "mart-sign", f"first hit at ({xy[0]:.0f},{xy[1]:.0f}) = {sel}"


def a9(page):
    want = {}
    for n in (1, 2, 3, 4):
        for s in (f"pump-hose-{n}a", f"pump-hose-{n}b"): want[s] = f"pump-{n}"
        want[f"pump-cabinet-top-{n}"] = f"pump-cabinet-{n}"
    want["pump-standee-3"] = "pump-3"
    live = boxes(page, list(want)); bad = [i for i, p in want.items() if i not in live or comp.get(i, {}).get("parent") != p]
    return not bad, f"missing or wrong parent: {bad[:6]}"


def a10(page):
    ids = [f"pump-island-{n}" for n in (1, 2, 3, 4)]; t = page.evaluate(TYPES, ids); bx = boxes(page, ids)
    bad = [i for i in ids if i not in t or any(x != "ExtrudeGeometry" for x in t[i]) or bx[i][0][1] < 0.15]
    return not bad, f"not extruded or below y 0.15: {bad}"


def a11(page):
    want = {"mart-eave": "mart"}
    for b in ("bin-blue-2", "bin-green-2"): want[b + "-lid"] = want[b + "-wheels"] = None
    for n in (1, 2, 3, 4): want[f"agave-{n}-leaf-4"] = want[f"agave-{n}-leaf-5"] = None
    for n in (1, 2): want[f"flagpole-{n}-base"] = want[f"flagpole-{n}-finial"] = None
    live = boxes(page, list(want)); bad = [i for i, p in want.items() if i not in live or (p and comp.get(i, {}).get("parent") != p)]
    gone = [f"tree-{n}-b" for n in (1, 2, 3, 4) if f"tree-{n}-b" in boxes(page, [f"tree-{n}-b"])]  # second crowns were removed on request
    return not bad and not gone, f"missing or wrong parent: {bad[:8]}, second crowns left: {gone}"


with gate_page("", viewport=(1280, 800)) as page:
    set_camera(page, V3); page.wait_for_timeout(1000)
    if args.dump_disc:
        bx = boxes(page, [f"column-disc-{n}" for n in (1, 2, 3, 4)])
        Path(ROOT / "shots/v10_disc_before.json").write_text(json.dumps({k: [(a + b) / 2 for a, b in zip(*v)] for k, v in bx.items()}, indent=1) + "\n")
        print("wrote shots/v10_disc_before.json"); sys.exit(0)
    lvl = ["1", "2", "3a", "3"].index(args.round)
    for n, f, need in ((1, a1, 0), (2, a2, 0), (3, a3, 1), (4, a4, 1), (6, a6, 1), (7, a7, 1), (8, a8, 1), (9, a9, 2), (10, a10, 2), (11, a11, 3)):
        if lvl >= need: check(n, lambda f=f: f(page))
    if lvl >= 1: check(12, lambda: a12(page))
    if args.round == "2": check(5, lambda: a5(page))
print("check_details round", args.round, "FAIL " + str(fails) if fails else "OK")
sys.exit(1 if fails else 0)
