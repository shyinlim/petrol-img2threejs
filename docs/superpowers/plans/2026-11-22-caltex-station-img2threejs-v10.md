# Caltex 加油站 Diorama img2threejs Implementation Plan (v10)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓使用者打開頁面時的感覺接近 `v3.webp` 的柔光黏土玩具，操作方式接近 `docs/sample/` 的作品頁。

**Architecture:** 分三輪。第 1 輪改 viewer 加少量便宜的 spec 色值：光影、配色、玻璃、旗子、作品頁 UI，第一個停點就看得到最大的變化。第 2 輪改 spec 的比例、圓角、立體字。第 3 輪加細節零件、貼圖與旗面動畫。每輪先寫會失敗的檢查，再改，最後停下給使用者看 normal mode 截圖。

**Tech Stack:** three 0.187.0 (`RoundedBoxGeometry`、`SVGLoader`、`RoomEnvironment`、`InstancedMesh`)、Vite 8.3.8、TypeScript、Python 3 + Python Playwright、img2threejs forge 腳本。

**Spec:** 無獨立 spec 文件。範圍是 2026-11-22 對話中與使用者定案的 41 項清單，加上兩份 subagent 審查 (可行性、需求對齊) 的修正。建模規格是 `object-sculpt-spec.json`。前一版計畫 `docs/superpowers/plans/2026-11-22-caltex-station-img2threejs-v9.md`。

## Global Constraints

- 目標外觀是 `v3.webp`。操作方式參考 `docs/sample/IMG_4548.PNG`、`IMG_4549.PNG`：左上小字眉標加大號襯線標題、左下斜體英文名、右側可收合的分組面板 (細灰滑桿、右側數值框、色票)、底部膠囊工具列、抓手游標。
- `K=/Users/shyin/.claude-shyin/skills/img2threejs`，腳本在專案資料夾執行。
- `src/createCaltexStationModel.ts` 不手改，只改 spec 再跑 `generate_threejs_factory.py --force`。
- 改 spec 一律用 `scripts/build_spec_v10.py`。它先從 `backup/spec_before_v10.json` 還原，再把備份之後追加的 `reviewHistory`、`visualEvidence`、`tier1Results` 接回去 (照 `build_spec_v9.py:9-11`)。`set_dim`、`set_pos`、`set_att`、`put_xz`、`shift_xz`、`clone` 從 `build_spec_v9.py` 複製。
- box 的大小烘在 geometry 裡 (`geometry.scale(w,h,d)`)，mesh scale 是 1。generator 只對 cylinder 走 attachment 端點，box 用 `transform.position`。
- 柱子改 box 時保留 `attachment` 區塊。strict validate 要求它 (subagent 實測：刪掉會報 `column-2 requires attachment`)。柱子的 `transform.position` 已是中點 y -2.945，只有 `column-disc-*` 的 local y 要從 2.2 改成 -0.295。
- cylinder 的長度取自 `attachment.localStart/localEnd`，粗細取自 `baseRadius/endRadius`，`set_dim` 對它無效。
- 圓角做法：`build_spec_v10.py` 寫 `geometryDescriptor.edgeTreatment = {type: "bevel", bevelRadius: r, segments: 2}`。`main.ts` 讀 spec，對 `primitive == "box"` 且 `bevelRadius > 0` 的 mesh 換成 `new RoundedBoxGeometry(w, h, d, 2, r)`，`w/h/d` 取 `transform.scale`。它繼承 `BoxGeometry`，face 順序不變，材質陣列照用。`mergeGroups` 之後 group 數會少於 6，這是正常的。最短邊 < 0.1 的零件不圓角。
- 圓角會讓貼齊父件的子件在弧邊凸出來。規則：子件在父件某一面上的範圍若落在 `(父件範圍 - 2r, 父件範圍]`，就要縮到 ≤ 父件範圍 - 2r。比父件大的子件 (簷板、桶蓋、橘帶) 是刻意外伸，不算。
- 道具站在草地上：草地變厚時，站在上面的 bush、trunk、bin、flagpole 一起抬高同樣高度。agave 是草地子件，只抬草地中心上移的量。
- 現有 id 不改名：`s-az`、`v-az`、`s-hue`、`v-hue`、`s-ch`、`v-ch`、`sel`、`b-detach`、`b-reset`。`check_orbit.py` 與 `check_hue.py` 靠這些 id，`check_orbit.py` 在 1280×800 畫面中央 `(640, 400)` 拖曳。
- **gate mode 完全不變**：`?gate=1` 的光線、曝光、背景、影子都照 v9。新的光線、影子、接觸陰影、背景漸層、UI、自動旋轉、旗面飄動、hover 與選取高亮都只在 normal mode。原因：pump-orange 是在 gate 光線下調到 dE 2.4 (ledger v8 Task 5)，`interior_difference` 的 baseline 也是 gate 圖。
- 驗收看 normal mode。`scripts/capture_normal.py` 在 v3 角度截圖：`azimuth -51, elevation 9.5, distance 30, fov 30, target [0, 1.5, 0]`。既有 gates 照舊用 gate 截圖。
- 顏色目標取自 v3 實測 (2026-11-22)：雨棚正面 `#F16925`、地面 `#E7E2DC`、背景 `#E8D4C5`。現況是 `#C94D1A`、`#B9B1A8`、`#E7D4C5`。門檻 CIE76 dE ≤ 10 (推論)。
- 黏土質感：環境光加進來後，spec 裡 clearcoat 1.0、roughness 0.05 的材質 (soil、grass、fascia-orange、pump-orange) 會出現鏡面反光，看起來像塑膠。normal mode 一律把 `clearcoat` 設 0。
- **Ruling (待你在審 plan 時同意)：** `performanceBudget.maxDrawCalls` 160 → 260，量 gate mode。normal mode 含影子的上限 520。三角形上限 250000 不變。subagent 實測：v9 gate 160，normal 開影子 237。估算做完是 gate 約 210、normal 約 330、三角形約 215k。代價：手機上可能掉幀，sample 的作品也是桌機展示。Task 1 把這個值寫進 spec。
- 不用後製 AO (`GTAOPass`、`SAOPass`)：它整個場景再畫一次，normal mode 會超過 520。改用接觸陰影貼片 (一個 `InstancedMesh`，1 次 draw call)。
- 既有檢查全部保留，每輪都跑：`check_grounded.py`、`check_soil.py`、`check_view.py`、`check_final.py`、`check_hue.py`、`check_orbit.py`、`check_layout.py`、`check_canopy.py`、`check_scene.py`。
- img2threejs 修正次數現在 `total=3/6`。第 1 輪的 spec 改動只有色值與旗子，不記 `reviewHistory` (同 v8 Task 5 調 pump-orange 的做法)。第 2、3 輪各記一筆 `refine-spec`，結束是 `5/6`。reviewer 判不過時記 `request-input` 並停下。
- rollback 點是 git tag `pre-v10`。每個 Task 完成後 commit 一次。
- 每個 Task 完成後複製新的 `docs/summary/yyyymmddhhmmss_plan_summary.md`，`.img2threejs/ledger.md` 加一行。

