"""Unit tests for PythonRunner actuator."""

import pytest
from jarvis.actuators.python_runner import PythonRunner

def test_python_runner_execution():
    runner = PythonRunner()
    code = """
import math
print("RESULT:", math.factorial(5))
"""
    result = runner.run_code(code)
    assert result.success is True
    assert "RESULT: 120" in result.output

def test_python_runner_env_injection():
    runner = PythonRunner()
    code = """
import os
print("SECRET_VAL:", os.getenv("TEST_VAR", ""))
"""
    result = runner.run_code(code, env_vars={"TEST_VAR": "super_secret"})
    assert result.success is True
    assert "SECRET_VAL: super_secret" in result.output

def test_python_runner_error_capture():
    runner = PythonRunner()
    code = """
raise ValueError("Intentional test exception")
"""
    result = runner.run_code(code)
    assert result.success is False
    assert "Intentional test exception" in (result.error or "")
