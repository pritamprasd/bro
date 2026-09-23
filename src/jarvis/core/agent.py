"""Core ReAct Agent Orchestrator for Jarvis Phase 2."""

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from jarvis.actuators.browser import BrowserActuator
from jarvis.actuators.cdp_browser import CDPBrowserActuator
from jarvis.actuators.desktop import DesktopActuator
from jarvis.actuators.python_runner import PythonRunner
from jarvis.actuators.recorder import MacroRecorder
from jarvis.actuators.shell import ShellActuator
from jarvis.config import JarvisConfig
from jarvis.core.audit import AuditManager
from jarvis.core.errors import error_tracker
from jarvis.core.safety import SafetyClassifier
from jarvis.memory.calendar_engine import CalendarEngine
from jarvis.memory.store import MemoryStore
from jarvis.models.base import ChatMessage, ModelResponse
from jarvis.models.local_matcher import LocalIntentMatcher
from jarvis.models.router import ModelRouter
from jarvis.models.tier0 import Tier0Router
from jarvis.security.vault import SecretVault
from jarvis.ui.console import JarvisConsole
from jarvis.ui.overlay import ApprovalOverlay
from jarvis.voice.tts import TextToSpeech

SYSTEM_PROMPT = """You are Jarvis, an elite personal AI assistant executing tasks on a Linux X11 workstation.
You have actuators to control the desktop GUI, an isolated Playwright web browser, your everyday browser via CDP, a local Python runner, and bash shell.

Available Actions:
1. `desktop_ground_and_act(instruction)`: Take a screenshot of the X11 desktop, identify the target element using computer vision, and click/type.
2. `desktop_click(x, y, button="left", clicks=1)`: Click directly at physical coordinates (x, y).
3. `desktop_type(text)`: Type text on keyboard into current active window.
4. `desktop_press_key(key)`: Press a key like "enter", "esc", "tab", "backspace".
5. `desktop_hotkey(keys)`: Press a key combo like ["ctrl", "c"], ["alt", "tab"].
6. `browser_navigate(url)`: Open or navigate the isolated Playwright browser to a URL.
7. `browser_click(selector=None, x=None, y=None)`: Click in the isolated browser.
8. `browser_type(text, selector=None)`: Type text into a browser input field.
9. `browser_get_text()`: Read the visible page content of the active browser page.
10. `browser_cdp_navigate(url)`: Navigate everyday Chrome/Brave browser (via CDP :9222).
11. `browser_cdp_click(selector)`: Click in everyday Chrome/Brave browser (via CDP :9222).
12. `browser_cdp_get_text()`: Read content from everyday Chrome/Brave browser.
13. `run_python(code)`: Execute Python code (e.g. data processing, math, Telegram bot API calls via requests).
14. `run_shell(command)`: Execute a safe bash shell command.
15. `run_macro(macro_name)`: Execute a previously compiled deterministic macro.
16. `get_secret(key)`: Retrieve a credential from the secure vault (e.g. "telegram_bot_token").
17. `save_workflow(topic, content)`: Save a learned workflow or note to persistent memory.
18. `request_file(description, expected_filename=None)`: Ask the user to supply a required file, dataset, or image if it was not provided or not found.
19. `show_media(media_type, content, title="Visual Display", caption=None, target="auto")`: Display a diagram (mermaid), chart (svg or image path), or image to the user in a dialog or desktop system window.
20. `manage_calendar(sub_action, title=None, date=None, time=None, tags=None, identifier=None)`: Manage workstation schedule and tasks (sub_action="add"|"toggle"|"today"|"list").
21. `desktop_switch_monitor(screen_index)`: Switch which desktop monitor Jarvis interacts with (0=all displays combined, 1=display 1, 2=display 2).
22. `desktop_inspect_screen(screen_index=None)`: Take a high-resolution screenshot of the active desktop monitor, observe active windows, and report visual state.
23. `finish(result)`: Task is finished. Provide the final response to the user.

CRITICAL INSTRUCTIONS & MARK 3 BEHAVIOR:
1. EXPLANATION PROTOCOL:
   When the user asks you to explain any concept, topic, system, code, or architecture:
   - First provide a crisp, executive summary (2-3 concise sentences).
   - Proactively ask the user if they would like to dig deeper into any specific technical details or components.
   - Whenever an explanation benefits from a visual structure, architecture diagram, flow, or comparison, generate a Mermaid diagram block (```mermaid ... ```) or call `show_media("diagram", content=...)`. The UI will render it in an expansive 90% screen dialog with your explanation streaming in the right sidebar.

2. SCREEN INSPECTION PROTOCOL:
   When asked to inspect the active screen or desktop, call `desktop_inspect_screen`. Always synthesize and explain what is open on the desktop (the active focused application, window title, open websites or tabs, IDE projects, or background apps) in a conversational, helpful manner, rather than just stating resolution or port numbers.

To call an action, output valid JSON in this exact structure:
```json
{
  "thought": "Your reasoning about what to do next",
  "action": "action_name",
  "params": { ... }
}
```
When you have finished the user's task, output:
```json
{
  "thought": "Task is complete",
  "action": "finish",
  "params": {
    "result": "Detailed answer or summary of actions performed"
  }
}
```
Always output ONLY the JSON object.
"""

