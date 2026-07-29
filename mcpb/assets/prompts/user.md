# dark-app-factory — User Guide

## Quick Start

### Installation
1. Clone the repository: `git clone https://github.com/sandraschi/dark-app-factory.git`
2. Create a virtual environment: `uv venv`
3. Activate: `.venv\Scripts\activate`
4. Install dependencies: `uv sync`
5. Install Playwright browsers: `playwright install chromium`
6. Ensure Ollama is running: `ollama serve`
7. Start the server: `uv run run_server.py`

### First Use
1. Call `dark-app-factory(params={"operation": "run", "vibe": "A minimal React dashboard with a sidebar and two charts"})`
2. Poll status with `dark-app-factory(params={"operation": "status", "run_id": "<id>"})`
3. Assess the result with `dark-app-factory(params={"operation": "assess"})`
4. Launch in browser with `dark-app-factory(params={"operation": "launch"})`

## Tutorials

### Tutorial 1: Generate a Simple App
Describe your app in natural language: `dark-app-factory(params={"operation": "run", "vibe": "A single-page app showing the current time and a greeting message"})`. The factory will plan the architecture, generate files, and return a run_id. The foreman model decides which framework and structure to use.

### Tutorial 2: Specify Tech Stack
Include a "## Tech Stack" section in your vibe: `dark-app-factory(params={"operation": "run", "vibe": "A task management board. ## Tech Stack: React, Vite, Tailwind CSS, no TypeScript"})`. This gives the foreman explicit guidance on what tools to use.

### Tutorial 3: Monitor Generation Progress
Call `dark-app-factory(params={"operation": "status", "run_id": "abc123"})` to check if the generation is still running. The response includes current progress, recent log lines, and the output directory when complete. Use `log_tail=100` for more log context.

### Tutorial 4: List All Runs
Call `dark-app-factory(params={"operation": "status"})` without a run_id to see all factory runs, both active and completed. Each entry shows the run ID, status, model used, and timestamp.

### Tutorial 5: List Generated Outputs
Call `dark-app-factory(params={"operation": "outputs", "limit": 5})` to see your 5 most recent generated application directories. Each entry includes the output name, file count, and creation time.

### Tutorial 6: Assess Output Quality
Call `dark-app-factory(params={"operation": "assess"})` to analyze the most recently generated app. The assessment includes: file count, entry point detection, missing files, syntax errors, framer-motion import correctness, and a 0-100 score with letter grade (A-F). Results render as a Prefab card.

### Tutorial 7: Assess a Specific Output
Call `factory_assess(output_dir="output_008")` to analyze a specific output directory by name or `factory_assess(output_dir="C:/factory/outputs/test_app")` with a full path.

### Tutorial 8: Launch Generated App
Call `dark-app-factory(params={"operation": "launch"})` to start the most recently generated app. The server runs `npm run dev` or `python main.py` in a new console window. Customize with `output_dir` and `port` parameters.

### Tutorial 9: Cancel a Run
If a generation is taking too long, cancel it: `dark-app-factory(params={"operation": "stop", "run_id": "abc123"})`. The partial output remains in the outputs directory for inspection.

### Tutorial 10: Use Custom Models
Generate with specific Ollama models: `dark-app-factory(params={"operation": "run", "vibe": "A data dashboard", "foreman_model": "llama3.2:3b", "worker_model": "phi3:14b"})`. This overrides the default FOREMAN_MODEL and WORKER_MODEL for this run only.

### Tutorial 11: Check Factory Dashboard Health
Call `dark-app-factory(params={"operation": "fleet", "operation_sub": "ping"})` to check if the web dashboard is reachable. Use `operation_sub: "dashboard_url"` to get the URL, or `operation_sub: "launch_dashboard"` to open it in the default browser.

### Tutorial 12: Tail Factory Logs
Call `dark-app-factory(params={"operation": "fleet", "operation_sub": "tail_log", "lines": 200})` to read the last 200 lines of the factory log. Add `log_search: "error"` to filter for error messages only.

