---
name: news-scrap-deck
description: Runs Playwright MCP against real news sites — article search/discovery is restricted to Naver News only, though any specific article URL the user provides directly is still scraped regardless of site — to find relevant articles, scrapes them as full-page screenshots, and turns the scraped content into both a python-docx Word report (.docx) and a python-pptx presentation (.pptx). Use this whenever the user asks things like "기사 스크랩해서 보고서/발표자료 만들어줘" (scrape articles and make a report/deck), "OO 관련 뉴스 모아서 PPT 만들어줘" (collect news about OO into a PPT), "이 기사들로 발표자료 만들어줘" (make a deck from these articles), "뉴스 스크랩하고 정리해줘" (scrap news and organize it), "기사 캡처해서 문서로 정리해줘" (capture articles into a document), or "네이버 뉴스에서 OO 찾아서 슬라이드로 만들어줘" (find OO on Naver News and make slides). This is not a plain text-summary task — it requires actually opening article pages in a browser to leave screenshot evidence, and producing both a report and a presentation as the deliverable. Trigger proactively whenever both artifacts (report + deck) are wanted from real, browser-scraped news articles.
---

# News Scrap → Report + Presentation

Takes a topic (or a list of article URLs) and carries it through (1) real article scraping via Playwright MCP (screenshots) → (2) analysis of the scraped content → (3) `.docx` report assembly → (4) `.pptx` presentation assembly. Don't write document/deck assembly code from scratch each time — reuse the bundled script and a sibling skill's script.

## Overall flow

1. **Confirm scope** — If the topic (or URL list) and the number of articles to scrape are already clear from the request, proceed immediately. If the article count isn't specified, default to 3-5 (5 for a broad topic, 3 for a narrow one). Article search/discovery is always restricted to Naver News only — never search or browse other news sites (Google News, Daum, publisher homepages, etc.) to find candidate articles. If the user gave specific article URLs directly, skip the search step and scrape those URLs right away, regardless of which site they're on.

