from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseCollector(ABC):
    @abstractmethod
    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        pass

    @abstractmethod
    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
