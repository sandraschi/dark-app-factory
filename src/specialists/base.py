import abc
from typing import List, Dict, Any


class Specialist(abc.ABC):
    """
    Base class for all Specialized Workers in the Dark App Factory Council.
    Each specialist owns specific files and may depend on others.
    """

    def __init__(
        self, name: str, owned_patterns: List[str], requires: List[str] = None
    ):
        self.name = name
        self.owned_patterns = owned_patterns
        self.requires = requires or []
        self.output_files: Dict[str, str] = {}  # Path -> Content
        self.ANTI_GASLIGHTING_PROMPT = """
        [ANTI-GASLIGHTING PROTOCOL]:
        - DO NOT output skeleton code or placeholders (e.g., // ... logic here).
        - EVERY functional requirement must be FULLY implemented.
        - Content must be DENSE and REALISTIC (no lorem ipsum, no 'Coming Soon').
        - If a section requires sub-pages or sub-routes, implement the SHELL and logic for those sub-pages IMMEDIATELY.
        """

    @abc.abstractmethod
    async def generate(
        self, specs: str, shared_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Produce code based on specs and context from previous workers.
        Returns a dictionary of {file_path: content}.
        """
        pass

    def can_handle(self, file_path: str) -> bool:
        """Simple prefix/extension matching for ownership."""
        for pattern in self.owned_patterns:
            if pattern.endswith("*"):
                if file_path.startswith(pattern[:-1]):
                    return True
            elif file_path == pattern:
                return True
        return False