## 範圍外

- 車子、人物：v3 沒有。
- 同材質每塊顏色微差、水波、行駛的列車：sample 有，v3 沒有。
- orthographic camera：sample 有，v3 是透視。
- 開場鏡頭動畫：sample 是靜態截圖，看不出有沒有，先不做。
- 底座寬扁 (原清單 2e)：量過，v3 與現況的底座厚寬比接近，取消。
- roundel 縮小 (原清單 2h 的半徑)：量過，現況直徑約雨棚正面高度 1.5 倍，v3 約 1.3 倍，差距小，只加厚不縮。
- pump-orange 改色 (原清單 2a)：gate 下已 dE 2.4，偏暗是光線造成，交給 normal mode 光線處理。
- 樹幹彎曲：圓柱只做傾斜 8 度，不做 tube 彎曲。

## 清單對照

| 輪 | 清單項目 | Task |
| --- | --- | --- |
| 1 | 1a–1f 光影、雨棚頂色、泥土；2b 玻璃、2c 綠色、3j Mart 玻璃貼圖、旗子朝向與大小；接觸陰影、背景漸層 | 2 |
| 1 | 1g–1l 自動旋轉、游標、選取高亮、面板、標題、工具列；面板參數擴充、樣式、hover | 3 |
| 2 | 2d、2f、2g、2h、2i、2j 柱子、道具放大、圓角、roundel 加厚、立體字、草地；Mart 招牌露出 | 4 |
| 3 | 3a–3h 加油機 | 5 |
| 3 | 3i、3k–3s Mart 簷板與橘帶、垃圾桶、樹、agave、旗杆、旗面飄動、車道線、擋條、嵌燈 | 6 |
| 檢查 | 4a–4d | 1、7 |

## Review Focus

1. 自動旋轉讓 `check_orbit.py` 的 `stable()` 等不到靜止：預設關，只由工具列按鈕打開。`check_ui.py` 斷言 6。
2. 圓角後貼齊的子件從弧邊凸出：`check_details.py` 斷言 7。
3. 影子與接觸陰影讓 normal mode draw call 爆掉：`check_scene.py` normal mode 量測。
4. 道具放大或新增後互撞、超出底座：每輪跑 `check_layout.py`，Task 1 把新零件加進它的道具清單。
5. 選取或 hover 高亮取消後材質沒還原：`check_ui.py` 斷言 7。

---

## 使用者停點

| 停點 | 在哪個 Task 之後 | 你要做什麼 |
| --- | --- | --- |
| 0 | 開工前 | 審 plan，同意 draw call ruling |
| A | Task 3 | 開 http://localhost:5173，看光影、配色、UI，比 `shots/v10_r1_v3view.png` 與 v3 |
| B | Task 4 | 看比例、圓角、立體字，比 `shots/v10_r2_v3view.png` |
| C | Task 7 | 看細節與 reviewer 分數，驗收 |

任一檢查調 3 次數值仍不過，就停下問你。

---

### Task 1: 檢查腳本先寫 (先失敗)

