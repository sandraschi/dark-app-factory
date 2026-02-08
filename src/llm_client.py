import os
import logging
from typing import Dict
from openai import AsyncOpenAI

logger = logging.getLogger("dark_factory")


class LLMClient:
    """Async LLM client with role-based model routing and token tracking."""

    def __init__(self, role: str = "foreman"):
        self.role = role
        self.client: AsyncOpenAI = None
        self.model: str = ""
        self.base_url: str = ""
        self.tokens_used = {"input": 0, "output": 0}
        self._configure()

    def _configure(self):
        if self.role == "foreman":
            api_key = os.getenv(
                "FOREMAN_API_KEY", os.getenv("OPENAI_API_KEY", "ollama")
            )
            self.base_url = os.getenv(
                "FOREMAN_BASE_URL",
                os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
            )
            self.model = os.getenv("FOREMAN_MODEL", "llama3.1:latest")
        else:
            api_key = os.getenv("WORKER_API_KEY", "ollama")
            self.base_url = os.getenv("WORKER_BASE_URL", "http://localhost:11434/v1")
            self.model = os.getenv("WORKER_MODEL", "qwen2.5-coder:latest")

        self.client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)
        logger.info(
            "LLMClient initialized: role=%s model=%s endpoint=%s",
            self.role, self.model, self.base_url,
        )

    async def generate(
        self, prompt: str, system_prompt: str = "You are a helpful assistant."
    ) -> str:
        prompt_len = len(prompt) + len(system_prompt)
        estimated_tokens = prompt_len // 4
        if estimated_tokens > 60000:
            logger.warning(
                "Prompt ~%d tokens may exceed context window. "
                "Ensure OLLAMA_CONTEXT_LENGTH >= 65536.",
                estimated_tokens,
            )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7 if self.role == "foreman" else 0.2,
            )

            if response.usage:
                self.tokens_used["input"] += response.usage.prompt_tokens
                self.tokens_used["output"] += response.usage.completion_tokens
                logger.debug(
                    "LLM call: in=%d out=%d model=%s",
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    self.model,
                )

            return response.choices[0].message.content

        except Exception as e:
            error_str = str(e)
            if "Connection refused" in error_str:
                logger.error(
                    "LLM connection refused at %s. Is Ollama running? (ollama serve)",
                    self.base_url,
                )
            else:
                logger.error("LLM generation failed: %s", error_str)
            return ""

    def get_usage(self) -> Dict[str, int]:
        return dict(self.tokens_used)

    def get_usage_summary(self) -> str:
        total = self.tokens_used["input"] + self.tokens_used["output"]
        return (
            f"[{self.role}] {self.model}: "
            f"in={self.tokens_used['input']} out={self.tokens_used['output']} "
            f"total={total}"
        )
