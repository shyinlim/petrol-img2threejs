# Caltex 加油站 Diorama img2threejs Implementation Plan (v8)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓使用者能用滑鼠 360 度旋轉模型。每個角度都要看得到完整外觀，形體與配置也要更接近 `v3.webp`。

**Architecture:** v6 已跑完 23 步 checklist，Fix4 也已套用。v8 分三層改：預覽層改 `src/main.ts`；幾何改 spec，再重新生成 factory；改完 spec 照 img2threejs 跑一輪 `refine-spec`，包含 gates 與 `append_review`。驗收用 12 個角度的環景，並由獨立 reviewer 照原門檻評分。

**Tech Stack:** three 0.187.0 (`three/addons/controls/OrbitControls.js`)、Vite 8.3.8、TypeScript、Python 3 + Python Playwright + Pillow、img2threejs forge 腳本。

**Spec:** 無獨立 spec 文件。範圍寫在 Global Constraints。建模規格是 `object-sculpt-spec.json`。v7 計畫 (`docs/superpowers/plans/2026-11-22-caltex-station-img2threejs-v7.md`) 經兩份審查後由本版取代。

## Global Constraints

- 目標外觀是 `v3.webp` (`reference/diorama.png`)。
- `K=/Users/shyin/.claude-shyin/skills/img2threejs`，腳本在專案資料夾執行，找檔用 `find -L`。
- `src/createCaltexStationModel.ts` 不手改，只能改 spec 再跑 `generate_threejs_factory.py`。
- 資料夾是 git repo，rollback 點是 tag `pre-v8`。每個 Task 完成後 commit 一次。改 spec 前也備份到 `backup/spec_before_v8.json`。
- 改 spec 一律用 `scripts/build_spec_v8.py`。腳本每次先從備份還原，再套改動，可以重跑。腳本保留 `reviewHistory`。
- factory 的顏色取自 `materials[].baseColor`、`.color`、`.albedo.dominant`。元件的 `colorMaterialRecipe` 只是 userData，改它沒有效果。
- cylinder 的位置取自 `attachment.localStart/localEnd`，粗細取自 `attachment.baseRadius/endRadius`，`transform.scale` 對它沒有效果。
- draw calls 上限 160。目前 149，每個可見的材質 group 算一個 call。`main.ts` 的燈光都不投陰影，關陰影省不到 call。
- draw calls 一律取 12 個環景角度的最大值。
- `?gate=1` 的參考相機不改 (`az -50.89, el 9.51, dist 48.52, fov 20, target [-0.21,2.2,-0.11]`)。
- 標誌、CALTEX 字、旗面的 SVG 不改。
- 推論的面 (背面、屋頂、柱子新位置) 寫進 spec `assumptions`，並列進 `REPORT.md`。
- 截圖用 Python Playwright headless Chromium，參數 `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`。截圖前等 `__IMG2THREEJS_READY__`，再等 `networkidle` 與 500ms。
- 腳本開頭先 `curl -s localhost:5173`，失敗就背景啟動 `npx vite --port 5173`。
- 每步完成後複製新的 summary 快照，`.img2threejs/ledger.md` 加一行。

## Review Focus

1. 旗桿穿過雨棚 (`flagpole-1` 在 x 1.7、z 6.9，落在雨棚範圍內)：Task 2 的 `check_scene.py` 斷言零件不穿雨棚。
2. 拖曳旋轉放開滑鼠時，click 事件會觸發，選取被誤換掉：Task 1 斷言 2。
3. 補面材質讓 draw calls 超過 160：Task 4 先做 group 合併，Task 2、4、6 各量一次最大值。
4. 背面貼圖左右相反：roundel 底 cap 不翻轉，旗子 `-z` 面要翻轉。Task 4 看 az 180。
5. 相機轉到底座下方，或被 maxPolarAngle 卡住預設視角：Task 1 斷言 5，Task 5 預設仰角 ≥ 4°。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你要做什麼 |
| --- | --- | --- |
| A | Task 1 | 開 http://localhost:5173 拖曳、縮放、點零件 |
| B | Task 5 | 看新視角並排圖與比例，確認柱子、加油機、停車格 |
| C | Task 7 | 看 12 角度環景與 reviewer 分數，驗收 |

