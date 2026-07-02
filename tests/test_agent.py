"""
Agent API endpoint tests.
RCON client is mocked, so no Minecraft server is required.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# conftest.py sets sys.path first, so agent modules are importable here.
# Mock connect/close to prevent lifespan from failing during import.
with (
    patch("rcon.RCONClient.connect", new_callable=AsyncMock),
    patch("rcon.RCONClient.close",   new_callable=AsyncMock),
):
    from main import app

API_KEY = "test-secret-key"
HEADERS = {"x-api-key": API_KEY}

KEEPINVENTORY_RESPONSE = "Game rule keep_inventory is currently set to: true"
LIST_RESPONSE = "There are 2 of a max of 20 players online: Steve, Alex"


@pytest.fixture
def client():
    with (
        patch("main.rcon.connect", new_callable=AsyncMock),
        patch("main.rcon.close",   new_callable=AsyncMock),
    ):
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# /rcon/execute
# ---------------------------------------------------------------------------

def test_execute_keepinventory(client):
    with patch("main.rcon.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = KEEPINVENTORY_RESPONSE
        resp = client.post(
            "/rcon/execute",
            json={"command": "gamerule keep_inventory"},
            headers=HEADERS,
        )
    assert resp.status_code == 200
    assert resp.json()["result"] == KEEPINVENTORY_RESPONSE


def test_execute_requires_api_key(client):
    resp = client.post("/rcon/execute", json={"command": "list"})
    assert resp.status_code == 422   # missing x-api-key header


def test_execute_wrong_api_key(client):
    resp = client.post(
        "/rcon/execute",
        json={"command": "list"},
        headers={"x-api-key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_execute_rcon_error_returns_503(client):
    from rcon import RCONError
    with patch("main.rcon.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.side_effect = RCONError("connection refused")
        resp = client.post(
            "/rcon/execute",
            json={"command": "list"},
            headers=HEADERS,
        )
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# /status
# ---------------------------------------------------------------------------

def test_status_online(client):
    with patch("main.rcon.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = LIST_RESPONSE
        resp = client.get("/status", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["online"] is True
    assert "Steve" in body["detail"]


def test_status_offline_when_rcon_fails(client):
    with patch("main.rcon.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.side_effect = ConnectionRefusedError("refused")
        resp = client.get("/status", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["online"] is False


def test_status_requires_api_key(client):
    resp = client.get("/status")
    assert resp.status_code == 422
