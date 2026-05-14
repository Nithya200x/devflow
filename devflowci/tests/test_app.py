from app import create_app


def test_health_endpoint_reports_service_status():
    client = create_app().test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "up"


def test_home_page_renders_dashboard():
    client = create_app().test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"DevFlow" in response.data
    assert b"CI/CD Ready" in response.data


def test_details_page_renders_runtime_metadata():
    client = create_app().test_client()

    response = client.get("/details")

    assert response.status_code == 200
    assert b"Pod Details" in response.data
    assert b"Hostname" in response.data
