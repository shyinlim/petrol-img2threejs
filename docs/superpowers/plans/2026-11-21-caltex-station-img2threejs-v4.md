# Caltex 加油站 Diorama img2threejs Implementation Plan (v4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把使用者選定的 diorama 圖 `v3.webp` 重建成 code-only 的 procedural Three.js 模型：地層切面底座、Caltex 加油站、Mart、旗桿、樹、垃圾桶，透視相機，淺色背景，右側滑桿面板。

**Architecture:** 用 img2threejs 的 23 步 checklist (`forge/next.py` 指定順序)。skill 產出 `createCaltexStationModel` factory，預覽頁 (我們自己寫) 負責相機、背景、滑桿。gate 截圖用獨立的 `?gate=1` 模式 (純色背景、無面板)。

**Tech Stack:** Python 3.12 (stdlib)、Node 24、Vite、three、TypeScript、Python Playwright、純 HTML range input。

**Spec:** 無獨立 spec 文件。範圍寫在 Global Constraints，建模規格是 `object-sculpt-spec.json` (Task 4 產出)。

## Global Constraints

- 參考圖：使用者選定 `/Users/shyin/Desktop/threejs/v3.webp`，轉成 `reference/diorama.png` 後使用。專案根目錄的 `v1.webp`、`v2.webp` 不動。
- 風格目標：地層切面底座 diorama、淺色背景、右側參數滑桿 (使用者選 C)。
- 相機：圖是透視視角 (從雨棚左前角看)，預覽用 `PerspectiveCamera`，FOV 與位置靠疊圖對齊。
- 範圍：底座 (白色水泥頂面、地層切面)、草地帶、雨棚 (橘色 fascia、白色 soffit 與嵌燈)、4 根柱子、4 台加油機、圓形標誌、CALTEX 字、Mart、2 支旗桿與旗、樹與灌木、藍綠垃圾桶、停車黃黑線。
- 不做：車輛、人、油罐車、背景建築。
- 重複物件 (樹、灌木、垃圾桶) 用 instancing，當成 repetition system。
- 旗面與標誌用 canvas decal，不下載圖檔，不追求精確。
- 單張圖看不到背面與被遮處，結果是 stylized 近似，報告標出推論區域，這些元件 confidence 標低。
- 原照片 `DSC05011 -copy.jpg` 不改，縮圖 `reference/ref_2000.jpg` 只用來交叉確認佈局。
- 圖是 1024x687，材質 crop 細節有限，不足處標推論。
- `K=/Users/shyin/.claude-shyin/skills/img2threejs`，腳本從專案資料夾用 `python3 $K/forge/...` 執行。
- 對象名稱固定 `Caltex Station`，factory 名稱是 `createCaltexStationModel`。
- 修正上限：全部 6 輪；每 pass 第 3 次 refine 決定就 hard stop，實際每 pass 2 輪修正。
- 滑桿只調預覽參數 (燈光方位角、橘色色相、雨棚高度)，不進 gate，不計入 pass 評分。
- 資料夾不是 git repo，不做 commit，證據記在 `.img2threejs/state.json`。
- 各指令 flag 以 `SKILL.md` 與 `--help` 為準。

## Review Focus

1. render 的前景遮罩與參考圖遮罩用同一套規則：飽和度高於 0.16 且亮度低於 0.94 的背景會被判成前景。參考圖背景 `#E7D4C5` 飽和度 0.147，已接近上限，gate 截圖一律用 `#EAE6E1` 純色背景。
2. Tier 1 輪廓 IoU 門檻 0.85：透視相機要疊圖對齊，`solve_camera_pose.py` 只給起始猜測。
3. 柱子與雨棚底面在圖中部分被遮：以原照片與圖 `v2.webp` 當輔助證據，confidence 標低。
4. 柱間透空被 turntable gate 當成洞：用 `--allow-holes` 並寫下理由。
5. 預覽沒有 `window.__IMG2THREEJS_READY__`：截圖會拍到半載入畫面。
6. 樹、灌木、垃圾桶數量多：instancing 才不會超過 `performanceBudget`。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你看什麼 |
| --- | --- | --- |
| 1 | Task 2 | suitability 判定與對齊後的相機 |
| 2 | Task 4 | spec 通過 strict-quality |
| 3 | Task 6 | blockout 的輪廓與比例 |
| 4 | Task 8 | 成品預覽、滑桿面板、推論區域清單 |