**Files:**
- Create: `scripts/capture_normal.py`、`scripts/check_ui.py`、`scripts/check_details.py`、`backup/spec_before_v10.json`、`scripts/build_spec_v10.py`
- Modify: `scripts/check_scene.py`、`scripts/check_layout.py`、`scripts/dump_parts.py`、`object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)

**Interfaces:**
- Consumes: `scripts/_viewer.py` 的 `gate_page(query)` (傳 `""` 就是 normal mode)、`set_camera()`；`scripts/_geom.py` 的 `boxes()`；`scripts/color_check.py` 的 `lab()`；`scripts/check_orbit.py` 的 `stable()`。
- Produces:
  - `python3 scripts/capture_normal.py <out.png>`：存 normal mode v3 角度截圖，印出三個顏色的 dE，任一 > 10 時 exit 1。
  - `python3 scripts/check_ui.py`：exit 0 代表 UI 斷言全過。
  - `python3 scripts/check_details.py --round {1,2,3a,3}`：每一輪包含前一輪全部斷言 (`3a` 只多加油機那幾項)。
  - `check_scene.py` 多印 `drawCallsNormalMax`、`triangles`。

- [ ] **Step 1: 寫 `scripts/capture_normal.py`**

截圖前等 1 秒讓影子與貼圖載完。取色都從 page screenshot 讀 9×9 平均：
1. 雨棚正面：world 點 `(canopy 最小 x - 0.01, canopy y 中心, -3.0)` 用 camera 投影到像素。
2. 地面：world 點 `(-7.8, 0.17, 8.6)`。這點在雨棚外，也不在草地上。
3. 背景：像素 `(640, 30)`。這點在標題、面板、工具列之外。

- [ ] **Step 2: 寫 `scripts/check_ui.py`**

normal mode 斷言：
1. `#eyebrow`、`#title`、`#footnote` 存在且可見。
2. `#panel` 裡至少 4 個 `.group`、至少 12 個 `input`。每個 `input[type=range]` 同一列有一個 `input[type=number]`，改其中一個，另一個跟著變。按 `#panel-head` 後 `#panel-body` 收合，再按展開。
3. `#toolbar` 有 `#b-reset-view`、`#b-rotate`、`#b-fullscreen`、`#b-shot`，每顆裡面是 `<svg>`。
4. canvas 的 `cursor` 是 `grab`。滑鼠停在 `mart` 上時是 `pointer`。
5. 拖曳 canvas，用 `stable()` 等相機靜止，按 `#b-reset-view`，再等靜止，位置與初始值差 < 0.01。
6. 頁面載入 3 秒後 `controls.autoRotate` 是 false。按 `#b-rotate` 後是 true，再按回 false。
7. 先記下 `mart` 每個材質元素的 `emissive` hex。`__IMG2THREEJS_PICK__.select('mart')` 後每個元素都是 `0xffb070`。`select(null)` 後回到原值。

gate mode 斷言：
8. `#eyebrow`、`#title`、`#toolbar`、`#panel` 的 `display` 是 `none`，`controls.autoRotate` 是 false，`scene.background` 是 `0x303030`。

- [ ] **Step 3: 寫 `scripts/check_details.py`**

`--round 1`：
1. 在 v3 角度，兩面旗的投影寬度除以各自旗桿的投影高度，介於 0.19 到 0.26 (v3 實測約 0.23)。
2. `glass-dark` 的顏色不是 `#2F3135`。

`--round 2` 再加：
3. `kerb-verge-a`、`kerb-verge-b`、`kerb-verge-c` 存在，parent 是 `base-slab`。
4. spec 裡 `bevelRadius > 0` 的 box，live mesh 的 `geometry.type` 是 `RoundedBoxGeometry`。
5. `column-1..4` 的 primitive 是 box。`column-disc-*` 的 world 中心與 `shots/v10_disc_before.json` 的差 < 0.05 (本斷言只在 `--round 2` 跑，第 3 輪會移動圓牌)。json 在本步驟先從 live viewer 傾印。
6. `canopy-wordmark` 底下有一個 `ExtrudeGeometry` mesh，world bbox 的 z 寬介於 2.0 到 2.6。
7. 貼齊檢查：每個 `bevelRadius > 0` 的 box，它的直屬子件若有一面貼齊父件表面 (差 < 0.06)，且在該面上某方向的範圍落在 `(父件 - 2r, 父件]`，就判失敗。
8. 在 v3 角度，從相機往 `mart-sign` 中心打 ray，第一個碰到的是 `mart-sign`。

`--round 3a` 再加：
9. `pump-hose-Na/Nb` (parent `pump-N`)、`pump-cabinet-top-N` (parent `pump-cabinet-N`)、`pump-standee-3` (parent `pump-3`)、`column-disc-b-N` (parent `column-N`) 存在。N 是 1–4。
10. `pump-island-N` 的 geometry 是 `ExtrudeGeometry`，world bbox 最低點 ≥ 0.15。

`--round 3` 再加：
11. `mart-eave` (parent `mart`)、`bin-*-lid`、`bin-*-wheels`、`tree-N-b` (parent `tree-N-trunk`)、`agave-N-leaf-4/5`、`flagpole-N-base`、`flagpole-N-finial` 存在。旗桿是 1–2。

- [ ] **Step 4: 改 `check_scene.py`、`check_layout.py`、`dump_parts.py`**

1. `check_scene.py`：上限從 spec 的 `performanceBudget.maxDrawCalls` 讀。加 normal mode：同 12 個角度量 `renderer.info.render.calls` 最大值，上限是 gate 上限的 2 倍。三角形取 gate 參考角度的 `renderer.info.render.triangles`。任一超標 exit 1。
2. `check_layout.py`：道具清單加 `tree-N-b` (與 `tree-N` 同組)、`bin-*-lid` 與 `bin-*-wheels` (與該桶同組)、`flagpole-N-base/finial` (與該旗桿同組)。
3. `dump_parts.py`：跳過沒有 `sculptComponent` 的 mesh (陰影平面、接觸陰影)。

- [ ] **Step 5: 備份 spec，寫 `build_spec_v10.py`，套 draw call ruling**

Run: `cp object-sculpt-spec.json backup/spec_before_v10.json`

