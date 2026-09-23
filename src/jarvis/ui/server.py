import asyncio
import base64
import io
import json
import os
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
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
from jarvis.memory.calendar_engine import CalendarEngine
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
calendar_engine = CalendarEngine(memory_store.memory_dir / "calendar.md")
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

class MemoryDirRequest(BaseModel):
    memory_dir: str

class DesktopSelectRequest(BaseModel):
    screen_index: int

class ModelPolicyRequest(BaseModel):
    policy: Literal["local_only", "cloud_only", "tier_fallback"]
    cloud_model: Optional[str] = None

class ModelSelectionRequest(BaseModel):
    policy: Optional[str] = None
    local_text_model: Optional[str] = None
    local_vision_model: Optional[str] = None
    tier0_model: Optional[str] = None
    cloud_model: Optional[str] = None
    gemini_api_key: Optional[str] = None

class WatchdogToggleRequest(BaseModel):
    target: str

class AutonomousModeRequest(BaseModel):
    autonomous_mode: bool

class VoiceSelectionRequest(BaseModel):
    voice: Optional[str] = None
    rate: Optional[str] = None
    pitch: Optional[str] = None
    volume: Optional[int] = None
    stt_engine: Optional[Literal["browser", "whisper_local"]] = None
    sfx_enabled: Optional[bool] = None

class ObsidianConfigRequest(BaseModel):
    obsidian_vault_dir: str
    semantic_search_enabled: Optional[bool] = True

class VoicePreviewRequest(BaseModel):
    voice: Optional[str] = None
    rate: Optional[str] = None
    pitch: Optional[str] = None
    volume: Optional[int] = None
    text: Optional[str] = None

class CalendarEventRequest(BaseModel):
    title: str
    date: str
    time: Optional[str] = ""
    tags: Optional[List[str]] = []

class CalendarToggleRequest(BaseModel):
    identifier: Union[int, str]
    completed: Optional[bool] = None

main_event_loop: Optional[asyncio.AbstractEventLoop] = None

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
    global main_event_loop
    try:
        loop = main_event_loop
        if not loop or loop.is_closed():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_ws(event, data), loop)
    except Exception:
        pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()
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
        "tts_voice": current_cfg.voice.tts_voice,
        "tts_rate": current_cfg.voice.tts_rate,
        "tts_volume": getattr(current_cfg.voice, "tts_volume", 100),
        "stt_engine": getattr(current_cfg.voice, "stt_engine", "browser"),
        "sfx_enabled": getattr(current_cfg.voice, "sfx_enabled", True),
        "obsidian_vault_dir": getattr(current_cfg.memory, "obsidian_vault_dir", None),
        "semantic_search_enabled": getattr(current_cfg.memory, "semantic_search_enabled", True),
        "rag_chunks": len(memory_store.rag.chunks) if (hasattr(memory_store, "rag") and memory_store.rag) else 0,
        "spotlight_enabled": current_cfg.spotlight.enabled,
        "cloud_model": current_cfg.model.cloud_model,
        "has_gemini_api_key": bool(current_cfg.model.gemini_api_key or os.getenv("GEMINI_API_KEY")),
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
    orig_response = agent.console.response

    def ws_thought(text: str):
        orig_thought(text)
        sync_broadcast("thought", text)

    def ws_action(act: str, detail: str):
        orig_action(act, detail)
        sync_broadcast("action", {"actuator": act, "detail": detail})
        if act == "pre_response":
            sync_broadcast("pre_response", {"text": detail, "conversation_mode": run_config.conversation_mode})

    def ws_step(num: int, total: int, desc: str):
        orig_step(num, total, desc)
        sync_broadcast("step", {"step": num, "total": total, "desc": desc})

    def ws_response(text: str):
        orig_response(text)
        sync_broadcast("task_response", {
            "text": text,
            "conversation_mode": run_config.conversation_mode
        })

    agent.console.thought = ws_thought
    agent.console.action = ws_action
    agent.console.step = ws_step
    agent.console.response = ws_response

    # Run in thread pool so server remains responsive
    global main_event_loop
    loop = asyncio.get_running_loop()
    main_event_loop = loop
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

