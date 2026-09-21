"""Integration tests for the Jarvis Agent ReAct loop."""

from unittest.mock import MagicMock, patch
import pytest
from jarvis.config import JarvisConfig
from jarvis.core.agent import JarvisAgent
from jarvis.models.base import ModelResponse

def test_agent_react_loop_finish():
    config = JarvisConfig(output_mode="cli")
    agent = JarvisAgent(config)

    # Mock the router to return a finish action
    agent.router.generate_text = MagicMock(return_value=ModelResponse(
        content='{"thought": "Computation done", "action": "finish", "params": {"result": "Result is 42"}}',
    ))

    result = agent.run_task("What is 6 * 7?")
    assert "Result is 42" in result

def test_agent_react_loop_with_python_action():
    config = JarvisConfig(output_mode="cli")
    agent = JarvisAgent(config)

    # 1st step: run python
    step1_resp = ModelResponse(
        content='{"thought": "Let\'s compute in python", "action": "run_python", "params": {"code": "print(2 + 2)"}}',
    )
    # 2nd step: finish
    step2_resp = ModelResponse(
        content='{"thought": "Got 4", "action": "finish", "params": {"result": "The sum is 4"}}',
    )

    agent.router.generate_text = MagicMock(side_effect=[step1_resp, step2_resp])

    result = agent.run_task("Calculate 2 + 2")
    assert "The sum is 4" in result