### Tutorial 13: Multi-Step Development Loop
1. Generate: `run` with your vibe.
2. Wait for completion: poll `status` until complete.
3. Assess: `assess` the output for quality issues.
4. Fix: manually edit generated files.
5. Launch: `launch` to preview in browser.
6. Iterate: generate with refined prompts.

### Tutorial 14: Ghost Extraction (Website Blueprint)
Use the GhostExtractor to capture a website's design DNA. Call the extraction pipeline with a URL to get: color palette (dominant colors), typography (font families), layout structure (sidebar, grid, etc.), component inventory (hero, feature grid, etc.), and technical stack (framework, styling approach). Blueprints are saved as JSON files in the ghosts/ directory.

## REST API Reference

### MCP Endpoint
POST /mcp — Standard FastMCP HTTP transport for tool calls. Accepts JSON-RPC style requests with params.name and params.arguments.

### Health
GET /health — Returns health status of the dark-app-factory server.

## Troubleshooting

### Ollama Connection Refused
Run `ollama serve` in a terminal. Verify with `curl http://localhost:11434/api/tags`. The factory requires Ollama running locally.

### Playwright Not Installed
Run `playwright install chromium` after installing Python dependencies. The auditor requires Chromium for headless testing.

### Generation Is Stuck
Check if the selected Ollama model is available: `ollama pull llama3.1:latest` or `ollama pull qwen2.5-coder:latest`. Cancel the run and retry with a smaller model.

### Assessment Shows Low Score
Common issues: missing entry point (index.html, package.json), syntax errors in generated JavaScript/Python, files using placeholder content like "TODO" or "Lorem ipsum", tree-character filenames (no meaningful naming), broken imports. Fix these and reassess.

### Console Shows "Failed to resolve import"
The Vite dev server detected a missing npm dependency. Run `npm install` in the output directory, or check the import paths in the generated code.

## Advanced Configuration

### Custom Model Endpoints
You can configure custom LLM endpoints for both foreman and worker roles independently. For OpenAI integration, set FOREMAN_BASE_URL=https://api.openai.com/v1, FOREMAN_API_KEY=sk-..., FOREMAN_MODEL=gpt-4o. For LM Studio locally, set FOREMAN_BASE_URL=http://localhost:1234/v1. For a remote Ollama server, set WORKER_BASE_URL=http://ollama-server:11434/v1. The factory automatically detects the appropriate configuration per role. When using cloud endpoints, monitor token usage via get_usage() to track costs. The foreman role typically uses 500-2000 tokens per generation. The worker role uses 500-5000 tokens per file depending on complexity.

### Multi-Output Comparison
Generate multiple versions of the same app with different models or prompts to compare quality. For example, generate with llama3.1:8b + qwen2.5-coder for one version, then gemma2:9b + deepseek-coder for another. Compare the assessment scores side by side. The factory_assess tool provides objective metrics for comparison. Use the outputs list to browse available versions.

### Custom Assessment Path
When assessing apps generated outside the factory (e.g., manually written, cloned from a template), use the full path parameter: factory_assess(output_dir="C:/my-project"). The assessment still works on arbitrary directories, evaluating file count, entry points, syntax errors, and naming quality. This is useful for auditing third-party code or student projects.

### Environment-Specific Configuration
Create .env files for different environments (dev, ci, production). The LLMClient reads configuration from environment variables with sensible defaults. For CI/CD pipelines, set WORKER_BASE_URL to a shared build server endpoint. For development, use local Ollama for fast iteration. For production code generation, use larger, more capable models. The factory logs include the model name and endpoint used for each run, providing full traceability.

### Continuous Generation Pipeline
Set up a continuous generation workflow where generated apps are automatically assessed, and low-scoring outputs trigger regeneration with adjusted parameters. The assessment score provides the feedback signal. Use the batch upload capability to store generated apps in the depot-mcp for version control. Integrate with the CI pipeline to automatically test generated apps with Playwright end-to-end tests. This creates a closed-loop improvement cycle: generate, assess, deploy, test, learn, regenerate.

