import logging

from flask import current_app

from orchestration.ai.providers.base import AIProvider
from orchestration.ai.providers.groq import GroqProvider
from orchestration.ai.providers.ollama import OllamaProvider
from orchestration.ai.providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)


def create_ai_provider() -> AIProvider:
    provider = current_app.config.get("AI_PROVIDER", "").strip().lower()

    if provider == "groq":
        key = current_app.config.get("GROQ_API_KEY", "")
        model = current_app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        timeout = current_app.config.get("AI_TIMEOUT", 120)
        if not key:
            logger.warning("GROQ_API_KEY is not set; Groq provider will not authenticate")
        logger.info("AI Provider: groq | Model: %s | Timeout: %ds | Key set: %s", model, timeout, bool(key))
        return GroqProvider(api_key=key, model=model, timeout=timeout)

    if provider in ("openai", "openai-compatible"):
        key = current_app.config.get("OPENAI_API_KEY", "")
        model = current_app.config.get("OPENAI_MODEL", "gpt-4o")
        api_base = current_app.config.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        timeout = current_app.config.get("AI_TIMEOUT", 60)
        return OpenAIProvider(api_key=key, model=model, api_base=api_base, timeout=timeout)

    if provider in ("ollama", "lmstudio"):
        url = current_app.config.get("OLLAMA_URL", "")
        model = current_app.config.get("OLLAMA_MODEL", "llama3")
        timeout = current_app.config.get("AI_TIMEOUT", 120)
        return OllamaProvider(base_url=url, model=model, timeout=timeout)

    logger.warning("AI_PROVIDER '%s' not recognised; returning None", provider)
    return None
