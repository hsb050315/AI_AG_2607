---
name: references
description: Given a design concept or a few design keywords, browses real design galleries (Land-book, Godly, Awwwards, SiteInspire, Behance, Dribbble, Pinterest, GDWEB, Notefolio, The Dieline, etc.) in a browser via Playwright MCP, captures full-design / full-layout screenshots of real published work that matches the concept, and saves them locally with a written selection rationale. Use this whenever the user asks "레퍼런스 찾아줘", "레퍼런스 모아줘", "참고 디자인 찾아줘", "레퍼런스 이미지 저장해줘", "이 컨셉이랑 비슷한 디자인 사례 보여줘", wants inspiration / benchmark examples before designing a website, poster, deck, card news, or brand identity, or hands over a design-concept Google Doc and asks for matching references. Also trigger when a downstream design task (웹 기획자, 웹 디자이너, canva-card-news, news-scrap-deck) needs real reference examples that don't exist yet. Don't just describe references in chat — actually browse the galleries and leave saved screenshots plus a rationale .txt.
---

# references: Real-world design reference collector

Given a design concept or a few design keywords, go find **real, finished design work** that matches it — actual landing pages, posters, decks, brand systems, editorial layouts — by browsing design galleries in a browser, and save each one as a screenshot plus a short written rationale. The point is to leave the team a small, curated board of "here is how other people solved a similar brief," not a mood collage of cropped fragments.

Two things make this skill worth triggering instead of answering in chat: the references must be **actual screenshots of real published work** (evidence, not description), and each pick needs a **documented reason it fits** so a designer can trust the board.

## Input: concept doc or keywords

The skill accepts either, and you often get both:

- **A `design-concept` Google Doc URL** (produced by the `design-concept` skill). Read it with `WebFetch`. If the doc isn't publicly shared and WebFetch returns nothing usable, ask the user to paste its 무드·톤앤매너 / 컬러 팔레트 / 주제 sections, or read it via the `gws` CLI if that's set up. Pull out: the topic, the 3~5 mood keywords, the palette (color names + HEX), and the medium if it's stated.
- **Free-text keywords in chat** (e.g. "미니멀한 핀테크 앱", "손으로 만든 느낌의 베이커리 브랜드"). Use them directly.

If both exist, the doc is the source of truth; fold any extra detail from chat into the search.

If you have almost nothing to go on (one vague word, no medium), ask one short question — what medium (웹 / 포스터 / 덱 / 패키지 / 브랜드) and is there a topic. Otherwise make a reasonable call and note the assumption in the .txt.

## Flow

### 1. Turn the concept into search inputs

Write these down before opening a browser:

- **Medium** — web page, landing page, poster / key visual, slide deck, packaging, editorial, full brand identity. This drives which galleries you use.
- **3~6 search phrases** — mix English and Korean, mix concept words with concrete descriptors: "warm handmade bakery branding", "베이커리 브랜딩", "artisan food packaging minimal". Galleries index mostly in English, so lead with English phrasings.
- **Target count** — default **5 final references** (browse ~8–12 candidates, keep the best 5). If the user gave a number, use that.

### 2. Pick galleries by medium

| Medium | Galleries (browse in this order) |
|---|---|
| Web / landing / UI | Land-book (land-book.com), Godly (godly.website), Awwwards (awwwards.com), SiteInspire (siteinspire.com), GDWEB (gdweb.co.kr — Korean market) |
| Poster / key visual / graphic | Behance (behance.net), Pinterest (pinterest.com), Savee (savee.it), Notefolio (notefolio.net — Korean) |
| Slide deck / pitch deck | Behance ("pitch deck", "presentation design"), Dribbble (dribbble.com), Pinterest |
| Packaging | Behance, Pinterest, The Dieline (thedieline.com) |
| Editorial / brand identity | Behance, Pinterest, Savee, Notefolio |

Behance, Land-book, Godly, Awwwards, SiteInspire, GDWEB, and The Dieline browse fine without login. Pinterest and Dribbble may gate deeper browsing behind a login wall — take what's visible on the search results grid and open individual pins / shots that don't require auth. **Never log in and never create an account.**

