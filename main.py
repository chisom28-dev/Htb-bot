
import sys
import subprocess
import threading
from pathlib import Path
from contextlib import asynccontextmanager

from pydantic import BaseModel
from typing import Literal
from mt5_connector import mt5_connector

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
ENGINE_FILE = BASE_DIR / "engine.py"

engine_process = None
engine_lock = threading.Lock()

class MT5ConnectRequest(BaseModel):
    login: int
    password: str
    server: str
    account_type: Literal["DEMO"]

def get_engine_status():
    global engine_process

    if engine_process is not None and engine_process.poll() is None:
        return {
            "status": "RUNNING",
            "pid": engine_process.pid
        }

    return {
        "status": "STOPPED",
        "pid": None
    }


def stop_engine():
    global engine_process

    with engine_lock:
        if engine_process is None:
            return

        if engine_process.poll() is None:
            engine_process.terminate()

            try:
                engine_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                engine_process.kill()
                engine_process.wait(timeout=5)

        engine_process = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    stop_engine()


app = FastAPI(
    title="HTG Scalper API",
    version="0.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "HTG Scalper backend running"}


@app.get("/api/health")
def health():
    return {"status": "OK"}


@app.get("/api/bot/status")
def get_bot_status():
    return get_engine_status()


@app.post("/api/bot/start")
def start_bot():
    global engine_process

    with engine_lock:
        if engine_process is not None and engine_process.poll() is None:
            return {
                "message": "Engine is already running",
                "status": "RUNNING",
                "pid": engine_process.pid
            }

        if not ENGINE_FILE.exists():
            raise HTTPException(
                status_code=500,
                detail="Engine file not found"
            )

        try:
            engine_process = subprocess.Popen(
                [sys.executable, str(ENGINE_FILE)],
                cwd=str(BASE_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            if engine_process.poll() is not None:
                raise RuntimeError("Engine process exited immediately")

            return {
                "message": "Simulation engine started",
                "status": "RUNNING",
                "pid": engine_process.pid
            }

        except Exception as error:
            engine_process = None
            raise HTTPException(
                status_code=500,
                detail=f"Could not start engine: {error}"
            )


@app.post("/api/bot/stop")
def stop_bot():
    stop_engine()

    return {
        "message": "Engine stopped",
        "status": "STOPPED"
    }
@app.post("/api/mt5/connect")
def connect_mt5(data: MT5ConnectRequest):
    result = mt5_connector.connect(
        login=data.login,
        password=data.password,
        server=data.server,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


@app.get("/api/mt5/status")
def mt5_status():
    return mt5_connector.get_status()


@app.post("/api/mt5/disconnect")
def disconnect_mt5():
    return mt5_connector.disconnect()