@app.get("/api/history/{run_id}/download")
async def download_run_report(run_id: str, format: str = "md"):
    """Direct browser attachment download endpoint for mission audit reports (markdown, html, json)."""
    details = audit.get_run(run_id)
    if not details:
        raise HTTPException(status_code=404, detail="Run not found")

    fmt = format.lower().strip()
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", details.get("goal", "mission")[:25]).strip("_")

    if fmt == "html":
        content = audit.export_run_html(run_id)
        filename = f"jarvis_report_{run_id}_{safe_slug}.html"
        media_type = "text/html"
    elif fmt == "json":
        content = audit.export_run_json(run_id)
        filename = f"jarvis_report_{run_id}_{safe_slug}.json"
        media_type = "application/json"
    else:
        content = audit.export_run_markdown(run_id)
        filename = f"jarvis_report_{run_id}_{safe_slug}.md"
        media_type = "text/markdown"

    return Response(
        content=content,
        media_type=f"{media_type}; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )

@app.post("/api/history/clear")
async def clear_audit_history():
    """Backup all mission runs to ~/ai-memory/jarvis/backups/ and reset audit logs/metrics."""
    result = audit.backup_and_clear()
    await broadcast_ws("history_cleared", result)
    return result

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

@app.post("/api/watchdogs/toggle")
async def toggle_watchdog(req: WatchdogToggleRequest):
    """Toggle a proactive sentinel or automation feature on/off."""
    global config
    target = req.target.lower().strip()
    msg = ""
    if target == "sentinel":
        config.watchdogs.sentinel.enabled = not config.watchdogs.sentinel.enabled
        state = config.watchdogs.sentinel.enabled
        msg = f"Thermal Sentinel {'enabled' if state else 'disabled'}"
    elif target == "organizer":
        config.watchdogs.organizer.enabled = not config.watchdogs.organizer.enabled
        state = config.watchdogs.organizer.enabled
        msg = f"Download Auto-Organizer {'enabled' if state else 'disabled'}"
    elif target == "tier0":
        config.model.tier0_enabled = not config.model.tier0_enabled
        state = config.model.tier0_enabled
        msg = f"Tier-0 Fast Classifier {'enabled' if state else 'disabled'}"
    elif target == "spotlight":
        config.spotlight.enabled = not config.spotlight.enabled
        state = config.spotlight.enabled
        msg = f"Spotlight Alt+J {'enabled' if state else 'disabled'}"
    elif target == "cdp":
        if not cdp_browser.is_cdp_available():
            await cdp_browser.connect()
        state = cdp_browser.is_cdp_available()
        msg = f"Everyday Chrome CDP {'connected (:9222)' if state else 'standby'}"
    elif target == "telegram":
        config.watchdogs.cron.enabled = not config.watchdogs.cron.enabled
        state = config.watchdogs.cron.enabled
        msg = f"Telegram/Cron Remote {'enabled' if state else 'disabled'}"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown watchdog target: {target}")

    save_config(config)
    await broadcast_ws("watchdog_toggled", {
        "target": target,
        "state": state,
        "message": msg,
    })
    return {
        "status": "success",
        "target": target,
        "state": state,
        "message": msg,
        "config": {
            "sentinel": config.watchdogs.sentinel.enabled,
            "organizer": config.watchdogs.organizer.enabled,
            "tier0": config.model.tier0_enabled,
            "spotlight": config.spotlight.enabled,
            "cdp": cdp_browser.is_cdp_available(),
            "telegram": config.watchdogs.cron.enabled,
        }
    }

@app.post("/api/settings/autonomous")
async def toggle_autonomous_mode(req: AutonomousModeRequest):
    """Toggle full autonomy vs human approval overlay."""
    global config
    config.autonomous_mode = req.autonomous_mode
    save_config(config)
    await broadcast_ws("autonomous_mode_changed", {"autonomous_mode": config.autonomous_mode})
    return {
        "status": "updated",
        "autonomous_mode": config.autonomous_mode,
        "label": "ON (Full Autonomy)" if config.autonomous_mode else "OFF (Approval Overlay Active)",
    }

@app.post("/api/safety/test-overlay")
async def test_approval_overlay():
    """Trigger a preview of the on-screen safety approval overlay."""
    from jarvis.core.safety import RiskAssessment
    from jarvis.ui.overlay import ApprovalOverlay
    overlay = ApprovalOverlay()
    sample = RiskAssessment(
        is_high_stakes=True,
        risk_level="critical",
        reason="Destructive system file modification detected: Recursive purge of temporary cache & service restart.",
        action_type="run_bash",
        action_details="rm -rf /tmp/jarvis_sandbox_test/ && echo 'Safety Gatekeeper Test Action'"
    )
    loop = asyncio.get_event_loop()
    approved = await loop.run_in_executor(None, overlay.request_approval, sample)
    return {"status": "completed", "approved": approved}

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

@app.get("/api/memory/config")
async def get_memory_config():
    obsidian_p = str(memory_store.rag.obsidian_dir) if (hasattr(memory_store, "rag") and memory_store.rag and memory_store.rag.obsidian_dir) else ""
    return {
        "memory_dir": config.memory.memory_dir,
        "resolved_path": str(memory_store.memory_dir),
        "default_memory_dir": "~/ai-memory/jarvis",
        "obsidian_vault_dir": getattr(config.memory, "obsidian_vault_dir", "~/obsidian/KnowledgeBase/ai-memory"),
        "resolved_obsidian_path": obsidian_p,
        "semantic_search_enabled": getattr(config.memory, "semantic_search_enabled", True),
        "total_chunks": len(memory_store.rag.chunks) if hasattr(memory_store, "rag") else 0,
    }

@app.post("/api/memory/config")
async def update_memory_config(req: MemoryDirRequest):
    global memory_store, config, calendar_engine
    new_dir = req.memory_dir.strip()
    if not new_dir:
        raise HTTPException(status_code=400, detail="Memory directory path cannot be empty.")
    
    config.memory.memory_dir = new_dir
    save_config(config)
    
    # Reinitialize memory store with new path (creates directory and migrates legacy if applicable)
    memory_store = MemoryStore(config.memory)
    calendar_engine = CalendarEngine(memory_store.memory_dir / "calendar.md")
    
    return {
        "status": "updated",
        "memory_dir": config.memory.memory_dir,
        "resolved_path": str(memory_store.memory_dir),
    }

@app.post("/api/memory/obsidian")
async def update_obsidian_config(req: ObsidianConfigRequest):
    """Link user's Obsidian Vault for hybrid BM25 + semantic retrieval."""
    global memory_store, config
    new_obsidian = req.obsidian_vault_dir.strip()
    config.memory.obsidian_vault_dir = new_obsidian
    if req.semantic_search_enabled is not None:
        config.memory.semantic_search_enabled = req.semantic_search_enabled
    save_config(config)

    memory_store = MemoryStore(config.memory)
    total = memory_store.rag.refresh_index() if hasattr(memory_store, "rag") else 0
    obsidian_p = str(memory_store.rag.obsidian_dir) if (hasattr(memory_store, "rag") and memory_store.rag and memory_store.rag.obsidian_dir) else ""

    return {
        "status": "updated",
        "obsidian_vault_dir": config.memory.obsidian_vault_dir,
        "resolved_obsidian_path": obsidian_p,
        "semantic_search_enabled": config.memory.semantic_search_enabled,
        "total_chunks": total,
    }

@app.post("/api/memory/reindex")
async def reindex_memory():
    """Trigger real-time re-indexing of memory files and Obsidian knowledge base."""
    global memory_store
    total = memory_store.rag.refresh_index() if hasattr(memory_store, "rag") else 0
    return {"status": "reindexed", "total_chunks": total}

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

    has_key = bool(config.model.gemini_api_key or os.getenv("GEMINI_API_KEY"))
    cloud_models = [
        {"id": "gemini-2.5-flash", "name": "Gemini 3.8 / 2.5 Flash (Free Tier)", "recommended": True},
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash (Fast Reasoning)", "recommended": False},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (Standard)", "recommended": False},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Deep Reasoning)", "recommended": False},
    ]

    return {
        "models": models,
        "cloud_models": cloud_models,
        "current": {
            "policy": config.model.policy,
            "local_text_model": config.model.local_text_model,
            "local_vision_model": config.model.local_vision_model,
            "tier0_model": config.model.tier0_model,
            "tier0_enabled": config.model.tier0_enabled,
            "cloud_model": config.model.cloud_model,
            "has_gemini_api_key": has_key,
        },
    }

