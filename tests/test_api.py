import pytest

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestAuth:
    def test_create_user(self, client):
        response = client.post(
            "/api/v1/auth/create",
            json={"fullname": "pytest user", "email": "pytest@gmail.com", "password": "12345678"}
        )
        assert response.status_code == 200

    def test_read_auth(self, client):
        response = client.get("/api/v1/auth/")
        assert response.status_code == 200
        assert response.json() == {"message": "You called auth endpoint"}

    def test_read_auth_id(self, client):
        response = client.get("/api/v1/auth/5/10")
        assert response.status_code == 200
        assert response.json() == {"message": "You called auth endpoint with id 5 and name 10. Name type is <class 'int'>"}

