---
name: figma-frame-builder
description: >-
  Build a finished visual deliverable in Figma from what the user hands you —
  raw material, a topic, a target format, or a full plan/기획안 document. Produces
  the actual frames: card news, posters, social graphics, thumbnails, slide decks,
  one-pagers. Lays out copy and visual elements to match the plan, then runs a
  dedicated final pass to fix every spot where frames, layers, or text overlap and
  hurt readability, and reports what was adjusted with verification screenshots.
  Use this whenever the user wants something designed or assembled in Figma from
  content they provide — "이 기획안대로 피그마 프레임 만들어줘", "카드뉴스 피그마로 제작해줘",
  "자료 줄 테니 피그마 작업물 만들어줘", "포스터 디자인해서 피그마에 올려줘", "슬라이드 프레임 짜줘" —
  even if they never say the word "skill" or "스킬". Defaults to the Pretendard font
  family for all text unless the user names a different font.
---

# figma-frame-builder

Turn a brief into built Figma frames. The user provides some mix of **자료 (material), 주제 (topic), 형태 (format), 기획안 (plan)**; you produce the frames in a Figma file, fix readability problems, and report back.

## 0. Prerequisites every run

- **Never call `use_figma` without loading its skill first.** Load `get_figma_skill(uri: "skill://figma/figma-use/SKILL.md")`, then pass `skillNames: "resource:figma-use"` on every `use_figma` call. Skipping this causes the font/color/page bugs listed in `references/figma-mechanics.md`.
- Read `references/figma-mechanics.md` once before the first `use_figma` call. It is the distilled set of failure modes — font loading, read-only fills, 0–1 colors, page context reset, ~10 ops per call, returning node IDs, atomic-on-error.
- **Figma MCP has a call budget.** Free/Starter plans cap `use_figma` calls (the limit resets roughly monthly; a paid 풀 seat is ~200 calls/day). Treat every call as scarce: batch operations, build a whole frame per call, verify with the inline `node.screenshot({scale: 0.4})` instead of a separate `get_screenshot` where possible, and don't re-screenshot what you already saw.

## 1. Pin down the brief

Before touching Figma, write out — for yourself, then confirm the gaps with the user:

- **형태 & 규격** — card news (1080×1080), story (1080×1920), poster (e.g. A2 @ 150dpi), slide (1920×1080), etc. If the user didn't say, propose the obvious default for the medium and note it.
- **프레임 수 & 순서** — one frame per card / slide / section. If a 기획안 lists sections, that list *is* the frame list.
- **프레임별 카피** — headline + body + labels + CTA for each frame, taken verbatim from the 기획안 or the user's material. **Do not invent factual content** (names, dates, numbers, quotes). If a slot has no confirmed content, use a clearly-marked placeholder and flag it in the report — never fabricate to fill space. Draftable *emotional/transitional* copy (mood lines, section intros) is fine to write.
- **팔레트 & 타이포** — from the 기획안 if it has one. If colors come from a named reference/brand, confirm the exact hex values with the user before applying them.
- **비주얼 요소** — lines, chips, dots, scrims, number badges, wordmark. Keep decoration quiet unless the brief asks otherwise.

If the 기획안 is thin or missing, ask one compact question covering 형태 + 주제 + 프레임 수, then proceed.

## 2. Get the Figma file

- If the user already connected a file or gave a URL, use it. Confirm it's a **design** file (`figma.com/design/...`), not FigJam or Slides.
- If there's no file, create one with `create_new_file` (or ask the user to make one and share the link).
- Run one read-only `use_figma` first to inventory the file: pages, existing frames, existing components/variables, and — critically — **which fonts are actually available** (`await figma.listAvailableFontsAsync()`). Match existing conventions where they exist.

## 3. Fonts — Pretendard by default

Default all text to **Pretendard**. But Pretendard is often not installed in a given Figma file, so never assume it:

1. From the step-2 font inventory, check for `Pretendard` (also accept `Pretendard JP`, `Pretendard Variable`).
2. If present, load the weights you need with `await figma.loadFontAsync({ family: "Pretendard", style: "<style>" })` before any text mutation. Verify the exact style strings against the inventory — guessing `"SemiBold"` vs `"Semi Bold"` is a common break.
3. **If Pretendard is absent**, fall back to `Noto Sans KR` (verified styles in most files: `Black`, `Bold`, `Medium`, `Regular`) for Korean, `Inter` for Latin. Use the fallback silently for the build, but **tell the user in the final report** that Pretendard wasn't available and what you used instead, so they can install it and re-run if they want.
4. If the user named a specific font, that overrides Pretendard — same availability check and fallback logic applies.

