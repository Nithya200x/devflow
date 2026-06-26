from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class NotificationProvider(ABC):
    @abstractmethod
    def send_incident_notification(self, incident: Any, recipient: str) -> bool:
        pass

    @abstractmethod
    def send_severity_alert(
        self, incident: Any, severity: str, recipient: str
    ) -> bool:
        pass

    @abstractmethod
    def send_resolution_notification(self, incident: Any, recipient: str) -> bool:
        pass

    @abstractmethod
    def send_bulk_notification(
        self, incident: Any, recipients: List[str]
    ) -> Dict[str, bool]:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class NotificationService:
    def __init__(self):
        self._providers: Dict[str, NotificationProvider] = {}

    def register_provider(self, provider: NotificationProvider):
        self._providers[provider.get_provider_name()] = provider

    def unregister_provider(self, name: str):
        self._providers.pop(name, None)

    def get_provider(self, name: str) -> Optional[NotificationProvider]:
        return self._providers.get(name)

    def notify_all(self, incident: Any, recipients: List[str]) -> Dict[str, bool]:
        results = {}
        for name, provider in self._providers.items():
            results[name] = provider.send_incident_notification(incident, recipients)
        return results

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())
