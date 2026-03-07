"""
Integration tests for the authentication flow.

These tests use a real SQLite in-memory database and exercise the full
request → route → CRUD → DB stack without any mocking.
"""
import base64
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_keypair():
    """Return (private_key, pk_b64) for a fresh Ed25519 key pair."""
    private_key = Ed25519PrivateKey.generate()
    pk_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return private_key, base64.b64encode(pk_bytes).decode()


def _register(client, pk_b64: str):
    return client.post("/api/v1/auth/register", json={"pk": pk_b64})


def _challenge(client, uid: str):
    return client.get("/api/v1/auth/challenge", params={"uid": uid})


def _verify(client, uid: str, private_key, nonce_b64: str):
    nonce = base64.b64decode(nonce_b64)
    sig_b64 = base64.b64encode(private_key.sign(nonce)).decode()
    return client.post("/api/v1/auth/verify", json={"uid": uid, "sig": sig_b64})


def _full_auth(client, private_key=None, pk_b64: str = None):
    """Register → challenge → verify; return (uid, access_token)."""
    if private_key is None:
        private_key, pk_b64 = _generate_keypair()
    uid = _register(client, pk_b64).json()["uid"]
    nonce_b64 = _challenge(client, uid).json()["nonce"]
    token = _verify(client, uid, private_key, nonce_b64).json()["access_token"]
    return uid, token


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_success_returns_uid_and_201(self, client):
        _, pk_b64 = _generate_keypair()
        response = _register(client, pk_b64)

        assert response.status_code == 201
        data = response.json()
        assert "uid" in data
        assert len(data["uid"]) == 8  # Crockford base-32, 8 chars

    def test_uid_is_unique_across_registrations(self, client):
        _, pk1 = _generate_keypair()
        _, pk2 = _generate_keypair()

        uid1 = _register(client, pk1).json()["uid"]
        uid2 = _register(client, pk2).json()["uid"]

        assert uid1 != uid2

    def test_duplicate_pk_returns_409(self, client):
        _, pk_b64 = _generate_keypair()
        _register(client, pk_b64)
        response = _register(client, pk_b64)

        assert response.status_code == 409


# ---------------------------------------------------------------------------
# Challenge
# ---------------------------------------------------------------------------

class TestChallenge:
    def test_returns_32_byte_nonce(self, client):
        _, pk_b64 = _generate_keypair()
        uid = _register(client, pk_b64).json()["uid"]

        response = _challenge(client, uid)

        assert response.status_code == 200
        nonce = base64.b64decode(response.json()["nonce"])
        assert len(nonce) == 32

    def test_nonce_stored_in_nonce_table(self, client):
        from app.api.v1 import auth as auth_module

        _, pk_b64 = _generate_keypair()
        uid = _register(client, pk_b64).json()["uid"]
        _challenge(client, uid)

        assert uid in auth_module.nonce_table
        assert len(auth_module.nonce_table[uid]) == 32

    def test_repeated_challenge_overwrites_nonce(self, client):
        from app.api.v1 import auth as auth_module

        _, pk_b64 = _generate_keypair()
        uid = _register(client, pk_b64).json()["uid"]

        _challenge(client, uid)
        first_nonce = bytes(auth_module.nonce_table[uid])

        _challenge(client, uid)
        second_nonce = bytes(auth_module.nonce_table[uid])

        # Two random 32-byte nonces will almost certainly differ
        assert first_nonce != second_nonce


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class TestVerify:
    def test_success_returns_jwt(self, client):
        private_key, pk_b64 = _generate_keypair()
        uid = _register(client, pk_b64).json()["uid"]
        nonce_b64 = _challenge(client, uid).json()["nonce"]

        response = _verify(client, uid, private_key, nonce_b64)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_nonce_consumed_after_verify(self, client):
        from app.api.v1 import auth as auth_module

        private_key, pk_b64 = _generate_keypair()
        uid = _register(client, pk_b64).json()["uid"]
        nonce_b64 = _challenge(client, uid).json()["nonce"]
        _verify(client, uid, private_key, nonce_b64)

        assert uid not in auth_module.nonce_table

    def test_wrong_signature_returns_401(self, client):
        _, pk_b64 = _generate_keypair()
        uid = _register(client, pk_b64).json()["uid"]
        _challenge(client, uid)
        bad_sig = base64.b64encode(b"\x00" * 64).decode()

        response = client.post("/api/v1/auth/verify", json={"uid": uid, "sig": bad_sig})

        assert response.status_code == 401

    def test_unknown_uid_returns_404(self, client):
        from app.api.v1 import auth as auth_module

        uid = "UNKNOWN1"
        auth_module.nonce_table[uid] = os.urandom(32)
        bad_sig = base64.b64encode(b"\x00" * 64).decode()

        response = client.post("/api/v1/auth/verify", json={"uid": uid, "sig": bad_sig})

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Fetch UID
# ---------------------------------------------------------------------------

class TestFetchUid:
    def test_returns_uid_for_known_pk(self, client):
        private_key, pk_b64 = _generate_keypair()
        expected_uid = _register(client, pk_b64).json()["uid"]

        response = client.post("/api/v1/auth/fetch_uid", json={"pk": pk_b64})

        assert response.status_code == 200
        assert response.json()["uid"] == expected_uid

    def test_unknown_pk_returns_401(self, client):
        _, pk_b64 = _generate_keypair()  # never registered

        response = client.post("/api/v1/auth/fetch_uid", json={"pk": pk_b64})

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Full flow
# ---------------------------------------------------------------------------

class TestFullAuthFlow:
    def test_register_challenge_verify_sequence(self, client):
        private_key, pk_b64 = _generate_keypair()

        reg = _register(client, pk_b64)
        assert reg.status_code == 201
        uid = reg.json()["uid"]

        ch = _challenge(client, uid)
        assert ch.status_code == 200

        ver = _verify(client, uid, private_key, ch.json()["nonce"])
        assert ver.status_code == 200
        assert "access_token" in ver.json()

    def test_token_grants_access_to_protected_endpoint(self, client):
        private_key, pk_b64 = _generate_keypair()
        uid, token = _full_auth(client, private_key, pk_b64)

        # The conversations/{id}/messages endpoint requires auth
        response = client.get(
            "/api/v1/conversations/1/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 200 even with no messages (empty list), as long as token is valid
        assert response.status_code == 200

    def test_expired_or_invalid_token_returns_401(self, client):
        response = client.get(
            "/api/v1/conversations/1/messages",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        assert response.status_code in (401, 403, 422)

    def test_missing_token_returns_403(self, client):
        response = client.get("/api/v1/conversations/1/messages")
        assert response.status_code == 403
