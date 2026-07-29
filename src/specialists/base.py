import abc
from typing import Any


class Specialist(abc.ABC):
    """
    Base class for all Specialized Workers in the Dark App Factory Council.
    Each specialist owns specific files and may depend on others.
    """

    # Default temperature; subclasses override via __init__ kwarg.
    DEFAULT_TEMPERATURE: float = 0.2

    def __init__(
        self,
        name: str,
        owned_patterns: list[str],
        requires: list[str] | None = None,
        temperature: float | None = None,
    ):
        self.name = name
        self.owned_patterns = owned_patterns
        self.requires = requires or []
        self.temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        self.output_files: dict[str, str] = {}  # Path -> Content
        self.ANTI_GASLIGHTING_PROMPT = """
        [ANTI-GASLIGHTING PROTOCOL]:
        - DO NOT output skeleton code or placeholders (e.g., // ... logic here).
        - EVERY functional requirement must be FULLY implemented.
        - Content must be DENSE and REALISTIC (no lorem ipsum, no 'Coming Soon').
        - If a section requires sub-pages or sub-routes, implement the SHELL and logic for those sub-pages IMMEDIATELY.
        """

    @abc.abstractmethod
    async def generate(self, file_path: str, specs: str, shared_context: dict[str, Any], worker: Any) -> str:
        """
        Generate code for a single file based on specs and upstream context.

        Args:
            file_path: Target file path to generate.
            specs: Full specification text.
            shared_context: Accumulated outputs from upstream specialists.
            worker: LLMClient instance for code generation.

        Returns:
            Generated source code as a string.
        """
        pass

    def can_handle(self, file_path: str) -> bool:
        """Glob-style ownership matching.

        Supports:
          - Exact match:           'server.js'
          - Single-level wildcard: 'src/components/*'  matches src/components/Foo.tsx
          - Multi-level wildcard:  'src/components/**' matches src/components/ui/Button.tsx
          - Catch-all:             '*'
        """
        for pattern in self.owned_patterns:
            if pattern == "*":
                return True
            if pattern.endswith("/**"):
                # Multi-level: match any file under the prefix directory
                prefix = pattern[:-3]  # strip /**
                if file_path.startswith(prefix + "/") or file_path == prefix:
                    return True
            elif pattern.endswith("/*"):
                # Single-level: match files directly inside the directory
                prefix = pattern[:-2]  # strip /*
                rest = file_path[len(prefix) :]
                if file_path.startswith(prefix + "/") and "/" not in rest.lstrip("/"):
                    return True
            elif file_path == pattern:
                return True
        return False

    # -----------------------------------------------------------------
    # Context Injection: read upstream dependency outputs
    # -----------------------------------------------------------------
    def get_dependency_context(self, shared_context: dict[str, Any]) -> str:
        """Build a summary of code produced by required upstream specialists.

        Returns a string (capped at 8000 chars) containing truncated file
        contents from each dependency, suitable for injection into prompts.
        """
        if not self.requires:
            return ""
        chunks: list[str] = []
        for req in self.requires:
            dep_output = shared_context.get(req, {})
            if not isinstance(dep_output, dict):
                continue
            for path, code in dep_output.items():
                if not code:
                    continue
                chunks.append(f"--- {req}/{path} ---\n{code[:2000]}")
        combined = "\n".join(chunks)
        return combined[:8000]

    # -----------------------------------------------------------------
    # Validation Hook: domain-specific quality checks
    # -----------------------------------------------------------------
    def validate(self, file_path: str, code: str, specs: str) -> tuple[bool, str]:
        """Return (is_valid, error_message). Override in subclasses."""
        return (True, "")

    # -----------------------------------------------------------------
    # Self-Declaration: specialists declare files they need
    # -----------------------------------------------------------------
    def declare_files(self, specs: str, stack_profile: dict[str, str]) -> list[str]:
        """Return additional file paths this specialist wants to generate,
        based on keyword analysis of the specs and the stack profile.
        Default: no extra files. Override in subclasses.
        """
        return []

    def get_docs(self) -> str:
        """Returns the specialist's documentation from its docstring."""
        return self.__doc__ or "No documentation available for this specialist."
