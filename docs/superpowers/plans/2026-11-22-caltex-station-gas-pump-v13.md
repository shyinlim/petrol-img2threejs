# Caltex Techron 三槍加油機 (Diesel / 黃色 95 / 97) Implementation Plan (v13)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將場景中 4 台加油機 (`pump-1` 到 `pump-4`) 升級為參考圖中的 Caltex Techron 三槍加油機款式：門型鏤空立柱、中段藍底 `BUSINESS SOLUTIONS` 小牌、黑底計價與油品選取面板、三組正面銀框嵌槽與三色油槍（左綠 Diesel、中黃 95、右紅 97）、斜切青白 `with TECHRON` 頂部燈箱，以及側邊 `It's all about you.` 紅白展示矮櫃，且不破壞任何既有驗收腳本與 `/?gate=1` 顏色基準。

**Architecture:** 先寫 `scripts/check_pump_v13.py` 驗證三槍加油機的幾何結構、三色油槍 (綠 `#1b8a3d` / 黃 `#f2c230` / 紅 `#d8372b`)、Canvas 貼圖像素、中段鏤空與 `/?gate=1` 相容性 (先跑紅燈)。接著在 `src/pumpParts.ts` 集中實作三槍加油機的 procedural 3D 子件與 5 張 Canvas 2D 貼圖（頂部 `with TECHRON` 編號燈箱、中段 `BUSINESS SOLUTIONS` 小牌、黑底計價面板、機身正面三色帶與左下半顆星、側邊矮櫃海報），並由 `src/customizeModel.ts` 在 `!gate` 模式下掛載到 `pump-1..4`，確保 `src/customizeModel.ts` (≤260 行) 與 `src/textures.ts` (≤220 行) 完全不超標，且 `/?gate=1` 的 `color_check.py` (pump-orange dE ≤ 12) 維持原狀。

**Tech Stack:** three 0.187.0、Vite 8.3.8、TypeScript 7.0.2、Python 3 + Playwright + Pillow。

**Spec:** 本對話 2026-11-22 22:57 使用者上傳的 Caltex Techron 三槍加油機參考圖 (`uploaded_media_1795359429068.jpg`) 與 22:59 指定規格（「中黑 Silver 改成黃色 95」）。建模規格為 `object-sculpt-spec.json`，架構規範見 `AGENTS.md`。

## Global Constraints

- `src/createCaltexStationModel.ts` 不可手改；若不改 `object-sculpt-spec.json` 則不需重生，所有加油機視覺細節透過 `src/pumpParts.ts` 在 runtime 對 `pump-1..4` 擴充子 mesh 與貼圖。
- **嚴守 `check_refactor.py` 行數上限**：`src/main.ts` ≤ 120 行、`src/scene.ts` ≤ 130 行、`src/textures.ts` ≤ 220 行、`src/customizeModel.ts` ≤ 260 行、`src/ui.ts` ≤ 220 行、`src/car.ts` ≤ 90 行。`src/pumpParts.ts` 維持 ≤ 260 行。
- **嚴守 `/?gate=1` 凍結原則**：新貼圖與三槍子組件只在 `!gate` (normal mode) 套用，或確保 `/?gate=1` 下 `pump-1` 的 `pump-orange` 投影顏色完全不變 (`python3 scripts/color_check.py` CIE76 dE ≤ 12，目前 2.4)。
- **嚴守既有節點相容性**：`pump-nozzle-Na/Nb`、`pump-hose-Na/Nb`、`pump-cabinet-N`、`pump-cabinet-top-N`、`pump-panel-N`、`pump-screen-N`、`pump-head-N`、`pump-sign-N`、`pump-pillar-Na/Nb` 的 `sculptComponent.id` 與父子關係不可刪除，確保 `check_details.py --round 3`、`check_grounded.py` 與 `check_part_coverage.py` 100% 通過。
- **效能預算**：gate draw calls ≤ 260，normal draw calls ≤ 520，triangles ≤ 250,000 (`python3 scripts/check_scene.py`)。新增的三槍子 mesh 一律設定 `castShadow = false` 並共用幾何與材質以節省 draw calls。
- **顏色選色器連動 (`#c-pump`)**：機身正面與矮櫃下半部保留使用或同步 `pump-orange` 材質的顏色，或讓 `#c-pump` 選色器仍能正常改變加油機主體顏色。

## Review Focus

