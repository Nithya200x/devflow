from typing import Any, Dict, List

from orchestration.interfaces.collector_interface import BaseCollector


class BaseEvidenceCollector(BaseCollector):
    def __init__(self, source_name: str):
        self.source_name = source_name

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        raise NotImplementedError

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
