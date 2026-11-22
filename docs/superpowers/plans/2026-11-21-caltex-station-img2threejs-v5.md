# Caltex 加油站 Diorama img2threejs Implementation Plan (v5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把使用者選定的 diorama 圖 `v3.webp` 重建成 code-only 的 procedural Three.js 模型：地層切面底座、Caltex 加油站、Mart、旗桿、樹、垃圾桶，透視相機，淺色背景，右側滑桿面板。

**Architecture:** 用 img2threejs 的 23 步 checklist (`forge/next.py` 指定順序)。skill 產出 `createCaltexStationModel` factory，預覽頁 (我們自己寫) 負責相機、背景、滑桿。gate 截圖用獨立的 `?gate=1` 模式 (深灰純色背景、1024x687、無面板)，Tier 1 對照去背的參考圖。

**Tech Stack:** Python 3.12 (stdlib)、Node 24、Vite、three、TypeScript、Python Playwright、純 HTML range input。

**Spec:** 無獨立 spec 文件。範圍寫在 Global Constraints，建模規格是 `object-sculpt-spec.json` (Task 4 產出)。

## Global Constraints

- 參考圖原檔：`/Users/shyin/Desktop/threejs/v3.webp`，轉成 `reference/diorama.png` 供材質 crop 與視覺對照。專案根目錄的 `v1.webp`、`v2.webp` 不動。
- 去背參考圖：`reference/diorama_isolated.png` (有 alpha、不含地面投影)，由使用者用 Preview 的移除背景產生。SAM2 沒安裝 (`run_vision_adapter.py` 要先 `uv sync`)，安裝要使用者同意。`state.py init --reference` 與所有 Tier 1 `--reference` 都用這張。
- 風格目標：地層切面底座 diorama、淺色背景、右側參數滑桿 (使用者選 C)。
- 相機：圖是透視視角 (從雨棚左前角看)，預覽用 `PerspectiveCamera`，FOV 與位置靠疊圖對齊，結果寫進 `spec.referenceCamera`。
- gate 截圖：一律 1024x687 (與參考圖同長寬比)、背景 `#303030`。
- 範圍：底座 (白色水泥頂面、地層切面)、草地帶、雨棚 (橘色 fascia、白色 soffit 與嵌燈)、4 根柱子、4 台加油機、圓形標誌、CALTEX 字、Mart、2 支旗桿與旗、樹與灌木、藍綠垃圾桶、停車黃黑線。
- 不做：車輛、人、油罐車、背景建築。
- 樹、灌木、垃圾桶各自建成獨立元件。spec 只放 1 筆 `repetitionSystems` (`elementComponentIds` 列出全部)，generator 不會為它放置實體，它只用來滿足 strict-quality 的下限 1。
- 旗面與標誌用 canvas decal，不下載圖檔，不追求精確。
- 單張圖看不到背面與被遮處，結果是 stylized 近似，報告標出推論區域，這些元件 confidence 標低。
- 輔助證據圖 (`diorama_v2.webp`、`ref_2000.jpg`) 以 `viewEvidence` 項目登記，額外加 `sourceImage` 欄位 (只是文件，沒有腳本讀它)；`evidenceRefs` 只能填 `viewEvidence` 的 id，不能填檔案路徑。
- 原照片 `DSC05011 -copy.jpg` 不改，縮圖 `reference/ref_2000.jpg` 只用來交叉確認佈局。
- 圖是 1024x687，材質 crop 細節有限，不足處標推論。
- `K=/Users/shyin/.claude-shyin/skills/img2threejs`，腳本從專案資料夾用 `python3 $K/forge/...` 執行。
- 對象名稱固定 `Caltex Station`，factory 名稱是 `createCaltexStationModel`。
- 修正上限：全部 6 輪的上限在第 6 次 refine 決定就停，實際最多 5 輪；每 pass 第 3 次 refine 決定就停，實際每 pass 2 輪。
- 滑桿只調預覽參數 (燈光方位角、橘色色相、雨棚高度)，不進 gate，不計入 pass 評分。
- 資料夾不是 git repo，不做 commit，證據記在 `.img2threejs/state.json`。
- 每個 checklist 步驟做完就立刻標記，順序不可跳。
- 各指令 flag 以 `SKILL.md` 與 `--help` 為準。

## Review Focus

