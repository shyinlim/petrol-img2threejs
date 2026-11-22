# Caltex 加油站 Diorama img2threejs Implementation Plan (v11)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正使用者 2026-11-22 紅框指出的 10 處差距，雨棚改用 Caltex 官方紅色，頁面 UI 改成英文並照 Apple HIG 修正。

**Architecture:** 先寫會失敗的檢查 (`scripts/check_v11.py` 加上 `check_ui.py` 的新斷言)。viewer 的修改只動 `src/main.ts`：預設鏡頭、旗子、雨棚底面、土壤、斜紋貼片、垃圾桶收窄、玻璃。零件的尺寸與位置改 `scripts/build_spec_v11.py`，再重新生成 factory。UI 只改 `index.html` 和 `main.ts` 的文案。

**Tech Stack:** three 0.187.0、Vite 8.3.8、TypeScript、Python 3 + Playwright、img2threejs forge 腳本。

**Spec:** 沒有獨立 spec。範圍是 2026-11-22 19:07 使用者的紅框截圖 (參考圖與現況各一張)，加上本對話整理的 12 點清單。建模規格是 `object-sculpt-spec.json`。前一版是 `docs/superpowers/plans/2026-11-22-caltex-station-img2threejs-v10.md`。

## Global Constraints

- `src/createCaltexStationModel.ts` 不手改。改 spec 再跑 `generate_threejs_factory.py --force`。
- 改 spec 一律透過 `scripts/build_spec_v11.py`。它先從 `backup/spec_before_v11.json` 還原，再接回 `reviewHistory`、`visualEvidence`、`tier1Results` (照 `build_spec_v10.py:7-10`)。helper (`set_dim`、`set_pos`、`set_att`、`put_xz`、`set_color`、`set_bevel`) 從 `build_spec_v10.py` 複製。
- 現有 id 不改名，material id `fascia-orange`、`mart-orange` 也不改。`main.ts:99` 的 hue slider 靠 `/orange/` 找材質。
- **gate mode 完全不變**：`?gate=1` 的鏡頭、光線、背景、view offset 照舊。新鏡頭、view offset、旗面幅度、底面亮度只在 normal mode。spec 改動 (紅色、尺寸) 兩個 mode 都看得到。
- 雨棚官方色：fascia 紅底，一角有白色斜紋 (Caltex Pakistan 官網：「white star on a red background with white stripes… diagonally across one corner」)。紅色起始值 `#ED1B2F` 來自 brandcolor.dev，不是官方規格。
- 斜紋的寬度、角度、條數官方沒有公布，本 plan 用 3 條、寬 0.14、間距 0.14、斜 55 度 (推論)。
- 驗收看 normal mode 預設鏡頭，視窗 1280×800 與 1667×900 兩種。sample 截圖的瀏覽器約 1667 CSS px 寬。
- UI 文案用 Title Case (`buttons.md › Content` 的 title-style capitalization)。
- draw call 上限 gate 260、normal 520 不變。v10 量到 gate 219、normal 321。
- img2threejs 修正次數現在 `total=4/6`。Task 3 記一筆 `refine-spec`，結束是 `5/6`。reviewer 判不過時記 `request-input` 並停下。
- rollback 點：開工前打 git tag `pre-v11`。每個 Task 完成後 commit 一次。
- 每個 Task 完成後複製新的 `docs/summary/yyyymmddhhmmss_plan_summary.md`，`.img2threejs/ledger.md` 加一行。
- 既有檢查每個 Task 都跑：`check_grounded.py`、`check_soil.py`、`check_view.py`、`check_final.py`、`check_hue.py`、`check_orbit.py`、`check_layout.py`、`check_canopy.py`、`check_scene.py`、`color_check.py`、`check_details.py --round 3`、`check_ui.py`。

## 範圍外

- 加油機造型：使用者框了 pump-1，看不出要改哪裡。Task 5 停點問。
- 柱子粗細與顏色：使用者沒框。
- 後製 AO：v10 量過，會讓 normal mode draw call 翻倍。

