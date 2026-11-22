# Caltex 加油站 img2threejs Implementation Plan (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `DSC05011 -copy.jpg` 的 Caltex 雨棚加加油機，重建成 code-only 的 procedural Three.js 模型 (TypeScript factory)。

**Architecture:** 用 img2threejs 的 23 步 checklist (`forge/next.py` 指定順序)。分析用整張縮圖，gate 與對照用只含雨棚與加油機的隔離參考圖。預覽用最小 Vite + three 頁面，Python Playwright 截圖。

**Tech Stack:** Python 3.12 (stdlib)、Node 24、Vite、three、TypeScript、Python Playwright。

**Spec:** 無獨立 spec 文件。範圍寫在 Global Constraints，建模規格是 `object-sculpt-spec.json` (Task 4 產出)。

## Global Constraints

- 範圍：前景雨棚 (橘色 fascia、白色 soffit)、柱子、加油機、Caltex 圓形標誌與招牌。
- 不做：油罐車、車輛、背景建築、背景紅色雨棚、樹、旗桿。
- 單張照片看不到背面，結果是 stylized 近似，報告標出推論區域。
- Logo 與文字用 canvas decal，不追求精確，不下載圖檔。
- 加油機被車遮擋且很小，confidence 標低。
- 原圖不改。`reference/ref_2000.jpg` (整張，只供分析)、`reference/ref_canopy.png` (雨棚加加油機，中性背景，供所有 gate 與對照)。
- `K=/Users/shyin/.claude-shyin/skills/img2threejs`，腳本從專案資料夾用 `python3 $K/forge/...` 執行。
- 對象名稱固定 `Caltex Station`，factory 名稱是 `createCaltexStationModel`。
- 修正上限：全部 6 輪；每 pass 第 3 次 refine 決定就 hard stop，實際每 pass 2 輪修正。
- 資料夾不是 git repo，不做 commit，證據記在 `.img2threejs/state.json`。
- 各指令 flag 以 `SKILL.md` 與 `--help` 為準。

## Review Focus

1. Tier 1 的輪廓 IoU 門檻是 0.85：拿整張場景當參考會永遠過不了，Task 1 做隔離參考圖。
2. 柱子與屋頂浮空：`attachment_anchor.py` 不檢查 canopy 與 columns，改靠 `role: support` 的 attachment gap 檢查。
3. 柱間透空被 turntable gate 當成洞：用 `--allow-holes` 並寫下理由。
4. 預覽沒有 `window.__IMG2THREEJS_READY__`：截圖會拍到半載入畫面。
5. 橘色烤漆被環境光洗掉：material pass 對照參考圖色相。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你看什麼 |
| --- | --- | --- |
| 1 | Task 2 | 範圍、三個限制、隔離參考圖 |
| 2 | Task 4 | spec 通過 strict-quality |
| 3 | Task 6 | blockout 的輪廓與比例 |
| 4 | Task 8 | 成品預覽與推論區域清單 |

其餘 pass 由執行者自跑。gate 失敗、到修正上限、需補圖才停下問你。

---

### Task 1: 參考圖與 state 初始化

**Files:**
- Create: `reference/ref_2000.jpg`、`reference/ref_canopy.png`、`.img2threejs/state.json`

**Interfaces:**
- Produces: `ref_2000.jpg` (分析用)、`ref_canopy.png` (所有 `--reference` 與 `--render` 對照用)

- [ ] **Step 1: 縮圖**

Run: `mkdir -p reference && sips -Z 2000 "DSC05011 -copy.jpg" --out reference/ref_2000.jpg`
Expected: 長邊 2000px。

- [ ] **Step 2: 確認 agent 能讀圖**

用 Read 開 `reference/ref_2000.jpg`。Expected: 看得到加油站。失敗就改長邊 1600 重做。

- [ ] **Step 3: 做隔離參考圖**

Run: `python3 $K/forge/stage1_intake/run_vision_adapter.py segment --help`，依 `docs/integrations/reference_fidelity_tooling.md` 的 SAM2 路徑產生雨棚與加油機的 mask，合成到中性灰背景，存 `reference/ref_canopy.png`。
Expected: 圖中只剩雨棚、柱子、加油機。SAM2 沒裝就停下問使用者，不自行安裝。

- [ ] **Step 4: 初始化 state**

Run: `python3 $K/forge/state.py init --state .img2threejs/state.json --reference reference/ref_2000.jpg --profile generic --spec object-sculpt-spec.json`
Expected: 輸出 `step=image-analysis`。

- [ ] **Step 5: 確認下一步**

Run: `python3 $K/forge/next.py --state .img2threejs/state.json`
Expected: `next command: Read grimoire/intake/image_analysis.md ...`，列出 23 個 pending 步驟。

---

### Task 2: Intake 與 suitability (停點 1)

