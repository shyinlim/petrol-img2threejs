Diorama follow-up prompt v6 (send in the same chat after the v4 result, file reference/gen_v4_try1.png)

Same scene: keep the slab, trees, palm trees, wheelie bins, grass verges, Mart and flag exactly as they are.
Change only the camera, the canopy and the background:
- Lower the camera elevation to about 20 degrees so the space under the canopy is visible. Keep strict orthographic projection.
- Show the white underside with recessed ceiling lights, all four grey columns and all four fuel dispensers with Techron signs.
- Make the roof a thin slab so the roof top does not fill the view.
- Put the round Caltex star logo standing on top of the canopy's right corner, as in image 2.
- Keep the white CALTEX lettering on the fascia.
- Background: one perfectly flat uniform very light warm grey, hex #EAE6E1, no gradient, no vignette, no floor shadow outside the slab, no beige or peach tint.
Output: 2048 px on the long side, no text overlay.

Why:
- The v4 result (reference/gen_v4_try1.png) hides the columns, the fourth dispenser and the underside behind the roof top, and shows a blank white roof panel that is not in image 2.
- The v4 background is beige with saturation 0.197. The Tier 1 foreground mask in diagnose_render.py counts any pixel with saturation above 0.16 and luma below 0.94 as foreground, so it reports 97.6 percent foreground and warns that the image is not isolated.
- Image B background (#E8D6C8, saturation 0.138) passes with 38.6 percent foreground.

Known issues:
- Not yet tested with any generator.
- 20 degrees may break the isometric look; if so try 25.
- The generator may still tint the background; check with the mask test before using the image.
