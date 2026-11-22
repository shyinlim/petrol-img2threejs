# Caltex 加油站 Diorama img2threejs Implementation Plan (v9)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修掉 v8 的穿模與擺位錯誤，讓雨棚正面的凹槽、CALTEX 與 roundel 的距離接近 `v3.webp`。

**Architecture:** 幾何全部改 spec，再重新生成 factory。新腳本 `scripts/build_spec_v9.py` 從 v9 備份還原後套改動，可以重跑。驗收先用兩支幾何測試 (world bbox) 擋住穿模與距離，再跑 img2threejs 的 refine-spec gates 與獨立 reviewer。

**Tech Stack:** three 0.187.0、Vite 8.3.8、TypeScript、Python 3 + Python Playwright、img2threejs forge 腳本。

**Spec:** 無獨立 spec 文件。範圍來自使用者 2026-11-22 兩張紅框截圖與本計畫 Global Constraints。建模規格是 `object-sculpt-spec.json`。前一版計畫 `docs/superpowers/plans/2026-11-22-caltex-station-img2threejs-v8.md`。

## Global Constraints

- 目標外觀是 `v3.webp` (`reference/diorama.png`)。
- `K=/Users/shyin/.claude-shyin/skills/img2threejs`，腳本在專案資料夾執行。
- `src/createCaltexStationModel.ts` 不手改，只能改 spec 再跑 `generate_threejs_factory.py --force`。
- 改 spec 一律用 `scripts/build_spec_v9.py`。它先從 `backup/spec_before_v9.json` 還原，保留備份之後追加的 `reviewHistory` 與 `visualEvidence` (照 `build_spec_v8.py:11-14` 的寫法)。
- box 的尺寸取自 `transform.scale`，`dimensions` 要同步改。cylinder 的位置取自 `attachment.localStart/localEnd`，粗細取自 `baseRadius/endRadius`。沿用 `build_spec_v8.py` 的 `set_dim`、`set_pos`、`set_att`。
- world 座標：雨棚正面是 `-x` 面 (canopy local x -5.75)，roundel 在 `+z` 端轉角。底座 `base-slab` 的 xz 範圍是 x ±8.1、z ±9.0。Mart 的 xz 範圍是 x 4.6–7.6、z -2.0–7.0。
- draw calls 上限 160，取 12 個環景角度的最大值 (`scripts/check_scene.py`)。2026-11-22 實測 158。
- `?gate=1` 的參考相機不改。旗面、roundel、CALTEX 的圖檔不改。
- rollback 點是 git tag `pre-v9`。每個 Task 完成後 commit 一次。
- img2threejs 狀態：`next.py` 目前 `loop=0/3 total=2/6`。`loop` 只算目前 pass (已 complete)，不會因為這一筆撞到每 pass 3 次的上限。本版只記一筆 `refine-spec`，記完是 total 3/6。
- 每步完成後複製新的 `docs/summary/yyyymmddhhmmss_plan_summary.md`，`.img2threejs/ledger.md` 加一行。

## 範圍外

- 加油機外觀 (橘白配色、油槍)、垃圾桶加蓋加輪、旗面飄動。這三項留給 v10。
- 背面 `canopy-wordmark-back` 不搬。v3 看不到背面。
- roundel 朝向不改。它的軸是轉角的 45 度斜線，v3 的 roundel 也斜對轉角。正面截圖看起來窄，是因為斜看。
- 雨棚右側面的上緣唇邊不做。目前 draw calls 158，加兩條凸邊就到上限 160。

## Review Focus

1. 搬動一個植物後撞上另一個植物或垃圾桶：Task 1 的 `check_layout.py` 斷言 1 做兩兩 bbox 檢查。
2. 旗子縮小後沒掛到桿頂，或旗面超出底座：`check_layout.py` 斷言 3、5。
3. roundel 放大後插進雨棚轉角：`check_canopy.py` 斷言 4。
4. 加兩條凸邊讓 draw calls 超過 160：Task 3 Step 3 量 `check_scene.py`。
5. 凸邊蓋住 CALTEX 字：`check_canopy.py` 斷言 3 要求凸邊與 wordmark 的 bbox 不重疊。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你要做什麼 |
| --- | --- | --- |
| A | Task 3 | 開 http://localhost:5173 轉一圈，看擺位、凹槽、字和 logo 的距離 |
| B | Task 4 | 看 reviewer 分數，驗收 |

