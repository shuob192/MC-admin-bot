import os
import httpx
from dotenv import load_dotenv

load_dotenv()

_BASE_URL = os.getenv("AGENT_URL", "http://localhost:8000")
_API_KEY  = os.getenv("AGENT_API_KEY", "")
_HEADERS  = {"x-api-key": _API_KEY}


class AgentError(Exception):
    pass


async def execute_rcon(command: str) -> str:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{_BASE_URL}/rcon/execute",
                json={"command": command},
                headers=_HEADERS,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()["result"]
        except httpx.HTTPStatusError as e:
            raise AgentError(f"Agent returned {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise AgentError(f"Could not reach agent: {e}")


async def get_status() -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{_BASE_URL}/status",
                headers=_HEADERS,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            return {"online": False, "detail": str(e)}
