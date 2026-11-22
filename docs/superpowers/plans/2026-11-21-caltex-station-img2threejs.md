# Caltex 加油站 img2threejs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `DSC05011 -copy.jpg` 的 Caltex 雨棚加加油機，重建成 code-only 的 procedural Three.js 模型 (TypeScript factory)。

**Architecture:** 用 img2threejs skill 的 23 步 checklist (`forge/next.py` 指定順序)。腳本負責驗證與 gate，agent vision 負責逐 pass 對照截圖。預覽用最小 Vite + three 頁面，Chrome DevTools MCP 截圖。

**Tech Stack:** Python 3.12 (stdlib)、Node 24、Vite、three、TypeScript、Chrome DevTools MCP。

**Spec:** 無獨立 spec 文件。範圍與限制寫在 Global Constraints，建模規格是 `object-sculpt-spec.json` (Task 4 產出)。

## Global Constraints

- 範圍：雨棚 (橘色 fascia、白色 soffit)、柱子、加油機、Caltex 圓形標誌與招牌。
- 不做：油罐車、車輛、背景建築、樹、旗桿。
- 單張照片看不到背面，結果是 stylized 近似，報告要標推論區域。
- Logo 與文字不追求精確，用 generated canvas texture，不下載圖檔。
- 原圖 `DSC05011 -copy.jpg` 不改，工作用副本是 `reference/ref_2000.jpg` (長邊 2000px)。
- skill 路徑：`K=/Users/shyin/.claude-shyin/skills/img2threejs`，腳本都從專案資料夾用 `python3 $K/forge/...` 執行。
- 修正上限：每 pass 3 輪、全部 6 輪，到了 hard stop 並回報。
- 資料夾不是 git repo，不做 commit，證據記在 `.img2threejs/state.json`。
- 各指令 flag 以 `SKILL.md` 為準，卡住先跑 `--help`。

## Review Focus

1. 8.4MB 原圖解碼失敗：先前出現 `decoder_unavailable`，Task 1 用縮圖解決。
2. 場景照被 rubric 判 Reject：Task 2 要寫明 Conditional 的三個接受條件。
3. 預覽缺 `window.__IMG2THREEJS_READY__`：沒有它截圖會拍到半載入畫面。
4. 屋頂懸臂與柱子浮空：`attachment_anchor.py` 要在每個 pass 通過。
5. 橘色烤漆被環境光洗掉：material pass 要對照參考圖色相。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你看什麼 |
| --- | --- | --- |
| 1 | Task 2 | 範圍與三個限制，Conditional 判定 |
| 2 | Task 4 | `object-sculpt-spec.json` 通過 strict-quality |
| 3 | Task 6 | blockout 的輪廓與比例 |
| 4 | Task 8 | 成品預覽與推論區域清單 |

其餘 pass 由執行者自跑。gate 失敗、到修正上限、需補圖才停下問你。

---

### Task 1: 參考圖與 state 初始化

**Files:**
- Create: `reference/ref_2000.jpg`、`.img2threejs/state.json`

**Interfaces:**
- Produces: `reference/ref_2000.jpg` (後續所有 `--image` 與 `--reference` 都用它)、可被 `next.py` 讀取的 state

- [ ] **Step 1: 縮圖**

Run: `mkdir -p reference && sips -Z 2000 "DSC05011 -copy.jpg" --out reference/ref_2000.jpg`
Expected: 檔案存在，長邊 2000px。

- [ ] **Step 2: 確認 agent 能讀圖**

用 Read 工具開 `reference/ref_2000.jpg`。Expected: 看得到加油站。失敗就改長邊 1600 重做。

- [ ] **Step 3: 初始化 state**

Run: `python3 $K/forge/state.py init --state .img2threejs/state.json --reference reference/ref_2000.jpg --profile generic --spec object-sculpt-spec.json`
Expected: 輸出 `step=image-analysis`。

- [ ] **Step 4: 確認下一步**

Run: `python3 $K/forge/next.py --state .img2threejs/state.json`
Expected: `next command: Read grimoire/intake/image_analysis.md ...`，列出 23 個 pending 步驟。

---

### Task 2: Intake 與 suitability (停點 1)

**Files:**
- Create: `analysis.md`、`assessment.json`
- Modify: `.img2threejs/state.json`

**Interfaces:**
- Consumes: `reference/ref_2000.jpg`
- Produces: `assessment.json` (`objectClass`、`complexity`、`qualityContract`)，供 Task 4 的 `--assessment`

- [ ] **Step 1: 寫 `analysis.md`**

依 `grimoire/intake/image_analysis.md` 8 層寫：分類、形體、macro/meso/micro、空間關係、PBR 材質、色彩、identity 特徵、單圖限制。觀察與推論分開標。

- [ ] **Step 2: probe 圖檔**

Run: `python3 $K/forge/stage1_intake/probe_image.py reference/ref_2000.jpg`
Expected: 印出尺寸與格式，無 error。