1. Tier 1 的輪廓 IoU 門檻是 0.85：用原圖當參考，背景雜訊讓前景比例虛高 (0.556 對真實約 0.37)，IoU 只有約 0.66 到 0.69 (subagent 在暫存目錄實測，我未重跑)，所以參考圖必須去背。
2. gate 背景若與白色底座太接近，render 的遮罩會塌成整張：用 `#303030`。
3. 柱子與雨棚底面在圖中部分被遮：以原照片與 `v2.webp` 當輔助證據，confidence 標低。
4. 柱間透空被 turntable gate 當成洞：用 `--allow-holes` 並寫下理由。
5. 預覽沒有 `window.__IMG2THREEJS_READY__`：截圖會拍到半載入畫面。
6. 小配件 (藍色與綠色垃圾桶) 的顏色在 Tier 1 的逐部位色差檢查可能超過 ΔE 20：預留 request-input 停點。
7. 橘色 fascia 的 PBR confidence 實測 0.691，低於 0.7：預留 request-input 停點。
8. 元件數量多，draw calls 可能超過預設預算 160 (未驗證)：optimization-pass 實測。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你要做什麼 |
| --- | --- | --- |
| 0 | Task 1 前 | 用 Preview 移除背景，存 `reference/diorama_isolated.png` |
| 1 | Task 2 | 看 suitability 判定與對齊後的相機 |
| 2 | Task 4 | 看 spec 摘要；決定橘色 fascia confidence 0.691 的處理 |
| 3 | Task 6 | 看 blockout 的輪廓與比例 |
| 3b | material-pass | 決定小配件顏色色差超標時，合併或刪除它們的 recipe |
| 4 | Task 8 | 看成品預覽、滑桿面板、推論區域清單 |

其餘 pass 由執行者自跑。gate 失敗、到修正上限、需補圖才停下問你。

---

### Task 1: 參考圖與 state 初始化

**Files:**
- Create: `reference/ref_2000.jpg`、`reference/diorama_v3.webp`、`reference/diorama.png`、`reference/diorama_v2.webp`、`.img2threejs/state.json`
- Input (使用者提供): `reference/diorama_isolated.png`

**Interfaces:**
- Produces: `diorama.png` (材質 crop、視覺對照)、`diorama_isolated.png` (state 與 Tier 1 的 reference)、輔助證據圖

- [ ] **Step 1: 縮原照片並整理參考圖**

Run: `cp v3.webp reference/diorama_v3.webp && cp v2.webp reference/diorama_v2.webp && sips -s format png v3.webp --out reference/diorama.png && sips -Z 2000 "DSC05011 -copy.jpg" --out reference/ref_2000.jpg`
Expected: `reference/` 有 4 個檔案，`diorama.png` 是 1024x687。

- [ ] **Step 2: 停點 0，使用者去背**

使用者用 Preview 對 `reference/diorama.png` 做移除背景，存成 `reference/diorama_isolated.png`，不含地面投影。
Expected: 檔案存在且有 alpha。

- [ ] **Step 3: 驗證去背參考圖**

用 Read 開 `reference/diorama_isolated.png`，跑 `probe_image.py`，再用 `extract_pbr_evidence.build_foreground_mask` 檢查前景比例。
Expected: 單一物件置中、完整不裁切、`technicalSuitability: pass`、前景比例約 0.37、無警告。

- [ ] **Step 4: 初始化 state**

Run: `python3 $K/forge/state.py init --state .img2threejs/state.json --reference reference/diorama_isolated.png --profile generic --spec object-sculpt-spec.json`
Expected: 輸出 `step=image-analysis`。

- [ ] **Step 5: 確認下一步**

Run: `python3 $K/forge/next.py --state .img2threejs/state.json`
Expected: `next command: Read grimoire/intake/image_analysis.md ...`，列出 23 個 pending 步驟。

---

### Task 2: Intake 與 suitability (停點 1)

**Files:**
- Create: `analysis.md`、`admission.json`、`probe.json`、`assessment.json`、`camera.json`

**Interfaces:**
- Consumes: `reference/diorama_isolated.png`、`reference/ref_2000.jpg`、`reference/diorama_v2.webp`
- Produces: `assessment.json`、`camera.json`

- [ ] **Step 1: 寫 `analysis.md`**

依 `grimoire/intake/image_analysis.md` 8 層寫，觀察與推論分開標。記錄來源：參考圖由使用者用外部工具生成，生成 prompt 未完整保存。結尾寫 suitability 判定 (依 `validation_rubric.md` 的 Pass 與 Conditional 條款) 與接受條件：背面是推論、旗與標誌不精確。標 `image-analysis`。

- [ ] **Step 2: suitability 與 admission**

