"""
Scenario Parser -- extracts structured GIVEN/WHEN/THEN scenarios from Markdown.

Parses the factory-generated scenarios.md into executable scenario objects.
The format expected is:

    ### N. Scenario Title
      - [ ] **Title**: Description.
        - GIVEN: precondition text
        - WHEN: action text (typically HTTP method + path)
        - THEN: expected outcome text

Each parsed scenario becomes a Scenario dataclass with enough structure
for the executor to attempt real HTTP calls or browser actions.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger("dark_factory")


class ScenarioType(Enum):
    """Classification of scenario by execution method."""

    API = "api"  # HTTP request (GET, POST, PUT, DELETE, PATCH)
    BROWSER = "browser"  # Requires browser interaction (page load, click, form)
    STATIC = "static"  # Cannot be executed mechanically (encryption, architecture)


@dataclass
class HttpAction:
    """Parsed HTTP action from a WHEN clause."""

    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str  # /users, /treatments/{id}, etc.
    body_hint: str = ""  # "valid JSON payload", "invalid JSON payload", etc.


@dataclass
class Assertion:
    """Parsed expected outcome from a THEN clause."""

    raw_text: str
    expected_status: int | None = None  # 200, 201, 404, 409, 403
    expects_list: bool = False  # "list of X is returned"
    expects_creation: bool = False  # "is created"
    expects_error: bool = False  # "error is returned"
    expects_rejection: bool = False  # "is rejected"


@dataclass
class Scenario:
    """A single parsed scenario ready for execution."""

    title: str
    description: str
    category: str  # "User Management", "Security Scenarios", etc.
    given: str  # Raw GIVEN text
    when: str  # Raw WHEN text
    then: str  # Raw THEN text
    scenario_type: ScenarioType = ScenarioType.STATIC
    http_action: HttpAction | None = None
    assertion: Assertion | None = None


# ---------------------------------------------------------------------------
# Regex patterns for parsing
# ---------------------------------------------------------------------------

_CATEGORY_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_SCENARIO_TITLE_RE = re.compile(r"^\s*-\s*\[[ x]\]\s*\*\*(.+?)\*\*:\s*(.+)$", re.MULTILINE)
_GIVEN_RE = re.compile(r"^\s*-\s*GIVEN:\s*(.+)$", re.MULTILINE)
_WHEN_RE = re.compile(r"^\s*-\s*WHEN:\s*(.+)$", re.MULTILINE)
_THEN_RE = re.compile(r"^\s*-\s*THEN:\s*(.+)$", re.MULTILINE)

# HTTP method + path extraction from WHEN text
_HTTP_RE = re.compile(
    r"(?:Submit|Send|Make)\s+(?:a\s+)?"
    r"(GET|POST|PUT|DELETE|PATCH|GET/PUT)\s+"
    r"(?:request(?:s)?\s+to\s+)?"
    r"`?(/[\w/{}\-]+)`?",
    re.IGNORECASE,
)

# Status code extraction from THEN text
_STATUS_RE = re.compile(r"(\d{3})\s+\w+", re.IGNORECASE)


def parse_http_action(when_text: str) -> HttpAction | None:
    """Extract HTTP method and path from a WHEN clause."""
    match = _HTTP_RE.search(when_text)
    if not match:
        return None

    raw_method = match.group(1).upper()
    path = match.group(2)

    # Handle "GET/PUT" -> take the first
    if "/" in raw_method:
        raw_method = raw_method.split("/")[0]

    # Determine body hint
    body_hint = ""
    lower = when_text.lower()
    if "invalid json payload" in lower:
        body_hint = "invalid"
    elif "duplicating" in lower:
        body_hint = "duplicate"
    elif "valid json payload" in lower:
        body_hint = "valid"

    return HttpAction(method=raw_method, path=path, body_hint=body_hint)


def parse_assertion(then_text: str) -> Assertion:
    """Extract structured expectations from a THEN clause."""
    assertion = Assertion(raw_text=then_text)

    # Look for explicit HTTP status codes
    status_match = _STATUS_RE.search(then_text)
    if status_match:
        code = int(status_match.group(1))
        if 100 <= code <= 599:
            assertion.expected_status = code

    lower = then_text.lower()

    # Semantic classification
    if "list" in lower and "returned" in lower:
        assertion.expects_list = True
    if "created" in lower:
        assertion.expects_creation = True
        if assertion.expected_status is None:
            assertion.expected_status = 201
    if "error" in lower or "not found" in lower:
        assertion.expects_error = True
    if "rejected" in lower:
        assertion.expects_rejection = True
        assertion.expects_error = True
    if "forbidden" in lower:
        assertion.expects_error = True
        if assertion.expected_status is None:
            assertion.expected_status = 403

    return assertion


def classify_scenario(http_action: HttpAction | None, then_text: str) -> ScenarioType:
    """Determine how to execute a scenario."""
    lower = then_text.lower()
    # Static/architectural scenarios that can't be mechanically tested
    static_keywords = ["encrypted", "aes-256", "encryption", "hashing"]
    if any(kw in lower for kw in static_keywords):
        return ScenarioType.STATIC

    if http_action:
        return ScenarioType.API

    return ScenarioType.BROWSER


def parse_scenarios(text: str) -> list[Scenario]:
    """Parse a scenarios.md file into a list of Scenario objects.

    Args:
        text: Raw markdown content of scenarios.md

    Returns:
        List of parsed Scenario objects.
    """
    scenarios = []
    current_category = "Uncategorized"

    # Split by scenario blocks. Each block starts with a ### heading.
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Track category (## headings)
        cat_match = _CATEGORY_RE.match(line)
        if cat_match:
            current_category = cat_match.group(1).strip()
            i += 1
            continue

        # Look for scenario title lines
        title_match = _SCENARIO_TITLE_RE.match(line)
        if title_match:
            title = title_match.group(1).strip()
            description = title_match.group(2).strip()

            # Scan forward for GIVEN/WHEN/THEN within the next few lines
            given_text = ""
            when_text = ""
            then_text = ""

            for j in range(i + 1, min(i + 6, len(lines))):
                given_m = _GIVEN_RE.match(lines[j])
                when_m = _WHEN_RE.match(lines[j])
                then_m = _THEN_RE.match(lines[j])

                if given_m:
                    given_text = given_m.group(1).strip()
                elif when_m:
                    when_text = when_m.group(1).strip()
                elif then_m:
                    then_text = then_m.group(1).strip()

            if when_text and then_text:
                http_action = parse_http_action(when_text)
                assertion = parse_assertion(then_text)
                scenario_type = classify_scenario(http_action, then_text)

                scenarios.append(
                    Scenario(
                        title=title,
                        description=description,
                        category=current_category,
                        given=given_text,
                        when=when_text,
                        then=then_text,
                        scenario_type=scenario_type,
                        http_action=http_action,
                        assertion=assertion,
                    )
                )

        i += 1

    logger.info(
        "Parsed %d scenarios: %d API, %d browser, %d static",
        len(scenarios),
        sum(1 for s in scenarios if s.scenario_type == ScenarioType.API),
        sum(1 for s in scenarios if s.scenario_type == ScenarioType.BROWSER),
        sum(1 for s in scenarios if s.scenario_type == ScenarioType.STATIC),
    )
    return scenarios


def parse_scenarios_file(path: str) -> list[Scenario]:
    """Parse a scenarios.md file from disk."""
    filepath = Path(path)
    if not filepath.exists():
        logger.error("Scenarios file not found: %s", path)
        return []
    text = filepath.read_text(encoding="utf-8")
    return parse_scenarios(text)