1. `src/customizeModel.ts` 目前剛好 260 行（上限 260 行）：任何在 `customizeModel.ts` 新增的行數都會讓 `python3 scripts/check_refactor.py` 失敗。必須將 `customizeModel.ts` 內對 `applyPumpPartGeometry` 的呼叫替換為單行 `customizePumps(model, gate)`，把所有加油機細節邏輯封裝在 `src/pumpParts.ts`。
2. `/?gate=1` 下 `scripts/color_check.py` 會擷取 `pump-1` 投影範圍內的橘紅像素計算 median 與 dE76：若在 `gate=true` 時把 `pump-1` 正面換成含大面積銀色槍槽、綠黃紅標籤或白底漸層的貼圖，會稀釋或偏移橘色像素導致 `color_check.py` 失敗。因此 `customizePumps(model, gate)` 在 `gate === true` 時只跑原有的 `applyPumpPartGeometry`，所有三槍視覺升級僅在 `!gate` 啟用。
3. 中段門型鏤空視覺：原本 `pump-panel-N` (高 0.7, y=0.8) 幾乎填滿 `pump-1` (頂 y=0.45) 到 `pump-head-1` (底 y=1.625) 的空間。在 `!gate` 下需將 `pump-panel-N` 高度壓扁為計價黑面板 (高 0.34, y=0.62)，騰出 `y = 0.79 .. 1.62` 的門型鏤空區，並在 `y = 0.94` 立起藍底 `BUSINESS SOLUTIONS` 小牌。
4. 雙面加油島方向：場景中的加油機正面朝 `-x` (與雨棚正面同向，背面朝 `+x`)。三組正面槍槽、三色油槍 (綠 Diesel / 黃 95 / 紅 97)、計價黑面板、頂部 `with TECHRON` 編號與小廣告牌必須同時顯示在 `-x` (正面) 與 `+x` (背面)，而原本掛在 `±z` 兩側的舊 `pump-nozzle-Na/Nb` 與 `pump-hose-Na/Nb` 在 `!gate` 下縮小隱藏進機身內（保留節點與 bounding box 在 `y >= 0.15` 以通過 `check_details.py` 與 `check_grounded.py`）。
5. 頂部燈箱編號 `1`..`4`：參考圖右上角有紅色數字 `1`，`pump-1` 到 `pump-4` 的頂部燈箱 (`pump-head-N` 與 `pump-sign-N`) 應分別顯示對應的 `1`、`2`、`3`、`4`。

---

### Task 1: 建立三槍加油機驗收腳本 `scripts/check_pump_v13.py` (先紅燈)

**Files:**
- Create: `scripts/check_pump_v13.py`

**Interfaces:**
- Consumes: `http://localhost:5173/` (`window.__IMG2THREEJS_VIEWER__`)。
- Produces: `python3 scripts/check_pump_v13.py`，exit 0 代表 4 台加油機在 normal mode 具備門型鏤空、`BUSINESS SOLUTIONS` 小牌、三組銀框槍槽、綠/黃/紅三支油槍與軟管、更新後的頂部燈箱與側櫃貼圖，且 `/?gate=1` 完全不受影響。

- [ ] **Step 1: 撰寫 `scripts/check_pump_v13.py`**

