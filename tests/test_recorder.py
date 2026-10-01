"""Unit tests for 'Watch & Learn' Macro Recorder."""

import tempfile
from pathlib import Path
from bro.actuators.recorder import MacroRecorder

def test_macro_compilation():
    with tempfile.TemporaryDirectory() as tmpdir:
        recorder = MacroRecorder(workflows_dir=Path(tmpdir))

        steps = [
            {"action": "desktop_click", "params": {"x": 100, "y": 200}},
            {"action": "desktop_type", "params": {"text": "hello"}},
            {"action": "desktop_press_key", "params": {"key": "enter"}},
        ]

        macro_file = recorder.compile_macro("test_login", steps)
        assert macro_file.exists()
        content = macro_file.read_text()
        assert "pyautogui.click(100, 200)" in content
        assert "pyautogui.write('hello')" in content
        assert "pyautogui.press('enter')" in content
