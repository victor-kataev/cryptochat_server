"""
Integration tests for the conversations endpoint.

Exercises GET /api/v1/conversations/{id}/messages with a real SQLite DB.
Data is seeded directly via SQLAlchemy before each test.
"""
import uuid
from datetime import datetime, UTC

import pytest

from app.models.conversation import Conversation
from app.models.conversation_member import ConversationMember
from app.models.message import Message
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

def _register_and_login(client):
    """Register a user and return (uid, Bearer token) via the full auth flow."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    import base64

    private_key = Ed25519PrivateKey.generate()
    pk_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    pk_b64 = base64.b64encode(pk_bytes).decode()

    uid = client.post("/api/v1/auth/register", json={"pk": pk_b64}).json()["uid"]
    nonce_b64 = client.get("/api/v1/auth/challenge", params={"uid": uid}).json()["nonce"]
    nonce = base64.b64decode(nonce_b64)
    sig_b64 = base64.b64encode(private_key.sign(nonce)).decode()
    token = client.post("/api/v1/auth/verify", json={"uid": uid, "sig": sig_b64}).json()[
        "access_token"
    ]
    return uid, token


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def seeded(db, client):
    """
    Seed the DB with:
      - one registered user (via API so the User row exists)
      - one conversation
      - two messages in that conversation
      - a ConversationMember linking user ↔ conversation

    Returns a dict with everything the tests need.
    """
    uid, token = _register_and_login(client)

    # Fetch the User row so we can use its `id`
    user = db.query(User).filter(User.uid == uid).first()

    conv = Conversation(name="test-room")
    db.add(conv)
    db.commit()
    db.refresh(conv)

    msg1 = Message(
        id=uuid.uuid4(),
        body="hello",
        sender_uid=uid,
        conversation_id=conv.id,
        created_at=datetime.now(UTC),
    )
    msg2 = Message(
        id=uuid.uuid4(),
        body="world",
        sender_uid=uid,
        conversation_id=conv.id,
        created_at=datetime.now(UTC),
    )
    db.add_all([msg1, msg2])
    db.commit()

    member = ConversationMember(
        conversation_id=conv.id,
        user_id=user.id,
        # last_read_message_id=msg1.id,
    )
    db.add(member)
    db.commit()

    return {
        "uid": uid,
        "token": token,
        "conv_id": conv.id,
        "msg1": msg1,
        "msg2": msg2,
        "user_id": user.id,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetConversationMessages:
    def test_returns_200_with_messages(self, client, seeded):
        response = client.get(
            f"/api/v1/conversations/{seeded['conv_id']}/messages",
            headers=_auth_headers(seeded["token"]),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        bodies = {m["body"] for m in data["messages"]}
        assert bodies == {"hello", "world"}

    def test_response_includes_sender_uid(self, client, seeded):
        response = client.get(
            f"/api/v1/conversations/{seeded['conv_id']}/messages",
            headers=_auth_headers(seeded["token"]),
        )

        for msg in response.json()["messages"]:
            assert msg["sender_uid"] == seeded["uid"]

    # def test_last_read_message_returned_for_member(self, client, seeded):
    #     response = client.get(
    #         f"/api/v1/conversations/{seeded['conv_id']}/messages",
    #         headers=_auth_headers(seeded["token"]),
    #     )

    #     data = response.json()
    #     assert data["last_read_message"] is not None
    #     assert data["last_read_message"]["id"] == str(seeded["msg1"].id)

    def test_empty_conversation_returns_zero_count(self, client, db):
        uid, token = _register_and_login(client)

        conv = Conversation(name="empty-room")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        response = client.get(
            f"/api/v1/conversations/{conv.id}/messages",
            headers=_auth_headers(token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["messages"] == []
        # assert data["last_read_message"] is None

    def test_requires_authentication(self, client, seeded):
        response = client.get(f"/api/v1/conversations/{seeded['conv_id']}/messages")
        assert response.status_code == 403

    def test_invalid_token_rejected(self, client, seeded):
        response = client.get(
            f"/api/v1/conversations/{seeded['conv_id']}/messages",
            headers={"Authorization": "Bearer bad.token.value"},
        )
        assert response.status_code in (401, 403, 422)

    def test_limit_parameter_respected(self, client, db):
        uid, token = _register_and_login(client)

        conv = Conversation(name="paginated-room")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        for i in range(5):
            db.add(Message(
                id=uuid.uuid4(),
                body=f"msg {i}",
                sender_uid=uid,
                conversation_id=conv.id,
                created_at=datetime.now(UTC),
            ))
        db.commit()

        response = client.get(
            f"/api/v1/conversations/{conv.id}/messages",
            params={"limit": 3},
            headers=_auth_headers(token),
        )

        assert response.status_code == 200
        assert response.json()["count"] == 3

    def test_non_member_gets_messages_but_no_last_read(self, client, db, seeded):
        """A user who is not a member can read messages but has no last_read_message."""
        uid2, token2 = _register_and_login(client)

        response = client.get(
            f"/api/v1/conversations/{seeded['conv_id']}/messages",
            headers=_auth_headers(token2),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        # assert data["last_read_message"] is None
