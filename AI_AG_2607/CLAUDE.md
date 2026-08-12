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

## Output folder conventions

- All work artifacts go under `output/`, organized by kind:
  - Reports (docx/txt pairs) → `output/reports/`
  - Research spreadsheets (xlsx) → `output/research/`
  - Screenshots, including ones captured via the Playwright MCP (browser screenshots, page captures) → `output/screenshots/`
  - Design/template search results (e.g. Canva template search and detail-page screenshots) → `output/references/image/`
- When creating a new kind of artifact that doesn't fit an existing subfolder, create a new subfolder under `output/` for it rather than leaving it loose at the project root.

