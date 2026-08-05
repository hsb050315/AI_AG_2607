---
name: canva-card-news
description: Runs a checkpoint-driven Canva design workflow using the Canva MCP tools — from a topic to a finished, exported design saved and organized in the user's Canva account. Use this whenever the user asks to create a "카드뉴스" (card news), poster, presentation, social post, or any other visual design in Canva, especially when they name a topic (e.g. "OO 소개하는 카드뉴스 만들어줘", "Canva로 포스터 제작해줘", "이 주제로 디자인 뽑아줘"). Also use it if the user is already mid-conversation about a Canva design and asks to pick a candidate, resize, export, or save/organize it. Trigger even if the user doesn't say "skill" or name Canva explicitly, as long as they want a topic turned into a real design artifact rather than just advice about design.
---

# Canva Guided Design Workflow (Card News & More)

This skill turns a topic into a finished design in the user's real Canva
account, through the Canva MCP tools. Because every generation, resize, export,
and folder change is a real, visible action in a third-party account (not a
local file the user can just discard), the workflow is built around explicit
checkpoints rather than running straight through. Skipping a checkpoint to
"save time" produces designs the user didn't actually approve — slower to fix
than the checkpoint itself would have cost.

## The four checkpoints

Never advance past these without the user's explicit response (not silence,
not an ambiguous reply):

1. **Concept approval** — after you propose design concepts, before anything
   is created in Canva.
2. **Candidate selection** — after `generate-design` returns candidates,
   before `create-design-from-candidate` materializes one.
3. **Draft review** — after the draft's edit link is shared, before doing
   anything further to that design (only proceed on the user's own review
   comments, e.g. "이거 별로야", "이 부분 바꿔줘", or approval).
4. **Save/export approval** — only export and file away once the user
   actually says to save/finalize (e.g. "저장해줘", "이걸로 확정").

## Step 1 — Get the topic and derive concepts

Ask for a topic if none was given. Then derive **at least 3 distinct
concepts** — vary structure, tone, and color direction, not just wording.
Present them in chat as short, skimmable options (what pages/cards it has,
the visual mood, who it's for). Do not call any Canva tool yet — concepts are
free to iterate on before anything is created.

## Step 2 — Confirm the artifact type

Once a concept is picked, confirm what kind of artifact the user wants (card
news, poster, presentation, single social post, etc.) if it isn't already
obvious from their request. This decides the `design_type` passed to
`generate-design` — multi-card "card news" maps to `design_type: presentation`
since that's the only type supporting multiple pages/slides in one design.

If the user wants the design to follow an existing brand kit, ask before
calling `list-brand-kits` — don't assume. Only pass `brand_kit_id` to
`generate-design` after they've picked one.

## Step 3 — Generate candidates

Call `generate-design` with a detailed query describing the approved concept:
page count, what goes on each page, color palette, and font/typography style.
Written language should match the user's design language (usually Korean for
Korean topics) — say so explicitly in the query, since the tool doesn't
default to any particular language.

**Known constraint: candidate count is fixed.** `generate-design` does not
expose a parameter for how many candidates to return — in testing it always
returned exactly 4, regardless of how the request was phrased. If the user
asks for a specific number of candidates, tell them this upfront rather than
quietly returning whatever count the tool gives — they should know it's a
tool limitation, not something you chose to ignore.

Present the candidate thumbnails/links and **wait for the user to pick one**
(checkpoint 2).

## Step 4 — Materialize the chosen candidate

Call `create-design-from-candidate` with the chosen `candidate_id` and the
`job_id` from the generation call. This is the point where the design
actually becomes a real, editable Canva item — everything before this was
still just a preview.

## Step 5 — Aspect ratio (only if requested)

**Known constraint: ratio can't be set at generation time.**
`generate-design` has no aspect-ratio parameter, so every candidate comes out
at the design type's default (e.g. 16:9 for presentations). A non-default
ratio can only be applied afterward, via `resize-design` on the materialized
design — presets only cover `presentation`/`whiteboard`, so anything else
(4:3, square, etc.) needs `type: custom` with explicit `width`/`height` in
pixels. Explain this ordering to the user if they expect the ratio to show up
in the candidates — don't claim to have applied it earlier than you could.

## Step 6 — Share the draft and wait for review

Send the design's `edit_url` to the user as the confirmation link
(checkpoint 3). Don't touch the design further until they respond with
feedback or approval — this is their first look at an actual editable Canva
file, not a static preview.

## Step 7 — External reference images (only if requested)

Canva MCP has no web or stock-photo search tool — `get-assets` only reads
what's already uploaded to the account. If the user wants a real photo, logo,
or other reference image inserted:

1. Use `WebSearch`/`WebFetch` to find a real public source (official site,
   Wikipedia, etc.) — never invent or guess a URL.
2. Verify the candidate URL actually resolves to image content (e.g. a HEAD
   request) before using it — a webpage link is not the same as a direct
   image file link, and `upload-asset-from-url` needs the latter.
3. Upload it with `upload-asset-from-url`, then pass its returned asset id
   via `generate-design`'s `asset_ids` parameter (this means images need to
   be sourced *before* generation, not patched into an existing design).
4. If no reliable direct image URL can be found, skip it and tell the user
   plainly that it was skipped and why. Don't silently drop the request, and
   don't substitute a fabricated or unverified link to satisfy it.

## Step 8 — Save/export (checkpoint 4)

Only proceed once the user explicitly approves saving or finalizing. Then:

1. Call `get-export-formats` for the design first — never assume a format is
   supported, and never guess it based on what the user asked for.
2. Call `export-design` with `format.type: "png"` (this skill's default
   output extension) unless the user asked for a different format.

## Step 9 — Organize into Canva folders

Keep finished work under a predictable structure: a top-level folder named
`canva`, with a subfolder per topic underneath it.

1. `search-folders` for a folder named `canva`; only `create-folder` it (at
   `root`) if the search comes back empty — don't create a duplicate.
2. Same check-then-create pattern for the topic subfolder inside it.
3. `move-item-to-folder` the finalized design into the topic subfolder.

## Step 10 — Report results

Give the user the PNG export link(s) and the Canva folder link so they can
find the design again without re-asking.

## The cross-cutting rule

Every "known constraint" above exists because the tool genuinely can't do
that thing yet — not because it's being deprioritized. When you hit one of
these, or any other gap between what the user asked for and what's actually
possible (a format that isn't supported, an image that can't be sourced, a
size that doesn't fit a preset), **stop, explain the specific gap, and get
the user's approval on the alternative before proceeding.** Silently
substituting something close-enough, or quietly dropping part of the request,
is worse than asking — the user is working in their real Canva account and
should know what actually happened to it.

## Edge cases

- **User changes the concept or artifact type mid-flow**: treat it as
  restarting from Step 1/2 for that part — don't try to patch an
  already-generated candidate into matching a different concept.
- **User asks to skip a checkpoint** ("그냥 다 진행해줘"): this authorizes
  moving through the *remaining* steps without asking again at each one, but
  the save/export checkpoint (Step 8) is a distinct, explicit trigger
  ("저장해줘"/"승인"/equivalent) — don't treat a general "proceed with the
  rest" as also covering that unless the user's phrasing clearly includes it.
- **Multiple designs from one topic** (e.g. a card news plus a matching
  poster): run the concept → candidate → draft → save loop separately for
  each artifact type; don't conflate them into one `generate-design` call.