Map intended roles to weights: display/headline → Black or Extra Bold; subhead → Bold/Semi Bold; body → Regular; labels/caption → Medium.

## 4. Build the frames

Work one frame (or one tight group of elements) per `use_figma` call, ≤10 logical operations each.

- Position each top-level frame away from (0,0) — e.g. `x = index * (frameWidth + 100)`. Children use frame-local coordinates.
- Build order per frame: frame container → background fill → structural/decorative elements → text last (so you can place text against what's already there).
- For any container whose children are structurally related (stacked lines, a chip row, a label/value pair), use `figma.createAutoLayout()` rather than absolute x/y — it survives copy changes and is the main defense against overlap.
- Text blocks: set an explicit width (`FIXED` + `resize()`), `textAutoResize = 'HEIGHT'`, and a real `lineHeight` (`{unit:'PERCENT', value:...}` or `{unit:'PIXELS', value:...}`). Check `node.width > 0` after.
- Colors are 0–1 range. Paint `color` is `{r,g,b}` only; opacity is a sibling field on the paint. `fills`/`strokes` are read-only — clone, edit, reassign a fresh array.
- **Return every created/mutated node ID** from each call, in a structured object, so later calls (and the fix pass) can target them.
- After each frame, capture `await frame.screenshot({ scale: 0.4 })` inline to eyeball it. Don't spend a separate screenshot call unless something looks structurally wrong.

If you hit the MCP call limit mid-build: stop, write the remaining frame specs (copy + coordinates, frame by frame) to `output/<kind>/<name>_남은작업.txt` so nothing is lost, and tell the user the build is paused on the limit.

## 5. Final readability pass — the part that matters

After all frames exist, do a deliberate sweep for anything that reduces 가시성/가독성. This is a required step, not optional polish, and the user specifically wants it reported.

**Screenshot every frame** (one `use_figma` call returning `frame.screenshot({scale:0.4})` for each, or `get_screenshot` per frame). Then check each frame for:

- **Text overlapping text or shapes** — two blocks whose bounding boxes intersect; body copy running under a divider line; a caption colliding with the frame-number badge or wordmark.
- **Text over a busy image area with no scrim** — headline on top of a photo's detail region with no darkening rectangle behind it.
- **Text past the safe margin or clipped by the frame edge** — line height cutting off descenders; a long line overflowing the frame.
- **Weak contrast** — colored text on a colored background that's too close in value; check accent-on-background and text-on-background legibility.
- **Awkward wrap** — a headline breaking to leave one orphan word; a two-line block where line 2 is a single particle.
- **Elements too tight** — no breathing room between a title and body, or between stacked blocks.

**Fix** by: adjusting y-position or the auto-layout gap; reducing font size or increasing wrap width; inserting a semi-transparent scrim rectangle behind text over imagery; nudging decorative elements clear; rebalancing the line break (explicit `\n` or a wider box). Batch fixes across frames into as few `use_figma` calls as the 10-op limit allows.

**Re-screenshot the frames you changed** to confirm the fix landed and didn't create a new collision.

## 6. Export and report

- Export each final frame with `get_screenshot(nodeId, fileKey, maxDimension)` and download via `curl -sL -o "<path>" "<url>"` into the right `output/` subfolder by kind (card news → `output/card-news/`, poster/graphic → `output/design/`, slides → `output/presentations/`; make a new subfolder if none fits).
- Report to the user, in Korean:
  - The Figma file URL and the frame list.
  - Font used, and **explicitly whether Pretendard was available** or a fallback was used.
  - Every readability issue you found in step 5 and how you fixed it (frame number + before → after).
  - Any slots left as placeholders because content wasn't confirmed — call these out so the user fills them.
  - Local paths of the exported PNGs.
- Commit + push per the repo's CLAUDE.md rules (a normal build is not a structural change).

## References

- `references/figma-mechanics.md` — every `use_figma` gotcha with the fix. Read before the first build call.
