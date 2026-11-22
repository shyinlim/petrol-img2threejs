# Caltex Station Three.js diorama: report

Preview: `npx vite --port 5173` then open http://localhost:5173. `?gate=1` is the 1024x687 review mode (reference camera, v9 light, grey background, no UI). `?clay=1` is the grey no-texture mode.

## The page (normal mode)

- UI is English, system font (SF Pro on Mac), designed against Apple HIG (`apple-design` skill). Title and subtitle top-left, one footnote bottom-left, floating inspector panel on the right (280 px, 5 groups, 9 sliders with number boxes, 4 colour pickers), bottom pill toolbar.
- Toolbar: Reset View, Auto Rotate (off by default), Full Screen, Save Image. Each has an `aria-label`.
- Panel: Sun azimuth, Sun height, Exposure, Shadow softness, Ambient light, Brand hue, Canopy / Grass / Pumps / Background colour, Canopy height, Spin speed, Wind. The panel title is a button (`aria-expanded`) that collapses it.
- Sliders have a 3 px track and a 14 px graphite thumb (`#4a4540`), 20 px hit height, keyboard focus ring system blue. Muted text is `#5f554e` (5.6:1 on the page background). Panel and toolbar turn solid with `prefers-reduced-transparency`.
- Mouse: drag rotates, hover on a part glows and shows a pointer, click selects, Lift / Drop lifts the part 3 units, Reset Parts puts every lifted part back (disabled until a part is lifted).
- Default camera: azimuth -51, elevation 4.2, distance 40, fov 30. It sits under the soffit (y 4.13 < 4.84) and a view offset moves the scene left of the panel when the window is 900 px or wider.
- Light: soft key light with shadows, RoomEnvironment light, ground shadow, contact blobs under props. Flags wave (Wind 0.14). The soffit glows with 3 x 4 downlights.

## Scene

- Shadow softness starts at 0. Canopy: Caltex red `#ED1B2F`, three white diagonal energy lines at the lower left of the long face, 3D CALTEX letters, deeper front lips. There is no CALTEX wordmark on the back face. The roundel (radius 0.5) stands on the right-hand short face, 0.85 in from the corner.
- Pumps: four islands, one number disc per column (centred on the column face). Wheel stops lie across each 1.2 x 4.8 stall at its outer end. The pump posters are removed.
- Left verge from the back: two bins (tapered, 85% at the base), agave, bush, tree, agave, tree.
- Mart band is the same red as the canopy. Mart glass is a vertical gradient with two glares, no shelf bars. Soil is horizontal strata.

## Output files

- `src/createCaltexStationModel.ts`: generated factory. Do not edit by hand. Edit `scripts/build_spec_v11.py` (restores `backup/spec_before_v11.json`, applies the v11 edits, keeps review history), then regenerate.
- `src/main.ts`: viewer, OrbitControls, panel and toolbar, textures, view offset, flag wave, hover and select glow, `energyLinesTex`.
- `object-sculpt-spec.json`: 157 components. `parts.json`: 158 built parts (`scripts/dump_parts.py`). `shots/`: renders, `shots/v11_gates/`: gate outputs.
- `scripts/`: `check_v11.py --task {2,3}`, `capture_normal.py`, `check_ui.py` (assertions 1 to 14), `check_details.py --round {1,2,3a,3}`, `check_layout.py`, `check_canopy.py`, `check_orbit.py`, `check_scene.py`, `check_soil.py`, `check_hue.py`, `check_view.py`, `check_final.py`, `check_grounded.py`, `color_check.py`, `turntable.py`.

## Current numbers

| Item | Value | Budget |
| --- | --- | --- |
| Draw calls, gate mode (max of 12 angles) | 206 | 260 |
| Draw calls, normal mode with shadows | 308 | 520 |
| Triangles | 216,250 | 250,000 |
| Piercing parts | none | none |
| Normal-mode colour dE76 vs v3 (canopy / ground / background) | 10.3 / 2.7 / 0.2 | 10 (canopy FAIL) |
| Pump orange dE76 vs v3 crop (gate light) | 2.4 | 12 |
| Tier 1 silhouette IoU | 0.594 | 0.85 (waived) |
| Tier 1 max colour dE | 45.95 | 20 (not waived) |
| Interior difference vs v10 | 0.040 | none |
| Turntable gate, multi-angle, attachment anchor | pass, not degenerate, 0 errors | pass |
| Part coverage | 157 specified, 158 built, 0 errors | 0 |

