"""Gallery-page UI check (normal mode 1-7, 9-17, gate mode 8). Exit 0 = all assertions pass."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page

HEX = """() => { const out = []; let n = null;
  __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (!n && o.userData?.sculptComponent?.id === 'mart' && !o.isMesh) n = o; });
  n.traverse(m => { if (m.isMesh) [].concat(m.material).forEach(x => { if (x.emissive) out.push(x.emissive.getHex()); }); });
  return out; }"""
CAM = "(() => { const p = __IMG2THREEJS_VIEWER__.camera.position; return [p.x, p.y, p.z]; })()"
fails = []


def check(n, fn):
    try:
        ok, msg = fn()
    except Exception as e:
        ok, msg = False, f"{type(e).__name__}: {str(e).splitlines()[0][:120]}"
    print(f"{'PASS' if ok else 'FAIL'} {n} {msg}")
    if not ok: fails.append(n)


def stable(page):  # copied from check_orbit.py (that file runs its main() on import)
    prev = page.evaluate(CAM)
    for _ in range(400):
        page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r))))"); cur = page.evaluate(CAM)  # 3 rendered frames per sample
        if max(abs(a - b) for a, b in zip(prev, cur)) < 1e-4: return cur
        prev = cur
    raise RuntimeError("camera never stabilised")


def drag(page, dx, dy):
    page.mouse.move(640, 400); page.mouse.down()
    for i in range(1, 21): page.mouse.move(640 + dx * i / 20, 400 + dy * i / 20)
    page.mouse.up()


def a1(page): v = [page.is_visible(f"#{i}") for i in ("eyebrow", "title", "footnote")]; return all(v), str(v)


def a2(page):
    g, i = page.locator("#panel .group").count(), page.locator("#panel input").count()
    if g < 4 or i < 12: return False, f"groups={g} inputs={i}"
    bad = page.evaluate("""() => { const bad = [];
      document.querySelectorAll('#panel input[type=range]').forEach(r => {
        const n = r.parentElement.querySelector('input[type=number]'); if (!n) { bad.push(r.id + ': no number box'); return; }
        const set = (el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true})); };
        const lo = +r.min, hi = +r.max, mid = String(lo + (hi - lo) * 0.25);
        set(r, mid); if (+n.value !== +r.value) bad.push(r.id + ': range->number');
        const mid2 = String(lo + (hi - lo) * 0.75); set(n, mid2); if (+r.value !== +n.value) bad.push(r.id + ': number->range'); });
      return bad; }""")
    if bad: return False, "; ".join(bad)
    page.click("#panel-head"); c = not page.is_visible("#panel-body")
    page.click("#panel-head"); o = page.is_visible("#panel-body")
    return c and o, f"groups={g} inputs={i} collapse={c} expand={o}"


def a3(page):
    ids = ("b-reset-view", "b-rotate", "b-fullscreen", "b-shot")
    n = [page.locator(f"#toolbar #{i} svg").count() for i in ids]
    return all(x == 1 for x in n), str(n)


def a4(page):
    cur = page.evaluate("getComputedStyle(__IMG2THREEJS_VIEWER__.renderer.domElement).cursor")
    xy = page.evaluate("""(() => { const v = __IMG2THREEJS_VIEWER__; let m = null;
      v.scene.traverse(o => { if (!m && o.userData?.sculptComponent?.id === 'mart' && !o.isMesh) m = o; });
      const p = m.getWorldPosition(v.camera.position.clone()); p.project(v.camera); const r = v.renderer.domElement.getBoundingClientRect();
      return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; })()""")
    page.mouse.move(xy[0], xy[1]); page.wait_for_timeout(300)
    on = page.evaluate("getComputedStyle(__IMG2THREEJS_VIEWER__.renderer.domElement).cursor")
    return cur == "grab" and on == "pointer", f"idle={cur} over-mart={on}"


def a5(page):
    a = stable(page); drag(page, 300, 80); b = stable(page)
    page.click("#b-reset-view"); c = stable(page)
    d = max(abs(x - y) for x, y in zip(a, c)); moved = max(abs(x - y) for x, y in zip(a, b))
    return moved > 0.5 and d < 0.01, f"dragged={moved:.2f} afterReset={d:.4f}"


def a6(page):
    page.wait_for_timeout(3000); rot = "__IMG2THREEJS_VIEWER__.controls.autoRotate"
    s0 = page.evaluate(rot); page.click("#b-rotate"); s1 = page.evaluate(rot); page.click("#b-rotate"); s2 = page.evaluate(rot)
    return (s0, s1, s2) == (False, True, False), f"{s0},{s1},{s2}"


def a7(page):
    before = page.evaluate(HEX); page.evaluate("__IMG2THREEJS_PICK__.select('mart')"); sel = page.evaluate(HEX)
    page.evaluate("__IMG2THREEJS_PICK__.select(null)"); after = page.evaluate(HEX)
    ok = bool(sel) and all(x == 0xffb070 for x in sel) and after == before
    return ok, f"before={[hex(x) for x in before][:3]} selected={[hex(x) for x in sel][:3]} restored={after == before}"


def a9(page):
    """Typing in a number box must not be rewritten key by key: "45" into the sun-height box, "0.8" into exposure."""
    out = []
    for num, rng, text in (("v-el", "s-el", "45"), ("v-exp", "s-exp", "0.8")):
        page.click(f"#{num}", click_count=3); page.keyboard.type(text); page.keyboard.press("Tab")
        out.append((page.evaluate(f"document.getElementById('{num}').value"), page.evaluate(f"document.getElementById('{rng}').value")))
    return all(float(n) == float(r) == float(x) for (n, r), x in zip(out, ("45", "0.8"))), f"typed 45 and 0.8 -> {out}"


def a8(page):
    d = page.evaluate("""() => ['eyebrow','title','toolbar','panel'].map(i => { const e = document.getElementById(i); return e ? getComputedStyle(e).display : 'missing'; })""")
    ar = page.evaluate("__IMG2THREEJS_VIEWER__.controls.autoRotate"); bg = page.evaluate("__IMG2THREEJS_VIEWER__.scene.background?.getHex()")
    return all(x == "none" for x in d) and ar is False and bg == 0x303030, f"display={d} autoRotate={ar} bg={bg and hex(bg)}"


def a10(page):
    t = page.evaluate("document.body.innerText"); cjk = sorted(set(c for c in t if "\u3400" <= c <= "\u9fff"))
    return not cjk, f"CJK chars in page text: {''.join(cjk)[:20]}"


def a11(page):
    t, ff = page.evaluate("[document.getElementById('title').innerText, getComputedStyle(document.getElementById('title')).fontFamily]")
    return t == "Caltex Station" and "Songti" not in ff, f"title={t!r} font={ff[:60]}"


def a12(page):
    miss = page.evaluate("[...document.querySelectorAll('#toolbar button')].filter(b => !(b.getAttribute('aria-label') || '').trim()).map(b => b.id)")
    tag = page.evaluate("document.getElementById('panel-head').tagName")
    if tag != "BUTTON": return False, f"panel-head is {tag}, no aria-label on {miss}"
    e0 = page.get_attribute("#panel-head", "aria-expanded"); page.click("#panel-head"); e1 = page.get_attribute("#panel-head", "aria-expanded"); page.click("#panel-head")
    return not miss and (e0, e1) == ("true", "false"), f"missing aria-label {miss} aria-expanded {e0}->{e1}"


def a13(page):
    r = page.evaluate("""() => ({ small: [...document.querySelectorAll('#panel input[type=range]')].filter(r => r.getBoundingClientRect().height < 20).map(r => r.id),
      font: [...document.querySelectorAll('#panel .row label')].filter(l => parseFloat(getComputedStyle(l).fontSize) < 13).map(l => l.textContent) })""")
    return not r["small"] and not r["font"], f"sliders under 20px {r['small']} labels under 13px {r['font']}"


def a14(page):
    c, bg = page.evaluate("[getComputedStyle(document.getElementById('eyebrow')).color, getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()]")
    import re
    def rgb(s):
        s = s.strip()
        if s.startswith("#"): s = s[1:]; s = "".join(ch * 2 for ch in s) if len(s) == 3 else s; return [int(s[i:i + 2], 16) for i in (0, 2, 4)]
        return [int(float(x)) for x in re.findall(r"[\d.]+", s)[:3]]
    def lum(c):
        f = lambda v: v / 255 / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
    l1, l2 = sorted((lum(rgb(c)), lum(rgb(bg))), reverse=True); ratio = (l1 + 0.05) / (l2 + 0.05)
    return ratio >= 4.5, f"eyebrow {c} on {bg}: {ratio:.2f}:1 (need 4.5)"


def a15(page):
    """Reset Parts: disabled until a part is lifted; Lift raises the selected part, Reset Parts puts it back and disables itself again."""
    Y = "id => { let r = null; __IMG2THREEJS_VIEWER__.scene.traverse(o => { if (!r && !o.isMesh && o.userData?.sculptComponent?.id === id) r = o; }); return r.position.y; }"
    d0 = page.is_disabled("#b-reset"); page.evaluate("__IMG2THREEJS_PICK__.select('pump-1')"); y0 = page.evaluate(Y, "pump-1")
    page.click("#b-detach"); y1 = page.evaluate(Y, "pump-1"); d1 = page.is_disabled("#b-reset")
    page.click("#b-reset"); y2 = page.evaluate(Y, "pump-1"); d2 = page.is_disabled("#b-reset")
    return d0 and not d1 and d2 and y1 > y0 + 1 and abs(y2 - y0) < 1e-6, f"disabled before/lifted/after={d0}/{d1}/{d2} y {y0:.2f}->{y1:.2f}->{y2:.2f}"


def a16(page):
    """Shadow softness starts at 0 (slider and number box)."""
    r = page.evaluate("[document.getElementById('s-sh').value, document.getElementById('v-sh').value]")
    return all(float(x) == 0 for x in r), f"s-sh, v-sh = {r} (want 0)"


def a17(page):
    """Slider track, left and right of the thumb, is a thin line (<= 4 px dark rows) and the thumb at most 16 px, measured on a screenshot of the Sun azimuth slider."""
    import io
    from PIL import Image
    box = page.evaluate("(() => { const r = document.getElementById('s-az').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
    frac = page.evaluate("(() => { const e = document.getElementById('s-az'); return (e.value - e.min) / (e.max - e.min); })()")
    im = Image.open(io.BytesIO(page.screenshot(clip={"x": box[0], "y": box[1] - 4, "width": box[2], "height": box[3] + 8}))).convert("L")
    dark = lambda x: sum(1 for y in range(im.height) if im.getpixel((min(int(x), im.width - 1), y)) < 200)
    track, thumb = max(dark(box[2] * 0.15), dark(box[2] * 0.92)), dark(7 + frac * (box[2] - 14))  # 15%: left of the thumb (filled part on native sliders), 92%: right of it
    return track <= 4 and thumb <= 16, f"track {track}px thumb {thumb}px (want <= 4 and <= 16)"


errors = []
with gate_page("", viewport=(1280, 800)) as page:
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.evaluate("__IMG2THREEJS_VIEWER__.controls.dampingFactor = 0.3")  # settle faster; the checks do not depend on the damping rate
    for n, f in ((16, a16), (1, a1), (2, a2), (3, a3), (4, a4), (5, a5), (6, a6), (7, a7), (9, a9), (10, a10), (11, a11), (12, a12), (13, a13), (14, a14), (15, a15), (17, a17)): check(n, lambda f=f: f(page))
with gate_page("?gate=1") as page:
    check(8, lambda: a8(page))
check("errors", lambda: (not errors, "; ".join(errors)))
print("check_ui", "FAIL " + str(fails) if fails else "OK")
sys.exit(1 if fails else 0)