## 清單對照

| 清單 | 內容 | Task |
| --- | --- | --- |
| 1 | 雨棚改紅色加斜紋，Mart 橘帶同色 | 3 |
| 2 | 預設鏡頭能看到 CALTEX 長邊，字不擠 | 2 |
| 3 | 星標縮小 | 3 |
| 4 | 雨棚底面變亮，燈點減少 | 2 |
| 5 | 前緣唇邊加深 | 3 |
| 6 | 兩面旗都入鏡，飄動幅度加大 | 2 |
| 7 | Mart 玻璃改大片 | 3 |
| 8 | 車擋拉長 | 3 |
| 9 | 垃圾桶收窄，和樹對調位置 | 3 |
| 10 | 土壤改橫向分層 | 2 |
| 11 | UI 全英文，標題換字型，對比與點擊範圍 | 4 |
| 12 | 檢查腳本改紅色目標、改英文 | 1 |

## Review Focus

1. 視窗寬度 < 900px 時，view offset 會把模型推出畫面：寬度 < 900 時 offset 設 0。Task 2 斷言 A6。
2. 視窗縮放後，view offset 沒有重算：`resize()` 重新呼叫 `setViewOffset`。Task 2 斷言 A1 用同一頁 `set_viewport_size` 換尺寸。
3. 加了 view offset 後，點零件 (raycast) 對不到位置：`setFromCamera` 用的 projection 含 offset。`check_ui.py` 斷言 4 在新鏡頭下 hover `mart` 必須是 pointer。
4. 紅色 fascia 在 hue slider 上失效：`check_hue.py` 繼續跑。
5. 面板標題改成 `<button>` 之後，收合功能壞掉：`check_ui.py` 斷言 2 照舊點 `#panel-head`。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你要做什麼 |
| --- | --- | --- |
| 0 | 開工前 | 審 plan，選執行方式 |
| A | Task 2 | 開 http://localhost:5173，看鏡頭、旗子、底面、土壤 |
| B | Task 5 | 看紅色雨棚、UI、reviewer 分數，回答加油機要改哪裡 |

任一檢查調 3 次數值仍不過，就停下問你。

---

### Task 1: 檢查先寫，先失敗

**Files:**
- Create: `scripts/check_v11.py`、`backup/spec_before_v11.json` (複製現在的 `object-sculpt-spec.json`)
- Modify: `scripts/capture_normal.py:3,11`、`scripts/check_ui.py`

**Interfaces:**
- Consumes: `_viewer.gate_page(query, viewport)`、`_viewer.set_camera()`、`_geom.boxes()`、`capture_normal.lab()` 的寫法 (複製，不 import)。
- Produces:
  - `python3 scripts/check_v11.py --task {2,3}`：`--task 3` 包含 `--task 2` 的斷言。exit 0 代表全過。
  - `check_ui.py` 新斷言 10–14。

- [ ] **Step 1: `git tag pre-v11`，複製 spec 到 `backup/spec_before_v11.json`**

- [ ] **Step 2: 寫 `scripts/check_v11.py`，normal mode，預設鏡頭 (不呼叫 `set_camera`)**

`--task 2`：
- A1. 1280×800 與 1667×900 (同一頁 `page.set_viewport_size` 換尺寸，等 500ms)：`canopy`、`flag-malaysia`、`flag-johor`、`base-slab`、`bin-blue-2` 的投影 bbox 全部落在 `x ∈ [16, #panel 左緣 - 16]`、`y ∈ [16, #toolbar 上緣 - 8]`。
- A2. `camera.position.y < soffit 的 world bbox min.y`，代表看得到雨棚底面。
- A3. 頁面載入 1 秒後，`flag-malaysia` 的 position attribute 與原始值的最大 z 差 ≥ 0.2。
- A4. 雨棚底面亮度：world 點 `(canopy min.x + 1.0, soffit min.y - 0.001, 2.0)` 投影後取 9×9 平均，CIE L* ≥ 85。
- A5. 土壤分層：讀 `base-slab` 的 `-x` 面材質 `map.image` (canvas)，算每列平均亮度的標準差與每欄平均亮度的標準差，前者 ≥ 後者 × 3。
- A6. 視窗 800×700：`camera.view` 是 null 或 `offsetX == 0`，而且頁面沒有 error。