- [ ] **Step 3: 寫 suitability 判定**

在 `analysis.md` 結尾寫判定 Conditional，並列三個接受條件 (遮擋只做可見結構、stylized 近似、logo 文字不精確)。

- [ ] **Step 4: reference admission**

先找腳本：`find $K/forge -name "check_reference_admission.py"`，再依 `--help` 執行。Expected: 通過或給出具體缺漏。

- [ ] **Step 5: 本地 spec 搜尋與評估**

Run: `python3 $K/forge/stage2_spec/new_pre_spec_assessment.py "Caltex Station Canopy" --image reference/ref_2000.jpg --complexity complex --out assessment.json`
Expected: 產出 `assessment.json`，含 `localSpecSearch`。

- [ ] **Step 6: 標記步驟**

對 `image-analysis`、`reference-suitability`、`reference-admission`、`local-spec-search`、`pre-spec-assessment` 各跑 `python3 $K/forge/state.py mark <step-id> --state .img2threejs/state.json --evidence <path>`。
Expected: `next.py` 轉到 `detail-inventory`。

- [ ] **Step 7: 停點 1**

回報給使用者：suitability 判定與三個限制，等同意再繼續。

---

### Task 3: 細節清單與 projection 判斷

**Files:**
- Create: `detail/` (切格圖)、`di.json`

**Interfaces:**
- Consumes: `assessment.json`
- Produces: `di.json` (每個細節對應一個 `component.localFeatures` 或 `material.localOverrides`)

- [ ] **Step 1: 建清單**

Run: `python3 $K/forge/stage1_intake/build_detail_inventory.py reference/ref_2000.jpg --mode grid-3x3 --out-dir detail --out di.json`
Expected: `di.json` 存在，`detail/` 有 9 格圖。

- [ ] **Step 2: 補細節**

逐格補：fascia 倒角、soffit 嵌燈、柱子金屬環、加油機號碼牌、圓形標誌星形、招牌字。數量不低於 `assessment.json` 的 `targetMinDetails`。

- [ ] **Step 3: projection-route 標 skipped**

橘色是平塗烤漆，用 solid albedo。跑 `python3 $K/forge/state.py mark --help` 確認語法，再以 `--reason "flat paint, solid albedo"` 標記。
Expected: `next.py` 轉到 `spec-authoring`。

---

### Task 4: Spec、材質、驗證 (停點 2)

**Files:**
- Create: `object-sculpt-spec.json`、`crops/` (材質 crop)

**Interfaces:**
- Consumes: `assessment.json`、`di.json`
- Produces: 通過 `--strict-quality` 的 `object-sculpt-spec.json`，含元件階層、材質、pivot、socket

- [ ] **Step 1: 產生 spec**

Run: `python3 $K/forge/stage2_spec/new_sculpt_spec.py "Caltex Station Canopy" --image reference/ref_2000.jpg --assessment assessment.json --out object-sculpt-spec.json`
Expected: 產出 spec 骨架。

- [ ] **Step 2: 補元件階層**

至少 macro：canopy、columns、pump-island、pump、roundel-logo、sign。每個元件填 `topologyClass`、`topologyRationale`、`attachment` (parentSocket、contactType)。屋頂挑出部分標 cantilever 並接到柱子。

- [ ] **Step 3: 材質 crop 與分析**

為橘色 fascia、白色 soffit、灰色柱子、加油機外殼各切一張 crop 放 `crops/`，逐張跑：
`python3 $K/forge/stage1_intake/analyze_texture.py crops/<name>.png --spec object-sculpt-spec.json --material-id <id> --in-place`
Expected: 材質寫入 spec，confidence 低於 0.7 就重切 crop。

- [ ] **Step 4: 驗證**

Run: `python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality`
Expected: 兩次都 exit 0。

- [ ] **Step 5: 標記並停點 2**

標記 `spec-authoring`、`material-evidence`、`material-spec-wiring`、`strict-validation`，回報使用者看 spec 摘要，等同意再繼續。

---

### Task 5: 預覽 harness

**Files:**
- Create: `package.json`、`index.html`、`src/main.ts`

**Interfaces:**
- Consumes: Task 6 之後產出的 `src/createCaltexStationModel.ts` (`createCaltexStationModel(spec, options): THREE.Group`)
- Produces: `http://localhost:5173`，頁面設 `window.__IMG2THREEJS_READY__ = true` 與 `window.__IMG2THREEJS_VIEWER__ = { renderer, scene, camera }`

- [ ] **Step 1: 安裝**

Run: `npm init -y && npm i three && npm i -D vite typescript @types/three`
Expected: 無 error，記下 `three` 版本。

- [ ] **Step 2: 寫 `index.html` 與 `src/main.ts`**

`main.ts` 建 scene、camera (先用 1600x900 viewport)、燈光，載入 factory，第一個 frame 渲染完才設 `__IMG2THREEJS_READY__`。camera 位置之後依 `referenceCamera` 對齊。

