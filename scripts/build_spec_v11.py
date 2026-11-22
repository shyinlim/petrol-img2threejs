"""Rebuild object-sculpt-spec.json from backup/spec_before_v11.json with the v11 edits.
Re-runnable: always restores from the backup first; reviews appended after the backup survive (same rule as build_spec_v10.py)."""
import copy
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = json.loads((ROOT / "archive/backup/spec_before_v11.json").read_text())
cur = json.loads((ROOT / "object-sculpt-spec.json").read_text())
for key in ("reviewHistory", "visualEvidence", "tier1Results"):  # tier1Results too: diagnose_render --in-place appends there
    spec[key] += cur[key][len(spec[key]):]

by = {c["id"]: c for c in spec["componentTree"]}


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
    """Cylinder/box with an attachment in root frame: attachment start/end and position all move to (x, z)."""
    set_att(c, start=[x, None, z], end=[x, None, z]); set_pos(c, x=x, z=z)


def shift_xz(c, dx, dz):
    """Move a part by a delta in its parent's frame (attachment and position together); keeps a leaning trunk leaning."""
    for key in ("localStart", "localEnd"):
        if c.get("attachment"):
            c["attachment"][key][0] += dx; c["attachment"][key][2] += dz
    c["transform"]["position"][0] += dx; c["transform"]["position"][2] += dz


def set_color(mat_id, hexv):
    m = next(m for m in spec["materials"] if m["id"] == mat_id)
    m["baseColor"] = m["color"] = hexv; m["albedo"]["dominant"] = hexv


# 1. Caltex red canopy; the Mart band follows it (start value from brandcolor.dev, not an official spec)
set_color("fascia-orange", "#ED1B2F"); set_color("mart-orange", "#ED1B2F")

# 2. roundel radius 0.6 -> 0.5
r = by["roundel-logo"]; set_att(r, base=0.5, endr=0.5); set_dim(r, w=1.0, d=1.0)
# 2b. user feedback: the roundel stands on the right-hand short face (+z, v3), facing +z, 0.85 in from the corner, not on the corner diagonal
set_att(r, start=[-4.9, 0.5, 6.99], end=[-4.9, 0.5, 7.27]); set_pos(r, x=-4.9, z=7.13)

# 3. deeper front lips: 0.1 -> 0.18 in x, outer face moves out, inner face stays on the canopy face (-5.75)
for lip in ("fascia-lip-top", "fascia-lip-end"):
    set_dim(by[lip], w=0.18); set_pos(by[lip], x=-5.84)

# 4. wheel stops lie ACROSS the 1.2-wide stall (x 1.1, z 0.18) at the stall end away from the other stall of the same line, so a car drives in along z and stops against them
for n in range(1, 9):
    w = by[f"wheel-stop-{n}"]; pump = int(w["parent"][-1]); set_dim(w, w=1.1, d=0.18); set_pos(w, z=2.1 if pump in (1, 3) else -2.1)

# 4b. user: no striped kerbs at all (car route and consistency): drop all 8 wheel stops and kerb-mart. The grass-verge kerbs stay.
spec["componentTree"] = [c for c in spec["componentTree"] if not (c["id"].startswith("wheel-stop-") or c["id"] == "kerb-mart")]

# 4c. user: no second crown on the trees (tree-N-b)
spec["componentTree"] = [c for c in spec["componentTree"] if not (c["id"].startswith("tree-") and c["id"].endswith("-b"))]

# 5. bins and tree swap places along the left verge (tree keeps its lean: shift, not put_xz)
put_xz(by["bin-blue-1"], -6.84, -6.6); put_xz(by["bin-green-1"], -6.84, -5.75)
shift_xz(by["tree-1-trunk"], 0, -0.7 - by["tree-1-trunk"]["attachment"]["localStart"][2])

