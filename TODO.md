# TODO: Blocks integration pass (2026-07-30 evening)

**For**: autonomous coding agent (opencode / ds4) or human.
**Evidence and reasoning**: `reports/reassess-blocks-2026-07-30.md`. Read it first.
**Guardrails**: invariants in `CLAUDE.md`. Do not undo the 0.2.1/0.2.2 boot-verify contract. Never modify `outputs/` or `logs/`.

**Completed 2026-07-30 (morning work order)**: T1-T9 all landed and verified in git (921afaf, 8384293, 81dd792, plus CI b11e2b6, pre-commit 00af0bf). See git log. Superseded task text removed; history in `reports/deep-assess-2026-07-30.md`.

**Verification for every task**:
```
uv run pytest tests/ blocks/ --ignore=tests/test_e2e_scaffold.py -q
ruff check . ; ruff format --check .
```
Baseline: 207 passed, 1 skipped, ~7 s. Must not regress.

---

## G1 (CRITICAL, do first): Two-phase block install

Blocks currently install at `worker.py` step 0b into an empty output dir, so `install_block`'s glue appends (target file must exist) and `merge_deps` (requirements.txt / package.json must exist) both silently no-op on every real run.

1. Split `blocks/loader.py` responsibilities: `match_blocks(specs)` stays pre-generation. New `integrate_blocks(output_dir, matched)` runs POST-generation: copy backend/frontend files, mount routers (see G5), merge deps.
2. In `worker.py`: step 0b becomes match-only and builds `block_context` (see G2). Add a new step after all specialist file generation and before manifest write: call `integrate_blocks`.
3. `merge_deps` must create `requirements.txt` if missing (blocks may be the only Python deps). For package.json, if missing, log a warning naming the block deps that could not be merged; do not fabricate a package.json.

**Accept**: unit test that runs match then generation-simulation (write a stub main.py + requirements.txt) then integrate, and asserts glue applied and deps present. Second test: integrate into a dir with no main.py fails loudly with a named error, not silently.

## G2 (CRITICAL): Inject block context into LLM prompts

Nothing reads `block.json`'s `specialists` section; architect and council prompts contain zero block information.

1. Build `block_context: str` from matched manifests: for each block its name, description, `backend_routes`, `frontend_pages`, importable frontend symbols (`specialists.*.imports`), and backend import path (`backend.blocks.<name>.routes`).
2. Append to the architect `file_list_prompt` in `worker.py`: the block file paths already provided (do not plan them again) and the capabilities covered (do not plan competing implementations, e.g. no custom auth when membership block is present).
3. Append to the council specialist prompts in `src/specialists/council.py`: same context plus explicit instruction that frontend pages import block components from `src/components/blocks/<name>/...` and backend code must not redefine block routes.

**Accept**: unit test that block_context contains routes/pages/imports for a matched block; prompt-construction test asserting the context string is present in architect and specialist prompts when blocks matched, absent when none matched.

## G3 (CRITICAL): Pin stack to FastAPI + React when blocks match

All blocks are FastAPI + React. `src/specialists/council.py` (~line 114) still teaches Express handler patterns.

1. In `src/utils/stack_profile.py` (or where the profile is resolved): if any block matched, force `backend=python/fastapi`, `frontend=react`, log the override with the block names as reason.
2. Branch the council backend-specialist prompt on the stack profile: FastAPI patterns (APIRouter, async def, HTTPException, pydantic models) for python/fastapi; keep the existing Express text for node runs without blocks.

**Accept**: test that a spec matching the membership block resolves to fastapi regardless of what the Foreman proposed; council prompt test asserting no Express instructions appear in the fastapi branch.

## G5 (HIGH, do before G4): Deterministic router mount, delete append-glue

`main.py.append` snippets lack import lines (`app.include_router(stripe_router)` alone is a NameError) and file-append is order-fragile.

1. `integrate_blocks` writes `backend/blocks/__init__.py` in the output: imports each installed block's router and exposes `all_routers: list`.
2. Ensure the generated `main.py` mounts them. Preferred: G2's prompt instructs the backend specialist to include the loop `for r in all_routers: app.include_router(r)`; safety net: post-generation, if the loop marker is absent from main.py, append the import plus loop deterministically (this append IS allowed because it carries its own imports and runs post-generation).
3. Delete all `glue/*.append` files and the append branch in loader.py. `blocks/stripe/glue/App.tsx.append` currently holds JSON metadata; move that information into block.json (it is already redundant with `specialists`) and delete the file.

**Accept**: integrate a temp output with membership + stripe: `python -c "import main"`-style compile check passes, both routers reachable in a TestClient smoke test. Grep shows zero `.append` files under blocks/.

## G4 (HIGH): Fix node dependency schema

`merge_deps` string-parsing writes `"": "@stripe/stripe-js"` into package.json for scoped packages.

1. Change block.json schema: `dependencies.node` becomes an object `{"@stripe/stripe-js": "^4", "@stripe/react-stripe-js": "^3"}`. Update the two blocks that use node deps and the schema doc in `docs/BLOCKS_PLAN.md`.
2. `merge_deps` copies key/value pairs verbatim, existing keys win.

**Accept**: unit test merging scoped packages produces correct package.json, no empty keys.

## G6 (MEDIUM): Trigger matching sanity

Substring triggers (`pay`, `plan`, `user`, `org`, `team`) over-match wildly.

1. Word-boundary regex matching (`\b`), case-insensitive.
2. Cap matched blocks at 6; log the discarded overflow.
3. Optional flag `--blocks` to force an explicit list, bypassing matching.

**Accept**: test that `payload` does not match `pay`, `organize` does not match `org`; cap test.

## G7 (MEDIUM): Stub honesty

`admin`, `aichat`, `social` have no backend implementation; `blog`, `booking` have no tests.

1. Add `"status": "stub"` to admin/aichat/social block.json; `"status": "beta"` to blog/booking; `"status": "ready"` elsewhere.
2. `match_blocks` skips status=stub with a log line. Help page / README block table shows the status column.
3. Either write the missing blog/booking tests (preferred, mirror an existing block's test shape) or mark them stub too. Do not leave beta blocks untested past this pass.

**Accept**: matching a spec containing "admin" installs nothing and logs the stub skip; block table in Help shows status.

## G9 (LOW): Inter-block requires

Add optional `"requires": ["stripe"]` to block.json (webshop -> stripe, admin -> membership, subscriptions -> stripe). Loader installs transitively, cycles rejected. Test with webshop.

---

## After G1-G5 land: THE RUN

Run the beekeeper vibe (`vibe_current.md`) end to end. Expect membership (+ booking if not stub-blocked) to trigger. Keep the output as the first regression baseline whatever the verdict. File what breaks as new tasks; do NOT add new blocks before this run has happened.

Then: CHANGELOG 0.3.0-beta, mark this file's completed items with [x] and a date.

## Carried, re-scoped (after THE RUN)

- JS/TS gates (`node --check` where applicable, `tsc --noEmit`, `vite build`) with one repair pass: now primarily verifies LLM glue pages against block exports.
- Closure pass, reduced scope: LLM-generated files only (blocks declare their own deps).
- worker.py deep-crawl bare-import fix, framer-motion regex guard.
- pytest timeout + marker for test_e2e_scaffold.py.
