# dark-app-factory — MCP Server Capabilities

## Server Overview

Dark App Factory is a FastMCP 3.2 server that generates, audits, and scores web applications from natural-language "vibe" descriptions using local AI models (Ollama). It implements a two-stage generation pipeline: a "foreman" model plans the application architecture and a "worker" model writes the code files. The server includes a Playwright-based visual auditor that takes screenshots, captures console errors, and detects Vite error overlays, empty page renders, 404 responses, and broken imports. The auditor scores apps 0-100 with letter grades (A-F) via static analysis: file counts, entry point detection, missing files, syntax errors, framer-motion import correctness, runt/stub detection, and tree-character filenames. Results are rendered as Prefab UI cards and optionally POSTed to the web dashboard. The server also features a GhostExtractor that reverse-engineers structural and aesthetic "blueprints" from existing websites (color palettes, typography, layout, technical stack) for use as design references.

The server runs on port 10738 (backend) with a web dashboard on port 10739. It exposes one primary MCP portmanteau tool (dark-app-factory) with 7 operations plus a dedicated assessment tool. The LLM client supports role-based model routing with configurable endpoints, models, temperatures, and token tracking for foreman (planning/architecture) and worker (code generation) roles.

## Tools

### dark-app-factory
**Purpose**: Software Factory scaffold for local AI models. Portmanteau consolidating run, status, outputs, fleet, launch, stop, and assess operations.
**Parameters**:
- params (dict, required): Operation parameters container.
  - operation (str, required): One of "run", "status", "outputs", "fleet", "launch", "stop", "assess".
  - vibe (str, optional): Natural-language description of what to build. Required for "run". 10-8000 chars. Can include "## Tech Stack" section.
  - output_name (str, optional): Directory name under outputs/. Auto-generated if omitted.
  - foreman_model (str, optional): Ollama model for planning (e.g., "llama3.1:latest").
  - worker_model (str, optional): Ollama model for code generation (e.g., "qwen2.5-coder:latest").
  - run_id (str, optional): Run ID for status/stop operations. Omit for status to list all runs.
  - log_tail (int, optional, default=30): Log lines to include in status. Max 500.
  - limit (int, optional, default=10): Max results for outputs. Max 50.
  - output_dir (str, optional): Path or bare name for assess/launch. Omit for most recent.
  - port (int, optional): Override port for launch.
  - push_to_webapp (bool, optional, default=True): POST assessment result to DAF_WEB_BASE.
  - lines (int, optional, default=80): Log lines for fleet tail_log. Max 2000.
  - log_search (str, optional): Substring filter for fleet tail_log.

**Return Format**: Varies by operation. All return structured dict.
**Examples**:
- dark-app-factory(params={"operation": "run", "vibe": "A modern dashboard with charts"})
- dark-app-factory(params={"operation": "status", "run_id": "abc123", "log_tail": 50})
- dark-app-factory(params={"operation": "outputs", "limit": 5})
- dark-app-factory(params={"operation": "assess", "output_dir": "output_008"})
- dark-app-factory(params={"operation": "fleet", "operation_sub": "ping"})
- dark-app-factory(params={"operation": "launch", "output_dir": "output_008"})

### factory_assess (dedicated tool)
**Purpose**: Analyse a generated app and render an interactive Prefab assessment card. Static analysis only (no LLM): file counts, entry point detection, missing files, JS/Python syntax errors, framer-motion import correctness, runt/stub detection, tree-character filenames. Scores 0-100, letter grade A-F.
**Parameters**:
- output_dir (str | None): Path or bare name. Omit for most recent.
- push_to_webapp (bool, default=True): POST full JSON to web dashboard.
**Return Format**: Prefab card with stats grid + issue table + language breakdown.
**Examples**:
- factory_assess(output_dir="output_008")
- factory_assess(output_dir="C:/factory/outputs/test_app")

## Operation Details

### run — Factory Generation
Starts a full factory generation from a vibe/prompt. Returns run_id for polling. The foreman model plans the application architecture and component tree. The worker model generates each file sequentially. Supports custom Ollama models per role via env vars FOREMAN_MODEL and WORKER_MODEL. Generation output is written to outputs/{output_name}/.

### status — Poll Run Status
Returns current run state (queued, running, complete, failed), progress, recent log lines, and the generated output directory when complete. Omit run_id to list all runs.

### outputs — List Completed Outputs
Returns all completed generation outputs sorted by newest first. Each entry includes name, size, creation time, and file count.

