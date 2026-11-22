"""Rebuild object-sculpt-spec.json from backup/spec_before_v10.json with the v10 edits.
Re-runnable: always restores from the backup first; reviews appended after the backup survive (same rule as build_spec_v9.py)."""
import copy, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = json.loads((ROOT / "backup/spec_before_v10.json").read_text())
cur = json.loads((ROOT / "object-sculpt-spec.json").read_text())
for key in ("reviewHistory", "visualEvidence", "tier1Results"):  # tier1Results too: diagnose_render --in-place appends there
    spec[key] += cur[key][len(spec[key]):]

tree = spec["componentTree"]
by = {c["id"]: c for c in tree}


def set_dim(c, w=None, h=None, d=None):
    """dimensions and transform.scale stay in sync (box sizes come from scale)."""
    for i, (k, v) in enumerate((("width", w), ("height", h), ("depth", d))):
        if v is not None:
            c["dimensions"][k] = v
            c["transform"]["scale"][i] = v


def set_pos(c, x=None, y=None, z=None):
    for i, v in enumerate((x, y, z)):
        if v is not None:
            c["transform"]["position"][i] = v


def set_att(c, start=None, end=None, base=None, endr=None):
    a = c["attachment"]
    for key, v in (("localStart", start), ("localEnd", end)):
        if v is not None:
            for i, x in enumerate(v):
                if x is not None:
                    a[key][i] = x
    if base is not None: a["baseRadius"] = base
    if endr is not None: a["endRadius"] = endr


def put_xz(c, x, z):
    """Cylinder (trunk, bin, pole) in root frame: attachment start/end and position all move to (x, z)."""
    set_att(c, start=[x, None, z], end=[x, None, z]); set_pos(c, x=x, z=z)


def shift_xz(c, dx, dz):
    """Move a part by a delta in its parent's frame (attachment and position together)."""
    for key in ("localStart", "localEnd"):
        if c.get("attachment"):
            c["attachment"][key][0] += dx; c["attachment"][key][2] += dz
    c["transform"]["position"][0] += dx; c["transform"]["position"][2] += dz


def clone(src_id, new_id, name, parent, material, after=None):
    c = copy.deepcopy(by[src_id])
    c["id"], c["name"], c["parent"], c["confidence"] = new_id, name, parent, 0.4
    c["dimensions"]["confidence"] = 0.4
    c["material"], c["materialLayers"] = material, [material]
    d = c["actionProfile"]["destruction"]; d["fractureGroup"], d["debrisMaterial"] = new_id, material
    c["topologyRationale"] = f"{name} is a discrete {c['primitive']} part of the station, assembled by contact, not a sculpted shell."
    tree.insert(tree.index(by[after or src_id]) + 1, c)
    by[new_id] = c
    return c


# --- Task 1: draw-call budget ruling (gate mode 160 -> 260; normal mode with shadows may use 2x) ---
spec["performanceBudget"]["maxDrawCalls"] = 260

# --- Round 1: colours and flag facing (start values, inferred from v3 pixels) ---
import math


def set_color(mat_id, hexv):
    m = next(m for m in spec["materials"] if m["id"] == mat_id)
    m["baseColor"] = m["color"] = hexv; m["albedo"]["dominant"] = hexv


set_color("glass-dark", "#4A4F57"); set_color("grass", "#5FB84A"); set_color("tree-green", "#5DBB45")
FLAG_YAW = math.radians(-35)  # turn toward the v3 camera (az -51); the slab corner (8.1, 9) caps the turn, see ledger ruling
FLAG_W = 1.8  # 2:1, hung from the pole top; v3 ratio needs flag width / pole height 0.19-0.26
put_xz(by["flagpole-1"], 4.4, 7.85); put_xz(by["flagpole-2"], 6.55, 7.9)  # clear of tree-3's crown; keeps flag-johor's tip inside the slab
for flag in ("flag-malaysia", "flag-johor"):
    f = by[flag]; set_dim(f, w=FLAG_W, h=FLAG_W / 2)
    f["transform"]["rotation"][1] = FLAG_YAW
    f["transform"]["position"][0] = (0.06 + FLAG_W / 2) * math.cos(FLAG_YAW)  # inner edge 0.06 off the pole axis
    f["transform"]["position"][1] = 6.99 - FLAG_W / 4  # top edge stays at 6.99
    f["transform"]["position"][2] = -(0.06 + FLAG_W / 2) * math.sin(FLAG_YAW)
spec["assumptions"].append("Round 1 colours (glass #4A4F57, grass #5FB84A, tree #5DBB45) and flag yaw are inferred from v3 pixels, not measured.")

# --- Round 2 ---
def raise_y(c, dy):
    """Lift a part (and its attachment endpoints) by dy; children in its frame move with it."""
    c["transform"]["position"][1] += dy
    if c.get("attachment"):
        c["attachment"]["localStart"][1] += dy; c["attachment"]["localEnd"][1] += dy


