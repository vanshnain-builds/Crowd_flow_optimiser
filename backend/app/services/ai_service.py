from __future__ import annotations

"""
AI service — selects and initializes the AI provider.
"""

from app.core.config import settings
from app.ai.provider import AIProvider
from app.core.logging import get_logger

log = get_logger(__name__)

_provider: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    global _provider
    if _provider is not None:
        return _provider

    mode = settings.effective_ai_mode
    if mode == "huggingface":
        from app.ai.huggingface_provider import HuggingFaceAIProvider
        _provider = HuggingFaceAIProvider()
        log.info("AI provider: HuggingFace | model=%s", settings.hf_model)
    else:
        from app.ai.mock_provider import MockAIProvider
        _provider = MockAIProvider()
        log.info("AI provider: Mock (no HF token or mock mode)")

    return _provider
