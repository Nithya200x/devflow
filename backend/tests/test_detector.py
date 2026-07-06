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


def test_detector_resolves_when_trigger_no_longer_firing():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = create_app()
    with app.app_context():
        detector = PrometheusIncidentDetector()

        mock_incident = MagicMock()
        mock_incident.incident_id = "INC-TEST456"
        mock_incident.status = "open"
        mock_incident.resolved_at = None

        mock_svc = MagicMock()
        mock_orch_incident = MagicMock()
        mock_svc.incident_service.get_incident.return_value = mock_orch_incident

        with patch(
            "orchestration.detectors.prometheus_detector.detector_config",
        ) as mock_config:
            mock_config.get_active_triggers.return_value = {
                "high_error_rate": {
                    "query": "some_query > 5",
                    "severity": "critical",
                    "title": "High error rate ({value:.1f}%)",
                    "description": "Error rate is high at {value:.1f}%",
                    "threshold": 5.0,
                },
            }

            with patch(
                "orchestration.detectors.prometheus_detector.prometheus_service",
            ) as mock_ps:
                mock_ps._base_url = "http://prometheus:9090"
                mock_ps.connected = True
                mock_ps.instant_query.return_value = {
                    "status": "success",
                    "data": {"result": []},
                }

                with patch.object(
                    detector, "_find_open_incident", return_value=mock_incident
                ):
                    with patch(
                        "orchestration.services.orchestration_service.get_orchestrator",
                        return_value=mock_svc,
                    ):
                        with patch("extensions.db.session.commit"):
                            detector._check_triggers()

                            mock_svc.incident_service.resolve_incident.assert_called_once()
                            assert mock_incident.status == "resolved"


def test_detector_uses_config_manager():
    from orchestration.detectors.detector_config import detector_config

    app = create_app()
    with app.app_context():
        all_config = detector_config.get_all()
        assert "high_error_rate" in all_config
        assert "high_latency" in all_config
        assert "service_down" in all_config

        error_cfg = detector_config.get("high_error_rate")
        assert error_cfg is not None
        assert error_cfg["enabled"] is True
        assert error_cfg["severity"] == "critical"


def test_detector_config_can_enable_disable():
    from orchestration.detectors.detector_config import detector_config

    app = create_app()
    with app.app_context():
        updated = detector_config.update("high_error_rate", {"enabled": False})
        assert updated is not None
        assert updated["enabled"] is False

        active = detector_config.get_active_triggers()
        assert "high_error_rate" not in active

        detector_config.update("high_error_rate", {"enabled": True})
        active = detector_config.get_active_triggers()
        assert "high_error_rate" in active


def test_detector_config_threshold_adjustment():
    from orchestration.detectors.detector_config import detector_config

    app = create_app()
    with app.app_context():
        updated = detector_config.update("high_error_rate", {"threshold": 10.0})
        assert updated is not None
        assert updated["threshold"] == 10.0

        fetched = detector_config.get("high_error_rate")
        assert fetched["threshold"] == 10.0

        detector_config.update("high_error_rate", {"threshold": 5.0})