其餘 pass 由執行者自跑。gate 失敗、到修正上限、需補圖才停下問你。

---

### Task 1: 參考圖與 state 初始化

**Files:**
- Create: `reference/ref_2000.jpg`、`reference/diorama_v3.webp`、`reference/diorama.png`、`reference/diorama_v2.webp`、`.img2threejs/state.json`

**Interfaces:**
- Produces: `diorama.png` (所有 `--reference` 與 `--image` 用)、`ref_2000.jpg` 與 `diorama_v2.webp` (輔助證據)

- [ ] **Step 1: 縮原照片並整理參考圖**

Run: `cp v3.webp reference/diorama_v3.webp && cp v2.webp reference/diorama_v2.webp && sips -s format png v3.webp --out reference/diorama.png && sips -Z 2000 "DSC05011 -copy.jpg" --out reference/ref_2000.jpg`
Expected: `reference/` 有 4 個檔案，`diorama.png` 是 1024x687。

- [ ] **Step 2: 驗證 diorama 參考圖**

用 Read 開 `reference/diorama.png`，並跑 `python3 $K/forge/stage1_intake/probe_image.py reference/diorama.png`。再用 `extract_pbr_evidence.build_foreground_mask` 檢查前景比例。
Expected: 單一物件置中、完整不裁切、`technicalSuitability: pass`、前景比例在 0.15 到 0.6 之間且無警告 (scratchpad 試跑 v3 為 0.556)。

- [ ] **Step 3: 初始化 state**

Run: `python3 $K/forge/state.py init --state .img2threejs/state.json --reference reference/diorama.png --profile generic --spec object-sculpt-spec.json`
Expected: 輸出 `step=image-analysis`。

- [ ] **Step 4: 確認下一步**

Run: `python3 $K/forge/next.py --state .img2threejs/state.json`
Expected: `next command: Read grimoire/intake/image_analysis.md ...`，列出 23 個 pending 步驟。

---

### Task 2: Intake 與 suitability (停點 1)

**Files:**
- Create: `analysis.md`、`probe.json`、`assessment.json`

**Interfaces:**
- Consumes: `reference/diorama.png`、`reference/ref_2000.jpg`、`reference/diorama_v2.webp`
- Produces: `assessment.json`、對齊後的 `referenceCamera`

- [ ] **Step 1: 寫 `analysis.md`**

依 `grimoire/intake/image_analysis.md` 8 層寫，觀察與推論分開標。記錄來源：參考圖由使用者用外部工具生成，生成 prompt 未完整保存。結尾寫 suitability 判定 (依 `validation_rubric.md` 的 Pass 與 Conditional 條款) 與接受條件：背面是推論、旗與標誌不精確。

- [ ] **Step 2: reference admission 並寫 probe**

先 `find $K/forge -name "check_reference_admission.py"`，再依 `--help` 對 `reference/diorama.png` 執行，加 `--probe-out probe.json`。
Expected: 通過，`probe.json` 存在。

- [ ] **Step 3: 評估**

Run: `python3 $K/forge/stage2_spec/new_pre_spec_assessment.py "Caltex Station" --image reference/diorama.png --complexity complex --out assessment.json`，加上 `--spec-query` 查詢詞 (diorama、canopy、gas pump、ground slab、instanced trees，詞表見 `grimoire/intake/local_spec_search.md`)。
Expected: `assessment.json` 含 `localSpecSearch`。

- [ ] **Step 4: referenceCamera 起始猜測**

Run: `python3 $K/forge/stage1_intake/solve_camera_pose.py reference/diorama.png --fov-degrees 35 --out camera.json`
Expected: `camera.json` 含 FOV 與 `agentFill` 的 yaw、pitch、position 欄位 (腳本不解真實姿態，這裡只是起點)。

- [ ] **Step 5: 疊圖對齊**

Task 5 的預覽完成後，回來調整 yaw、pitch、distance、FOV，直到 render 的底座邊與雨棚輪廓和參考圖對上，結果寫回 `camera.json`。對齊記錄放 `shots/camera_align_*.png`。

