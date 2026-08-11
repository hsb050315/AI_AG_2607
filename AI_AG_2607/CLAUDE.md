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

- Default to acting autonomously: proceed with small, contained changes (typical edits, additions, single-file work) without stopping to ask for approval first.
- Require a plan + explicit approval (e.g. "yes", "진행", "ok") only for tasks that are large-scale or high-impact — e.g. changes that restructure the file/folder layout, or that interfere with or affect multiple other parts of the project. For those, write the plan as a short numbered step list in the chat reply, then stop and wait. Do not proceed on silence or an ambiguous reply.
- Use the task list tool (TaskCreate/TaskUpdate) to track progress on multi-step work, but only when the task is substantial enough to warrant it — don't create todo items for every small action. Minor/trivial steps don't need an explicit todo entry.
- This gate never applies to purely conversational/informational replies, or to read-only inspection (e.g. reading files, `git status`, `git log`, `git diff`) that changes no file and no repository state.

## Output folder conventions

- All work artifacts go under `output/`, organized by kind:
  - Reports (docx/txt pairs) → `output/reports/`
  - Research spreadsheets (xlsx) → `output/research/`
  - Screenshots → `output/screenshots/`
  - Anything produced via the Playwright MCP (e.g. browser screenshots, page captures) → `output/playwright/`
- When creating a new kind of artifact that doesn't fit an existing subfolder, create a new subfolder under `output/` for it rather than leaving it loose at the project root.

## Repository status

This repository is currently empty scaffolding — it contains no source code, build configuration, or tests yet. The only tracked content is `.claude/settings.local.json` (local Claude Code permission settings).

There are no build, lint, or test commands to run because no project has been initialized here.

When code is added to this repository, update this file with:
- Build/lint/test commands (including how to run a single test)
- High-level architecture notes once a real structure exists