## Workflow: End-to-End App Factory

### Step 1: Environment Setup
Ensure Ollama is running with the desired models pulled: `ollama pull llama3.1:8b` and `ollama pull qwen2.5-coder:7b`. Verify with `ollama list`. Start the dark-app-factory server with `uv run run_server.py`.

### Step 2: Generate Application
Define a clear vibe description. Include specific requirements: framework, styling approach, component list, and data flow. Example: "Build a project management dashboard with a sidebar navigation, a task list with drag-and-drop reordering, a calendar view, and real-time notifications. Use React, Tailwind CSS, Framer Motion for animations, and Zustand for state management. Include mock data for demonstration."

### Step 3: Monitor and Wait
Poll the status with the run_id every 30 seconds. The foreman phase takes ~30-60 seconds. The worker phase generates files sequentially at ~10-30 seconds per file. A typical 10-file app completes in 2-5 minutes.

### Step 4: Assess Quality
Run factory_assess on the completed output. Review the score and issues list. Common issues: missing package.json, broken imports, syntax errors, placeholder content. Address critical issues (score below 70) by refining the prompt and regenerating.

### Step 5: Manual Refinement
Open the output directory and manually fix any issues identified in the assessment. Add missing imports, fix syntax errors, replace placeholder content with real implementation. The factory generates a solid foundation but may need human polish.

### Step 6: Launch and Test
Use the launch operation to start the dev server. Open the app in the browser. Test core functionality manually. If issues are found, fix them directly in the output files and restart the dev server.

### Step 7: Export to Production
Copy the refined output to your main project repository. Replace mock data with real API integration. Add authentication, error handling, and production configuration. The generated app serves as a high-fidelity prototype that accelerates development.

## Performance Optimization
For faster generation, use smaller models (3B-7B parameters) for the worker role. Process more complex apps by splitting the vibe into multiple smaller generation runs. The foreman model benefits from more context — include specific file structure examples in your vibe description. For batch generation, run multiple factory instances with different configuration (separate Python processes, different output directories). The token usage tracking helps estimate LLM API costs when using cloud endpoints.

## Troubleshooting: Common Generation Failures

### Model Not Found
Error: "Connection refused" or model name not recognized. Solution: pull the model in Ollama first: `ollama pull <model-name>`. Verify with `ollama list`.

### Generation Hangs at Plan Phase
The foreman model may be too small or the vibe description too vague. Solution: provide more specific instructions in the vibe, including tech stack, file structure, and component names. Switch to a larger foreman model.

### Generated App Has No Entry Point
The worker model may not have generated index.html, package.json, or main.py. Solution: explicitly mention the expected entry point in the vibe description. The assessment will detect the missing entry point and score accordingly.

### Syntax Errors in Generated Code
The worker model may produce invalid JavaScript/Python syntax. Solution: use a code-specialized model (qwen2.5-coder, deepseek-coder). Increase worker temperature slightly (0.3) for more variation. Include explicit syntax requirements in the vibe.

### Vite Error Overlay After Launch
The generated app may have missing dependencies or incorrect import paths. Solution: run `cd output_dir && npm install` to install dependencies. Check import paths in the generated files. Use the audit results to identify the specific errors.

## Generation Prompt Engineering
The quality of generated applications depends critically on the vibe description. Effective prompts include: a one-sentence summary of what the app does, the specific tech stack requirements (React 18, Vite, Tailwind CSS, Framer Motion, Zustand), the component tree and layout (sidebar with navigation, main content area with data table, footer with status bar), user interaction patterns (click to expand, drag to reorder, type to search), data flow and state management (Zustand store with actions and selectors, mock data generator), visual style guidance (dark theme with slate backgrounds and amber accents, glassmorphism for modals), performance requirements (virtualized list for 10000+ items, lazy loading for images), and error and edge case handling (loading skeletons, empty state, error boundaries). Including a ## Tech Stack section explicitly signals framework choices to the foreman model. The foreman model generates better architecture plans when given constraints — specifying the number of components, file organization strategy, and data flow pattern improves output quality significantly. The worker model produces better code when the vibe includes example file contents or specific API usage patterns.