### fleet — Dashboard Operations
Sub-operations: ping (health check), web_health (dashboard status), web_status (detailed), dashboard_url (return URL), launch_dashboard (start in browser), tail_log (read log lines), read_settings (show config).

### launch — Launch Generated App
Starts the generated app (npm run dev or python main.py) in a new console window on a configurable port.

### stop — Cancel a Run
Cancels a running factory build by run_id. The partial output remains in the outputs directory.

### assess — Static Analysis Assessment
Scans the generated output directory for quality signals. Scores 0-100 with grade A-F. Detects: broken imports, file count anomalies, missing entry points, syntax errors.

## LLM Client Configuration

### Foreman (Planning) Role
- Default model: llama3.1:latest (configurable via FOREMAN_MODEL)
- Default endpoint: http://localhost:11434/v1 (configurable via FOREMAN_BASE_URL)
- Default API key: ollama (configurable via FOREMAN_API_KEY, falls back to OPENAI_API_KEY)
- Default temperature: 0.7
- Responsible for: application architecture, component tree planning, file list generation

### Worker (Code Generation) Role
- Default model: qwen2.5-coder:latest (configurable via WORKER_MODEL)
- Default endpoint: http://localhost:11434/v1 (configurable via WORKER_BASE_URL)
- Default API key: ollama (configurable via WORKER_API_KEY)
- Default temperature: 0.2
- Responsible for: writing each file's content, implementing planned components

### Token Tracking
Both clients track input and output tokens per session. Call get_usage() or get_usage_summary() to retrieve tokens consumed.

## GhostExtractor

The GhostExtractor reverse-engineers websites into structured blueprints:
- Aesthetic analysis: dominant colors, typography, theme classification
- Structural analysis: layout type, component inventory
- Technical specs: framework detection, styling approach
Blueprints are saved as JSON files in the ghosts/ directory.

## Auditor (Playwright)

The visual auditor runs headless Chromium via Playwright to:
- Navigate to the app URL (wait for networkidle)
- Capture console logs and page errors
- Detect Vite Error Overlay text
- Check for empty page content (< 500 chars = suspicious)
- Scan for "Failed to resolve import" errors
- Detect 404 pages
- Take full-page screenshots (saved to audit_results/)
Screenshots are timestamped PNG files.

## Configuration

### Environment Variables
- FOREMAN_MODEL (str, default="llama3.1:latest"): Ollama model for the planning/foreman role.
- FOREMAN_BASE_URL (str, default="http://localhost:11434/v1"): OpenAI-compatible endpoint for foreman.
- FOREMAN_API_KEY (str, default="ollama"): API key for foreman endpoint.
- WORKER_MODEL (str, default="qwen2.5-coder:latest"): Ollama model for the code generation/worker role.
- WORKER_BASE_URL (str, default="http://localhost:11434/v1"): OpenAI-compatible endpoint for worker.
- WORKER_API_KEY (str, default="ollama"): API key for worker endpoint.
- DAF_PORT / MCP_PORT (int, default=10738): HTTP server port.
- DAF_HOST (str, default="127.0.0.1"): HTTP server bind address.
- DAF_WEB_BASE (str): Base URL for the web dashboard (for push_to_webapp).

## Data Sources
- Generated outputs: outputs/{output_name}/ directories containing the full generated app.
- Ghost blueprints: ghosts/ghost_{hash}.json files from website extraction.
- Audit results: audit_results/screenshot_{timestamp}.png screenshots.
- No external databases or APIs required (all local via Ollama).

## Integration Points
- Ollama: Required for LLM generation (foreman and worker models).
- Playwright: Required for visual auditing (install browsers separately).
- Web dashboard: Optional FastAPI + React dashboard at port 10739.
- Prefab UI: Assessment cards rendered via prefab-ui library.

## Error Handling
- LLM connection refused: Clear error message instructing to start Ollama.
- Missing Playwright: Error message with install command.
- Generation failures: Partial output preserved in outputs directory.
- All tools return structured dicts with success/failure status.

## Audit Scoring Rubric
The factory_assess tool evaluates generated apps on multiple dimensions weighted into a composite score:

