# Skill Benchmark: gws-doc

**Model**: <model-name>
**Date**: 2026-08-23T06:28:29Z
**Evals**: 1, 2, 3 (3 runs each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 42% ± 52% | +0.58 |
| Time | 0.0s ± 0.0s | 0.0s ± 0.0s | +0.0s |
| Tokens | 0 ± 0 | 0 ± 0 | +0 |

## Notes

- eval-folder-specified without_skill run passed all 6 assertions because the baseline agent had reference-memory access to the gws CLI and used it manually — this eval may not clearly demonstrate the skill's differentiated value; consider a stricter baseline (no CLI memory) or a harder eval for the next iteration.
- Several with_skill runs (eval-folder-unspecified, eval-folder-specified) hit a cmd.exe reinterpretation bug with '|'/'&' characters during document creation, worked around manually mid-run. The shared builder scripts (gws_docs_builder.py) were already fixed for this bug, but these eval runs appear to predate that fix being in place — the pass rate is genuine, but expect fewer workarounds needed on a re-run against the current skill version.
- time_seconds and tokens are 0 for all runs because no timing.json files were captured during these eval runs — the pass-rate comparison is reliable, but there is no time/token efficiency data for this iteration.