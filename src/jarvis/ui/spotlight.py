"""Desktop Spotlight Bar with Context-Aware Active Window & Clipboard Injection."""

import subprocess
import threading
from typing import Callable, Optional
from pynput import keyboard
import pyperclip
from jarvis.config import SpotlightConfig

def get_active_window_title() -> str:
    """Get title of active X11 window using xdotool or xprop."""
    try:
        res = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    try:
        # Fallback to xprop
        res = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0:
            win_id = res.stdout.split()[-1]
            title_res = subprocess.run(["xprop", "-id", win_id, "WM_NAME"], capture_output=True, text=True, timeout=1)
            if title_res.returncode == 0:
                return title_res.stdout.split("=", 1)[-1].strip().strip('"')
    except Exception:
        pass
    return "Desktop Workspace"

class SpotlightBar:
    def __init__(self, config: SpotlightConfig, task_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.task_callback = task_callback
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self._is_open = False

    def start_listener(self) -> None:
        """Start listening for global hotkey (e.g. <alt>+j)."""
        hotkey_map = {
            self.config.hotkey: self.show_spotlight,
        }
        self.listener = keyboard.GlobalHotKeys(hotkey_map)
        self.listener.daemon = True
        self.listener.start()

    def stop_listener(self) -> None:
        if self.listener:
            self.listener.stop()

    def show_spotlight(self) -> None:
        """Summon the floating spotlight search bar."""
        if self._is_open:
            return
        threading.Thread(target=self._run_tk_spotlight, daemon=True).start()

    def _run_tk_spotlight(self) -> None:
        import tkinter as tk
        from tkinter import font

        self._is_open = True
        active_window = get_active_window_title()
        clip_content = pyperclip.paste().strip()
        clip_preview = (clip_content[:40] + "...") if len(clip_content) > 40 else clip_content

        root = tk.Tk()
        root.title("Jarvis Spotlight")
        root.attributes("-topmost", True)
        root.geometry("640x160")
        root.configure(bg="#080c14")
        root.resizable(False, False)

        # Center on screen
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 3)
        root.geometry(f"+{x}+{y}")

        title_font = font.Font(family="Inter", size=11, weight="bold")
        sub_font = font.Font(family="Inter", size=9)
        input_font = font.Font(family="Inter", size=13)

        # Context Header Frame
        header = tk.Frame(root, bg="#0d1527", padx=16, pady=8)
        header.pack(fill="x")

        lbl_win = tk.Label(
            header,
            text=f"🪟 Active: {active_window[:45]}",
            bg="#0d1527",
            fg="#00e5ff",
            font=sub_font,
        )
        lbl_win.pack(side="left")

        if clip_preview:
            lbl_clip = tk.Label(
                header,
                text=f"📋 Clip: {clip_preview}",
                bg="#0d1527",
                fg="#a0aec0",
                font=sub_font,
            )
            lbl_clip.pack(side="right")

        # Input Frame
        frame_input = tk.Frame(root, bg="#080c14", padx=16, pady=16)
        frame_input.pack(fill="both", expand=True)

        entry = tk.Entry(
            frame_input,
            bg="#11192e",
            fg="#ffffff",
            insertbackground="#00e5ff",
            font=input_font,
            relief="flat",
            highlightthickness=1,
            highlightbackground="#1e293b",
            highlightcolor="#00e5ff",
        )
        entry.pack(fill="x", ipady=8, padx=4)
        entry.focus_set()

        # Footer hints
        lbl_footer = tk.Label(
            frame_input,
            text="Press Enter to execute • Esc to dismiss • Context auto-injected",
            bg="#080c14",
            fg="#64748b",
            font=sub_font,
        )
        lbl_footer.pack(anchor="w", pady=(8, 0), padx=4)

        def on_submit(event=None):
            text = entry.get().strip()
            if text and self.task_callback:
                full_goal = f"[Context: Active Window '{active_window}'] {text}"
                if clip_content:
                    full_goal += f"\n[Clipboard]:\n{clip_content[:500]}"
                self.task_callback(full_goal)
            self._is_open = False
            root.destroy()

        def on_cancel(event=None):
            self._is_open = False
            root.destroy()

        root.bind("<Return>", on_submit)
        root.bind("<Escape>", on_cancel)

        root.mainloop()
        self._is_open = False
