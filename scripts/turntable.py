"""python3 scripts/turntable.py <tag>: 13 gate-mode shots + 4x4 sheet in shots/. Exit 0 if all exist and std > 5."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page, set_camera, ANGLES

tag = sys.argv[1]
out = Path("shots"); out.mkdir(exist_ok=True)
names = ["ref"] + list(ANGLES)
with gate_page() as page:
    page.screenshot(path=str(out / f"v8_{tag}_ref.png"))  # untouched reference camera
    for n, cam in ANGLES.items():
        set_camera(page, cam)
        page.screenshot(path=str(out / f"v8_{tag}_{n}.png"))

bad, cell = [], (512, 343)
sheet = Image.new("RGB", (cell[0] * 4, cell[1] * 4), (48, 48, 48))
for i, n in enumerate(names):
    f = out / f"v8_{tag}_{n}.png"
    if not f.exists(): bad.append(f"{n}: missing"); continue
    im = Image.open(f).convert("RGB")
    if max(ImageStat.Stat(im).stddev) <= 5: bad.append(f"{n}: std<=5")
    t = im.resize(cell); ImageDraw.Draw(t).text((8, 8), n, fill=(255, 255, 0))
    sheet.paste(t, ((i % 4) * cell[0], (i // 4) * cell[1]))
sheet.save(out / f"v8_{tag}_sheet.png")
print("turntable", tag, "FAIL " + "; ".join(bad) if bad else "OK 13 shots")
sys.exit(1 if bad else 0)
