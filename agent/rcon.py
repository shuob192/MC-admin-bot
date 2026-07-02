import asyncio
import struct
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_RCON_AUTH = 3
_RCON_EXEC = 2


class RCONError(Exception):
    pass


class RCONClient:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()
        self._req_id = 0

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
        await self._authenticate()
        logger.info("RCON connected to %s:%d", self.host, self.port)

    async def close(self) -> None:
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def execute(self, command: str) -> str:
        async with self._lock:
            return await self._execute_inner(command)

    async def _execute_inner(self, command: str) -> str:
        try:
            if self._writer is None or self._writer.is_closing():
                await self.connect()
            return await self._send_command(command)
        except (ConnectionResetError, BrokenPipeError, EOFError, OSError):
            logger.warning("RCON connection lost, reconnecting...")
            self._writer = None
            await self.connect()
            return await self._send_command(command)

    async def _send_command(self, command: str) -> str:
        req_id = self._next_id()
        await self._send_packet(req_id, _RCON_EXEC, command)
        resp_id, _, payload = await self._recv_packet()
        if resp_id != req_id:
            raise RCONError(f"Unexpected response id: {resp_id}")
        return payload

    async def _authenticate(self) -> None:
        req_id = self._next_id()
        await self._send_packet(req_id, _RCON_AUTH, self.password)
        resp_id, _, _ = await self._recv_packet()
        if resp_id == -1 or resp_id != req_id:
            raise RCONError("RCON authentication failed — check rcon.password in server.properties")

    def _next_id(self) -> int:
        self._req_id = (self._req_id % 0x7FFFFF) + 1
        return self._req_id

    async def _send_packet(self, req_id: int, ptype: int, payload: str) -> None:
        data = payload.encode("utf-8") + b"\x00\x00"
        length = 4 + 4 + len(data)
        packet = struct.pack("<iii", length, req_id, ptype) + data
        self._writer.write(packet)
        await self._writer.drain()

    async def _recv_packet(self) -> Tuple[int, int, str]:
        header = await self._reader.readexactly(12)
        length, req_id, ptype = struct.unpack("<iii", header)
        body = await self._reader.readexactly(length - 8)
        payload = body[:-2].decode("utf-8", errors="replace")
        return req_id, ptype, payload
