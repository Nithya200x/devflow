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
    """Ensure no integration URLs or auth leak from the environment."""
    for key in ("PROMETHEUS_URL", "PROMETHEUS_USERNAME", "PROMETHEUS_PASSWORD", "PROMETHEUS_TOKEN",
                "GRAFANA_URL", "ALERTMANAGER_URL", "KUBE_CONFIG_PATH"):
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


class TestPrometheusURLNormalization:
    def test_grafana_cloud_full_url(self):
        os.environ["PROMETHEUS_URL"] = "https://prometheus-prod-42.grafana.net/api/prom"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert ps._base_url == "https://prometheus-prod-42.grafana.net/api/prom"
        assert ps._base_url.count("/api/prom") == 1

    def test_grafana_cloud_base_domain(self):
        os.environ["PROMETHEUS_URL"] = "https://prometheus-prod-42.grafana.net"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert ps._base_url == "https://prometheus-prod-42.grafana.net/api/prom"

    def test_standard_prometheus_url_unchanged(self):
        os.environ["PROMETHEUS_URL"] = "http://localhost:9090"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert ps._base_url == "http://localhost:9090"
        assert "/api/prom" not in ps._base_url

    def test_empty_url_stays_empty(self):
        os.environ.pop("PROMETHEUS_URL", None)
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert ps._base_url == ""

    def test_grafana_url_trailing_slash_stripped(self):
        os.environ["PROMETHEUS_URL"] = "https://prometheus-prod-42.grafana.net/api/prom/"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert ps._base_url == "https://prometheus-prod-42.grafana.net/api/prom"

    def test_no_duplicate_api_prom(self):
        os.environ["PROMETHEUS_URL"] = "https://prometheus-prod-42.grafana.net/api/prom"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        query_url = f"{ps._base_url}/api/v1/query"
        assert query_url.count("api/prom") == 1
        assert query_url == "https://prometheus-prod-42.grafana.net/api/prom/api/v1/query"


class TestPrometheusBasicAuth:
    def test_connect_uses_basic_auth(self):
        os.environ["PROMETHEUS_URL"] = "http://prometheus:9090"
        os.environ["PROMETHEUS_USERNAME"] = "testuser"
        os.environ["PROMETHEUS_PASSWORD"] = "testpass"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert ps._username == "testuser"
        assert ps._password == "testpass"
        ps._setup_session()
        assert ps._session.auth == ("testuser", "testpass")

    def test_connect_uses_bearer_token(self):
        os.environ["PROMETHEUS_URL"] = "http://prometheus:9090"
        os.environ.pop("PROMETHEUS_USERNAME", None)
        os.environ.pop("PROMETHEUS_PASSWORD", None)
        os.environ["PROMETHEUS_TOKEN"] = "tok123"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        ps._setup_session()
        assert ps._session.headers.get("Authorization") == "Bearer tok123"

    def test_connect_no_auth_no_creds(self):
        os.environ["PROMETHEUS_URL"] = "http://prometheus:9090"
        os.environ.pop("PROMETHEUS_USERNAME", None)
        os.environ.pop("PROMETHEUS_PASSWORD", None)
        os.environ.pop("PROMETHEUS_TOKEN", None)
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        ps._setup_session()
        assert ps._session.auth is None
        assert "Authorization" not in ps._session.headers


class TestPrometheusQueryEndpointURLs:
    def test_grafana_cloud_query_endpoint(self):
        os.environ["PROMETHEUS_URL"] = "https://prometheus-prod-42.grafana.net/api/prom"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert f"{ps._base_url}/api/v1/query" == \
            "https://prometheus-prod-42.grafana.net/api/prom/api/v1/query"
        assert f"{ps._base_url}/api/v1/query_range" == \
            "https://prometheus-prod-42.grafana.net/api/prom/api/v1/query_range"
        assert f"{ps._base_url}/api/v1/status/buildinfo" == \
            "https://prometheus-prod-42.grafana.net/api/prom/api/v1/status/buildinfo"
        assert ps._base_url.count("api/prom") == 1

    def test_grafana_cloud_base_domain_query_endpoint(self):
        os.environ["PROMETHEUS_URL"] = "https://prometheus-prod-42.grafana.net"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert f"{ps._base_url}/api/v1/query" == \
            "https://prometheus-prod-42.grafana.net/api/prom/api/v1/query"
        assert f"{ps._base_url}/api/v1/query_range" == \
            "https://prometheus-prod-42.grafana.net/api/prom/api/v1/query_range"

    def test_standard_prometheus_query_endpoint(self):
        os.environ["PROMETHEUS_URL"] = "http://localhost:9090"
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        assert f"{ps._base_url}/api/v1/query" == \
            "http://localhost:9090/api/v1/query"