標 `reference-suitability` (附 `analysis.md`)。先 `find $K/forge -name "check_reference_admission.py"`，依 `--help` 對 `reference/diorama_isolated.png` 執行，加 `--out admission.json --probe-out probe.json`。標 `reference-admission`。
Expected: 通過，兩個 json 存在。

- [ ] **Step 3: 評估**

Run: `python3 $K/forge/stage2_spec/new_pre_spec_assessment.py "Caltex Station" --image reference/diorama_isolated.png --complexity complex --out assessment.json`，加上 `--spec-query` 查詢詞 (diorama、canopy、gas pump、ground slab，詞表見 `grimoire/intake/local_spec_search.md`)。標 `local-spec-search`、`pre-spec-assessment`。
Expected: `assessment.json` 含 `localSpecSearch`，`complex` 的下限是 macro 3、meso 8、micro 5、materials 3、repetition 1、viewpoints 4、targetMinDetails 10。

- [ ] **Step 4: referenceCamera 起始猜測**

Run: `python3 $K/forge/stage1_intake/solve_camera_pose.py reference/diorama.png --fov-degrees 35 --out camera.json`
Expected: `camera.json` 含 FOV 與 `agentFill` 的 yaw、pitch、position 欄位 (腳本不解真實姿態)。

- [ ] **Step 5: 疊圖對齊**

Task 6 預覽接上 factory 後，回來調整 yaw、pitch、distance、FOV，直到 render 的底座邊與雨棚輪廓和參考圖對上。可試 `solve_camera_pose.fit_camera_to_correspondences` (Python API，yaw 與 pitch 的座標慣例與 Three.js 是否一致未驗證)。結果寫回 `camera.json`，對齊記錄放 `shots/camera_align_*.png`。

- [ ] **Step 6: 停點 1**

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

- [ ] **Step 2: 補細節並標記**

逐格補：地層切面層次、草地帶邊緣、fascia 倒角、soffit 嵌燈、柱子與編號圓牌、加油機 Techron 招牌、圓形標誌星形、CALTEX 字、Mart 橘帶與窗、旗面圖樣、樹與灌木形狀、垃圾桶、停車黃黑線。數量不低於 `targetMinDetails`。先標 `detail-inventory` (附 `di.json`)。

- [ ] **Step 3: projection-route 標 skipped**

Run: `python3 $K/forge/state.py mark projection-route --state .img2threejs/state.json --status skipped --reason "flat stylized paint uses solid albedo; logo and flags via canvas decal, exact fidelity not required"`
Expected: `next.py` 轉到 `spec-authoring`。順序一定是先 `detail-inventory` 再 `projection-route`。

---

### Task 4: Spec、材質、驗證 (停點 2)

**Files:**
- Create: `object-sculpt-spec.json`、`crops/`、`material-evidence/`

**Interfaces:**
- Consumes: `assessment.json`、`di.json`、`camera.json`
- Produces: 通過 `--strict-quality` 的 spec，含元件階層、材質、pivot、socket

- [ ] **Step 1: 產生 spec**

Run: `python3 $K/forge/stage2_spec/new_sculpt_spec.py "Caltex Station" --image reference/diorama_isolated.png --assessment assessment.json --out object-sculpt-spec.json`

- [ ] **Step 2: 補元件階層與必填欄位**

- macro：base-slab (根，含地層切面)、canopy、mart、pump-island、trees、bushes、bins、flagpoles。
- meso (至少 8 個)：grass-verges、columns、fascia、soffit、roundel-logo、sign、pump、parking-lines 等。
- 圓柱、圓錐、capsule、tube 類 primitive (柱子、旗桿、樹幹、垃圾桶) 都要 attachment，填 `parentSocket`、`contactType`、`embedDepth`、`localStart`、`localEnd`、`gapTolerance`；柱子設 `role: support`。
- 每個元件填 `topologyClass`、`topologyRationale`、`colorMaterialRecipe` (rgba 字串)。
- `objectClass` 填 `primaryType`、`formLanguage`、`structureKind`、`motionPotential`、`materialFamilies`。
- `featureReviewTargets` 換成這個物件的真實特徵 (CALTEX 字、標誌位置、4 台加油機、4 根柱子、Mart 橘帶)。
- `lightingFromPhoto` 填 key、fill、rim、exposure、contact shadow。
- `qualityTargets.reviewViewpoints` 填 4 個視角。
- 1 筆 `repetitionSystems` 列全部樹、灌木、垃圾桶的 `elementComponentIds`。
- 被遮處的元件 confidence 標低，`viewEvidence` 指向 `diorama_v2.webp` 與 `ref_2000.jpg`。
- 把 `camera.json` 寫進 `spec.referenceCamera`。
標 `spec-authoring`。

