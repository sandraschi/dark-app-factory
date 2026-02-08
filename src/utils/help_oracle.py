class HelpOracle:
    """Multilevel Help System for the Dark App Factory."""

    LEVELS = ["basic", "intermediate", "advanced", "expert"]

    DOCS = {
        "basic": {
            "summary": "Core CLI usage for rapid application factory operations.",
            "commands": {
                "foreman plan": "Analyzes vibe.md and generates specs and scenarios.",
                "worker build": "Executes the spec to generate application code.",
                "judge judge": "Performs execution-based verification of the generated app.",
                "help": "Displays this help oracle. Use --level to go deeper.",
            },
        },
        "intermediate": {
            "summary": "Specialist Council and Dependency Management.",
            "specialists": {
                "Sculptor": "React/Frontend aesthetics and UI logic.",
                "Plumber": "Backend architecture, APIs, and DB integration.",
                "Auditor": "Logical verification and data parsing specialists.",
                "Council": "Dependency-aware parallel execution levels (e.g., Level 0: Plumber -> Level 1: Sculptor).",
            },
            "environment": "Configuration via .env (LLM endpoints, base URLs, roles).",
        },
        "advanced": {
            "summary": "Deep Architecture and Custom Specialists.",
            "internals": {
                "Deep-Crawl": "Recursive code scanning logic in worker.py.",
                "Context Hardening": "50k character spec injection system.",
                "Satisficer (QA)": "Execution-based judging using Playwright.",
            },
            "extending": "Creating new specialists in src/specialists/council.py.",
        },
        "expert": {
            "summary": "SOTA/DTU Signaling and System Diagnostics.",
            "dtu": "Digital Twin Universe signaling via Socket.io / OSC.",
            "hot-tail": "Real-time log streaming from production endpoints.",
            "benchmarking": "Latency and token efficiency optimization for locally hosted Workers.",
        },
    }

    def get_help(self, level="basic", topic=None):
        if level not in self.LEVELS:
            level = "basic"

        content = self.DOCS.get(level, {})

        if topic:
            # Topic-specific search logic could go here
            return f"Topic '{topic}' help not implemented yet. Showing {level} overview:\n{content}"

        return content


# Global instance
oracle = HelpOracle()