## Opus review against the original thresholds (not lowered)

The canopy criterion for this round is "Caltex red with white energy lines". The reviewer saw the build before the roundel, wheel-stop and number-disc fixes.

| Feature | v11 | Threshold | Result | v10 |
| --- | --- | --- | --- | --- |
| overall-silhouette (critical) | 0.74 | 0.80 | FAIL | 0.80 |
| canopy-identity (critical) | 0.85 | 0.80 | PASS | 0.86 |
| four-pumps-four-columns (critical) | 0.80 | 0.75 | PASS | 0.78 |
| mart band (critical) | 0.72 | 0.75 | FAIL | 0.80 |
| flags-exact (critical) | 0.68 | 0.80 | FAIL | 0.76 |
| important-feature average | 0.67 | 0.65 | PASS | 0.80 |
| overall | 0.75 | 0.70 | PASS | 0.78 |
| ui (like the sample) | 0.70 | none | info | 0.86 |

Review action recorded: `request-input` (three critical features under threshold). `next.py` shows `total=4/6`. Scores are one reviewer's judgement, noise about 0.02. The UI score is for the Chinese UI that existed at review time.

## Open gaps (most severe first)

1. Flags (0.68): both poles stand behind Mart at the back-right. v3 has the Malaysia pole front-right on the forecourt verge.
2. Silhouette (0.74): the canopy crops at the left edge at the 1280 x 800 default view, and the right panel hides the flags in the v3-angle capture.
3. Mart band (0.72): the rear and side walls have no red band.
4. Canopy dE 10.3 against `#ED1B2F`. Raising HSL lightness by 3, 6 and 9% gave 11.8, 15.0 and 19.9 (the red channel saturates), so the colour stays at `#ED1B2F`.
5. Soffit has downlights as a flat glow only, no recessed discs. The soffit strip is thin at the default view because the camera is almost level.
6. Pump bodies are brick red `#AC5545`. v3 is Caltex orange. Pump orange was tuned in gate light.
7. Brand hue slider moves the red fascia and Mart band, not the pumps.
8. Tier 1 max colour dE 45.95 (bins and small parts).

## Waivers (user decisions)

1. Tier 1 IoU 0.85 is waived for the whole project. Honest scores are kept.
2. Blockout silhouette threshold 0.8 to 0.6 (blockout pass only).
3. Earlier passes lowered visual and feature thresholds. The v8 to v11 reviews use the original ones.
4. Draw-call budget 160 to 260 (gate) and 520 (normal with shadows), accepted by running the v10 plan.

## Logo, wordmark, flags

- Vector SVGs from worldvectorlogo and Wikimedia Commons, not official brand files. Confirm with your own brand files before real use.
- The CALTEX wordmark is the SVG extruded in three.js (`canopy-wordmark` child mesh).
- Roundel is teal, red and white on the red canopy. The reference shows orange and white.
- Flags: Malaysia and Johor, turned 35 degrees toward the v3 camera, 1.8 x 0.9, wave in normal mode.

## Inferred (not measured)

- Canopy red `#ED1B2F` comes from brandcolor.dev, not an official spec. The Caltex Pakistan site describes a white star on red with white stripes across one corner. Stripe count (3), width and gap (0.14) and angle (55 degrees) are inferred.
- Roundel position on the right face, wheel-stop size (1.1 x 0.18) and end of the stall, the bin, tree, agave and bush order on the left verge, lip depth 0.18.
- Back and right faces, Mart rear, canopy rear, canopy underside.
- Round 1 colours (glass `#4A4F57`, grass `#5FB84A`, tree `#5DBB45`) and the flag turn come from v3 pixels. Light values (exposure 0.9, environment 0.3, hemisphere 0.7) were tuned to dE under 10.
- Round 2 and 3 proportions, prop sizes, bevel radii, Mart sign position, kerb strips, pump details, eave size, bin wheels, tree lean, agave splay, lane lines (x -1.1 and 2.7).
- Stall size 1.2 x 4.8. Roof colour `#f3eee8`. Pump orange `#AC5545` was tuned to one crop.
- Soil strata colours, band count and wave are an approximation of v3.

## Not run

- `self_intersection.py` (exporter missing), grazing-angle close-up, LOD, a check of the live flag wave in a recording, dark appearance of the page UI.
