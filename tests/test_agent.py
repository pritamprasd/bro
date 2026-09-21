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

def test_agent_show_media_action():
    config = JarvisConfig(output_mode="cli")
    media_captured = []
    def on_media(payload):
        media_captured.append(payload)

    agent = JarvisAgent(config, show_media_cb=on_media)

    # 1st step: show media
    step1_resp = ModelResponse(
        content='{"thought": "Displaying flow", "action": "show_media", "params": {"media_type": "diagram", "content": "graph TD; X-->Y", "title": "Flowchart"}}',
    )
    # 2nd step: finish
    step2_resp = ModelResponse(
        content='{"thought": "All done", "action": "finish", "params": {"result": "Displayed diagram"}}',
    )

    agent.router.generate_text = MagicMock(side_effect=[step1_resp, step2_resp])
    result = agent.run_task("Draw me a flow")

    assert "Displayed diagram" in result
    assert len(media_captured) == 1
    assert media_captured[0]["media_type"] == "diagram"
    assert "graph TD; X-->Y" in media_captured[0]["content"]

def test_agent_auto_detect_mermaid_in_finish():
    config = JarvisConfig(output_mode="cli")
    media_captured = []
    def on_media(payload):
        media_captured.append(payload)

    agent = JarvisAgent(config, show_media_cb=on_media)

    # Model finishes with a mermaid code block in the result string
    finish_resp = ModelResponse(
        content='{"thought": "Returning diagram", "action": "finish", "params": {"result": "Here is the flow:\\n```mermaid\\ngraph TD\\nStart --> Stop\\n```"}}',
    )

    agent.router.generate_text = MagicMock(return_value=finish_resp)
    result = agent.run_task("Show me how it flows")

    assert "Here is the flow" in result
    assert len(media_captured) == 1
    assert media_captured[0]["media_type"] == "diagram"
    assert "Start --> Stop" in media_captured[0]["content"]

def test_agent_desktop_switch_monitor():
    config = JarvisConfig(output_mode="cli", desktop={"screen_index": 1})
    agent = JarvisAgent(config)
    assert agent.desktop.screen_index == 1

    # Step 1: switch monitor
    step1_resp = ModelResponse(
        content='{"thought": "Switching to monitor 2", "action": "desktop_switch_monitor", "params": {"screen_index": 2}}',
    )
    # Step 2: finish
    step2_resp = ModelResponse(
        content='{"thought": "Done switching", "action": "finish", "params": {"result": "Switched to display 2"}}',
    )

    agent.router.generate_text = MagicMock(side_effect=[step1_resp, step2_resp])
    res = agent.run_task("Look at screen 2")
    assert "Switched to display 2" in res
    assert agent.desktop.screen_index == 2