draw calls 合併後仍超過 160，或色差調 3 次仍不過，就停下問你。

---

### Task 1: OrbitControls (停點 A)

**Files:**
- Modify: `src/main.ts:1-35`、`src/main.ts:222-227`、`src/main.ts:242-258`
- Create: `scripts/check_orbit.py`

**Interfaces:**
- Produces: `controls: OrbitControls`。`window.__IMG2THREEJS_VIEWER__` 加 `controls`。`setCamera()` 結束時，`controls.target` 等於 `cam.target`。

- [ ] **Step 1: 寫 `scripts/check_orbit.py`**

開一般模式，viewport 1280x800。「相機穩定」的定義：連讀兩次相隔 200ms，位置差 < 1e-4。斷言：
1. 從畫面中心向右拖 300px，相機穩定後，x 或 z 變化 > 1。
2. 先 `__IMG2THREEJS_PICK__.select('canopy')`，拖曳後 `#sel` 仍是 `canopy`。
3. 先 `select(null)`，再把 `mart` 世界中心投影到螢幕座標，單擊不移動。`#sel` 變成非 `click a part` 的 id。
4. 相機穩定後 `set_viewport_size(1000, 700)`，再等穩定，位置差 < 0.01。
5. 向上拖 2000px，相機穩定後 `camera.position.y > controls.target.y`。
6. `setCamera({azimuth: 40, target: [1, 2, 3]})` 後，`controls.target` 等於 `(1,2,3)`。
7. 全程 `pageerror` 數為 0。

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 scripts/check_orbit.py`
Expected: 斷言 1 FAIL。

- [ ] **Step 3: 改 `src/main.ts`**

- 加 `OrbitControls(camera, renderer.domElement)`，`enableDamping = true`，target 取 `cam.target`。
- `maxPolarAngle = Math.PI / 2 - 0.05`、`minDistance = 12`、`maxDistance = 90`。
- `loop()` 每幀 `controls.update()` 再 render。
- `resize()` 只更新 aspect、projection 與 renderer 尺寸，不呼叫 `applyCamera()`。
- `setCamera()` 結束時 `controls.target.copy(cam.target); controls.update()`。
- click：`pointerdown` 記座標，位移 > 5px 的 click 直接 return。

- [ ] **Step 4: 驗證**

Run: `npx tsc --noEmit && python3 scripts/check_orbit.py && npx vite build`
Expected: 全部 exit 0，7 個斷言 PASS。

- [ ] **Step 5: 停點 A**

---

### Task 2: 環景、場景檢查與原門檻基準

**Files:**
- Create: `scripts/turntable.py`、`scripts/check_scene.py`、`shots/v8_checklist.md`、`shots/v8_base_*`

**Interfaces:**
- Produces:
  - `python3 scripts/turntable.py <tag>` 輸出 13 張 `?gate=1` 截圖：`shots/v8_<tag>_ref.png`、8 張 `_az{000..315}` (el 22、dist 40、fov 30、target `[0,1.5,0]`)、`_low` (az -51、el 5)、`_high` (az -51、el 60)、`_top` (az 0、el 85)、`_back` (az 130、el 12)。另輸出 4x4 拼圖 `_sheet.png`。
  - `python3 scripts/check_scene.py` 在上面 12 個角度量 `renderer.info.render.calls`，輸出 `{"drawCallsMax": N, "piercing": [...]}` 到 `shots/v8_scene.json`。
  - piercing 規則：root 下非 canopy 子孫的零件，world bbox 頂端高於 soffit 底 (y 4.84)，且 xz 範圍與 canopy bbox 重疊，就列入。
  - exit 0 條件：`drawCallsMax ≤ 160` 且 `piercing` 為空。

- [ ] **Step 1: 寫兩支腳本**

turntable 的 exit 0 條件：13 張都存在，且像素標準差 > 5。

- [ ] **Step 2: 寫 `shots/v8_checklist.md`**

每個角度檢查 10 項：
1. 旗子兩面有圖，canton 在旗桿側。
2. roundel 兩面有圖，星形不反。
3. CALTEX 在雨棚兩個長邊，字不反。
4. 加油機頂牌兩面有內容。
5. Mart 四面有橘帶，背面有門。
6. 雨棚頂面不是整片暗橘。
7. 沒有零件浮空、穿出底座或穿過雨棚。
8. 沒有透明的面。
9. 柱子立在加油島上。
10. 每台加油機兩側都有黃框停車格與黑黃輪擋。

- [ ] **Step 3: 拍基準並記錄原門檻分數**

Run: `python3 scripts/turntable.py base; python3 scripts/check_scene.py`
Expected: turntable exit 0。check_scene 預期 FAIL，因為 `flagpole-1` 穿過雨棚。把這次輸出記進 ledger 當基準。

派一個 Opus subagent，只給它 `reference/diorama.png` 與 `shots/v8_base_sheet.png`。它照原門檻評 5 個 critical feature：0.8 / 0.8 / 0.75 / 0.75 / 0.8，important 平均 0.65，整體 ≥ 0.70。分數寫進 ledger，標題「Fix4 驗收結果未記錄，v8 基準以此為準」。

---

### Task 3: spec 改形體與配置 (refine-spec)

**Files:**
- Create: `backup/spec_before_v8.json`、`scripts/build_spec_v8.py`
- Modify: `object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)