- [ ] **Step 6: 標記步驟**

對 `image-analysis`、`reference-suitability`、`reference-admission`、`local-spec-search`、`pre-spec-assessment` 各跑 `python3 $K/forge/state.py mark <step-id> --state .img2threejs/state.json --evidence <path>`，依序標記。
Expected: `next.py` 轉到 `detail-inventory`。

- [ ] **Step 7: 停點 1**

回報 suitability 判定與相機對齊結果，等同意再繼續。

---

### Task 3: 細節清單與 projection 判斷

**Files:**
- Create: `detail/`、`di.json`

**Interfaces:**
- Consumes: `assessment.json`
- Produces: `di.json` (每個細節對應 `component.localFeatures` 或 `material.localOverrides`)

- [ ] **Step 1: 建清單**

Run: `python3 $K/forge/stage1_intake/build_detail_inventory.py reference/diorama.png --mode grid-3x3 --complexity complex --out-dir detail --out di.json`
Expected: `di.json` 存在，`detail/` 有 9 格圖。

- [ ] **Step 2: 補細節**

逐格補：地層切面層次、草地帶邊緣、fascia 倒角、soffit 嵌燈、柱子與編號圓牌、加油機 Techron 招牌、圓形標誌星形、CALTEX 字、Mart 橘帶與窗、旗面圖樣、樹與灌木形狀、垃圾桶、停車黃黑線。數量不低於 `targetMinDetails`。

- [ ] **Step 3: projection-route 標 skipped**

Run: `python3 $K/forge/state.py mark projection-route --state .img2threejs/state.json --status skipped --reason "flat stylized paint uses solid albedo; logo and flags via canvas decal, exact fidelity not required"`
Expected: `next.py` 轉到 `spec-authoring`。

---

### Task 4: Spec、材質、驗證 (停點 2)

**Files:**
- Create: `object-sculpt-spec.json`、`crops/`、`material-evidence/`

**Interfaces:**
- Consumes: `assessment.json`、`di.json`
- Produces: 通過 `--strict-quality` 的 spec，含元件階層、材質、repetition system、pivot、socket

- [ ] **Step 1: 產生 spec**

Run: `python3 $K/forge/stage2_spec/new_sculpt_spec.py "Caltex Station" --image reference/diorama.png --assessment assessment.json --out object-sculpt-spec.json`

- [ ] **Step 2: 補元件階層**

macro：base-slab (根，含地層切面)、grass-verges、canopy、columns、pump-island、pump、roundel-logo、sign、mart、flagpoles、trees (instanced)、bushes (instanced)、bins (instanced)、parking-lines。柱子設 `role: support`，填 parentSocket、contactType、embedDepth。每個元件填 `topologyClass` 與 `topologyRationale`。被遮處的元件 confidence 標低，evidence ref 指向 `diorama_v2.webp` 或 `ref_2000.jpg`。

- [ ] **Step 3: 材質 crop 與分析**

地層切面、白色水泥頂面、草地、橘色 fascia、白色 soffit、柱子、加油機外殼、Mart 外牆、垃圾桶各切一張 crop 放 `crops/` (從 `diorama.png` 切)，每張跑兩支：
`python3 $K/forge/stage1_intake/analyze_texture.py crops/<name>.png --spec object-sculpt-spec.json --material-id <id> --in-place`
`python3 $K/forge/stage1_intake/extract_pbr_evidence.py crops/<name>.png --out-dir material-evidence --material-id <id> --spec object-sculpt-spec.json --in-place`
Expected: confidence 低於 0.7 就重切 crop，仍不足就標推論。

- [ ] **Step 4: 標記 material-spec-wiring**

用 `--status skipped --reason "analyze_texture and extract_pbr_evidence wrote materials via --in-place"`。
Expected: `next.py` 轉到 `strict-validation`。

- [ ] **Step 5: 驗證**

Run: `python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality`
Expected: 兩次都 exit 0。

- [ ] **Step 6: 標記並停點 2**

標記 `spec-authoring`、`material-evidence`、`strict-validation` (附證據)，回報使用者看 spec 摘要，等同意再繼續。

---

### Task 5: 預覽 harness、gate 模式與滑桿面板

**Files:**
- Create: `package.json`、`index.html`、`src/main.ts`