## Model Selection Guide
Choosing the right models for generation depends on your hardware and quality requirements. For best quality on high-end GPUs (24GB+ VRAM): foreman=llama3.1:70b, worker=qwen2.5-coder:32b. For good quality on mid-range GPUs (12-16GB VRAM): foreman=llama3.1:8b, worker=qwen2.5-coder:14b or deepseek-coder:16b. For acceptable quality on lower-end GPUs or CPU: foreman=llama3.2:3b or gemma2:9b, worker=phi3:14b or starcoder2:15b. For fast iteration on any hardware: foreman=llama3.2:1b or tinyllama:1.1b, worker=qwen2.5-coder:1.5b or deepseek-coder:1.3b. Code-specialized models (qwen2.5-coder, deepseek-coder, starcoder2, phi3) produce significantly better code quality than general-purpose models of equivalent size. The foreman model benefits from larger context windows for complex app descriptions. Always pull the desired models in Ollama before running the factory: ollama pull model-name.

## Assessment Score Interpretation
The factory_assess composite score ranges from 0 to 100 and is interpreted as follows. Scores 90-100 (Grade A): excellent generation with proper entry points, valid syntax, meaningful filenames, complete component structure, correct import paths, and no placeholder content. These apps are production-viable with minimal human polish. Scores 80-89 (Grade B): good generation with minor issues such as one or two missing imports, a placeholder text in one component, or slightly awkward naming. These apps need a few minutes of human refinement. Scores 70-79 (Grade C): adequate generation with several issues including multiple syntax errors, missing entry points, or several placeholder files. These apps need significant manual correction — consider regenerating with a refined prompt. Scores 60-69 (Grade D): poor generation with major structural problems. The generated files may be incomplete, have critical syntax errors, or lack essential components. Regenerate with a more specific prompt or use a larger worker model. Scores 0-59 (Grade F): the generation failed basic validation checks. Common causes: empty output directory, no recognizable entry points, Python/JavaScript parse errors in most files, or placeholder-only content. Investigate the console logs and retry with different models or prompt.

## Environment Configuration Guide
The dark-app-factory uses environment variables for all configuration. Create a .env file in the repo root with FOREMAN_MODEL=llama3.2:3b for quick iteration with a small model, or FOREMAN_MODEL=llama3.1:70b for high-quality planning. The WORKER_MODEL defaults to qwen2.5-coder:latest — a 7B code-specialized model that produces high-quality JavaScript and Python. For GPU-constrained systems, use WORKER_MODEL=deepseek-coder:1.3b for faster but lower-quality code. The FOREMAN_BASE_URL and WORKER_BASE_URL default to http://localhost:11434/v1 (Ollama). For LM Studio, change to http://localhost:1234/v1. For OpenAI, set FOREMAN_BASE_URL=https://api.openai.com/v1 with a valid API key. The temperature parameters are set per-role: foreman (0.7 for creative planning) and worker (0.2 for deterministic coding). The factory logs token usage for cost tracking when using paid API endpoints.

## Batch Generation Workflow
For generating multiple related components, use a batch strategy: start with a system architecture vibe that generates the app skeleton and entry points. Then generate individual components one at a time with focused vibes describing each component's specific requirements. Assemble the components into the skeleton manually or via a manifest file. This approach produces higher quality results than generating the entire app in one pass because each component gets focused attention from the worker model. Use the assessment tool on each component independently before integration. For large applications, consider generating the data layer first (models, stores, API clients), then the UI layer (components, pages, layouts), then integration layer (routing, state management wiring, event handling). The factory outputs each generation to a separate directory — use the download and copy operations to assemble the final app.

