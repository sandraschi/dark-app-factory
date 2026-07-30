import json
import logging
import os
import urllib.request

from openai import AsyncOpenAI

logger = logging.getLogger("dark_factory")


def preflight_models(base_url: str, *model_names: str) -> None:
    """Verify all requested models exist on the Ollama server.

    Raises ValueError with available model list if any model is missing
    or the server is unreachable. Only runs when base_url points at localhost.
    """
    if not any(host in base_url.lower() for host in ["localhost", "127.0.0.1"]):
        return  # remote provider — skip preflight
    tags_url = base_url.rstrip("/v1").rstrip("/") + "/api/tags"
    try:
        req = urllib.request.Request(tags_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        available = {m["name"] for m in data.get("models", []) if "name" in m}
    except Exception as e:
        raise ValueError(
            f"Cannot reach Ollama at {tags_url} — is it running?\n{e}"
        ) from e

    missing = [m for m in model_names if m and m not in available]
    if missing:
        ordered = sorted(available)
        raise ValueError(
            f"Model(s) not found: {', '.join(missing)}\n"
            f"Available models on this machine:\n"
            + "\n".join(f"  - {m}" for m in ordered)
        )


class LLMClient:
    """Async LLM client with role-based model routing and token tracking."""

    def __init__(self, role: str = "foreman", model: str | None = None, base_url: str | None = None):
        self.role = role
        self.client: AsyncOpenAI = None
        self.model: str = model if model else ""
        self.base_url: str = base_url if base_url else ""
        self.tokens_used = {"input": 0, "output": 0}
        self._configure()

    def _configure(self):
        if self.role == "foreman":
            api_key = os.getenv("FOREMAN_API_KEY", os.getenv("OPENAI_API_KEY", "ollama"))
            if not self.base_url:
                self.base_url = os.getenv(
                    "FOREMAN_BASE_URL",
                    os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
                )
            if not self.model:
                self.model = os.getenv("FOREMAN_MODEL", "llama3.1:8b")
        else:
            api_key = os.getenv("WORKER_API_KEY", "ollama")
            if not self.base_url:
                self.base_url = os.getenv("WORKER_BASE_URL", "http://localhost:11434/v1")
            if not self.model:
                self.model = os.getenv("WORKER_MODEL", "qwen2.5-coder:32b-instruct-q4_K_M")

        self.client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)
        logger.info(
            "LLMClient initialized: role=%s model=%s endpoint=%s",
            self.role,
            self.model,
            self.base_url,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float | None = None,
    ) -> str:
        prompt_len = len(prompt) + len(system_prompt)
        estimated_tokens = prompt_len // 4
        if estimated_tokens > 60000:
            logger.warning(
                "Prompt ~%d tokens may exceed context window. Ensure OLLAMA_CONTEXT_LENGTH >= 65536.",
                estimated_tokens,
            )

        # Use caller-specified temperature, else role default
        effective_temp = temperature if temperature is not None else (0.7 if self.role == "foreman" else 0.2)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=effective_temp,
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

    def get_usage(self) -> dict[str, int]:
        return dict(self.tokens_used)

    def get_usage_summary(self) -> str:
        total = self.tokens_used["input"] + self.tokens_used["output"]
        return (
            f"[{self.role}] {self.model}: in={self.tokens_used['input']} out={self.tokens_used['output']} total={total}"
        )
