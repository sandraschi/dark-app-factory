import json
import logging
import urllib.request
import os

logger = logging.getLogger("dark_factory")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LMSTUDIO_URL = os.environ.get("LMSTUDIO_URL", "http://localhost:1234")

def get_available_models(provider: str = "ollama") -> list:
    """Fetch real available model names from the specified provider."""
    models = []
    try:
        if provider == "ollama":
            url = f"{OLLAMA_URL}/api/tags"
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    models = [m["name"] for m in data.get("models", [])]
        elif provider == "lmstudio":
            url = f"{LMSTUDIO_URL}/v1/models"
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    models = [m["id"] for m in data.get("data", [])]
    except Exception as e:
        logger.warning("Failed to fetch models from %s: %s", provider, e)
    
    return models

def get_best_model(provider: str = "ollama", preferred_keywords=None) -> str:
    """Select the best available model based on keywords (e.g., 'coder', 'llama3')."""
    if preferred_keywords is None:
        preferred_keywords = ["coder", "instruct", "llama3.1", "qwen2.5"]
    
    models = get_available_models(provider)
    if not models:
        # Fallback if no models found (though should be avoided in strict e2e)
        return "llama3.1" if provider == "ollama" else "llava-v1.5-7b"

    # Search for preferred keywords in order
    for keyword in preferred_keywords:
        for model in models:
            if keyword.lower() in model.lower():
                return model
                
    return models[0] # Just take the first one if no preference matches
