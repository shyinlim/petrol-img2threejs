# Caltex 加油站 Diorama 程式碼架構重構與 README Implementation Plan (v12)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 636 行單檔全包的 `src/main.ts` 拆解為職責清晰、易讀的 5 個 TypeScript 模組，補齊 `package.json` 常用啟動指令與完整 `README.md`，且不改動任何 3D 幾何、畫面表現與既有 Python 驗收腳本。

**Architecture:** 先寫結構檢查腳本 `scripts/check_refactor.py` 驗證模組拆分、行數上限、`package.json` scripts 與 `README.md` 必備章節 (先跑紅燈)。接著依職責將 `src/main.ts` 拆成 `src/scene.ts` (場景、相機、燈光)、`src/textures.ts` (12 種 Canvas 2D 與 SVG 貼圖)、`src/customizeModel.ts` (模型倒角、材質覆寫、陰影、旗幟飄動) 與 `src/ui.ts` (控制面板、選色、Raycaster 零件抬升、工具列)，最後由 `src/main.ts` 組裝並掛載 `__IMG2THREEJS_*` 全域測試介面。根目錄的 `.img2threejs/state.json` evidence 檔案與 `material-evidence/` 原路徑保留不動，確保所有既有 gate 100% 綠燈。

**Tech Stack:** three 0.187.0、Vite 8.3.8、TypeScript 7.0.2、Python 3 + Playwright。

**Spec:** 本對話 2026-11-22 22:06 使用者需求（「全部架構做整理、好讀的程式架構、要有 README.md、code 要跑得起來」）。建模規格為 `object-sculpt-spec.json`，前一版計畫為 `docs/superpowers/plans/2026-11-22-caltex-station-img2threejs-v11.md`。

## Global Constraints

- `src/createCaltexStationModel.ts` (6328 行自動生成檔) 與 `src/car.ts` (73 行獨立車輛模組) 不改動。
- 根目錄 `object-sculpt-spec.json`、`parts.json`、`material-evidence/`、`reference/`、`shots/`、`analysis.md`、`admission.json`、`assessment.json`、`di.json` 路徑不可搬移 (`.img2threejs/state.json` 與 `scripts/*.py` 直接依賴)。
- **純重構零行為變更**：Normal mode 與 Gate mode (`?gate=1`)、Clay mode (`?clay=1`) 的鏡頭、光線、貼圖、互動、動畫與全域 hook (`window.__IMG2THREEJS_VIEWER__`、`window.__IMG2THREEJS_CAPTURE__`、`window.__IMG2THREEJS_PICK__`、`window.__IMG2THREEJS_READY__`、`window.__CAR_T__`) 必須與重構前完全一致。
- 拆分後的 `src/main.ts` 行數上限 ≤ 120 行；`src/scene.ts`、`src/textures.ts`、`src/customizeModel.ts`、`src/ui.ts` 單檔皆 ≤ 260 行。
- 開工前先把目前 working tree 的未提交修改 commit 或打 git tag `pre-v12-refactor`，每個 Task 完成後 commit 一次。
- 每個 Task 完成後複製新的 `docs/summary/yyyymmddhhmmss_plan_summary.md` (把完成的步驟 `[ ]` 改 `[x]` 並在行尾加 `2026-11-22 HH:MM` 時間戳)，`.img2threejs/ledger.md` 加一行紀錄。
- 既有檢查在拆分完成後必須全過：`npx tsc --noEmit`、`npx vite build`、`python3 scripts/check_ui.py`、`python3 scripts/check_v11.py --task 3`、`python3 scripts/check_details.py --round 3`、`python3 scripts/check_orbit.py`、`python3 scripts/check_layout.py`、`python3 scripts/check_canopy.py`、`python3 scripts/check_scene.py`、`python3 scripts/check_soil.py`、`python3 scripts/check_hue.py`、`python3 scripts/check_view.py`、`python3 scripts/check_final.py`、`python3 scripts/check_grounded.py`、`python3 scripts/color_check.py`。

