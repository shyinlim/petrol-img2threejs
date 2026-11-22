"""python3 scripts/check_v11.py --task {2,3}: v11 checks, normal mode, default camera (never calls set_camera).
--task 2: A1-A6 (camera framing, flag wave, soffit brightness, soil layers, narrow viewport). --task 3 adds B1-B7 (red canopy parts).
Exit 0 = every assertion passes."""
import io, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page
from _geom import boxes, screen_boxes

fails = []
PROJECT = """p => { const v = __IMG2THREEJS_VIEWER__, q = v.camera.position.clone().set(...p).project(v.camera);
  const r = v.renderer.domElement.getBoundingClientRect(); return [r.left + (q.x + 1) / 2 * r.width, r.top + (1 - q.y) / 2 * r.height]; }"""
MESH = """id => { let m = null; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (!m && o.isMesh && o.userData?.sculptComponent?.id === id) m = o; }); return m; }"""
FLAG_Z = """id => { const m = (%s)(id); return Array.from(m.geometry.attributes.position.array).filter((_, i) => i %% 3 === 2); }""" % MESH
SOIL = """() => { const m = (%s)('base-slab'), out = [];
  for (const x of [].concat(m.material)) { const im = x.map?.image; if (!im || !im.getContext) continue;
    const d = im.getContext('2d').getImageData(0, 0, im.width, im.height).data, W = im.width, H = im.height;
    const rows = new Array(H).fill(0), cols = new Array(W).fill(0);
    for (let y = 0; y < H; y++) for (let x2 = 0; x2 < W; x2++) { const i = 4 * (y * W + x2), l = 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]; rows[y] += l / W; cols[x2] += l / H; }
    const sd = a => { const m = a.reduce((s, v) => s + v, 0) / a.length; return Math.sqrt(a.reduce((s, v) => s + (v - m) ** 2, 0) / a.length); };
    out.push([sd(rows), sd(cols)]); }
  return out; }""" % MESH
TAPER = """() => { const m = (%s)('bin-blue-2'), p = m.geometry.attributes.position, ys = [], xs = [];
  for (let i = 0; i < p.count; i++) { ys.push(p.getY(i)); xs.push(p.getX(i)); }
  const lo = Math.min(...ys), hi = Math.max(...ys), w = t => { const v = xs.filter((_, i) => Math.abs(ys[i] - t) < 1e-4); return Math.max(...v) - Math.min(...v); };
  return w(lo) / w(hi); }""" % MESH
BBOX = """id => { const m = (%s)(id); m.geometry.computeBoundingBox(); const b = m.geometry.boundingBox; return [b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z]; }""" % MESH
BANDS = """() => { const hex = m => [].concat(m.material).map(x => x.color.getHex());
  return { band: hex((%s)('mart-band')), canopy: hex((%s)('canopy')) }; }""" % (MESH, MESH)


def check(n, fn):
    try:
        ok, msg = fn()
    except Exception as e:
        ok, msg = False, f"{type(e).__name__}: {str(e).splitlines()[0][:140]}"
    print(f"{'PASS' if ok else 'FAIL'} {n} {msg}")
    if not ok: fails.append(n)


def lab_l(rgb):  # CIE L* of an sRGB triple (0-255)
    def lin(c): c /= 255; return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(lin, rgb); y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return 116 * (y ** (1 / 3) if y > 216 / 24389 else (24389 / 27 * y + 16) / 116) - 16


def a1(page):
    ids = ["canopy", "flag-malaysia", "flag-johor", "base-slab", "bin-blue-2"]; bad = []
    for vp in ((1280, 800), (1667, 900)):
        page.set_viewport_size({"width": vp[0], "height": vp[1]}); page.wait_for_timeout(500)
        pl, tt = page.evaluate("[document.getElementById('panel').getBoundingClientRect().left, document.getElementById('toolbar').getBoundingClientRect().top]")
        sb = screen_boxes(page, ids)
        for i in ids:
            x0, y0, x1, y1 = sb[i]
            if not (x0 >= 16 and x1 <= pl - 16 and y0 >= 16 and y1 <= tt - 8): bad.append(f"{vp[0]} {i} [{x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}] panel {pl:.0f} bar {tt:.0f}")
    return not bad, "; ".join(bad) or "all five parts inside the free area at both sizes"