`--task 3` 再加：
- B1. `canopy` 的 mesh 底下有一個 `name == 'energy-lines'` 的子 mesh，有 `map`。它的 world bbox：`min.x ≥ canopy min.x - 0.02`，z 範圍落在 `[-6.25, -4.2]` (canopy 在 root z 0.6，local -6.85 到 -4.8)。
- B2. `roundel-logo` mesh 的 geometry bbox x 寬介於 0.98 到 1.02 (半徑 0.5)。
- B3. 每個 `wheel-stop-*` 的 geometry bbox z 長介於 1.98 到 2.02。
- B4. `bin-blue-1`、`bin-green-1` 的 world 中心 z < -5。`tree-1-trunk` 的 world 中心 z > -2。
- B5. `bin-blue-1` mesh 的 geometry：最低點那排頂點的 x 寬 ÷ 最高點那排 ≤ 0.9。
- B6. 場景裡沒有 `sculptComponent.id` 以 `mart-rail-` 開頭的節點。
- B7. `mart-band` 的材質顏色 hex 等於 `canopy` 側面材質的顏色 hex。

- [ ] **Step 3: 改 `scripts/capture_normal.py`**

`TARGETS["canopy"]` 從 `#F16925` 改成 `#ED1B2F`。docstring 同步改。另外兩個目標不動。

- [ ] **Step 4: `check_ui.py` 加斷言 10–14 (normal mode 1280×800)**

- 10. `document.body.innerText` 不含 `[㐀-鿿]`。
- 11. `#title` 文字是 `Caltex Station`，computed `font-family` 不含 `Songti`。
- 12. `#toolbar button` 每顆都有非空的 `aria-label`。`#panel-head` 的 tagName 是 `BUTTON`，點一下後 `aria-expanded` 從 `true` 變 `false`。
- 13. 每個 `#panel input[type=range]` 的 `getBoundingClientRect().height ≥ 20`。每個 `.row label` 的 computed `font-size ≥ 13px`。
- 14. `#eyebrow` 的文字色對 `--bg` 的對比 ≥ 4.5:1，在 Python 算 WCAG relative luminance。

- [ ] **Step 5: 跑一次，確認是紅燈**

Run: `python3 scripts/check_v11.py --task 3; python3 scripts/check_ui.py; python3 scripts/capture_normal.py shots/v11_before.png`
Expected：A1、A3、A4、A5、B1–B7、UI 10–14、canopy dE 都 FAIL。A2 與 A6 現在就 PASS (鏡頭 y 3.88 低於底面 4.84)，它們是防止 Task 2 改壞的護欄。

- [ ] **Step 6: Commit** `test: v11 checks for camera, flags, soffit, soil, red canopy, English UI (red)`

---

### Task 2: viewer：鏡頭、旗子、底面、土壤

**Files:**
- Modify: `src/main.ts:30-32` (鏡頭)、`:58` (`look.wind`)、`:143-160` (底面)、`:290-305` (土壤)、`:333-335` (底面材質)、`:571` (`resize`)
- Modify: `index.html:93` (`s-wind` 的 max 與 value)

**Interfaces:**
- Consumes: Task 1 的 `check_v11.py --task 2`。
- Produces: `applyViewOffset()`，`applyCamera()` 與 `resize()` 都會呼叫它。

- [ ] **Step 1: 預設鏡頭**

normal mode 的 `cam` 改成 `{ azimuth: -51, elevation: 6, distance: 32, fov: 30, target: (0, 1.2, 0) }`。這是 v3 的方位角，鏡頭壓低到雨棚底面以下 (A2)。