2. **Find and scrape articles with Playwright MCP** — Use the Playwright MCP tools (`mcp__playwright__browser_navigate`, `browser_find`, `browser_snapshot`, `browser_click`, `browser_take_screenshot`, etc.). If they're deferred, load them via ToolSearch first.
   - **Naver News search**: navigate to `https://search.naver.com/search.naver?where=news&query=<query>`, or use a Naver News section (`https://news.naver.com/section/<sid>`) or the classic publisher list (`https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=<sid>`) to find relevant articles. Do not use any other search engine or news site (Google News, Daum News, a publisher's own site, etc.) to find candidate articles — Naver News is the only source for discovery.
     - Section codes for reference: Politics 100 / Economy 101 / Society 102 / Life&Culture 103 / World 104 / IT&Science 105.
     - The "기사 더보기" (load more) button on `news.naver.com/section/<sid>` pages may not actually add new articles — it can cycle within a fixed pool (roughly 50-60 items). If you need real page numbers, use the classic list page `news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=<sid>`, which has genuine numbered pagination (1, 2, 3, ...).
   - **Arbitrary URLs**: if the user gave a specific news site or article URL, navigate there directly regardless of whether it's Naver.
   - For each article:
     1. Navigate to the article page.
     2. Call `browser_take_screenshot` with `fullPage: true` to capture the whole page. Save it per the "Output location" rules below.
     3. Read the article body text (via `browser_snapshot` or extracted page text) — this is what the analysis step summarizes. The screenshot is evidence, not the text-extraction mechanism; base the actual summary on the text you read from the page.
     4. Record the article's title, publisher, URL, and screenshot path — needed for assembling the report/deck.

3. **Analyze** — Synthesize the scraped articles into:
   - A per-article key summary (2-4 sentences or 3-5 bullets)
   - Common trends/issues across the articles, and any conflicting viewpoints if present
   - Conclusions and implications

4. **Assemble the `.docx` report** — Import and use `scripts/docx_generator.py` from the sibling skill `docx-research-report` as-is (it's reachable via a relative path since both live under the same `.claude/skills/`). Don't write low-level python-docx code from scratch.

   ```python
   import sys
   sys.path.insert(0, "<project root>/.claude/skills/docx-research-report/scripts")
   from docx_generator import (
       new_document, add_title, add_heading, add_paragraph,
       add_bullet_list, add_table, add_image, add_divider,
       set_margins, add_page_number_footer, save,
   )

   doc = new_document(main_color="1F4E79")
   set_margins(doc)
   add_page_number_footer(doc)
   add_title(doc, "OO News Scrap Report", subtitle=f"Date: {today} | {N} articles scraped")

   add_heading(doc, "1. Overview", level=1)
   add_paragraph(doc, "...")

   add_heading(doc, "2. Per-article summaries", level=1)
   # For each article: subheading (add_heading level=2) -> summary (add_paragraph/add_bullet_list) -> screenshot (add_image) -> source (add_paragraph)

   add_heading(doc, "3. Synthesis / insights", level=1)
   add_paragraph(doc, "...")

   add_heading(doc, "4. Conclusion and implications", level=1)
   add_paragraph(doc, "...")

   save(doc, "output/reports/OO_뉴스_스크랩_보고서.docx")
   ```

   As with the docx-research-report skill, also produce a plain-text `.txt` with the same basename and equivalent content (tables/images become captions and paths in the text version).

5. **Assemble the `.pptx` deck** — Use `scripts/pptx_generator.py` bundled with this skill. The target is a simple template (title/summary bullets + screenshot thumbnail) — don't try to add charts or elaborate custom layouts.

   ```python
   import sys
   sys.path.insert(0, "<this skill folder>/scripts")
   from pptx_generator import (
       new_presentation, add_title_slide, add_section_slide,
       add_bullet_slide, add_image_bullet_slide, add_closing_slide, save,
   )

   prs = new_presentation(main_color="1F4E79")
   add_title_slide(prs, "OO News Scrap Briefing", subtitle=f"Date: {today}")

   add_section_slide(prs, "Per-article summaries")
   # One slide per article: add_image_bullet_slide(prs, article_title, [key summary bullets...], screenshot_path, source="Source: publisher · date")

   add_section_slide(prs, "Synthesis / insights")
   add_bullet_slide(prs, "Conclusion", ["trend/implication bullets..."])

   add_closing_slide(prs)
   save(prs, "output/presentations/OO_뉴스_스크랩_브리핑.pptx")
   ```

   Match `main_color` to the `.docx` report's color so both deliverables share the same visual tone.

6. **Report results** — Summarize the saved screenshot paths and the absolute paths of the `.docx`/`.txt`/`.pptx` files for the user.

## Output location

Follow this project's (AI_AG_2607) `output/` folder conventions:

- Screenshots (captured via Playwright MCP) → `output/screenshots/`
- `.docx`/`.txt` report → `output/reports/`
- `.pptx` presentation → `output/presentations/` (create it if it doesn't exist — a pptx doesn't fit any existing subfolder, so it's a new kind of artifact)

If this skill is used in a project without an `output/` folder yet, create the same subfolder structure there.

## File naming

- Screenshots: `<article title or publisher+number>.png` (replace filesystem-unsafe characters with underscores)
- Report/deck: `<topic (spaces as underscores)>_뉴스_스크랩_보고서.docx` / same-basename `.txt` / `<topic>_뉴스_스크랩_브리핑.pptx`

## Don't

- Don't summarize articles from search snippets or prior knowledge without a screenshot — the whole point of this skill is leaving real, browser-scraped evidence.
- Don't stop after producing only one of the two deliverables — unless the user explicitly asked for just one, make both the report and the deck.
- Don't write low-level `.docx`/`.pptx` assembly code from scratch — compose the bundled/sibling script's functions instead.
- If python-pptx isn't installed (`ModuleNotFoundError: No module named 'pptx'`), run `pip install python-pptx` and continue.