## Review Focus

1. `c-canopy` 與 `c-pump` 選色器依賴模型材質未被陣列覆寫前的原始 `baseColors` 與 `orangeSpec`：`customizeModel` 必須在把單一材質換成多面材質陣列**之前**先收集 `baseColors` 與 `orangeSpec` 並回傳給 `ui.ts`，否則 `check_hue.py` 會失敗。
2. 零件 hover / select 發光 (`origMat`) 與草地選色器 (`c-grass`) 的互動：當草地正在發光時改草地顏色，`grassMats()` 必須透過 `origMat.get(o) ?? o.material` 找原始材質，所以 `origMat` Map 必須由 `ui.ts` 內部統一管理。
3. 視窗縮放與窄視窗 (`w() < 900`) 的 `applyViewOffset()`：`scene.ts` 暴露 `applyViewOffset()` 與 `resize()`，在 `applyCamera()` 與 window `resize` 事件中都要呼叫，`check_v11.py` 斷言 A1 與 A6 會驗證。
4. Top-level `await` 相容性：`customizeModel.ts` 載入 `decals/caltex_wordmark.svg` 使用 `await new SVGLoader().loadAsync(...)`，因此匯出為 `async function customizeModel(...)`，在 `src/main.ts` 以 top-level `await customizeModel(...)` 呼叫，確保 `__IMG2THREEJS_READY__ = true` 在 3D 字載入完成後才觸發。
5. `window.__CAR_T__` 截圖凍結時鐘：render loop 必須維持 `car.update((window as any).__CAR_T__ ?? carClock)`，不可寫死 `carClock`。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你要做什麼 |
| --- | --- | --- |
| 0 | 開工前 | 審閱本 plan 與 `docs/summary/` 初始摘要，選執行方式 (Subagent-driven 或 Native) |
| A | Task 5 | 看重構後 `src/` 5 個檔案結構、`README.md` 與全部驗收腳本綠燈結果 |

---

### Task 1: 建立架構重構檢查腳本 `scripts/check_refactor.py` (先紅燈)

**Files:**
- Create: `scripts/check_refactor.py`

**Interfaces:**
- Consumes: 專案檔案系統 (`package.json`、`README.md`、`src/*.ts`)。
- Produces: `python3 scripts/check_refactor.py`，exit 0 代表檔案拆分、行數限制、`package.json` scripts 與 `README.md` 皆符合規範。

- [ ] **Step 1: 保存重構前基準並打 git tag `pre-v12-refactor`**

Run: `git status -s` (若有未 commit 的 v11 變更先 `git commit -am "chore: save v11 working state before v12 refactor"`，再 `git tag pre-v12-refactor`)

- [ ] **Step 2: 撰寫 `scripts/check_refactor.py`**

```python
"""Verify v12 codebase refactoring: modular src/ files, line limits, package.json scripts, and README.md sections."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails = []


def check(name: str, ok: bool, msg: str) -> None:
    print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
    if not ok:
        fails.append(name)


# R1: Modular src/ files and line counts
expected_limits = {
    "src/main.ts": 120,
    "src/scene.ts": 130,
    "src/textures.ts": 220,
    "src/customizeModel.ts": 260,
    "src/ui.ts": 220,
    "src/car.ts": 90,
}
for rel, limit in expected_limits.items():
    p = ROOT / rel
    if not p.exists():
        check(f"file:{rel}", False, "missing")
    else:
        lines = len(p.read_text().splitlines())
        check(f"file:{rel}", lines <= limit, f"{lines} lines (limit <= {limit})")

# R2: package.json scripts
pkg = json.loads((ROOT / "package.json").read_text())
scripts = pkg.get("scripts", {})
for s in ("dev", "build", "preview"):
    check(f"pkg:script:{s}", s in scripts, f"scripts[{s!r}] = {scripts.get(s)!r}")

# R3: README.md existence and key sections
readme = ROOT / "README.md"
if not readme.exists():
    check("readme:exists", False, "README.md missing")
else:
    text = readme.read_text()
    check("readme:exists", len(text) >= 400, f"{len(text)} chars")
    for token in ("npm run dev", "src/scene.ts", "src/textures.ts", "src/customizeModel.ts", "src/ui.ts", "?gate=1", "check_ui.py"):
        check(f"readme:{token}", token in text, f"contains {token!r}")

sys.exit(1 if fails else 0)
```

