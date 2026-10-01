"""Native X11 Desktop System Window for displaying diagrams, charts, and images."""

import os
from pathlib import Path
import threading
from typing import Optional
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class SystemWindowManager:
    """Manages spawning native desktop system windows for visual media display."""

    @staticmethod
    def show_media(
        media_type: str,
        content: str,
        title: str = "Bro Visual Display",
        caption: Optional[str] = None
    ) -> None:
        """Spawn a non-blocking system window on the X11 display."""
        thread = threading.Thread(
            target=SystemWindowManager._create_window,
            args=(media_type, content, title, caption),
            daemon=True
        )
        thread.start()

    @staticmethod
    def _create_window(media_type: str, content: str, title: str, caption: Optional[str]) -> None:
        try:
            # Ensure DISPLAY is set
            if not os.environ.get("DISPLAY"):
                os.environ["DISPLAY"] = ":1" if os.path.exists("/tmp/.X11-unix/X1") else ":0"

            root = tk.Tk()
            root.title(f"BRO // {title}")
            root.configure(bg="#060910")
            root.minsize(520, 380)

            # Center window on screen
            root.update_idletasks()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()

            # Bro Tactical HUD Header Frame
            header_frame = tk.Frame(root, bg="#060910", pady=10, padx=15)
            header_frame.pack(fill="x")

            title_label = tk.Label(
                header_frame,
                text=f"⚡ BRO VARIANT 2 // {title.upper()}",
                fg="#00e5ff",
                bg="#060910",
                font=("Helvetica", 11, "bold")
            )
            title_label.pack(side="left")

            type_badge = tk.Label(
                header_frame,
                text=f"[{media_type.upper()}]",
                fg="#ffab00",
                bg="#1a1500",
                font=("Courier", 9, "bold"),
                padx=6,
                pady=2
            )
            type_badge.pack(side="right")

            # Main Content Area
            content_frame = tk.Frame(root, bg="#0a0e17", padx=15, pady=15, relief="solid", bd=1)
            content_frame.pack(expand=True, fill="both", padx=15, pady=5)

            # 1. IMAGE DISPLAY
            if media_type in ["image", "chart"] and (content.endswith(".png") or content.endswith(".jpg") or content.endswith(".jpeg") or content.endswith(".webp") or os.path.exists(content)):
                img_path = Path(content).expanduser()
                if img_path.exists():
                    pil_img = Image.open(str(img_path))
                    orig_w, orig_h = pil_img.size

                    # Scale to fit window while preserving aspect ratio
                    max_w = min(1000, screen_width - 200)
                    max_h = min(700, screen_height - 250)
                    scale = min(max_w / orig_w, max_h / orig_h, 1.0)
                    new_w = max(1, int(orig_w * scale))
                    new_h = max(1, int(orig_h * scale))

                    resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(resized)

                    img_label = tk.Label(content_frame, image=photo, bg="#0a0e17")
                    img_label.image = photo  # Keep reference
                    img_label.pack(expand=True, fill="both")

                    dim_label = tk.Label(
                        content_frame,
                        text=f"Resolution: {orig_w}x{orig_h} • Path: {img_path.name}",
                        fg="#758296",
                        bg="#0a0e17",
                        font=("Courier", 8)
                    )
                    dim_label.pack(pady=4)
                else:
                    err_lbl = tk.Label(content_frame, text=f"File not found: {content}", fg="#ff1744", bg="#0a0e17")
                    err_lbl.pack(pady=20)

            # 2. DIAGRAM / MERMAID / CODE DISPLAY
            else:
                txt = tk.Text(
                    content_frame,
                    bg="#04060a",
                    fg="#a6e3a1",
                    insertbackground="#00e5ff",
                    font=("Courier", 10),
                    relief="flat",
                    padx=12,
                    pady=12,
                    wrap="none"
                )
                txt.insert("1.0", content)
                txt.config(state="disabled")

                # Scrollbars
                ysb = tk.Scrollbar(content_frame, orient="vertical", command=txt.yview)
                xsb = tk.Scrollbar(content_frame, orient="horizontal", command=txt.xview)
                txt.config(xscrollcommand=xsb.set, yscrollcommand=ysb.set)
                ysb.pack(side="right", fill="y")
                xsb.pack(side="bottom", fill="x")
                txt.pack(expand=True, fill="both")

            # Caption Footer
            if caption:
                cap_frame = tk.Frame(root, bg="#060910", padx=15, pady=4)
                cap_frame.pack(fill="x")
                cap_label = tk.Label(
                    cap_frame,
                    text=f"Note: {caption}",
                    fg="#cbd5e1",
                    bg="#060910",
                    font=("Helvetica", 9),
                    wraplength=700,
                    justify="left"
                )
                cap_label.pack(side="left")

            # Action Buttons Bar
            btn_frame = tk.Frame(root, bg="#060910", pady=10, padx=15)
            btn_frame.pack(fill="x")

            def copy_content():
                root.clipboard_clear()
                root.clipboard_append(content)
                copy_btn.config(text="✔ Copied!")
                root.after(2000, lambda: copy_btn.config(text="📋 Copy Content"))

            copy_btn = tk.Button(
                btn_frame,
                text="📋 Copy Content",
                command=copy_content,
                bg="#1a2332",
                fg="#00e5ff",
                activebackground="#00e5ff",
                activeforeground="#060910",
                font=("Helvetica", 9, "bold"),
                relief="flat",
                padx=10,
                pady=4
            )
            copy_btn.pack(side="left", padx=5)

            import webbrowser
            def open_web_hud():
                webbrowser.open("http://127.0.0.1:8765")

            hud_btn = tk.Button(
                btn_frame,
                text="🌐 Open in Web HUD",
                command=open_web_hud,
                bg="#1a2332",
                fg="#ffffff",
                activebackground="#00e5ff",
                activeforeground="#060910",
                font=("Helvetica", 9),
                relief="flat",
                padx=10,
                pady=4
            )
            hud_btn.pack(side="left", padx=5)

            close_btn = tk.Button(
                btn_frame,
                text="Close (Esc)",
                command=root.destroy,
                bg="#ff1744",
                fg="#ffffff",
                activebackground="#ff5252",
                activeforeground="#ffffff",
                font=("Helvetica", 9, "bold"),
                relief="flat",
                padx=12,
                pady=4
            )
            close_btn.pack(side="right", padx=5)

            # Close on Escape key
            root.bind("<Escape>", lambda e: root.destroy())

            # Focus and bring to front
            root.lift()
            root.attributes("-topmost", True)
            root.after_idle(root.attributes, "-topmost", False)

            root.mainloop()
        except Exception as e:
            print(f"[SystemWindow Error] Failed to display system window: {e}")
