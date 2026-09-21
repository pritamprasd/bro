"""Core ReAct Agent Orchestrator for Jarvis Phase 2."""

import json
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
from jarvis.core.safety import SafetyClassifier
from jarvis.memory.store import MemoryStore
from jarvis.models.base import ChatMessage, ModelResponse
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
18. `finish(result)`: Task is finished. Provide the final response to the user.

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
    def __init__(self, config: JarvisConfig):
        self.config = config
        self.console = JarvisConsole(output_mode=config.output_mode)
        self.router = ModelRouter(config.model)
        self.tier0 = Tier0Router(config.model)
        self.desktop = DesktopActuator()
        self.browser = BrowserActuator(config.browser)
        self.cdp_browser = CDPBrowserActuator(port=config.browser.cdp_port)
        self.python_runner = PythonRunner()
        self.shell = ShellActuator()
        self.macro_recorder = MacroRecorder()
        self.memory = MemoryStore(config.memory)
        self.vault = SecretVault()
        self.safety = SafetyClassifier(config.safety)
        self.overlay = ApprovalOverlay()
        self.tts = TextToSpeech(config.voice)
        self.audit = AuditManager()

    def run_task(self, user_goal: str, max_steps: int = 15) -> str:
        """Execute a user goal through perception, reasoning, and action."""
        self.console.banner()
        self.console.console.print(f"[bold]Goal:[/bold] {user_goal}\n")

        # 0. Start Audit Run
        self.audit.start_run(user_goal)

        # 1. Tier-0 Fast Classification (sub-100ms)
        tier0_result = self.tier0.classify(user_goal)
        self.console.thought(f"[Tier-0 Intent: {tier0_result.intent}] {tier0_result.summary} ({tier0_result.elapsed_ms}ms)")

        # 2. On-demand lean memory loading
        relevant_memory = self.memory.get_relevant_memory(user_goal)
        system_instructions = SYSTEM_PROMPT
        if relevant_memory:
            system_instructions += f"\n\nContext & Relevant Memory:\n{relevant_memory}"

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
                self._deliver_output(final_result)
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

            else:
                from jarvis.actuators.base import ActionResult
                return ActionResult(success=False, error=f"Unknown action: {action}")

        except Exception as e:
            from jarvis.actuators.base import ActionResult
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

    def _deliver_output(self, text: str) -> None:
        """Deliver output according to configured output_mode ('both', 'cli', 'voice')."""
        if self.config.output_mode in ["both", "cli"]:
            self.console.response(text)
        if self.config.output_mode in ["both", "voice"]:
            self.tts.speak(text)
