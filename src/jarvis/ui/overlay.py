"""Floating Approval Overlay Dialog for High-Stakes Actions."""

import sys
import threading
from typing import Optional
from jarvis.core.safety import RiskAssessment

class ApprovalOverlay:
    """Displays a modern, floating, always-on-top confirmation dialog on X11."""

    def __init__(self):
        pass

    def request_approval(self, assessment: RiskAssessment) -> bool:
        """Prompt user for approval. Returns True if approved, False if rejected."""
        # Try launching Tkinter GUI overlay
        try:
            return self._show_tk_dialog(assessment)
        except Exception as e:
            # Graceful fallback to CLI prompt if display/tkinter is unavailable
            return self._show_cli_prompt(assessment)

    def _show_tk_dialog(self, assessment: RiskAssessment) -> bool:
        import tkinter as tk
        from tkinter import font

        result = {"approved": False}

        root = tk.Tk()
        root.title("Jarvis Security Guard")
        root.attributes("-topmost", True)
        root.geometry("520x300")
        root.configure(bg="#1e1e2e")
        root.resizable(False, False)

        # Center on screen
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"+{x}+{y}")

        title_font = font.Font(family="Inter", size=14, weight="bold")
        body_font = font.Font(family="Inter", size=10)
        btn_font = font.Font(family="Inter", size=10, weight="bold")

        # Header Frame
        header = tk.Frame(root, bg="#181825", padx=16, pady=12)
        header.pack(fill="x")

        icon_color = "#f38ba8" if assessment.risk_level == "critical" else "#fab387"
        lbl_header = tk.Label(
            header,
            text=f"⚠️ High-Stakes Action Approval [{assessment.risk_level.upper()}]",
            bg="#181825",
            fg=icon_color,
            font=title_font,
        )
        lbl_header.pack(anchor="w")

        # Content Frame
        content_frame = tk.Frame(root, bg="#1e1e2e", padx=20, pady=14)
        content_frame.pack(fill="both", expand=True)

        lbl_reason = tk.Label(
            content_frame,
            text=f"Reason: {assessment.reason}",
            bg="#1e1e2e",
            fg="#cdd6f4",
            font=body_font,
            wraplength=480,
            justify="left",
        )
        lbl_reason.pack(anchor="w", pady=(0, 8))

        lbl_action = tk.Label(
            content_frame,
            text=f"Action ({assessment.action_type}):",
            bg="#1e1e2e",
            fg="#a6adc8",
            font=body_font,
        )
        lbl_action.pack(anchor="w")

        # Text box showing action details
        txt_box = tk.Text(
            content_frame,
            height=3,
            bg="#11111b",
            fg="#a6e3a1",
            relief="flat",
            font=("Monospace", 9),
            padx=8,
            pady=8,
        )
        txt_box.insert("1.0", assessment.action_details[:300])
        txt_box.config(state="disabled")
        txt_box.pack(fill="x", pady=(4, 10))

        # Button Actions
        def on_approve(event=None):
            result["approved"] = True
            root.destroy()

        def on_reject(event=None):
            result["approved"] = False
            root.destroy()

        # Keyboard bindings
        root.bind("<Return>", on_approve)
        root.bind("<Escape>", on_reject)

        # Button Frame
        btn_frame = tk.Frame(root, bg="#181825", padx=16, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        btn_reject = tk.Button(
            btn_frame,
            text="Reject (Esc)",
            bg="#313244",
            fg="#f38ba8",
            activebackground="#45475a",
            activeforeground="#f38ba8",
            font=btn_font,
            relief="flat",
            padx=16,
            pady=6,
            command=on_reject,
            cursor="hand2",
        )
        btn_reject.pack(side="right", padx=(8, 0))

        btn_approve = tk.Button(
            btn_frame,
            text="Approve (Enter)",
            bg="#a6e3a1",
            fg="#11111b",
            activebackground="#94e2d5",
            activeforeground="#11111b",
            font=btn_font,
            relief="flat",
            padx=16,
            pady=6,
            command=on_approve,
            cursor="hand2",
        )
        btn_approve.pack(side="right")

        root.focus_force()
        root.mainloop()

        return result["approved"]

    def _show_cli_prompt(self, assessment: RiskAssessment) -> bool:
        """Terminal fallback if GUI display fails."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm

        console = Console()
        console.print(
            Panel(
                f"[bold red]Risk Level: {assessment.risk_level.upper()}[/bold red]\n"
                f"[yellow]{assessment.reason}[/yellow]\n\n"
                f"[cyan]Action ({assessment.action_type}):[/cyan] {assessment.action_details}",
                title="[bold yellow]⚠️ Jarvis Safety Gatekeeper[/bold yellow]",
                border_style="red",
            )
        )
        return Confirm.ask("[bold]Do you authorize this action?[/bold]", default=False)