**Interfaces:**
- Consumes: `createCaltexStationModel(spec, options): THREE.Group`、`camera.json`
- Produces: `http://localhost:5173`，頁面設 `window.__IMG2THREEJS_READY__`、`window.__IMG2THREEJS_VIEWER__ = { renderer, scene, camera }`、`window.__IMG2THREEJS_CAPTURE__.setCamera(spec)`；`?gate=1` 模式用 `#EAE6E1` 純色背景、無面板、無地面陰影

- [ ] **Step 1: 安裝**

Run: `npm init -y && npm i three && npm i -D vite typescript @types/three`
Expected: 無 error，記下 `three` 版本。

- [ ] **Step 2: 寫 `index.html` 與 `src/main.ts`**

先放占位 box 當 factory。用 `PerspectiveCamera`，初始值取 `camera.json`。一般模式背景色取參考圖 `#E7D4C5`。`setCamera` 接受 `{azimuth, elevation, distance, fov}`，供 4 個 turntable 角度與參考視角。第一個 frame 渲染完才設 `__IMG2THREEJS_READY__ = true`。

- [ ] **Step 3: 滑桿面板**

右側固定面板，3 個 `<input type="range">`：燈光方位角、橘色色相、雨棚高度比例。事件改 light 與 material 參數，不重新生成 factory。`?gate=1` 時隱藏面板。

- [ ] **Step 4: 驗證**

Run: `npx vite --port 5173` (背景)，開 `?gate=1` 讀 `window.__IMG2THREEJS_READY__`，截圖後用 `build_foreground_mask` 檢查前景比例。
Expected: `true`，占位 box 的前景比例合理且無警告。`scripts/capture_threejs_playwright.py` 的需求以 `--help` 為準。

---

### Pass loop (Task 6 與 Task 7 共用)

每個 pass 照此執行，只動目前解鎖的 pass。每步完成後標對應 checklist 步驟並附證據，順序不可亂 (新 pass 與每次 refine 都會讓這 8 步重置)。

1. `python3 $K/forge/stage3_build/orchestrate_passes.py status object-sculpt-spec.json`
2. `generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts` (新 pass 加 `--force`)。標 `build-current-pass`。
3. 截圖 (用 `?gate=1`)：參考視角 `shots/<pass-id>_ref.png`，加 4 個 turntable 角度 `_az0`、`_az90`、`_az180`、`_az270`。標 `render-capture`。
4. 重讀 `grimoire/review/gates_reference.md` 與 `self_correction.md`。標 `review-contract-read`。
5. `diagnose_render.py` 與 `diagnose_render_multi_angle.py`，`--reference reference/diorama.png --spec object-sculpt-spec.json --pass-id <pass-id> --in-place`，render 用 `_ref.png`。標 `tier1-diagnostics`、`multi-angle-review`。
6. `turntable_gate.py --capture 0=... --capture 90=... --capture 180=... --capture 270=... --allow-holes --json` (理由：柱間透空)。`interior_difference.py` 檢查輪廓內差異。
7. `self_intersection.py`：用 `evaluate_script` 把 world-space 頂點與索引傾印成它讀的格式 (安裝版缺 `runtime/scripts/export_mesh_geometry.mjs`，格式未驗證)，失敗就在 review 記「未執行」。
8. `orchestrate_passes.py check object-sculpt-spec.json --pass-id <pass-id>`。標 `pass-gate-check`。
9. `make_comparison_sheet.py --reference reference/diorama.png --render shots/<pass-id>_ref.png --out shots/<pass-id>_cmp.png --json`，用 vision 看對照圖。
10. `append_review.py` 記分並選一個 action：`continue`、`refine-spec`、`refine-code`、`request-input`、`stop`。標 `ai-review-recorded`。
11. `orchestrate_passes.py sync object-sculpt-spec.json --in-place`，標 `pipeline-sync`，再跑 `next.py`。

Expected: `next.py` 指到下一個 pass，loop 計數未到上限。

---

### Task 6: Pass 1 blockout (停點 3)

**Files:**
- Create: `src/createCaltexStationModel.ts`、`shots/blockout_*.png`

**Interfaces:**
- Consumes: Task 4 的 spec、Task 5 的預覽
- Produces: 輪廓與比例正確的 blockout