draw calls 超過 160，或 Task 2、3 的數值調 3 次測試仍不過，就停下問你。

---

### Task 1: 兩支幾何測試 (先寫，先失敗)

**Files:**
- Create: `scripts/check_layout.py`、`scripts/check_canopy.py`

**Interfaces:**
- Consumes: `scripts/_viewer.py` 的 `gate_page()`。world bbox 的算法照 `scripts/check_scene.py:9-25`，用 `userData.sculptComponent.id` 找元件，只算該元件的直屬 mesh。
- Produces: 兩支腳本 exit 0 代表通過，失敗時印出每一條違規 (元件 id 與數值)。

- [ ] **Step 1: 寫 `scripts/check_layout.py`**

道具清單：`tree-N`、`tree-N-trunk`、`bush-N`、`agave-N-leaf-M`、`bin-*`、`flagpole-N`、`flag-malaysia`、`flag-johor`。
群組 key：`tree-N` 與 `tree-N-trunk` 同組，`agave-N-*` 同組，`flagpole-1` 與 `flag-malaysia` 同組，`flagpole-2` 與 `flag-johor` 同組，其餘各自一組。
每個 bbox 先各邊內縮 0.02 再判斷。`tree-N` 樹冠與 `bush-N` 是球體，兩者之間或與其他道具比對時，改用球心距離減半徑判斷，不用 bbox。斷言：
1. 不同組的道具兩兩不重疊。
2. 道具的 3D bbox 不與 `mart` 的 bbox 重疊。
3. 道具的 xz 範圍都在 x ±8.1、z ±9.0 之內。
4. `bin-*`、`bush-*`、`tree-N-trunk`、`agave-N` 整組 bbox 的 xz 中心，都落在某個 `grass-verge-*` 的 xz 範圍內。
5. 每面旗的 bbox 頂端，介於旗桿頂端減 0.15 到旗桿頂端之間。
6. `grass-verge-*` 的 xz 範圍不與 `mart` 的 xz 範圍重疊。

- [ ] **Step 2: 寫 `scripts/check_canopy.py`**

斷言：
1. `roundel-logo` 的 bbox 最小 z，減去 `canopy-wordmark` 的 bbox 最大 z，結果 ≤ 1.6。
2. `roundel-logo` 的 bbox 頂端，高於 `canopy` 直屬 mesh 的 bbox 頂端至少 0.5。
3. `fascia-lip-top`、`fascia-lip-end` 都存在。兩者的 bbox 最小 x 都小於 `canopy` 的最小 x，且都不與 `canopy-wordmark` 的 bbox 重疊。
4. 把雨棚轉角點 (canopy 最小 x、canopy y 中心、canopy 最大 z) 用 `worldToLocal` 換到 roundel mesh 的 local 座標。轉角點不能落在圓柱內 (徑向距離 ≤ 半徑且軸向 ≤ 半厚)。45 度斜放的圓盤，bbox 一定包住轉角，所以不用 bbox。

- [ ] **Step 3: 跑測試確認失敗**

Run: `python3 scripts/check_layout.py; python3 scripts/check_canopy.py`
Expected: 兩支都 FAIL。layout 至少列出 `tree-4`×`mart`、`bush-2`×`bush-4`、`flagpole-1`×`bush-4`、`agave-3`×`bush-3`、`flag-johor` 超出底座、`bin-green-1` 不在草地、`grass-verge-c`×`mart`。canopy 列出斷言 1、2、3。

- [ ] **Step 4: 開 rollback 點並 commit**

```bash
git tag pre-v9
git add scripts/check_layout.py scripts/check_canopy.py
git commit -m "test: layout and canopy geometry checks (v9 task 1)"
```

---

### Task 2: 植物、垃圾桶、旗子擺位 (refine-spec)

