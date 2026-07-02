"""
RCON client unit tests.
No real Minecraft server required — a mock TCP server is spun up with asyncio.
"""
import asyncio
import struct
import pytest
import pytest_asyncio

from rcon import RCONClient, RCONError

PASSWORD = "test-password"
HOST = "127.0.0.1"

# ---------------------------------------------------------------------------
# Mock RCON server
# ---------------------------------------------------------------------------

def _pack(req_id: int, ptype: int, payload: str) -> bytes:
    data = payload.encode() + b"\x00\x00"
    length = 4 + 4 + len(data)
    return struct.pack("<iii", length, req_id, ptype) + data


async def _read(reader: asyncio.StreamReader) -> tuple[int, int, str]:
    header = await reader.readexactly(12)
    length, req_id, ptype = struct.unpack("<iii", header)
    body = await reader.readexactly(length - 8)
    return req_id, ptype, body[:-2].decode()


def make_rcon_server(password: str, command_map: dict[str, str]):
    """
    command_map: {"gamerule keep_inventory": "...is currently set to: true", ...}
    """
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            # Auth phase
            req_id, ptype, payload = await _read(reader)
            assert ptype == 3, "expected auth packet"
            if payload == password:
                writer.write(_pack(req_id, 2, ""))
            else:
                writer.write(_pack(-1, 2, ""))
            await writer.drain()

            # Command phase
            while True:
                try:
                    req_id, ptype, payload = await asyncio.wait_for(_read(reader), timeout=2.0)
                    result = command_map.get(payload, f"Unknown command: {payload}")
                    writer.write(_pack(req_id, 0, result))
                    await writer.drain()
                except asyncio.TimeoutError:
                    break
        finally:
            writer.close()

    return handler


@pytest_asyncio.fixture
async def rcon_server(unused_tcp_port):
    """Spin up a mock RCON server for each test."""
    command_map = {
        "gamerule keep_inventory": "Game rule keep_inventory is currently set to: true",
        "gamerule mob_griefing":   "Game rule mob_griefing is currently set to: false",
        "list": "There are 2 of a max of 20 players online: Steve, Alex",
    }
    server = await asyncio.start_server(
        make_rcon_server(PASSWORD, command_map),
        HOST,
        unused_tcp_port,
    )
    yield HOST, unused_tcp_port
    server.close()
    await server.wait_closed()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_successful_authentication(rcon_server):
    host, port = rcon_server
    client = RCONClient(host, port, PASSWORD)
    await client.connect()          # no exception means auth succeeded
    await client.close()


@pytest.mark.asyncio
async def test_wrong_password_raises(rcon_server):
    host, port = rcon_server
    client = RCONClient(host, port, "wrong-password")
    with pytest.raises(RCONError, match="authentication failed"):
        await client.connect()


@pytest.mark.asyncio
async def test_keepinventory_returns_true(rcon_server):
    host, port = rcon_server
    client = RCONClient(host, port, PASSWORD)
    await client.connect()
    result = await client.execute("gamerule keep_inventory")
    assert "true" in result
    await client.close()


@pytest.mark.asyncio
async def test_multiple_commands(rcon_server):
    host, port = rcon_server
    client = RCONClient(host, port, PASSWORD)
    await client.connect()

    r1 = await client.execute("gamerule keep_inventory")
    r2 = await client.execute("gamerule mob_griefing")
    r3 = await client.execute("list")

    assert "true" in r1
    assert "false" in r2
    assert "Steve" in r3

    await client.close()


@pytest.mark.asyncio
async def test_auto_reconnect(rcon_server):
    """execute should auto-reconnect after the connection is dropped."""
    host, port = rcon_server
    client = RCONClient(host, port, PASSWORD)
    await client.connect()

    # Force disconnect
    await client.close()

    # execute should reconnect internally
    result = await client.execute("gamerule keep_inventory")
    assert "true" in result
    await client.close()
