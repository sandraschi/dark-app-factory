# 7-Zip Control: MCP Server + Webapp

> Build an MCP server and webapp for 7-Zip archive operations on Windows. Package for PyPI and GitHub.

## Requirements

1. **MCP Server** (FastMCP, stdio):
   - Tools: `sevenzip_extract`, `sevenzip_compress`, `sevenzip_list`, `sevenzip_test`
   - Invoke 7z.exe via subprocess (`7z x`, `7z a`, `7z l`, `7z t`)
   - Configurable 7z path (default: `C:\Program Files\7-Zip\7z.exe` or PATH)

2. **Webapp** (FastAPI + React or HTMX):
   - Upload archive, extract to folder
   - Select folder, compress to .zip or .7z
   - List archive contents
   - Same backend logic as MCP tools (shared service layer)

3. **Packaging**:
   - pyproject.toml with entry point `sevenzip-mcp`
   - GitHub Actions for test and release
   - PyPI publishable

## Tech Stack

- **Backend**: python/fastapi
- **Frontend**: react
- **Database**: sqlite (optional, for operation history)

## Constraints

- Windows-only (7z.exe path, subprocess)
- No placeholders; all tools must invoke real 7z or return clear error if not found