`build_spec_v10.py` 這時只做還原、接回 review 欄位、設 `spec["performanceBudget"]["maxDrawCalls"] = 260`，再寫回。後面的 Task 在檔尾加段落，每段用 `# --- Round N ---` 註解分開。

Run: `python3 scripts/build_spec_v10.py && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts --force && npx tsc --noEmit`
Expected: 全部 exit 0。

- [ ] **Step 6: 跑測試確認失敗**

Run: `python3 scripts/capture_normal.py shots/v10_r0_v3view.png; python3 scripts/check_ui.py; python3 scripts/check_details.py --round 1; python3 scripts/check_scene.py; python3 scripts/check_layout.py`
Expected: 前三支 FAIL。capture_normal 至少雨棚與地面 dE > 10。`check_scene.py`、`check_layout.py` exit 0，照實記錄 normal mode 數字。

- [ ] **Step 7: rollback 點與 commit**

```bash
git tag pre-v10
git add scripts/ backup/spec_before_v10.json object-sculpt-spec.json src/createCaltexStationModel.ts shots/v10_disc_before.json shots/v10_r0_v3view.png
git commit -m "test: normal-mode capture, UI and detail checks; draw-call budget 260 (v10 task 1)"
```

---

### Task 2: 光影、配色、玻璃、旗子 (第 1 輪)

**Files:**
- Modify: `src/main.ts:12-20`、`src/main.ts:50-60`、`src/main.ts:200-213`、`src/main.ts:236-239`、`index.html:8`、`scripts/build_spec_v10.py`、`object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)

**Interfaces:**
- Consumes: Task 1 的 `capture_normal.py`、`check_details.py --round 1`、`build_spec_v10.py`。
- Produces: `scene.environment` (normal mode)、`key.castShadow = !gate`、`shadow-catcher` 與 `contact-shadows` 兩個不帶 `sculptComponent` 的 mesh (點選不到)。Task 3 的面板會調這些值，所以光線參數放在一個 `look` 物件裡 (`exposure`、`envIntensity`、`sunAz`、`sunEl`、`shadowRadius`、`bg`)。

- [ ] **Step 1: 改光線 (只在 normal mode)**

起始值 (推論，以 Step 5 的 dE 為準)：
| 項目 | 現值 | 新值 |
| --- | --- | --- |
| `renderer.toneMappingExposure` | 1 | 1.25 |
| `scene.environment` | 無 | `PMREMGenerator` + `RoomEnvironment`，`scene.environmentIntensity = 0.4` |
| `HemisphereLight` 顏色 | `0xeaf0f6`、`0xd8d2c8` | `0xfff4e6`、`0xe8d6c6` |
| key 影子 | 無 | `castShadow`、`mapSize 2048`、shadow camera ±12、`radius 4`、`bias -0.0005`、`PCFShadowMap` (0.187 已移除 `PCFSoftShadowMap`) |
| 材質 clearcoat | 部分 1.0 | 全部 0 |

factory 已對每個 mesh 設 `castShadow`、`receiveShadow`，不用再設。

- [ ] **Step 2: 地面陰影、接觸陰影、背景漸層 (只在 normal mode)**

1. `shadow-catcher`：`PlaneGeometry(200, 200)` + `ShadowMaterial({ opacity: 0.18 })`，y 在 `base-slab` 底面。
2. `contact-shadows`：一個 `InstancedMesh`，平面貼一張徑向漸層 canvas (中心黑 35% 透明到邊緣全透明)，`depthWrite: false`。每個 instance 放在下列零件底下，大小是零件 xz 範圍的 1.3 倍：`pump-island-*`、`bin-*`、`tree-*-trunk`、`bush-*`、`mart`、`flagpole-*`，再加一個大的放在 `base-slab` 底下。
3. 背景：normal mode `renderer` 開 `alpha: true`、`scene.background = null`。`index.html` 的 body 背景改 CSS 徑向漸層，中心 `#EFDFD2`、邊緣 `#E2CBBA`。

- [ ] **Step 3: 雨棚頂色、泥土、Mart 玻璃 (viewer)**

1. 雨棚頂面 `0xe9e6e1` 改 `0xf3eee8`。
2. `soilTex()` 拿掉三條橫紋，改成底色 `#9A7756` 上隨機斑塊：兩個色 `#8A6446`、`#B08E6C`，半徑 6–30 px，覆蓋約 40%，再加原本 3% 的細點。亂數沿用現有 LCG 與 seed。
3. 3j：`mart-window` 的 `-x` 面貼 canvas：底色用 `glass-dark`，畫幾排較淺的貨架剪影，加一道斜向白色反光 (20% 透明)。

- [ ] **Step 4: 在 `build_spec_v10.py` 加 Round 1 段 (色值與旗子)**

| 項目 | 元件或材質 | 現值 | 新值 |
| --- | --- | --- | --- |
| 2b | `glass-dark` | `#2F3135` | `#4A4F57` (灰藍，推論) |
| 2c | `grass` | `#6FA055` | `#5FB84A` |
| 2c | `tree-green` | `#4FA63E` | `#5DBB45` |
| 旗子 | `flag-malaysia`、`flag-johor` | 旗面朝 +z，在 v3 角度被斜著壓扁 | 先繞旗桿轉 y，讓旗面法線朝 v3 相機 (約 -30 度，推論)。斷言 1 仍不過再放大，寬高比維持 2:1 |