- [ ] **Step 1: 預覽頁接上 factory**

`src/main.ts` 以真實 factory 取代占位 box，回頭完成 Task 2 Step 5 的相機對齊。

- [ ] **Step 2: 跑 Pass loop，pass-id 為 `blockout`**

Expected: review 記錄 `continue`，`root.userData.sculptRuntime` 存在。

- [ ] **Step 3: 停點 3**

給使用者看並排對照圖，確認底座比例、屋頂比例、柱子、加油機、Mart 位置。不對就 `refine-spec`，不往下走。

---

### Task 7: Pass 2 到 8

**Files:**
- Modify: `object-sculpt-spec.json`、`src/createCaltexStationModel.ts`

**Interfaces:**
- Consumes: Task 6 的 factory
- Produces: 7 個 pass 全部 `continue`

- [ ] **Step 1: 依序跑 Pass loop**

順序：`structural-pass`、`form-refinement`、`material-pass`、`surface-pass`、`lighting-pass`、`interaction-pass`、`optimization-pass`。

- [ ] **Step 2: 進 material-pass 前先看缺口**

跑 `orchestrate_passes.py status object-sculpt-spec.json`，確認 `material_pass_gaps` 要求哪些貼圖與覆蓋。平塗風格若被要求完整貼圖，停下問使用者要不要降低要求。

- [ ] **Step 3: material-pass 額外檢查**

橘色 fascia、草地、地層切面色相對照參考圖，跑 `material_views.py`、`material_comparator.py`、`material_gate.py`，指令見 `grimoire/scripts.md`。

- [ ] **Step 4: lighting-pass 與滑桿一致**

lighting-pass 通過的燈光是滑桿預設值，滑桿拖動範圍在 spec 的 lighting 區塊定義。

- [ ] **Step 5: optimization-pass 額外檢查**

記錄 `renderer.info` 的 draw calls 與 triangles，樹、灌木、垃圾桶確認走 instancing，在 `performanceBudget` 範圍內。

---

### Task 8: 收尾 (停點 4)

**Files:**
- Create: `parts.json`、`REPORT.md`

**Interfaces:**
- Consumes: 全部 pass 通過的 spec 與 factory
- Produces: 可拆解、可點選的模型加推論區域清單

- [ ] **Step 1: 產生 `parts.json`**

用 `evaluate_script` 從 `root.userData.sculptRuntime` 傾印元件清單，存 `parts.json`。

- [ ] **Step 2: part coverage**

Run: `python3 $K/forge/stage4_review/check_part_coverage.py --spec object-sculpt-spec.json --manifest parts.json --inventory di.json`
Expected: exit 0。

- [ ] **Step 3: 標記剩餘步驟**

`part-coverage`、`action-ready` 附證據標 done。`emission-target`：`--status skipped --reason "no emission target selected"`。`plugin-gates`：跑 `python3 $K/forge/stage3_build/run_gates.py --workspace .`，exit 0 後附輸出標 done。
Expected: `next.py` 顯示全部完成。

- [ ] **Step 4: 寫 `REPORT.md`**

列輸出檔案、各 pass 分數、推論區域 (背面、被遮擋處、旗面與標誌)、近似程度聲明、滑桿參數清單。

- [ ] **Step 5: 停點 4**

給使用者預覽網址 `http://localhost:5173` 與 `REPORT.md`。

---

## Self-Review

1. Spec coverage：23 個 checklist 步驟皆有對應 (Task 1 到 4 覆蓋前 11 步，Pass loop 覆蓋 8 步，Task 8 覆蓋最後 4 步)；v3.webp 的底座、Mart、旗桿、樹、垃圾桶、停車線分別在 Task 3、4。
2. Step scan：未驗證處已標明 (`solve_camera_pose` 對齊方式、`self_intersection` 輸入格式、`material_pass_gaps`、spec 掛輔助證據)。
3. Type consistency：對象 `Caltex Station`、factory `createCaltexStationModel`、參考圖 `reference/diorama.png` 在各 Task 一致。
4. Review Focus：6 項皆有對應步驟 (Task 1、2、4、5、Pass loop 第 6 步、Task 7)。
5. Proportion：沒有貼 code 本體，滑桿只用原生 HTML，不加套件。