@app.post("/api/models/select")
async def select_models(req: ModelSelectionRequest):
    """Update selected models and routing policy in configuration."""
    global config
    if req.policy:
        config.model.policy = req.policy
    if req.local_text_model:
        config.model.local_text_model = req.local_text_model
    if req.local_vision_model:
        config.model.local_vision_model = req.local_vision_model
    if req.tier0_model:
        config.model.tier0_model = req.tier0_model
    if req.cloud_model:
        config.model.cloud_model = req.cloud_model
    if req.gemini_api_key is not None:
        val = req.gemini_api_key.strip()
        config.model.gemini_api_key = val if val else None
    save_config(config)
    await broadcast_ws("model_policy_changed", {
        "policy": config.model.policy,
        "cloud_model": config.model.cloud_model,
        "local_text_model": config.model.local_text_model,
        "local_vision_model": config.model.local_vision_model,
        "tier0_model": config.model.tier0_model,
    })
    return {"status": "updated", "current": config.model.model_dump()}

@app.post("/api/models/policy")
async def set_model_policy(req: ModelPolicyRequest):
    """Quick-switch between Local LLM, Cloud Gemini 3.8 Flash, or Hybrid."""
    global config
    config.model.policy = req.policy
    if req.cloud_model:
        config.model.cloud_model = req.cloud_model
    save_config(config)
    await broadcast_ws("model_policy_changed", {
        "policy": config.model.policy,
        "cloud_model": config.model.cloud_model,
    })
    return {"status": "updated", "policy": config.model.policy, "cloud_model": config.model.cloud_model}

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