1. **File Count (15 points)**: Expects 3-15 well-named files. Fewer than 3 files suggests a placeholder. More than 30 suggests fragmentation.
2. **Entry Point Detection (20 points)**: Checks for index.html, package.json, main.py, or app.py. Missing entry points reduce the score significantly.
3. **Missing File Detection (15 points)**: Scans for broken imports — files referenced in imports or includes that do not exist.
4. **Syntax Errors (20 points)**: Runs JavaScript/Python syntax parsers on each generated file. Any parse error deducts heavily.
5. **Framer Motion Correctness (10 points)**: Validates that framer-motion imports follow the expected pattern (framer-motion not motion). Incorrect package names indicate the model was not following instructions.
6. **Runt/Stub Detection (10 points)**: Flags files containing placeholder content like "TODO", "Lorem ipsum", "Function name", or minimal stub implementations.
7. **Filename Quality (10 points)**: Detects tree-character filenames (ab.c, x.js, temp1.txt) which suggest poor organization. Well-named descriptive files score higher.

Grade thresholds: A=90-100 (excellent, production-viable), B=80-89 (good, minor issues), C=70-79 (adequate, several issues), D=60-69 (poor, major issues), F=0-59 (fails basic checks, likely non-functional).

## LLM Client Architecture
The LLMClient class implements role-based model routing with separate configuration for foreman (architecture planning) and worker (code generation) roles. Each role has independent model selection, base URL, API key, and temperature defaults. The foreman role defaults to temperature 0.7 for creative architecture planning. The worker role defaults to temperature 0.2 for deterministic code generation. Token usage is tracked per-role with cumulative input/output counters accessible via get_usage() and get_usage_summary(). The client performs a 60K-token warning threshold check before generation, alerting when prompts may exceed the model's context window. Connection errors to the LLM endpoint are caught and logged with clear recovery instructions. The client uses the OpenAI SDK for API compatibility, supporting any OpenAI-compatible endpoint including Ollama, LM Studio, vLLM, and cloud providers.

## Factory Generation Pipeline
The generation pipeline proceeds through these stages:

