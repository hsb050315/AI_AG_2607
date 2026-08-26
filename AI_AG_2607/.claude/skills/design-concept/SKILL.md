---
name: design-concept
description: Takes a topic (brand, product, service, campaign, event, content series) and does two things in sequence — deep web research on it, then derives a complete visual design concept from that research: 3~5 mood / tone-and-manner keywords, a color palette with HEX codes and usage guidance, and typography (Korean + Latin font pairings). The deliverable is a structured Google Docs document created in the user's real Google Drive. Use this skill whenever the user names a topic and asks to "디자인 컨셉 잡아줘", "디자인 방향 정해줘", "컨셉 잡아줘", "무드 잡아줘", "톤앤매너 정리해줘", "컬러 팔레트 뽑아줘", "브랜드 컨셉 만들어줘", "조사해서 디자인 컨셉까지 잡아줘", "design concept", or wants a visual direction established before building a website, slide deck, card news, blog, or Canva design. Also trigger when a downstream design/planning task (웹 기획자, 웹 디자이너, canva-card-news, news-scrap-deck) needs a design direction that does not exist yet. Don't answer the concept inline as chat prose — run the research and produce the Google Doc.
---

# design-concept: Research-driven visual design concept

Take one topic and carry it all the way from "I don't know anything about this yet" to "here is a documented visual direction anyone on the team can build against." Two phases, in order:

1. **Research** the topic properly (web research, not prior knowledge).
2. **Derive** a design concept from what the research actually says — mood/tone keywords, color palette, typography — and write it up as a Google Docs document in the user's Drive.

The concept is medium-agnostic on purpose. It should be usable whether the output later becomes a website, a deck, card news, or a Canva design, so keep recommendations at the level of direction (palette, type, mood) rather than layout or component specs.

## Flow

### 1. Scope the topic

If the topic is clear enough from the request, start. Only ask a short clarifying question when the subject is genuinely ambiguous (e.g. a brand name that could be several companies). If it's vague but you can make a reasonable call, note the assumption in the document's "근거 및 출처" section and proceed.

Worth pinning down quickly if the user hasn't said: is there an intended audience, a market/region, or an emotional goal they already have in mind? These sharpen the concept but aren't blockers.

### 2. Deep research

Prefer to spawn the **조사관 subagent** for this — it's built for well-sourced Korean research and keeps the research context out of the main thread. Give it a focused brief covering:

- **분야 개요** — what this topic/industry actually is, its current state
- **타깃** — who the audience or customer is; their expectations, age band, context of use
- **경쟁·유사 사례의 비주얼 경향** — how comparable brands/products present themselves (color, type, imagery mood); what's the category norm and what breaks from it
- **색·타이포 관습과 연상** — colors and type styles conventionally associated with this field, and the emotions/associations they carry (culture-specific where relevant, e.g. Korean market)
- **전달하려는 감정·가치** — what feeling or brand values this topic should communicate
- **최근 트렌드** — recent shifts in how this space is designed

If spawning a subagent isn't available in the current context, do the research directly with WebSearch/WebFetch against the same brief. Either way: cross-check anything specific against 2+ sources, keep the source URLs, and record today's date as the research date.

### 3. Derive the concept

Synthesize the research into three deliverables. Every choice should trace back to something the research said — if you can't explain *why* a color or font fits from the research, it's a guess, and a guess belongs in "근거 및 출처" as an open question, not in the palette.

**무드 · 톤앤매너 키워드 (3~5개)**
- 3 to 5 concept keywords that capture the intended feeling (e.g. "절제된 신뢰감", "따뜻한 실용주의", "선명한 에너지").
- For each: one line on what it means here, and how it should show up visually (weight, contrast, saturation, spacing feel).
- One "컨셉 스테이트먼트" sentence that ties them together — this is the north star for anyone building against the concept.

