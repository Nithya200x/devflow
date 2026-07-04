import json
import logging
import time
from typing import Any, Dict, Optional

import requests

from orchestration.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)

RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFFS = [5, 15, 30]


class GroqProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        timeout: int = 120,
    ):
        self._api_key = api_key
        self._model = model
        self._api_base = "https://api.groq.com/openai/v1"
        self._timeout = timeout

    def name(self) -> str:
        return "groq"

    def model_name(self) -> str:
        return self._model

    def analyze(
        self, prompt: str, system_prompt: str = None, timeout: int = None
    ) -> Optional[Dict[str, Any]]:
        t = timeout or self._timeout
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if not self._api_key:
            headers.pop("Authorization")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.1,
        }

        use_json_mode = True
        max_attempts = 2 + RATE_LIMIT_RETRIES
        rate_limit_attempts = 0

        for attempt in range(max_attempts):
            if use_json_mode:
                payload["response_format"] = {"type": "json_object"}
            else:
                payload.pop("response_format", None)

            try:
                resp = requests.post(
                    f"{self._api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=t,
                )

                if resp.status_code == 400 and use_json_mode:
                    logger.warning("JSON mode not supported by Groq model %s; retrying without it", self._model)
                    use_json_mode = False
                    continue

                if resp.status_code == 429:
                    rate_limit_attempts += 1
                    if rate_limit_attempts <= RATE_LIMIT_RETRIES:
                        backoff = RATE_LIMIT_BACKOFFS[rate_limit_attempts - 1]
                        logger.warning("Groq rate limited (attempt %d/%d). Backing off %ds...", rate_limit_attempts, RATE_LIMIT_RETRIES, backoff)
                        time.sleep(backoff)
                        continue
                    logger.error("Groq rate limited after %d retries. Giving up.", RATE_LIMIT_RETRIES)
                    return None

                resp.raise_for_status()
                body = resp.json()
                content = body["choices"][0]["message"]["content"]
                return json.loads(content)

            except requests.Timeout:
                logger.error("Groq request timed out after %ds", t)
                return None
            except requests.RequestException as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    rate_limit_attempts += 1
                    if rate_limit_attempts <= RATE_LIMIT_RETRIES:
                        backoff = RATE_LIMIT_BACKOFFS[rate_limit_attempts - 1]
                        logger.warning("Groq rate limited via exception (attempt %d/%d). Backing off %ds...", rate_limit_attempts, RATE_LIMIT_RETRIES, backoff)
                        time.sleep(backoff)
                        continue
                    logger.error("Groq rate limited after %d retries. Giving up.", RATE_LIMIT_RETRIES)
                    return None
                logger.error("Groq request failed: %s", e)
                return None
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.error("Failed to parse Groq response: %s", e)
                return None

        return None
