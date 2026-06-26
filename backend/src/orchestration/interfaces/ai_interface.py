from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIAnalysisService(ABC):
    @abstractmethod
    def analyze_incident(self, incident: Any, evidence: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def summarize_logs(self, logs: List[str]) -> str:
        pass

    @abstractmethod
    def suggest_fixes(self, incident: Any, context: Dict[str, Any]) -> List[str]:
        pass

    @abstractmethod
    def estimate_confidence(self, incident: Any, analysis: Dict[str, Any]) -> float:
        pass

    @abstractmethod
    def classify_root_cause(
        self, incident: Any, evidence: Dict[str, Any]
    ) -> Optional[str]:
        pass
