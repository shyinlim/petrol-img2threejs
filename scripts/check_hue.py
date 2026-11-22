"""#s-hue = 20 must recolour the canopy side faces (they became a material array). Exit 0 = enough pixels changed."""
import sys
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageChops
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page

with gate_page() as page:
    a = Image.open(BytesIO(page.screenshot())).convert("RGB")
    page.evaluate("(() => { const e = document.getElementById('s-hue'); e.value = 20; e.dispatchEvent(new Event('input')); })()")
    page.wait_for_timeout(500)
    b = Image.open(BytesIO(page.screenshot())).convert("RGB")
n = sum(1 for p in ImageChops.difference(a, b).convert("L").getdata() if p > 8)
print("changed pixels:", n)
sys.exit(0 if n > 2000 else 1)
