set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# Run fast tests (excludes slow Ollama-dependent e2e)
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -q -m "not slow" --deselect tests/test_e2e_scaffold.py

# Run full test suite including e2e (requires Ollama, 10+ min per test)
test-e2e:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/test_e2e_scaffold.py -v --timeout=600

# Run all gates: lint + test + fmt
gates-green: lint test fmt

# Run ruff format check
fmt:
    Set-Location '{{justfile_directory()}}'
    uv run ruff format src/ --check

# Serve factory dashboard (backend)
serve:
    Set-Location '{{justfile_directory()}}'
    uv run uvicorn web.server:app --host 127.0.0.1 --port 10738 --reload

# Serve frontend dev server (Vite)
dev:
    Set-Location '{{justfile_directory()}}'
    Start-Process "bun" -ArgumentList "run --cwd web_sota dev"

# Build the SOTA frontend
build-web:
    Set-Location '{{justfile_directory()}}'
    bun run --cwd web_sota build

# Run all gates: lint + test + fmt
gates-green: lint test fmt

# Bootstrap: install dev deps
bootstrap:
    uv sync --group dev
    Write-Host "Dependencies synced." -ForegroundColor Green