**Interfaces:**
- Produces:
  - 新元件 `canopy-wordmark-back` (parent `canopy`，box，material `decal-white`)。
  - 新元件 `pump-panel-1..4` (parent `pump-N`，box，material `pump-white`)。
  - 新元件 `wheel-stop-5..8` (parent `pump-N`)。
  - 刪除 `parking-line-1..3` (改成 Task 4 的地面貼圖)。

- [ ] **Step 1: 備份**

Run: `mkdir -p backup scripts && cp object-sculpt-spec.json backup/spec_before_v8.json`

- [ ] **Step 2: 寫 `scripts/build_spec_v8.py`**

數值是我依 v3 像素估的 (推論)，要靠 Task 5 的並排圖確認。改到的元件，`dimensions`、`transform.scale`、`attachment` 三處要同步改。

| 元件 | 欄位 | 現值 | 新值 |
| --- | --- | --- | --- |
| `roundel-logo` | `attachment.baseRadius/endRadius` | 0.75 | 0.475 |
| `roundel-logo` | localStart/localEnd 的 y | 0.4 | 0.45 |
| `flagpole-1` | localStart/End 的 x、z (與 transform 同步) | 1.7、6.9 | 4.4、8.0 (雨棚 x 上限 4.2 之外，Mart z 上限 7.0 之外) |
| `flagpole-2` | localStart/End 的 x、z (與 transform 同步) | 5.6、7.6 | 7.0、8.4 (旗面 x 7.0–9.4，不與旗 1 的 4.4–6.8 重疊) |
| `column-1..4` | localStart/End 的 x、z (canopy local) | 角落 | 立在各自加油島 -z 端：`(-1.45, 2.25)`、`(-1.45, -3.15)`、`(2.35, 2.25)`、`(2.35, -3.15)` |
| `pump-island-1..4` | scale z | 2.8 | 3.4，中心 z 往 -0.3 移 |
| `pump-1..4` (機身) | scale y、position y | 1.5、1.11 | 0.9、0.81 |
| `pump-panel-1..4` | 新增 | 無 | 0.52 x 0.7 x 0.72，在機身上方。`pump-screen-N` 改掛在 panel 上 |
| `pump-poster-blue-1..4` | 刪除 | 有 | 無 (v3 沒有藍色側塊) |
| `materials[pump-orange]` | `baseColor`、`color`、`albedo.dominant` | `#D2401F` | 依 Task 5 色差調整，起始值 `#E2582A` |
| `tree-1`、`tree-2` | 直徑 | 1.7 | 1.0 |
| `tree-3`、`tree-4` | 直徑 | 2.1 | 1.4 |
| `tree-N-trunk` | localEnd.y | 1.9 | 1.1，crown 跟著下移 |
| `mart-band` | height、position.y | 0.5、1.34 | 0.8、1.19 |
| `mart-sign` | height、depth | 0.42、1.4 | 0.65、2.0 |
| `wheel-stop-1..4` | position x | -1.1 | -1.3 (加油機 -x 側車格) |
| `wheel-stop-5..8` | 新增 | 無 | 複製 1..4，x 改 +1.3 |
| `canopy-wordmark-back` | 新增 | 無 | 複製 `canopy-wordmark`，x +5.77、z -1.5 |
| `parking-line-1..3` | 刪除 | 有 | 無 |
| `assumptions` | 加 4 條 | | 柱子位置、Mart 後門、雨棚頂色、wordmark 背面，皆為推論 |

