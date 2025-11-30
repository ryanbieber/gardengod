from fastapi.testclient import TestClient
from gardengod.main import app

def test_read_main():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Garden God" in response.text  # Now serves HTML

def test_get_plants():
    with TestClient(app) as client:
        response = client.get("/plants")
        assert response.status_code == 200
        assert len(response.json()) > 0