- [ ] **Step 3: 跑 `scripts/check_refactor.py` 確認先失敗 (紅燈)**

Run: `python3 scripts/check_refactor.py`
Expected: FAIL on `file:src/main.ts` (636 lines > 120), missing `src/scene.ts`, `src/textures.ts`, `src/customizeModel.ts`, `src/ui.ts`, missing `pkg:script:dev/build/preview`, and missing `README.md`.

- [ ] **Step 4: Commit 並更新 summary 與 ledger**

```bash
git add scripts/check_refactor.py
git commit -m "test: add check_refactor.py for v12 modular architecture and README (red)"
```

---

### Task 2: 抽出場景與燈光模組 `src/scene.ts` 及貼圖生成模組 `src/textures.ts`

**Files:**
- Create: `src/scene.ts`、`src/textures.ts`

**Interfaces:**
- Consumes: `three`、`three/addons/controls/OrbitControls.js`、`three/addons/environments/RoomEnvironment.js`。
- Produces:
  - `src/scene.ts`:
    - `export type LookState = { exposure: number; envIntensity: number; sunAz: number; sunEl: number; shadowRadius: number; bg: string; wind: number };`
    - `export type CameraRig = { azimuth: number; elevation: number; distance: number; fov: number; target: THREE.Vector3 };`
    - `export function createSceneContext(gate: boolean): { stage: HTMLElement; w: () => number; h: () => number; renderer: THREE.WebGLRenderer; scene: THREE.Scene; camera: THREE.PerspectiveCamera; cam: CameraRig; controls: OrbitControls; look: LookState; applyViewOffset: () => void; applyCamera: () => void; applyLook: () => void; resize: () => void }`
  - `src/textures.ts`:
    - `export function decalTex(url: string, flip?: boolean, rot?: number): THREE.Texture`
    - `export function martText(): THREE.CanvasTexture`
    - `export function canvasTex(w: number, h: number, draw: (g: CanvasRenderingContext2D) => void): THREE.CanvasTexture`
    - `export function pumpSignTex(): THREE.CanvasTexture`
    - `export function stripeTex(len: number, top: boolean): THREE.CanvasTexture`
    - `export function soffitTex(gate: boolean): THREE.CanvasTexture`
    - `export function soffitGlowTex(gate: boolean): THREE.CanvasTexture`
    - `export function numberTex(n: number): THREE.CanvasTexture`
    - `export function posterTex(): THREE.CanvasTexture`
    - `export function standeeTex(): THREE.CanvasTexture`
    - `export function recycleTex(bg: string): THREE.CanvasTexture`
    - `export function pylonTex(): THREE.CanvasTexture`
    - `export function martFaceTex(widthU: number, heightU: number, white: string, door: boolean): THREE.CanvasTexture`
    - `export function stallTex(box: THREE.Box3, pumps: THREE.Vector3[], base: string): THREE.CanvasTexture`
    - `export function soilTex(widthU: number, heightU: number, seed: number): THREE.CanvasTexture`
    - `export function glassTex(base: string): THREE.CanvasTexture`
    - `export function energyLinesTex(): THREE.CanvasTexture`

- [ ] **Step 1: 建立 `src/scene.ts`**

搬移自 `src/main.ts:9-89` 與 `:632-633`。`createSceneContext(gate: boolean)` 內設定 `document.body.classList.toggle('gate', gate)`、建立 `renderer`、`scene`、`camera`、`cam`、`controls`、`look`、`hemi`、`key`、`rim` 與 `RoomEnvironment`，並執行初始的 `applyCamera()` 與 `applyLook()`；若 `!gate` 則註冊 `addEventListener('resize', resize)`。所有數值與 `main.ts` 逐字相同。