新元件要補 `topologyClass`、`topologyRationale`、`colorMaterialRecipe`，並設 `confidence: 0.4`。刪掉的元件，也要從 `repetitionSystems`、`di.json` 的 `mapsTo` 移除。

- [ ] **Step 3: 驗證並生成**

Run: `python3 scripts/build_spec_v8.py && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts --force && npx tsc --noEmit`
Expected: 全部 exit 0。

- [ ] **Step 4: 跑 refine-spec 的 gates**

pass-id 用 `optimization-pass`，照 v6 Pass loop 的步驟 3、5、6、7、10、11 執行：
- `render-capture` 改用 `scripts/turntable.py refine`。
- 跑 Tier 1、`diagnose_render_multi_angle.py`、`turntable_gate.py --allow-holes`、`interior_difference.py` (baseline `shots/v8_base_ref.png`)、`attachment_anchor.py`、`make_comparison_sheet.py`。
- `append_review` 記一筆 `refine-spec`，附 gates 輸出。
- `state.py` 沒有 reopen 指令。在 ledger 記一條 ruling：這一輪只寫進 `reviewHistory`，不改 checklist。

Expected: `attachment_anchor.py` 0 errors，turntable gate pass。

---

### Task 4: 預覽層補面與 draw call 控制

**Files:**
- Modify: `src/main.ts:121-170`

**Interfaces:**
- Consumes: Task 3 的新元件 id
- Produces: `mergeGroups(mesh: THREE.Mesh): void`。它會把連續共用同一個材質的面合成一個 group，並刪掉 `visible: false` 材質的 group。

- [ ] **Step 1: 搬色相滑桿的收集程式**

`main.ts:166-170` 的 `baseColors` 收集移到材質覆寫 traverse 之前。這樣它拿到的是原本的單一材質物件。

- [ ] **Step 2: 補面材質**

BoxGeometry 面順序 `+x, -x, +y, -y, +z, -z`。
- 旗子：`-z` 面用同一張 PNG，`repeat.x = -1`。
- roundel：底 cap (index 2) 用 `decalTex`，不翻轉。
- `canopy-wordmark-back`：`+x` 面貼 wordmark，其餘 `hidden`。
- `pump-head-N`：`+x` 面換成 `signTex`。
- `mart`：`+x`、`+z`、`-z` 面用 canvas texture，白底加橘帶。橘帶的高度與位置在 runtime 從 `mart-band` 的 bbox 讀。`+x` 面中央加灰色門，寬 1.0、高 2.2。
- `canopy`：`+y` 面 `#e9e6e1`，其餘 5 面沿用原材質物件。
- `concrete-top`：`+y` 面用 canvas texture 畫 8 個黃框車格，每台加油機左右各一格 (2.2 x 4.8，線寬 0.1)。

- [ ] **Step 3: 合併 group**

所有被改成材質陣列的 mesh，包含既有的 kerb、wheel-stop、column-disc，都呼叫 `mergeGroups`。

- [ ] **Step 4: 驗證**

Run: `npx tsc --noEmit && python3 scripts/check_orbit.py && python3 scripts/turntable.py faces && python3 scripts/check_scene.py`
Expected: 全部 exit 0。檢查表第 1 到 6 項與第 10 項全過，az 180 的 roundel 星形不反。把 `#s-hue` 設 20，canopy 側面要變色。
draw calls 仍超過 160 時，停下問使用者：放寬上限，或把 4 個 `wheel-stop-5..8` 改成地面貼圖。

---

### Task 5: 預設視角與色差 (停點 B)

**Files:**
- Modify: `src/main.ts:21-35`
- Create: `scripts/color_check.py`

- [ ] **Step 1: 一般模式預設相機**

fov 35，target `[0, 1.2, 0]`，azimuth -50.89。相機 y 在 3.5 到 4.4 之間 (低於 soffit 底 4.84)，仰角 ≥ 4°。distance 調到底座寬佔畫面 85%。gate 相機不變。

- [ ] **Step 2: 寫 `scripts/color_check.py`**