# 5b. the bins now sit where agave-1 was: slide agave-1, bush-1 and tree-2 forward along the verge to make room (check_layout)
for k in range(1, 6): shift_xz(by[f"agave-1-leaf-{k}"], 0, 0.6)
shift_xz(by["bush-1"], 0, 0.55); set_dim(by["bush-1"], d=0.8); shift_xz(by["tree-2-trunk"], 0, 0.5)  # bush-1 is 0.3 shorter along the verge
for k in range(1, 6): shift_xz(by[f"agave-2-leaf-{k}"], 0, 0.25)

# 5c. one number disc per column (user feedback), centred on the column face
spec["componentTree"] = [c for c in spec["componentTree"] if not c["id"].startswith("column-disc-b-")]
for n in range(1, 5):
    d = by[f"column-disc-{n}"]; set_pos(d, z=0.0); set_att(d, start=[None, None, 0.0], end=[None, None, 0.0])

# 5d. user asked "what is this" about the thin poster strip beside each pump: it floats beside the pump, so remove it (the pump-3 standee stays)
spec["componentTree"] = [c for c in spec["componentTree"] if not c["id"].startswith("pump-poster-")]

# 5e. no CALTEX on the back (+x) face of the canopy (user feedback)
spec["componentTree"] = [c for c in spec["componentTree"] if c["id"] != "canopy-wordmark-back"]

# 6. drop the Mart window rails
spec["componentTree"] = [c for c in spec["componentTree"] if not c["id"].startswith("mart-rail-")]

# 7. user: the left bins go; a Caltex pylon sign stands on the back-left slab corner (clear of the mart and the car lane x -4.6), faces -x
pylon = copy.deepcopy(by["bin-blue-1"]); pylon.update(id="pylon-sign", name="Caltex pylon sign")
pylon["actionProfile"]["destruction"]["fractureGroup"] = "pylon-sign"
set_dim(pylon, w=0.25, h=4.4, d=1.5); set_pos(pylon, x=7.3, y=2.36, z=-8.0); set_att(pylon, start=[7.3, 0.16, -8.0], end=[7.3, 4.56, -8.0])
i = spec["componentTree"].index(by["bin-blue-1"]); spec["componentTree"].insert(i, pylon)
spec["componentTree"] = [c for c in spec["componentTree"] if not re.match(r"^bin-(blue|green)-1(-|$)", c["id"])]

spec["assumptions"].append("v11: the canopy red #ED1B2F comes from brandcolor.dev, not an official spec; the energy-line stripes and the other v11 values are inferred from v3 pixels, not measured.")
# 8. user: bin wheels sit at the back-bottom (+z, logo is on -z) with the axle across the bin width (x), not a roller on the +x side
for k in ("bin-blue-2", "bin-green-2"):
    w = by[k + "-wheels"]; set_att(w, start=[-0.29, -0.335, 0.3], end=[0.29, -0.335, 0.3]); set_pos(w, x=0.0, z=0.3)

# 9. user: CALTEX wordmark a touch lower on the fascia (y 0 -> -0.04)
set_pos(by["canopy-wordmark"], y=-0.04)

# 10. user: fuel nozzles, draped hoses, and beveled/tucked side cabinets
for n in range(1, 5):
    set_pos(by[f"pump-cabinet-{n}"], z=-0.63)
    ct = by[f"pump-cabinet-top-{n}"]
    ct["geometryDescriptor"]["edgeTreatment"]["bevelRadius"] = 0.04
    for side in ("a", "b"):
        by[f"pump-nozzle-{n}{side}"]["geometryDescriptor"]["partStyle"] = "fuel-nozzle"
        by[f"pump-hose-{n}{side}"]["geometryDescriptor"]["partStyle"] = "curved-hose"

# review targets that named the left bins now point at the right-hand pair
out = json.dumps(spec, indent=2, ensure_ascii=False).replace('"bin-blue-1"', '"bin-blue-2"').replace('"bin-green-1"', '"bin-green-2"')
(ROOT / "object-sculpt-spec.json").write_text(out + "\n")
