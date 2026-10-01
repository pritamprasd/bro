"""Standalone Spotlight Window process for clean, crash-free X11 rendering."""

import json
import subprocess
import sys
import tkinter as tk
from tkinter import font
import pyperclip

def get_active_window_title() -> str:
    try:
        res = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    try:
        res = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0:
            win_id = res.stdout.split()[-1]
            title_res = subprocess.run(["xprop", "-id", win_id, "WM_NAME"], capture_output=True, text=True, timeout=1)
            if title_res.returncode == 0:
                return title_res.stdout.split("=", 1)[-1].strip().strip('"')
    except Exception:
        pass
    return "Desktop Workspace"

def main():
    active_window = get_active_window_title()
    try:
        clip_content = pyperclip.paste().strip()
    except Exception:
        clip_content = ""
    clip_preview = (clip_content[:40] + "...") if len(clip_content) > 40 else clip_content

    root = tk.Tk()
    root.title("Bro Spotlight (Variant 3)")
    root.attributes("-topmost", True)
    root.geometry("640x160")
    root.configure(bg="#080c14")
    root.resizable(False, False)

    # Center on upper third of screen
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 3)
    root.geometry(f"+{x}+{y}")

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
        if text:
            payload = {
                "text": text,
                "active_window": active_window,
                "clipboard": clip_content[:500] if clip_content else "",
            }
            print(json.dumps(payload), flush=True)
        root.destroy()
        sys.exit(0)

    def on_cancel(event=None):
        root.destroy()
        sys.exit(0)

    root.bind("<Return>", on_submit)
    root.bind("<Escape>", on_cancel)
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.mainloop()

if __name__ == "__main__":
    main()