def a2(page):
    cy = page.evaluate("__IMG2THREEJS_VIEWER__.camera.position.y"); s = boxes(page, ["soffit"])["soffit"][0][1]
    return cy < s, f"camera y {cy:.2f} soffit min y {s:.2f}"


def a3(page):
    page.wait_for_timeout(1000); lo, hi = {}, {}
    for _ in range(12):
        for i, z in enumerate(page.evaluate(FLAG_Z, "flag-malaysia")):
            lo[i] = min(lo.get(i, z), z); hi[i] = max(hi.get(i, z), z)
        page.wait_for_timeout(250)
    swing = max(hi[i] - lo[i] for i in lo)  # per-vertex z range over 3 s = up to 2x the wave amplitude
    return swing >= 0.4, f"max per-vertex z swing {swing:.2f} (need >= 0.4, i.e. amplitude 0.2)"


def a4(page):
    cb = boxes(page, ["canopy", "soffit"]); p = [cb["canopy"][0][0] + 1.0, cb["soffit"][0][1] - 0.001, 2.0]
    x, y = page.evaluate(PROJECT, p); im = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    px = [im.getpixel((int(x) + dx, int(y) + dy)) for dx in range(-4, 5) for dy in range(-4, 5)]
    L = lab_l(tuple(sum(c[i] for c in px) / len(px) for i in range(3)))
    return L >= 85, f"soffit L* {L:.1f} at ({x:.0f},{y:.0f}) (need >= 85)"


def a5(page):
    r = page.evaluate(SOIL)
    return bool(r) and all(row >= 3 * col for row, col in r), f"(row sd, col sd) per soil map: {[(round(a, 1), round(b, 1)) for a, b in r]} (need row >= 3x col)"


def a6(page):
    page.set_viewport_size({"width": 800, "height": 700}); page.wait_for_timeout(500)
    v = page.evaluate("(() => { const c = __IMG2THREEJS_VIEWER__.camera; return !c.view || !c.view.enabled || c.view.offsetX === 0; })()")
    return v and not errors, f"view offset off={v} errors={errors}"


def b1(page):
    r = page.evaluate("""() => { const c = (%s)('canopy'), e = c && c.children.find(k => k.name === 'energy-lines'); if (!e) return null;
      const m = [].concat(e.material)[0]; e.updateWorldMatrix(true, false); e.geometry.computeBoundingBox();
      const b = e.geometry.boundingBox.clone().applyMatrix4(e.matrixWorld); return { map: !!m.map, min: [b.min.x, b.min.y, b.min.z], max: [b.max.x, b.max.y, b.max.z] }; }""" % MESH)
    if not r: return False, "no energy-lines child under canopy"
    cx = boxes(page, ["canopy"])["canopy"][0][0]
    ok = r["map"] and r["min"][0] >= cx - 0.02 and r["min"][2] >= -6.25 and r["max"][2] <= -4.2
    return ok, f"map={r['map']} min.x {r['min'][0]:.2f} (canopy min.x {cx:.2f}) z [{r['min'][2]:.2f},{r['max'][2]:.2f}] (need [-6.25,-4.2])"


def b2(page): w = page.evaluate(BBOX, "roundel-logo")[0]; return 0.98 <= w <= 1.02, f"roundel width {w:.3f}"


def b3(page):
    """No striped kerb and no wheel stop: nothing on the forecourt blocks the car."""
    left = [k for k in boxes(page) if k.startswith("wheel-stop-") or k == "kerb-mart"]
    return not left, f"striped parts left: {left}"


def b8(page):
    """Roundel stands on the right-hand short face (+z), facing +z, not on the corner diagonal."""
    b = boxes(page, ["roundel-logo", "canopy"]); r, c = b["roundel-logo"], b["canopy"]
    cz = (r[0][2] + r[1][2]) / 2; thick = r[1][2] - r[0][2]
    cx = (r[0][0] + r[1][0]) / 2
    ok = cz >= c[1][2] - 0.01 and thick <= 0.4 and r[0][0] > c[0][0] + 0.3 and cx - c[0][0] <= 1.1
    return ok, f"roundel centre z {cz:.2f} (canopy +z face {c[1][2]:.2f}), z thickness {thick:.2f}, {cx - c[0][0]:.2f} in from the corner (want <= 1.1), min x {r[0][0]:.2f}"


