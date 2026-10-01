import os
import re
from pathlib import Path

def extract_modules():
    web_dir = Path("/home/pritam/code/ai/jarvis/src/bro/ui/web")
    index_file = web_dir / "index.html"
    raw_content = index_file.read_text(encoding="utf-8")
    lines = raw_content.splitlines()

    css_dir = web_dir / "css"
    js_dir = web_dir / "js"
    tabs_dir = web_dir / "tabs"
    css_dir.mkdir(parents=True, exist_ok=True)
    js_dir.mkdir(parents=True, exist_ok=True)
    tabs_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # 1. EXTRACT HTML TABS
    # -------------------------------------------------------------
    def get_lines(start_idx, end_idx):
        return "\n".join(lines[start_idx:end_idx]).strip()

    # Find line indices
    def find_line(pattern):
        for i, l in enumerate(lines):
            if re.search(pattern, l):
                return i
        return -1

    tab_command_start = find_line(r'<div id="tab-command"')
    tab_cal_start = find_line(r'<div id="tab-calendar"')
    tab_disp_start = find_line(r'<div id="tab-displays"')
    tab_set_start = find_line(r'<div id="tab-settings"')
    tab_hist_start = find_line(r'<div id="tab-history"')
    tab_err_start = find_line(r'<div id="tab-errors"')
    tab_mem_start = find_line(r'<div id="tab-memory"')
    tab_guide_start = find_line(r'<div id="tab-guide"')
    tab_res_start = find_line(r'<div id="tab-resources"')
    modals_start = find_line(r'<!-- High-Tech Media Display Dialog Modal')
    if modals_start == -1:
        modals_start = find_line(r'<div id="media-modal"')
        if modals_start == -1:
            modals_start = find_line(r'class="media-modal-overlay')

    script_start = find_line(r'<script>\s*$')
    if script_start == -1 or script_start < tab_res_start:
        for i in range(len(lines)-1, -1, -1):
            if '<script>' in lines[i]:
                script_start = i
                break

    print("Tab Command:", tab_command_start)
    print("Tab Calendar:", tab_cal_start)
    print("Tab Displays:", tab_disp_start)
    print("Tab Settings:", tab_set_start)
    print("Tab History:", tab_hist_start)
    print("Tab Errors:", tab_err_start)
    print("Tab Memory:", tab_mem_start)
    print("Tab Guide:", tab_guide_start)
    print("Tab Resources:", tab_res_start)
    print("Modals Start:", modals_start)
    print("Script Start:", script_start)

    # Save tab HTML partials
    (tabs_dir / "calendar.html").write_text(get_lines(tab_cal_start, tab_disp_start), encoding="utf-8")
    (tabs_dir / "displays.html").write_text(get_lines(tab_disp_start, tab_set_start), encoding="utf-8")
    (tabs_dir / "settings.html").write_text(get_lines(tab_set_start, tab_hist_start), encoding="utf-8")
    (tabs_dir / "history.html").write_text(get_lines(tab_hist_start, tab_err_start), encoding="utf-8")
    (tabs_dir / "alerts.html").write_text(get_lines(tab_err_start, tab_mem_start), encoding="utf-8")
    (tabs_dir / "memory.html").write_text(get_lines(tab_mem_start, tab_guide_start), encoding="utf-8")
    (tabs_dir / "guide.html").write_text(get_lines(tab_guide_start, tab_res_start), encoding="utf-8")
    (tabs_dir / "resources.html").write_text(get_lines(tab_res_start, modals_start), encoding="utf-8")
    (tabs_dir / "modals.html").write_text(get_lines(modals_start, script_start), encoding="utf-8")
    print("All Tab and Modal HTML partials extracted successfully!")

if __name__ == "__main__":
    extract_modules()