**Files:**
- Create: `analysis.md`、`probe.json`、`assessment.json`

**Interfaces:**
- Consumes: `reference/ref_2000.jpg`、`reference/ref_canopy.png`
- Produces: `assessment.json` (`objectClass`、`complexity`、`qualityContract`)

- [ ] **Step 1: 寫 `analysis.md`**

依 `grimoire/intake/image_analysis.md` 8 層寫，觀察與推論分開標。結尾寫 suitability 判定 Conditional 與三個接受條件 (遮擋只做可見結構、stylized 近似、logo 文字不精確)。

- [ ] **Step 2: reference admission 並寫 probe**

先 `find $K/forge -name "check_reference_admission.py"`，再依 `--help` 對 `reference/ref_canopy.png` 執行，加 `--probe-out probe.json`。
Expected: 通過，`probe.json` 存在。

- [ ] **Step 3: 評估**

Run: `python3 $K/forge/stage2_spec/new_pre_spec_assessment.py "Caltex Station" --image reference/ref_canopy.png --complexity complex --out assessment.json`，加上 `--spec-query` 查詢詞 (canopy、gas pump、fascia，詞表見 `grimoire/intake/local_spec_search.md`)。
Expected: `assessment.json` 含 `localSpecSearch`。

- [ ] **Step 4: 標記步驟**

對 `image-analysis`、`reference-suitability`、`reference-admission`、`local-spec-search`、`pre-spec-assessment` 各跑 `python3 $K/forge/state.py mark <step-id> --state .img2threejs/state.json --evidence <path>`，依序標記。
Expected: `next.py` 轉到 `detail-inventory`。

- [ ] **Step 5: 停點 1**

回報 suitability 判定、三個限制與 `ref_canopy.png`，等同意再繼續。

---

### Task 3: 細節清單與 projection 判斷

**Files:**
- Create: `detail/`、`di.json`

**Interfaces:**
- Consumes: `assessment.json`
- Produces: `di.json` (每個細節對應 `component.localFeatures` 或 `material.localOverrides`)

- [ ] **Step 1: 建清單**

Run: `python3 $K/forge/stage1_intake/build_detail_inventory.py reference/ref_canopy.png --mode grid-3x3 --complexity complex --out-dir detail --out di.json`
Expected: `di.json` 存在，`detail/` 有 9 格圖。

- [ ] **Step 2: 補細節**

逐格補：fascia 倒角、soffit 嵌燈、柱子金屬環、加油機號碼牌、圓形標誌星形、招牌字。數量不低於 `targetMinDetails`。

- [ ] **Step 3: projection-route 標 skipped**

Run: `python3 $K/forge/state.py mark projection-route --state .img2threejs/state.json --status skipped --reason "flat paint uses solid albedo; logo via canvas decal, exact logo fidelity not required"`
Expected: `next.py` 轉到 `spec-authoring`。

---

### Task 4: Spec、材質、驗證 (停點 2)

**Files:**
- Create: `object-sculpt-spec.json`、`crops/`、`material-evidence/`

**Interfaces:**
- Consumes: `assessment.json`、`di.json`
- Produces: 通過 `--strict-quality` 的 spec，含元件階層、材質、pivot、socket

- [ ] **Step 1: 產生 spec**

Run: `python3 $K/forge/stage2_spec/new_sculpt_spec.py "Caltex Station" --image reference/ref_canopy.png --assessment assessment.json --out object-sculpt-spec.json`

- [ ] **Step 2: 補元件階層**

macro：canopy、columns、pump-island、pump、roundel-logo、sign。柱子設 `role: support`，填 parentSocket、contactType、embedDepth。屋頂挑出部分接到柱子。每個元件填 `topologyClass` 與 `topologyRationale`。

- [ ] **Step 3: 材質 crop 與分析**

橘色 fascia、白色 soffit、灰色柱子、加油機外殼各切一張 crop 放 `crops/`，每張跑兩支：
`python3 $K/forge/stage1_intake/analyze_texture.py crops/<name>.png --spec object-sculpt-spec.json --material-id <id> --in-place`
`python3 $K/forge/stage1_intake/extract_pbr_evidence.py crops/<name>.png --out-dir material-evidence --material-id <id> --spec object-sculpt-spec.json --in-place`
Expected: confidence 低於 0.7 就重切 crop。

- [ ] **Step 4: 標記 material-spec-wiring**

用 `--status skipped --reason "analyze_texture and extract_pbr_evidence wrote materials via --in-place"`。
Expected: `next.py` 轉到 `strict-validation`。

- [ ] **Step 5: 驗證**

Run: `python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality`
Expected: 兩次都 exit 0。

- [ ] **Step 6: 標記並停點 2**

標記 `spec-authoring`、`material-evidence`、`strict-validation` (附證據)，回報使用者看 spec 摘要，等同意再繼續。

---

