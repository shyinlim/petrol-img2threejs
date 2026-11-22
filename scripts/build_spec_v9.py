"""Rebuild object-sculpt-spec.json from backup/spec_before_v9.json with the v9 layout and canopy edits.
Re-runnable: always restores from the backup first; reviews appended after the backup survive (same rule as build_spec_v8.py)."""
import copy, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = json.loads((ROOT / "backup/spec_before_v9.json").read_text())
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


# --- Task 2: props out of Mart and out of each other (world positions, root frame; start values, inferred) ---
vc = by["grass-verge-c"]; set_dim(vc, d=1.3); set_pos(vc, z=7.75)
put_xz(by["tree-4-trunk"], 7.35, 7.75)
put_xz(by["tree-3-trunk"], 5.8, 7.8)
put_xz(by["tree-2-trunk"], -6.84, -2.8)
set_pos(by["bush-2"], x=5.0); set_pos(by["bush-4"], x=3.7); set_pos(by["bush-3"], x=-1.2)
put_xz(by["bin-blue-1"], -6.84, -1.1); put_xz(by["bin-green-1"], -6.84, -0.4)

# agaves keep their shape; the group moves by a delta in its verge's frame
for n in (1, 2, 3):
    shift_xz(by[f"agave-2-leaf-{n}"], 0, -0.63)  # world z -1.27 -> -1.9
vb = by["grass-verge-b"]; vb_pos = vb["transform"]["position"]
for n in (1, 2, 3):
    a = by[f"agave-4-leaf-{n}"]
    a["parent"] = "grass-verge-b"; a["attachment"]["parentSocket"] = by["agave-3-leaf-1"]["attachment"]["parentSocket"]
    # old group base in verge-c local (0.6, -0.6); new base in verge-b local so the world base lands on (2.7, 8.0)
    shift_xz(a, (2.7 - vb_pos[0]) - 0.6, (8.0 - vb_pos[2]) + 0.6)

# flags: 1.6 x 0.8, hung at the pole top; flag frame origin is the pole's attachment start (y 0.16), pole top 7.2
put_xz(by["flagpole-2"], 6.4, 8.4)
for flag in ("flag-malaysia", "flag-johor"):
    f = by[flag]; set_dim(f, w=1.6, h=0.8); set_pos(f, x=0.86, y=6.59)

spec["assumptions"].append("Flag size 1.6 x 0.8 and the pole-top hang are inferred from v3 pixel ratios, not measured.")


# --- Task 3: fascia recess (two raised lips), CALTEX next to the roundel, larger roundel (canopy frame, inferred from v3 pixels) ---
def clone(src_id, new_id, name, parent, material):
    c = copy.deepcopy(by[src_id])
    c["id"], c["name"], c["parent"], c["confidence"] = new_id, name, parent, 0.4
    c["dimensions"]["confidence"] = 0.4
    c["material"], c["materialLayers"] = material, [material]
    d = c["actionProfile"]["destruction"]; d["fractureGroup"], d["debrisMaterial"] = new_id, material
    c["topologyRationale"] = f"{name} is a discrete {c['primitive']} part of the station, assembled by contact, not a sculpted shell."
    tree.insert(tree.index(by[src_id]) + 1, c)
    by[new_id] = c
    return c


set_pos(by["canopy-wordmark"], z=4.5)
r = by["roundel-logo"]
set_att(r, start=[None, 0.5, None], end=[None, 0.5, None], base=0.6, endr=0.6)  # v3: diameter ~1.3x fascia height
set_dim(r, w=1.2, d=1.2); set_pos(r, y=0.5)
lip = clone("canopy-wordmark", "fascia-lip-top", "Fascia top lip", "canopy", "fascia-orange")
set_dim(lip, w=0.1, h=0.14, d=14.0); set_pos(lip, -5.80, 0.38, 0)
lip = clone("fascia-lip-top", "fascia-lip-end", "Fascia end lip", "canopy", "fascia-orange")
set_dim(lip, w=0.1, h=0.9, d=0.14); set_pos(lip, -5.80, 0, -6.93)
spec["assumptions"].append("Fascia recess is two raised lips (depth 0.1, top and -z end); the depth is inferred from v3.")

(ROOT / "object-sculpt-spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
print("spec components:", len(tree))
