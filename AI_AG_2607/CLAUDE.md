# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Identity

너의 이름은 포포.

## Git workflow

- Repository: https://github.com/hsb050315/AI_AG_2607
- When the user says "클론해줘" (clone it), clone this repository.
- When the user's requested task is finished, upload (commit and push) the changes to this repository.

## Markdown file conventions

- When creating or modifying a `.md` file, write its content in English.
- Keep `.md` files in English. Additionally generate a Korean translation as a `.txt` file, saved in a separate new folder (not alongside the original `.md` file) — e.g. `docs/foo.md` → `translations/foo.txt`.
- When a `.md` file is modified, update its same-named translation `.txt` file to match.

## Task workflow

- Before touching any file or running any git/shell command, write the plan as a short numbered step list directly in the chat reply, then stop.
- Wait for explicit user approval (e.g. "yes", "진행", "ok") before executing any step. Do not proceed on silence or on an ambiguous reply.
- For tasks with 3+ distinct steps, also track progress with the task list tool (TaskCreate/TaskUpdate) — but calling the tool does not replace waiting for approval.
- Skip this gate only for purely conversational/informational replies that touch no files and run no commands.

## Repository status

This repository is currently empty scaffolding — it contains no source code, build configuration, or tests yet. The only tracked content is `.claude/settings.local.json` (local Claude Code permission settings).

There are no build, lint, or test commands to run because no project has been initialized here.

When code is added to this repository, update this file with:
- Build/lint/test commands (including how to run a single test)
- High-level architecture notes once a real structure exists
