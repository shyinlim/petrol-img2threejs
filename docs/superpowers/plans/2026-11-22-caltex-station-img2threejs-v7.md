# Caltex 加油站 Diorama img2threejs Implementation Plan (v7)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓使用者能用滑鼠 360 度旋轉模型，並讓每個角度都看得到完整外觀，比例向 `v3.webp` 靠攏。

**Architecture:** v6 已跑完 23 步 checklist (`state.json` 是 `complete`)，Fix4 也已套用。v7 不重開 pass loop，照 Fix4 的路線：預覽層改 `src/main.ts`，幾何改 spec 再重新生成 factory，最後用 8 角度環景加獨立 reviewer 驗收。

**Tech Stack:** three 0.187.0 (含 `three/addons/controls/OrbitControls.js`)、Vite 8.3.8、TypeScript、Python 3 + Python Playwright、img2threejs forge 腳本。

**Spec:** 無獨立 spec 文件。範圍寫在 Global Constraints；建模規格是 `object-sculpt-spec.json`；前一版計畫是 `docs/superpowers/plans/2026-11-21-caltex-station-img2threejs-v6.md`。

## Global Constraints

- 目標外觀是 `v3.webp` (`reference/diorama.png`)。v1、v2 不動。
- `K=/Users/shyin/.claude-shyin/skills/img2threejs`，腳本在專案資料夾執行。
- `src/createCaltexStationModel.ts` 不手改，只能改 spec 再跑 `generate_threejs_factory.py`。
- 資料夾不是 git repo，不 commit。改 spec 前先備份到 `backup/spec_before_v7.json`。
- 改 spec 一律用 `scripts/build_spec_v7.py`，每次先從備份還原再套改動，可重跑。
- cylinder 元件的位置取自 `attachment.localStart/localEnd`，不是 `transform.position`，兩者要一起改。
- draw calls 上限 160 (`spec.performanceBudget.maxDrawCalls`)，目前 149。
- `?gate=1` 的參考相機 (`az -50.89, el 9.51, dist 48.52, fov 20`) 不改，留作和 v6 分數對照。
- 標誌、CALTEX 字、旗面的向量素材 (`assets/*.svg`) 不改。
- 圖上看不到的面 (背面、屋頂) 屬推論，寫進 `REPORT.md` 的推論清單。
- 每步完成後照 summary 規則複製新快照，`.img2threejs/ledger.md` 加一行。

## Review Focus

1. 拖曳旋轉放開滑鼠時，`click` 事件會觸發，選取被誤換掉：Task 1 測拖曳後選取不變。
2. 視窗 resize 會呼叫 `applyCamera()`，把使用者轉好的角度重置：Task 1 測 resize 後相機位置不變。
3. 新增面材質會增加 draw calls，可能超過 160：Task 3、4 結束各量一次。
4. 背面的旗子、roundel、CALTEX 字左右相反：Task 2 環景 az 180 逐一看。
5. 相機轉到底座下方或鑽進雨棚：Task 1 限制仰角與距離，並測極端拖曳。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你要做什麼 |
| --- | --- | --- |
| A | Task 1 | 開 http://localhost:5173 自己拖曳，確認能 360 度轉 |
| B | Task 5 | 看新舊預設視角並排圖，確認比例與相機 |
| C | Task 7 | 看 8 角度環景與 reviewer 結論，驗收 |

---

### Task 1: OrbitControls (停點 A)

**Files:**
- Modify: `src/main.ts:1-35` (import、相機)、`src/main.ts:222-227` (click)、`src/main.ts:242-258` (setCamera、resize、loop)
- Create: `scripts/check_orbit.py`

**Interfaces:**
- Produces: `controls: OrbitControls`，`window.__IMG2THREEJS_VIEWER__` 加 `controls` 欄位；`setCamera()` 後 `controls.target` 等於 `cam.target`。

- [ ] **Step 1: 寫 `scripts/check_orbit.py`**

