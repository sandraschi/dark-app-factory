import argparse
import asyncio
import json
import sys
# ruff: noqa: E402
import os

# Normalize import paths: ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if os.path.join(BASE_DIR, "src") not in sys.path:
    sys.path.insert(1, os.path.join(BASE_DIR, "src"))

from src.utils.logger import logger
from src.llm_client import LLMClient
from src.utils.help_oracle import oracle
from src.utils.stack_profile import (
    parse_stack_from_vibe,
    embed_in_specs,
    describe_stack,
)


def read_vibe(path: str = "vibe.md") -> str:
    if not os.path.exists(path):
        logger.error(f"Vibe file not found at {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_file_if_exists(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# =====================================================================
# ENRICH: LLM-augmented vibe expansion
# =====================================================================
async def enrich_vibe(
    vibe_path: str = "vibe.md",
    output_path: str = "enriched_vibe.md",
    foreman: LLMClient = None,
):
    """Read a terse vibe and use the Foreman LLM to expand it into a rich,
    domain-aware brief. The user reviews and approves before proceeding to plan.
    """
    vibe_content = read_vibe(vibe_path)
    logger.info("Enriching vibe with LLM domain expansion...")
    logger.debug("Input vibe: %d chars", len(vibe_content))

    if not foreman:
        foreman = LLMClient(role="foreman")

    enrich_prompt = f"""
    You are the Vibe Enricher for the Dark App Factory.

    The user has given you a terse, informal description of the app they want.
    Your job is to EXPAND this into a rich, structured vibe document that a
    software factory can act on.

    INPUT VIBE:
    ---
    {vibe_content}
    ---

    YOUR TASK:
    1. **Identify the Domain**: What industry/profession is this for? What are
       the professional standards, regulations, and terminology?
    2. **Expand Features**: Based on the domain, suggest concrete features the
       user likely needs but did not mention. Think like a domain expert.
       Examples:
       - A dentist app needs: appointment booking, patient records (GDPR!),
         treatment plans, X-ray viewer integration, insurance billing codes.
       - A beekeeper app needs: hive health monitoring, swarm calendar,
         queen tracking, harvest logging, webshop for honey/products,
         weather integration, apiary map.
       - An MCP + webapp for controlling a Windows app (VLC, 7-Zip, etc.) needs:
         FastMCP tools mirroring control actions, shared service layer (subprocess),
         FastAPI routes for the webapp, pyproject.toml + PyPI packaging.
    3. **Suggest Tech Integrations**: What real-world APIs or services would
       make this app genuinely useful? (e.g., payment gateway, calendar sync,
       weather API, camera feeds, notification services)
    4. **Propose a Name/Brand**: Suggest a catchy domain name or brand that
       fits the user's locale and language.
    5. **Identify Pages/Views**: List the distinct screens/pages the app needs.
    6. **Business Logic**: Describe at least 2 multi-step workflows.
    7. **Preserve the original vibe**: Keep the user's voice and intent.
       Do NOT contradict what they explicitly stated.

    OUTPUT FORMAT:
    Write an enriched vibe.md in Markdown. Keep the original "## Tech Stack"
    section if present (or suggest one). Mark your additions with
    "[ENRICHED]" so the user can easily review what you added vs. what they wrote.

    Be specific and concrete. No generic filler. Think like a domain consultant
    who actually understands the user's business.
    """

    enriched = await foreman.generate(
        enrich_prompt,
        system_prompt=(
            "You are a domain expansion expert. You turn vague app ideas into "
            "rich, actionable briefs. Output ONLY the enriched Markdown document."
        ),
        temperature=0.6,
    )

    if not enriched:
        logger.error("LLM enrichment failed -- check Ollama connectivity.")
        return

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(enriched)

    logger.success("Enriched vibe written to: %s", output_path)
    logger.info(
        "NEXT STEP: Review %s, edit as needed, then run:\n"
        "  python foreman.py plan --vibe %s",
        output_path,
        output_path,
    )


# =====================================================================
# PLAN: Generate specs + scenarios from vibe
# =====================================================================
async def generate_blueprint(vibe_content: str, foreman: LLMClient = None):
    logger.info("Foreman is analyzing the vibe...")
    logger.debug(f"Input length: {len(vibe_content)} chars")

    # Parse stack profile from vibe
    stack_profile = parse_stack_from_vibe(vibe_content)
    stack_desc = describe_stack(stack_profile)
    logger.info("Resolved stack: %s", stack_desc)

    if not foreman:
        foreman = LLMClient(role="foreman")

    # 1. Generate Specs
    system_prompt_specs = """You are the Foreman of a Dark App Factory.
Your job is to take a loose 'vibe' (user intent) and turn it into rigorous, implementable software specifications.
You must be precise, reductionist, and exhaustive. No fluff.
Focus on:
- Core Data Models
- API Endpoints
- State Machines
- Necessary 3rd Party Integrations (Identify where Digital Twins are needed)

Output format: Markdown."""

    # Load historical feedback/critique and research
    feedback = read_file_if_exists("feedback.md")
    critique = read_file_if_exists("critique.md")
    research = read_file_if_exists("specs/research.md")

    historical_context = ""
    if feedback or critique:
        historical_context = f"""
        ### PREVIOUS FAILURES (FIX THESE FIRST)
        FEEDBACK:
        {feedback}
        
        CRITIQUE:
        {critique}
        
        CRITICAL: The previous build failed. You MUST address every issue mentioned above in the new specs. 
        If the user wants a 'Store', ensure the store logic and routing are EXPLICITLY defined.
        If 'Login' was incomplete, specify the EXACT validation and API requirements.
        """

    research_context = ""
    if research:
        research_context = f"""
        ### DOMAIN RESEARCH (ORACLE DATA)
        {research}
        
        CRITICAL: Use the latest 2026 domain data above for all terminology, standards, and features. 
        Do NOT use generic or dated information.
        """

    specs_prompt = f"""
    The User wants this app:
    ---
    {vibe_content}
    ---
    
    {historical_context}
    
    {research_context}
    
    TECH STACK (from user's vibe):
    {stack_desc}
    
    Generate a rigorous, production-grade `specs.md`.
    
    CRITICAL QUALITY REQUIREMENTS:
    1.  **Architecture**: Must use the tech stack specified above: {stack_desc}.
        - Generate all code, models, and APIs using the specified backend language/framework.
        - Generate frontend using the specified frontend framework (or skip if "none").
    2.  **UI/UX Richness** (ONLY if frontend is NOT "none"):
        -   Define at least **4 distinct functional views/pages**.
        -   Specify interactive elements (Modals, Forms with validation, Sorting/Filtering).
        -   Identify complex UI states (Loading spinners, "Empty State" illustrations, Error toast messages).
        -   If frontend is plain JS/HTML (not React): define standard HTML pages, NO JSX/TSX/React components.
    3.  **Deep Business Logic**:
        -   Describe a core multi-step workflow (e.g., "Create Asset" -> "Queue for Processing" -> "Notify User").
        -   Define internal data transformation logic (e.g., "Calculate ROI based on tax brackets").
    4.  **Database & API**:
        -   **Database Schema**: Detailed table definitions including indexes and cascading deletes.
        -   **API Reference**: Exhaustive list of RESTful routes with JSON request/response examples.
    5.  **Documentation (MANDATORY)**:
        -   Provide a complete, multi-section template for the final `README.md`.
        -   Include specific instructions for "First Time Setup" and "Digital Twin Integration".
    
    Output format: Detailed Markdown.
    """

    logger.info("Generating Specs...")
    specs = await foreman.generate(specs_prompt, system_prompt=system_prompt_specs)
    if specs:
        # Embed stack profile as HTML comment at top of specs
        specs = embed_in_specs(specs, stack_profile)
        os.makedirs("specs", exist_ok=True)
        with open("specs/specs.md", "w", encoding="utf-8") as f:
            f.write(specs)
        logger.success("Specs Generated -> specs/specs.md")
    else:
        logger.error("Failed to generate specs.")
        return  # Abort if specs fail

    # 2. Generate Scenarios
    system_prompt_scenarios = """You are the QA Lead of a Dark App Factory.
Your job is to take software specifications and generate exhaustive user scenarios for testing.
These scenarios will be run by the 'Satisficer' (AI Judge) against the running app.
Focus on:
- Happy Paths
- Edge Cases
- Error States
- Security Boundaries

Output format: Markdown checklist."""

    scenarios_prompt = f"""
    Here are the specs for the application:
    ---
    {specs}
    ---
    
    Generate a `scenarios.md` file containing a list of testable user stories.
    
    FORMAT each scenario EXACTLY as:
    - [ ] **Title**: Description
      - GIVEN: Context
      - WHEN: Action (use "Submit a GET/POST/PUT/DELETE request to \`/path\`" for API scenarios)
      - THEN: Expected Result (include status codes when relevant, e.g. "A 404 Not Found error is returned")
    
    PREFER standard flows from these domains when the app matches:
    - E-commerce: registration, login, product list, add to cart, checkout, orders. Use paths like /products, /cart, /orders.
    - SaaS auth: signup, verify email, login, logout, forgot/reset password, protected endpoints. Use paths like /api/auth/*.
    - CRUD resources: create, list, get by ID, update, delete, validation errors. Use GIVEN/WHEN/THEN format.
    
    The Satisficer parses WHEN clauses to run real HTTP requests. Ensure WHEN lines match:
    "Submit a POST request to \`/users\` with valid JSON payload." or "Submit a GET request to \`/products\`."
    """

    logger.info("Generating Scenarios...")
    scenarios = await foreman.generate(
        scenarios_prompt, system_prompt=system_prompt_scenarios
    )

    if scenarios:
        os.makedirs("scenarios", exist_ok=True)
        with open("scenarios/scenarios.md", "w", encoding="utf-8") as f:
            f.write(scenarios)
        logger.success("Scenarios Generated -> scenarios/scenarios.md")
    else:
        logger.error("Failed to generate scenarios.")


# =====================================================================
# RESEARCH: Generate search queries for domain data
# =====================================================================
async def conduct_research(vibe_content: str, foreman: LLMClient = None):
    logger.info("Oracle is preparing research queries...")

    if not foreman:
        foreman = LLMClient(role="foreman")

    research_prompt = f"""
    You are the Domain Research Oracle. 
    Analyze this application 'vibe' and generate 5 precise, SOTA (State of the Art) search queries to gather relevant domain data.
    Think about:
    1.  **Standards/Regulations**: What are the current legal or professional requirements for this field in 2026?
    2.  **Top Features**: What do premium competitors in this niche offer today?
    3.  **Regional Context**: If the vibe mentions a location, include it.
    4.  **Terminology**: What are the professional terms used in this industry?
    
    Vibe: {vibe_content}
    
    Output ONLY a JSON list of strings.
    Example: ["modern dental coding standards 2026", "urology clinic patient portal features"]
    """

    logger.info("Generating Search Queries...")
    queries_json = await foreman.generate(
        research_prompt, system_prompt="You are the Oracle. Output ONLY valid JSON."
    )

    try:
        queries = json.loads(queries_json)
        os.makedirs("specs", exist_ok=True)
        with open("specs/queries.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(queries, indent=2))
        logger.success("Research Queries queued -> specs/queries.json")
        logger.warning(
            "AGENT ACTION REQUIRED: Execute these queries using search_web and save to specs/research.md"
        )
    except Exception as e:
        logger.error(f"Failed to parse research queries: {e}")
        logger.debug(queries_json)


# =====================================================================
# CLI Entry Point
# =====================================================================
def main():
    parser = argparse.ArgumentParser(description="Dark App Factory Foreman")
    subparsers = parser.add_subparsers(dest="command")

    # Enrich command (NEW)
    enrich_parser = subparsers.add_parser(
        "enrich",
        help="LLM-augment the vibe with domain expertise -> enriched_vibe.md",
    )
    enrich_parser.add_argument("--vibe", default="vibe.md", help="Path to vibe file")
    enrich_parser.add_argument(
        "--output", default="enriched_vibe.md", help="Output path for enriched vibe"
    )

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Generate blueprint from vibe")
    plan_parser.add_argument("--vibe", default="vibe.md", help="Path to vibe file")

    # Research command
    research_parser = subparsers.add_parser(
        "research", help="Generate domain research queries"
    )
    research_parser.add_argument("--vibe", default="vibe.md", help="Path to vibe file")

    # Help Command (Multilevel)
    help_parser = subparsers.add_parser("help", help="Query the Help Oracle")
    help_parser.add_argument(
        "--level",
        default="basic",
        choices=["basic", "intermediate", "advanced", "expert"],
        help="Help detail level",
    )
    help_parser.add_argument("--topic", help="Specific topic to query")

    # Log Command
    log_parser = subparsers.add_parser("log", help="Manage factory logs")
    log_parser.add_argument("--tail", type=int, help="Tail the last N lines of the log")
    log_parser.add_argument(
        "--export", action="store_true", help="Export logs to a zip file"
    )

    args = parser.parse_args()

    if args.command == "enrich":
        asyncio.run(enrich_vibe(args.vibe, args.output))
    elif args.command == "plan":
        vibe = read_vibe(args.vibe)
        asyncio.run(generate_blueprint(vibe))
    elif args.command == "research":
        vibe = read_vibe(args.vibe)
        asyncio.run(conduct_research(vibe))
    elif args.command == "help":
        help_content = oracle.get_help(level=args.level, topic=args.topic)
        logger.info("Help Oracle - %s:\n%s", args.level.upper(), help_content)
    elif args.command == "log":
        if args.tail:
            lines = logger.tail(args.tail)
            for line in lines:
                logger.info(line.strip())
        elif args.export:
            zip_path = logger.export()
            logger.success(f"Logs exported to: {zip_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
