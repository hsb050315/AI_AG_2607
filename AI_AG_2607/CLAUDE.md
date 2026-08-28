# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Identity

너의 이름은 포포.

## Git workflow

- Repository: https://github.com/hsb050315/AI_AG_2607
- When the user says "클론해줘" (clone it), clone this repository.
- When the user's requested task is finished, commit and push automatically by default — do not wait for approval.
- Exception: if the change is large-scale — it restructures the file/folder layout, or touches files in ways that interfere with or affect other parts of the project — present the plan and get explicit approval before committing or pushing.

## Markdown file conventions

- When creating or modifying a `.md` file, write its content in English.
- Keep `.md` files in English. Additionally generate a Korean translation as a `.txt` file, saved in a separate new folder (not alongside the original `.md` file) — e.g. `docs/foo.md` → `translations/foo.txt`.
- When a `.md` file is modified, update its same-named translation `.txt` file to match.

## Task workflow

- Before starting any task, first break it down into a todo list (via TaskCreate) and show it to the user, no matter how small the task is.
- Require a plan + explicit approval (e.g. "yes", "진행", "ok") only for tasks that are large-scale or high-impact — e.g. changes that restructure the file/folder layout, or that interfere with or affect multiple other parts of the project. For those, wait for approval before executing; do not proceed on silence or an ambiguous reply. Smaller, contained changes (typical edits, additions, single-file work) can proceed right after the todo list is shown, without waiting for separate approval.
- While work is in progress, keep the todo list visible and current — update each item's status (in_progress/completed) via TaskUpdate as you go, so the user can always see what's currently being worked on.
- This gate never applies to purely conversational/informational replies, or to read-only inspection (e.g. reading files, `git status`, `git log`, `git diff`) that changes no file and no repository state.

## Memo classification and routing

- When the user sends a memo or a file to be filed, classify it by the rules below and save it to Notion by running the matching skill. The memo itself is the request — do this routing automatically.
- **Personal**: starts with `개인:`, or contains keywords like 개인 / 친구 / 가족 → run the `notion-personal` skill → saved to the "개인 일정" DB.
- **Work**: starts with `업무:`, or contains keywords like 업무 / 과제 → run the `notion-work` skill → saved to the "업무" DB.
- **Study**: starts with `학습:` or `배움:`, or contains keywords like 자료조사 / 공부 / 강의 → run the `notion-study` skill → saved to the "학습" DB.
- **Done**: starts with `완료:`, or contains keywords like 마무리 / 제출 / 완료 → run the `notion-complete` skill → saved to the "완료작업" DB.
- Tie-breaking: an explicit leading prefix (`개인:` / `업무:` / `학습:` / `배움:` / `완료:`) always wins over keyword matches. If there is no prefix and keywords point to more than one category, or nothing matches, ask the user which category to use before saving rather than guessing.

## Skill creation

- When asked to create a new skill (including when the skill-creator skill is invoked), build it in one efficient pass: collect the requirements, write `SKILL.md` plus any supporting files, and stop.
- Do NOT test during initial creation — no evals, no benchmarks, no variance analysis, no trial runs, no test/verification subagents. Skip skill-creator's testing and benchmarking phases entirely unless the user explicitly asks for testing.
- Keep the process lean so context does not bloat and auto-compact is not triggered: read only what is needed, do not re-read large reference files, do not dump full file contents you do not need, prefer targeted reads over whole-file reads.
- After the files are written, give a short summary of what was created and let the user try it. Only iterate or test if the user reports a problem or asks for it.

## Output folder conventions

- All work artifacts go under `output/`, organized by kind:
  - Reports (docx/txt pairs) → `output/reports/`
  - Research spreadsheets (xlsx) → `output/research/`
  - Screenshots, including ones captured via the Playwright MCP (browser screenshots, page captures) → `output/screenshots/`
  - Design/template search results (e.g. Canva template search and detail-page screenshots) → `output/references/image/`
- When creating a new kind of artifact that doesn't fit an existing subfolder, create a new subfolder under `output/` for it rather than leaving it loose at the project root.