## Advanced Assessment and Debugging
When a generated app scores below 70 on assessment, investigate the specific issues. Syntax errors: read the error message and line number, check for missing brackets, semicolons, or parentheses — the worker model may have been truncated mid-expression. Missing imports: check which modules are imported in package.json/requirements.txt versus which are referenced in the code. Placeholder content: search for "TODO", "Lorem", "example", "function_name", "ComponentName" in the generated files. Broken framer-motion imports: verify the import path uses "framer-motion" not "motion" or "framer". Entry point missing: check for index.html, main.tsx, App.tsx, or main.py depending on the framework. For persistent quality issues, try a larger worker model, add more specific file structure examples to the vibe, reduce the scope of the generation (fewer components per run), or manually fix the identified issues and regenerate only the problematic files.

## Real-World Use Cases and Examples
The factory has been used to generate a variety of applications. A common use case is prototyping internal dashboards: describe the data sources, chart types, and layout, and the factory generates a functional dashboard with mock data. Another use case is generating landing pages for marketing campaigns: specify the brand colors, messaging, sections, and call-to-action, and the factory produces a polished landing page. For developer tools, describe the tool functionality and the factory generates a working CLI or UI tool. For educational content, describe the learning objective and the factory generates an interactive tutorial or quiz app. For design exploration, generate multiple variations of a UI component with different layouts and styling to compare before committing to implementation. The factory shines when the goal is to go from idea to functional prototype in minutes rather than hours.

## Uninstallation and Cleanup
To remove the factory, delete the repository and its outputs directory. The outputs directory contains all generated apps — back up any you want to keep before deletion. The ghost blueprints are stored in the ghosts/ directory. Audit screenshots are in audit_results/. The virtual environment (.venv) can be deleted independently. No system-wide installations are made. No background processes or services are created.

## Troubleshooting Common Generation Issues
When generation fails or produces poor quality, check these common causes. The foreman model generates a plan but the worker produces no files: the worker model may be too small or the plan too complex — reduce scope or use a larger worker. Generation produces only placeholder files: the worker model needs more specific instructions in the vibe — include example file contents. Generation produces files with incorrect syntax: the worker model may not be code-specialized — use qwen2.5-coder or deepseek-coder. Generation is very slow: the model may be running on CPU — check GPU utilization with nvidia-smi. Generation crashes mid-way: the model may have hit its context limit — reduce the vibe description length. Assessment score is low but the app looks functional: the assessment may be flagging false positives — check each issue manually. The factory generates different results each run: this is expected due to LLM temperature — run multiple generations and select the best.

