"""Verify v13 Caltex Techron 3-nozzle gas pump upgrade in normal mode and gate invariance."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _viewer import gate_page

fails = []


def check(name: str, ok: bool, msg: str) -> None:
    print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
    if not ok:
        fails.append(name)


with gate_page("", viewport=(1280, 800)) as page:
    res = page.evaluate("""() => {
      const v = window.__IMG2THREEJS_VIEWER__;
      const out = { pumps: 0, bays: 0, topper: 0, gapOk: true, screenHidden: true,
                    signUuids: [], negXOrder: [], posXOrder: [] };
      for (let n = 1; n <= 4; n++) {
        let p = null, panel = null, head = null, sign = null, scr = null;
        v.scene.traverse(o => {
          const id = o.userData?.sculptComponent?.id;
          if (!o.isMesh && id === `pump-${n}`) p = o;
          if (o.isMesh && id === `pump-panel-${n}`) panel = o;
          if (o.isMesh && id === `pump-head-${n}`) head = o;
          if (o.isMesh && id === `pump-sign-${n}`) sign = o;
          if (!o.isMesh && id === `pump-screen-${n}`) scr = o;
        });
        if (!p || !panel || !head) continue;
        out.pumps++;
        panel.updateWorldMatrix(true, false); panel.geometry.computeBoundingBox();
        head.updateWorldMatrix(true, false); head.geometry.computeBoundingBox();
        const pTop = panel.geometry.boundingBox.clone().applyMatrix4(panel.matrixWorld).max.y;
        const hBot = head.geometry.boundingBox.clone().applyMatrix4(head.matrixWorld).min.y;
        if (hBot - pTop < 0.70) out.gapOk = false;
        if (scr && Math.abs(scr.position.x) > 0.01) out.screenHidden = false;
        const sm = [].concat(sign?.material || []).find(m => m?.map?.image?.width === 1024);
        if (sm?.map?.uuid) out.signUuids.push(sm.map.uuid);
        const negX = [], posX = [];
        p.traverse(c => {
          if (c.name === `pump-bay-${n}`) out.bays++;
          if (c.name === `pump-topper-${n}`) out.topper++;
          if (c.name?.startsWith(`pump-front-nozzle-${n}-`)) {
            const entry = { z: c.position.z, hex: c.material.color.getHexString() };
            if (c.position.x < 0) negX.push(entry); else posX.push(entry);
          }
        });
        negX.sort((a, b) => a.z - b.z);
        posX.sort((a, b) => a.z - b.z);
        out.negXOrder.push(negX.map(e => e.hex).join(','));
        out.posXOrder.push(posX.map(e => e.hex).join(','));
      }
      return out;
    }""")
    check("P1:4-pumps-found", res["pumps"] == 4, f"pumps={res['pumps']}")
    check("P2:hollow-portal-gap", res["gapOk"], f"gapOk={res['gapOk']} (need >= 0.70 between panel top and head bottom)")
    check("P3:topper-signs", res["topper"] == 4, f"topper={res['topper']} (want 4 BUSINESS SOLUTIONS signs)")
    check("P4:three-bays-per-pump", res["bays"] >= 12, f"bays={res['bays']} (want >= 12 bay recesses across 4 pumps)")
    want_neg = "1b8a3d,f2c230,d8372b"
    want_pos = "d8372b,f2c230,1b8a3d"
    check("P5:nozzle-order-both-sides",
          len(res["negXOrder"]) == 4 and all(x == want_neg for x in res["negXOrder"]) and all(x == want_pos for x in res["posXOrder"]),
          f"-x={res['negXOrder'][0] if res['negXOrder'] else None} +x={res['posXOrder'][0] if res['posXOrder'] else None}")
    check("P6:distinct-numbered-signs", len(set(res["signUuids"])) == 4, f"distinct={len(set(res['signUuids']))}")
    check("P7:screen-hidden-inside-panel", res["screenHidden"], f"screenHidden={res['screenHidden']}")

with gate_page("?gate=1") as gp:
    gres = gp.evaluate("""() => {
      const v = window.__IMG2THREEJS_VIEWER__;
      let extra = 0, panelH = 0;
      v.scene.traverse(o => {
        if (/^pump-(bay|topper|front-nozzle)-/.test(o.name || '')) extra++;
        if (o.isMesh && o.userData?.sculptComponent?.id === 'pump-panel-1') {
          o.geometry.computeBoundingBox();
          const b = o.geometry.boundingBox;
          panelH = (b.max.y - b.min.y) * o.scale.y;
        }
      });
      return { extra, panelH };
    }""")
    check("G1:gate-invariance", gres["extra"] == 0 and abs(gres["panelH"] - 0.7) < 0.02,
          f"extra={gres['extra']} panelH={gres['panelH']:.3f}")

sys.exit(1 if fails else 0)
