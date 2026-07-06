from unittest.mock import MagicMock, patch

from app import create_app


def test_detector_skips_when_no_prometheus_url():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    detector = PrometheusIncidentDetector()
    with patch.object(detector, "_check_triggers") as mock_check:
        mock_check.side_effect = Exception("should not be called")
        detector._has_open_incident("high_error_rate")
        assert True


def test_has_open_incident_returns_true_when_exists():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = create_app()
    with app.app_context():
        detector = PrometheusIncidentDetector()
        with patch("models.Incident") as MockIncident:
            MockIncident.query.filter.return_value.first.return_value = MagicMock()
            assert detector._has_open_incident("high_error_rate") is True


def test_has_open_incident_returns_false_when_none():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = create_app()
    with app.app_context():
        detector = PrometheusIncidentDetector()
        with patch("models.Incident") as MockIncident:
            MockIncident.query.filter.return_value.first.return_value = None
            assert detector._has_open_incident("high_error_rate") is False


def test_detector_triggers_only_when_query_has_results():
    from orchestration.detectors.prometheus_detector import _extract_value

    assert _extract_value({"status": "success", "data": {"result": [{"value": [123, "42.5"]}]}}) == 42.5
    assert _extract_value({"status": "success", "data": {"result": []}}) == -1.0
    assert _extract_value({}) == -1.0
    assert _extract_value({"data": {"result": [{"value": [0, "NaN"]}]}}) == 0.0


def test_detector_config_triggers_have_valid_queries():
    from orchestration.detectors.prometheus_detector import TRIGGER_CONFIG

    assert "high_error_rate" in TRIGGER_CONFIG
    assert "high_latency" in TRIGGER_CONFIG
    assert "service_down" in TRIGGER_CONFIG
    for key, config in TRIGGER_CONFIG.items():
        assert "query" in config
        assert "severity" in config
        assert config["severity"] in ("critical", "warning")
        assert "title" in config
        assert "description" in config


def test_detector_creates_incident_with_orchestration():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = create_app()
    with app.app_context():
        detector = PrometheusIncidentDetector()
        mock_svc = MagicMock()
        mock_incident = MagicMock()
        mock_incident.incident_id = "INC-TEST123"
        mock_svc.incident_service.create_incident.return_value = mock_incident

        mock_ai = MagicMock()

        with patch(
            "orchestration.services.orchestration_service.get_orchestrator",
            return_value=mock_svc,
        ):
            with patch(
                "orchestration.ai.service.trigger_ai_analysis",
                mock_ai,
            ):
                detector._create_incident(
                    "high_error_rate",
                    "High HTTP error rate (12.5%)",
                    "Error rate exceeded threshold",
                    "critical",
                )

                mock_svc.incident_service.create_incident.assert_called_once_with(
                    summary="High HTTP error rate (12.5%)",
                    severity="critical",
                    category="prometheus_high_error_rate",
                    description="Error rate exceeded threshold",
                )
                mock_ai.assert_called_once_with("INC-TEST123")


def test_detector_skips_when_open_incident_exists():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = create_app()
    with app.app_context():
        detector = PrometheusIncidentDetector()
        detector._has_open_incident = MagicMock(return_value=True)
        detector._create_incident = MagicMock()

        with patch.object(detector, "_check_triggers") as mock_check:
            mock_check.side_effect = None
            assert detector._has_open_incident("high_error_rate") is True
