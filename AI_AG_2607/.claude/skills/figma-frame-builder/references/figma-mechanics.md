# figma-mechanics — `use_figma` failure modes and fixes

Read this once before the first `use_figma` call in a build. These are the mistakes that cost a retry (and retries cost scarce MCP calls). The authoritative source is the `figma-use` skill's own `references/`; this file is the short version tuned for frame-building.

## Execution model

- Code is auto-wrapped in an async context. Write **plain JS with top-level `await` and `return`**. Do NOT wrap in `(async () => {})()`. Do NOT call `figma.closePlugin()`.
- `figma.notify()` throws `"not implemented"` — never use it.
- `console.log()` output is **not** returned. The agent sees only what you `return`. Return a structured object.
- **On error the script is atomic** — nothing executed, file unchanged. STOP, read the error, fix, then retry. Do not blind-retry.
- **~10 logical operations per call.** Creating a node + setting its props + parenting it ≈ one op. Split bigger work across calls.

## Colors

- 0–1 range, not 0–255. `{ r: 0x4F/255, g: 0xA3/255, b: 0xC7/255 }`.
- Paint `color` takes `{r,g,b}` **only** — no alpha field. Opacity is a sibling on the paint: `{ type:'SOLID', color:{...}, opacity:0.9 }`.
- Gradient stop alpha *does* go inside the stop color as `{r,g,b,a}`.
- `fills` and `strokes` are **read-only arrays**. Clone → modify → reassign a fresh array literal:
  ```js
  const f = node.fills.map(p => ({...p}));
  f[0] = { ...f[0], color: aqua };
  node.fills = f;
  ```
- Partial-range text color: `node.setRangeFills(start, end, [{ type:'SOLID', color }])`.

## Fonts — the canonical text recipe

Every text mutation: **load font → `await` → mutate → return node IDs.** Skipping the load throws `Cannot write to node with unloaded font "<family> <style>"`.

```js
for (const s of ["Regular","Medium","Bold","Black"]) {
  await figma.loadFontAsync({ family: "Noto Sans KR", style: s });
}
```

- Verify style strings with `await figma.listAvailableFontsAsync()` — do not guess. `"Semi Bold"` and `"Extra Bold"` (Inter) have a space; `"SemiBold"` will fail.
- When editing existing text, load its *current* fonts via `node.getStyledTextSegments(['fontName'])`, not a hardcoded default.
- Known-good in most files: Noto Sans KR → `Black`, `Bold`, `Medium`, `Regular`. Inter → `Regular`, `Medium`, `Semi Bold`, `Bold`, `Extra Bold`.
- Pretendard is frequently **not present**. Check the font inventory first; fall back to Noto Sans KR + tell the user.

## Text layout

- Wrapping text: explicit width (`node.resize(w, h)` then it's `FIXED`) + `node.textAutoResize = 'HEIGHT'` + real `lineHeight` as `{unit, value}`. A bare number fails.
- `FILL` sizing alone under default `WIDTH_AND_HEIGHT` collapses the node to ~0 width. After setup, assert `node.width > 0`.
- `resize()` resets sizing modes to `FIXED` — call it **before** setting `HUG`/`FILL`.
- `layoutSizingHorizontal/Vertical` = `'FIXED' | 'HUG' | 'FILL'` and only works once the node is a child of an auto-layout frame (append first, then set). `primaryAxisSizingMode/counterAxisSizingMode` = `'FIXED' | 'AUTO'` — different enum, don't cross them.

## Auto-layout

- Use `figma.createAutoLayout('VERTICAL', { itemSpacing: 24, name: 'col' })` for any group of structurally-related children. Children can use `layoutSizingHorizontal = 'FILL'` right after `appendChild`.
- Absolute x/y is for where a container sits on the canvas; auto-layout is for how children relate inside it. Both, not either.

## Positioning

- New top-level nodes default to (0,0) and stack on existing content. Scan `figma.currentPage.children` and place new frames clear — e.g. to the right of the rightmost node, or `x = index * (w + gap)`.
- Frame children are positioned in **frame-local** coordinates.

## Pages

- `figma.currentPage` resets to the first page at the start of **every** `use_figma` call. Re-`await figma.setCurrentPageAsync(page)` at the top of each call that targets a non-default page.
- The sync setter `figma.currentPage = page` throws. Always the async method.
- Call `setCurrentPageAsync` at most once per script. For multi-page work, fan out into N parallel `use_figma` calls (one message, N tool blocks).

## Return values

- **Every script that creates or mutates canvas nodes MUST `return` all affected node IDs**, structured: `return { createdNodeIds: [...], mutatedNodeIds: [...], shot: await frame.screenshot({scale:0.4}) }`.
- You need these IDs for the readability fix pass and for any later call.

## Verification

- `await node.screenshot({ scale: 0.4 })` returns the image inline in the same call — cheaper than a separate `get_screenshot`. Use it to eyeball each frame as you build.
- `get_metadata` for structure (counts, hierarchy, positions). `get_screenshot` for a full-res export at the end.
- `get_screenshot(nodeId, fileKey, maxDimension)` returns a short-lived `image_url`; download immediately with `curl -sL -o "<path>" "<url>"`.

## Forbidden in `use_figma`

`loadAllPagesAsync`, `setPluginData` / `getPluginData` (keep state in `return` values and node `description`s instead), `createImageAsync`. `figma.createPage()` only works in design files.