```python
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
      const out = { pumps: 0, bays: 0, nozzles: [], topper: 0, gapOk: true, signTexOk: false };
      for (let n = 1; n <= 4; n++) {
        let p = null, panel = null, head = null;
        v.scene.traverse(o => {
          if (!o.isMesh && o.userData?.sculptComponent?.id === `pump-${n}`) p = o;
          if (o.isMesh && o.userData?.sculptComponent?.id === `pump-panel-${n}`) panel = o;
          if (o.isMesh && o.userData?.sculptComponent?.id === `pump-head-${n}`) head = o;
        });
        if (!p || !panel || !head) continue;
        out.pumps++;
        // Check hollow portal gap between panel top and head bottom
        panel.updateWorldMatrix(true, false); panel.geometry.computeBoundingBox();
        head.updateWorldMatrix(true, false); head.geometry.computeBoundingBox();
        const pTop = panel.geometry.boundingBox.clone().applyMatrix4(panel.matrixWorld).max.y;
        const hBot = head.geometry.boundingBox.clone().applyMatrix4(head.matrixWorld).min.y;
        if (hBot - pTop < 0.45) out.gapOk = false;
        p.traverse(c => {
          if (c.name === `pump-bay-${n}`) out.bays++;
          if (c.name === `pump-topper-${n}`) out.topper++;
          if (c.name?.startsWith(`pump-front-nozzle-${n}-`)) {
            out.nozzles.push(c.material.color.getHexString());
          }
        });
        const hm = [].concat(head.material)[0];
        if (n === 1 && hm?.map?.image?.width === 1024) out.signTexOk = true;
      }
      return out;
    }""")
    check("P1:4-pumps-found", res["pumps"] == 4, f"pumps={res['pumps']}")
    check("P2:hollow-portal-gap", res["gapOk"], f"gapOk={res['gapOk']} (need >= 0.45 between panel top and head bottom)")
    check("P3:topper-signs", res["topper"] == 4, f"topper={res['topper']} (want 4 BUSINESS SOLUTIONS signs)")
    check("P4:three-bays-per-pump", res["bays"] >= 12, f"bays={res['bays']} (want >= 12 bay recesses across 4 pumps)")
    # Green (#1b8a3d), Yellow 95 (#f2c230), Red 97 (#d8372b)
    want_cols = {"1b8a3d", "f2c230", "d8372b"}
    got_cols = set(res["nozzles"])
    check("P5:nozzle-colors-green-yellow95-red97", want_cols.issubset(got_cols) and len(res["nozzles"]) >= 12,
          f"count={len(res['nozzles'])} colors={sorted(got_cols)}")
    check("P6:head-sign-texture", res["signTexOk"], f"signTexOk={res['signTexOk']}")

sys.exit(1 if fails else 0)
```

- [ ] **Step 2: 執行 `scripts/check_pump_v13.py` 確認先失敗 (紅燈)**

Run: `python3 scripts/check_pump_v13.py`
Expected: FAIL on `P2:hollow-portal-gap`, `P3:topper-signs`, `P4:three-bays-per-pump`, `P5:nozzle-colors-green-yellow95-red97`.

- [ ] **Step 3: Commit 測試腳本**

```bash
git add scripts/check_pump_v13.py
git commit -m "test: add check_pump_v13.py for 3-nozzle Caltex Techron gas pump (red)"
```

---

### Task 2: 在 `src/pumpParts.ts` 實作三槍加油機貼圖與 3D 組件，並接入 `src/customizeModel.ts`

**Files:**
- Modify: `src/pumpParts.ts:1-44`
- Modify: `src/customizeModel.ts:129-192`

**Interfaces:**
- Consumes: `src/textures.ts` (`canvasTex`)。
- Produces:
  - `src/pumpParts.ts`:
    - `export function applyPumpPartGeometry(mesh: THREE.Mesh, partStyle: string): void` (保留原有簽名供 gate mode 與相容性使用)
    - `export function pumpHeadNumberTex(n: number): THREE.CanvasTexture` (1024×353：左深青 `#0b5563` 斜切、白底黑邊紅星 roundel、中右 `with TECHRON` 藍字、右上紅字編號 `n`)
    - `export function customizePumps(model: THREE.Object3D, gate: boolean): void`

- [ ] **Step 1: 在 `src/pumpParts.ts` 實作 5 張貼圖與三槍幾何組裝 `customizePumps(model, gate)`**

在 `src/pumpParts.ts` 中實作（全檔控制在 ≤ 240 行）：
1. **`pumpHeadNumberTex(n: number)`** (1024×353)：
   - 白色底 `#f4f4f2`，外框淺灰邊；左上到左下深青色 `#0b5563` 斜切梯形 (`(0,0) -> (540,0) -> (180,353) -> (0,353)`) 加一條細白斜線分割；右上角深青色橫條 (`(555,0) -> (1024,0) -> (1024,52) -> (510,52)`)。
   - 載入 `decals/caltex_roundel.png` 畫在 `(215, 75, 210, 210)`。
   - 中間偏右畫藍色 `#1b5299` `with` 與粗體 `TECHRON`，右上角 `(945, 115)` 畫紅色 `#d8372b` 粗體編號 `String(n)`。
2. **`pumpBodyFrontTex()`** (512×640)：
   - 上半紅底 `#e52521`、中段柔和暖光漸層 `#ff7350`、底部深灰踢腳線 `#1d1d1d`。
   - 頂部三色油品橫幅 (高 76 px)：
     - 左三分之一：綠底 `#1b8a3d`，白字 `Diesel` 與 `with Techron D`。
     - 中三分之一：黃底 `#f2c230`，黑字 `Premium 95` 與 `with Techron`。
     - 右三分之一：紅底 `#b31919`，白字 `Platinum 97` 與 `with Techron`。
   - 各槍槽右上方畫三個黃底黑框辛烷值小標：`B10`、`95`、`97`。
   - 左下角畫半顆白底紅星 Caltex 標誌與右下角白色斜切弧塊 + `TECHRON` 字樣。
