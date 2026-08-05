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

Some steps below also require *asking a question* rather than gating on
approval (content/style preferences). These aren't optional either — guessing
at wording, font, or color just means the generator guesses too, which
produces less predictable results than asking up front.

## The four checkpoints

Never advance past these without the user's explicit response (not silence,
not an ambiguous reply):

1. **Concept approval** — after you propose design concepts (and any matching
   brand templates), before anything is created in Canva.
2. **Candidate selection** — after `generate-design` (or a brand template
   fill) produces options, before materializing one.
3. **Draft review** — after the draft's edit link is shared, before doing
   anything further to that design (only proceed on the user's own review
   comments, e.g. "이거 별로야", "이 부분 바꿔줘", or approval).
4. **Save/export approval** — only export and file away once the user
   actually says to save/finalize (e.g. "저장해줘", "이걸로 확정").

## Step 1 — Get the topic, and find out if content already exists

Ask for a topic if none was given. Then find out whether the user already
has specific text/copy they want on the design — a script, key messages,
exact wording — rather than just a topic.

- **If they already have content**: use their wording faithfully in the
  `generate-design` query (or brand template fields) later. Don't rewrite or
  "improve" it — treat it as fixed input, the way a doc's `verbatim` mode
  treats supplied text.
- **If they don't**: tell them you'll draft the copy for each card to fit
  the topic (the default), and let them redirect if they'd rather write it
  together first. Either way, the drafted copy still goes through concept
  approval below before anything is generated.

## Step 2 — Check for a matching brand template, then derive concepts

Before inventing concepts from scratch, call `search-brand-templates` with
the topic as the query. A returned template already carries a layout someone
vetted before, so if one genuinely fits, it's worth surfacing as an option —
even though it's not the default path. Don't force a weak match just to have
one to show.

Then derive **at least 3 distinct AI-generated concepts** — vary structure,
tone, and color direction, not just wording. Present everything together in
chat as short, skimmable choices: the template(s) if any, plus the concepts.
Do not call any design-creation tool yet.

If the user picks a brand template, skip Steps 5-6 below and follow **Step
5a** instead. Otherwise continue with the concept path as normal.

## Step 3 — Confirm the artifact type

Once a concept (or template) is picked, confirm what kind of artifact the
user wants (card news, poster, presentation, single social post, etc.) if it
isn't already obvious from their request. This decides the `design_type`
passed to `generate-design` — multi-card "card news" maps to
`design_type: presentation` since that's the only type supporting multiple
pages/slides in one design.

If the user wants the design to follow an existing brand kit, ask before
calling `list-brand-kits` — don't assume. Only pass `brand_kit_id` to
`generate-design` after they've picked one.

## Step 4 — Ask about style before generating

Before calling `generate-design`, ask what the user wants for:

- **Font** — a general feel is enough ("굵은 산세리프", "손글씨 느낌", etc.);
  Canva's generator takes style description, not an exact font name.
- **Color palette** — specific colors, a mood, or a brand color to match.
- **Image/layout placement** — photo-heavy vs. typography-heavy, where a
  logo or hero image sits, one shared image vs. per-card illustration.

If the user has no opinion on one of these, say so and pick something that
fits the approved concept rather than leaving it unspecified.

## Step 5 — Generate candidates

Call `generate-design` with a detailed query built from everything gathered
so far: the approved concept, page count and per-page content (the user's
own copy if they supplied it in Step 1), color palette, and font/typography
style from Step 4.

**Output language defaults to Korean.** Switch to whatever language the user
asks for instead, and say so explicitly in the query either way — the tool
has no language default of its own, so an unstated language just means
whatever it happens to guess.

**Known constraint: candidate count is fixed.** `generate-design` does not
expose a parameter for how many candidates to return — in testing it always
returned exactly 4, regardless of how the request was phrased. If the user
asks for a specific number of candidates, tell them this upfront rather than
quietly returning whatever count the tool gives — they should know it's a
tool limitation, not something you chose to ignore.

If, while building this query, a different Canva MCP tool looks like a
better fit for what the user is asking than the ones this skill currently
names, don't just switch silently — propose it, use it once they agree, and
see "Keep this skill current" below.

Present the candidate thumbnails/links and **wait for the user to pick one**
(checkpoint 2).

## Step 5a — Using a brand template instead

If the user picked a brand template in Step 2:

1. Call `get-brand-template-dataset` to see what fields the template
   expects (title, body text, images, etc.).
2. Fill those fields with the user's supplied content (Step 1) or copy you
   draft to fit the topic, and **confirm the filled-in copy with the user
   before creating** — a template's fields are fixed, and there's no
   "regenerate 4 candidates" step to fall back on here if the wording is
   wrong.
3. Call `create-design-from-brand-template` to produce the design.
4. Skip ahead to Step 7 (aspect ratio) — a template-based design has no
   separate candidate-selection stage.

## Step 6 — Materialize the chosen candidate

Call `create-design-from-candidate` with the chosen `candidate_id` and the
`job_id` from the generation call. This is the point where the design
actually becomes a real, editable Canva item — everything before this was
still just a preview.

## Step 7 — Aspect ratio (only if requested)