cached_voices: Optional[List[Dict[str, Any]]] = None

CURATED_VOICES: List[Dict[str, Any]] = [
    {"short_name": "en-GB-RyanNeural", "name": "British English - Ryan (Jarvis Butler Default)", "gender": "Male", "locale": "en-GB", "recommended": True},
    {"short_name": "en-GB-SoniaNeural", "name": "British English - Sonia", "gender": "Female", "locale": "en-GB", "recommended": True},
    {"short_name": "en-GB-ThomasNeural", "name": "British English - Thomas (Classic British)", "gender": "Male", "locale": "en-GB", "recommended": False},
    {"short_name": "en-GB-LibbyNeural", "name": "British English - Libby", "gender": "Female", "locale": "en-GB", "recommended": False},
    {"short_name": "en-US-GuyNeural", "name": "US English - Guy (Natural Assistant)", "gender": "Male", "locale": "en-US", "recommended": True},
    {"short_name": "en-US-JennyNeural", "name": "US English - Jenny (Natural Assistant)", "gender": "Female", "locale": "en-US", "recommended": True},
    {"short_name": "en-US-ChristopherNeural", "name": "US English - Christopher (Tactical / Deep)", "gender": "Male", "locale": "en-US", "recommended": True},
    {"short_name": "en-US-AriaNeural", "name": "US English - Aria (Expressive)", "gender": "Female", "locale": "en-US", "recommended": False},
    {"short_name": "en-US-EricNeural", "name": "US English - Eric", "gender": "Male", "locale": "en-US", "recommended": False},
    {"short_name": "en-US-RogerNeural", "name": "US English - Roger (Deep)", "gender": "Male", "locale": "en-US", "recommended": False},
    {"short_name": "en-AU-WilliamMultilingualNeural", "name": "Australian English - William", "gender": "Male", "locale": "en-AU", "recommended": False},
    {"short_name": "en-AU-NatashaNeural", "name": "Australian English - Natasha", "gender": "Female", "locale": "en-AU", "recommended": False},
    {"short_name": "en-CA-LiamNeural", "name": "Canadian English - Liam", "gender": "Male", "locale": "en-CA", "recommended": False},
    {"short_name": "en-CA-ClaraNeural", "name": "Canadian English - Clara", "gender": "Female", "locale": "en-CA", "recommended": False},
    {"short_name": "en-IN-PrabhatNeural", "name": "Indian English - Prabhat", "gender": "Male", "locale": "en-IN", "recommended": False},
    {"short_name": "en-IN-NeerjaNeural", "name": "Indian English - Neerja", "gender": "Female", "locale": "en-IN", "recommended": False},
    {"short_name": "en-IE-ConnorNeural", "name": "Irish English - Connor", "gender": "Male", "locale": "en-IE", "recommended": False},
]