v3 取 `reference/diorama.png` 的 (470,380)-(560,465) 框。render 取 `pump-1` 投影的 bbox。兩邊都取 H 0–25°、S > 0.45、V > 0.35 的像素中位數。用手寫的 CIE76 (Lab 歐氏距離) 算色差。exit 0 條件：ΔE ≤ 12。

- [ ] **Step 3: 調色**

Run: `python3 scripts/turntable.py color && python3 scripts/color_check.py shots/v8_color_ref.png`
不過就改 `build_spec_v8.py` 的 pump-orange，重跑 Task 3 Step 3，最多 3 次。

- [ ] **Step 4: 並排圖與停點 B**

截一般模式 1024x687 存成 `shots/v8_view_new.png`。
Run: `python3 $K/forge/stage4_review/make_comparison_sheet.py --reference reference/diorama.png --render shots/v8_view_new.png --out shots/v8_view_cmp.png --json`
給使用者看 `v8_view_cmp.png` 與 `v8_color_sheet.png`。

---

### Task 6: 土層紋理

**Files:**
- Modify: `src/main.ts`

- [ ] **Step 1: canvas texture**

`base-slab` 的 4 個側面用 canvas 畫土層：從 `reference/diorama.png` 的地層區取 2 個主色，鋪底色後灑 2% 到 4% 的深淺雜點。頂面與底面保留原材質，最後呼叫 `mergeGroups`。

- [ ] **Step 2: 驗證**

Run: `npx tsc --noEmit && python3 scripts/turntable.py soil && python3 scripts/check_scene.py`
Expected: exit 0，4 個側面看得到顆粒，沒有接縫錯位。

---

### Task 7: 驗收與文件 (停點 C)

**Files:**
- Modify: `parts.json`、`REPORT.md` (整份重寫成目前狀態)、`.img2threejs/ledger.md`
- Create: `shots/v8_final_*`、新的 summary 快照

- [ ] **Step 1: 全部檢查**

Run: `npx tsc --noEmit && npx vite build && python3 scripts/check_orbit.py && python3 scripts/turntable.py final && python3 scripts/check_scene.py && python3 scripts/color_check.py shots/v8_final_ref.png && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/run_gates.py --workspace .`
Expected: 全部 exit 0。

- [ ] **Step 2: parts.json 與 part coverage**

重新傾印 `parts.json`，方法同 v6 Task 8 Step 1。
Run: `python3 $K/forge/stage4_review/check_part_coverage.py --spec object-sculpt-spec.json --manifest parts.json --inventory di.json`
Expected: exit 0。

- [ ] **Step 3: 獨立 reviewer 照原門檻評分**

派 Opus subagent，只給 `reference/diorama.png`、`shots/v8_final_sheet.png`、`shots/v8_checklist.md`、Task 2 的基準分數。它要做兩件事：
1. 逐角度判定檢查表 10 項。
2. 照原門檻評 5 個 critical feature 與整體分數。

用 `append_review` 記一筆 `continue` 或 `refine-spec`。未達原門檻就照實記錄，不降門檻。

- [ ] **Step 4: 文件**

`REPORT.md` 整份重寫成目前狀態：操作方式、元件數、draw calls、12 角度結果、原門檻分數、推論清單。ledger 加一行，複製 summary 快照。

- [ ] **Step 5: 停點 C**

給使用者 http://localhost:5173、`shots/v8_final_sheet.png`、reviewer 分數。

---

## Self-Review

1. Spec coverage：兩份審查的 blocker 與 major 都對應到 Task。旗桿在 T3，柱子、加油機、停車格在 T3、T4，原門檻在 T2、T7，環景角度在 T2，refine-spec 在 T3 Step 4。
2. Step scan：比例數值標了推論，由停點 B 確認。draw calls 與色差都有上限和停點。
3. Type consistency：`turntable.py <tag>`、`check_scene.py`、`mergeGroups`、`canopy-wordmark-back`、`pump-panel-N`、`wheel-stop-5..8` 在各 Task 用法一致。
4. Review Focus：5 項分別落在 T2 piercing、T1 斷言 2 與 5、T4 Step 3 與 Step 4、T5 Step 1。
5. Proportion：沒有貼 code 本體，數值集中在 Task 3 的表格。