- [ ] **Step 2: 建立 `src/textures.ts`**

搬移自 `src/main.ts:115-225` 與 `:298-360` 的 17 個貼圖生成 helper。注意 `soffitTex(gate: boolean)` 與 `soffitGlowTex(gate: boolean)` 改從參數接收 `gate: boolean`，其餘演算法與畫布尺寸完全不變。

- [ ] **Step 3: 跑 `npx tsc --noEmit` 檢查型別**

Run: `npx tsc --noEmit`
Expected: exit 0 (無任何編譯錯誤)。

- [ ] **Step 4: Commit 並更新 summary 與 ledger**

```bash
git add src/scene.ts src/textures.ts
git commit -m "refactor: extract src/scene.ts and src/textures.ts"
```

---

### Task 3: 抽出模型後處理模組 `src/customizeModel.ts` 與介面互動模組 `src/ui.ts`

**Files:**
- Create: `src/customizeModel.ts`、`src/ui.ts`

**Interfaces:**
- Consumes: `src/scene.ts` (`LookState`)、`src/textures.ts` (所有貼圖函數)、`object-sculpt-spec.json`。
- Produces:
  - `src/customizeModel.ts`:
    - `export type CustomizedModelInfo = { baseColors: Map<THREE.MeshStandardMaterial, THREE.Color>; orangeSpec: Map<THREE.MeshStandardMaterial, string>; waveFlags: (t: number) => void; meshById: (id: string) => any; partById: (id: string) => THREE.Object3D | null };`
    - `export async function customizeModel(model: THREE.Object3D, scene: THREE.Scene, gate: boolean, clay: boolean, getWind: () => number): Promise<CustomizedModelInfo>`
  - `src/ui.ts`:
    - `export type UIHooks = { getCarSpeed: () => number; pickApi: { select: (id: string | null) => void; partCount: () => number } };`
    - `export function setupUI(params: { model: THREE.Object3D; scene: THREE.Scene; camera: THREE.PerspectiveCamera; renderer: THREE.WebGLRenderer; controls: OrbitControls; look: LookState; applyLook: () => void; gate: boolean; baseColors: Map<THREE.MeshStandardMaterial, THREE.Color>; orangeSpec: Map<THREE.MeshStandardMaterial, string>; partById: (id: string) => THREE.Object3D | null }): UIHooks`

- [ ] **Step 1: 建立 `src/customizeModel.ts`**

搬移自 `src/main.ts:106-112`、`:226-296`、`:361-469`、`:473-477`：
1. 先遍歷 `model` 收集 `baseColors` 與 `orangeSpec` (`main.ts:106-111`)。
2. 執行 `bevelOf` (`RoundedBoxGeometry`)、加油島 `planShape === 'stadium'` 擠出、以及 `await new SVGLoader().loadAsync('decals/caltex_wordmark.svg')` 3D CALTEX 立體字 (`main.ts:264-296`)。
3. 遍歷 `model` 套用各 `sculptComponent.id` 的貼圖與材質覆寫、垃圾桶底部 85% 收窄、雨棚 `energy-lines` 子 mesh、以及 `mergeGroups` (`main.ts:361-424`)。
4. 設定 `NO_SHADOW`；若 `!gate` 則清除 `clearcoat`、加入 `shadow-catcher` 與 `contact-shadows` (`InstancedMesh`)；若 `clay` 為 true 則將所有 mesh 材質換為灰色黏土材質 (`main.ts:426-454`)。
5. 收集旗幟頂點並建立 `waveFlags(t: number)` (使用 `getWind()` 讀取風力)，回傳 `{ baseColors, orangeSpec, waveFlags, meshById, partById }`。

- [ ] **Step 2: 建立 `src/ui.ts`**