- [ ] **Step 2: `applyViewOffset()`**

normal mode 且 `w() ≥ 900` 時：`camera.setViewOffset(w(), h(), ox, 0, w(), h())`，`ox = (panel 寬 + 16) / 2`，panel 寬從 `#panel` 的 `offsetWidth` 讀。其他情況呼叫 `camera.clearViewOffset()`。gate mode 不呼叫。

- [ ] **Step 3: 跑 A1、A2、A6，距離在 28–38 之間調到 A1 通過**

Run: `python3 scripts/check_v11.py --task 2`

- [ ] **Step 4: 旗子**

`look.wind` 預設 0.06 → 0.14。`#s-wind` 的 `max` 0.2 → 0.3，`value` 0.14。A3 通過。

- [ ] **Step 5: 雨棚底面**

燈點從 4×6 改 3×4。`soffitGlowTex()` 的底色從 `#000` 改 `#404040`，整片底面帶一點自發光，燈點維持 `#fff`。底面材質的 `emissiveIntensity` 從 0.6 開始調，直到 A4 通過。

- [ ] **Step 6: 土壤 `soilTex(widthU, heightU, seed)`**

簽名不變。做法：由上往下 5 層，每層高度隨機 (seed 決定)，層色在 `#8A6446`、`#9A7756`、`#A9865F`、`#7E5B3E` 間輪流。層與層的交界用正弦波起伏，振幅 ≤ 3% 高度。最上面 6% 高度壓暗成 `#6E4E34`，代表根系層。再撒 8% 面積的 2px 細顆粒。圓點 blob 拿掉。A5 與 `check_soil.py` 都要通過。

- [ ] **Step 7: 全部檢查**

Run: `python3 scripts/check_v11.py --task 2` 加上 Global Constraints 列的全部既有檢查。
Expected：`check_v11 --task 2` 全 PASS，既有檢查全部 exit 0。`check_orbit.py` 斷言 4 在 v10 就時好時壞，失敗時連跑 3 次，記下結果。

- [ ] **Step 8: 存 `shots/v11_t2_default.png` (normal 預設鏡頭，1280×800)，commit**，停點 A

`feat: default camera at v3 azimuth with panel offset, stronger flag wave, bright soffit, layered soil (v11 task 2)`

---

### Task 3: spec 與零件：紅雨棚、斜紋、星標、唇邊、車擋、垃圾桶、Mart 玻璃

**Files:**
- Create: `scripts/build_spec_v11.py`
- Modify: `object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)、`parts.json` (`scripts/dump_parts.py` 重新生成)
- Modify: `src/main.ts:307-315` (`glassTex`)、`:324-325` (垃圾桶)、`:346-349` (canopy，加斜紋)

**Interfaces:**
- Consumes: Task 1 的 `check_v11.py --task 3`、`capture_normal.py`。
- Produces: `energyLinesTex(): THREE.CanvasTexture`，canopy 底下的 mesh `energy-lines`。

- [ ] **Step 1: 寫 `scripts/build_spec_v11.py`**

值全部是 (推論)，取自 v3 像素比例：
1. `set_color("fascia-orange", "#ED1B2F")`、`set_color("mart-orange", "#ED1B2F")`。
2. 星標半徑 0.6 → 0.5：`roundel-logo` 的 `attachment.baseRadius` 與 `endRadius` 改 0.5，`dimensions.width/depth` 與 `transform.scale` x、z 改 1.0。
3. 唇邊加深：`fascia-lip-top`、`fascia-lip-end` 的 x 深 0.1 → 0.18，position x -5.8 → -5.84 (內側貼面不動)。
4. 車擋：`wheel-stop-1..8` 的 depth 1.3 → 2.0。
5. 垃圾桶與樹對調：`put_xz(bin-blue-1, -6.84, -6.6)`、`put_xz(bin-green-1, -6.84, -5.75)`、`put_xz(tree-1-trunk, -6.84, -1.0)`。
6. 從 `componentTree` 刪掉 `mart-rail-1`、`mart-rail-2`，並刪掉 spec 其他地方引用這兩個 id 的項目 (先 grep `"mart-rail-`)。
7. `spec["assumptions"]` 加一行：v11 的紅色來自 brandcolor.dev，斜紋尺寸與其他數值是 v3 像素推論。