3. **`pumpMeterPanelTex()`** (512×256)：
   - 深黑灰底 `#22252a`，頂部銀色金屬橫條 `#c8cdd2`。
   - 左側刷卡/鍵盤區 (銀灰小方格鍵盤 + 小螢幕)，中央雙行紅黃亮字計價視窗 (`TOTAL SALE 85.00`、`LITRES 41.46`)，計價視窗下方三顆油品選取方鍵：左綠 `#1b8a3d`、中黃 `#f2c230`、右紅 `#d8372b`。
4. **`pumpTopperTex()`** (512×220)：
   - 銀黑外框 `#2b2e33`，水藍色漸層底 `#7ec8f2` -> `#5bb3e8`，左側小號 Caltex 星標與 `CALTEX`，右側深灰斜體粗字 `BUSINESS SOLUTIONS` 與紅色小箭頭。
5. **`pumpCabinetPosterTex()`** (512×768)：
   - 上方 68% 藍天漸層海報區 (`#56a3d9` -> `#d8ecf8`)，寫白色斜體 `It's all about you.`、`For you. With You.`、底部紅斜帶 `ENJOY THE JOURNEY CALTEX`；下方 32% 亮紅底座 `#e52521` 中央帶暖白高光。
6. **`customizePumps(model: THREE.Object3D, gate: boolean)`**：
   - 先對所有帶 `partStyle` 的 mesh 呼叫 `applyPumpPartGeometry(o, ps)`。
   - 若 `gate` 為 `true`，直接 `return`（確保 `/?gate=1` 100% 零變更）。
   - 若 `!gate`，對 `n = 1..4` 的每台 `pump-${n}`：
     - **門型鏤空與計價黑面板**：把 `pump-panel-${n}` 的 `scale.y` 調整為 `0.36 / 0.7`、`position.y = 0.63`，±x 面套用 `pumpMeterPanelTex()`；把 `pump-screen-${n}` 縮小藏入面板內 (`scale.set(0.2, 0.2, 0.2)`)。
     - **兩側銀色立柱**：把 `pump-pillar-${n}a` 與 `pump-pillar-${n}b` 的 `position.x` 設為 `0`、`scale.x` 設為 `0.48 / 0.22`，材質設為銀灰金屬 (`#c4c9ce`, `roughness: 0.35`, `metalness: 0.3`)，形成包夾機身與頂部燈箱的雙立柱。
     - **中段 `BUSINESS SOLUTIONS` 小牌**：在 `pump-${n}` 下新增 `name = "pump-topper-" + n` 的 `BoxGeometry(0.06, 0.24, 0.44)`，置於 `(0, 0.94, 0)`（貼在黑面板頂部 `y = 0.81` 上方，置於門型鏤空區中央），±x 面套用 `pumpTopperTex()`。
     - **機身正面三色帶與紅底貼圖**：把 `pump-${n}` mesh 的 ±x 面換成帶 `pumpBodyFrontTex()` 的 `MeshStandardMaterial`（其餘面維持原本的 `pump-orange` 材質以供 `#c-pump` 選色器連動）。
     - **三組正面銀框槍槽 + 綠/黃/紅三支油槍與彎管**：
       - 對三個槽位 `zSlot of [-0.21, 0, 0.21]`，對應顏色 `col of [0x1b8a3d, 0xf2c230, 0xd8372b]` (綠 Diesel、黃 95、紅 97)：
       - 在 `pump-${n}` 新增銀色凹槽框 `name = "pump-bay-" + n` (`BoxGeometry(0.53, 0.36, 0.13)` at `(0, -0.02, zSlot)`) 與深灰內襯 (`BoxGeometry(0.54, 0.31, 0.09)` at `(0, -0.02, zSlot)`)。
       - 在正面 (`x = -0.27`) 與背面 (`x = +0.27`) 各掛一支對應顏色的油槍握把 `name = "pump-front-nozzle-" + n + "-" + idx` (`BoxGeometry(0.05, 0.19, 0.045)`，傾斜 `rotation.z = ±0.25`，材質顏色為 `col`) 與黑色短垂管 (`CylinderGeometry(0.014, 0.014, 0.16, 8)` at `y = -0.10`)。
     - **隱藏舊的側面雙槍與雙管（保留節點防壞）**：將 `pump-nozzle-${n}a/b` 與 `pump-hose-${n}a/b` 的 `scale.set(0.05, 0.05, 0.05)` 並移到 `position.set(0, 0.1, 0)` 藏進機身內部，既不穿幫又能通過 `check_details.py` 的父子與 live bbox 檢查。
     - **頂部編號燈箱**：把 `pump-head-${n}` 與 `pump-sign-${n}` 的 `-x` / `+x` 招牌面換成 `pumpHeadNumberTex(n)`。
     - **側邊展示矮櫃**：把 `pump-cabinet-${n}` 位置微調至 `(0, -0.08, -0.66)`，`-x` 與 `+x` 面套用 `pumpCabinetPosterTex()`，頂蓋 `pump-cabinet-top-${n}` 改為薄銀框邊 (`scale.y = 0.06 / 0.25`, `position.y = 0.36`)。

