"""
Stack profile parsing and defaults for the Dark App Factory.

The stack profile determines what languages/frameworks the factory generates.
It is declared explicitly in vibe.md under a '## Tech Stack' section and
embedded as a STACK_PROFILE HTML comment in specs.md by the Foreman.
"""

import json
import logging
import re

logger = logging.getLogger("dark_factory")

DEFAULT_STACK = {
    "backend": "node/express",
    "frontend": "react",
    "database": "sqlite",
}

VALID_BACKENDS = {
    "node/express",
    "python/fastapi",
    "python/flask",
    "python/django",
}
VALID_FRONTENDS = {
    "react",
    "htmx",
    "svelte",
    "none",
}
VALID_DATABASES = {
    "sqlite",
    "postgresql",
    "mongodb",
    "mysql",
}


def parse_stack_from_vibe(vibe_content: str) -> dict[str, str]:
    """
    Extract stack profile from vibe.md Tech Stack section.
    Falls back to DEFAULT_STACK for any missing or invalid values.

    Expected format in vibe.md:
        ## Tech Stack
        - **Backend**: python/fastapi
        - **Frontend**: react
        - **Database**: postgresql
    """
    profile = dict(DEFAULT_STACK)

    backend_match = re.search(r"\*\*Backend\*\*:\s*(\S+)", vibe_content, re.IGNORECASE)
    if backend_match:
        val = backend_match.group(1).strip().lower()
        if val in VALID_BACKENDS:
            profile["backend"] = val
        else:
            logger.warning(
                "Unknown backend '%s' in vibe. Valid: %s. Using default: %s",
                val,
                VALID_BACKENDS,
                DEFAULT_STACK["backend"],
            )

    frontend_match = re.search(r"\*\*Frontend\*\*:\s*(\S+)", vibe_content, re.IGNORECASE)
    if frontend_match:
        val = frontend_match.group(1).strip().lower()
        if val in VALID_FRONTENDS:
            profile["frontend"] = val
        else:
            logger.warning(
                "Unknown frontend '%s' in vibe. Valid: %s. Using default: %s",
                val,
                VALID_FRONTENDS,
                DEFAULT_STACK["frontend"],
            )

    db_match = re.search(r"\*\*Database\*\*:\s*(\S+)", vibe_content, re.IGNORECASE)
    if db_match:
        val = db_match.group(1).strip().lower()
        if val in VALID_DATABASES:
            profile["database"] = val
        else:
            logger.warning(
                "Unknown database '%s' in vibe. Valid: %s. Using default: %s",
                val,
                VALID_DATABASES,
                DEFAULT_STACK["database"],
            )

    logger.info(
        "Stack profile: backend=%s frontend=%s database=%s",
        profile["backend"],
        profile["frontend"],
        profile["database"],
    )
    return profile


def embed_in_specs(specs_content: str, profile: dict[str, str]) -> str:
    """Prepend a STACK_PROFILE HTML comment to specs content."""
    tag = f"<!-- STACK_PROFILE: {json.dumps(profile)} -->\n\n"
    return tag + specs_content


def extract_from_specs(specs_content: str) -> dict[str, str]:
    """
    Extract STACK_PROFILE from specs.md HTML comment.
    Falls back to DEFAULT_STACK if not found.
    """
    match = re.search(r"<!-- STACK_PROFILE:\s*(\{.*?\})\s*-->", specs_content)
    if match:
        try:
            profile = json.loads(match.group(1))
            logger.info(
                "Extracted stack profile from specs: backend=%s frontend=%s database=%s",
                profile.get("backend", "?"),
                profile.get("frontend", "?"),
                profile.get("database", "?"),
            )
            return profile
        except json.JSONDecodeError as e:
            logger.error("Failed to parse STACK_PROFILE from specs: %s", e)

    logger.warning("No STACK_PROFILE found in specs. Using defaults.")
    return dict(DEFAULT_STACK)


def is_python_backend(profile: dict[str, str]) -> bool:
    """Check if the stack uses a Python backend."""
    return profile.get("backend", "").startswith("python/")


def is_node_backend(profile: dict[str, str]) -> bool:
    """Check if the stack uses a Node.js backend."""
    return profile.get("backend", "").startswith("node/")


def has_frontend(profile: dict[str, str]) -> bool:
    """Check if the stack includes a frontend."""
    return profile.get("frontend", "none") != "none"


def is_react_frontend(profile: dict[str, str]) -> bool:
    """Check if the stack uses React."""
    return profile.get("frontend", "") == "react"


def describe_stack(profile: dict[str, str]) -> str:
    """Human-readable stack description for LLM prompts."""
    backend = profile.get("backend", "node/express")
    frontend = profile.get("frontend", "react")
    database = profile.get("database", "sqlite")

    parts = []

    if backend == "python/fastapi":
        parts.append("Python 3.12+ with FastAPI, Pydantic v2, SQLAlchemy 2.0, uvicorn")
    elif backend == "python/flask":
        parts.append("Python 3.12+ with Flask, Marshmallow, SQLAlchemy 2.0")
    elif backend == "python/django":
        parts.append("Python 3.12+ with Django 5, Django REST Framework")
    else:
        parts.append("Node.js with Express, Sequelize ORM")

    if frontend == "react":
        parts.append("React 18 (Vite + TypeScript), Tailwind CSS, Framer Motion")
    elif frontend == "htmx":
        parts.append("HTMX with Jinja2 templates, Alpine.js")
    elif frontend == "svelte":
        parts.append("SvelteKit with TypeScript, Tailwind CSS")
    elif frontend == "none":
        parts.append("No frontend (API-only)")

    if database == "postgresql":
        parts.append("PostgreSQL")
    elif database == "mongodb":
        parts.append("MongoDB")
    elif database == "mysql":
        parts.append("MySQL")
    else:
        parts.append("SQLite")

    return " | ".join(parts)
