from typing import Any, Dict, List, Optional

from orchestration.interfaces.collector_interface import BaseCollector


class CollectorRegistry:
    def __init__(self):
        self._collectors: Dict[str, BaseCollector] = {}

    def register(self, name: str, collector: BaseCollector):
        self._collectors[name] = collector

    def unregister(self, name: str):
        self._collectors.pop(name, None)

    def get(self, name: str) -> Optional[BaseCollector]:
        return self._collectors.get(name)

    def list_collectors(self) -> List[str]:
        return list(self._collectors.keys())

    def collect_all_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for name, collector in self._collectors.items():
            results[name] = collector.collect_evidence(context)
        return results

    def collect_all_logs(self, context: Dict[str, Any]) -> Dict[str, List[str]]:
        results = {}
        for name, collector in self._collectors.items():
            results[name] = collector.collect_logs(context)
        return results

    def collect_all_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for name, collector in self._collectors.items():
            results[name] = collector.collect_metadata(context)
        return results

    def collect_all_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for name, collector in self._collectors.items():
            results[name] = collector.collect_metrics(context)
        return results