class JarvisAgent:
    def __init__(self, config: JarvisConfig, request_file_cb: Optional[Any] = None, show_media_cb: Optional[Any] = None):
        self.config = config
        self.request_file_cb = request_file_cb
        self.show_media_cb = show_media_cb
        self.console = JarvisConsole(output_mode=config.output_mode)
        self.router = ModelRouter(config.model)
        self.tier0 = Tier0Router(config.model)
        screen_idx = getattr(self.config.desktop, "screen_index", 1) if hasattr(self.config, "desktop") else 1
        self.desktop = DesktopActuator(screen_index=screen_idx)
        self.browser = BrowserActuator(config.browser)
        self.cdp_browser = CDPBrowserActuator(port=config.browser.cdp_port)
        self.python_runner = PythonRunner()
        self.shell = ShellActuator()
        self.macro_recorder = MacroRecorder()
        self.memory = MemoryStore(config.memory)
        self.calendar = CalendarEngine(self.memory.memory_dir / "calendar.md")
        self.local_matcher = LocalIntentMatcher(self.memory.memory_dir, calendar_engine=self.calendar)
        self.vault = SecretVault()
        self.safety = SafetyClassifier(config.safety)
        self.overlay = ApprovalOverlay()
        self.tts = TextToSpeech(config.voice)
        self.audit = AuditManager()

    def run_task(self, user_goal: str, file_paths: Optional[List[str]] = None, max_steps: int = 15) -> str:
        """Execute a user goal through perception, reasoning, and action."""
        self.console.banner()

        # 0. Sub-5ms Local Intent & Templated Offline Fast-Path
        local_match = self.local_matcher.match_and_execute(user_goal)
        if local_match:
            self.console.thought(f"[Local Instant Intent: {local_match['pattern']}] Sub-5ms offline execution")
            if local_match.get("action_data") and self.show_media_cb:
                action_data = local_match["action_data"]
                if action_data.get("action") == "show_file_content":
                    try:
                        self.show_media_cb(
                            "file",
                            action_data["content"],
                            title=action_data["file_name"],
                            caption=f"Path: {action_data['file_path']}",
                        )
                    except Exception:
                        pass
            resp = local_match["response_text"]
            self._deliver_output(resp, is_conversation=True)
            self.audit.start_run(user_goal)
            self.audit.complete_run(resp, status="success")
            return resp

        # Handle attached resources
        if file_paths:
            file_summaries = []
            for fp in file_paths:
                p = Path(fp).expanduser()
                if p.exists():
                    size_kb = round(p.stat().st_size / 1024, 1)
                    content_preview = ""
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            lines = [f.readline() for _ in range(8)]
                            content_preview = "".join(lines)
                    except Exception:
                        pass
                    file_summaries.append(f"Attached Resource: '{p.name}' ({size_kb} KB, path: '{p.resolve()}')\nPreview:\n{content_preview}")
            user_goal += "\n\nAttached Resources:\n" + "\n---\n".join(file_summaries)

        self.console.console.print(f"[bold]Goal:[/bold] {user_goal}\n")

        # 0. Start Audit Run
        self.audit.start_run(user_goal)

        # 1. On-demand lean memory loading
        relevant_memory = self.memory.get_relevant_memory(user_goal)
        system_instructions = SYSTEM_PROMPT
        if relevant_memory:
            system_instructions += f"\n\nContext & Relevant Memory:\n{relevant_memory}"

        # 2. Tier-0 Fast Classification & Instant Response (sub-100ms)
        tier0_result = self.tier0.classify(user_goal, relevant_memory=relevant_memory)
        self.console.thought(f"[Tier-0 Intent: {tier0_result.intent}] {tier0_result.summary} ({tier0_result.elapsed_ms}ms)")

        # Fast path: Tier-0 direct response for conversational queries (greetings, QA, explanations)
        if tier0_result.intent == "CONVERSATION":
            direct_ans = tier0_result.direct_response
            if not direct_ans:
                direct_ans = self.tier0.respond_direct(user_goal, relevant_memory=relevant_memory)
            if direct_ans:
                self.console.thought(f"[Tier-0 Instant Response via {self.tier0.model_name}] Sub-second response active")
                self._deliver_output(direct_ans, is_conversation=True)
                self.audit.complete_run(direct_ans, status="success")
                return direct_ans

        # 3. Acoustic Pre-Response Acknowledgment (fills silence while LLM processes)
        if self.config.conversation_mode in ["audio_only", "audio+chat"] and self.config.voice.enabled:
            from jarvis.voice.pre_responses import get_random_pre_response
            pre_ack = get_random_pre_response()
            self.console.action("pre_response", pre_ack)
            self.tts.speak(pre_ack, blocking=False)

        messages = [
            ChatMessage(role="user", content=f"Goal: {user_goal}"),
        ]

        recorded_steps: List[Dict[str, Any]] = []

        for step_idx in range(1, max_steps + 1):
            self.console.step(step_idx, max_steps, "Thinking & Planning...")

            # Generate reasoning & next action
            try:
                model_resp: ModelResponse = self.router.generate_text(
                    messages=messages,
                    system_prompt=system_instructions,
                )
            except Exception as e:
                err_msg = f"Model execution failed: {e}"
                self.console.error(err_msg)
                error_tracker.log_error("ModelExecutionFailure", err_msg, context=f"Goal: {user_goal}", exc=e)
                self.audit.complete_run(err_msg, status="failed")
                return err_msg

            content = model_resp.content.strip()

            # Parse JSON action
            parsed_action = self._parse_action_json(content)
            if not parsed_action:
                self.console.warning("Could not parse JSON action. Retrying with format reminder...")
                messages.append(ChatMessage(role="assistant", content=content))
                messages.append(
                    ChatMessage(
                        role="user",
                        content="Error: Output must be a valid JSON object with 'thought', 'action', and 'params'.",
                    )
                )
                continue

            thought = parsed_action.get("thought", "")
            action_name = parsed_action.get("action", "")
            params = parsed_action.get("params", {})

            if thought:
                self.console.thought(thought)

            # Check for task completion
            if action_name == "finish":
                final_result = params.get("result", "Task finished successfully.")
                self.console.success("Task completed!")

                # Auto-detect Mermaid diagrams in final response
                mermaid_match = re.search(r"```mermaid\s*([\s\S]*?)```", final_result)
                if mermaid_match:
                    d_code = mermaid_match.group(1).strip()
                    self.show_media("diagram", d_code, title="Generated Diagram", caption="Rendered from assistant response", target="auto")

                # Auto-detect local image markdown in final response
                img_match = re.search(r"!\[(.*?)\]\((.*?)\)", final_result)
                if img_match:
                    c_text = img_match.group(1)
                    i_path = Path(img_match.group(2)).expanduser()
                    if i_path.exists():
                        self.show_media("image", str(i_path.resolve()), title=c_text or "Visual Result", caption=c_text, target="auto")

                self._deliver_output(final_result, is_conversation=(tier0_result.intent == "CONVERSATION"))
                self.audit.complete_run(final_result, status="success")

                # Compile macro if multi-step desktop/browser workflow
                if len(recorded_steps) >= 2:
                    macro_name = re.sub(r"[^a-zA-Z0-9_-]", "_", user_goal[:25]).strip("_")
                    self.macro_recorder.compile_macro(macro_name, recorded_steps)
                    self.console.thought(f"Compiled reusable macro: {macro_name}.py")

                return final_result

            # Safety Assessment
            assessment = self.safety.assess_action(
                action_type=action_name,
                details=json.dumps(params),
            )

            if assessment.is_high_stakes and not self.config.autonomous_mode:
                self.console.warning(f"High-Stakes Action Detected: {assessment.reason}")
                approved = self.overlay.request_approval(assessment)
                if not approved:
                    self.console.error("User rejected this action.")
                    messages.append(ChatMessage(role="assistant", content=content))
                    messages.append(
                        ChatMessage(
                            role="user",
                            content="Action was REJECTED by user. Do not attempt this destructive action again. Choose an alternative approach.",
                        )
                    )
                    continue
                else:
                    self.console.success("Action approved by user.")

            # Execute action
            self.console.action(action_name, str(params))
            action_result = self._dispatch_action(action_name, params)

            # Record step in Audit Manager & Macro Recorder
            obs_text = action_result.output if action_result.success else f"Error: {action_result.error}"
            self.audit.record_step(
                step_num=step_idx,
                thought=thought,
                action=action_name,
                params=params,
                observation=obs_text,
                success=action_result.success,
                screenshot_b64=action_result.screenshot_base64,
            )
            recorded_steps.append({"action": action_name, "params": params, "thought": thought})

            # Feedback loop
            messages.append(ChatMessage(role="assistant", content=content))
            messages.append(ChatMessage(role="user", content=f"Observation ({action_name}): {obs_text}"))

        timeout_msg = "Task reached maximum execution step limit."
        self.console.warning(timeout_msg)
        error_tracker.log_error("StepTimeout", timeout_msg, context=f"Goal: {user_goal}")
        self.audit.complete_run(timeout_msg, status="timeout")
        return timeout_msg

    def _dispatch_action(self, action: str, params: Dict[str, Any]):
        try:
            if action == "desktop_ground_and_act":
                _, b64 = self.desktop.capture_screenshot()
                w, h = self.desktop.get_screen_dimensions()
                instruction = params.get("instruction", "")
                pred = self.router.ground_coordinates(b64, instruction, w, h)
                self.console.thought(f"Grounding '{instruction}' -> ({pred.x}, {pred.y}) action={pred.action}")
                if pred.action in ["click", "none"]:
                    return self.desktop.click(pred.x, pred.y)
                elif pred.action == "double_click":
                    return self.desktop.double_click(pred.x, pred.y)
                elif pred.action == "right_click":
                    return self.desktop.right_click(pred.x, pred.y)
                elif pred.action == "type" and pred.text_to_type:
                    self.desktop.click(pred.x, pred.y)
                    return self.desktop.type_text(pred.text_to_type)
                else:
                    return self.desktop.click(pred.x, pred.y)

            elif action == "desktop_click":
                return self.desktop.click(
                    x=params.get("x", 0),
                    y=params.get("y", 0),
                    button=params.get("button", "left"),
                    clicks=params.get("clicks", 1),
                )

            elif action == "desktop_type":
                return self.desktop.type_text(params.get("text", ""))

            elif action == "desktop_press_key":
                return self.desktop.press_key(params.get("key", "enter"))

            elif action == "desktop_hotkey":
                return self.desktop.hotkey(params.get("keys", []))

            elif action == "desktop_switch_monitor":
                s_idx = params.get("screen_index", 1)
                self.desktop.set_screen_index(s_idx)
                info = self.desktop.get_active_monitor_info()
                from jarvis.actuators.base import ActionResult
                return ActionResult(success=True, output=f"Switched active desktop to Display {s_idx} ({info['output']}, {info['width']}x{info['height']}).")

            elif action == "desktop_inspect_screen":
                s_idx = params.get("screen_index")
                res = self.desktop.inspect_screen(s_idx)
                if res.success and res.screenshot_base64:
                    try:
                        import tempfile
                        buf = base64.b64decode(res.screenshot_base64)
                        t_path = Path(tempfile.gettempdir()) / f"jarvis_display_{self.desktop.screen_index}_inspect.png"
                        with open(t_path, "wb") as f:
                            f.write(buf)
                        self.show_media("image", str(t_path), title=f"Desktop Display {self.desktop.screen_index} Inspection", caption=f"Active Display: {self.desktop.get_active_monitor_info()['output']}", target="auto")
                    except Exception:
                        pass
                return res

            elif action == "browser_navigate":
                return self.browser.navigate(params.get("url", ""))

            elif action == "browser_click":
                return self.browser.click(
                    selector=params.get("selector"),
                    x=params.get("x"),
                    y=params.get("y"),
                )

            elif action == "browser_type":
                return self.browser.type_text(
                    text=params.get("text", ""),
                    selector=params.get("selector"),
                )

            elif action == "browser_get_text":
                return self.browser.get_text_content()

            elif action == "browser_cdp_navigate":
                return self.cdp_browser.navigate(params.get("url", ""))

            elif action == "browser_cdp_click":
                return self.cdp_browser.click(params.get("selector", ""))

            elif action == "browser_cdp_get_text":
                return self.cdp_browser.get_text_content()

            elif action == "run_macro":
                return self.macro_recorder.run_macro(params.get("macro_name", ""))

            elif action == "run_python":
                code = params.get("code", "")
                env = {}
                for k in self.vault.list_keys():
                    secret = self.vault.get_secret(k)
                    if secret:
                        env[k.upper()] = secret
                return self.python_runner.run_code(code, env_vars=env)

            elif action == "run_shell":
                return self.shell.run_command(params.get("command", ""))

            elif action == "get_secret":
                key = params.get("key", "")
                val = self.vault.get_secret(key)
                from jarvis.actuators.base import ActionResult
                if val:
                    return ActionResult(success=True, output=f"Secret '{key}' retrieved.")
                return ActionResult(success=False, error=f"Secret '{key}' not found in vault.")

            elif action == "save_workflow":
                topic = params.get("topic", "workflow")
                content = params.get("content", "")
                path = self.memory.save_workflow(topic, content)
                from jarvis.actuators.base import ActionResult
                return ActionResult(success=True, output=f"Saved workflow to {path}")

            elif action == "request_file":
                desc = params.get("description", "A required resource file")
                exp = params.get("expected_filename")
                from jarvis.actuators.base import ActionResult
                self.console.warning(f"Resource Needed: {desc}")

                supplied_path = None
                if self.request_file_cb:
                    supplied_path = self.request_file_cb(desc, exp)
                else:
                    from rich.prompt import Prompt
                    supplied_path = Prompt.ask(f"[bold yellow]Jarvis needs a file:[/bold yellow] {desc}\n[dim]Enter full file path[/dim]")

                if supplied_path and Path(supplied_path).exists():
                    p = Path(supplied_path).resolve()
                    self.console.success(f"User supplied file: {p.name}")
                    preview = ""
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            lines = [f.readline() for _ in range(12)]
                            preview = "".join(lines)
                    except Exception:
                        pass
                    return ActionResult(success=True, output=f"User supplied file at '{p}'. Content preview:\n{preview}")
                else:
                    return ActionResult(success=False, error=f"User cancelled or file '{supplied_path}' does not exist.")

            elif action == "show_media":
                m_type = params.get("media_type", "image")
                content = params.get("content", "")
                title = params.get("title", "Jarvis Visual Display")
                caption = params.get("caption")
                target = params.get("target", "auto")
                return self.show_media(m_type, content, title, caption, target)

            elif action == "manage_calendar":
                sub_action = params.get("sub_action", "list")
                from jarvis.actuators.base import ActionResult
                if sub_action == "add":
                    title = params.get("title", "")
                    dt = params.get("date", "")
                    tm = params.get("time", "")
                    tags = params.get("tags")
                    if not title or not dt:
                        return ActionResult(success=False, error="Parameters 'title' and 'date' are required to add an event.")
                    ev = self.calendar.add_event(title, dt, tm, tags)
                    return ActionResult(success=True, output=f"Added calendar event: {ev['title']} on {ev['date']} {ev['time']}.")
                elif sub_action == "toggle":
                    ident = params.get("identifier", "")
                    completed = params.get("completed")
                    ok = self.calendar.toggle_event(ident, completed)
                    return ActionResult(success=ok, output=f"Toggled event '{ident}'." if ok else f"Event '{ident}' not found.")
                elif sub_action == "today":
                    summary = self.calendar.get_today_summary()
                    return ActionResult(success=True, output=summary)
                else:
                    events = self.calendar.get_pending_events()
                    return ActionResult(success=True, output=f"Found {len(events)} pending calendar events: {json.dumps(events)}")

            else:
                from jarvis.actuators.base import ActionResult
                return ActionResult(success=False, error=f"Unknown action: {action}")

        except Exception as e:
            from jarvis.actuators.base import ActionResult
            return ActionResult(success=False, error=str(e))

    def show_media(self, media_type: str, content: str, title: str = "Jarvis Visual Display", caption: Optional[str] = None, target: str = "auto"):
        """Display a diagram, chart, or image to the user via dialog or system window."""
        from jarvis.actuators.base import ActionResult
        try:
            # Resolve image file paths if local
            resolved_content = content
            if media_type in ["image", "chart"]:
                p = Path(content).expanduser()
                if p.exists():
                    resolved_content = str(p.resolve())

            # 1. Callback (e.g. Web UI WebSocket broadcast)
            if self.show_media_cb:
                try:
                    self.show_media_cb(media_type, resolved_content, title, caption, target)
                except TypeError:
                    self.show_media_cb({
                        "media_type": media_type,
                        "content": resolved_content,
                        "title": title,
                        "caption": caption,
                        "target": target,
                    })
            elif target in ["auto", "window", "system_window"]:
                from jarvis.ui.system_window import SystemWindowManager
                SystemWindowManager.show_media(media_type, resolved_content, title, caption)

            self.console.action("show_media", f"{media_type.upper()}: '{title}' via {target}")
            return ActionResult(success=True, output=f"Displayed {media_type} '{title}' to user via {target}.")
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def _parse_action_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return None
        return None

    def _deliver_output(self, text: str, is_conversation: bool = False) -> None:
        """Deliver output according to configured conversation_mode, output_mode and voice settings."""
        if self.config.conversation_mode == "chat_only":
            self.console.response(text)
            return

        if self.config.conversation_mode == "audio_only":
            self.console.response(text)
            if self.config.voice.enabled:
                self.console.action("voice", "Speaking response...")
                self.tts.speak(text, blocking=True)
            return

        # Default / audio+chat mode
        if self.config.output_mode in ["both", "cli"]:
            self.console.response(text)

        should_speak = (
            self.config.output_mode in ["both", "voice"]
            or self.config.voice.always_voice_response
            or (self.config.voice.voice_reply_on_chat and is_conversation)
        )
        if should_speak and self.config.voice.enabled:
            self.console.action("voice", "Speaking response...")
            self.tts.speak(text, blocking=True)