### 3. Browse with Playwright MCP

Use `mcp__playwright__browser_navigate`, `browser_snapshot`, `browser_find`, `browser_click`, `browser_take_screenshot`. Load them via ToolSearch if they're deferred.

- On a cookie / consent banner, choose the most privacy-preserving option (reject non-essential). Don't click "accept all".
- Most galleries have a search box or a URL search pattern (e.g. `behance.net/search/projects?search=<query>`, `land-book.com/?search=<query>`). Navigate, scan the grid via `browser_snapshot`, and pick candidates that genuinely match the *concept*, not just the topic — a fintech site that feels loud and playful is not a match for "절제된 신뢰감".
- Open each candidate's detail page (the real project / site page). For a live site linked from Awwwards or Land-book, you may open the actual site and screenshot the real thing.

### 4. Capture full designs, not fragments

The user wants complete layouts. For each kept reference:

- Web page: `browser_take_screenshot` with `fullPage: true` so the whole scroll is in one image.
- Poster / deck / packaging: get the full composition in frame; if the gallery shows several images for one project, screenshot the 1–2 that show the overall layout, not detail crops.
- Save via `browser_take_screenshot`'s `filename`, then move the file into place (below).
- Record for each: a short name, the gallery, the creator / studio if shown, the **detail-page URL** and the **real site URL** if there is one, and 1–2 sentences on *why it fits this concept* — which mood keyword, what about the color / type / layout.

### 5. Save

- Screenshots → `output/references/image/<topic-slug>/`, named `NN_<gallery>_<short-name>.png` (e.g. `01_landbook_oat-milk-bakery.png`). `<topic-slug>` is a short ASCII slug of the concept.
- Rationale doc → `output/references/<topic-slug>_레퍼런스.txt`, written in Korean, using the structure below.

Create the folders if they don't exist.

### 6. Write the rationale .txt

Follow this house style (it matches `output/references/gdweb/Airbnb_기업소개페이지_GDWEB_디자인레퍼런스.txt`):

```
<컨셉/주제> 디자인 레퍼런스
(수집일: YYYY-MM-DD | 입력: design-concept 문서 <URL>  또는  채팅 키워드 "...")

■ 조사 방법
- 사용한 갤러리와 검색어
- 무엇을 포함 / 제외했는지 기준 (매체, 무드 일치도, 최신성)

■ 선정 레퍼런스 (N건)
1. <이름> — <한 줄 요약>
- 갤러리 / 제작자:
- 상세페이지 URL:
- 실제 사이트 URL: (있으면)
- 매체 / 표현방법:
- 주색상: (눈에 띄면)
- 이 컨셉에 맞는 이유: <무드 키워드 연결 + 색 / 타이포 / 레이아웃 근거>
- 로컬 저장 경로: output/references/image/<slug>/NN_....png
...

■ 종합 제안
- 이 레퍼런스들에서 공통적으로 가져올 방향 (레이아웃 / 컬러·무드 / 타이포)
- 색상 확정은 사용자 최종 컨펌 필요 (design-concept 문서가 있으면 그 팔레트 우선)

■ 참고: 검토했으나 제외한 결과
- <이름> — 제외 사유
```

### 7. Report back

Give the user: the `.txt` path, the screenshot folder path and file list, and a 3–4 line summary of the direction the references point to. Report in Korean.

## Don't

- Don't hand back references you only read about — every pick needs a real screenshot you captured.
- Don't collect cropped mood fragments or single-color swatches; this skill is for complete layouts / finished pieces.
- Don't log in, sign up, or accept "agree to all" cookie banners on any gallery.
- Don't match on topic alone — a reference that's the right industry but the wrong mood is a miss; say so in the 제외 section instead of including it.
- Don't download source files (PPTX, ZIP, fonts) — screenshots only, unless the user explicitly asks and approves.
- Don't invent the palette. If there's a design-concept doc, its palette wins; otherwise leave color direction as an observation for the user to confirm.
