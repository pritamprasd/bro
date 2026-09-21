"""Desktop Computer-Use Actuator for Linux X11 using mss, pyautogui, and pynput."""

import base64
import io
import time
from typing import List, Optional, Tuple
import mss
from PIL import Image
import pyautogui
from jarvis.actuators.base import ActionResult, BaseActuator

# Configure PyAutoGUI
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True

class DesktopActuator(BaseActuator):
    def __init__(self, screen_index: int = 1):
        self.screen_index = screen_index
        self._sct = mss.MSS()
        # Monitor bounds
        self.monitors = self._sct.monitors
        target_mon = self.monitors[screen_index] if screen_index < len(self.monitors) else self.monitors[0]
        self.width = target_mon["width"]
        self.height = target_mon["height"]
        self.left = target_mon["left"]
        self.top = target_mon["top"]

    def reset(self) -> None:
        pass

    def get_screen_dimensions(self) -> Tuple[int, int]:
        return self.width, self.height

    def capture_screenshot(self, max_dimension: Optional[int] = 1280) -> Tuple[Image.Image, str]:
        """Capture screenshot of the screen and return (PIL.Image, base64_png)."""
        target_mon = self.monitors[self.screen_index] if self.screen_index < len(self.monitors) else self.monitors[0]
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
