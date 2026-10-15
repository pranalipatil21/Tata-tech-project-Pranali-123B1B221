"""Local Ollama LLM Service integration with health check and streaming support."""
import logging
import json
from typing import Generator, List, Dict, Any, Optional
import requests

from config.settings import OLLAMA_BASE_URL, DEFAULT_LLM_MODEL, FALLBACK_LLM_MODELS

logger = logging.getLogger(__name__)

class LLMService:
    """Manages communication with local Ollama daemon."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, default_model: str = DEFAULT_LLM_MODEL):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama service is reachable and list locally installed models."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                active_model = self.default_model
                if self.default_model not in models:
                    # Pick best available model from installed models
                    for fb in FALLBACK_LLM_MODELS:
                        for m in models:
                            if fb in m:
                                active_model = m
                                break
                        if active_model != self.default_model:
                            break
                    if active_model == self.default_model and models:
                        active_model = models[0]
                    self.default_model = active_model

                return {
                    "is_running": True,
                    "models": models,
                    "active_model": active_model,
                    "error": None
                }
            return {
                "is_running": False,
                "models": [],
                "active_model": None,
                "error": f"Ollama returned status {resp.status_code}"
            }
        except Exception as e:
            return {
                "is_running": False,
                "models": [],
                "active_model": None,
                "error": f"Ollama connection error: {str(e)}"
            }

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        """Execute non-streaming generation via Ollama /api/generate."""
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": 0.9,
                "repeat_penalty": 1.15
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=180)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
            logger.error(f"Ollama generation failed: {resp.status_code} - {resp.text}")
            return f"Error: Local LLM returned status code {resp.status_code}."
        except Exception as e:
            logger.error(f"Error during LLM generation: {e}")
            return f"Error connecting to local Ollama LLM: {str(e)}. Please ensure Ollama is running."

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> Generator[str, None, None]:
        """Stream generation response token-by-token for Streamlit UI."""
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "repeat_penalty": 1.15
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with requests.post(f"{self.base_url}/api/generate", json=payload, stream=True, timeout=90) as resp:
                if resp.status_code != 200:
                    yield f"Error: Local LLM returned status {resp.status_code}"
                    return

                for line in resp.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        token = chunk.get("response", "")
                        yield token
                        if chunk.get("done", False):
                            break
        except Exception as e:
            yield f"\n[Inference Error: {str(e)}. Check Ollama status.]"
