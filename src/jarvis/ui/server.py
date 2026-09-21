import asyncio
import base64
import io
import json
import os
import shutil
import threading
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import requests
from jarvis.actuators.cdp_browser import CDPBrowserActuator
from jarvis.config import JarvisConfig, load_config, save_config
from jarvis.core.audit import AuditManager
from jarvis.core.errors import error_tracker
from jarvis.memory.store import MemoryStore
from jarvis.security.vault import SecretVault
from jarvis.voice.tts import TextToSpeech
from jarvis.watchdogs.cron_engine import CronEngine
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
tts = TextToSpeech(config.voice)
cron_engine = CronEngine(config.watchdogs.cron, briefing_callback=lambda b: tts.speak(b))

active_websockets: List[WebSocket] = []
current_agent_instance = None
kill_callback = None

file_request_event = threading.Event()
last_supplied_file: Optional[str] = None

class TaskRequest(BaseModel):
    goal: str
    autonomous: Optional[bool] = None
    file_paths: Optional[List[str]] = None
    conversation_mode: Optional[str] = None

class ConversationModeRequest(BaseModel):
    mode: Literal["audio_only", "audio+chat", "chat_only"]

class MediaShowRequest(BaseModel):
    media_type: Literal["diagram", "chart", "image"]
    content: str
    title: Optional[str] = "Jarvis Visual Display"
    caption: Optional[str] = None
    target: Optional[Literal["auto", "dialog", "window", "system_window", "both"]] = "auto"

class SupplyFileRequest(BaseModel):
    file_path: Optional[str] = None

class SecretRequest(BaseModel):
    key: str
    value: str

class MemoryUpdateRequest(BaseModel):
    filename: str
    content: str

class DesktopSelectRequest(BaseModel):
    screen_index: int

class ModelSelectionRequest(BaseModel):
    local_text_model: Optional[str] = None
    local_vision_model: Optional[str] = None
    tier0_model: Optional[str] = None

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
    current_cfg = load_config()
    return {
        "online": True,
        "telemetry": sentinel.get_hardware_metrics(),
        "cdp_browser_available": cdp_browser.is_cdp_available(),
        "autonomous_mode": current_cfg.autonomous_mode,
        "output_mode": current_cfg.output_mode,
        "conversation_mode": current_cfg.conversation_mode,
        "policy": current_cfg.model.policy,
        "tier0_enabled": current_cfg.model.tier0_enabled,
        "tier0_model": current_cfg.model.tier0_model,
        "sentinel_active": current_cfg.watchdogs.sentinel.enabled,
        "organizer_active": current_cfg.watchdogs.organizer.enabled,
        "cron_brief_active": current_cfg.watchdogs.cron.enabled,
        "voice_reply_on_chat": current_cfg.voice.voice_reply_on_chat,
        "always_voice_response": current_cfg.voice.always_voice_response,
        "desktop_screen_index": getattr(current_cfg.desktop, "screen_index", 1),
    }

