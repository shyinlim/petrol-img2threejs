"""Props must not overlap each other or Mart, stay on the slab and on grass; flags hang at the pole top. Exit 0 = no violation."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page
from _geom import boxes

INSET = 0.02
bx = {}
with gate_page() as page:
    bx = boxes(page)
PROP = re.compile(r"^(tree-\d+(-trunk|-b)?|bush-\d+|agave-\d+-leaf-\d+|bin-\w+-\d+(-lid|-wheels)?|flagpole-\d+(-base|-finial)?|flag-(malaysia|johor))$")
SPHERE = re.compile(r"^(tree-\d+(-b)?|bush-\d+)$")  # crowns and bushes: judged by distance, not by AABB corners


def group(i):
    m = re.match(r"^(tree-\d+|agave-\d+|bin-\w+-\d+|flagpole-\d+)", i)
    if m: return m.group(1)
    return {"flag-malaysia": "flagpole-1", "flag-johor": "flagpole-2"}.get(i, i)


# one entry per component (never a union of pole+flag, that AABB would swallow neighbours); same-group parts are exempt from each other
ents = {}
for i, (mn, mx) in bx.items():
    if not PROP.match(i): continue
    if SPHERE.match(i):
        ents[i] = ("sphere", [(a + b) / 2 for a, b in zip(mn, mx)], (mx[0] - mn[0]) / 2 - INSET)
    else:
        ents[i] = ("box", [a + INSET for a in mn], [a - INSET for a in mx])


def hit(a, b):
    if a[0] == "box" and b[0] == "box":
        return all(a[1][k] < b[2][k] and b[1][k] < a[2][k] for k in range(3))
    if a[0] == "sphere" and b[0] == "sphere":
        return sum((a[1][k] - b[1][k]) ** 2 for k in range(3)) < (a[2] + b[2]) ** 2
    s, x = (a, b) if a[0] == "sphere" else (b, a)
    d = sum(max(x[1][k] - s[1][k], 0, s[1][k] - x[2][k]) ** 2 for k in range(3))
    return d < s[2] ** 2


bad = []
if len(ents) < 30: bad_n = f"only {len(ents)} props matched (expected 32): ids renamed or boxes() missed meshes"; print("layout FAIL", bad_n); sys.exit(1)
names = sorted(ents)
for n, i in enumerate(names):
    for j in names[n + 1:]:
        if group(i) != group(j) and hit(ents[i], ents[j]): bad.append(f"1 overlap {i} x {j}")
mart = ("box", [a + INSET for a in bx["mart"][0]], [a - INSET for a in bx["mart"][1]])
for i in names:
    if hit(ents[i], mart): bad.append(f"2 {i} overlaps mart")
slab = bx["base-slab"]
for i, (mn, mx) in bx.items():
    if PROP.match(i) and not (mn[0] >= slab[0][0] and mx[0] <= slab[1][0] and mn[2] >= slab[0][2] and mx[2] <= slab[1][2]):
        bad.append(f"3 {i} outside slab xz")
verges = [v for k, v in bx.items() if k.startswith("grass-verge-")]
seen = {}
for i, e in ents.items():  # grass check per group: trees by trunk, others by the mean centre of their parts
    if i.endswith("-trunk") or not (i.startswith("tree-")):
        c = e[1] if e[0] == "sphere" else [(x + y) / 2 for x, y in zip(e[1], e[2])]
        if re.match(r"^(bin-|bush-|tree-\d+-trunk|agave-)", i): seen.setdefault(group(i), []).append(c)
for g, cs in seen.items():
    c = [sum(x[k] for x in cs) / len(cs) for k in range(3)]
    if not any(v[0][0] <= c[0] <= v[1][0] and v[0][2] <= c[2] <= v[1][2] for v in verges): bad.append(f"4 {g} centre not on grass")
for pole, flag in (("flagpole-1", "flag-malaysia"), ("flagpole-2", "flag-johor")):
    top, ft = bx[pole][1][1], bx[flag][1][1]
    if not (top - 0.15 <= ft <= top + 1e-6): bad.append(f"5 {flag} top {ft:.2f} vs pole top {top:.2f}")
    gap = bx[flag][0][0] - bx[pole][1][0]  # flag must touch its pole, not float beside it
    if gap > 0.1: bad.append(f"5 {flag} is {gap:.2f} away from {pole}")
for k, v in bx.items():
    if k.startswith("grass-verge-") and v[0][0] < bx["mart"][1][0] and bx["mart"][0][0] < v[1][0] and v[0][2] < bx["mart"][1][2] and bx["mart"][0][2] < v[1][2]:
        bad.append(f"6 {k} overlaps mart xz")
print("layout", "FAIL" if bad else "OK", *bad, sep="\n  " if bad else " ")
sys.exit(1 if bad else 0)