- [ ] **Step 3: 驗證**

Run: `npx vite --port 5173` (背景)，用 Chrome DevTools MCP 開頁面，`evaluate_script` 讀 `window.__IMG2THREEJS_READY__`。
Expected: `true`，截圖有畫面。

---

### Pass loop (Task 6 與 Task 7 共用)

每個 pass 照此 9 步，只動目前解鎖的 pass：

1. `python3 $K/forge/stage3_build/orchestrate_passes.py status object-sculpt-spec.json`
2. `python3 $K/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts` (新 pass 加 `--force`)
3. 預覽截圖，存 `shots/<pass-id>_front.png` 與至少 2 個 orbit 角度。
4. 幾何 gate：`self_intersection.py`、`attachment_anchor.py`、`turntable_gate.py` (指令見 `SKILL.md` 第 7a 步)。
5. `diagnose_render.py` 加 `diagnose_render_multi_angle.py`，結果寫回 spec。
6. `interior_difference.py` 檢查輪廓內差異。
7. `make_comparison_sheet.py --reference reference/ref_2000.jpg --render shots/<pass-id>_front.png --out shots/<pass-id>_cmp.png --json`，用 vision 看對照圖。
8. `append_review.py` 記分並選一個 action：`continue`、`refine-spec`、`refine-code`、`request-input`、`stop`。
9. `orchestrate_passes.py sync object-sculpt-spec.json --in-place`，再跑 `next.py`。

Expected: 步驟 9 的 `next.py` 指到下一個 pass，且 `loop` 計數未超過 3/6。

---

### Task 6: Pass 1 blockout (停點 3)

**Files:**
- Create: `src/createCaltexStationModel.ts`、`shots/blockout_*.png`

**Interfaces:**
- Consumes: Task 4 的 spec、Task 5 的預覽
- Produces: 輪廓與比例正確的 blockout，`createCaltexStationModel(spec, options): THREE.Group`

- [ ] **Step 1: 跑 Pass loop，pass-id 為 `blockout`**

Expected: review 記錄 `continue`，`root.userData.sculptRuntime` 已存在。

- [ ] **Step 2: 停點 3**

給使用者看並排對照圖，確認屋頂比例、柱子位置、加油機位置。不對就 `refine-spec`，不往下走。

---

### Task 7: Pass 2 到 8

**Files:**
- Modify: `object-sculpt-spec.json`、`src/createCaltexStationModel.ts`

**Interfaces:**
- Consumes: Task 6 的 factory
- Produces: 7 個 pass 全部 `continue`

- [ ] **Step 1: 依序跑 Pass loop**

順序：`structural-pass`、`form-refinement`、`material-pass`、`surface-pass`、`lighting-pass`、`interaction-pass`、`optimization-pass`。一個 pass 通過才開下一個。

- [ ] **Step 2: material-pass 額外檢查**

橘色 fascia 的色相對照參考圖，跑 `material_views.py`、`material_comparator.py`、`material_gate.py`，指令見 `grimoire/scripts.md`。

- [ ] **Step 3: optimization-pass 額外檢查**

記錄 `renderer.info` 的 draw calls 與 triangles，在 spec 的 `performanceBudget` 範圍內。

---

### Task 8: 收尾 (停點 4)

**Files:**
- Create: `parts.json`、`REPORT.md`

**Interfaces:**
- Consumes: 全部 pass 通過的 spec 與 factory
- Produces: 可拆解、可點選的模型加推論區域清單

- [ ] **Step 1: part coverage**

Run: `python3 $K/forge/stage4_review/check_part_coverage.py --spec object-sculpt-spec.json --manifest parts.json`
Expected: exit 0，每個元件可 explode 與 click。

- [ ] **Step 2: 標記剩餘步驟**

`part-coverage`、`action-ready` 附證據標記。`emission-target` 與 `plugin-gates` 用 `--reason` 標 skipped (無 emission target、無 domain plugin)。
Expected: `next.py` 顯示全部完成。

- [ ] **Step 3: 寫 `REPORT.md`**

列輸出檔案、各 pass 的 fidelity 分數、推論區域 (背面、被遮擋處)、近似程度聲明。

- [ ] **Step 4: 停點 4**

給使用者預覽網址 `http://localhost:5173` 與 `REPORT.md`。

---

## Self-Review

1. Spec coverage：範圍 4 類元件對應 Task 4 的 macro 清單與 Task 6、7 的 pass。
2. Step scan：flag 不確定處已標「先跑 `--help`」(Task 2 step 4、Task 3 step 3、Task 7 step 2)。
3. Type consistency：factory 名稱 `createCaltexStationModel` 在 Task 5、6 一致。
4. Review Focus：5 項皆有對應步驟 (Task 1、2、5、Pass loop 步驟 4、Task 7 step 2)。
5. Proportion：計畫行數與 skill 流程相當，沒有貼 code 本體。