@app.post("/api/run")
async def run_task(req: TaskRequest):
    from jarvis.core.agent import JarvisAgent
    global current_agent_instance

    run_config = load_config()
    if req.autonomous is not None:
        run_config.autonomous_mode = req.autonomous
    if req.conversation_mode:
        run_config.conversation_mode = req.conversation_mode
        if req.conversation_mode == "audio_only":
            run_config.output_mode = "voice"
            run_config.voice.enabled = True
            run_config.voice.always_voice_response = True
        elif req.conversation_mode == "chat_only":
            run_config.output_mode = "cli"
            run_config.voice.enabled = False
        elif req.conversation_mode == "audio+chat":
            run_config.output_mode = "both"
            run_config.voice.enabled = True

    def request_file_handler(desc: str, exp: Optional[str]) -> Optional[str]:
        global last_supplied_file
        last_supplied_file = None
        file_request_event.clear()
        sync_broadcast("file_requested", {"description": desc, "expected_filename": exp})
        file_request_event.wait(timeout=180)
        return last_supplied_file

    def show_media_handler(m_type: str, content: str, title: str, caption: Optional[str], target: str):
        sync_broadcast("show_media", {
            "media_type": m_type,
            "content": content,
            "title": title,
            "caption": caption,
            "target": target
        })
        if target in ["window", "system_window", "both"]:
            try:
                from jarvis.ui.system_window import SystemWindowManager
                SystemWindowManager.show_media(m_type, content, title, caption)
            except Exception as e:
                print(f"[SystemWindow Warning] {e}")

    agent = JarvisAgent(run_config, request_file_cb=request_file_handler, show_media_cb=show_media_handler)
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
    await broadcast_ws("task_start", {"goal": req.goal, "file_paths": req.file_paths, "conversation_mode": run_config.conversation_mode})
    result = await loop.run_in_executor(None, agent.run_task, req.goal, req.file_paths)
    await broadcast_ws("task_finish", {
        "result": result,
        "conversation_mode": run_config.conversation_mode,
        "should_speak": (run_config.conversation_mode != "chat_only" and run_config.voice.enabled)
    })

    return {"status": "completed", "result": result, "conversation_mode": run_config.conversation_mode}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a resource file into Jarvis workspace."""
    attachments_dir = Path.home() / ".jarvis" / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)
    dest_path = attachments_dir / file.filename
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {
        "filename": file.filename,
        "path": str(dest_path.resolve()),
        "size_kb": round(dest_path.stat().st_size / 1024, 1),
    }

@app.post("/api/supply-file")
async def supply_requested_file(req: SupplyFileRequest):
    """Fulfill or cancel a pending file request from Jarvis."""
    global last_supplied_file
    if req.file_path and req.file_path.strip():
        last_supplied_file = req.file_path.strip()
        file_request_event.set()
        await broadcast_ws("file_supplied", {"file_path": last_supplied_file, "cancelled": False})
        return {"status": "supplied", "file_path": last_supplied_file}
    else:
        last_supplied_file = None
        file_request_event.set()
        await broadcast_ws("file_supplied", {"file_path": None, "cancelled": True})
        return {"status": "cancelled", "file_path": None}

@app.get("/api/guide")
async def get_user_guide():
    """Retrieve the full user-guide.md content for in-UI display."""
    guide_path = Path(__file__).resolve().parent.parent.parent.parent / "user-guide.md"
    if not guide_path.exists():
        guide_path = Path("user-guide.md")
    content = ""
    if guide_path.exists():
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
    return {"content": content}

@app.get("/api/history/analytics")
async def get_history_analytics():
    """Get aggregated analytics, success rate, and actuator breakdown."""
    return audit.get_analytics()

@app.get("/api/history")
async def get_history():
    return audit.list_recent_runs(limit=30)

@app.get("/api/history/{run_id}")
async def get_run_details(run_id: str):
    details = audit.get_run(run_id)
    if not details:
        raise HTTPException(status_code=404, detail="Run not found")
    return details

@app.get("/api/history/{run_id}/markdown")
async def get_run_markdown(run_id: str):
    """Export mission run details as clean formatted Markdown."""
    md = audit.export_run_markdown(run_id)
    return {"markdown": md, "run_id": run_id}

@app.get("/api/history/{run_id}/screenshot/{filename}")
async def get_run_screenshot(run_id: str, filename: str):
    path = audit.base_dir / run_id / "screenshots" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(str(path), media_type="image/png")

@app.post("/api/media/show")
async def show_media_endpoint(req: MediaShowRequest):
    """Trigger display of a diagram, chart, or image via Web UI dialog and/or system window."""
    target = req.target or "auto"
    payload = {
        "media_type": req.media_type,
        "content": req.content,
        "title": req.title or "Jarvis Visual Display",
        "caption": req.caption,
        "target": target
    }
    # 1. Broadcast to Web UI WebSocket clients
    await broadcast_ws("show_media", payload)

    # 2. If target is window, system_window, or both, also spawn native X11 desktop system window
    if target in ["window", "system_window", "both"]:
        try:
            from jarvis.ui.system_window import SystemWindowManager
            SystemWindowManager.show_media(req.media_type, req.content, req.title or "Jarvis Visual Display", req.caption)
        except Exception as e:
            print(f"[SystemWindow Error] {e}")

    return {"status": "displayed", "media_type": req.media_type, "target": target}

@app.get("/api/media/file")
async def get_media_file(path: str):
    """Serve a local image/chart file to the Web HUD modal."""
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".gif": "image/gif"
    }
    mtype = media_types.get(p.suffix.lower(), "application/octet-stream")
    return FileResponse(str(p), media_type=mtype)

@app.get("/api/desktop/monitors")
async def get_desktop_monitors():
    """List all detected physical and virtual desktop displays."""
    from jarvis.actuators.desktop import DesktopActuator
    monitors = DesktopActuator.list_monitors()
    current_cfg = load_config()
    curr_idx = getattr(current_cfg.desktop, "screen_index", 1)
    return {
        "monitors": monitors,
        "current_screen_index": curr_idx,
    }

@app.post("/api/desktop/select")
async def select_desktop(req: DesktopSelectRequest):
    """Set the main desktop screen index for Jarvis vision & interaction."""
    global config, current_agent_instance
    config = load_config()
    config.desktop.screen_index = req.screen_index
    save_config(config)
    if current_agent_instance and hasattr(current_agent_instance, "desktop"):
        current_agent_instance.desktop.set_screen_index(req.screen_index)

    await broadcast_ws("desktop_changed", {
        "screen_index": req.screen_index
    })
    return {
        "status": "updated",
        "screen_index": req.screen_index
    }

@app.get("/api/desktop/preview")
async def get_desktop_preview(screen_index: Optional[int] = None):
    """Grab a live preview thumbnail of the requested desktop monitor."""
    from jarvis.actuators.desktop import DesktopActuator
    current_cfg = load_config()
    idx = screen_index if screen_index is not None else getattr(current_cfg.desktop, "screen_index", 1)
    act = DesktopActuator(screen_index=idx)
    img, _ = act.capture_screenshot(max_dimension=640, target_screen_index=idx)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return Response(content=buf.getvalue(), media_type="image/jpeg", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

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

@app.get("/api/models")
async def list_available_models():
    """Fetch installed local models from Ollama."""
    models = []
    try:
        r = requests.get(f"{config.model.ollama_url}/api/tags", timeout=3)
        if r.status_code == 200:
            for m in r.json().get("models", []):
                size_gb = round(m.get("size", 0) / (1024**3), 2)
                models.append({
                    "name": m.get("name", ""),
                    "size": f"{size_gb} GB",
                    "modified": m.get("modified_at", "")[:10],
                })
    except Exception as e:
        error_tracker.log_error("OllamaConnectionError", str(e))

    return {
        "models": models,
        "current": {
            "local_text_model": config.model.local_text_model,
            "local_vision_model": config.model.local_vision_model,
            "tier0_model": config.model.tier0_model,
            "tier0_enabled": config.model.tier0_enabled,
        },
    }

@app.post("/api/models/select")
async def select_models(req: ModelSelectionRequest):
    """Update selected local models in configuration."""
    global config
    if req.local_text_model:
        config.model.local_text_model = req.local_text_model
    if req.local_vision_model:
        config.model.local_vision_model = req.local_vision_model
    if req.tier0_model:
        config.model.tier0_model = req.tier0_model
    save_config(config)
    return {"status": "updated", "current": config.model.model_dump()}

@app.get("/api/errors")
async def get_system_errors():
    """Get list of system errors, timeouts, and failures."""
    return error_tracker.get_errors()

@app.post("/api/errors/clear")
async def clear_system_errors():
    """Clear error history."""
    error_tracker.clear()
    return {"status": "cleared"}

@app.post("/api/brief")
async def trigger_daily_brief():
    """Manually trigger the Daily brief."""
    msg = cron_engine.trigger_brief()
    await broadcast_ws("briefing", msg)
    return {"status": "delivered", "briefing": msg}

@app.post("/api/voice/toggle")
async def toggle_voice_setting(mode: str = "reply_on_chat"):
    """Toggle voice reply settings."""
    global config
    if mode == "always":
        config.voice.always_voice_response = not config.voice.always_voice_response
    elif mode == "reply_on_chat":
        config.voice.voice_reply_on_chat = not config.voice.voice_reply_on_chat
    elif mode == "mute":
        config.voice.enabled = not config.voice.enabled
    save_config(config)
    return {
        "voice_enabled": config.voice.enabled,
        "always_voice_response": config.voice.always_voice_response,
        "voice_reply_on_chat": config.voice.voice_reply_on_chat,
    }

@app.post("/api/settings/conversation-mode")
async def set_conversation_mode(req: ConversationModeRequest):
    """Set conversational interaction mode: audio_only, audio+chat, or chat_only."""
    global config
    config = load_config()
    config.conversation_mode = req.mode
    if req.mode == "audio_only":
        config.output_mode = "voice"
        config.voice.enabled = True
        config.voice.always_voice_response = True
        config.voice.voice_reply_on_chat = True
    elif req.mode == "audio+chat":
        config.output_mode = "both"
        config.voice.enabled = True
        config.voice.voice_reply_on_chat = True
        config.voice.always_voice_response = False
    elif req.mode == "chat_only":
        config.output_mode = "cli"
        config.voice.enabled = False
        config.voice.always_voice_response = False
        config.voice.voice_reply_on_chat = False
    save_config(config)
    await broadcast_ws("conversation_mode_changed", {
        "conversation_mode": config.conversation_mode,
        "output_mode": config.output_mode,
        "voice_enabled": config.voice.enabled,
    })
    return {
        "status": "updated",
        "conversation_mode": config.conversation_mode,
        "output_mode": config.output_mode,
        "voice_enabled": config.voice.enabled,
    }

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