**Files:**
- Create: `backup/spec_before_v9.json`、`scripts/build_spec_v9.py`
- Modify: `object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)

**Interfaces:**
- Produces: `python3 scripts/build_spec_v9.py` 可重跑，印出元件數。Task 3 在同一支腳本加段落。

- [ ] **Step 1: 備份**

Run: `cp object-sculpt-spec.json backup/spec_before_v9.json`

- [ ] **Step 2: 寫 `scripts/build_spec_v9.py` 的擺位段**

下表的 world 座標是起始值 (推論)，以 Task 1 測試為準。子件位置是相對父件，換算時減去父件位置。

| 元件 | 現值 | 新值 | 原因 |
| --- | --- | --- | --- |
| `grass-verge-c` | z 中心 7.0、深 2.8 | z 中心 7.75、深 1.3 | 不壓 Mart |
| `tree-4-trunk` (含 crown) | x 7.2、z 6.6 | x 7.35、z 7.75 | 樹冠穿出 Mart 牆 |
| `tree-3-trunk` (含 crown) | x 6.0 | x 5.8 | 讓出 tree-4 樹冠 |
| `bush-2` | x 4.886 | x 5.15 | 與 bush-4 疊成一坨 |
| `bush-4` | x 4.6 | x 3.6 | 旗桿穿過它 |
| `bush-3` | x 0.0 | x -1.2 | agave-3 插在裡面 |
| `agave-4-leaf-1..3` | 父件 `grass-verge-c` | 父件改 `grass-verge-b`，整組中心 world (2.6, 8.0)，葉片間相對位置不變 | verge-c 只剩 tree-4 的空間 |
| `tree-2-trunk` (含 crown) | z -0.86 | z -2.8 | 樹貼著垃圾桶 |
| `agave-2-leaf-1..3` | 整組 world z -1.27 | 整組 world z -1.9 | 讓出垃圾桶 |
| `bin-blue-1` | z -0.344 | z -1.1 | 收回草地內 |
| `bin-green-1` | z 0.43 | z -0.4 | 原本超出草地端點 |
| `flag-malaysia`、`flag-johor` | 2.4 x 1.2 | 1.6 x 0.8 | v3 旗寬約桿高 0.22 倍 (推論) |
| 兩面旗的 local 位置 | x 1.3、y 5.8 | x 0.86；y 設成旗頂 = 桿頂 - 0.05 | 旗沒掛到桿頂 |
| `flagpole-2` | x 7.0 | x 6.4 | Johor 旗超出底座 |

`assumptions` 加一條：旗子尺寸依 v3 像素比例推論。

- [ ] **Step 3: 生成並驗證**

Run: `python3 scripts/build_spec_v9.py && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts --force && npx tsc --noEmit && python3 scripts/check_layout.py && python3 scripts/check_scene.py`
Expected: 全部 exit 0。layout 仍有違規就調表中數值重跑，最多 3 次。

- [ ] **Step 4: Commit**

```bash
git add backup/spec_before_v9.json scripts/build_spec_v9.py object-sculpt-spec.json src/createCaltexStationModel.ts di.json
git commit -m "fix: move props out of Mart and each other, flags at pole top (v9 task 2)"
```

---

### Task 3: 雨棚凹槽、CALTEX 位置、roundel 大小 (停點 A)

**Files:**
- Modify: `scripts/build_spec_v9.py`、`object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)

**Interfaces:**
- Consumes: Task 2 的 `build_spec_v9.py`。
- Produces: 新元件 `fascia-lip-top`、`fascia-lip-end`，parent `canopy`，box，material `fascia-orange`。

- [ ] **Step 1: 在 `build_spec_v9.py` 加雨棚段**

數值依 v3 像素估 (推論)，以 Task 1 測試為準。

| 元件 | 欄位 | 現值 | 新值 |
| --- | --- | --- | --- |
| `canopy-wordmark` | position z | 1.5 | 4.5 |
| `roundel-logo` | `baseRadius`、`endRadius` | 0.475 | 0.8 |
| `roundel-logo` | localStart/localEnd 與 position 的 y | 0.45 | 0.7 |
| `roundel-logo` | dimensions width、depth | 0.95 | 1.6 |
| `fascia-lip-top` | 新增 | 無 | position `[-5.80, 0.38, 0]`，scale `[0.1, 0.14, 14.0]` |
| `fascia-lip-end` | 新增 | 無 | position `[-5.80, 0, -6.93]`，scale `[0.1, 0.9, 0.14]` |