def set_bevel(cid, r):
    c = by[cid]
    c["geometryDescriptor"]["edgeTreatment"] = {"type": "bevel", "bevelRadius": r, "segments": 2}
    for f in c.get("localFeatures", []):
        if f["kind"] == "bevel": f["bevelRadius"] = r


def new_material(src_id, mat_id, name, hexv):
    m = copy.deepcopy(next(m for m in spec["materials"] if m["id"] == src_id))
    m["id"], m["name"] = mat_id, name
    spec["materials"].append(m); set_color(mat_id, hexv)


def retype(c, material):
    c["material"], c["materialLayers"] = material, [material]
    c["actionProfile"]["destruction"]["debrisMaterial"] = material


# 2d: square dark columns. Box origin is its centre, so children (number discs) move from the cylinder's start-based frame to the centre frame.
new_material("column-grey", "column-dark", "Column dark grey", "#8E8A86")
for n in (1, 2, 3, 4):
    c = by[f"column-{n}"]; c["primitive"] = "box"; set_dim(c, w=0.6, h=4.99, d=0.6); retype(c, "column-dark")
    d = by[f"column-disc-{n}"]; set_pos(d, y=-0.295); set_att(d, start=[None, -0.295, None], end=[None, -0.295, None])

# 2j: taller grass (bottom stays on the ground, top +0.08), curb strip on each verge's field-side long edge
GRASS_UP = 0.08
new_material("concrete", "curb-grey", "Curb grey", "#C9C6C2")
for v in ("a", "b", "c"):
    g = by[f"grass-verge-{v}"]; set_dim(g, h=0.2); raise_y(g, GRASS_UP / 2); set_bevel(f"grass-verge-{v}", 0.04)
for n in (1, 2, 3, 4):  # agaves are verge children: the verge centre rose 0.04, the top rose 0.08
    for k in (1, 2, 3):
        a = by.get(f"agave-{n}-leaf-{k}")
        if a: raise_y(a, GRASS_UP / 2)
for v, (x, z, w, d) in {"a": (-6.2, -3.87, 0.12, 7.74), "b": (1.183, 7.456, 7.794, 0.12), "c": (6.5, 7.16, 2.8, 0.12)}.items():
    k = clone(f"grass-verge-{v}", f"kerb-verge-{v}", f"Kerb verge {v.upper()}", "base-slab", "curb-grey")
    set_dim(k, w=w, h=0.24, d=d); set_pos(k, x, 0.78, z)

# 2f: props bigger, and lifted onto the thicker grass. Back-row trees/bushes/poles re-spaced so the bigger crowns clear each other and the slab edge.
put_xz(by["tree-3-trunk"], 5.65, 7.9); put_xz(by["tree-4-trunk"], 7.25, 7.9)
put_xz(by["flagpole-1"], 4.4, 7.85); put_xz(by["flagpole-2"], 6.45, 7.6)
set_pos(by["bush-2"], x=-2.3); set_pos(by["bush-4"], x=3.75); set_pos(by["bush-1"], z=-4.4); put_xz(by["tree-2-trunk"], -6.84, -3.4)
for k in (1, 2, 3): shift_xz(by[f"agave-2-leaf-{k}"], 0, -0.15)
for n in (1, 2, 3, 4):
    raise_y(by[f"tree-{n}-trunk"], GRASS_UP)
    big = 1.2 if n <= 2 else 1.6
    crown = by[f"tree-{n}"]; set_dim(crown, w=big, h=big, d=big); raise_y(crown, 0.1)
for n in (1, 2, 3, 4):
    b = by[f"bush-{n}"]; set_dim(b, w=1.1, h=0.8, d=1.1); set_pos(b, y=0.55 + GRASS_UP + 0.05)
for n in (1, 2): raise_y(by[f"flagpole-{n}"], GRASS_UP)
put_xz(by["bin-blue-1"], -6.84, -1.2); put_xz(by["bin-green-1"], -6.84, -1.2 + 0.85)
for bid in ("bin-blue-1", "bin-green-1", "bin-blue-2", "bin-green-2"):
    c = by[bid]; c["primitive"] = "box"; set_dim(c, w=0.7, h=0.95, d=0.7)
    set_pos(c, y=0.36 + 0.475); set_att(c, start=[None, 0.36, None], end=[None, 1.31, None]); set_bevel(bid, 0.06)

# 2g: rounded corners (RoundedBoxGeometry in main.ts); flush children stay within parent size minus 2r so they stay on the flat face
for cid, r in (("canopy", 0.03), ("mart", 0.03), ("concrete-top", 0.04), ("kerb-mart", 0.04)): set_bevel(cid, r)
for n in (1, 2, 3, 4):
    set_bevel(f"pump-head-{n}", 0.06); set_bevel(f"pump-cabinet-{n}", 0.05)
    set_dim(by[f"pump-sign-{n}"], h=0.43, d=1.38)
