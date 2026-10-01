"""Isolated Browser Actuator using Playwright."""

import base64
from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright
from bro.actuators.base import ActionResult, BaseActuator
from bro.config import BrowserConfig

class BrowserActuator(BaseActuator):
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.user_data_dir = Path(config.user_data_dir).expanduser()
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self._pw: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def _ensure_browser(self) -> Page:
        if self._page and not self._page.is_closed():
            return self._page

        if not self._pw:
            self._pw = sync_playwright().start()

        # Launch persistent context to keep isolated user cookies / session data
        self._context = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.config.headless,
            viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
            args=["--no-first-run", "--no-default-browser-check"],
        )
        if len(self._context.pages) > 0:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()

        return self._page

    def navigate(self, url: str) -> ActionResult:
        """Navigate to a given URL."""
        try:
            page = self._ensure_browser()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            _, b64 = self.capture_screenshot()
            title = page.title()
            return ActionResult(
                success=True,
                output=f"Navigated to {url} (Title: {title})",
                screenshot_base64=b64,
            )
        except Exception as e:
            return ActionResult(success=False, error=f"Navigation failed: {e}")

    def capture_screenshot(self) -> Tuple[bytes, str]:
        """Capture screenshot of the active browser page."""
        page = self._ensure_browser()
        img_bytes = page.screenshot(type="png", full_page=False)
        b64_str = base64.b64encode(img_bytes).decode("utf-8")
        return img_bytes, b64_str

    def click(self, selector: Optional[str] = None, x: Optional[int] = None, y: Optional[int] = None) -> ActionResult:
        """Click by CSS/XPath selector or by visual coordinates."""
        try:
            page = self._ensure_browser()
            if selector:
                page.click(selector, timeout=5000)
                msg = f"Clicked element matching '{selector}'"
            elif x is not None and y is not None:
                page.mouse.click(x, y)
                msg = f"Clicked at coordinates ({x}, {y})"
            else:
                return ActionResult(success=False, error="Neither selector nor coordinates provided")

            page.wait_for_timeout(500)
            _, b64 = self.capture_screenshot()
            return ActionResult(success=True, output=msg, screenshot_base64=b64)
        except Exception as e:
            return ActionResult(success=False, error=f"Click failed: {e}")

    def type_text(self, text: str, selector: Optional[str] = None) -> ActionResult:
        """Type text into an active input or selector."""
        try:
            page = self._ensure_browser()
            if selector:
                page.fill(selector, text, timeout=5000)
            else:
                page.keyboard.type(text)

            _, b64 = self.capture_screenshot()
            return ActionResult(
                success=True,
                output=f"Typed text: '{text[:20]}...'",
                screenshot_base64=b64,
            )
        except Exception as e:
            return ActionResult(success=False, error=f"Type text failed: {e}")

    def press_key(self, key: str) -> ActionResult:
        try:
            page = self._ensure_browser()
            page.keyboard.press(key)
            _, b64 = self.capture_screenshot()
            return ActionResult(success=True, output=f"Pressed key: '{key}'", screenshot_base64=b64)
        except Exception as e:
            return ActionResult(success=False, error=f"Press key failed: {e}")

    def get_text_content(self) -> ActionResult:
        """Get visible page text content."""
        try:
            page = self._ensure_browser()
            text = page.inner_text("body")
            title = page.title()
            return ActionResult(
                success=True,
                output=f"Title: {title}\nContent:\n{text[:4000]}",
                data={"title": title, "url": page.url},
            )
        except Exception as e:
            return ActionResult(success=False, error=f"Failed to get text content: {e}")

    def reset(self) -> None:
        self.close()

    def close(self) -> None:
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
            self._page = None
        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None
