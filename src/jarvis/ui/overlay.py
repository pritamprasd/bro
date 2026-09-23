"""Floating Approval Overlay Dialog for High-Stakes Actions."""

import sys
import threading
from typing import Optional
from jarvis.core.safety import RiskAssessment

class ApprovalOverlay:
    """Displays a modern, minimalist, always-on-top confirmation dialog on X11."""

    def __init__(self):
        pass

    def request_approval(self, assessment: RiskAssessment) -> bool:
        """Prompt user for approval. Returns True if approved, False if rejected."""
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
        root.title("Jarvis Mark 3 // Safety Gatekeeper")
        root.attributes("-topmost", True)
        root.geometry("640x420")
        root.configure(bg="#070c18")
        root.resizable(False, False)

        # Center on screen
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"+{x}+{y}")

        # Modern font resolution
        def get_best_font(family_candidates, size, weight="normal"):
            available = set(font.families())
            for fam in family_candidates:
                if fam in available:
                    return font.Font(family=fam, size=size, weight=weight)
            return font.Font(size=size, weight=weight)

        title_font = get_best_font(["Inter", "DejaVu Sans", "Roboto", "Helvetica Neue", "Arial"], 13, "bold")
        badge_font = get_best_font(["JetBrains Mono", "DejaVu Sans Mono", "Monospace"], 9, "bold")
        body_font = get_best_font(["Inter", "DejaVu Sans", "Roboto", "Helvetica Neue", "Arial"], 10)
        code_font = get_best_font(["JetBrains Mono", "DejaVu Sans Mono", "Courier New", "Monospace"], 10)
        btn_font = get_best_font(["Inter", "DejaVu Sans", "Roboto", "Helvetica Neue", "Arial"], 10, "bold")

        is_critical = (assessment.risk_level.lower() == "critical")
        accent_color = "#f43f5e" if is_critical else "#f59e0b"
        badge_bg = "#3b0712" if is_critical else "#3d2105"

        # 1. Header Frame
        header = tk.Frame(root, bg="#0b1326", padx=24, pady=16, highlightthickness=1, highlightbackground="#182642")
        header.pack(fill="x")

        header_top = tk.Frame(header, bg="#0b1326")
        header_top.pack(fill="x")

        lbl_shield = tk.Label(
            header_top,
            text="🛡️ SECURITY GATEKEEPER",
            bg="#0b1326",
            fg="#00e5ff",
            font=title_font,
        )
        lbl_shield.pack(side="left")

        lbl_badge = tk.Label(
            header_top,
            text=f"  {assessment.risk_level.upper()} RISK  ",
            bg=badge_bg,
            fg=accent_color,
            font=badge_font,
            padx=8,
            pady=3,
        )
        lbl_badge.pack(side="right")

        lbl_sub = tk.Label(
            header,
            text="Action intercepted: Unattended execution paused for explicit human authorization.",
            bg="#0b1326",
            fg="#64748b",
            font=body_font,
        )
        lbl_sub.pack(anchor="w", pady=(4, 0))

        # 2. Main Content Frame
        content_frame = tk.Frame(root, bg="#070c18", padx=24, pady=18)
        content_frame.pack(fill="both", expand=True)

        # Reason Banner Box
        reason_box = tk.Frame(content_frame, bg="#0e172a", padx=14, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        reason_box.pack(fill="x", pady=(0, 14))

        lbl_reason_title = tk.Label(
            reason_box,
            text="ASSESSMENT REASON",
            bg="#0e172a",
            fg="#94a3b8",
            font=badge_font,
        )
        lbl_reason_title.pack(anchor="w")

        lbl_reason = tk.Label(
            reason_box,
            text=assessment.reason,
            bg="#0e172a",
            fg="#f8fafc",
            font=body_font,
            wraplength=560,
            justify="left",
        )
        lbl_reason.pack(anchor="w", pady=(3, 0))

        # Action Details Header
        lbl_action = tk.Label(
            content_frame,
            text=f"PROPOSED ACTION // [{assessment.action_type.upper()}]",
            bg="#070c18",
            fg="#38bdf8",
            font=badge_font,
        )
        lbl_action.pack(anchor="w", pady=(0, 4))

        # Monospace Text Box showing action details
        txt_frame = tk.Frame(content_frame, bg="#030712", highlightthickness=1, highlightbackground="#1b2a47")
        txt_frame.pack(fill="both", expand=True)

        txt_box = tk.Text(
            txt_frame,
            height=4,
            bg="#030712",
            fg="#00f0ff",
            relief="flat",
            font=code_font,
            padx=12,
            pady=10,
            wrap="word",
            insertbackground="#00f0ff",
        )
        txt_box.insert("1.0", assessment.action_details.strip())
        txt_box.config(state="disabled")
        txt_box.pack(fill="both", expand=True)

        # Button Actions
        def on_approve(event=None):
            result["approved"] = True
            root.destroy()

        def on_reject(event=None):
            result["approved"] = False
            root.destroy()

        # Keyboard shortcuts
        root.bind("<Return>", on_approve)
        root.bind("<Escape>", on_reject)

        # 3. Bottom Action Bar
        footer = tk.Frame(root, bg="#0b1326", padx=24, pady=14, highlightthickness=1, highlightbackground="#182642")
        footer.pack(fill="x", side="bottom")

        lbl_hint = tk.Label(
            footer,
            text="Press [Enter] to Approve  •  [Esc] to Reject",
            bg="#0b1326",
            fg="#64748b",
            font=body_font,
        )
        lbl_hint.pack(side="left")

        btn_reject = tk.Button(
            footer,
            text="✕  Reject Action (Esc)",
            bg="#1e1b2e",
            fg="#f43f5e",
            activebackground="#2e1a24",
            activeforeground="#f43f5e",
            font=btn_font,
            relief="flat",
            highlightthickness=1,
            highlightbackground="#f43f5e",
            padx=16,
            pady=7,
            command=on_reject,
            cursor="hand2",
        )
        btn_reject.pack(side="right", padx=(10, 0))

        btn_approve = tk.Button(
            footer,
            text="✔  Approve Execution (Enter)",
            bg="#00e5ff",
            fg="#030712",
            activebackground="#00b4d8",
            activeforeground="#030712",
            font=btn_font,
            relief="flat",
            padx=18,
            pady=7,
            command=on_approve,
            cursor="hand2",
        )
        btn_approve.pack(side="right")

        root.lift()
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
