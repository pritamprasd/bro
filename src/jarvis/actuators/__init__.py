"""Actuators for desktop, browser, python scripts, and shell."""

from jarvis.actuators.base import ActionResult, BaseActuator
from jarvis.actuators.browser import BrowserActuator
from jarvis.actuators.desktop import DesktopActuator
from jarvis.actuators.python_runner import PythonRunner
from jarvis.actuators.shell import ShellActuator

__all__ = [
    "ActionResult",
    "BaseActuator",
    "DesktopActuator",
    "BrowserActuator",
    "PythonRunner",
    "ShellActuator",
]
