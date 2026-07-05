import json
import logging
from typing import Any, Dict, Optional

import requests

from orchestration.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    def __init__(
        self,
        base_url: str = "",
        model: str = "llama3",
        timeout: int = 120,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def name(self) -> str:
        return "ollama"

    def model_name(self) -> str:
        return self._model

    def analyze(
        self, prompt: str, system_prompt: str = None, timeout: int = None
    ) -> Optional[Dict[str, Any]]:
        t = timeout or self._timeout
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1,
            "format": "json",
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            resp = requests.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=t,
            )
            resp.raise_for_status()
            body = resp.json()
            raw = body.get("response", "{}")
            return json.loads(raw)
        except requests.Timeout:
            logger.error("Ollama request timed out after %ds", t)
            return None
        except requests.RequestException as e:
            logger.error("Ollama request failed: %s", e)
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse Ollama response: %s", e)
            return None