旗子轉向後跑 `check_layout.py`，旗面不能出底座。`assumptions` 加一條：色值與旗子朝向依 v3 像素推論。

- [ ] **Step 5: 驗證**

Run: `python3 scripts/build_spec_v10.py && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts --force && npx tsc --noEmit && python3 scripts/capture_normal.py shots/v10_r1_v3view.png && python3 scripts/check_details.py --round 1 && python3 scripts/check_layout.py && python3 scripts/check_scene.py && python3 scripts/check_soil.py && python3 scripts/turntable.py v10_r1 && python3 scripts/color_check.py shots/v8_v10_r1_ref.png`
Expected: 全部 exit 0。dE 不過就調曝光與 hemi 強度，最多 3 次。gate 光線沒動，`color_check.py` 應維持 dE 2.4 左右。

- [ ] **Step 6: Commit**

```bash
git add src/main.ts index.html scripts/build_spec_v10.py object-sculpt-spec.json src/createCaltexStationModel.ts shots/v10_r1_v3view.png shots/v8_v10_r1_*
git commit -m "feat: soft light and shadows, contact shadows, v3 greens, glass, flags facing camera (v10 task 2)"
```

---

### Task 3: 作品頁 UI (第 1 輪，停點 A)

**Files:**
- Modify: `index.html`、`src/main.ts:41-48`、`src/main.ts:291-339`

**Interfaces:**
- Consumes: Task 1 的 `check_ui.py`；Task 2 的 `look` 物件。
- Produces: DOM id `#eyebrow`、`#title`、`#footnote`、`#panel`、`#panel-head`、`#panel-body`、`.group`、`#toolbar`、`#b-reset-view`、`#b-rotate`、`#b-fullscreen`、`#b-shot`。

- [ ] **Step 1: 改 `index.html` 版面與字型**

1. 左上：`#eyebrow` 小字 `JOHOR · MALAYSIA`，字距加寬。下面 `#title` 大號 `加油站`，字型 `"Songti TC", "Noto Serif TC", serif`。
2. 左下：`#footnote` 兩行。第一行斜體襯線 `Caltex Station`，第二行 12px 灰字 `Three.js · 全程式生成，無外部模型`。
3. 右上：`#panel` 寬 240px，圓角 12px，白色 85% 透明，柔和陰影。頂部 `#panel-head` 寫 `參數`，點擊收合 `#panel-body`。
4. 底部中央：`#toolbar` 膠囊形，4 顆按鈕用 inline SVG 圖示 (重置、旋轉、全螢幕、相機)，中間一條細分隔線，各帶 `title` 屬性。不用 Unicode 符號，`⛶` 在部分系統會顯示成 emoji。
5. `body.gate` 隱藏上面全部。
6. 面板與工具列不蓋住 1280×800 畫面中央 `(440–840, 250–550)`，`check_orbit.py` 在那裡拖曳與點選。

- [ ] **Step 2: 面板參數與樣式**

每列是「標籤、細灰滑桿、右側數值框」，或「標籤、色票、hex 文字」。滑桿用 CSS 改成 2px 灰色軌道、10px 圓點。

| 組 | 參數 | 綁到 |
| --- | --- | --- |
| 光線 | 太陽方位 (`s-az`，保留)、太陽高度、曝光、陰影柔和度、環境光強度 | `look` |
| 顏色 | 橘色色相 (`s-hue`，保留)、雨棚色、草地色、加油機色、背景色 | 材質 `color` 與 CSS 變數 |
| 結構 | 雨棚高度 (`s-ch`，保留) | 現有邏輯 |
| 動態 | 自動旋轉速度、旗面風力 (Task 6 才接到旗子，之前先存值) | `controls.autoRotateSpeed`、`look.wind` |
| 零件 | 選取名稱 (`sel`)、抬起 (`b-detach`)、重置 (`b-reset`) | 現有邏輯 |

色票用 `<input type="color">`。數值框與滑桿雙向同步。

- [ ] **Step 3: 改 `main.ts` 操作**

1. canvas `cursor: grab`，`pointerdown` 時 `grabbing`。滑鼠移到零件上時 `pointer`，且該零件加淡高亮 (`emissive 0xffb070`、強度 0.15)，移開還原。
2. `#b-rotate` 切換 `controls.autoRotate`。gate mode 不綁。
3. `#b-reset-view` 呼叫 `controls.reset()`。建立 controls 並 `update()` 後立刻 `controls.saveState()`。
4. `#b-fullscreen` 切換 `requestFullscreen()` / `exitFullscreen()`。
5. `#b-shot` 用 `renderer.domElement.toDataURL()` 下載 PNG (`preserveDrawingBuffer` 已開)。
6. 選取高亮：拿掉 `BoxHelper`。選取時把該零件底下所有 mesh 的材質 clone，`emissive 0xffb070`、強度 0.35。取消時換回原材質，原材質存在 `Map<Mesh, Material | Material[]>`。hover 與選取共用這個 Map。

- [ ] **Step 4: 驗證**

Run: `npx tsc --noEmit && python3 scripts/check_ui.py && python3 scripts/check_orbit.py && python3 scripts/check_hue.py && python3 scripts/check_view.py && python3 scripts/check_final.py && python3 scripts/capture_normal.py shots/v10_r1_v3view.png`
Expected: 全部 exit 0，`check_orbit` 7/7。

- [ ] **Step 5: Commit 與停點 A**