## Environment Variable Reference
Complete list of configuration environment variables: FOREMAN_MODEL (default llama3.1:latest), FOREMAN_BASE_URL (default http://localhost:11434/v1), FOREMAN_API_KEY (default ollama), WORKER_MODEL (default qwen2.5-coder:latest), WORKER_BASE_URL (default http://localhost:11434/v1), WORKER_API_KEY (default ollama), OPENAI_API_KEY (fallback for both roles when FOREMAN_API_KEY and WORKER_API_KEY are not set), OPENAI_BASE_URL (fallback for both roles), DAF_PORT or MCP_PORT (default 10738), DAF_HOST (default 127.0.0.1), DAF_WEB_BASE (web dashboard URL for pushing assessment results). All variables are optional. The factory works with default local Ollama configuration. For cloud API integration, set the model, base URL, and API key for each role independently.

## Security Considerations
The factory operates with local Ollama models by default, meaning no data leaves your machine. When using cloud API endpoints (OpenAI, Anthropic), the vibe descriptions and generated code are sent to the API provider. Do not include sensitive information (credentials, API keys, personal data) in vibe descriptions when using cloud providers. Generated code may contain security issues — always review generated apps for common vulnerabilities (XSS, CSRF, injection) before production deployment. The factory does not implement authentication — restrict access to trusted networks. The output directory contains all generated files with no encryption — protect sensitive outputs appropriately. The audit assessment does not perform security analysis — use dedicated security scanning tools for production-ready code.

## Framework-Specific Generation Tips
For React apps, always specify React 18 with Vite as the build tool in the vibe description. Include the component hierarchy and props interface for complex components. For Vue apps, specify the composition API (script setup) for modern patterns. Include store structure if using Pinia. For Python apps, specify the framework (Flask, FastAPI, Django) and include routing patterns. For landing pages, focus on sections (hero, features, testimonials, pricing, FAQ, footer) with specific copy and image placeholders. For dashboards, describe the data points, chart types, and layout grid explicitly. For forms, specify fields, validation rules, and submission behavior. For data visualizations, mention the charting library (Chart.js, D3, Recharts, etc.) and the data shape. For mobile-responsive designs, explicitly state the breakpoint behavior. The worker model generates more idiomatic code when you specify the exact packages and versions in the vibe.

## Template Presets
The factory can be configured with preset vibe templates for common application types. A dashboard preset might include: "Build an admin dashboard with React 18, Vite, Tailwind CSS, Recharts for charts, and Zustand for state. Include a sidebar with navigation links to Dashboard, Analytics, Users, Settings pages. Use a dark theme with slate backgrounds and blue accents. Include mock data generators for each page." A landing page preset might include: "Build a modern landing page with Next.js 14 and Tailwind CSS. Include a hero section with headline and CTA button, features grid with icons, testimonials carousel, pricing table with three tiers, FAQ accordion, and footer with social links. Use a light theme with white backgrounds and indigo accents." These presets can be saved and reused to speed up generation of similar applications.

## Collaboration Workflow
The factory supports multi-person collaboration on generated apps. One person describes the vision in the vibe description, generating the initial app. A reviewer runs factory_assess to evaluate quality. They collaborate on refinements by editing the generated files or regenerating with improved prompts. The generated outputs can be shared via the depot-mcp or committed to a shared repository. The assessment score provides an objective quality metric. The output directory contains all generated files in a standard structure — use your existing collaboration tools (git, shared drives, cloud storage) to work on the generated code collaboratively. The factory itself does not implement multi-user features — collaboration happens around the generated output files.

## Troubleshooting Model Issues
When models fail to load or respond, check these common issues. Connection refused: Ollama is not running — start with ollama serve in a terminal. Model not found: the model name is incorrect or not pulled — run ollama list to see available models and ollama pull <name> to download. GPU out of memory: the model is too large for your GPU VRAM — use a smaller model or enable Ollama's GPU offloading configuration. Slow generation: the model is running on CPU instead of GPU — check that Ollama is using the GPU (ollama ps shows the model running) and that you have the appropriate GPU drivers installed. Truncated output: the model's context window is too small for your prompt — reduce the vibe description length or use a model with a larger context window. Empty response: the model generated nothing — check for timeout errors in the logs and retry with a shorter prompt. Repeated content: the model is stuck in a loop — reduce the temperature or switch to a different model.

## Customizing the Factory
The factory can be customized through configuration and code. To add a new output format (e.g., Svelte, SolidJS, Qwik), create a new template in the generation pipeline that instructs the worker model to use the target framework. To add custom assessment criteria, extend the assessment function in auditor.py with new scoring dimensions. To add a new LLM provider, extend the LLMClient class with a new provider adapter. To add post-generation processing (e.g., auto-formatting, linting, minification), add a pipeline stage after file generation that runs the processing tools. To add deployment integration, create a pipeline stage that packages the output and deploys it to a target environment (Netlify, Vercel, Docker, local server). The factory is designed to be extensible — each stage (parse, plan, generate, assess, deploy) is an independent module that can be replaced or extended.

## Output Directory Structure
Generated apps follow a consistent directory structure. For React/Vite apps: output_name/index.html (entry point), output_name/src/main.tsx or output_name/src/App.tsx (React root), output_name/src/components/ (React components), output_name/src/styles/ (CSS files), output_name/package.json (dependencies and scripts), output_name/vite.config.ts (Vite configuration), output_name/tsconfig.json (TypeScript config when applicable). For Python/Flask apps: output_name/main.py or output_name/app.py (entry point), output_name/templates/ (HTML templates), output_name/static/ (static assets), output_name/requirements.txt (Python dependencies). The factory creates these directories automatically. If a generated app is missing expected files, check the vibe description for completeness and the worker model for quality. The assessment tool checks for the presence of standard entry points and reports missing files in the issues list.

## Best Practices for Vibe Descriptions
The quality of generated apps depends heavily on the vibe description. Follow these best practices: be specific about the tech stack (framework, styling, state management), describe the layout and component structure, mention data sources and how data flows through the app, specify any user interactions (clicks, drags, keyboard shortcuts), include examples of desired behavior, mention error states and edge cases, describe the visual style and theme, and list any dependencies the app should use. Bad example: "Make a dashboard." Good example: "Build a project management dashboard with React 18, Vite, Tailwind CSS, and Framer Motion. Include a collapsible sidebar with navigation links, a main content area with a task list, a kanban board view, a calendar, and a settings page. Use Zustand for state management with mock data stored in a local JSON file. The theme should be dark with amber accents following the fleet Slate/Amber design system."

## Performance Tuning for Different Hardware
On an RTX 4090 (24GB VRAM), use 13B-70B models for both foreman and worker roles for the best generation quality. On an RTX 3090 (24GB VRAM), 8B-13B models provide a good balance of speed and quality. On an RTX 3060 (12GB VRAM), use 3B-7B models for reasonable generation times. On CPU-only systems, use 1B-3B models with Ollama — generation will be slower (5-10x) but functional. For batch generation, consider running factory instances in parallel with different model configurations on multi-GPU systems. For cloud API usage, monitor token consumption with get_usage() and set appropriate rate limits in the OpenAI dashboard.

## REST API Endpoints Reference

### MCP HTTP Transport
POST /mcp — JSON-RPC messages for tool calls. Accepts {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "...", "arguments": {...}}}.