- [ ] **Step 3: 材質 crop 與分析**

地層切面、白色水泥頂面、草地、橘色 fascia、白色 soffit、柱子、加油機外殼、Mart 外牆、垃圾桶各切一張 crop 放 `crops/` (從 `diorama.png` 切)，每張跑兩支：
`python3 $K/forge/stage1_intake/analyze_texture.py crops/<name>.png --spec object-sculpt-spec.json --material-id <id> --in-place`
`python3 $K/forge/stage1_intake/extract_pbr_evidence.py crops/<name>.png --out-dir material-evidence --material-id <id> --spec object-sculpt-spec.json --in-place`
Expected: 地層切面與草地 confidence 約 0.86 通過；橘色 fascia 0.691 低於 0.7，spec 不會被修補，這步停下問使用者 (見停點 2)。標 `material-evidence`。

- [ ] **Step 4: 決定平塗材質的路線 (停點 2)**

向使用者說明：平塗材質宣告 `textureless` 後，`orchestrate_passes.material_pass_gaps` 仍會報 5 個缺口，預設 `qualityPriority: reference-fidelity` 會啟用嚴格材質規則。提出建議：橘色 fascia、白色 soffit、水泥頂面、地層切面維持 `reference-fidelity`；垃圾桶、旗、樹、草地等次要材質設 `qualityTier: utility` (效果未驗證)。等使用者同意才改。

- [ ] **Step 5: 標記 material-spec-wiring**

用 `--status skipped --reason "analyze_texture and extract_pbr_evidence wrote materials via --in-place"`。
Expected: `next.py` 轉到 `strict-validation`。

- [ ] **Step 6: 驗證**

Run: `python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality`
Expected: 兩次都 exit 0。標 `strict-validation`，回報 spec 摘要，等同意再繼續。

---

### Task 5: 預覽 harness、gate 模式與滑桿面板

**Files:**
- Create: `package.json`、`index.html`、`src/main.ts`

**Interfaces:**
- Consumes: `createCaltexStationModel(spec, options): THREE.Group`、`spec.referenceCamera`
- Produces: `http://localhost:5173`，頁面設 `window.__IMG2THREEJS_READY__`、`window.__IMG2THREEJS_VIEWER__ = { renderer, scene, camera }`、`window.__IMG2THREEJS_CAPTURE__.setCamera(spec)`；`?gate=1` 模式用 `#303030` 純色背景、無面板、無地面陰影、canvas 固定 1024x687

- [ ] **Step 1: 安裝**

Run: `npm init -y && npm i three && npm i -D vite typescript @types/three`
Expected: 無 error，記下 `three` 版本。

- [ ] **Step 2: 寫 `index.html` 與 `src/main.ts`**

先放占位 box 當 factory。用 `PerspectiveCamera`，初始值取 `spec.referenceCamera`。一般模式背景色取參考圖 `#E7D4C5`。`setCamera` 接受 `{azimuth, elevation, distance, fov}`，供 4 個 turntable 角度與參考視角。第一個 frame 渲染完才設 `__IMG2THREEJS_READY__ = true`。

- [ ] **Step 3: 滑桿面板**

右側固定面板，3 個 `<input type="range">`：燈光方位角、橘色色相、雨棚高度比例。事件改 light 與 material 參數，不重新生成 factory。`?gate=1` 時隱藏面板。

- [ ] **Step 4: 驗證**

Run: `npx vite --port 5173` (背景)，開 `?gate=1`，用 `scripts/capture_threejs_playwright.py` 或 Python Playwright 的 `page.screenshot` 截圖 (它不能截透明 canvas)。
Expected: `__IMG2THREEJS_READY__` 為 `true`，截圖 1024x687，前景比例合理且無警告。

---

### Pass loop (Task 6 與 Task 7 共用)

每個 pass 照此執行，只動目前解鎖的 pass。每步完成後標對應 checklist 步驟並附證據，順序不可亂 (新 pass 與每次 refine 都會讓這 8 步重置)。