搬移自 `src/main.ts:478-615`：
1. 取得 `canopy` 與 `columns`，實作 `stretchColumns(dy)`。
2. 實作 `bind(id, out, fn)` 並綁定 10 組滑桿與數字框 (`s-az` 到 `s-car`)，維護內部 `carSpeed` (初始值 2) 並由 `getCarSpeed()` 回傳。
3. 實作 `bindColor` 並綁定 4 組選色器 (`c-canopy`、`c-pump`、`c-grass`、`c-bg`)。
4. 實作 Raycaster 零件 hover / click 發光 (`tint` / `untint` / `setHover` / `select` / `partAt`)、`#b-detach` 抬升、`#b-reset` 重置與 `syncReset()`。
5. 若 `!gate`，綁定 `#panel-head` 收合與 `#toolbar` 四顆按鈕 (`#b-reset-view`、`#b-rotate`、`#b-fullscreen`、`#b-shot`)。
6. 回傳 `{ getCarSpeed: () => carSpeed, pickApi: { select: (id) => select(id ? partById(id) : null), partCount } }`。

- [ ] **Step 3: 跑 `npx tsc --noEmit` 檢查型別**

Run: `npx tsc --noEmit`
Expected: exit 0。

- [ ] **Step 4: Commit 並更新 summary 與 ledger**

```bash
git add src/customizeModel.ts src/ui.ts
git commit -m "refactor: extract src/customizeModel.ts and src/ui.ts"
```

---

### Task 4: 精簡入口檔 `src/main.ts` 並跑通所有既有驗收腳本

**Files:**
- Modify: `src/main.ts:1-636`

**Interfaces:**
- Consumes: `src/scene.ts`、`src/customizeModel.ts`、`src/ui.ts`、`src/car.ts`、`src/createCaltexStationModel.ts`。
- Produces: `window.__IMG2THREEJS_VIEWER__`、`window.__IMG2THREEJS_CAPTURE__`、`window.__IMG2THREEJS_PICK__`、`window.__IMG2THREEJS_READY__`。

- [ ] **Step 1: 改寫 `src/main.ts` 為組裝入口 (≤ 100 行)**

`src/main.ts` 依序執行：
1. 解析 URL 參數 `gate = params.get('gate') === '1'` 與 `clay = params.get('clay') === '1'`。
2. 呼叫 `createSceneContext(gate)` 取得 `{ renderer, scene, camera, cam, controls, look, applyCamera, applyLook }`。
3. 透過 `import.meta.glob('./createCaltexStationModel.ts')` 載入模型並 `scene.add(model)`；若 `!gate` 則 `createCar()` 並加入場景。
4. 呼叫 `await customizeModel(model, scene, gate, clay, () => look.wind)` 取得 `{ baseColors, orangeSpec, waveFlags, partById }`。
5. 呼叫 `setupUI({ model, scene, camera, renderer, controls, look, applyLook, gate, baseColors, orangeSpec, partById })` 取得 `{ getCarSpeed, pickApi }`。
6. 掛載 `window.__IMG2THREEJS_PICK__ = pickApi`、`window.__IMG2THREEJS_VIEWER__ = { renderer, scene, camera, controls }`、`window.__IMG2THREEJS_CAPTURE__ = { setCamera, setReferenceMode }`。
7. 啟動 render `loop()` 與 `window.__IMG2THREEJS_READY__ = true`。

- [ ] **Step 2: 跑 TypeScript 編譯、Vite 打包與 UI / v11 核心驗收**

Run: `npx tsc --noEmit && npx vite build && python3 scripts/check_ui.py && python3 scripts/check_v11.py --task 3`
Expected: 全部 exit 0，`check_ui OK`，`check_v11` A1–A6、B1–B7 全 PASS。

- [ ] **Step 3: 跑全部既有幾何與材質驗收腳本**

