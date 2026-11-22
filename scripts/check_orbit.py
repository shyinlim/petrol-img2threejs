"""Task 1 check: OrbitControls drag/zoom/click/resize behave. Exit 0 = all 7 assertions pass."""
import subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://localhost:5173/"
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
CHROME = None  # set below if default playwright chromium is missing


def ensure_server():
    try:
        urllib.request.urlopen(URL, timeout=2)
    except Exception:
        subprocess.Popen(["npx", "vite", "--port", "5173"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            time.sleep(0.5)
            try:
                urllib.request.urlopen(URL, timeout=2); return
            except Exception:
                pass
        sys.exit("vite did not start")


def cam(page):
    return page.evaluate("(() => { const p = window.__IMG2THREEJS_VIEWER__.camera.position; return [p.x, p.y, p.z]; })()")


def stable(page):
    prev = cam(page)
    for _ in range(400):
        # 3 rendered frames per sample: normal mode renders at ~7 fps under SwiftShader, so a 200 ms wait can span zero frames and look "stable"
        page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r))))")
        cur = cam(page)
        if max(abs(a - b) for a, b in zip(prev, cur)) < 1e-4:
            return cur
        prev = cur
    raise RuntimeError("camera never stabilised")


def drag(page, dx, dy):
    page.mouse.move(640, 400); page.mouse.down()
    steps = 20
    for i in range(1, steps + 1):
        page.mouse.move(640 + dx * i / steps, 400 + dy * i / steps)
    page.mouse.up()


def main():
    ensure_server()
    fails, errors = [], []
    with sync_playwright() as p:
        kw = {"args": ARGS}
        if CHROME: kw["executable_path"] = CHROME
        b = p.chromium.launch(**kw)
        page = b.new_page(viewport={"width": 1280, "height": 800})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL); page.wait_for_function("window.__IMG2THREEJS_READY__ === true")
        page.wait_for_load_state("networkidle"); page.wait_for_timeout(500)
        page.evaluate("__IMG2THREEJS_VIEWER__.controls.dampingFactor = 0.3")  # settle faster; the checks do not depend on the damping rate

        def check(n, ok, msg=""):
            print(f"{'PASS' if ok else 'FAIL'} {n} {msg}")
            if not ok: fails.append(n)

        # 1 drag right orbits
        a = stable(page); drag(page, 300, 0); c = stable(page)
        check(1, max(abs(c[0] - a[0]), abs(c[2] - a[2])) > 1, f"dxz={max(abs(c[0]-a[0]), abs(c[2]-a[2])):.3f}")
        # 2 drag keeps selection
        page.evaluate("__IMG2THREEJS_PICK__.select('canopy')"); drag(page, 200, 0); stable(page)
        sel = page.inner_text("#sel"); check(2, sel == "canopy", sel)
        # 3 click selects a part under the cursor
        page.evaluate("__IMG2THREEJS_PICK__.select(null)")
        xy = page.evaluate("""(() => { const v = window.__IMG2THREEJS_VIEWER__; let m = null;
          v.scene.traverse(o => { if (!m && o.userData?.sculptComponent?.id === 'mart') m = o; });
          const p = m.getWorldPosition(v.camera.position.clone()); p.project(v.camera);
          const r = v.renderer.domElement.getBoundingClientRect();
          return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; })()""")
        stable(page); page.mouse.click(xy[0], xy[1]); sel = page.inner_text("#sel")
        check(3, sel != "click a part", sel)
        # 4 resize keeps camera
        a = stable(page); page.set_viewport_size({"width": 1000, "height": 700}); c = stable(page)
        d = max(abs(x - y) for x, y in zip(a, c)); check(4, d < 0.01, f"d={d:.5f}")
        # 5 drag up 2000px -> camera stays above target
        drag(page, 0, -2000); c = stable(page)
        ty = page.evaluate("__IMG2THREEJS_VIEWER__.controls.target.y"); check(5, c[1] > ty, f"y={c[1]:.3f} ty={ty}")
        # 6 setCamera syncs controls.target
        page.evaluate("__IMG2THREEJS_CAPTURE__.setCamera({azimuth: 40, target: [1, 2, 3]})")
        t = page.evaluate("(() => { const t = __IMG2THREEJS_VIEWER__.controls.target; return [t.x, t.y, t.z]; })()")
        check(6, t == [1, 2, 3], str(t))
        # 7 no page errors
        check(7, not errors, "; ".join(errors))
        b.close()
    sys.exit(1 if fails else 0)


main()
