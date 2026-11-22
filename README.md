[English](README.md) | [繁體中文](readme/README.zh-TW.md)

# Caltex Station (Procedural Three.js Diorama)

A 3D diorama of a Caltex petrol station in Johor, Malaysia. Built purely in Three.js code with procedural geometry, car animation, and Canvas 2D / SVG textures, with no external 3D model files.

## Quick Start

```bash
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

Common commands:
- `npm run dev`: Start the Vite dev server (`http://localhost:5173`)
- `npm run build`: Build the production bundle into `dist/`
- `npm run preview`: Preview the built `dist/` bundle
- `npm run typecheck`: Run `tsc --noEmit` to check TypeScript types

## URL Modes

- `/` (Normal mode): Full interactive showcase with soft shadows, environment lighting, waving flags, animated sports car, right-hand inspector panel, and bottom toolbar.
- `/?gate=1` (Gate mode): Automated acceptance mode with a fixed 1024×687 reference camera, grey background, no UI, no shadows, and no animation for deterministic pixel checks.
- `/?clay=1` (Clay mode): Uniform grey clay material to inspect silhouette and proportions.

## Code Architecture (`src/`)

```
src/
├── src/main.ts                    # App entry: wires scene, model, car, UI, and render loop
├── src/scene.ts                   # WebGLRenderer, PerspectiveCamera, OrbitControls, and sun/env lights
├── src/textures.ts                # Canvas 2D procedural textures (signs, stalls, soil strata, glass, stripes) and SVG decals
├── src/customizeModel.ts          # Model post-processing: bevels, 3D CALTEX letters, material overrides, draw-call merging, and flag wave
├── src/ui.ts                      # Right-hand sliders/pickers, raycast part picking/lifting, and bottom toolbar
├── src/car.ts                     # Procedural silver coupe with pit-stop loop animation
└── src/createCaltexStationModel.ts  # Auto-generated 157-part factory from object-sculpt-spec.json (do not edit by hand)
```

### Global Test Hooks (`window`)

Exposed for Playwright verification scripts:
- `window.__IMG2THREEJS_VIEWER__`: `{ renderer, scene, camera, controls }`
- `window.__IMG2THREEJS_CAPTURE__`: `{ setCamera, setReferenceMode }`
- `window.__IMG2THREEJS_PICK__`: `{ select, partCount }`
- `window.__IMG2THREEJS_READY__`: Set to `true` once the scene and 3D wordmark finish loading
- `window.__CAR_T__`: Optional timestamp override to freeze the car for screenshots

## Model Spec & Regeneration

`src/createCaltexStationModel.ts` is generated from `object-sculpt-spec.json`. Do not edit it manually. To adjust dimensions, colours, or part placement:
1. Edit `scripts/build_spec_v11.py` and run `python3 scripts/build_spec_v11.py` to update `object-sculpt-spec.json`.
2. Regenerate `src/createCaltexStationModel.ts` and update `parts.json` via `python3 scripts/dump_parts.py`.
3. `vite.config.ts` sets `publicDir` to `material-evidence/`, which serves PBR maps and `decals/`.
4. Historical build artifacts (crops, detail grids, backups) are archived in `archive/`.

## Automated Verification (`scripts/`)

Requires Python 3 and Playwright (`playwright`, `Pillow`):

```bash
python3 scripts/check_refactor.py       # Check modular src/ files, line limits, npm scripts, and README
python3 scripts/check_ui.py             # Check normal & ?gate=1 UI interactions, contrast, and zero errors
python3 scripts/check_v11.py --task 3   # Check camera framing, flag wave, soffit brightness, soil strata, and red canopy
```

Additional geometry and colour checks live in `scripts/` (`check_details.py`, `check_orbit.py`, `check_layout.py`, `check_canopy.py`, `check_scene.py`, `check_soil.py`, `check_hue.py`, `check_view.py`, `check_final.py`, `check_grounded.py`, `color_check.py`).