def b9(page):
    """One number disc per column, centred on the column face."""
    r = page.evaluate("""() => { const out = {extra: [], off: []}; __IMG2THREEJS_VIEWER__.scene.traverse(o => { const id = o.userData?.sculptComponent?.id || '';
      if (!o.isMesh && /^column-disc-b-/.test(id)) out.extra.push(id); }); return out; }""")
    b = boxes(page, [f"column-{n}" for n in range(1, 5)] + [f"column-disc-{n}" for n in range(1, 5)])
    off = [n for n in range(1, 5) if abs((b[f"column-disc-{n}"][0][2] + b[f"column-disc-{n}"][1][2]) / 2 - (b[f"column-{n}"][0][2] + b[f"column-{n}"][1][2]) / 2) > 0.05]
    return not r["extra"] and not off, f"extra discs {r['extra']} discs off the column centre {off}"


def b4(page):
    # left bins replaced by the pylon sign on the back-left slab corner
    left = page.evaluate("(() => { const out = []; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (/^bin-(blue|green)-1/.test(o.userData?.sculptComponent?.id || '')) out.push(o.userData.sculptComponent.id); }); return out; })()")
    b = boxes(page, ["pylon-sign", "concrete-top"]); p, s = b["pylon-sign"], b["concrete-top"]
    ok = not left and p[0][0] > 6.5 and p[0][2] < -8 and p[1][0] <= s[1][0] and p[0][2] >= s[0][2] and abs(p[0][1] - s[1][1]) < 0.02 and p[1][1] - p[0][1] > 2.5
    return ok, f"left bins {left} pylon {p} slab {s}"


def b5(page): r = page.evaluate(TAPER); return r <= 0.9, f"bottom/top width ratio {r:.3f} (need <= 0.9)"


def b6(page):
    n = page.evaluate("(() => { const out = []; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if ((o.userData?.sculptComponent?.id || '').startsWith('mart-rail-')) out.push(o.userData.sculptComponent.id); }); return out; })()")
    return not n, f"mart-rail nodes {n}"


def b7(page):
    r = page.evaluate(BANDS); roof = 0xf3eee8; side = [c for c in r["canopy"] if c != roof]
    return bool(side) and set(r["band"]) == set(side[:1]) and len(set(side)) == 1, f"mart-band {[hex(c) for c in r['band']]} canopy sides {[hex(c) for c in side]}"


def g1(page):
    """Gate mode keeps the v10 soffit: emissive 0.6, black glow base, 4x6 downlights (Global Constraints: gate mode unchanged)."""
    r = page.evaluate("""() => { let m = null; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (!m && o.isMesh && o.userData?.sculptComponent?.id === 'soffit') m = o; });
      const x = [].concat(m.material).find(k => k.emissiveMap), im = x.emissiveMap.image, d = im.getContext('2d').getImageData(2, 2, 1, 1).data;
      return { inten: x.emissiveIntensity, base: d[0] }; }""")
    return r["inten"] == 0.6 and r["base"] == 0, f"gate soffit emissiveIntensity {r['inten']} glow base value {r['base']} (want 0.6 and 0)"


def b10(page):
    """No wordmark on the back (+x) face of the canopy."""
    n = page.evaluate("(() => { const out = []; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (o.userData?.sculptComponent?.id === 'canopy-wordmark-back') out.push(o.name); }); return out; })()")
    return not n, f"canopy-wordmark-back nodes {n}"


task = int(sys.argv[sys.argv.index("--task") + 1]); errors = []
with gate_page("", viewport=(1280, 800)) as page:
    page.on("pageerror", lambda e: errors.append(str(e)))
    steps = [("A2", a2), ("A3", a3), ("A4", a4), ("A5", a5), ("A1", a1), ("A6", a6)]
    if task >= 3: steps += [("B1", b1), ("B2", b2), ("B3", b3), ("B4", b4), ("B5", b5), ("B6", b6), ("B7", b7), ("B8", b8), ("B9", b9), ("B10", b10)]
    for n, f in steps: check(n, lambda f=f: f(page))
with gate_page("?gate=1") as gp: check("G1", lambda: g1(gp))
print("check_v11", "FAIL " + ",".join(fails) if fails else "OK")
sys.exit(1 if fails else 0)
