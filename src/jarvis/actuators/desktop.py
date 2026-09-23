"""Desktop Computer-Use Actuator for Linux X11 using mss, pyautogui, and pynput."""

import base64
import io
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple
import mss
from PIL import Image
import pyautogui
from jarvis.actuators.base import ActionResult, BaseActuator

# Configure PyAutoGUI
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True

class DesktopActuator(BaseActuator):
    def __init__(self, screen_index: int = 1):
        self._sct = mss.MSS()
        self.monitors = self._sct.monitors
        self.set_screen_index(screen_index)

    def reset(self) -> None:
        pass

    def set_screen_index(self, screen_index: int) -> None:
        """Switch the target desktop / monitor for screen capture and mouse actions."""
        if not hasattr(self, "monitors") or not self.monitors:
            self.monitors = self._sct.monitors
        total = len(self.monitors)
        # 0 is all monitors combined, 1..N are individual displays
        if 0 <= screen_index < total:
            self.screen_index = screen_index
        else:
            self.screen_index = 1 if total > 1 else 0

        target_mon = self.monitors[self.screen_index]
        self.width = target_mon["width"]
        self.height = target_mon["height"]
        self.left = target_mon["left"]
        self.top = target_mon["top"]

    def get_active_monitor_info(self) -> dict:
        target_mon = self.monitors[self.screen_index]
        return {
            "screen_index": self.screen_index,
            "width": self.width,
            "height": self.height,
            "left": self.left,
            "top": self.top,
            "output": target_mon.get("output", "DEFAULT"),
            "name": target_mon.get("name", f"Display {self.screen_index}"),
            "is_primary": target_mon.get("is_primary", False)
        }

    @classmethod
    def list_monitors(cls) -> List[dict]:
        """Detect and return all physical and virtual desktop displays."""
        with mss.MSS() as sct:
            res = []
            for idx, m in enumerate(sct.monitors):
                is_all = (idx == 0)
                is_primary = m.get("is_primary", False)
                output = m.get("output") or ("ALL-COMBINED" if is_all else f"DISPLAY-{idx}")
                name = m.get("name") or ("All Displays (Virtual Canvas)" if is_all else f"Display {idx}")
                
                if is_all:
                    label = f"Display 0: All Displays Combined ({m['width']}x{m['height']})"
                elif is_primary:
                    label = f"Display {idx}: {output} ({m['width']}x{m['height']}) [PRIMARY]"
                else:
                    label = f"Display {idx}: {output} ({m['width']}x{m['height']})"

                res.append({
                    "index": idx,
                    "name": name,
                    "output": output,
                    "width": m["width"],
                    "height": m["height"],
                    "left": m["left"],
                    "top": m["top"],
                    "is_primary": is_primary,
                    "label": label
                })
            return res

    def get_screen_dimensions(self) -> Tuple[int, int]:
        return self.width, self.height

    def capture_screenshot(self, max_dimension: Optional[int] = 1280, target_screen_index: Optional[int] = None) -> Tuple[Image.Image, str]:
        """Capture screenshot of chosen desktop monitor and return (PIL.Image, base64_png)."""
        idx = target_screen_index if target_screen_index is not None else self.screen_index
        target_mon = self.monitors[idx] if (0 <= idx < len(self.monitors)) else self.monitors[0]
        sct_img = self._sct.grab(target_mon)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        # Downscale for VLM if larger than max_dimension to preserve token speed
        if max_dimension and (img.width > max_dimension or img.height > max_dimension):
            ratio = min(max_dimension / img.width, max_dimension / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
        else:
            resized_img = img

        buffer = io.BytesIO()
        resized_img.save(buffer, format="PNG", optimize=True)
        b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return img, b64_str

    def get_open_windows_info(self) -> Dict[str, Any]:
        """Query X11 window hierarchy to find active focused window and open applications."""
        active_window = "Unknown"
        open_apps: List[str] = []
        try:
            # 1. Query active focused window
            p_active = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"], capture_output=True, text=True, timeout=2)
            match = re.search(r"window id # (0x[0-9a-fA-F]+)", p_active.stdout)
            active_id = match.group(1) if match else None

            if active_id and active_id != "0x0":
                p_win = subprocess.run(["xprop", "-id", active_id, "_NET_WM_NAME", "WM_CLASS"], capture_output=True, text=True, timeout=2)
                name_m = re.search(r'_NET_WM_NAME\([^\)]+\)\s*=\s*"(.*)"', p_win.stdout)
                class_m = re.search(r'WM_CLASS\([^\)]+\)\s*=\s*"([^"]*)",\s*"([^"]*)"', p_win.stdout)
                title = name_m.group(1) if name_m else ""
                app = class_m.group(2) if class_m else (class_m.group(1) if class_m else "")
                if app and title:
                    active_window = f"{app} - '{title}'"
                elif app or title:
                    active_window = app or title

            # 2. Query open windows client list
            p_clients = subprocess.run(["xprop", "-root", "_NET_CLIENT_LIST"], capture_output=True, text=True, timeout=2)
            win_ids = re.findall(r"0x[0-9a-fA-F]+", p_clients.stdout)
            seen_titles = set()
            for wid in win_ids:
                p_item = subprocess.run(["xprop", "-id", wid, "_NET_WM_NAME", "WM_CLASS"], capture_output=True, text=True, timeout=1)
                name_m = re.search(r'_NET_WM_NAME\([^\)]+\)\s*=\s*"(.*)"', p_item.stdout)
                class_m = re.search(r'WM_CLASS\([^\)]+\)\s*=\s*"([^"]*)",\s*"([^"]*)"', p_item.stdout)
                title = name_m.group(1) if name_m else ""
                app = class_m.group(2) if class_m else (class_m.group(1) if class_m else "")
                
                # Filter out background or blank window entries
                if app in ("Gjs", "Desktop") and not title:
                    continue
                if title or app:
                    desc = f"{app}: {title}" if app and title else (app or title)
                    if desc not in seen_titles:
                        seen_titles.add(desc)
                        open_apps.append(desc)
        except Exception:
            pass

        return {
            "active_window": active_window,
            "open_apps": open_apps[:12],
        }

    def inspect_screen(self, screen_index: Optional[int] = None) -> ActionResult:
        """Capture screenshot of the desktop, inspect active windows, and report what is open."""
        if screen_index is not None:
            self.set_screen_index(screen_index)
        img, b64 = self.capture_screenshot(max_dimension=1920)
        info = self.get_active_monitor_info()
        win_info = self.get_open_windows_info()

        active_win = win_info.get("active_window", "Desktop")
        apps_list = win_info.get("open_apps", [])
        apps_str = "\n  • " + "\n  • ".join(apps_list) if apps_list else "None detected"

        output_desc = (
            f"Active Desktop Display: Display {info['screen_index']} ({info['output']}, {info['width']}x{info['height']})\n"
            f"Active Focused Window: {active_win}\n"
            f"Open Desktop Applications & Tabs:{apps_str}\n"
            f"(High-resolution 1080p desktop image captured for visual analysis)."
        )
        return ActionResult(
            success=True,
            output=output_desc,
            screenshot_base64=b64
        )

    def click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> ActionResult:
        """Click at coordinate (x, y)."""
        try:
            # Bound check
            x = max(0, min(x, self.width - 1)) + self.left
            y = max(0, min(y, self.height - 1)) + self.top

            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.05)
            if clicks == 2:
                pyautogui.doubleClick(x, y, button=button)
            else:
                pyautogui.click(x, y, button=button)

            time.sleep(0.2)
            _, b64 = self.capture_screenshot()
            return ActionResult(
                success=True,
                output=f"Clicked at ({x}, {y}) with button='{button}' (clicks={clicks})",
                screenshot_base64=b64,
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def right_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, button="right", clicks=1)

    def double_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, button="left", clicks=2)

    def type_text(self, text: str, interval: float = 0.02) -> ActionResult:
        """Type text using simulated keyboard."""
        try:
            pyautogui.write(text, interval=interval)
            time.sleep(0.1)
            _, b64 = self.capture_screenshot()
            return ActionResult(
                success=True,
                output=f"Typed text: '{text[:20]}...' (length={len(text)})",
                screenshot_base64=b64,
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def press_key(self, key: str) -> ActionResult:
        """Press a special key (e.g., 'enter', 'esc', 'tab', 'backspace')."""
        try:
            pyautogui.press(key)
            time.sleep(0.1)
            _, b64 = self.capture_screenshot()
            return ActionResult(
                success=True,
                output=f"Pressed key: '{key}'",
                screenshot_base64=b64,
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def hotkey(self, keys: List[str]) -> ActionResult:
        """Execute hotkey combination (e.g. ['ctrl', 'c'], ['alt', 'tab'])."""
        try:
            pyautogui.hotkey(*keys)
            time.sleep(0.2)
            _, b64 = self.capture_screenshot()
            return ActionResult(
                success=True,
                output=f"Pressed hotkey: {'+'.join(keys)}",
                screenshot_base64=b64,
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def scroll(self, clicks: int) -> ActionResult:
        """Scroll mouse wheel (positive = up, negative = down)."""
        try:
            pyautogui.scroll(clicks)
            time.sleep(0.2)
            _, b64 = self.capture_screenshot()
            return ActionResult(
                success=True,
                output=f"Scrolled {clicks} clicks",
                screenshot_base64=b64,
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> ActionResult:
        """Drag mouse from start to end coordinates."""
        try:
            pyautogui.moveTo(start_x, start_y)
            time.sleep(0.1)
            pyautogui.dragTo(end_x, end_y, duration=duration, button="left")
            time.sleep(0.2)
            _, b64 = self.capture_screenshot()
            return ActionResult(
                success=True,
                output=f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})",
                screenshot_base64=b64,
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))
