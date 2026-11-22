"""Shared helpers: start vite if needed, open the viewer (gate mode 1024x687 by default; query "" = normal mode)."""
import subprocess, sys, time, urllib.request
from contextlib import contextmanager
from playwright.sync_api import sync_playwright

URL = "http://localhost:5173/"
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
# 8 turntable angles + 4 special views; every entry is a setCamera() argument.
BASE = dict(elevation=22, distance=40, fov=30, target=[0, 1.5, 0])
ANGLES = {f"az{a:03d}": dict(BASE, azimuth=a) for a in range(0, 360, 45)}
ANGLES.update(
    low=dict(BASE, azimuth=-51, elevation=5),
    high=dict(BASE, azimuth=-51, elevation=60),
    top=dict(BASE, azimuth=0, elevation=85),
    back=dict(BASE, azimuth=130, elevation=12),
)


def ensure_server():
    try:
        urllib.request.urlopen(URL, timeout=2); return
    except Exception:
        subprocess.Popen(["npx", "vite", "--port", "5173"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        time.sleep(0.5)
        try:
            urllib.request.urlopen(URL, timeout=2); return
        except Exception:
            pass
    sys.exit("vite did not start")


@contextmanager
def gate_page(query="?gate=1", viewport=(1024, 687)):
    ensure_server()
    with sync_playwright() as p:
        b = p.chromium.launch(args=ARGS)
        page = b.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        page.goto(URL + query)
        page.wait_for_function("window.__IMG2THREEJS_READY__ === true")
        page.wait_for_load_state("networkidle"); page.wait_for_timeout(500)
        try:
            yield page
        finally:
            b.close()


def set_camera(page, cam):
    page.evaluate("c => __IMG2THREEJS_CAPTURE__.setCamera(c)", cam)
    page.wait_for_timeout(300)
