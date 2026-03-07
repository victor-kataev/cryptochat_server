import base64
import os

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy.exc import SQLAlchemyError

from app.main import app
from app.models.user import User
from app.services.database import get_db
from app.api.v1 import auth as auth_module


@pytest.fixture(autouse=True)
def clear_nonce_table():
    auth_module.nonce_table.clear()
    yield
    auth_module.nonce_table.clear()


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_keypair():
    """Generate an Ed25519 key pair and return (private_key, pk_b64, mock_user)."""
    private_key = Ed25519PrivateKey.generate()
    pk_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    pk_b64 = base64.b64encode(pk_bytes).decode()
    mock_user = MagicMock(spec=User)
    mock_user.uid = "ABC12345"
    mock_user.pk = pk_b64
    return private_key, pk_b64, mock_user


class TestRegister:
    def test_success_returns_uid(self, client, mock_db):
        mock_user = MagicMock(spec=User)
        mock_user.uid = "ABC12345"

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("app.crud.user.create_user", AsyncMock(return_value=mock_user))
            response = client.post("/api/v1/auth/register", json={"pk": "dGVzdHB1YmxpY2tleQ=="})

        assert response.status_code == 201
        assert response.json()["uid"] == "ABC12345"

    def test_duplicate_pk_returns_409(self, client, mock_db):
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("app.crud.user.create_user", AsyncMock(side_effect=SQLAlchemyError))
            response = client.post("/api/v1/auth/register", json={"pk": "dGVzdHB1YmxpY2tleQ=="})

        assert response.status_code == 409


class TestChallenge:
    def test_returns_32_byte_nonce(self, client):
        response = client.get("/api/v1/auth/challenge", params={"uid": "ABC12345"})

        assert response.status_code == 200
        nonce = base64.b64decode(response.json()["nonce"])
        assert len(nonce) == 32

    def test_stores_nonce_for_uid(self, client):
        uid = "ABC12345"
        client.get("/api/v1/auth/challenge", params={"uid": uid})

        assert uid in auth_module.nonce_table
        assert len(auth_module.nonce_table[uid]) == 31


class TestVerify:
    def test_success_returns_token(self, client, mock_db):
        uid = "ABC12345"
        private_key, _, mock_user = make_keypair()
        nonce = os.urandom(32)
        auth_module.nonce_table[uid] = nonce
        sig_b64 = base64.b64encode(private_key.sign(nonce)).decode()

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("app.crud.user.get_user", AsyncMock(return_value=mock_user))
            response = client.post("/api/v1/auth/verify", json={"uid": uid, "sig": sig_b64})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_nonce_consumed_after_verify(self, client, mock_db):
        uid = "ABC12345"
        private_key, _, mock_user = make_keypair()
        nonce = os.urandom(32)
        auth_module.nonce_table[uid] = nonce
        sig_b64 = base64.b64encode(private_key.sign(nonce)).decode()

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("app.crud.user.get_user", AsyncMock(return_value=mock_user))
            client.post("/api/v1/auth/verify", json={"uid": uid, "sig": sig_b64})

        assert uid not in auth_module.nonce_table

    def test_user_not_found_returns_404(self, client, mock_db):
        uid = "NOTFOUND"
        auth_module.nonce_table[uid] = os.urandom(32)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("app.crud.user.get_user", AsyncMock(return_value=None))
            response = client.post("/api/v1/auth/verify", json={"uid": uid, "sig": "dGVzdA=="})

        assert response.status_code == 404

    def test_invalid_signature_returns_401(self, client, mock_db):
        uid = "ABC12345"
        _, _, mock_user = make_keypair()
        auth_module.nonce_table[uid] = os.urandom(32)
        bad_sig = base64.b64encode(b"\x00" * 64).decode()

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("app.crud.user.get_user", AsyncMock(return_value=mock_user))
            response = client.post("/api/v1/auth/verify", json={"uid": uid, "sig": bad_sig})

        assert response.status_code == 401


class TestFetchUid:
    def test_success_returns_uid(self, client, mock_db):
        mock_user = MagicMock(spec=User)
        mock_user.uid = "ABC12345"

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("app.crud.user.get_user_by_pk", AsyncMock(return_value=mock_user))
            response = client.post("/api/v1/auth/fetch_uid", json={"pk": "dGVzdHB1YmxpY2tleQ=="})

        assert response.status_code == 200
        assert response.json()["uid"] == "ABC12345"

    def test_pk_not_found_returns_401(self, client, mock_db):
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("app.crud.user.get_user_by_pk", AsyncMock(return_value=None))
            response = client.post("/api/v1/auth/fetch_uid", json={"pk": "dGVzdHB1YmxpY2tleQ=="})

        assert response.status_code == 401