### Health
GET /health — Returns {"status": "ok", "service": "dark-app-factory"}.

### Web Dashboard
The Vite React dashboard on port 10739 provides visual access to all factory operations. It displays generation history, output file trees, assessment results as scored cards, and log tailing. The dashboard auto-refreshes during active generation.

## FAQ

**Q: What models should I use for generation?**
A: For architecture planning use a larger model (llama3.1:8b+). For code generation use a code-specialized model (qwen2.5-coder, deepseek-coder). Both should be pulled in Ollama first.

**Q: Can I use OpenAI instead of Ollama?**
A: Yes. Set FOREMAN_BASE_URL and WORKER_BASE_URL to OpenAI's API endpoint, and set the API keys accordingly.

**Q: How long does generation take?**
A: Depends on model size and app complexity. Small apps with a 3B model take 30-60 seconds. Larger apps with 8B+ models can take 2-5 minutes.

**Q: Can I generate non-React apps?**
A: Yes. Specify in the vibe description. The foreman model will plan accordingly. Python/Flask, vanilla JS, Vue, and Svelte are all supported.

**Q: Does the factory install npm dependencies?**
A: No. It generates source files only. Run `npm install` in the output directory before launching.

**Q: Where are generated apps stored?**
A: In the outputs/ directory at the repo root. Each generation gets its own subdirectory.

**Q: Can I run multiple generations simultaneously?**
A: No. The factory is single-threaded per role. However, you can queue runs by calling run multiple times — they will execute sequentially.

**Q: What does the assessment score mean?**
A: A=90-100 (excellent, production-viable), B=80-89 (good, minor issues), C=70-79 (adequate, several issues), D=60-69 (poor, major issues), F=0-59 (fails basic checks, likely non-functional).