```bash
git add index.html src/main.ts shots/v10_r1_v3view.png
git commit -m "feat: gallery page with serif title, styled collapsible panel, svg toolbar, hover (v10 task 3)"
```

給使用者 http://localhost:5173 與 `shots/v10_r1_v3view.png`。

---

### Task 4: 比例、圓角、立體字 (第 2 輪，停點 B)

**Files:**
- Modify: `scripts/build_spec_v10.py`、`object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)、`src/main.ts`、`material-evidence/decals/caltex_wordmark.svg` (新增複本)

**Interfaces:**
- Consumes: Task 1 的 `check_details.py --round 2`、Task 2 的 `build_spec_v10.py`。
- Produces: 新元件 `kerb-verge-a/b/c`，新材質 `curb-grey`、`column-dark`。`main.ts` 的 `roundBoxes()` 與 `extrudeWordmark()`。

- [ ] **Step 1: 在 `build_spec_v10.py` 加 Round 2 段**

數值是起始值 (推論)，以 Step 4 的檢查為準。

| 項目 | 元件或材質 | 現值 | 新值 |
| --- | --- | --- | --- |
| 2d | `column-1..4` | cylinder 半徑 0.28 | box `0.6 × 4.99 × 0.6`，保留 attachment，材質新 `column-dark` `#8E8A86`。`column-disc-*` local y 2.2 → -0.295 |
| 2f | `bin-*` | cylinder 0.6 × 0.82 | box `0.7 × 0.95 × 0.7`，`bevelRadius 0.06`。`bin-green-1` 的 z 移到與 `bin-blue-1` 中心相距 0.85 |
| 2f | `tree-1/2` 樹冠 | 1.0 | 1.2 |
| 2f | `tree-3/4` 樹冠 | 1.4 | 1.6 |
| 2f | `bush-*` | 0.9 × 0.7 × 0.9 | 1.1 × 0.8 × 1.1 |
| 2g | `bevelRadius` | 0 | `canopy` 0.03、`mart` 0.03、`concrete-top` 0.04、`pump-head-N` 0.06、`pump-cabinet-N` 0.05、`grass-verge-*` 0.04、`wheel-stop-*` 0.04、`kerb-mart` 0.04 |
| 2g | 貼齊子件 | `fascia-lip-top` 深 14.0、`pump-sign-N` 0.5 × 1.45 | `fascia-lip-top` 深 13.94；`pump-sign-N` 高 0.43、長 1.38 |
| 2h | `roundel-logo` | 厚 0.2 | 厚 0.28，半徑維持 0.6 |
| 2j | `grass-verge-*` | 高 0.12 | 高 0.2，底面留在地面 |
| 2j | `kerb-verge-a/b/c` | 無 | box，`curb-grey` `#C9C6C2`，寬 0.12、高 0.24，沿各草地朝場內的長邊 |
| 招牌 | `mart-sign` | local z -1.8 | 移到斷言 8 通過的位置，先試 band 中心 z 0 |

`base-slab`、`pump-N`、`pump-island-N` 不圓角：`concrete-top` 與 `base-slab` 同尺寸、`pump-panel` 比 `pump-N` 寬、島在第 3 輪改膠囊形。

草地加高 0.08 後，`bush-*`、`tree-N-trunk`、`bin-*`、`flagpole-*` 一起抬高 0.08。agave 抬 0.04。

`assumptions` 加一條：比例與道具尺寸依 v3 像素推論。

- [ ] **Step 2: `main.ts` 的 `roundBoxes()`**

import `RoundedBoxGeometry`。在材質覆寫與 `mergeGroups` 之前跑，規則見 Global Constraints。

- [ ] **Step 3: `main.ts` 的 `extrudeWordmark()`**

1. 複製 `assets/caltex_wordmark.svg` 到 `material-evidence/decals/` (Vite 的 publicDir)。它有 2 個 `<path>`、7 個子路徑，沒有洞。
2. `SVGLoader` 讀檔，`SVGLoader.createShapes()` 收齊全部 shape，餵給一個 `ExtrudeGeometry(shapes, { depth: 4.5, bevelEnabled: true, bevelThickness: 0.6, bevelSize: 0.4 })`。深度單位是 SVG 單位，縮放後約 0.06。
3. 不把負 scale 烘進 geometry (會內外翻面)。改在 mesh 上設 `scale.set(s, -s, s)`，`s = 2.4 / 180`。
4. 轉到朝 `-x`，加成 `canopy-wordmark` mesh 的子物件，置中在它的 bbox。原本的平面貼圖改 `hidden`。

- [ ] **Step 4: 生成並驗證**

Run: `python3 scripts/build_spec_v10.py && python3 $K/forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality && python3 $K/forge/stage3_build/generate_threejs_factory.py object-sculpt-spec.json --out src/createCaltexStationModel.ts --force && npx tsc --noEmit && python3 scripts/check_details.py --round 2 && python3 scripts/check_layout.py && python3 scripts/check_canopy.py && python3 scripts/check_grounded.py && python3 scripts/check_soil.py && python3 scripts/check_final.py && python3 scripts/check_view.py && python3 scripts/check_hue.py && python3 scripts/check_scene.py && python3 scripts/check_orbit.py && python3 scripts/turntable.py v10_r2 && python3 scripts/capture_normal.py shots/v10_r2_v3view.png && python3 scripts/color_check.py shots/v8_v10_r2_ref.png`
Expected: 全部 exit 0。layout 撞到就挪道具位置，最多 3 次。

- [ ] **Step 5: reviewer 與記錄**