**Known constraint: ratio can't be set at generation time.**
`generate-design` has no aspect-ratio parameter, so every candidate comes out
at the design type's default (e.g. 16:9 for presentations). A non-default
ratio can only be applied afterward, via `resize-design` on the materialized
design — presets only cover `presentation`/`whiteboard`, so anything else
(4:3, square, etc.) needs `type: custom` with explicit `width`/`height` in
pixels. Explain this ordering to the user if they expect the ratio to show up
in the candidates — don't claim to have applied it earlier than you could.

## Step 8 — Share the draft and wait for review

Send the design's `edit_url` to the user as the confirmation link
(checkpoint 3). Don't touch the design further until they respond with
feedback or approval — this is their first look at an actual editable Canva
file, not a static preview.

## Step 9 — External reference images (only if requested)

Canva MCP has no web or stock-photo search tool — `get-assets` only reads
what's already uploaded to the account. If the user wants a real photo, logo,
or other reference image inserted:

1. Use `WebSearch`/`WebFetch` to find a real public source (official site,
   Wikipedia, etc.) — never invent or guess a URL.
2. Verify the candidate URL actually resolves to image content (e.g. a HEAD
   request) before using it — a webpage link is not the same as a direct
   image file link, and `upload-asset-from-url` needs the latter.
3. This skill's designs are for non-commercial use by default, so a
   copyrighted image found online is fine to fetch and use if the user wants
   it inserted — don't withhold it just because it's copyrighted. If the
   request actually looks commercial (a business logo, a product for sale,
   an ad), check with the user first — that changes the copyright exposure
   the non-commercial default assumes away.
4. Upload the chosen image with `upload-asset-from-url`, then pass its
   returned asset id via `generate-design`'s `asset_ids` parameter (images
   need to be sourced *before* generation, not patched into an existing
   design).
5. If no reliable direct image URL can be found at all, don't just drop the
   request — use a substitute instead: either let `generate-design` produce
   its own illustrative artwork for that spot (its default behavior when no
   `asset_ids` are supplied) or generate/describe a stand-in image that fits
   the mood. Tell the user plainly that the real image couldn't be sourced
   and that a substitute was used instead, so they know what's actually in
   the design. Never fill the gap with a fabricated or unverified link.

## Step 10 — Save/export (checkpoint 4)

Only proceed once the user explicitly approves saving or finalizing. Then:

1. Call `get-export-formats` for the design first — never assume a format is
   supported, and never guess it based on what the user asked for.
2. Call `export-design` with `format.type: "png"` (this skill's default
   output extension) unless the user asked for a different format.

## Step 11 — Organize into Canva folders

Keep finished work under a predictable structure: a top-level folder named
`canva`, with a subfolder per topic underneath it.

1. `search-folders` for a folder named `canva`; only `create-folder` it (at
   `root`) if the search comes back empty — don't create a duplicate.
2. Same check-then-create pattern for the topic subfolder inside it.
3. `move-item-to-folder` the finalized design into the topic subfolder.

## Step 12 — Report results

Give the user the PNG export link(s) and the Canva folder link so they can
find the design again without re-asking.

## Keep this skill current

This skill is a snapshot of the best known workflow, not a fixed spec. Two
things should feed back into it rather than staying one-off:

- **A better tool appears.** Canva MCP's tool set can change over time. If
  you notice a tool that fits a step here better than the one currently
  named — faster, more direct, less error-prone — propose the switch to the
  user in the moment, use it once they agree, and then edit this file so the
  new tool is the named default going forward. Otherwise the same discovery
  has to happen again next time.
- **A better workflow appears.** If an actual run reveals a smoother order
  of operations, a question that should be asked earlier, or a step that
  turned out to be unnecessary, ask the user whether to adopt it — and if
  they agree, edit this SKILL.md to reflect it before finishing up. A good
  discovery that only lives in one conversation is lost the next time this
  skill runs.

## The cross-cutting rule

Every "known constraint" above exists because the tool genuinely can't do
that thing yet — not because it's being deprioritized. When you hit one of
these, or any other gap between what the user asked for and what's actually
possible (a format that isn't supported, an image that can't be sourced, a
size that doesn't fit a preset, content a template's fields can't hold),
**stop, explain the specific gap, and get the user's approval on the
alternative before proceeding.** Silently substituting something
close-enough, or quietly dropping part of the request, is worse than asking
— the user is working in their real Canva account and should know what
actually happened to it.

## Edge cases

- **User changes the concept or artifact type mid-flow**: treat it as
  restarting from Step 1/2/3 for that part — don't try to patch an
  already-generated candidate into matching a different concept.
- **User asks to skip a checkpoint** ("그냥 다 진행해줘"): this authorizes
  moving through the *remaining* steps without asking again at each one, but
  the save/export checkpoint (Step 10) is a distinct, explicit trigger
  ("저장해줘"/"승인"/equivalent) — don't treat a general "proceed with the
  rest" as also covering that unless the user's phrasing clearly includes it.
- **Multiple designs from one topic** (e.g. a card news plus a matching
  poster): run the concept → candidate → draft → save loop separately for
  each artifact type; don't conflate them into one `generate-design` call.
- **A brand template matches but the user's supplied content doesn't fit its
  fields** (too long, wrong number of sections): say so and offer the
  AI-generated-concept path instead, rather than truncating their content to
  force it into the template.
