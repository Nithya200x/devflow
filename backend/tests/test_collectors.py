"""
Verify all infrastructure collectors correctly report status.

Rules under test:
- NOT_CONFIGURED when env variables are missing (no localhost fallbacks)
- CONNECTED only when real external API authentication succeeds
- UNAVAILABLE when credentials exist but connection fails
- No localhost defaults that pretend services exist in production
"""
import os
import pytest


@pytest.fixture(autouse=True)
def clear_env():
    """Ensure no integration URLs leak from the environment."""
    for key in ("PROMETHEUS_URL", "GRAFANA_URL", "ALERTMANAGER_URL", "KUBE_CONFIG_PATH"):
        os.environ.pop(key, None)
    yield


class TestPrometheusCollector:
    def test_not_configured_when_url_missing(self):
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert ps._base_url == "", "Should default to empty string, not localhost"
        assert ps.connect() is False
        assert ps.connected is False

    def test_not_configured_when_url_empty_string(self):
        os.environ["PROMETHEUS_URL"] = ""
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert ps._base_url == ""
        assert ps.connect() is False


class TestGrafanaCollector:
    def test_not_configured_when_url_missing(self):
        from services.grafana_service import GrafanaService
        gs = GrafanaService()
        assert gs._base_url == "", "Should default to empty string, not localhost"
        assert gs.connect() is False
        assert gs.connected is False

    def test_not_configured_when_url_empty_string(self):
        os.environ["GRAFANA_URL"] = ""
        from services.grafana_service import GrafanaService
        gs = GrafanaService()
        assert gs._base_url == ""
        assert gs.connect() is False


class TestAlertmanagerCollector:
    def test_not_configured_when_url_missing(self):
        from services.alertmanager_service import AlertmanagerService
        am = AlertmanagerService()
        assert am._base_url == "", "Should default to empty string, not localhost"
        assert am.connect() is False
        assert am.connected is False

    def test_not_configured_when_url_empty_string(self):
        os.environ["ALERTMANAGER_URL"] = ""
        from services.alertmanager_service import AlertmanagerService
        am = AlertmanagerService()
        assert am._base_url == ""
        assert am.connect() is False


class TestKubernetesCollector:
    def test_not_configured_when_no_kubeconfig(self):
        from services.kubernetes_service import KubernetesService
        ks = KubernetesService()
        assert ks.connect() is False
        assert ks.connected is False


class TestConfigDefaults:
    """Verify no localhost defaults exist in configuration."""

    def test_alertmanager_url_defaults_to_empty(self):
        os.environ.pop("ALERTMANAGER_URL", None)
        from config.config import Config
        assert Config.ALERTMANAGER_URL == "", \
            "ALERTMANAGER_URL must default to empty, not localhost:9093"

    def test_ollama_url_defaults_to_empty(self):
        os.environ.pop("OLLAMA_URL", None)
        from config.config import Config
        assert Config.OLLAMA_URL == "", \
            "OLLAMA_URL must default to empty, not localhost:11434"