### Task 5: 預覽 harness

**Files:**
- Create: `package.json`、`index.html`、`src/main.ts`

**Interfaces:**
- Consumes: `createCaltexStationModel(spec, options): THREE.Group`
- Produces: `http://localhost:5173`，頁面設 `window.__IMG2THREEJS_READY__`、`window.__IMG2THREEJS_VIEWER__ = { renderer, scene, camera }`、`window.__IMG2THREEJS_CAPTURE__.setCamera(spec)`

- [ ] **Step 1: 安裝**

Run: `npm init -y && npm i three && npm i -D vite typescript @types/three`
Expected: 無 error，記下 `three` 版本。

- [ ] **Step 2: 寫 `index.html` 與 `src/main.ts`**

先放一個占位 box 當 factory。`setCamera` 接受 `{azimuth, elevation, distance}`，供 4 個 turntable 角度與 reference camera 對齊。第一個 frame 渲染完才設 `__IMG2THREEJS_READY__ = true`。

- [ ] **Step 3: 驗證**

Run: `npx vite --port 5173` (背景)，開頁面讀 `window.__IMG2THREEJS_READY__`。
Expected: `true`，占位 box 有畫面。`scripts/capture_threejs_playwright.py` 的需求以 `--help` 為準。

---

### Pass loop (Task 6 與 Task 7 共用)

每個 pass 照此執行，只動目前解鎖的 pass。每步完成後標對應 checklist 步驟並附證據，順序不可亂 (新 pass 與每次 refine 都會讓這 8 步重置)。

1. `python3 $K/forge/stage3_build/orchestrate_passes.py status object-sculpt-spec.json`
2. `generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts` (新 pass 加 `--force`)。標 `build-current-pass`。
3. 用 `setCamera` 截 4 角度：`shots/<pass-id>_az0.png`、`_az90`、`_az180`、`_az270`。標 `render-capture`。
4. 重讀 `grimoire/review/gates_reference.md` 與 `self_correction.md`。標 `review-contract-read`。
5. `diagnose_render.py` 與 `diagnose_render_multi_angle.py`，`--reference reference/ref_canopy.png --spec object-sculpt-spec.json --pass-id <pass-id> --in-place`。標 `tier1-diagnostics`、`multi-angle-review`。
6. `turntable_gate.py --capture 0=... --capture 90=... --capture 180=... --capture 270=... --allow-holes --json` (理由：柱間透空)。`interior_difference.py` 檢查輪廓內差異。
7. `self_intersection.py`：用 `evaluate_script` 把 world-space 頂點與索引傾印成它讀的格式 (安裝版缺 `runtime/scripts/export_mesh_geometry.mjs`，格式未驗證)，失敗就在 review 記「未執行」。
8. `orchestrate_passes.py check object-sculpt-spec.json --pass-id <pass-id>`。標 `pass-gate-check`。
9. `make_comparison_sheet.py --reference reference/ref_canopy.png --render shots/<pass-id>_az0.png --out shots/<pass-id>_cmp.png --json`，用 vision 看對照圖。
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

- [ ] **Step 1: 跑 Pass loop，pass-id 為 `blockout`**

Expected: review 記錄 `continue`，`root.userData.sculptRuntime` 存在。

- [ ] **Step 2: 停點 3**

給使用者看並排對照圖，確認屋頂比例、柱子與加油機位置。不對就 `refine-spec`，不往下走。

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

跑 `orchestrate_passes.py status object-sculpt-spec.json`，確認 `material_pass_gaps` 要求哪些貼圖與覆蓋。平塗烤漆若被要求完整貼圖，停下問使用者要不要降低要求。

- [ ] **Step 3: material-pass 額外檢查**

橘色 fascia 色相對照參考圖，跑 `material_views.py`、`material_comparator.py`、`material_gate.py`，指令見 `grimoire/scripts.md`。

- [ ] **Step 4: optimization-pass 額外檢查**

記錄 `renderer.info` 的 draw calls 與 triangles，在 `performanceBudget` 範圍內。

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

列輸出檔案、各 pass 分數、推論區域 (背面、被遮擋處、加油機細節)、近似程度聲明。

- [ ] **Step 5: 停點 4**

給使用者預覽網址 `http://localhost:5173` 與 `REPORT.md`。

---

## Self-Review

1. Spec coverage：23 個 checklist 步驟皆有對應 (Task 1 到 4 覆蓋前 11 步，Pass loop 覆蓋 8 步，Task 8 覆蓋最後 4 步)。
2. Step scan：未驗證處已標明 (SAM2 路徑、`self_intersection` 輸入格式、`material_pass_gaps`)。
3. Type consistency：對象 `Caltex Station`、factory `createCaltexStationModel` 在各 Task 一致。
4. Review Focus：5 項皆有對應步驟。
5. Proportion：沒有貼 code 本體。
