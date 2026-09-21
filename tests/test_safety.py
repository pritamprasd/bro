"""Unit tests for Jarvis Safety Gatekeeper."""

import pytest
from jarvis.config import SafetyConfig
from jarvis.core.safety import SafetyClassifier

def test_safe_action():
    config = SafetyConfig()
    classifier = SafetyClassifier(config)

    assessment = classifier.assess_action("desktop_click", '{"x": 100, "y": 200}', "Open Calculator")
    assert not assessment.is_high_stakes
    assert assessment.risk_level == "safe"

def test_high_stakes_keywords():
    config = SafetyConfig()
    classifier = SafetyClassifier(config)

    # Keyword: delete
    assessment = classifier.assess_action("shell", "delete all cache files")
    assert assessment.is_high_stakes

    # Keyword: payment
    assessment = classifier.assess_action("browser_click", '{"selector": "button#payment"}')
    assert assessment.is_high_stakes

    # Keyword: sudo
    assessment = classifier.assess_action("shell", "sudo systemctl restart nginx")
    assert assessment.is_high_stakes

def test_destructive_shell_patterns():
    config = SafetyConfig()
    classifier = SafetyClassifier(config)

    assessment = classifier.assess_action("shell", "rm -rf /tmp/test_dir")
    assert assessment.is_high_stakes
    assert assessment.risk_level == "critical"

    assessment_safe = classifier.assess_action("shell", "ls -la /tmp")
    assert not assessment_safe.is_high_stakes
