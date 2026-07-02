import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from dotenv import load_dotenv

from rcon import RCONClient, RCONError

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RCON_HOST     = os.getenv("RCON_HOST", "localhost")
RCON_PORT     = int(os.getenv("RCON_PORT", "25575"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD", "")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")

if not AGENT_API_KEY:
    raise RuntimeError("AGENT_API_KEY is not set")

rcon = RCONClient(RCON_HOST, RCON_PORT, RCON_PASSWORD)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rcon.connect()
    yield
    await rcon.close()


app = FastAPI(title="MC Agent", lifespan=lifespan)


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != AGENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class CommandRequest(BaseModel):
    command: str


@app.post("/rcon/execute")
async def execute_rcon(req: CommandRequest, _=Depends(verify_api_key)):
    try:
        result = await rcon.execute(req.command)
        return {"result": result}
    except RCONError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logging.exception("Unexpected error executing RCON command")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def server_status(_=Depends(verify_api_key)):
    try:
        result = await rcon.execute("list")
        return {"online": True, "detail": result}
    except Exception as e:
        return {"online": False, "detail": str(e)}