1. `python3 $K/forge/stage3_build/orchestrate_passes.py status object-sculpt-spec.json`
2. 新 pass 或 `refine-spec`：`generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts --force`。`refine-code`：直接改 factory，不重新生成。標 `build-current-pass`。
3. 用 `?gate=1` 截 1024x687 圖：參考視角 `shots/<pass-id>_ref.png`，加 4 個 turntable 角度 `_az0`、`_az90`、`_az180`、`_az270`。blockout 另截 clay 版 `shots/blockout_ref_clay.png` (去掉材質)。標 `render-capture`。
4. 重讀 `grimoire/review/gates_reference.md` 與 `self_correction.md`。標 `review-contract-read`。
5. Tier 1：`diagnose_render.py --reference reference/diorama_isolated.png --render shots/<pass-id>_ref.png --spec object-sculpt-spec.json --pass-id <pass-id> --in-place`；blockout 另加 `--map-stripped-render shots/blockout_ref_clay.png` (其他旗標先看 `--help`)。標 `tier1-diagnostics`。
6. 多角度：`diagnose_render_multi_angle.py --reference shots/<pass-id>_ref.png --orbit shots/<pass-id>_az90.png --orbit shots/<pass-id>_az180.png --json`。它不吃 `--spec`，結果寫進 review 證據。標 `multi-angle-review`。
7. `turntable_gate.py --capture 0=... --capture 90=... --capture 180=... --capture 270=... --allow-holes --json` (理由：柱間透空)。`interior_difference.py` 以上一個 pass 的 `_ref.png` 當 baseline。`attachment_anchor.py` 照跑，記下 `unmeasuredAttachments`。
8. `self_intersection.py`：用 `evaluate_script` 把 world-space 頂點與索引傾印成它讀的格式 (安裝版缺 `runtime/scripts/export_mesh_geometry.mjs`，格式未驗證)，失敗就在 review 記「未執行」。
9. `orchestrate_passes.py check object-sculpt-spec.json --pass-id <pass-id>`。標 `pass-gate-check`。
10. `make_comparison_sheet.py --reference reference/diorama.png --render shots/<pass-id>_ref.png --out shots/<pass-id>_cmp.png --json`，用 vision 看對照圖 (對照用原圖，Tier 1 用去背圖)。
11. `append_review.py` 記分並選一個 action：`continue`、`refine-spec`、`refine-code`、`request-input`、`stop`。標 `ai-review-recorded`。
12. `orchestrate_passes.py sync object-sculpt-spec.json --in-place`，標 `pipeline-sync`，再跑 `next.py`。

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

跑 `orchestrate_passes.py status object-sculpt-spec.json`，依 Task 4 Step 4 決定的路線處理 `material_pass_gaps`。

- [ ] **Step 3: material-pass 的色差停點 (停點 3b)**

Tier 1 的 `per_part_color_delta` 只用 5 個 k-means 群集比對所有 recipe，ΔE 上限 20。藍色垃圾桶實測 ΔE 約 37 到 40，綠色約 26 (subagent 以參考圖自身像素實測，我未重跑)。若超標，停下問使用者：合併小配件的 recipe，或刪除它們。

- [ ] **Step 4: material-pass 額外檢查**

橘色 fascia、草地、地層切面色相對照參考圖，跑 `material_views.py`、`material_comparator.py`、`material_gate.py`，指令見 `grimoire/scripts.md`。

- [ ] **Step 5: lighting-pass 與滑桿一致**

lighting-pass 通過的燈光是滑桿預設值，滑桿拖動範圍在 spec 的 lighting 區塊定義。

- [ ] **Step 6: optimization-pass 額外檢查**

記錄 `renderer.info` 的 draw calls 與 triangles，對照預設預算 160 draw calls。超標就合併幾何 (樹與灌木合併成單一 mesh)，仍不行停下問使用者放寬預算。

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

1. Spec coverage：23 個 checklist 步驟皆有對應 (Task 1 到 4 覆蓋前 11 步並逐步標記，Pass loop 覆蓋 8 步，Task 8 覆蓋最後 4 步)；v3.webp 的底座、Mart、旗桿、樹、垃圾桶、停車線分別在 Task 3、4。
2. Step scan：未驗證處已標明 (`fit_camera_to_correspondences` 座標慣例、`self_intersection` 輸入格式、`qualityTier: utility` 效果、draw calls 預算、subagent 的實測數字)。
3. Type consistency：對象 `Caltex Station`、factory `createCaltexStationModel`、參考圖 `diorama.png` 與 `diorama_isolated.png` 的分工在各 Task 一致。
4. Review Focus：8 項皆有對應步驟 (Task 1、4、5、7、Pass loop)。
5. Proportion：沒有貼 code 本體，滑桿只用原生 HTML，不加套件。