**컬러 팔레트**
- Cover these roles: 주조색(dominant), 보조색(secondary, 1~2), 강조색(accent), 중립색(neutral/background/text).
- Each color needs: 색상명, 역할, HEX, 사용처(where it's used), 선정 근거(why — tied to research).
- Give a rough usage ratio (e.g. 주조 60 / 보조 25 / 강조 10 / 중립은 배경·텍스트).
- Check that 강조색 on 중립 배경, and text color on background, have enough contrast to be legible.

**타이포그래피**
- Recommend a 제목용 pairing and a 본문용 pairing, each with a **한글 폰트 + 영문 폰트** (Korean text usually needs a different family than Latin).
- Prefer widely available / free fonts (Pretendard, Noto Sans KR, Nanum, Gmarket Sans, SUIT for Korean; Inter, Roboto, Source Serif, etc. for Latin) unless the concept clearly calls for something distinctive.
- For each: why it fits the mood (letterform character, weight range), and a fallback font.

### 4. Present the concept to the user before writing the doc

Show the palette (with HEX), the keywords, and the font picks in chat, and ask for a yes or tweaks. Applying a visual direction the user hasn't seen — especially colors — tends to miss; a 30-second check here saves a rebuild. Adjust on their feedback before moving on.

### 5. Confirm the Drive folder — every time

This step is never skipped, no matter how obvious the destination seems.

- Call `find_folders(name_query)` with a folder name the user mentioned or a keyword from the topic, show the candidates, and confirm which one.
- If the user named no folder, ask: "어느 폴더에 저장할까요? (비워두면 내 드라이브 최상위에 만듭니다)"
- No folder → `create_document(title, folder_id=None)` (My Drive root).
- `create_document` fails with `insufficientParentPermissions` → that folder isn't owned by the user (view-only share). Tell them, and re-ask for a folder or the root.

### 6. Assemble the Google Doc

Reuse the `gws-doc` skill's builder — don't hand-roll `gws` calls or Docs API JSON. The table/index math is already handled there.

```python
import sys, glob
# Locate the builder (repo layout: .claude/skills/gws-doc/scripts/gws_docs_builder.py)
builder_dir = glob.glob("**/skills/gws-doc/scripts", recursive=True)[0]
sys.path.insert(0, builder_dir)
from gws_docs_builder import (
    find_folders, create_document, get_share_link,
    add_title, add_subtitle, add_heading, add_paragraph,
    add_emphasized_paragraph, add_bullet_list, add_table,
)

folders = find_folders("브랜드")          # after user confirms the folder
doc_id = create_document("OO 디자인 컨셉", folder_id=folders[0]["id"])  # or folder_id=None
add_title(doc_id, "OO 디자인 컨셉")
add_subtitle(doc_id, "문서구분: 디자인 컨셉 정의서 | 작성일자: 2026년 8월 26일")
# ... add_heading / add_paragraph / add_table / add_bullet_list top-to-bottom ...
print(get_share_link(doc_id))
```

All `add_*` calls append to the end of the document, so call them in the order the reader should see them.

### 7. Report back

The final deliverable is the `get_share_link(doc_id)` URL. Give the user the link, plus a 2~3 line summary of the concept direction. Not a local file path — none exists.

## Document structure

Use this shape. Adjust heading wording to the topic, but keep the six sections.

```
[주제] 디자인 컨셉            (add_title)
문서구분: 디자인 컨셉 정의서 | 작성일자: YYYY년 M월 D일   (add_subtitle)

## 1. 개요                    (add_heading level=1)
   주제, 이 컨셉의 목적, 적용 대상(미정이면 "범용 — 웹/인쇄/영상 공통"), 조사 기준일

## 2. 리서치 요약             (add_heading level=1)
   컨셉 도출에 직접 쓰인 것만: 타깃, 경쟁 비주얼 경향, 색·타이포 관습, 전달할 감정·가치
   (배경 설명은 문단, 나열은 add_bullet_list)

## 3. 무드 · 톤앤매너         (add_heading level=1)
   키워드 3~5개와 각 의미·시각적 방향 (add_bullet_list 또는 add_table)
   컨셉 스테이트먼트 한 문장 (add_emphasized_paragraph)

## 4. 컬러 팔레트             (add_heading level=1)
   add_table: 색상명 | 역할 | HEX | 사용처 | 선정 근거
   사용 비율 가이드 (add_paragraph 또는 add_bullet_list)

## 5. 타이포그래피            (add_heading level=1)
   add_table: 용도(제목/본문) | 한글 폰트 | 영문 폰트 | 굵기 | 근거
   대체 폰트·사용 규칙 (add_bullet_list)

## 6. 근거 및 출처            (add_heading level=1)
   조사 출처 URL 목록, 조사 시점, 가정한 내용, 확인하지 못한 부분
```

## Handling Korean text on Windows

Most of this document is Korean, so how you run the assembly code matters:

- The **Bash** tool (Git Bash/MSYS) corrupts non-ASCII argument strings before Python even starts. If you must run inline `python -c "..."` with Korean in it, use the **PowerShell** tool instead.
- Safest: use the **Write** tool to create a `.py` file with the Korean literals (title, body, table contents) inside it, and pass only its ASCII path to the shell. This is also easier to manage as the document grows.

## Don'ts

- Don't fill the concept from prior knowledge — it must come from actual research on this specific topic.
- Don't finalize colors without showing them to the user first.
- Don't skip the Drive-folder confirmation.
- Don't make design choices you can't justify from the research — put uncertainty in "근거 및 출처" instead of inventing a rationale.
- Don't go past direction into layout, grid, component, or imagery specs — that's the downstream planner/designer's job. This skill sets palette, type, and mood.
- Don't hand-roll `gws` low-level commands or Docs API JSON — use `gws_docs_builder.py`.
- Report back in Korean.