- [ ] **Step 2: 生成 factory，strict validate**

Run: `python3 scripts/build_spec_v11.py && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts --force && npx tsc --noEmit`
Expected：全部 exit 0。

- [ ] **Step 3: 斜紋貼片**

`energyLinesTex()`：canvas 512×256，透明底，畫 3 條白色平行斜帶，寬 0.14、間距 0.14 (換算成貼片寬度的比例)，斜 55 度，貼在左下角。canopy 分支 (`main.ts:346`) 加一個 `PlaneGeometry`：寬 1.9 (z 方向)、高 0.75 (y 從 -0.45 到 0.30，避開上唇邊)，面向 -x，中心 z = -5.85 (canopy local，避開 z -6.82 起的端唇邊)，x = canopy 的 -x 面再往外 0.005。材質 `MeshStandardMaterial({ map, transparent: true, alphaTest: 0.05, polygonOffset: true, polygonOffsetFactor: -2 })`。mesh 名 `energy-lines`，`castShadow = false`，加進 canopy mesh 的 children。B1 通過。

- [ ] **Step 4: 垃圾桶收窄**

`/^bin-(blue|green)-\d$/` 分支先把 geometry clone，所有 y < 0 的頂點，x 與 z 乘上 `0.85 + 0.15 × (y - minY) / (0 - minY)`。最底部是 0.85 倍，中線以上不動。B5 通過，`check_layout.py` 也要通過 (輪子在桶內)。

- [ ] **Step 5: Mart 玻璃 `glassTex(base)`**

簽名不變。拿掉貨架橫條。改成上深下淺的垂直漸層，底色 `base` 往下調亮 15%，再畫兩道斜反光，不透明度 0.18 與 0.10。

- [ ] **Step 6: 重新產生 `parts.json`，跑全部檢查**

Run: `python3 scripts/dump_parts.py && python3 scripts/check_v11.py --task 3 && python3 scripts/capture_normal.py shots/v11_t3.png` 加上 Global Constraints 的既有檢查。
Expected：全部 exit 0。canopy dE > 10 時，`fascia-orange` 的 HSL 亮度一次調 +3%，最多 3 次。仍不過就停下問。

- [ ] **Step 7: img2threejs review**

照 v10 Task 7 的命令跑 gates (turntable、multi-angle、attachment_anchor、diagnose_render、interior_difference、check_part_coverage)。再派一個 Opus reviewer，比較 `shots/v11_t3.png` 與 `v3.webp`，雨棚那一項的標準改成「Caltex 官方紅加斜紋」，其他門檻照原本的。用 `append_review.py --action refine-spec --force-out-of-order` 記一筆，`total` 變 5/6。

- [ ] **Step 8: Commit** `feat: Caltex red canopy with energy lines, smaller roundel, deeper lips, longer wheel stops, tapered bins, clear Mart glass (v11 task 3)`

---

### Task 4: UI 英文化與 HIG 修正

**Files:**
- Modify: `index.html:7` (`--mute`)、`:14-15` (標題字型)、`:18-21` (footnote)、`:23-25` (panel 寬、head)、`:30-33` (row 欄寬、字級)、`:36-40` (滑桿)、`:61-105` (全部文案)
- Modify: `src/main.ts:508` (`'click a part'`)、`:545` (`aria-expanded`)

**Interfaces:**
- Consumes: Task 1 的 `check_ui.py` 斷言 10–14。
- Produces: 無。所有元素 id 不變。

- [ ] **Step 1: 文案對照，逐字照抄**