Python Playwright，SwiftShader 參數沿用 v6 截圖腳本。開 `http://localhost:5173/` (一般模式，1280x800)，等 `__IMG2THREEJS_READY__`。斷言：
1. 從畫面中心向右拖 300px 後，`camera.position` 的 x 或 z 變化大於 1。
2. 拖曳前用 `__IMG2THREEJS_PICK__.select('canopy')` 選取，拖曳後 `#sel` 文字仍是 `canopy`。
3. 不移動滑鼠的單擊點在 canopy 上，`#sel` 會變成被點到的零件 id。
4. `page.set_viewport_size(1000, 700)` 後，相機位置與 resize 前相差小於 0.01。
5. 向下拖 2000px 後，`camera.position.y` 大於 0.5 (不到底座下)。
6. 呼叫 `__IMG2THREEJS_CAPTURE__.setCamera({azimuth: 40})` 後，`controls.target` 等於 `(-0.21, 2.2, -0.11)`。
7. 全程 `pageerror` 數為 0。

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 scripts/check_orbit.py`
Expected: 斷言 1 失敗 (相機不動)。

- [ ] **Step 3: 改 `src/main.ts`**

- 加 `OrbitControls(camera, renderer.domElement)`，`enableDamping = true`，`target` 取 `cam.target`。
- 限制：`maxPolarAngle = Math.PI / 2 - 0.05`、`minDistance = 12`、`maxDistance = 90`。
- `loop()` 每幀先 `controls.update()` 再 render。
- `resize()` 只更新 `camera.aspect`、`updateProjectionMatrix()` 與 renderer 尺寸，不呼叫 `applyCamera()`。
- `setCamera()` 結束時 `controls.target.copy(cam.target); controls.update()`。
- click：`pointerdown` 記座標，`click` 時位移超過 5px 就 return。

- [ ] **Step 4: 驗證**

Run: `npx tsc --noEmit && python3 scripts/check_orbit.py && npx vite build`
Expected: 全部 exit 0，7 個斷言 PASS。

- [ ] **Step 5: 停點 A**

請使用者開 http://localhost:5173 拖曳、滾輪縮放、點零件。等確認再繼續。

---

### Task 2: 8 角度環景截圖與基準

**Files:**
- Create: `scripts/turntable.py`、`shots/v7_base_*.png`、`shots/v7_base_sheet.png`

**Interfaces:**
- Consumes: `__IMG2THREEJS_CAPTURE__.setCamera({azimuth, elevation, distance, fov, target})`
- Produces: `python3 scripts/turntable.py <tag>` 輸出 `shots/v7_<tag>_ref.png` (gate 參考視角) 加 `shots/v7_<tag>_az{000,045,...,315}.png` (8 張，el 22、dist 40、fov 30、target `[0,1.5,0]`)，再拼成 `shots/v7_<tag>_sheet.png` (3x3)。

- [ ] **Step 1: 寫 `scripts/turntable.py`**

用 `?gate=1` (1024x687、`#303030` 背景)。拼圖用 Pillow，沒裝就改用 `sips` 逐張輸出不拼。exit 0 條件：9 張 PNG 都存在且不是單色 (像素標準差 > 5)。

- [ ] **Step 2: 拍基準**

Run: `python3 scripts/turntable.py base`
Expected: 9 張圖加 1 張 sheet，exit 0。

- [ ] **Step 3: 寫環景檢查表**

在 `shots/v7_checklist.md` 寫 8 項，每個角度都照這 8 項打勾：
1. 旗子正反兩面都有圖，canton 在旗桿那一側。
2. roundel 兩面都有圖，星形不反。
3. CALTEX 字至少在雨棚兩個長邊出現，字不反。
4. 加油機頂牌兩面都有內容。
5. Mart 四面都有橘帶，背面有門。
6. 雨棚頂面不是整片暗橘。
7. 沒有零件浮空或穿出底座。
8. 沒有整面透明 (看得到另一側) 的面。

用 vision 看 base sheet，逐項記錄目前失敗的角度，當 Task 3 的待修清單。

---

### Task 3: 背面與屋頂 (只改 `src/main.ts`)

**Files:**
- Modify: `src/main.ts:121-156` (材質覆寫)

**Interfaces:**
- Consumes: Task 2 的 `scripts/turntable.py`
- Produces: 每個帶貼圖的零件，從外側看得到的面都有材質。

- [ ] **Step 1: 改材質覆寫**