- [ ] **Step 2: 更新 `src/customizeModel.ts` 接入 `customizePumps(model, gate)`**

在 `src/customizeModel.ts`：
1. 將 `import { applyPumpPartGeometry } from './pumpParts';` 改為 `import { customizePumps } from './pumpParts';`。
2. 將第 129 行 `model.traverse((o: any) => { const ps = o.userData?.sculptComponent?.geometryDescriptor?.partStyle; if (o.isMesh && ps) applyPumpPartGeometry(o, ps); });` 替換為 `customizePumps(model, gate);`（行數不增反減，維持 ≤ 260 行）。

- [ ] **Step 3: 跑 `check_pump_v13.py`、`check_refactor.py` 與 TypeScript 編譯 (綠燈)**

Run: `npx tsc --noEmit && python3 scripts/check_refactor.py && python3 scripts/check_pump_v13.py`
Expected: 全部 PASS，exit 0。

- [ ] **Step 4: Commit 程式碼**

```bash
git add src/pumpParts.ts src/customizeModel.ts
git commit -m "feat(pump): upgrade gas pumps to 3-nozzle Caltex Techron design (Diesel, Yellow 95, Red 97)"
```

---

### Task 3: 執行全套迴歸驗收與視覺截圖確認

**Files:**
- Modify: `.img2threejs/ledger.md` (加一行 v13 紀錄)

**Interfaces:**
- Consumes: Task 1–2 的修改。
- Produces: 全套 14 支驗收腳本綠燈與加油機近景截圖 `shots/v13_pump_closeup.png`。

- [ ] **Step 1: 跑全套既有驗收腳本確認零破壞**

Run:
```bash
npm run build && \
python3 scripts/check_refactor.py && \
python3 scripts/check_pump_v13.py && \
python3 scripts/check_ui.py && \
python3 scripts/check_v11.py --task 3 && \
python3 scripts/check_details.py --round 3 && \
python3 scripts/check_layout.py && \
python3 scripts/check_scene.py && \
python3 scripts/check_grounded.py && \
python3 scripts/check_final.py && \
python3 scripts/check_hue.py
```
Expected: 全部 exit 0。

- [ ] **Step 2: 擷取加油機特寫截圖 `shots/v13_pump_closeup.png` 並目視檢查**

Run:
```bash
python3 -c '
import sys; sys.path.insert(0, "scripts")
from _viewer import gate_page, set_camera
with gate_page("", viewport=(1280, 800)) as page:
    page.evaluate("document.getElementById(\"panel\").style.display = \"none\"")
    set_camera(page, dict(azimuth=-78, elevation=6, distance=6.5, fov=28, target=[-3.0, 1.35, 4.1]))
    page.wait_for_timeout(500)
    page.screenshot(path="shots/v13_pump_closeup.png")
'
```
Expected: 產生 `shots/v13_pump_closeup.png`，畫面清楚呈現頂部 `with TECHRON 1`、門型鏤空區 `BUSINESS SOLUTIONS` 小牌、計價黑面板、三色油品帶與綠/黃/紅三支油槍、左下半顆星以及側邊 `It's all about you.` 矮櫃。

- [ ] **Step 3: 更新 `.img2threejs/ledger.md` 並 commit**

```bash
git add .img2threejs/ledger.md
git commit -m "docs: record v13 3-nozzle Caltex Techron pump upgrade in ledger"
```