派 Opus subagent，只給 `v3.webp`、`docs/sample/IMG_4548.PNG`、`shots/v10_r2_v3view.png`、`shots/v8_v10_r2_sheet.png`、v9 分數。它照 v9 的 5 個 critical 門檻評分，另外給「整體感覺像不像 v3」與「操作頁像不像 sample」各一個 0–1 分數與理由。
用 `append_review --force-out-of-order` 記一筆 `refine-spec`，未達門檻照實記錄。

- [ ] **Step 6: Commit 與停點 B**

```bash
git add scripts/build_spec_v10.py object-sculpt-spec.json src/createCaltexStationModel.ts src/main.ts material-evidence/decals shots/v10_r2_* shots/v8_v10_r2_*
git commit -m "feat: square columns, rounded boxes, extruded wordmark, raised verges (v10 task 4)"
```

給使用者 http://localhost:5173 與 `shots/v10_r2_v3view.png`。

---

### Task 5: 加油機細節 (第 3 輪)

**Files:**
- Modify: `scripts/build_spec_v10.py`、`object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)、`src/main.ts:102-114`、`src/main.ts:133-154`、`src/main.ts:233-235`

**Interfaces:**
- Consumes: Task 4 的 `build_spec_v10.py`、`roundBoxes()`。
- Produces: 新元件 17 個，新材質 `pump-grey`、`nozzle-black`。

- [ ] **Step 1: 在 `build_spec_v10.py` 加 Round 3a 段**

| 項目 | 改動 |
| --- | --- |
| 3a | `pump-panel-N` 材質改新 `pump-grey` `#C8C6C2`，機身下半維持 `pump-orange` |
| 3b | `pump-nozzle-Na/Nb` 材質改新 `nozzle-black` `#262626`。新增 `pump-hose-Na/Nb`，cylinder 半徑 0.03，從油槍頂端往下 0.6 |
| 3d | 新增 `pump-cabinet-top-N`，box `0.42 × 0.25 × 0.37`，`pump-grey`，疊在 `pump-cabinet-N` 頂上 |
| 3e | 新增 `pump-standee-3`，box `0.08 × 1.0 × 0.45`，`pump-white`，立在 `pump-3` 前方的島上 |
| 3g | `pump-island-N` 加 `geometryDescriptor.planShape: "stadium"`，`bevelRadius` 維持 0 |
| 3h | `column-disc-N` 移到 local z -0.42。新增 `column-disc-b-N` 在 z +0.42。兩片都從柱子側面伸出去，軸向維持 x，兩面都顯示號碼 |

新元件用 `clone()` 從同類現有元件複製。

- [ ] **Step 2: `main.ts` 貼圖與膠囊島**

1. 3c：`pump-poster-*` 的 `-x` 面貼 canvas，天藍漸層加橘色色塊。
2. 3e：`pump-standee-3` 的 `-x` 面貼 canvas，白底、黑字 `Fuel up` 加小圖塊。
3. 3f：`pumpSignTex()` 改成左邊白色梯形放 roundel、右邊深青色，交界是斜線。
4. 3g：`planShape == "stadium"` 的 mesh 換成 `ExtrudeGeometry`：`Shape` 用 `absarc` 畫寬 1.3、長 3.4 的跑道形，擠出 0.2，轉成 y 向上，再沿 y 平移 -0.1 讓中心對齊原本的 box。
5. 3h：`column-disc-*` 的材質陣列改成 `[白色側面, 號碼, 號碼]`，兩面都顯示 (`main.ts:233-235` 現在第三面是 hidden)。

- [ ] **Step 3: 生成並驗證**

Run: 同 Task 4 Step 4，`check_details.py` 改 `--round 3a`，turntable 改 `v10_r3a`。
Expected: 全部 exit 0。

- [ ] **Step 4: Commit**

```bash
git add scripts/build_spec_v10.py object-sculpt-spec.json src/createCaltexStationModel.ts src/main.ts
git commit -m "feat: two-tone pumps, hoses, posters, standee, capsule islands, twin number discs (v10 task 5)"
```

---

### Task 6: Mart、道具、旗子、地面細節 (第 3 輪)

**Files:**
- Modify: `scripts/build_spec_v10.py`、`object-sculpt-spec.json`、`src/createCaltexStationModel.ts` (生成)、`src/main.ts:116-131`、`src/main.ts:179-199`、`src/main.ts:242-248`、`src/main.ts:358`

**Interfaces:**
- Consumes: Task 5 的 `build_spec_v10.py`；Task 3 的 `look.wind`。
- Produces: 新元件約 25 個，新材質 `agave-variegated`、`wheel-black`。

- [ ] **Step 1: 在 `build_spec_v10.py` 加 Round 3 段**

| 項目 | 改動 |
| --- | --- |
| 3i | 新增 `mart-eave`，box `3.4 × 0.15 × 9.4`，`mart-white`，蓋在 `mart` 頂上，四邊外伸 0.2，`bevelRadius 0.05` |
| 3l | 新增 `bin-*-lid` (box `0.78 × 0.08 × 0.78`，同材質) 與 `bin-*-wheels` (cylinder 半徑 0.08、長 0.7，水平，`wheel-black` `#2A2A2A`，貼在桶背面底部) |
| 3m | 新增 `tree-N-b`，sphere，半徑是主樹冠的 0.55 倍，相對主樹冠偏移 `(0.45, -0.25, 0.3)`。`tree-N-trunk` 半徑 0.12 → 0.07，傾斜 8 度 |
| 3n | 每株 agave 新增 `leaf-4`、`leaf-5`。5 片葉往外傾斜 25–40 度，`leaf-2`、`leaf-5` 用 `agave-variegated` `#9BC25A` |
| 3o | 新增 `flagpole-N-base` (box `0.3 × 0.15 × 0.3`) 與 `flagpole-N-finial` (sphere 半徑 0.09)，材質 `column-dark` |

