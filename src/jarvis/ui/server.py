"""FastAPI and WebSocket Server for Decoupled Graphical UI."""

import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jarvis.actuators.cdp_browser import CDPBrowserActuator
from jarvis.config import JarvisConfig, load_config
from jarvis.core.audit import AuditManager
from jarvis.memory.store import MemoryStore
from jarvis.security.vault import SecretVault
from jarvis.watchdogs.organizer import DownloadOrganizer
from jarvis.watchdogs.sentinel import HardwareSentinel

app = FastAPI(title="Jarvis HUD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = load_config()
audit = AuditManager()
sentinel = HardwareSentinel(config.watchdogs.sentinel)
cdp_browser = CDPBrowserActuator(port=config.browser.cdp_port)
organizer = DownloadOrganizer(config.watchdogs.organizer)
vault = SecretVault()
memory_store = MemoryStore(config.memory)

active_websockets: List[WebSocket] = []
current_agent_instance = None
kill_callback = None

class TaskRequest(BaseModel):
    goal: str
    autonomous: Optional[bool] = None

class SecretRequest(BaseModel):
    key: str
    value: str

class MemoryUpdateRequest(BaseModel):
    filename: str
    content: str

async def broadcast_ws(event: str, data: Any):
    payload = json.dumps({"event": event, "data": data})
    for ws in list(active_websockets):
        try:
            await ws.send_text(payload)
        except Exception:
            if ws in active_websockets:
                active_websockets.remove(ws)

def sync_broadcast(event: str, data: Any):
    """Bridge for synchronous agent calls to push updates to WebSockets."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_ws(event, data), loop)
    except Exception:
        pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        # Send initial telemetry
        await websocket.send_text(json.dumps({
            "event": "telemetry",
            "data": sentinel.get_hardware_metrics(),
        }))
        while True:
            msg = await websocket.receive_text()
            # Echo or handle incoming client pings
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

@app.get("/api/status")
async def get_status():
    return {
        "online": True,
        "telemetry": sentinel.get_hardware_metrics(),
        "cdp_browser_available": cdp_browser.is_cdp_available(),
        "autonomous_mode": config.autonomous_mode,
        "output_mode": config.output_mode,
        "policy": config.model.policy,
    }

@app.post("/api/run")
async def run_task(req: TaskRequest):
    from jarvis.core.agent import JarvisAgent
    global current_agent_instance

    run_config = load_config()
    if req.autonomous is not None:
        run_config.autonomous_mode = req.autonomous

    agent = JarvisAgent(run_config)
    current_agent_instance = agent

    # Hook agent console for WebSocket streaming
    orig_thought = agent.console.thought
    orig_action = agent.console.action
    orig_step = agent.console.step

    def ws_thought(text: str):
        orig_thought(text)
        sync_broadcast("thought", text)

    def ws_action(act: str, detail: str):
        orig_action(act, detail)
        sync_broadcast("action", {"actuator": act, "detail": detail})

    def ws_step(num: int, total: int, desc: str):
        orig_step(num, total, desc)
        sync_broadcast("step", {"step": num, "total": total, "desc": desc})

    agent.console.thought = ws_thought
    agent.console.action = ws_action
    agent.console.step = ws_step

    # Run in thread pool so server remains responsive
    loop = asyncio.get_event_loop()
    await broadcast_ws("task_start", {"goal": req.goal})
    result = await loop.run_in_executor(None, agent.run_task, req.goal)
    await broadcast_ws("task_finish", {"result": result})

    return {"status": "completed", "result": result}

@app.get("/api/history")
async def get_history():
    return audit.list_recent_runs(limit=30)

@app.get("/api/history/{run_id}")
async def get_run_details(run_id: str):
    details = audit.get_run(run_id)
    if not details:
        raise HTTPException(status_code=404, detail="Run not found")
    return details

@app.get("/api/history/{run_id}/screenshot/{filename}")
async def get_run_screenshot(run_id: str, filename: str):
    path = audit.base_dir / run_id / "screenshots" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(str(path), media_type="image/png")

@app.post("/api/browser/launch-cdp")
async def launch_cdp():
    success = cdp_browser.launch_everyday_browser()
    return {"success": success, "available": cdp_browser.is_cdp_available()}

@app.post("/api/organizer/run")
async def run_organizer():
    moved = organizer.organize_once()
    return {"moved_count": len(moved), "details": moved}

@app.get("/api/vault")
async def list_vault_keys():
    return {"keys": vault.list_keys()}

@app.post("/api/vault")
async def set_vault_secret(req: SecretRequest):
    vault.set_secret(req.key, req.value)
    return {"status": "saved", "key": req.key}

@app.get("/api/memory")
async def list_memory_files():
    files = []
    for p in sorted(memory_store.memory_dir.glob("**/*.md")):
        rel = str(p.relative_to(memory_store.memory_dir))
        content = p.read_text(encoding="utf-8")
        files.append({"name": rel, "content": content})
    return files

@app.post("/api/memory")
async def update_memory_file(req: MemoryUpdateRequest):
    path = memory_store.memory_dir / req.filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(req.content, encoding="utf-8")
    return {"status": "updated", "filename": req.filename}

@app.post("/api/system/kill")
async def master_kill():
    global kill_callback
    await broadcast_ws("system_kill", "Terminating all Jarvis services...")
    if kill_callback:
        asyncio.get_event_loop().call_later(0.5, kill_callback)
    return {"status": "terminating"}

# Serve Frontend HTML
WEB_DIR = Path(__file__).parent / "web"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>Jarvis HUD Web Interface Loading...</h1>")

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