1. **Parse Phase**: The vibe description is analyzed for tech stack hints (## Tech Stack sections), required features, and output constraints.
2. **Plan Phase (Foreman)**: The foreman model generates an architecture plan including component tree, file list, data flow, and styling approach. The plan is extracted from the model response.
3. **File Manifest Generation**: Based on the plan, a file manifest is created listing each file to generate with its purpose and dependencies.
4. **Code Generation Phase (Worker)**: For each file in the manifest, the worker model generates the complete file content. Files are generated sequentially with dependency awareness.
5. **Write Phase**: Generated files are written to the output directory under outputs/{output_name}/. Existing files are not overwritten.
6. **Completion Phase**: The run is marked as complete. The output directory path is stored for assessment and launch operations.

During generation, progress is tracked and available via the status operation. Log lines from both models are captured and returned with tail_log. The generation can be cancelled at any point via the stop operation — partial output remains for inspection.

## Generation Quality Considerations
The quality of generated apps depends heavily on the Ollama models used. Larger models (8B+ parameters) produce more coherent architecture plans and better-structured code. Code-specialized models (qwen2.5-coder, deepseek-coder) produce more idiomatic, bug-free code than general-purpose models. The foreman model benefits from higher temperature (0.7) for creative architecture planning. The worker model performs best at lower temperature (0.2) for deterministic, consistent code output. When generation quality is poor, try: using larger models, providing more specific tech stack instructions, including example file structures in the vibe description, or running multiple generations and selecting the best result.

## Ghost Extraction Architecture
The GhostExtractor reverse-engineers websites through these steps:

1. **URL Scraping**: The target URL is fetched and converted to markdown using the configured web scraping tool.
2. **Technical Spec Extraction**: Playwright analyzes the page for framework detection (React, Vue, Angular, vanilla), CSS methodology (Tailwind, Bootstrap, styled-components), and JavaScript usage patterns.
3. **Aesthetic Analysis**: Dominant colors are extracted from CSS computed styles. Typography (font families, weights, sizes) is catalogued. The overall theme is classified (dark, light, minimal, premium, playful, corporate).
4. **Structural Analysis**: Layout type is identified (sidebar, top-nav, grid, masonry, single-column). Components are inventoried (hero sections, feature grids, testimonials, pricing tables, navigation bars, footers).
5. **Blueprint Synthesis**: An LLM synthesizes the extracted data into a structured JSON blueprint saved to the ghosts/ directory as ghost_{url_hash}.json.
6. **Design Reference**: The blueprint can be used as input for future factory generations, informing the foreman model about desired aesthetic and structural patterns.

## Worker Model Output Characteristics
Different worker models produce different code quality characteristics. The qwen2.5-coder series (1.5B, 7B, 14B, 32B) excels at producing idiomatic Python and JavaScript with consistent indentation, proper imports, and few syntax errors. The deepseek-coder series (1.3B, 6.7B, 33B) produces good code with strong comment quality and documentation strings but occasionally introduces unused imports. The phi3 series (14B) produces concise, well-structured code but may skip edge case handling. The starcoder2 series (3B, 7B, 15B) produces functional code with good breadth of coverage but may include placeholder implementations. The codestral series (22B) produces high-quality code with strong attention to security and performance but requires substantial VRAM. General-purpose models (llama3.1, gemma2, mistral) produce more variable code quality and may not follow idiomatic patterns for the target language. For best results with React/TypeScript generation, use qwen2.5-coder or deepseek-coder at 7B+ parameter count. For Python backend generation, any code-specialized 7B+ model works well. For HTML/CSS generation, smaller models (3B-7B) are sufficient since the output is less syntactically complex.

## Foreman Model Planning Quality
The foreman model's architecture planning quality directly affects the worker model's output. Larger foreman models (70B+) produce detailed plans with specific component names, file structures, and data flow diagrams embedded in the plan text. Mid-size models (8B-13B) produce adequate plans with reasonable component decomposition but may miss edge cases or secondary features. Small models (1B-3B) produce minimal plans that may result in the worker generating incomplete or poorly structured applications. When using a small foreman model, compensate by providing a more detailed vibe description with explicit file structure and component hierarchy. The foreman's temperature (default 0.7) can be adjusted: higher temperature (0.8-1.0) produces more creative architecture plans with novel component organizations, lower temperature (0.3-0.5) produces more conventional, predictable plans that are easier for the worker to implement.

## Development and Extension
The dark-app-factory codebase is structured for easy extension. To add a new assessment criterion, edit the factory_assess function in the auditor module and add scoring logic. To add a new generation stage (e.g., a testing phase that runs generated apps through Playwright), add a new phase in the factory run pipeline. The LLMClient can be extended with additional roles beyond foreman and worker by adding new role configuration blocks. The GhostExtractor can be enhanced with additional analysis modules for specific technology stacks. The project follows the fleet SOTA standards with a justfile containing recipes for serve, test, lint, and pack-mcpb. Tests are in tests/ and can be run with `uv run pytest`. The package is distributed via uv and follows the standard Python MCP scaffold with pyproject.toml, src/ layout, and mcpb/ directory for Claude Desktop distribution.

## Use Cases and Applications
The dark-app-factory is designed for rapid prototyping and exploration. Common use cases include: generating React component libraries from natural language descriptions, creating landing pages and marketing sites for quick client demos, prototyping dashboard layouts before committing to a full implementation, generating code snippets and examples for documentation, creating educational apps for workshops and tutorials, exploring design alternatives by generating multiple variations of the same app, and bootstrapping internal tools that need a functional UI without manual coding. The factory excels at generating the first 80% of an application — the functional skeleton, layout, and basic interactivity. The remaining 20% (polish, edge cases, real data integration) benefits from human refinement.

## Logging and Debugging
The factory logs all generation activity to stdout/stderr with structured log messages. The tail_log operation in the fleet subcommand provides access to recent log lines. Logs include: model initialization details (role, model name, endpoint URL), generation progress (planning phase start/complete, each file generation start/complete), token usage per model call, errors and warnings (connection failures, model timeouts, generation truncation), assessment results (scores, issue counts, file counts). The ASSESSMENT_SCORE environment variable can be set to exit with a non-zero code if the score is below a threshold — useful for CI/CD integration. For debugging generation issues, examine the full log output with tail_log and search for errors. The token tracking in LLMClient provides per-role input/output token counts for cost analysis when using paid API endpoints. The generation output directory contains the complete generated app for inspection — examine individual files for correctness and completeness.

## Tool Composition Patterns
The dark-app-factory tools can be composed into multi-step workflows. The most common pattern is: (1) Run generation, (2) Poll status until complete, (3) Assess the output with factory_assess, (4) If score is acceptable, launch the app, (5) Iterate with a refined vibe if score is low. For batch generation workflows: run multiple generations sequentially with different vibe descriptions, then compare assessments side-by-side using the output names. For deployment workflows: generate an app, assess it, launch it for review, then copy the output to a production location. For learning workflows: generate an app, study the generated code to understand patterns, then manually modify it to deepen understanding. The portmanteau tool structure (dark-app-factory with params dict) keeps all operations discoverable through a single schema while providing clear operation dispatch internally.

## Web Dashboard Features
The web dashboard on port 10739 provides visual access to factory operations. Features include: generation run list with status indicators (queued, running, complete, failed), log viewer with real-time tailing during generation, output browser with file tree and content preview, assessment result display with scored cards and issue lists, launch button to start generated apps in the browser, configuration editor for model selection and parameters, and output directory file manager for download and delete operations. The dashboard auto-refreshes during active generation runs. Assessment results are displayed with color-coded grades (green for A/B, yellow for C/D, red for F) and drill-down issue details. The dashboard is built with React and Tailwind CSS following fleet SOTA standards.

## Fleet Integration Architecture
The factory registers with the MetaMCP orchestrator for health monitoring when the web_sota dashboard is running. The fleet integration includes: health endpoint for liveness checks (GET /health returns server status), log streaming via the tail_log operation for centralized log aggregation, output directory listing for artifact management, and assessment result export for quality tracking. The factory follows fleet port conventions: backend on 10738, frontend on 10739. When deployed as part of the MCP fleet, the factory can be discovered through the MetaMCP dashboard and started/stopped via the fleet orchestrator. The outputs directory can be shared with the depot-mcp for centralized artifact storage and versioning. The assessment results can be exported to the fleet quality dashboard for trend analysis across generations.

## Prompt Templates Reference
The dark-app-factory registers FastMCP 3.2 native prompts for common workflows. The factory_run prompt describes how to generate a new application from a vibe description, including required parameters, model selection guidance, and output format. The factory_assess prompt explains the assessment scoring rubric and how to interpret results. The factory_outputs prompt lists recently generated applications with their scores. The ghost_extract prompt guides users through extracting a website blueprint. These prompts are accessible via the MCP prompts/list and prompts/get protocol methods. When used with Claude Desktop, the prompts auto-fill the conversation with structured instructions for the relevant operation. The prompts are registered in the server module and can be extended by adding new prompt functions with @mcp.prompt() decorator.

## Error Recovery and Edge Cases
The factory handles several edge cases gracefully. If the LLM connection is lost during generation, the run is marked as failed with a partial output preserved in the outputs directory — the failed run can be inspected and individual files can be salvaged. If the vibe description is too long for the model's context window, a warning is logged and the description should be shortened. If the output directory already exists, a new output name is auto-generated with a numeric suffix. If the launch port is in use, an error is returned with instructions to specify a different port. If the assessment finds no output directory, a score of 0 is returned with a clear message. The factory operations are idempotent where possible — running the same operation twice with the same parameters produces consistent results. The stop operation gracefully terminates the current generation at the next file boundary.

## CI/CD Integration
The dark-app-factory can be integrated into CI/CD pipelines for automated app generation and testing. Typical CI pipeline: (1) Install dependencies (uv sync, playwright install chromium). (2) Start Ollama or connect to a remote LLM endpoint. (3) Run generation with a predefined vibe description. (4) Run factory_assess on the output to verify quality. (5) Assert minimum score threshold (e.g., score >= 70). (6) Launch the generated app and run Playwright end-to-end tests. (7) If all checks pass, deploy the generated app or commit it to the project repository. The CI configuration should set WORKER_BASE_URL and FOREMAN_BASE_URL to the CI environment's LLM endpoint. For GitHub Actions, use a self-hosted runner with GPU access for best performance. The token tracking enables cost reporting for cloud API usage in CI.

## Comparison with Other Generation Tools
Unlike Cursor AI or GitHub Copilot which assist within an existing codebase, dark-app-factory generates complete standalone applications from scratch. Unlike Replit AI or Bolt.new which are cloud-based, the factory runs entirely locally with no data leaving your machine. Unlike create-react-app or Vite templates which provide static scaffolds, the factory generates custom code tailored to each specific description. The factory's dual-model architecture (foreman + worker) is inspired by the current best practice of separating architecture planning from code implementation, similar to how human developers sketch before coding.

## Fleet Integration
The dark-app-factory integrates with the fleet MetaMCP orchestrator for health monitoring. The web dashboard (port 10739) provides visual access to generation history, output browsing, and assessment results. Assessment results can be pushed to the web dashboard for persistent storage and review. The factory supports integration with other fleet MCP servers: generated apps can be deployed via the fleet deployment pipeline, stored in the depot-mcp for versioned artifact management, and tested via the playwright-mcp browser automation. The port 10738 (backend) and 10739 (frontend) follow the fleet port adjacency convention within the 10700-11500 range.