BoxGeometry 面順序是 `+x, -x, +y, -y, +z, -z`。
- 旗子：`-z` 面用同一張 PNG，`repeat.x = -1`，讓 canton 留在旗桿側。
- roundel：底部 cap (index 2) 用 `decalTex` 加 `repeat.x = -1`，取代 `hidden`。
- 加油機頂牌：`pump-head-N` 的 `+x` 面換成 `signTex`，其餘面保留原材質物件。
- Mart：`mart` 的 `+x`、`+z`、`-z` 面用 canvas texture。白底，橘帶高度與位置對齊 `mart-band` (band 頂在 mart 頂下 0.1，高 0.5，之後 Task 4 改 0.8 時一起改)。`+x` 面中央加灰色門 (寬 1.0、高 2.2)。
- 雨棚頂面：`canopy` 的 `+y` 面換成 `#e9e6e1`，roughness 0.9。其餘 5 面保留原材質物件，色相滑桿才抓得到。

- [ ] **Step 2: 驗證**

Run: `npx tsc --noEmit && python3 scripts/check_orbit.py && python3 scripts/turntable.py back`
Expected: exit 0；用 vision 照 `shots/v7_checklist.md` 看 `v7_back_sheet.png`，第 1、2、4、5、6 項全過。

- [ ] **Step 3: 量 draw calls 與色相滑桿**

用 Playwright 讀 `renderer.info.render.calls` (一般模式、預設視角)，再把 `#s-hue` 設 20，確認 canopy 側面顏色有變。
Expected: draw calls ≤ 160。超過就把新加貼圖的零件加進 `NO_SHADOW` regex，仍超過就停下問使用者放寬預算。

---

### Task 4: 比例修正 (改 spec，重新生成 factory)

**Files:**
- Create: `backup/spec_before_v7.json`、`scripts/build_spec_v7.py`
- Modify: `object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)、`src/main.ts:127-132` (新增 wordmark 背面)

**Interfaces:**
- Produces: 新元件 `canopy-wordmark-back` (parent `canopy`、box、material `decal-white`)，`main.ts` 用 `+x` 面貼 wordmark。

- [ ] **Step 1: 備份**

Run: `mkdir -p backup && cp object-sculpt-spec.json backup/spec_before_v7.json`

- [ ] **Step 2: 寫 `scripts/build_spec_v7.py`**

先從 `backup/spec_before_v7.json` 讀，改完寫回 `object-sculpt-spec.json`。數值是依 v3 像素比例估計 (推論)，Step 5 用並排圖確認：

| 元件 | 欄位 | 現值 | 新值 |
| --- | --- | --- | --- |
| `roundel-logo` | dimensions 與 scale 的 width、depth | 1.5 | 0.95 |
| `roundel-logo` | localStart / localEnd 的 y | 0.4 | 0.45 |
| `tree-1`、`tree-2` | 直徑 | 1.7 | 1.0 |
| `tree-3`、`tree-4` | 直徑 | 2.1 | 1.2 |
| `tree-N-trunk` | 高度 (localEnd.y) | 1.9 | 1.1，crown 跟著下移 |
| `mart-band` | height | 0.5 | 0.8 |
| `mart-sign` | height、depth | 0.42、1.4 | 0.65、2.0 |
| `pump-orange` | colorMaterialRecipe | `#E0501F` | 依 Step 5 色差調整 |
| `canopy-wordmark-back` | 新增 | 無 | 複製 `canopy-wordmark`，x 改 +5.77，z 改 -1.5 |

每個改到的元件同步改 `dimensions`、`transform.scale`；cylinder 同步改 `attachment`。新元件補 `topologyClass`、`topologyRationale`、`colorMaterialRecipe`、`confidence: 0.4` (推論)。

- [ ] **Step 3: 重新生成與驗證**

Run: `python3 scripts/build_spec_v7.py && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts --force`
Expected: 全部 exit 0。

- [ ] **Step 4: 接上 wordmark 背面**

`main.ts` 的 `DECALS` 加 `canopy-wordmark-back`，`+x` 面貼 `decals/caltex_wordmark.png`，其餘面 `hidden`。

- [ ] **Step 5: 色差與並排**

寫一段 Python (放 `scripts/color_check.py`)：在 `reference/diorama.png` 與 `shots/v7_<tag>_ref.png` 的加油機機身各取 5x5 平均色，算 CIEDE2000。
Run: `python3 scripts/turntable.py prop && python3 scripts/color_check.py shots/v7_prop_ref.png`
Expected: 加油機 ΔE ≤ 10；不到就調 `pump-orange` 重跑 Step 3。draw calls ≤ 160，part coverage 照 Task 7 指令跑一次 exit 0。

---

