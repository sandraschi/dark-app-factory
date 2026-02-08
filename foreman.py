import argparse
import sys
import os
from utils.logger import logger

# Add src to path if needed or structure correctly
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from llm_client import LLMClient
from utils.help_oracle import oracle
from utils.stack_profile import (
    parse_stack_from_vibe,
    embed_in_specs,
    describe_stack,
)


def read_vibe(path: str = "vibe.md") -> str:
    if not os.path.exists(path):
        logger.error(f"Vibe file not found at {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_file_if_exists(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def generate_blueprint(vibe_content: str):
    logger.info("Foreman is analyzing the vibe...")
    logger.debug(f"Input length: {len(vibe_content)} chars")

    # Parse stack profile from vibe
    stack_profile = parse_stack_from_vibe(vibe_content)
    stack_desc = describe_stack(stack_profile)
    logger.info("Resolved stack: %s", stack_desc)

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
    2.  **UI/UX Richness** (if frontend is specified):
        -   Define at least **4 distinct functional views/pages** (e.g., Dashboard, Asset List, Detail View, User Profile, Settings).
        -   Specify interactive elements (Modals, Forms with validation, Sorting/Filtering).
        -   Identify complex UI states (Loading spinners, "Empty State" illustrations, Error toast messages).
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
    specs = foreman.generate(specs_prompt, system_prompt=system_prompt_specs)
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
    Format each scenario with:
    - [ ] **Title**: Description
      - GIVEN: Context
      - WHEN: Action
      - THEN: Expected Result
    """

    logger.info("Generating Scenarios...")
    scenarios = foreman.generate(
        scenarios_prompt, system_prompt=system_prompt_scenarios
    )

    if scenarios:
        os.makedirs("scenarios", exist_ok=True)
        with open("scenarios/scenarios.md", "w", encoding="utf-8") as f:
            f.write(scenarios)
        logger.success("Scenarios Generated -> scenarios/scenarios.md")
    else:
        logger.error("Failed to generate scenarios.")


def conduct_research(vibe_content: str):
    logger.info("Oracle is preparing research queries...")

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
    queries_json = foreman.generate(
        research_prompt, system_prompt="You are the Oracle. Output ONLY valid JSON."
    )

    try:
        import json

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


def main():
    parser = argparse.ArgumentParser(description="Dark App Factory Foreman")
    subparsers = parser.add_subparsers(dest="command")

    plan_parser = subparsers.add_parser("plan", help="Generate blueprint from vibe")
    plan_parser.add_argument("--vibe", default="vibe.md", help="Path to vibe file")

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

    if args.command == "plan":
        vibe = read_vibe(args.vibe)
        generate_blueprint(vibe)
    elif args.command == "research":
        vibe = read_vibe(args.vibe)
        conduct_research(vibe)
    elif args.command == "help":
        help_content = oracle.get_help(level=args.level, topic=args.topic)
        logger.info("Help Oracle - %s:\n%s", args.level.upper(), help_content)
    elif args.command == "log":
        from utils.logger import logger

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
