from app import create_app
from unittest.mock import MagicMock, patch
from sqlalchemy import exc as sa_exc


def test_health_endpoint_reports_service_status():
    client = create_app().test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "up"


def test_retry_on_db_disconnect_retries_on_ssl_error():
    from extensions import retry_on_db_disconnect

    call_count = [0]

    @retry_on_db_disconnect(max_retries=1)
    def failing_func():
        call_count[0] += 1
        if call_count[0] == 1:
            orig = Exception("SSL error: sslv3 alert bad record mac")
            raise sa_exc.OperationalError("stmt", {}, orig)
        return "ok"

    result = failing_func()
    assert result == "ok"
    assert call_count[0] == 2


def test_retry_on_db_disconnect_raises_after_max_retries():
    from extensions import retry_on_db_disconnect

    call_count = [0]

    @retry_on_db_disconnect(max_retries=1)
    def always_fails():
        call_count[0] += 1
        orig = Exception("SSL error: sslv3 alert bad record mac")
        raise sa_exc.OperationalError("stmt", {}, orig)

    import pytest
    with pytest.raises(sa_exc.OperationalError):
        always_fails()
    assert call_count[0] == 2


def test_retry_on_db_disconnect_passes_non_ssl_errors():
    from extensions import retry_on_db_disconnect

    call_count = [0]

    @retry_on_db_disconnect(max_retries=1)
    def fails_with_other():
        call_count[0] += 1
        raise sa_exc.OperationalError("stmt", {}, Exception("table not found"))

    import pytest
    with pytest.raises(sa_exc.OperationalError):
        fails_with_other()
    assert call_count[0] == 1
