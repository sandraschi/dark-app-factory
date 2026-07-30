# dark-app-factory Agent Context

Fleet MCP server. See `justfile` for available recipes.

## CURRENT WORK ORDER (2026-07-30)

Work through `TODO.md` in the repo root, tasks G1 to G9 in order (T1-T9 are done, see git log). Evidence and reasoning in `reports/reassess-blocks-2026-07-30.md`. Respect the invariants in `CLAUDE.md`. Never modify `outputs/` or `logs/`. Do not add new blocks before G1-G5 and the beekeeper regression run are done.

## Quick Ref

```powershell
uv run pytest tests/ --ignore=tests/test_e2e_scaffold.py -q
```
(test_e2e_scaffold.py hangs ~4 min, skip it)
