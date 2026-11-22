# AGENTS.md

Caltex 加油站 (Johor, Malaysia) 的 Three.js diorama。全部由程式碼生成，沒有外部 3D 模型檔。

## 指令

1. `npm run dev`：Vite 開發伺服器，`http://localhost:5173`。
2. `npm run build`：打包到 `dist/`。
3. `npm run typecheck`：`tsc --noEmit`。
4. `python3 scripts/check_refactor.py`：檢查 `src/` 模組與行數上限。
5. `python3 scripts/check_ui.py`：檢查 normal 與 gate 模式的 UI。
6. `python3 scripts/check_v11.py --task 3`：檢查鏡頭、旗幟、雨棚、土壤。
7. `python3 scripts/check_pump_v13.py`：檢查三槍加油機與 gate 不變性 (其餘迴歸：`check_scene.py`、`check_layout.py`、`check_details.py --round 3`、`color_check.py`)。

檢查腳本需要 Python 3、`playwright`、`Pillow`，且 dev server 已啟動。

## URL 模式

1. `/`：normal mode，陰影、旗幟飄動、車子動畫、UI 全開。
2. `/?gate=1`：驗收專用。1024×687、灰底、無 UI、無陰影、無動畫。
3. `/?clay=1`：全灰白模，檢查輪廓與比例。

視覺改動只進 normal mode。gate mode 的光線凍結，顏色基準 (pump-orange dE 2.4) 依賴它。

## 結構

1. `src/main.ts`：入口，組裝其他模組。
2. `src/scene.ts`：renderer、camera、controls、燈光。
3. `src/textures.ts`：Canvas 與 SVG 貼圖。
4. `src/customizeModel.ts`：圓角、立體字、材質覆寫、draw call 合併、旗幟 (上限 260 行)。
5. `src/pumpParts.ts`：三槍加油機幾何與貼圖擴充，只在 `!gate` 啟用 (上限 260 行)。
6. `src/ui.ts`：面板、點選抬升、工具列。
7. `src/car.ts`：銀色跑車與進站動畫。
8. `src/createCaltexStationModel.ts`：自動生成，不手改。

每個 `src/` 檔維持 ≤300 行。

## 規則

1. 改模型結構或 spec 只改 `scripts/build_spec_v11.py`，再重生 `src/createCaltexStationModel.ts`；normal mode 專用視覺擴充寫進 `src/pumpParts.ts` 或 `src/customizeModel.ts`，不改 `/?gate=1` 與既有 `sculptComponent.id`。
2. 圓柱改位置要同時改 `attachment.localStart/End`。
3. 圓角父件的貼齊子件縮 `2r`。
4. 已被檢查腳本引用的 element id 不改名：`s-az`、`s-ch`、`c-pump`、`b-reset`、`b-reset-view`、`b-rotate`、`b-fullscreen`、`b-shot`。
5. `window.__IMG2THREEJS_*` 掛載給 Playwright 用，不改名。
6. 版本化文件開新版：`docs/superpowers/plans/` 與 `docs/summary/` 都用時間戳命名，不覆蓋舊檔。
7. 預算：gate draw calls ≤260，normal ≤520，三角形 ≤250000。
8. Tier 1 IoU 0.85 已由使用者整案豁免，所有下調的門檻列在 `REPORT.md`。
9. 同一 `sculptComponent.id` 同時有外層 Group (`!o.isMesh`) 與內層 Mesh (`o.isMesh`)：改位置與縮放用 Group，換材質與幾何用 Mesh。

## 重要檔案

1. `object-sculpt-spec.json`：建模規格。
2. `parts.json`：零件清單。
3. `.img2threejs/ledger.md`：每個 Task 的進度與決定。
4. `reference/`：參考圖。
5. `archive/`：歷史過程檔，已歸檔。