@app.get("/api/voice/voices")
async def get_available_voices():
    """List available Edge-TTS neural voices with current selection."""
    global cached_voices
    voices_list = cached_voices
    if not voices_list:
        try:
            import edge_tts
            raw_voices = await edge_tts.list_voices()
            en_voices = []
            other_voices = []
            rec_ids = {"en-GB-RyanNeural", "en-GB-SoniaNeural", "en-US-GuyNeural", "en-US-JennyNeural", "en-US-ChristopherNeural"}
            for v in raw_voices:
                s_name = v.get("ShortName", "")
                locale = v.get("Locale", "")
                gender = v.get("Gender", "Unknown")
                f_name = v.get("FriendlyName", s_name)
                clean_name = f_name.replace("Microsoft ", "").replace(" Online (Natural)", "").replace(" (Preview)", "")
                item = {
                    "short_name": s_name,
                    "name": clean_name,
                    "gender": gender,
                    "locale": locale,
                    "recommended": s_name in rec_ids or "Ryan" in s_name or "Guy" in s_name or "Jenny" in s_name,
                }
                if locale.startswith("en-"):
                    en_voices.append(item)
                else:
                    other_voices.append(item)
            en_voices.sort(key=lambda x: (not x["recommended"], x["short_name"]))
            voices_list = en_voices + other_voices
            cached_voices = voices_list
        except Exception as e:
            print(f"[Voice Warning] Failed to fetch online voices: {e}")
            voices_list = CURATED_VOICES

    return {
        "voices": voices_list,
        "current_voice": config.voice.tts_voice,
        "current_rate": config.voice.tts_rate,
        "current_pitch": config.voice.tts_pitch,
        "voice_enabled": config.voice.enabled,
    }

@app.post("/api/voice/select")
async def select_voice(req: VoiceSelectionRequest):
    """Set the active speech synthesis voice, speed rate, and/or volume."""
    global config, tts
    if req.voice:
        config.voice.tts_voice = req.voice
    if req.rate is not None:
        config.voice.tts_rate = req.rate
    if req.pitch is not None:
        config.voice.tts_pitch = req.pitch
    if req.volume is not None:
        config.voice.tts_volume = max(0, min(100, int(req.volume)))
    if req.stt_engine:
        config.voice.stt_engine = req.stt_engine
    if req.sfx_enabled is not None:
        config.voice.sfx_enabled = req.sfx_enabled
    save_config(config)
    tts = TextToSpeech(config.voice)
    await broadcast_ws("voice_changed", {
        "tts_voice": config.voice.tts_voice,
        "tts_rate": config.voice.tts_rate,
        "tts_pitch": config.voice.tts_pitch,
        "tts_volume": getattr(config.voice, "tts_volume", 100),
        "stt_engine": getattr(config.voice, "stt_engine", "browser"),
        "sfx_enabled": getattr(config.voice, "sfx_enabled", True),
    })
    return {
        "status": "updated",
        "current_voice": config.voice.tts_voice,
        "current_rate": config.voice.tts_rate,
        "current_pitch": config.voice.tts_pitch,
        "current_volume": getattr(config.voice, "tts_volume", 100),
        "stt_engine": getattr(config.voice, "stt_engine", "browser"),
        "sfx_enabled": getattr(config.voice, "sfx_enabled", True),
    }