for k in range(1, 9): set_bevel(f"wheel-stop-{k}", 0.04)
set_dim(by["fascia-lip-top"], h=0.11, d=13.94); set_pos(by["fascia-lip-top"], y=0.365)  # top at 0.42 = canopy half-height 0.45 - r; bottom stays above the wordmark box (0.305)
set_dim(by["mart-band"], h=0.74); set_dim(by["mart-door-frame"], h=1.76); set_pos(by["mart-door-frame"], y=-0.68)  # off the rounded mart corners
set_dim(by["fascia-lip-end"], h=0.84); set_pos(by["fascia-lip-end"], z=-6.89)

# 2h: thicker roundel (radius stays 0.6). Mart sign to the band centre so the canopy and pumps do not hide it
r = by["roundel-logo"]; set_att(r, start=[-5.76, None, None], end=[-6.04, None, None]); set_dim(r, h=0.28)
set_pos(by["mart-sign"], z=0)
spec["assumptions"].append("Round 2 proportions, prop sizes, bevel radii and the Mart sign position are inferred from v3 pixels, not measured.")
# --- Round 3a: pumps ---
new_material("pump-white", "pump-grey", "Pump panel grey", "#C8C6C2")
new_material("pump-white", "nozzle-black", "Nozzle black", "#262626")
for n in (1, 2, 3, 4):
    retype(by[f"pump-panel-{n}"], "pump-grey")
    for side, z in (("a", -0.402), ("b", 0.402)):
        retype(by[f"pump-nozzle-{n}{side}"], "nozzle-black")
        h = clone(f"column-disc-{n}", f"pump-hose-{n}{side}", f"Pump hose {n}{side}", f"pump-{n}", "nozzle-black", after=f"pump-nozzle-{n}{side}")
        set_dim(h, w=0.06, h=0.6, d=0.06); set_pos(h, -0.12, 0.35, z)
        h["attachment"]["parentSocket"] = f"pump-{n}-socket"
        set_att(h, start=[-0.12, 0.65, z], end=[-0.12, 0.05, z], base=0.03, endr=0.03)
    ct = clone(f"pump-cabinet-{n}", f"pump-cabinet-top-{n}", f"Pump cabinet top {n}", f"pump-cabinet-{n}", "pump-grey", after=f"pump-cabinet-{n}")
    set_dim(ct, w=0.42, h=0.25, d=0.37); set_pos(ct, 0, 0.475, 0); set_bevel(f"pump-cabinet-top-{n}", 0)
    by[f"pump-island-{n}"]["geometryDescriptor"]["planShape"] = "stadium"
    d = by[f"column-disc-{n}"]; set_pos(d, z=-0.42); set_att(d, start=[None, None, -0.42], end=[None, None, -0.42])
    db = clone(f"column-disc-{n}", f"column-disc-b-{n}", f"Column disc {n} back", f"column-{n}", "decal-white")
    set_pos(db, z=0.42); set_att(db, start=[None, None, 0.42], end=[None, None, 0.42])
st = clone("pump-poster-3", "pump-standee-3", "Pump 3 standee", "pump-3", "pump-white", after="pump-poster-3")
set_dim(st, w=0.08, h=1.0, d=0.45); set_pos(st, -0.1, 0.05, -1.7)
spec["assumptions"].append("Round 3a pump details (hose length, cabinet top, standee, number-disc offsets) are inferred from v3 pixels, not measured.")

# --- Round 3: Mart eave, bins, trees, agaves, flag poles ---
import math as _m
new_material("tree-green", "agave-variegated", "Agave variegated", "#9BC25A")
new_material("column-dark", "wheel-black", "Wheel black", "#2A2A2A")
put_xz(by["flagpole-1"], 4.4, 7.8); put_xz(by["flagpole-2"], 6.35, 7.6)  # flags wave in normal mode: keep a margin from the slab edge

# 3i: eave on top of Mart, 0.2 out on every side
e = clone("mart-band", "mart-eave", "Mart eave", "mart", "mart-white", after="mart-band")
set_dim(e, w=3.4, h=0.15, d=9.4); set_pos(e, 0, 1.675, 0); set_bevel("mart-eave", 0.05)