新元件用 `build_spec_v8.py` 的 `clone()` 從 `canopy-wordmark` 複製，再改 material、scale、position。補 `topologyRationale`，`confidence: 0.4`。`assumptions` 加一條：凹槽用兩條凸邊表現，深度 0.1 為推論。

- [ ] **Step 2: 生成並驗證**

Run: 同 Task 2 Step 3，再加 `python3 scripts/check_canopy.py`
Expected: 全部 exit 0。

- [ ] **Step 3: draw calls 與環景**

Run: `python3 scripts/check_scene.py && python3 scripts/check_orbit.py && python3 scripts/turntable.py v9`
Expected: `drawCallsMax ≤ 160`，orbit 7/7。超過 160 就停下問使用者：放寬上限，或在 `main.ts` 把兩條凸邊合併進 canopy mesh。

- [ ] **Step 4: Commit 與停點 A**

```bash
git add scripts/build_spec_v9.py object-sculpt-spec.json src/createCaltexStationModel.ts
git commit -m "feat: fascia recess lips, wordmark next to roundel, larger roundel (v9 task 3)"
```

給使用者 http://localhost:5173 與 `shots/v8_v9_sheet.png`。

---

### Task 4: refine-spec gates、評分與文件 (停點 B)

**Files:**
- Modify: `object-sculpt-spec.json` (`reviewHistory`)、`parts.json`、`REPORT.md`、`.img2threejs/ledger.md`
- Create: 新的 summary 快照

- [ ] **Step 1: gates**

照 v8 Task 3 Step 4 的清單跑：Tier 1、`diagnose_render_multi_angle.py`、`turntable_gate.py --allow-holes`、`interior_difference.py` (baseline `shots/v8_final_ref.png`)、`attachment_anchor.py`、`make_comparison_sheet.py`。
Expected: `attachment_anchor.py` 0 errors，turntable gate pass。

- [ ] **Step 2: 獨立 reviewer**

派 Opus subagent，只給 `reference/diorama.png`、`shots/v8_v9_sheet.png`、`shots/v8_checklist.md`、v8 Task 7 的分數。它照原門檻評 5 個 critical feature (0.8 / 0.8 / 0.75 / 0.75 / 0.8)、important 平均 0.65、整體 0.70，並逐角度判定檢查表第 7 項 (穿模)。
用 `append_review --force-out-of-order` 記一筆 `refine-spec`，未達門檻照實記錄。

- [ ] **Step 3: parts.json 與全部檢查**

重新傾印 `parts.json` (方法同 v8 Task 7 Step 2)。
Run: `npx tsc --noEmit && npx vite build && python3 scripts/check_layout.py && python3 scripts/check_canopy.py && python3 scripts/check_scene.py && python3 $K/forge/stage4_review/check_part_coverage.py --spec object-sculpt-spec.json --manifest parts.json --inventory di.json && python3 $K/forge/next.py --state .img2threejs/state.json object-sculpt-spec.json`
Expected: 全部 exit 0，next.py 顯示 `total=3/6`。

- [ ] **Step 4: 文件、commit、停點 B**

`REPORT.md` 整份改寫成目前狀態，推論清單加上旗子尺寸與凹槽深度。ledger 加一行，複製 summary 快照。

```bash
git add -A REPORT.md parts.json object-sculpt-spec.json .img2threejs docs/summary shots/v8_v9_*
git commit -m "docs: v9 review, parts.json, report (v9 task 4)"
```

---

## Self-Review

1. Spec coverage：兩張紅框的每一處都有 Task。穿模與擺位在 T2，凹槽、字距、roundel 在 T3。加油機、垃圾桶、旗面飄動列在範圍外。
2. Step scan：所有座標都有測試把關，數值標了推論。
3. Type consistency：`check_layout.py`、`check_canopy.py`、`build_spec_v9.py`、`fascia-lip-top`、`fascia-lip-end` 在各 Task 用法一致。
4. Review Focus：5 項分別落在 T1 的斷言與 T3 Step 3。
5. Proportion：沒有貼 code 本體，數值集中在兩張表。