- [ ] **Step 2: `main.ts` 改動**

1. 3k：`martFaceTex()` 的側面與背面不畫橘帶，只有正面的 `mart-band` 保留。
2. 3l：垃圾桶正面貼 canvas 回收標誌 (白色三箭頭)。
3. 3p：旗面飄動。每幀改 `flag-*` geometry 的頂點 z：`sin(x * 6 + t * 3) * look.wind * (x - 旗桿端 x)`，旗桿端固定，`look.wind` 預設 0.06。改完 `computeVertexNormals()`。只在 normal mode。flag box 有 12 段細分，頂點夠用。
4. 3q：`stallTex()` 加白色虛線，寬 0.1，實 0.8、空 0.6，沿 z 方向，x 在 -1.1 與 2.7 (推論，兩排油島之間與 Mart 前)。
5. 3r：`stripeTex()` 改黃底配短黑段：128 px 寬裡黑段 24 px。
6. 3s：`soffitTex()` 的燈改成金屬圈 `#b8b4ae` 6 px 加內圈白。另做一張 `emissiveMap` 只有燈是白、其他全黑，`emissiveIntensity` 0.25 → 0.6。

- [ ] **Step 3: 生成並驗證**

Run: 同 Task 4 Step 4，`check_details.py --round 3`，turntable 改 `v10_r3`，截圖存 `shots/v10_r3_v3view.png`。
Expected: 全部 exit 0。draw call 超過 260 或 520 就停下問使用者。

- [ ] **Step 4: Commit**

```bash
git add scripts/build_spec_v10.py object-sculpt-spec.json src/createCaltexStationModel.ts src/main.ts shots/v10_r3_* shots/v8_v10_r3_*
git commit -m "feat: mart eave, wheelie bins, two-ball trees, waving flags, lane lines, downlights (v10 task 6)"
```

---

### Task 7: gates、評分與文件 (停點 C)

**Files:**
- Modify: `object-sculpt-spec.json` (`reviewHistory`)、`parts.json`、`REPORT.md`、`.img2threejs/ledger.md`
- Create: 新的 summary 快照

- [ ] **Step 1: gates**

照 v9 Task 4 Step 1 的清單跑：Tier 1、`diagnose_render_multi_angle.py`、`turntable_gate.py --allow-holes`、`interior_difference.py` (baseline `shots/v8_v9_ref.png`)、`attachment_anchor.py`、`make_comparison_sheet.py`。
Expected: `attachment_anchor.py` 0 errors，turntable gate pass。

- [ ] **Step 2: 獨立 reviewer**

同 Task 4 Step 5，換成 `shots/v10_r3_v3view.png` 與 `shots/v8_v10_r3_sheet.png`，附上 Task 4 的分數。
用 `append_review --force-out-of-order` 記一筆 `refine-spec`。未達門檻就改記 `request-input`。

- [ ] **Step 3: parts.json 與全部檢查**

Run: `python3 scripts/dump_parts.py && npx tsc --noEmit && npx vite build && python3 scripts/check_ui.py && python3 scripts/check_details.py --round 3 && python3 scripts/check_layout.py && python3 scripts/check_canopy.py && python3 scripts/check_grounded.py && python3 scripts/check_soil.py && python3 scripts/check_final.py && python3 scripts/check_view.py && python3 scripts/check_hue.py && python3 scripts/check_scene.py && python3 scripts/check_orbit.py && python3 $K/forge/stage4_review/check_part_coverage.py --spec object-sculpt-spec.json --manifest parts.json --inventory di.json && python3 $K/forge/next.py --state .img2threejs/state.json object-sculpt-spec.json`
Expected: 全部 exit 0，`next.py` 顯示 `total=5/6`。

- [ ] **Step 4: 文件、commit、停點 C**

`REPORT.md` 整份改寫成目前狀態，推論清單加上配色、旗子朝向、道具尺寸、車道線位置、draw call ruling。ledger 加一行，複製 summary 快照。

```bash
git add -A REPORT.md parts.json object-sculpt-spec.json .img2threejs docs/summary shots/v10_* shots/v8_v10_*
git commit -m "docs: v10 review, parts.json, report (v10 task 7)"
```

---

## Self-Review

1. Spec coverage：41 項都在「清單對照」有 Task。2a、2e、2h 縮小三項量過後取消，寫在範圍外。需求審查的 12 項中，10 項併入 Task 2、3、4，開場動畫與 AO 後製寫在範圍外與 Global Constraints。
2. Step scan：數值都標了起始值或實測來源，由檢查把關。
3. Type consistency：`check_details.py` 的 round 與 id 對得上 Task 2–6。`look` 物件在 Task 2 定義，Task 3、6 使用。`column-disc-b-N` 的命名配合 `main.ts` 的 `slice(-1)`。
4. Review Focus：5 項分別落在 `check_ui.py` 斷言 6、7，`check_details.py` 斷言 7，`check_scene.py` normal mode，`check_layout.py`。
5. Proportion：沒有貼 code 本體，數值集中在表格。