# 3l: bin lids and a wheel axle on the back (+x) side, bottom
for bid in ("bin-blue-1", "bin-green-1", "bin-blue-2", "bin-green-2"):
    lid = clone(bid, f"{bid}-lid", f"{bid} lid", bid, by[bid]["material"], after=bid)
    set_dim(lid, w=0.78, h=0.08, d=0.78); set_pos(lid, 0, 0.515, 0); set_bevel(f"{bid}-lid", 0); lid["role"] = "support"  # part of the bin, not a worn/held item (attachment_anchor gate); strict validate then wants an attachment block
    lid["attachment"]["parentSocket"] = f"{bid}-lid-socket"; set_att(lid, start=[0, 0.475, 0], end=[0, 0.555, 0])
    wh = clone("column-disc-1", f"{bid}-wheels", f"{bid} wheels", bid, "wheel-black", after=f"{bid}-lid")
    set_dim(wh, w=0.16, h=0.58, d=0.16); set_pos(wh, 0.36, -0.335, 0)  # inside the bin's rounded edges: length 0.7-2r, bottom 2r up
    wh["attachment"]["parentSocket"] = f"{bid}-socket"
    set_att(wh, start=[0.36, -0.335, -0.29], end=[0.36, -0.335, 0.29], base=0.08, endr=0.08)

# 3m: thin trunks leaning 8 degrees toward the slab centre, a second smaller crown ball
for n in (1, 2, 3, 4):
    tr = by[f"tree-{n}-trunk"]; sgn = 1 if n <= 2 else -1
    L = 0.88; dx = sgn * L * _m.sin(_m.radians(8)); dy = L * _m.cos(_m.radians(8))
    st = tr["attachment"]["localStart"]
    set_att(tr, end=[st[0] + dx, st[1] + dy, st[2]], base=0.07, endr=0.06)
    set_dim(tr, w=0.14, d=0.14); set_pos(tr, x=st[0] + dx / 2, y=st[1] + dy / 2)
    crown = by[f"tree-{n}"]; cy = crown["transform"]["position"][1] - (L - dy)
    set_pos(crown, x=dx, y=cy)
    big = crown["dimensions"]["width"]
    bx, bz = {1: (0.45, 0.3), 2: (0.45, 0.3), 3: (-0.45, 0.3), 4: (-0.2, 0.35)}[n]
    b = clone(f"tree-{n}", f"tree-{n}-b", f"Tree {n} second crown", f"tree-{n}-trunk", "tree-green", after=f"tree-{n}")
    set_dim(b, w=0.55 * big, h=0.55 * big, d=0.55 * big); set_pos(b, dx + bx, cy - 0.25, bz)

# 3n: five agave leaves splayed 25-40 degrees from vertical, leaf 2 and 5 variegated
for n in (1, 2, 3, 4):
    l1 = by[f"agave-{n}-leaf-1"]; base = list(l1["attachment"]["localStart"])
    if n == 4: base[0] += 0.1  # clear bin-green-2's wheels
    l4 = clone(f"agave-{n}-leaf-1", f"agave-{n}-leaf-4", f"Agave {n} leaf 4", l1["parent"], "tree-green", after=f"agave-{n}-leaf-3")
    l5 = clone(f"agave-{n}-leaf-1", f"agave-{n}-leaf-5", f"Agave {n} leaf 5", l1["parent"], "agave-variegated", after=f"agave-{n}-leaf-4")
    for k, (phi, lat, hgt) in enumerate(((0, 0.33, 0.70), (72, 0.36, 0.66), (144, 0.35, 0.74), (216, 0.32, 0.68), (288, 0.35, 0.72)), start=1):
        lf = by[f"agave-{n}-leaf-{k}"]; a = _m.radians(phi)
        end = [base[0] + lat * _m.cos(a), base[1] + hgt, base[2] + lat * _m.sin(a)]
        set_att(lf, start=base, end=end)
        ln = _m.dist(base, end); set_dim(lf, h=ln)
        set_pos(lf, *[(base[i] + end[i]) / 2 for i in range(3)])
        if k == 2: retype(lf, "agave-variegated")

# 3o: flag pole foot block and finial ball
for n in (1, 2):
    pole = by[f"flagpole-{n}"]; px, py, pz = pole["attachment"]["localStart"][0], pole["attachment"]["localStart"][1], pole["attachment"]["localStart"][2]
    top = pole["attachment"]["localEnd"][1]
    fb = clone("wheel-stop-1", f"flagpole-{n}-base", f"Flagpole {n} base", "root", "column-dark", after=f"flagpole-{n}")
    set_dim(fb, w=0.3, h=0.15, d=0.3); set_pos(fb, px, py + 0.15, pz); set_bevel(f"flagpole-{n}-base", 0)
    fi = clone("tree-1", f"flagpole-{n}-finial", f"Flagpole {n} finial", "root", "column-dark", after=f"flagpole-{n}-base")
    set_dim(fi, w=0.18, h=0.18, d=0.18); set_pos(fi, px, top + 0.06, pz)
spec["assumptions"].append("Round 3 details (eave size, bin wheels, tree lean and second crown, agave splay, flag-pole foot and finial) are inferred from v3 pixels, not measured.")

(ROOT / "object-sculpt-spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
print("spec components:", len(tree))