Run:
```bash
python3 scripts/check_details.py --round 3 && \
python3 scripts/check_orbit.py && \
python3 scripts/check_layout.py && \
python3 scripts/check_canopy.py && \
python3 scripts/check_scene.py && \
python3 scripts/check_soil.py && \
python3 scripts/check_hue.py && \
python3 scripts/check_view.py && \
python3 scripts/check_final.py && \
python3 scripts/check_grounded.py && \
python3 scripts/color_check.py
```
Expected: 全部 exit 0。

- [ ] **Step 4: Commit 並更新 summary 與 ledger**

```bash
git add src/main.ts
git commit -m "refactor: slim down src/main.ts to orchestrate scene, model, and UI"
```

---

### Task 5: 補齊 `package.json` scripts、撰寫 `README.md` 並通過 `check_refactor.py`

**Files:**
- Modify: `package.json:9-16`
- Create: `README.md`

**Interfaces:**
- Consumes: Task 1 的 `scripts/check_refactor.py`。
- Produces: 可直接執行的 `npm run dev`、`npm run build`、`npm run preview` 與完整的 `README.md`。

- [ ] **Step 1: 更新 `package.json` 的 `scripts` 與 `description`**

在 `package.json` 的 `"scripts"` 加入：
```json
  "scripts": {
    "dev": "vite --port 5173",
    "build": "vite build",
    "preview": "vite preview --port 5173",
    "typecheck": "tsc --noEmit"
  },
```

- [ ] **Step 2: 撰寫 `README.md`**

包含以下章節：
1. **專案簡介**：馬來西亞柔佛 (Johor, Malaysia) Caltex 加油站 Procedural Three.js Diorama，100% 程式碼生成幾何與 Canvas 2D / SVG 貼圖，無外部 3D 模型檔。
2. **快速啟動**：`npm install`、`npm run dev` (開啟 `http://localhost:5173`)、`npm run build`、`npm run typecheck`。
3. **網址參數模式**：一般模式 (`/`)、驗收模式 (`/?gate=1`，固定 1024×687 參考鏡頭與無 UI 灰底)、白模模式 (`/?clay=1`)。
4. **程式碼架構 (`src/`)**：
   - `src/main.ts`：應用程式入口、載入模型與車輛、綁定全域測試 hook 與 render loop。
   - `src/scene.ts`：WebGLRenderer、PerspectiveCamera、OrbitControls、太陽與環境光設定。
   - `src/textures.ts`：所有 Canvas 2D 動態貼圖 (招牌、車格線、土壤分層、玻璃反光、雨棚斜紋等) 與 SVG Decal 載入。
   - `src/customizeModel.ts`：模型後處理 (圓角倒角、3D CALTEX 立體字、材質套用、draw call 合併、陰影與旗幟飄動)。
   - `src/ui.ts`：右側控制面板 (光線、顏色、高度、風速、車速)、Raycaster 點選抬升零件、底部工具列。
   - `src/car.ts`：程序化生成的銀色雙門跑車與進站加油動畫。
   - `src/createCaltexStationModel.ts`：由 `object-sculpt-spec.json` 自動生成的 157 個組件工廠函數 (勿手改)。
5. **模型規格修改與重新生成流程**：編輯 `scripts/build_spec_v11.py` 更新 `object-sculpt-spec.json`，再執行 generator 的指令說明。
6. **自動化測試與驗證 (`scripts/`)**：如何執行 `python3 scripts/check_ui.py`、`python3 scripts/check_v11.py --task 3`、`python3 scripts/check_refactor.py` 等 Playwright 檢查腳本。

- [ ] **Step 3: 跑 `scripts/check_refactor.py`、`npm run build` 與 `check_ui.py`**

Run: `python3 scripts/check_refactor.py && npm run typecheck && npm run build && python3 scripts/check_ui.py`
Expected: 全部 PASS，exit 0。

- [ ] **Step 4: Commit 並更新 summary 與 ledger，停點 A**

```bash
git add package.json README.md
git commit -m "docs: add README.md and npm scripts for v12 architecture refactor"
```
