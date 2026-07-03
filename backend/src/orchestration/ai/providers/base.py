import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    def analyze(
        self, prompt: str, system_prompt: str = None, timeout: int = 60
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def model_name(self) -> str:
        pass
