# dark-app-factory Agent Context

Fleet MCP server. See `justfile` for available recipes.

## Status (2026-07-30 late)

**T1-T9**: Done (morning fix pass)
**G1-G7**: Done (evening integration pass — all committed, 219 tests pass)
**Next**: `just test-e2e` (beekeeper regression run per TODO.md §After G1-G5 land)

## Quick Ref

```powershell
uv run pytest tests/ --ignore=tests/test_e2e_scaffold.py -q
```
(test_e2e_scaffold.py hangs ~4 min, skip it)
