# Demo Artifacts

This directory contains **Showboat-generated** demo documents that provide
verifiable proof-of-work for Dark App Factory builds.

## What's Here

| File | Description |
|------|-------------|
| `build-report.md` | Auto-generated build report with real file listings |
| `audit-report.md` | Judge/Satisficer audit report with verdict |
| `screenshots/` | Browser screenshots captured by Rodney during verification |

## How They're Created

1. **Showboat** (`uvx showboat`) captures real CLI output into Markdown documents.
   Every code block in these files contains actual command output, not agent-reported text.

2. **Rodney** (`uvx rodney`) drives a headless Chrome instance to navigate the
   generated app, take screenshots, and verify UI elements exist.

3. The factory pipeline runs both tools automatically during the build:
   - After worker build: Showboat creates `build-report.md`
   - During judge phase: Rodney takes screenshots, Showboat creates `audit-report.md`

## Verification

Re-run all recorded commands and diff against captured output:

```powershell
uvx showboat verify demos/build-report.md
uvx showboat verify demos/audit-report.md
```

## References

- [Showboat](https://github.com/simonw/showboat) -- Create executable demo documents
- [Rodney](https://github.com/simonw/rodney) -- Chrome automation from the CLI
- [Agent Demo Verification Pattern](../docs/AGENT_DEMO_VERIFICATION_PATTERN.md)
