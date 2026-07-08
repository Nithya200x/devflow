from unittest.mock import MagicMock, patch

from app import create_app

_APP = None

def _get_app():
    global _APP
    if _APP is None:
        _APP = create_app(testing=True)
    return _APP


def test_detector_skips_when_no_prometheus_url():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    detector = PrometheusIncidentDetector()
    with patch.object(detector, "_check_triggers") as mock_check:
        mock_check.side_effect = Exception("should not be called")
        detector._has_open_incident("high_error_rate")
        assert True


def test_has_open_incident_returns_true_when_exists():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = _get_app()
    with app.app_context():
        detector = PrometheusIncidentDetector()
        with patch("models.Incident") as MockIncident:
            MockIncident.query.filter.return_value.first.return_value = MagicMock()
            assert detector._has_open_incident("high_error_rate") is True


def test_has_open_incident_returns_false_when_none():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = _get_app()
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

    app = _get_app()
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

    app = _get_app()
    with app.app_context():
        detector = PrometheusIncidentDetector()
        detector._has_open_incident = MagicMock(return_value=True)
        detector._create_incident = MagicMock()

        with patch.object(detector, "_check_triggers") as mock_check:
            mock_check.side_effect = None
            assert detector._has_open_incident("high_error_rate") is True


def test_detector_resolves_when_trigger_no_longer_firing():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = _get_app()
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

    app = _get_app()
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

    app = _get_app()
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

    app = _get_app()
    with app.app_context():
        updated = detector_config.update("high_error_rate", {"threshold": 10.0})
        assert updated is not None
        assert updated["threshold"] == 10.0

        fetched = detector_config.get("high_error_rate")
        assert fetched["threshold"] == 10.0

        detector_config.update("high_error_rate", {"threshold": 5.0})


def test_detector_background_context_can_access_db():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector
    import threading

    app = _get_app()
    detector = PrometheusIncidentDetector(interval=0.1)

    db_ok = threading.Event()
    db_error = []

    def test_check():
        try:
            from models import Incident
            _ = Incident.query.count()
            db_ok.set()
        except Exception as e:
            db_error.append(str(e))
            db_ok.set()

    detector._check_triggers = test_check
    detector.start(app)
    db_ok.wait(timeout=5)
    detector.stop()

    assert not db_error, f"DB access from background context failed: {db_error}"


def test_detector_duplicate_start_does_not_create_multiple_threads():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector

    app = _get_app()
    detector = PrometheusIncidentDetector(interval=30)
    detector.start(app)
    first_thread = detector._thread

    detector.start(app)

    assert detector._thread is first_thread
    assert detector._thread.is_alive()

    detector.stop()


def test_detector_find_open_incident_has_context_from_thread_target():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector
    import threading

    app = _get_app()
    detector = PrometheusIncidentDetector(interval=0.1)

    results = []
    done = threading.Event()

    def test_loop():
        try:
            result = detector._find_open_incident("high_error_rate")
            results.append(("ok", result))
        except Exception as e:
            results.append(("error", str(e)))
        done.set()

    detector._run_loop = test_loop
    detector.start(app)
    done.wait(timeout=10)
    detector.stop()

    assert len(results) == 1
    assert results[0][0] == "ok", f"_find_open_incident failed: {results[0]}"


def test_detector_recovers_from_failed_cycle():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector
    import threading

    app = _get_app()
    detector = PrometheusIncidentDetector(interval=0.2)

    call_count = [0]
    cycle2_db_ok = [False]
    done = threading.Event()

    def alternate():
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("simulated cycle 1 failure")
        try:
            from models import Incident
            _ = Incident.query.count()
            cycle2_db_ok[0] = True
        except Exception:
            cycle2_db_ok[0] = False
        done.set()

    detector._check_triggers = alternate
    detector.start(app)
    done.wait(timeout=10)
    detector.stop()

    assert call_count[0] >= 2, "Should have run at least 2 cycles"
    assert cycle2_db_ok[0] is True, "Cycle 2 DB access should succeed after cycle 1 failure"


def test_db_session_remove_called_after_detector_cycle():
    from orchestration.detectors.prometheus_detector import PrometheusIncidentDetector
    from extensions import db
    import threading
    import time

    app = _get_app()
    detector = PrometheusIncidentDetector(interval=0.1)

    remove_called = [False]
    cycle_done = threading.Event()

    original_remove = db.session.remove

    def tracked_remove(*args, **kwargs):
        remove_called[0] = True
        return original_remove(*args, **kwargs)

    def quick_cycle():
        cycle_done.set()

    detector._check_triggers = quick_cycle
    db.session.remove = tracked_remove

    try:
        detector.start(app)
        assert cycle_done.wait(timeout=12), "First detector cycle did not complete within timeout"
        detector.stop()
        for _ in range(50):
            if remove_called[0]:
                break
            time.sleep(0.05)

        assert remove_called[0], "db.session.remove should have been called after a cycle"
    finally:
        db.session.remove = original_remove