| 位置 | 現在 | 改成 |
| --- | --- | --- |
| `#title` | 加油站 | Caltex Station |
| `#footnote em` | Caltex Station | Procedural Diorama |
| `#footnote small` | Three.js · 全程式生成，無外部模型 | Three.js · Built in code, no external models |
| `#panel-head` | 參數 | Controls |
| group | 光線 / 顏色 / 結構 / 動態 / 零件 | Light / Color / Structure / Motion / Parts |
| 光線 | 太陽方位、太陽高度、曝光、陰影柔和、環境光 | Sun Azimuth、Sun Height、Exposure、Shadow Softness、Ambient Light |
| 顏色 | 橘色色相、雨棚色、草地色、加油機色、背景色 | Brand Hue、Canopy、Grass、Pumps、Background |
| 結構 | 雨棚高度 | Canopy Height |
| 動態 | 旋轉速度、旗面風力 | Spin Speed、Wind |
| 零件 | 選取：、抬起 / 放回、重置零件 | Selected:、Lift / Drop、Reset Parts |
| `#sel` 預設與 `main.ts:508` | click a part | None |
| toolbar `title` 與 `aria-label` | 重置視角、自動旋轉、全螢幕、存成圖片 | Reset View、Auto Rotate、Full Screen、Save Image |

- [ ] **Step 2: 樣式**

1. `#title`：`600 40px/1.1 -apple-system, "SF Pro Display", system-ui, sans-serif`，`letter-spacing: -0.01em`。
2. `#footnote em`：`500 15px/1.3` 同一組系統字，不用斜體。
3. `--mute`：`#8a817a` → `#645a53`。對 `#EFDFD2` 從約 3.0:1 升到約 5.2:1 (`accessibility.md`：17pt 以下文字要 4.5:1)。
4. `#panel` 寬 240 → 280。`.row` 欄寬 `62px 1fr 56px` → `112px 1fr 56px`，英文標籤不換行。
5. `.row label`、`.group button`：`font-size: 13px` (macOS 預設字級)。
6. 滑桿：`input[type=range]` 高 14 → 20px (`accessibility.md`：macOS 控制項最小 20×20pt)。thumb 10 → 14px，`margin-top` -4 → -6px。
7. `#panel-head` 改成 `<button id="panel-head" aria-expanded="true" aria-controls="panel-body">`，清掉按鈕預設樣式 (`border:0; background:none; width:100%; font:inherit; text-align:left`)。`main.ts:545` 切換時同步寫 `aria-expanded`。
8. `font-family` 拿掉 `"PingFang TC"`。

- [ ] **Step 3: 跑檢查**

Run: `python3 scripts/check_ui.py && python3 scripts/check_v11.py --task 3`
Expected：check_ui 斷言 1–14 全 PASS。panel 加寬後，A1 的 offset 會跟著重算。

- [ ] **Step 4: Commit** `feat: English UI, system title font, 5.2:1 muted text, 20px sliders, accessible panel toggle (v11 task 4)`

---

### Task 5: 收尾，停點 B

**Files:**
- Modify: `REPORT.md` (非分數區段)、`.img2threejs/ledger.md`
- Create: `docs/summary/yyyymmddhhmmss_plan_summary.md`

- [ ] **Step 1: 全部檢查再跑一次**

Run: Global Constraints 列的全部既有檢查，加上 `check_v11.py --task 3`、`npx vite build`。
Expected：全部 exit 0，draw call gate ≤ 260、normal ≤ 520。

- [ ] **Step 2: 存 1280×800 與 1667×900 的預設鏡頭截圖，各做一張與 `v3.webp` 的對照圖**

`shots/v11_final_1280.png`、`shots/v11_final_1667.png`，對照圖用 `make_comparison_sheet.py`。

- [ ] **Step 3: 更新 `REPORT.md`、ledger、summary，commit**，停點 B

`docs: v11 report, ledger, summary (v11 task 5)`