class TestPrometheusHealthQuery:
    def test_up_query_returns_results(self):
        os.environ["PROMETHEUS_URL"] = "http://prometheus:9090"
        from services.prometheus_service import PrometheusService
        from unittest.mock import MagicMock
        ps = PrometheusService()
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success", "data": {"result": [{"metric": {}, "value": [1, "1"]}]}}
        mock_session.get.return_value = mock_resp
        ps._session = mock_session
        ps._connected = True
        result = ps.query("up")
        assert result["status"] == "success"
        assert len(result["data"]["result"]) == 1

    def test_missing_kubernetes_metrics_returns_empty(self):
        os.environ["PROMETHEUS_URL"] = "http://prometheus:9090"
        from services.prometheus_service import PrometheusService
        from unittest.mock import MagicMock
        ps = PrometheusService()
        mock_session = MagicMock()
        def mock_get(url, **kw):
            resp = MagicMock()
            resp.status_code = 200
            query = kw.get("params", {}).get("query", "")
            if "namespace" in query:
                resp.json.return_value = {"status": "success", "data": {"result": []}}
            else:
                resp.json.return_value = {"status": "success", "data": {"result": [{"metric": {}, "value": [1, "1"]}]}}
            return resp
        mock_session.get.side_effect = mock_get
        ps._session = mock_session
        ps._connected = True
        ns_up = ps.query('up{namespace="testns"}')
        assert ns_up["status"] == "success"
        assert len(ns_up["data"]["result"]) == 0


class TestPrometheusHealthCheckEndpoint:
    def test_health_connected_with_metrics(self):
        os.environ["PROMETHEUS_URL"] = "http://prometheus:9090"
        from services.prometheus_service import PrometheusService
        from unittest.mock import MagicMock
        ps = PrometheusService()
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success", "data": {"result": [{"metric": {}, "value": [1, "1"]}]}}
        mock_session.get.return_value = mock_resp
        ps._session = mock_session
        result = ps.health_check()
        assert result["connected"] is True
        assert result["has_metrics"] is True
        assert result["error"] is None

    def test_health_connected_no_metrics(self):
        os.environ["PROMETHEUS_URL"] = "http://prometheus:9090"
        from services.prometheus_service import PrometheusService
        from unittest.mock import MagicMock
        ps = PrometheusService()
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success", "data": {"result": []}}
        mock_session.get.return_value = mock_resp
        ps._session = mock_session
        result = ps.health_check()
        assert result["connected"] is True
        assert result["has_metrics"] is False
        assert result["error"] is None

    def test_health_unauthenticated(self):
        os.environ["PROMETHEUS_URL"] = "http://prometheus:9090"
        from services.prometheus_service import PrometheusService
        from unittest.mock import MagicMock
        ps = PrometheusService()
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_session.get.return_value = mock_resp
        ps._session = mock_session
        result = ps.health_check()
        assert result["connected"] is False
        assert result["error"] == "HTTP 401"

    def test_health_not_configured(self):
        os.environ.pop("PROMETHEUS_URL", None)
        from services.prometheus_service import PrometheusService
        ps = PrometheusService()
        result = ps.health_check()
        assert result["connected"] is False
        assert "not configured" in result["error"]


class TestKubernetesCollector:
    def test_not_configured_when_no_kubeconfig(self):
        from services.kubernetes_service import KubernetesService
        ks = KubernetesService()
        assert ks.connect() is False
        assert ks.connected is False