@app.post("/api/voice/stop")
async def stop_voice():
    """Halt ongoing speech playback immediately (Barge-in)."""
    global current_agent_instance, tts
    if current_agent_instance and hasattr(current_agent_instance, "tts"):
        current_agent_instance.tts.stop()
    if tts:
        tts.stop()
    await broadcast_ws("voice_stopped", {"status": "halted"})
    return {"status": "stopped", "message": "Voice playback interrupted"}

@app.post("/api/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe uploaded audio buffer using local GPU Faster-Whisper."""
    from jarvis.voice.stt import SpeechToText
    stt_runner = SpeechToText(config.voice)
    content = await file.read()
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    text = stt_runner.transcribe_bytes(content, suffix=suffix)
    return {"status": "success", "text": text}

@app.post("/api/voice/preview")
async def preview_voice(req: VoicePreviewRequest):
    """Synthesize and play sample speech for voice testing."""
    voice_to_test = req.voice or config.voice.tts_voice
    rate_to_test = req.rate or config.voice.tts_rate
    vol_to_test = req.volume if req.volume is not None else getattr(config.voice, "tts_volume", 100)
    sample_text = req.text or "Greetings. Jarvis Mark 2 neural speech synthesis is online and operational."
    temp_cfg = config.voice.model_copy()
    temp_cfg.tts_voice = voice_to_test
    temp_cfg.tts_rate = rate_to_test
    temp_cfg.tts_volume = vol_to_test
    temp_cfg.enabled = True
    test_tts = TextToSpeech(temp_cfg)
    test_tts.speak(sample_text, blocking=False)
    return {
        "status": "playing",
        "voice": voice_to_test,
        "rate": rate_to_test,
        "volume": vol_to_test,
        "text": sample_text,
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

@app.get("/api/voice/greeting")
async def get_voice_greeting():
    """Retrieve a random contextual greeting from greetings.md."""
    greeting = memory_store.get_random_greeting()
    return {"greeting": greeting}

@app.get("/api/calendar")
async def get_calendar_events():
    """Fetch all events and pending items from calendar.md."""
    events = calendar_engine.get_events()
    pending = calendar_engine.get_pending_events()
    return {"events": events, "pending": pending}

@app.post("/api/calendar")
async def add_calendar_event(req: CalendarEventRequest):
    """Add a scheduled task or event to calendar.md."""
    if not req.title or not req.date:
        raise HTTPException(status_code=400, detail="Title and date are required.")
    event = calendar_engine.add_event(title=req.title, event_date=req.date, event_time=req.time or "", tags=req.tags)
    await broadcast_ws("calendar_updated", {"action": "add", "event": event})
    return {"status": "success", "event": event}

@app.post("/api/calendar/toggle")
async def toggle_calendar_event(req: CalendarToggleRequest):
    """Toggle event completion status in calendar.md."""
    ok = calendar_engine.toggle_event(req.identifier, completed=req.completed)
    if not ok:
        raise HTTPException(status_code=404, detail="Event not found")
    await broadcast_ws("calendar_updated", {"action": "toggle", "identifier": req.identifier})
    return {"status": "success"}

@app.get("/api/calendar/today")
async def get_calendar_today_summary():
    """Get natural language vocal summary for today's schedule."""
    summary = calendar_engine.get_today_summary()
    return {"summary": summary}

@app.post("/api/system/setup-shortcut")
async def setup_ubuntu_shortcut():
    """Configure Ubuntu GNOME custom keybinding Super+Shift+J for Jarvis HUD."""
    import subprocess
    script_path = Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "setup_ubuntu_shortcut.sh"
    if script_path.exists():
        proc = subprocess.run(["bash", str(script_path)], capture_output=True, text=True)
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "output": proc.stdout or proc.stderr,
        }
    return {"status": "error", "message": "Shortcut script not found"}

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