### Task 5: 一般模式的預設相機 (停點 B)

**Files:**
- Modify: `src/main.ts:21-35`

**Interfaces:**
- Produces: 一般模式預設相機與 gate 相機分開；gate 相機不變。

- [ ] **Step 1: 改預設視角**

ledger 記錄 v3 的視線在雨棚下方 (看得到 soffit)。gate 相機 y 約 10.2，比雨棚頂 5.8 高，所以看到整片暗橘頂面、Mart 被擋。一般模式改成：fov 35、target `[0, 1.2, 0]`、相機 y 介於 2.5 與 4.4 (soffit 底 4.84 以下)、azimuth -50.89、distance 依底座塞滿畫面 85% 寬調整。

- [ ] **Step 2: 並排圖**

Run: `python3 $K/forge/stage4_review/make_comparison_sheet.py --reference reference/diorama.png --render shots/v7_view_new.png --out shots/v7_view_cmp.png --json` (`v7_view_new.png` 用 Playwright 截一般模式 1024x687)。
Expected: 新視角看得到 soffit 與嵌燈、Mart 橘帶與 Mart 字、底座頂面。

- [ ] **Step 3: 停點 B**

給使用者看 `shots/v7_view_cmp.png` 與 `shots/v7_prop_sheet.png`，確認比例與預設視角。

---

### Task 6: 地層紋理

**Files:**
- Modify: `src/main.ts:121-156`

- [ ] **Step 1: 加地層 canvas texture**

`base-slab` 的 4 個側面用 canvas 畫 4 到 5 條水平色帶 (深咖啡到淺黃褐，取 `reference/diorama.png` 地層區的上中下三點顏色)，每條加少量隨機雜點。頂面與底面保留原材質。不用參考圖 crop 平鋪 (Fix4 記錄平鋪會出條紋)。

- [ ] **Step 2: 驗證**

Run: `npx tsc --noEmit && python3 scripts/turntable.py soil`
Expected: 4 個側面都看得到分層，沒有接縫錯位；draw calls ≤ 160。

---

### Task 7: 驗收與文件 (停點 C)

**Files:**
- Modify: `parts.json`、`REPORT.md`、`.img2threejs/ledger.md`
- Create: `shots/v7_final_*.png`、新的 `docs/summary/<ts>_plan_summary.md`

- [ ] **Step 1: 全部檢查**

Run: `npx tsc --noEmit && npx vite build && python3 scripts/check_orbit.py && python3 scripts/turntable.py final && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/run_gates.py --workspace .`
Expected: 全部 exit 0。

- [ ] **Step 2: 更新 `parts.json` 與 part coverage**

照 v6 Task 8 Step 1 傾印 `parts.json`，再跑 `python3 $K/forge/stage4_review/check_part_coverage.py --spec object-sculpt-spec.json --manifest parts.json --inventory di.json`。
Expected: exit 0。

- [ ] **Step 3: 獨立 reviewer**

派一個 Opus subagent，只給它 `reference/diorama.png`、`v3.webp`、`shots/v7_final_sheet.png`、`shots/v7_checklist.md`，不給我的結論。要它逐角度逐項判 pass / fail，並對照 v3 給比例意見。

- [ ] **Step 4: 文件**

`REPORT.md` 加 v7 段落：OrbitControls 操作、環景結果、推論清單 (Mart 背面門、雨棚頂色、wordmark 背面、旗背面)、draw calls。ledger 加一行，複製新 summary 快照。

- [ ] **Step 5: 停點 C**

給使用者 http://localhost:5173、`shots/v7_final_sheet.png`、reviewer 結論。

---

## Self-Review

1. Spec coverage：OrbitControls (Task 1)、8 角度驗收 (Task 2、7)、背面與雙面貼圖 (Task 3、4)、比例 (Task 4、5)、土層 (Task 6) 都有對應。
2. Step scan：v3 比例數值標推論，靠 Task 4 Step 5 與停點 B 確認；draw calls 超標有退路。
3. Type consistency：`scripts/turntable.py <tag>` 的輸出命名在 Task 2 到 7 一致；`canopy-wordmark-back` 在 Task 4 Step 2 與 Step 4 一致。
4. Review Focus：5 項分別落在 Task 1 斷言 2、4、5，Task 2 檢查表，Task 3 Step 3。
5. Proportion：沒有貼 code 本體，數值集中在一張表。
