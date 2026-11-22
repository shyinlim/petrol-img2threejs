"""Rebuild object-sculpt-spec.json (and di.json) from backup/spec_before_v8.json with the v8 shape/layout edits.
Re-runnable: always restores from the backup first. reviewHistory is kept as-is.
Pump-orange colour comes from scripts/pump_orange.txt if present (Task 5 tunes it), else the start value."""
import copy, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = json.loads((ROOT / "backup/spec_before_v8.json").read_text())
di = json.loads((ROOT / "backup/di_before_v8.json").read_text())
cur = json.loads((ROOT / "object-sculpt-spec.json").read_text())
# keep reviews appended after the backup (append_review output survives a re-run)
for key in ("reviewHistory", "visualEvidence"):
    spec[key] += cur[key][len(spec[key]):]
PUMP_ORANGE = (ROOT / "scripts/pump_orange.txt").read_text().strip() if (ROOT / "scripts/pump_orange.txt").exists() else "#E2582A"

tree = spec["componentTree"]
by = {c["id"]: c for c in tree}


def set_dim(c, w=None, h=None, d=None):
    """dimensions, transform.scale stay in sync (factory reads box sizes from scale)."""
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


def clone(src_id, new_id, name, parent, after_id=None):
    c = copy.deepcopy(by[src_id])
    c["id"], c["name"], c["parent"], c["confidence"] = new_id, name, parent, 0.4
    c["dimensions"]["confidence"] = 0.4
    d = c["actionProfile"]["destruction"]
    d["fractureGroup"] = new_id
    d["debrisMaterial"] = c["material"]
    c["topologyRationale"] = f"{name} is a discrete {c['primitive']} part of the station, assembled by contact, not a sculpted shell."
    tree.insert(tree.index(by[after_id or src_id]) + 1, c)
    by[new_id] = c
    return c


def delete(cid):
    tree.remove(by.pop(cid))


# roundel: smaller disc, y 0.4 -> 0.45 (cylinder size comes from attachment radii)
r = by["roundel-logo"]
set_att(r, start=[None, 0.45, None], end=[None, 0.45, None], base=0.475, endr=0.475)
set_dim(r, w=0.95, d=0.95); set_pos(r, y=0.45)

# flagpoles: move clear of canopy (x<=4.2) and Mart (z<=7.0); the two flags must not overlap in x
for cid, (x, z) in {"flagpole-1": (4.4, 8.0), "flagpole-2": (7.0, 8.4)}.items():
    p = by[cid]
    set_att(p, start=[x, None, z], end=[x, None, z]); set_pos(p, x=x, z=z)

# columns: stand on each island's -z end (canopy-local x,z)
for cid, (x, z) in {"column-1": (-1.45, 2.25), "column-2": (-1.45, -3.15), "column-3": (2.35, 2.25), "column-4": (2.35, -3.15)}.items():
    c = by[cid]
    set_att(c, start=[x, None, z], end=[x, None, z]); set_pos(c, x=x, z=z)

for n in "1234":
    # island: longer, centre shifted to -z
    isl = by[f"pump-island-{n}"]; set_dim(isl, d=3.4); set_pos(isl, z=-0.3)
    # body: shorter (bottom stays put), panel on top, screen moves onto the panel
    body = by[f"pump-{n}"]; set_dim(body, h=0.9); set_pos(body, y=0.81)
    # children keep parent-relative offsets, so lowering the body centre by 0.3 would sink island, wheel stops and cabinet into the floor
    for ch in [c for c in tree if c["parent"] == f"pump-{n}" and c["id"] != f"pump-screen-{n}"]:
        ch["transform"]["position"][1] += 0.3
    panel = clone(f"pump-head-{n}", f"pump-panel-{n}", f"Pump {n} display panel", f"pump-{n}", after_id=f"pump-{n}")
    set_dim(panel, w=0.52, h=0.7, d=0.72); set_pos(panel, 0, 0.8, 0)
    scr = by[f"pump-screen-{n}"]
    scr["parent"] = f"pump-panel-{n}"; set_dim(scr, h=0.5, d=0.5); set_pos(scr, -0.27, 0, 0)
    delete(f"pump-poster-blue-{n}")
    # parking-space wheel stops on both sides: -x moves to -1.3, copy at +1.3
    ws = by[f"wheel-stop-{n}"]; set_pos(ws, x=-1.3)
    w2 = clone(f"wheel-stop-{n}", f"wheel-stop-{int(n) + 4}", f"Pump {n} striped wheel stop (+x side)", f"pump-{n}", after_id=f"wheel-stop-{n}")
    set_pos(w2, x=1.3)

# trees: smaller crowns, shorter trunks, crown sits on the trunk top
for n, dia in {"1": 1.0, "2": 1.0, "3": 1.4, "4": 1.4}.items():
    t, cr = by[f"tree-{n}-trunk"], by[f"tree-{n}"]
    top = 1.1; start_y = t["attachment"]["localStart"][1]
    set_att(t, end=[None, top, None]); set_dim(t, h=top - start_y); set_pos(t, y=(start_y + top) / 2)
    set_dim(cr, w=dia, h=dia, d=dia); set_pos(cr, y=top + dia / 2 - t["transform"]["position"][1])

# Mart band/sign
b = by["mart-band"]; set_dim(b, h=0.8); set_pos(b, y=1.19)
s = by["mart-sign"]; set_dim(s, h=0.65, d=2.0)

# back wordmark on the +x long edge
wm = clone("canopy-wordmark", "canopy-wordmark-back", "Canopy wordmark (back edge)", "canopy")
set_pos(wm, x=5.77, z=-1.5)

# parking lines become a ground texture (Task 4); detail inventory points at the surface that hosts it
for n in "123": delete(f"parking-line-{n}")
for inv in (di["detailInventory"]["details"], spec["preSpecAssessment"]["detailInventory"]["details"]):
    for x in inv:
        if x["mapsTo"].get("ref") == "parking-line-1": x["mapsTo"]["ref"] = "concrete-top"

# pump-orange: baseColor, color, albedo.dominant (the factory reads these, not colorMaterialRecipe)
for m in spec["materials"]:
    if m["id"] == "pump-orange":
        m["baseColor"] = m["color"] = m["albedo"]["dominant"] = PUMP_ORANGE

spec["assumptions"] = [
    "Column positions (on each pump island -z end) are inferred from v3, not measured.",
    "Mart back door is inferred; v3 shows only the front and right faces.",
    "Canopy top colour (light grey-white) is inferred from the v3 top edge.",
    "Back canopy wordmark mirrors the front one; the back face is not visible in v3.",
]

(ROOT / "object-sculpt-spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
(ROOT / "di.json").write_text(json.dumps(di, indent=2, ensure_ascii=False) + "\n")
print("spec components:", len(tree), "pump-orange:", PUMP_ORANGE)
