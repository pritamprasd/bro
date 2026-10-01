"""Everyday Browser Automation via Chrome DevTools Protocol (CDP)."""

import os
import shutil
import subprocess
import time
from typing import Optional
import requests
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
from bro.actuators.base import ActionResult, BaseActuator

class CDPBrowserActuator(BaseActuator):
    def __init__(self, port: int = 9222):
        self.port = port
        self.endpoint = f"http://127.0.0.1:{port}"
        self._pw = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def is_cdp_available(self) -> bool:
        """Check if browser with CDP debugging port is active."""
        try:
            r = requests.get(f"{self.endpoint}/json/version", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    def launch_everyday_browser(self) -> bool:
        """Launch user's local Google Chrome or Brave with remote debugging enabled."""
        if self.is_cdp_available():
            return True

        # Find chrome / brave executable
        candidates = ["google-chrome", "google-chrome-stable", "brave-browser", "chromium", "chromium-browser"]
        binary = None
        for c in candidates:
            path = shutil.which(c)
            if path:
                binary = path
                break

        if not binary:
            return False

        # Launch in background
        cmd = [
            binary,
            f"--remote-debugging-port={self.port}",
            "--no-first-run",
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

        # Wait up to 5 seconds for port to open
        for _ in range(25):
            time.sleep(0.2)
            if self.is_cdp_available():
                return True

        return False

    def connect(self) -> Page:
        """Connect Playwright over CDP to everyday browser."""
        if not self.is_cdp_available():
            if not self.launch_everyday_browser():
                raise RuntimeError(
                    f"Could not connect to browser on CDP port {self.port} and failed to launch everyday browser."
                )

        if not self._pw:
            self._pw = sync_playwright().start()

        self._browser = self._pw.chromium.connect_over_cdp(self.endpoint)
        if len(self._browser.contexts) > 0:
            self._context = self._browser.contexts[0]
        else:
            self._context = self._browser.new_context()

        if len(self._context.pages) > 0:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()

        return self._page

    def navigate(self, url: str) -> ActionResult:
        try:
            page = self.connect()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return ActionResult(
                success=True,
                output=f"[CDP Everyday Browser] Navigated to {url} (Title: {page.title()})",
            )
        except Exception as e:
            return ActionResult(success=False, error=f"CDP Navigation failed: {e}")

    def click(self, selector: str) -> ActionResult:
        try:
            page = self.connect()
            page.click(selector, timeout=5000)
            return ActionResult(success=True, output=f"[CDP] Clicked '{selector}'")
        except Exception as e:
            return ActionResult(success=False, error=f"CDP Click failed: {e}")

    def get_text_content(self) -> ActionResult:
        try:
            page = self.connect()
            text = page.inner_text("body")
            return ActionResult(
                success=True,
                output=f"[CDP] Page: {page.title()}\n{text[:2000]}",
            )
        except Exception as e:
            return ActionResult(success=False, error=f"CDP read failed: {e}")

    def reset(self) -> None:
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
            self._page = None
        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None
